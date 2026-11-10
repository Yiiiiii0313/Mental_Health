"""
管理员路由模块
提供用户管理、公告管理、文章管理、数据统计、数据导出等功能
"""
import csv
import io
from flask import Blueprint, request, Response
from utils.db import execute_query, execute_update
from utils.auth import md5_encrypt, login_required
from utils.response import success, error

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def _registry_stat(kind):
    try:
        if kind == 'total':
            return execute_query(
                'SELECT COUNT(*) as count FROM student_registry', fetch_one=True
            )['count']
        if kind == 'registered':
            return execute_query(
                'SELECT COUNT(*) as count FROM student_registry WHERE is_registered = 1', fetch_one=True
            )['count']
        if kind == 'unregistered':
            return execute_query(
                'SELECT COUNT(*) as count FROM student_registry WHERE is_registered = 0', fetch_one=True
            )['count']
    except Exception:
        return 0
    return 0


# 导出配置：数据类型 -> (SQL查询, 列名, 文件名)
EXPORT_CONFIG = {
    'users': (
        'SELECT id, username, real_name, role, phone, email, gender, status, created_at FROM users ORDER BY id',
        ['ID', '用户名', '姓名', '角色', '手机', '邮箱', '性别', '状态', '注册时间'],
        'users_export.csv'
    ),
    'appointments': (
        'SELECT a.id, s.real_name as student, c.real_name as counselor, a.appointment_date, '
        'a.time_slot, a.status, a.reason, a.created_at '
        'FROM appointments a '
        'LEFT JOIN users s ON a.student_id=s.id LEFT JOIN users c ON a.counselor_id=c.id ORDER BY a.id',
        ['ID', '学生', '咨询师', '日期', '时间段', '状态', '原因', '创建时间'],
        'appointments_export.csv'
    ),
    'scale_records': (
        'SELECT sr.id, u.real_name as user_name, sc.name as scale_name, sr.total_score, '
        'sr.result_level, sr.created_at '
        'FROM scale_records sr '
        'LEFT JOIN users u ON sr.user_id=u.id LEFT JOIN scales sc ON sr.scale_id=sc.id ORDER BY sr.id',
        ['ID', '用户', '量表', '总分', '结果', '测评时间'],
        'scale_records_export.csv'
    ),
    'articles': (
        'SELECT a.id, a.title, a.category, u.real_name as author, a.view_count, a.like_count, a.created_at '
        'FROM articles a LEFT JOIN users u ON a.author_id=u.id WHERE a.status=1 ORDER BY a.id',
        ['ID', '标题', '分类', '作者', '浏览量', '点赞数', '发布时间'],
        'articles_export.csv'
    ),
    'tree_hole': (
        'SELECT p.id, p.content, p.is_anonymous, p.reply_count, p.created_at '
        'FROM tree_hole_posts p WHERE p.status=1 ORDER BY p.id',
        ['ID', '内容', '是否匿名', '回复数', '发布时间'],
        'tree_hole_export.csv'
    ),
    'student_registry': (
        'SELECT student_no, real_name, department, class_name, '
        'CASE is_registered WHEN 1 THEN "已注册" ELSE "未注册" END as status, '
        'registered_at, created_at '
        'FROM student_registry ORDER BY student_no',
        ['学号', '姓名', '院系', '班级', '注册状态', '注册时间', '入库时间'],
        'student_registry_export.csv'
    ),
}


@admin_bp.route('/dashboard', methods=['GET'])
@login_required(roles=['admin'])
def dashboard():
    """获取管理后台仪表盘统计数据"""
    stats = {
        'user_count': execute_query(
            'SELECT COUNT(*) as count FROM users', fetch_one=True
        )['count'],
        'student_count': execute_query(
            'SELECT COUNT(*) as count FROM users WHERE role = "student"', fetch_one=True
        )['count'],
        'registry_total': _registry_stat('total'),
        'registry_registered': _registry_stat('registered'),
        'registry_unregistered': _registry_stat('unregistered'),
        'counselor_count': execute_query(
            'SELECT COUNT(*) as count FROM users WHERE role = "counselor"', fetch_one=True
        )['count'],
        'appointment_count': execute_query(
            'SELECT COUNT(*) as count FROM appointments', fetch_one=True
        )['count'],
        'pending_appointments': execute_query(
            'SELECT COUNT(*) as count FROM appointments WHERE status = "pending"', fetch_one=True
        )['count'],
        'article_count': execute_query(
            'SELECT COUNT(*) as count FROM articles WHERE status = 1', fetch_one=True
        )['count'],
        'scale_record_count': execute_query(
            'SELECT COUNT(*) as count FROM scale_records', fetch_one=True
        )['count'],
        'consultation_count': execute_query(
            'SELECT COUNT(*) as count FROM consultations WHERE status = "active"', fetch_one=True
        )['count'],
        'tree_hole_count': execute_query(
            'SELECT COUNT(*) as count FROM tree_hole_posts WHERE status = 1', fetch_one=True
        )['count'],
        'notification_count': execute_query(
            'SELECT COUNT(*) as count FROM notifications', fetch_one=True
        )['count'],
    }
    return success(stats)


@admin_bp.route('/export/<data_type>', methods=['GET'])
@login_required(roles=['admin'])
def export_data(data_type):
    """
    导出数据报表为 CSV 文件
    支持: users, appointments, scale_records, articles, tree_hole
    """
    if data_type not in EXPORT_CONFIG:
        return error('不支持的导出类型')

    sql, headers, filename = EXPORT_CONFIG[data_type]
    rows = execute_query(sql)

    output = io.StringIO()
    output.write('\ufeff')  # BOM 头，Excel 正确显示中文
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(list(row.values()))

    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@admin_bp.route('/users', methods=['GET'])
@login_required(roles=['admin'])
def list_users():
    """获取用户列表，支持角色筛选"""
    role = request.args.get('role', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size

    where = 'WHERE 1=1'
    params = []
    if role:
        where += ' AND role = %s'
        params.append(role)

    total = execute_query(
        f'SELECT COUNT(*) as count FROM users {where}',
        tuple(params) if params else None,
        fetch_one=True
    )['count']

    params.extend([page_size, offset])
    users = execute_query(
        f'SELECT id, username, real_name, role, phone, email, gender, status, created_at '
        f'FROM users {where} ORDER BY created_at DESC LIMIT %s OFFSET %s',
        tuple(params)
    )

    return success({
        'list': users,
        'total': total,
        'page': page,
        'page_size': page_size
    })


@admin_bp.route('/students', methods=['GET'])
@login_required(roles=['admin'])
def list_student_registry():
    """获取学籍库列表，支持搜索与注册状态筛选"""
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    keyword = request.args.get('keyword', '').strip()
    registered = request.args.get('registered', '')
    offset = (page - 1) * page_size

    where = 'WHERE 1=1'
    params = []
    if keyword:
        where += ' AND (student_no LIKE %s OR real_name LIKE %s)'
        like = f'%{keyword}%'
        params.extend([like, like])
    if registered == '1':
        where += ' AND is_registered = 1'
    elif registered == '0':
        where += ' AND is_registered = 0'

    total = execute_query(
        f'SELECT COUNT(*) as count FROM student_registry {where}',
        tuple(params) if params else None,
        fetch_one=True
    )['count']

    params.extend([page_size, offset])
    items = execute_query(
        f'SELECT id, student_no, real_name, gender, department, class_name, '
        f'is_registered, user_id, registered_at, created_at '
        f'FROM student_registry {where} ORDER BY student_no ASC LIMIT %s OFFSET %s',
        tuple(params)
    )

    return success({
        'list': items,
        'total': total,
        'page': page,
        'page_size': page_size
    })


@admin_bp.route('/students', methods=['POST'])
@login_required(roles=['admin'])
def create_student_registry():
    """管理员添加学籍库学生信息"""
    data = request.get_json() or {}
    student_no = data.get('student_no', '').strip()
    real_name = data.get('real_name', '').strip()
    department = (data.get('department') or '').strip() or None
    class_name = (data.get('class_name') or '').strip() or None
    gender = data.get('gender', 0)

    if not student_no or not real_name:
        return error('学号和姓名不能为空')
    if len(student_no) > 20:
        return error('学号长度不能超过20位')
    if len(real_name) > 50:
        return error('姓名长度不能超过50字')
    if gender not in (0, 1, 2):
        return error('无效的性别值')

    existing = execute_query(
        'SELECT id FROM student_registry WHERE student_no = %s',
        (student_no,), fetch_one=True
    )
    if existing:
        return error('该学号已存在于学籍库')

    record_id = execute_update(
        'INSERT INTO student_registry (student_no, real_name, gender, department, class_name, is_registered) '
        'VALUES (%s, %s, %s, %s, %s, 0)',
        (student_no, real_name, gender, department, class_name)
    )
    return success({'id': record_id}, '学生信息添加成功')


@admin_bp.route('/users', methods=['POST'])
@login_required(roles=['admin'])
def create_user():
    """
    管理员创建用户
    请求体: { username, password, real_name, role, phone, email }
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '123456')
    real_name = data.get('real_name', '').strip()
    role = data.get('role', 'student')

    if not username or not real_name:
        return error('用户名和姓名不能为空')

    if role not in ('student', 'counselor', 'admin'):
        return error('无效的角色')

    existing = execute_query(
        'SELECT id FROM users WHERE username = %s', (username,), fetch_one=True
    )
    if existing:
        return error('用户名已存在')

    user_id = execute_update(
        'INSERT INTO users (username, password, real_name, role, phone, email, gender) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
        (
            username, md5_encrypt(password), real_name, role,
            data.get('phone', ''), data.get('email', ''), data.get('gender', 0)
        )
    )

    if role == 'counselor':
        execute_update(
            'INSERT INTO counselor_profiles (user_id, title, specialty, introduction) '
            'VALUES (%s, %s, %s, %s)',
            (user_id, data.get('title', '心理咨询师'), data.get('specialty', ''), data.get('introduction', ''))
        )

    return success({'user_id': user_id}, '用户创建成功')


@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@login_required(roles=['admin'])
def toggle_user_status(user_id):
    """启用/禁用用户"""
    data = request.get_json()
    status = data.get('status')

    if status not in (0, 1):
        return error('无效的状态值')

    execute_update('UPDATE users SET status = %s WHERE id = %s', (status, user_id))
    return success(message='用户状态更新成功')


@admin_bp.route('/announcements', methods=['POST'])
@login_required(roles=['admin'])
def create_announcement():
    """发布新公告"""
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()

    if not title or not content:
        return error('标题和内容不能为空')

    ann_id = execute_update(
        'INSERT INTO announcements (title, content, publisher_id) VALUES (%s, %s, %s)',
        (title, content, request.current_user['id'])
    )
    return success({'id': ann_id}, '公告发布成功')


@admin_bp.route('/announcements/<int:ann_id>', methods=['DELETE'])
@login_required(roles=['admin'])
def delete_announcement(ann_id):
    """下架公告"""
    execute_update('UPDATE announcements SET status = 0 WHERE id = %s', (ann_id,))
    return success(message='公告已下架')


@admin_bp.route('/articles', methods=['POST'])
@login_required(roles=['admin', 'counselor'])
def create_article():
    """发布心理文章"""
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    category = data.get('category', '心理健康')

    if not title or not content:
        return error('标题和内容不能为空')

    article_id = execute_update(
        'INSERT INTO articles (title, content, category, author_id) VALUES (%s, %s, %s, %s)',
        (title, content, category, request.current_user['id'])
    )
    return success({'id': article_id}, '文章发布成功')


@admin_bp.route('/articles/<int:article_id>', methods=['DELETE'])
@login_required(roles=['admin'])
def delete_article(article_id):
    """下架文章"""
    execute_update('UPDATE articles SET status = 0 WHERE id = %s', (article_id,))
    return success(message='文章已下架')
