"""
统一响应格式工具模块
封装API返回的JSON结构
"""
from flask import jsonify


def success(data=None, message='操作成功'):
    """
    返回成功响应
    :param data: 响应数据
    :param message: 提示信息
    :return: JSON响应
    """
    return jsonify({
        'code': 200,
        'message': message,
        'data': data
    })


def error(message='操作失败', code=400):
    """
    返回错误响应
    :param message: 错误信息
    :param code: 错误码
    :return: JSON响应
    """
    return jsonify({
        'code': code,
        'message': message,
        'data': None
    }), code if code >= 400 else 400
