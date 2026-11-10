"""
数据库连接工具模块
提供数据库连接和通用查询方法
"""
import pymysql
from pymysql.cursors import DictCursor
from pymysql.err import OperationalError
from config import Config


class DatabaseError(Exception):
    """数据库异常封装类，用于向上层返回友好错误信息"""

    def __init__(self, message, err_code=0):
        super().__init__(message)
        self.err_code = err_code


def get_db_connection():
    """
    获取MySQL数据库连接
    :return: pymysql连接对象
    :raises DatabaseError: 连接失败时抛出
    """
    try:
        return pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4',
            cursorclass=DictCursor,
            autocommit=False
        )
    except OperationalError as e:
        err_code = e.args[0] if e.args else 0
        if err_code == 1045:
            raise DatabaseError(
                '数据库认证失败，请检查 server/.env 中的 DB_PASSWORD 是否正确',
                err_code
            ) from e
        if err_code == 1049:
            raise DatabaseError(
                '数据库 mental_health_server 不存在，请先执行 server/sql/init.sql',
                err_code
            ) from e
        if err_code == 2003:
            raise DatabaseError('无法连接 MySQL，请确认 MySQL 服务已启动', err_code) from e
        raise DatabaseError(f'数据库连接失败：{e}', err_code) from e


def execute_query(sql, params=None, fetch_one=False):
    """
    执行查询SQL语句
    :param sql: SQL语句
    :param params: 参数元组
    :param fetch_one: 是否只取一条记录
    :return: 查询结果
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()
    finally:
        conn.close()


def execute_update(sql, params=None):
    """
    执行增删改SQL语句
    :param sql: SQL语句
    :param params: 参数元组
    :return: 受影响的行数或最后插入的ID
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
