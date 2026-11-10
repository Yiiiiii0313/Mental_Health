"""
用户认证路由模块
处理登录、注册、获取当前用户信息、头像上传、找回密码
"""
import os
import re
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

from flask import Blueprint, request
from werkzeug.utils import secure_filename

from config import Config
from utils.db import execute_query, execute_update, DatabaseError
from utils.auth import md5_encrypt, generate_token, login_required
from utils.response import success, error
from utils.email_sender import is_mail_configured, send_email, build_reset_code_mail

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

AVATAR_DIR = Path(__file__).resolve().parent.parent / 'static' / 'media' / 'avatars'
AVATAR_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_AVATAR_SIZE = 5 * 1024 * 1024
EMAIL_RE = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')

SECURITY_QUESTION_PRESETS = (
    '你的名字是什么？',
    '你的生日是什么？',
    '你小学的名称是什么？',
    '你最喜欢的老师叫什么？',
)

_nickname_ready = None
_student_no_ready = None
_registry_ready = None
_security_ready = None
_reset_codes_ready = None


def _ensure_student_no_column():
    global _student_no_ready
    if _student_no_ready is not None:
        return _student_no_ready
    try:
        execute_query('SELECT student_no FROM users LIMIT 1', fetch_one=True)
        _student_no_ready = True
    except Exception:
        try:
            execute_update(
                'ALTER TABLE users ADD COLUMN student_no VARCHAR(20) DEFAULT NULL UNIQUE '
                'COMMENT "学号(学生)" AFTER real_name'
            )
            _student_no_ready = True
        except Exception:
            _student_no_ready = False
    return _student_no_ready


def _ensure_student_registry_table():
    global _registry_ready
    if _registry_ready is not None:
        return _registry_ready
    try:
        execute_query('SELECT 1 FROM student_registry LIMIT 1', fetch_one=True)
        _registry_ready = True
    except Exception:
        try:
            execute_update(
                'CREATE TABLE student_registry ('
                'id INT PRIMARY KEY AUTO_INCREMENT, '
                'student_no VARCHAR(20) NOT NULL UNIQUE, '
                'real_name VARCHAR(50) NOT NULL, '
                'gender TINYINT DEFAULT 0, '
                'department VARCHAR(100) DEFAULT NULL, '
                'class_name VARCHAR(50) DEFAULT NULL, '
                'is_registered TINYINT DEFAULT 0, '
                'user_id INT DEFAULT NULL, '
                'created_at DATETIME DEFAULT CURRENT_TIMESTAMP, '
                'registered_at DATETIME DEFAULT NULL, '
                'FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL'
                ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4'
            )
            _registry_ready = True
        except Exception:
            _registry_ready = False
    return _registry_ready


def _validate_student_for_register(student_no, real_name):
    """校验学号与姓名是否可注册，返回 (registry, error_message)"""
    _ensure_student_registry_table()
    if not _ensure_student_registry_table():
        return None, '学籍库未初始化，请联系管理员'

    registry = execute_query(
        'SELECT * FROM student_registry WHERE student_no = %s',
        (student_no,), fetch_one=True
    )
    if not registry:
        return None, '学号不存在，请核对后重试'
    if registry['real_name'] != real_name:
        return None, '姓名与学号不匹配，请核对后重试'
    if registry['is_registered']:
        return None, '该学号已注册平台，请勿重复注册'
    return registry, None


def _ensure_nickname_column():
    global _nickname_ready
    if _nickname_ready is not None:
        return _nickname_ready
    try:
        execute_query('SELECT nickname FROM users LIMIT 1', fetch_one=True)
        _nickname_ready = True
    except Exception:
        try:
            execute_update(
                'ALTER TABLE users ADD COLUMN nickname VARCHAR(50) DEFAULT NULL COMMENT "昵称" AFTER real_name'
            )
            _nickname_ready = True
        except Exception:
            _nickname_ready = False
    return _nickname_ready


def _ensure_security_columns():
    """确保 users 表有安全问题字段"""
    global _security_ready
    if _security_ready is not None:
        return _security_ready
    try:
        execute_query('SELECT security_question, security_answer FROM users LIMIT 1', fetch_one=True)
        _security_ready = True
    except Exception:
        try:
            execute_update(
                'ALTER TABLE users ADD COLUMN security_question VARCHAR(200) DEFAULT NULL '
                'COMMENT "找回密码安全问题" AFTER email'
            )
            execute_update(
                'ALTER TABLE users ADD COLUMN security_answer VARCHAR(64) DEFAULT NULL '
                'COMMENT "安全问题答案(MD5)" AFTER security_question'
            )
            _security_ready = True
        except Exception:
            _security_ready = False
    return _security_ready


def _ensure_reset_codes_table():
    """确保找回密码验证码表存在"""
    global _reset_codes_ready
    if _reset_codes_ready is not None:
        return _reset_codes_ready
    try:
        execute_query('SELECT 1 FROM password_reset_codes LIMIT 1', fetch_one=True)
        _reset_codes_ready = True
    except Exception:
        try:
            execute_update(
                'CREATE TABLE password_reset_codes ('
                'id INT PRIMARY KEY AUTO_INCREMENT, '
                'user_id INT NOT NULL, '
                'email VARCHAR(100) NOT NULL, '
                'code VARCHAR(10) NOT NULL, '
                'expires_at DATETIME NOT NULL, '
                'used TINYINT NOT NULL DEFAULT 0, '
                'created_at DATETIME DEFAULT CURRENT_TIMESTAMP, '
                'KEY idx_reset_email (email), '
                'KEY idx_reset_user (user_id), '
                'CONSTRAINT fk_reset_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE'
                ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4'
            )
            _reset_codes_ready = True
        except Exception:
            _reset_codes_ready = False
    return _reset_codes_ready


def _normalize_answer(answer):
    return (answer or '').strip().lower()


def _hash_security_answer(answer):
    return md5_encrypt(_normalize_answer(answer))


def _validate_email(email):
    return bool(email and EMAIL_RE.match(email))


def _user_public_fields(user):
    return {
        'id': user['id'],
        'username': user['username'],
        'real_name': user['real_name'],
        'student_no': user.get('student_no'),
        'nickname': user.get('nickname'),
        'role': user['role'],
        'phone': user.get('phone'),
        'email': user.get('email'),
        'gender': user.get('gender'),
        'avatar': user.get('avatar'),
        'has_security_question': bool(user.get('security_question')),
    }


def _get_user_detail(user_id):
    _ensure_nickname_column()
    _ensure_student_no_column()
    _ensure_security_columns()
    return execute_query(
        'SELECT id, username, real_name, student_no, nickname, role, phone, email, gender, avatar, '
        'security_question, created_at '
        'FROM users WHERE id = %s',
        (user_id,),
        fetch_one=True
    )


def _remove_avatar_file(avatar_url):
    if not avatar_url or not avatar_url.startswith('/static/media/avatars/'):
        return
    file_path = Path(__file__).resolve().parent.parent / avatar_url.lstrip('/')
    if file_path.is_file():
        file_path.unlink()


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    请求体: { username, password }
    """
    _ensure_nickname_column()
    _ensure_security_columns()
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return error('用户名和密码不能为空')

    try:
        user = execute_query(
            'SELECT id, username, password, real_name, nickname, role, phone, email, gender, avatar, '
            'status, security_question '
            'FROM users WHERE username = %s',
            (username,),
            fetch_one=True
        )
    except DatabaseError as e:
        return error(str(e), 500)

    if not user:
        return error('用户名不存在')

    if user['status'] == 0:
        return error('账号已被禁用，请联系管理员')

    if user['password'] != md5_encrypt(password):
        return error('密码错误')

    token = generate_token(user['id'], user['username'], user['role'])
    user_info = _user_public_fields(user)

    return success({
        'token': token,
        'user': user_info
    }, '登录成功')


@auth_bp.route('/verify-student', methods=['POST'])
def verify_student():
    """
    注册前校验学号与姓名（公开接口）
    请求体: { student_no, real_name }
    """
    data = request.get_json() or {}
    student_no = data.get('student_no', '').strip()
    real_name = data.get('real_name', '').strip()
    if not student_no or not real_name:
        return error('请填写学号和姓名')

    registry, err = _validate_student_for_register(student_no, real_name)
    if err:
        return error(err)

    return success({
        'student_no': student_no,
        'real_name': registry['real_name'],
        'department': registry.get('department'),
        'class_name': registry.get('class_name'),
        'can_register': True,
    }, '学籍信息校验通过')


@auth_bp.route('/security-questions', methods=['GET'])
def list_security_questions():
    """返回推荐的安全问题列表"""
    return success({'questions': list(SECURITY_QUESTION_PRESETS)})


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    学生注册接口
    请求体: { username, password, student_no, real_name, email, security_question,
              security_answer, phone, gender }
    """
    _ensure_student_no_column()
    _ensure_student_registry_table()
    _ensure_security_columns()
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    student_no = data.get('student_no', '').strip()
    real_name = data.get('real_name', '').strip()
    email = data.get('email', '').strip()
    security_question = data.get('security_question', '').strip()
    security_answer = data.get('security_answer', '').strip()

    if not username or not password or not student_no or not real_name:
        return error('用户名、密码、学号和姓名不能为空')
    if not email:
        return error('请填写注册邮箱')
    if not _validate_email(email):
        return error('邮箱格式不正确')
    if not security_question:
        return error('请设置找回密码安全问题')
    if not security_answer:
        return error('请填写安全问题答案')
    if len(password) < 6:
        return error('密码至少 6 位')

    registry, err = _validate_student_for_register(student_no, real_name)
    if err:
        return error(err)

    try:
        existing = execute_query(
            'SELECT id FROM users WHERE username = %s',
            (username,),
            fetch_one=True
        )
        if existing:
            return error('用户名已存在')

        dup_no = execute_query(
            'SELECT id FROM users WHERE student_no = %s',
            (student_no,),
            fetch_one=True
        )
        if dup_no:
            return error('该学号已注册，请勿重复注册')

        dup_email = execute_query(
            'SELECT id FROM users WHERE email = %s',
            (email,),
            fetch_one=True
        )
        if dup_email:
            return error('该邮箱已被注册，请更换邮箱')

        user_id = execute_update(
            'INSERT INTO users (username, password, real_name, student_no, role, phone, email, '
            'security_question, security_answer, gender) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (
                username,
                md5_encrypt(password),
                real_name,
                student_no,
                'student',
                data.get('phone', ''),
                email,
                security_question,
                _hash_security_answer(security_answer),
                data.get('gender', registry.get('gender', 0) or 0)
            )
        )
        execute_update(
            'UPDATE student_registry SET is_registered = 1, user_id = %s, registered_at = NOW() '
            'WHERE student_no = %s',
            (user_id, student_no)
        )
    except DatabaseError as e:
        return error(str(e), 500)

    return success({'user_id': user_id}, '注册成功')


@auth_bp.route('/forgot-password/send-code', methods=['POST'])
def send_reset_code():
    """
    向注册邮箱发送找回密码验证码
    请求体: { email }
    """
    _ensure_reset_codes_table()
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    if not email:
        return error('请填写注册邮箱')
    if not _validate_email(email):
        return error('邮箱格式不正确')

    user = execute_query(
        'SELECT id, username, email, status FROM users WHERE email = %s',
        (email,),
        fetch_one=True
    )
    if not user:
        return error('该邮箱未注册')
    if user['status'] == 0:
        return error('账号已被禁用，请联系管理员')

    recent = execute_query(
        'SELECT id, created_at FROM password_reset_codes '
        'WHERE user_id = %s AND used = 0 ORDER BY id DESC LIMIT 1',
        (user['id'],),
        fetch_one=True
    )
    if recent and recent.get('created_at'):
        created = recent['created_at']
        if isinstance(created, str):
            created = datetime.strptime(created[:19], '%Y-%m-%d %H:%M:%S')
        if datetime.now() - created < timedelta(seconds=60):
            return error('发送过于频繁，请稍后再试')

    code = f'{random.randint(0, 999999):06d}'
    expire_minutes = Config.RESET_CODE_EXPIRE_MINUTES
    expires_at = datetime.now() + timedelta(minutes=expire_minutes)
    execute_update(
        'INSERT INTO password_reset_codes (user_id, email, code, expires_at) VALUES (%s, %s, %s, %s)',
        (user['id'], email, code, expires_at.strftime('%Y-%m-%d %H:%M:%S'))
    )

    subject, body = build_reset_code_mail(code, expire_minutes)
    mailed, mail_msg = send_email(email, subject, body)

    payload = {
        'email': email,
        'expire_minutes': expire_minutes,
        'mailed': mailed,
    }
    if not is_mail_configured() or not mailed:
        payload['dev_code'] = code
        tip = '验证码已生成（当前为开发模式，请使用页面显示的验证码）'
        if is_mail_configured() and not mailed:
            tip = f'{mail_msg}；已启用开发回退，请使用页面显示的验证码'
        return success(payload, tip)

    return success(payload, '验证码已发送到邮箱，请查收')


@auth_bp.route('/forgot-password/reset-by-email', methods=['POST'])
def reset_by_email():
    """
    通过邮箱验证码重置密码
    请求体: { email, code, new_password }
    """
    _ensure_reset_codes_table()
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    code = data.get('code', '').strip()
    new_password = data.get('new_password', '')

    if not email or not code or not new_password:
        return error('请填写邮箱、验证码和新密码')
    if len(new_password) < 6:
        return error('新密码至少 6 位')

    user = execute_query(
        'SELECT id, status FROM users WHERE email = %s',
        (email,),
        fetch_one=True
    )
    if not user:
        return error('该邮箱未注册')
    if user['status'] == 0:
        return error('账号已被禁用，请联系管理员')

    record = execute_query(
        'SELECT * FROM password_reset_codes WHERE email = %s AND code = %s AND used = 0 '
        'ORDER BY id DESC LIMIT 1',
        (email, code),
        fetch_one=True
    )
    if not record:
        return error('验证码错误或已失效')

    expires_at = record['expires_at']
    if isinstance(expires_at, str):
        expires_at = datetime.strptime(expires_at[:19], '%Y-%m-%d %H:%M:%S')
    if datetime.now() > expires_at:
        return error('验证码已过期，请重新获取')

    execute_update(
        'UPDATE users SET password = %s WHERE id = %s',
        (md5_encrypt(new_password), user['id'])
    )
    execute_update('UPDATE password_reset_codes SET used = 1 WHERE id = %s', (record['id'],))
    return success(message='密码已重置，请使用新密码登录')


@auth_bp.route('/forgot-password/question', methods=['GET'])
def get_security_question():
    """
    根据用户名获取安全问题（公开）
    查询参数: username
    """
    _ensure_security_columns()
    username = (request.args.get('username') or '').strip()
    if not username:
        return error('请填写用户名')

    user = execute_query(
        'SELECT id, security_question, status FROM users WHERE username = %s',
        (username,),
        fetch_one=True
    )
    if not user:
        return error('用户名不存在')
    if user['status'] == 0:
        return error('账号已被禁用，请联系管理员')
    if not user.get('security_question'):
        return error('该账号未设置安全问题，请使用邮箱找回')

    return success({
        'username': username,
        'security_question': user['security_question'],
    })


@auth_bp.route('/forgot-password/reset-by-question', methods=['POST'])
def reset_by_question():
    """
    通过安全问题答案重置密码
    请求体: { username, security_answer, new_password }
    """
    _ensure_security_columns()
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    answer = data.get('security_answer', '')
    new_password = data.get('new_password', '')

    if not username or not answer or not new_password:
        return error('请填写用户名、安全问题答案和新密码')
    if len(new_password) < 6:
        return error('新密码至少 6 位')

    user = execute_query(
        'SELECT id, security_answer, status FROM users WHERE username = %s',
        (username,),
        fetch_one=True
    )
    if not user:
        return error('用户名不存在')
    if user['status'] == 0:
        return error('账号已被禁用，请联系管理员')
    if not user.get('security_answer'):
        return error('该账号未设置安全问题，请使用邮箱找回')
    if user['security_answer'] != _hash_security_answer(answer):
        return error('安全问题答案不正确')

    execute_update(
        'UPDATE users SET password = %s WHERE id = %s',
        (md5_encrypt(new_password), user['id'])
    )
    return success(message='密码已重置，请使用新密码登录')


@auth_bp.route('/profile', methods=['GET'])
@login_required()
def get_profile():
    """获取当前登录用户信息"""
    detail = _get_user_detail(request.current_user['id'])
    if detail:
        detail['has_security_question'] = bool(detail.pop('security_question', None))
    return success(detail)


@auth_bp.route('/avatar/upload', methods=['POST'])
@login_required()
def upload_avatar():
    """上传用户头像"""
    file = request.files.get('file')
    if not file or not file.filename:
        return error('请选择头像图片')

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in AVATAR_EXTS:
        return error('仅支持 jpg/png/gif/webp 格式的图片')

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_AVATAR_SIZE:
        return error('头像图片请控制在 5MB 以内')

    user_id = request.current_user['id']
    old = execute_query('SELECT avatar FROM users WHERE id = %s', (user_id,), fetch_one=True)

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    safe_ext = secure_filename(f'file.{ext}').rsplit('.', 1)[-1]
    filename = f'{user_id}_{uuid.uuid4().hex[:12]}.{safe_ext}'
    file.save(AVATAR_DIR / filename)

    avatar_url = f'/static/media/avatars/{filename}'
    execute_update('UPDATE users SET avatar = %s WHERE id = %s', (avatar_url, user_id))
    _remove_avatar_file(old.get('avatar') if old else None)

    return success({'avatar': avatar_url}, '头像上传成功')


@auth_bp.route('/profile', methods=['PUT'])
@login_required()
def update_profile():
    """更新当前用户个人信息"""
    _ensure_nickname_column()
    data = request.get_json()
    user = request.current_user

    nickname = (data.get('nickname') or '').strip() or None
    if nickname and len(nickname) > 20:
        return error('昵称不能超过20字')

    email = (data.get('email') or '').strip()
    if email and not _validate_email(email):
        return error('邮箱格式不正确')

    execute_update(
        'UPDATE users SET real_name=%s, nickname=%s, phone=%s, email=%s, gender=%s WHERE id=%s',
        (
            data.get('real_name', user['real_name']).strip(),
            nickname,
            data.get('phone', ''),
            email,
            data.get('gender', 0),
            user['id']
        )
    )
    detail = _get_user_detail(user['id'])
    if detail:
        detail['has_security_question'] = bool(detail.pop('security_question', None))
    return success(detail, '个人信息更新成功')


@auth_bp.route('/password', methods=['PUT'])
@login_required()
def change_password():
    """修改密码"""
    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return error('请填写原密码和新密码')

    user = execute_query(
        'SELECT password FROM users WHERE id = %s',
        (request.current_user['id'],),
        fetch_one=True
    )

    if user['password'] != md5_encrypt(old_password):
        return error('原密码错误')

    execute_update(
        'UPDATE users SET password = %s WHERE id = %s',
        (md5_encrypt(new_password), request.current_user['id'])
    )
    return success(message='密码修改成功')
