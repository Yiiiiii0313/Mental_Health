"""
公告路由模块
提供公告的查询功能
"""
from flask import Blueprint, request
from utils.db import execute_query
from utils.auth import login_required
from utils.response import success, error

announcement_bp = Blueprint('announcement', __name__, url_prefix='/api/announcements')


@announcement_bp.route('', methods=['GET'])
@login_required()
def list_announcements():
    """
    获取公告列表
    支持分页参数: page, page_size
    """
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size

    total = execute_query(
        'SELECT COUNT(*) as count FROM announcements WHERE status = 1',
        fetch_one=True
    )['count']

    items = execute_query(
        'SELECT a.*, u.real_name as publisher_name '
        'FROM announcements a '
        'LEFT JOIN users u ON a.publisher_id = u.id '
        'WHERE a.status = 1 '
        'ORDER BY a.created_at DESC '
        'LIMIT %s OFFSET %s',
        (page_size, offset)
    )

    return success({
        'list': items,
        'total': total,
        'page': page,
        'page_size': page_size
    })


@announcement_bp.route('/<int:announcement_id>', methods=['GET'])
@login_required()
def get_announcement(announcement_id):
    """获取公告详情"""
    item = execute_query(
        'SELECT a.*, u.real_name as publisher_name '
        'FROM announcements a '
        'LEFT JOIN users u ON a.publisher_id = u.id '
        'WHERE a.id = %s AND a.status = 1',
        (announcement_id,),
        fetch_one=True
    )
    if not item:
        return error('公告不存在')
    return success(item)
