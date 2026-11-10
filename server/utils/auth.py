"""
认证工具模块
提供密码加密、JWT令牌生成与验证、登录校验装饰器
"""
import hashlib
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request
from config import Config
from utils.db import execute_query
from utils.response import error


def md5_encrypt(password):
    """
    对密码进行MD5加密
    :param password: 明文密码
    :return: MD5哈希值
    """
    return hashlib.md5(password.encode('utf-8')).hexdigest()


def generate_token(user_id, username, role):
    """
    生成JWT令牌
    :param user_id: 用户ID
    :param username: 用户名
    :param role: 用户角色
    :return: JWT字符串
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRE_HOURS)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')


def decode_token(token):
    """
    解析JWT令牌
    :param token: JWT字符串
    :return: 载荷字典或None
    """
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def login_required(roles=None):
    """
    登录验证装饰器，可选角色限制
    :param roles: 允许的角色列表，如 ['admin', 'counselor']
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return error('请先登录', 401)

            token = auth_header.split(' ')[1]
            payload = decode_token(token)
            if not payload:
                return error('登录已过期，请重新登录', 401)

            user = execute_query(
                'SELECT id, username, real_name, role, status FROM users WHERE id = %s',
                (payload['user_id'],),
                fetch_one=True
            )
            if not user or user['status'] == 0:
                return error('用户不存在或已被禁用', 401)

            if roles and user['role'] not in roles:
                return error('权限不足', 403)

            request.current_user = user
            return f(*args, **kwargs)
        return wrapper
    return decorator
