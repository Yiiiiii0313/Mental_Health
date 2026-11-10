"""
心屿校园心理健康服务平台 - Flask应用入口
"""
import socket
import pymysql
from flask import Flask
from flask_cors import CORS
from config import Config
from utils.response import error
from utils.db import DatabaseError
from routes.auth import auth_bp
from routes.announcement import announcement_bp
from routes.article import article_bp
from routes.appointment import appointment_bp
from routes.scale import scale_bp
from routes.mood import mood_bp
from routes.consultation import consultation_bp
from routes.admin import admin_bp
from routes.notification import notification_bp
from routes.relaxation import relaxation_bp
from routes.tree_hole import tree_hole_bp
from routes.ai_chat import ai_chat_bp
from routes.insight import insight_bp
from routes.agent_report import agent_report_bp


def get_lan_ip():
    """获取本机局域网 IP，供同一 Wi-Fi / 网段内其他设备访问"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 不实际发包，仅借路由表解析出本机对外网卡 IP
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'


def create_app():
    """
    创建并配置Flask应用实例
    :return: Flask应用对象
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # 启用跨域支持
    CORS(app, supports_credentials=True)

    # 注册蓝图（路由模块）
    app.register_blueprint(auth_bp)
    app.register_blueprint(announcement_bp)
    app.register_blueprint(article_bp)
    app.register_blueprint(appointment_bp)
    app.register_blueprint(scale_bp)
    app.register_blueprint(mood_bp)
    app.register_blueprint(consultation_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(relaxation_bp)
    app.register_blueprint(tree_hole_bp)
    app.register_blueprint(ai_chat_bp)
    app.register_blueprint(insight_bp)
    app.register_blueprint(agent_report_bp)

    @app.route('/api/health')
    def health_check():
        """健康检查接口，同时检测数据库连接"""
        try:
            from utils.db import get_db_connection
            conn = get_db_connection()
            conn.close()
            return {'status': 'ok', 'message': '心屿校园心理健康服务平台运行正常', 'database': 'connected'}
        except pymysql.err.OperationalError as e:
            return {
                'status': 'error',
                'message': '数据库连接失败，请检查 server/.env 中的 MySQL 配置',
                'database': 'disconnected',
                'detail': str(e)
            }, 503

    @app.errorhandler(DatabaseError)
    def handle_custom_db_error(e):
        """业务层数据库异常，返回友好提示"""
        return error(str(e), 500)

    @app.errorhandler(pymysql.err.OperationalError)
    def handle_db_error(e):
        """数据库连接/操作异常统一处理"""
        err_code = e.args[0] if e.args else 0
        if err_code == 1045:
            msg = '数据库认证失败，请在 server/.env 中设置正确的 DB_PASSWORD'
        elif err_code == 1049:
            msg = '数据库不存在，请先执行 server/sql/init.sql 初始化数据库'
        elif err_code == 2003:
            msg = '无法连接 MySQL 服务，请确认 MySQL 已启动'
        else:
            msg = f'数据库错误：{e}'
        return error(msg, 500)

    @app.errorhandler(Exception)
    def handle_general_error(e):
        """其他未捕获异常统一返回 JSON，避免前端只看到 500"""
        return error(f'服务器内部错误：{str(e)}', 500)

    return app


app = create_app()

if __name__ == '__main__':
    port = 5000
    lan_ip = get_lan_ip()
    print('\n' + '=' * 50)
    print('  心屿校园心理健康服务平台已启动')
    print(f'  本机访问:     http://127.0.0.1:{port}')
    print(f'  局域网访问:   http://{lan_ip}:{port}')
    print('  （同一 Wi-Fi 下的其他电脑/手机可使用上方局域网地址）')
    print('=' * 50 + '\n')
    app.run(host='0.0.0.0', port=port, debug=True)
