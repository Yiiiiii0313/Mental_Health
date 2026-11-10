"""
应用配置文件
定义数据库连接、JWT密钥等全局配置项
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 server/.env 中的环境变量（override 确保修改后重新读取）
load_dotenv(Path(__file__).resolve().parent / '.env', override=True)


class Config:
    """Flask应用配置类"""

    # Flask密钥
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mental-health-secret-key-2026')

    # MySQL数据库配置（密码请写在 server/.env 文件中，不要硬编码）
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'mental_health_server')

    # JWT配置
    JWT_SECRET = os.environ.get('JWT_SECRET', 'mental-health-jwt-secret')
    JWT_EXPIRE_HOURS = 24

    # 邮件配置（找回密码验证码；不填则走开发模式，接口直接返回验证码）
    MAIL_HOST = os.environ.get('MAIL_HOST', '')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USER = os.environ.get('MAIL_USER', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_FROM = os.environ.get('MAIL_FROM', '')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', '1') == '1'
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', '0') == '1'
    RESET_CODE_EXPIRE_MINUTES = int(os.environ.get('RESET_CODE_EXPIRE_MINUTES', 10))

    # 大模型配置（OpenAI 兼容接口，支持 DeepSeek、通义千问等）
    LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
    LLM_API_BASE = os.environ.get('LLM_API_BASE', 'https://api.deepseek.com/v1')
    LLM_MODEL = os.environ.get('LLM_MODEL', 'deepseek-chat')
    LLM_TIMEOUT = int(os.environ.get('LLM_TIMEOUT', 60))

    # RAG 知识库配置（AI 助手检索增强）
    LLM_EMBEDDING_MODEL = os.environ.get('LLM_EMBEDDING_MODEL', 'text-embedding-3-small')
    _emb_base = (os.environ.get('LLM_EMBEDDING_API_BASE') or '').strip().rstrip('/')
    LLM_EMBEDDING_API_BASE = _emb_base or None
    RAG_TOP_K = int(os.environ.get('RAG_TOP_K', 5))
    RAG_ENABLED = os.environ.get('RAG_ENABLED', '1') == '1'
