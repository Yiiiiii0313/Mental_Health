"""
消息通知工具模块
提供创建通知的通用方法
"""
from utils.db import execute_update


def create_notification(user_id, title, content, ntype='system', related_id=None):
    """
    创建一条消息通知
    :param user_id: 接收用户ID
    :param title: 通知标题
    :param content: 通知内容
    :param ntype: 通知类型
    :param related_id: 关联业务ID
    """
    execute_update(
        'INSERT INTO notifications (user_id, title, content, type, related_id) VALUES (%s, %s, %s, %s, %s)',
        (user_id, title, content, ntype, related_id)
    )


def mark_related_notifications_read(user_id, ntype, related_id):
    """将指定业务关联的通知标记为已读"""
    execute_update(
        'UPDATE notifications SET is_read = 1 '
        'WHERE user_id = %s AND type = %s AND related_id = %s AND is_read = 0',
        (user_id, ntype, related_id)
    )
