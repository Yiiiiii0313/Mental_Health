"""
消息通知路由模块
"""
from flask import Blueprint, request
from utils.db import execute_query, execute_update
from utils.auth import login_required
from utils.response import success, error

notification_bp = Blueprint('notification', __name__, url_prefix='/api/notifications')


@notification_bp.route('', methods=['GET'])
@login_required()
def list_notifications():
    """获取当前用户的通知列表，支持 is_read 筛选：0未读 1已读 不传为全部"""
    user_id = request.current_user['id']
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    offset = (page - 1) * page_size
    read_filter = request.args.get('is_read')

    conditions = ['user_id = %s']
    params = [user_id]
    if read_filter in ('0', '1'):
        conditions.append('is_read = %s')
        params.append(int(read_filter))

    where = ' AND '.join(conditions)

    total = execute_query(
        f'SELECT COUNT(*) as count FROM notifications WHERE {where}',
        tuple(params), fetch_one=True
    )['count']

    list_params = params + [page_size, offset]
    items = execute_query(
        f'SELECT * FROM notifications WHERE {where} ORDER BY created_at DESC LIMIT %s OFFSET %s',
        tuple(list_params)
    )

    unread = execute_query(
        'SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = 0',
        (user_id,), fetch_one=True
    )['count']

    read_count = execute_query(
        'SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = 1',
        (user_id,), fetch_one=True
    )['count']

    all_count = execute_query(
        'SELECT COUNT(*) as count FROM notifications WHERE user_id = %s',
        (user_id,), fetch_one=True
    )['count']

    return success({
        'list': items,
        'total': total,
        'unread_count': unread,
        'read_count': read_count,
        'all_count': all_count,
        'page': page,
        'page_size': page_size
    })


@notification_bp.route('/unread-count', methods=['GET'])
@login_required()
def unread_count():
    """获取未读通知数量"""
    count = execute_query(
        'SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = 0',
        (request.current_user['id'],), fetch_one=True
    )['count']
    return success({'unread_count': count})


@notification_bp.route('/<int:notification_id>/read', methods=['PUT'])
@login_required()
def mark_read(notification_id):
    """标记单条通知为已读"""
    execute_update(
        'UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s',
        (notification_id, request.current_user['id'])
    )
    return success(message='已标记为已读')


@notification_bp.route('/read-all', methods=['PUT'])
@login_required()
def mark_all_read():
    """标记全部通知为已读"""
    execute_update(
        'UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0',
        (request.current_user['id'],)
    )
    return success(message='全部已读')


@notification_bp.route('/<int:notification_id>', methods=['DELETE'])
@login_required()
def delete_notification(notification_id):
    """删除通知"""
    execute_update(
        'DELETE FROM notifications WHERE id = %s AND user_id = %s',
        (notification_id, request.current_user['id'])
    )
    return success(message='通知已删除')
