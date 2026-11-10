"""
嵌入向量工具
调用 OpenAI 兼容 API 的 /embeddings 端点生成文本向量
与 utils/llm.py 保持一致的错误处理和配置读取模式
"""
import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / '.env'
_CONFIG_PATH = Path(__file__).resolve().parent.parent


def _get_embedding_config():
    """每次调用前重新加载 .env，支持热更新配置"""
    load_dotenv(_ENV_PATH, override=True)
    # 嵌入 API 地址：优先使用 LLM_EMBEDDING_API_BASE，fallback 到 LLM_API_BASE
    embedding_api_base = (os.environ.get('LLM_EMBEDDING_API_BASE') or '').strip()
    if embedding_api_base:
        api_base = embedding_api_base.rstrip('/')
    else:
        api_base = (os.environ.get('LLM_API_BASE') or 'https://api.deepseek.com/v1').rstrip('/')
    return {
        'api_key': (os.environ.get('LLM_API_KEY') or '').strip(),
        'api_base': api_base,
        'model': (os.environ.get('LLM_EMBEDDING_MODEL') or 'text-embedding-3-small').strip(),
        'timeout': int(os.environ.get('LLM_TIMEOUT') or 60),
    }


class EmbeddingError(Exception):
    """嵌入向量生成异常"""


def _friendly_error(msg):
    """将常见英文错误译为中文"""
    lower = str(msg).lower()
    if 'insufficient balance' in lower or 'insufficient_quota' in lower:
        return '大模型账户余额不足，无法生成向量嵌入，请检查账户余额'
    if 'authentication' in lower or 'invalid api key' in lower or 'api key' in lower:
        return 'API Key 无效或已失效，请检查 LLM_API_KEY 配置'
    if 'model' in lower and ('not' in lower or 'found' in lower or 'exist' in lower):
        return f'嵌入模型名称有误（{msg}），请检查 LLM_EMBEDDING_MODEL 配置'
    if 'timeout' in lower:
        return '嵌入服务响应超时，请稍后重试'
    return f'嵌入向量生成失败：{msg}'


def get_embedding(text):
    """
    获取单个文本的嵌入向量
    :param text: 输入文本
    :return: float 列表（嵌入向量）
    """
    return get_embeddings([text])[0]


def get_embeddings(texts):
    """
    批量获取多个文本的嵌入向量
    :param texts: 文本列表
    :return: 二维列表 [[float, float, ...], ...]
    """
    cfg = _get_embedding_config()
    url = f"{cfg['api_base']}/embeddings"

    payload = {
        'model': cfg['model'],
        'input': texts,
    }

    headers = {'Content-Type': 'application/json'}
    if cfg['api_key']:
        headers['Authorization'] = f'Bearer {cfg["api_key"]}'

    try:
        resp = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=cfg['timeout'],
        )
        data = resp.json()

        if resp.status_code != 200:
            err = data.get('error', {})
            msg = err.get('message', str(data)) if isinstance(err, dict) else str(data)
            raise EmbeddingError(_friendly_error(msg))

        # 按 input 顺序提取 embedding
        items = data.get('data', [])
        items.sort(key=lambda x: x.get('index', 0))
        return [item['embedding'] for item in items]

    except requests.Timeout:
        raise EmbeddingError('嵌入模型响应超时，请稍后重试')
    except requests.RequestException as e:
        raise EmbeddingError(f'无法连接嵌入服务：{e}')
    except (KeyError, IndexError) as e:
        raise EmbeddingError(f'嵌入服务返回数据格式异常：{e}')
