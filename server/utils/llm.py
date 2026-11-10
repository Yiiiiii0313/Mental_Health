"""
大模型调用工具
支持 OpenAI 兼容接口（DeepSeek、通义千问、OpenAI 等）
"""
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / '.env'


def _get_llm_config():
    """每次调用前重新加载 .env，避免修改配置后必须重启服务"""
    load_dotenv(_ENV_PATH, override=True)
    return {
        'api_key': (os.environ.get('LLM_API_KEY') or '').strip(),
        'api_base': (os.environ.get('LLM_API_BASE') or 'https://api.deepseek.com/v1').rstrip('/'),
        'model': os.environ.get('LLM_MODEL') or 'deepseek-chat',
        'timeout': int(os.environ.get('LLM_TIMEOUT') or 60),
    }

# AI心理助手系统提示词
SYSTEM_PROMPT = """你是校园心理健康服务平台的AI心理助手"小暖"。你的职责是：
1. 以温暖、共情、非评判的态度倾听用户的困扰
2. 提供情绪疏导、压力管理、人际交往、学业适应等方面的建议
3. 适时推荐平台功能：心理测评、放松训练、心情日记、预约咨询师等
4. 不做医学诊断，不替代专业心理咨询；若用户有自伤、自杀念头或严重症状，请温和引导其拨打心理援助热线400-123-4567或预约校内心理咨询

回复简洁亲切，使用中文，每次控制在200字以内为宜。"""


class LLMError(Exception):
    """大模型调用异常"""


def _friendly_error(msg):
    """将常见英文错误转为易懂的中文提示"""
    lower = str(msg).lower()
    if 'insufficient balance' in lower or 'insufficient_quota' in lower:
        return '大模型账户余额不足，请登录 DeepSeek 控制台充值后再试'
    if (
        'invalid api key' in lower
        or 'authentication' in lower
        or 'is invalid' in lower
        or 'api key' in lower and 'invalid' in lower
    ):
        return (
            'API Key 无效或已失效。请登录 https://platform.deepseek.com '
            '重新创建 API Key，填入 server/.env 的 LLM_API_KEY 后保存并重启后端'
        )
    if 'model' in lower and 'not' in lower:
        return f'模型名称有误，请检查 LLM_MODEL 配置：{msg}'
    return f'大模型请求失败：{msg}'


def _is_local_llm(api_base):
    """本地大模型（如 Ollama）通常不需要 API Key"""
    base = (api_base or '').lower()
    return 'localhost' in base or '127.0.0.1' in base


def chat_completion(messages):
    """
    调用大模型进行对话补全
    :param messages: [{"role": "user/assistant/system", "content": "..."}]
    :return: 助手回复文本
    """
    cfg = _get_llm_config()
    if not cfg['api_key'] and not _is_local_llm(cfg['api_base']):
        raise LLMError('未配置大模型 API Key，请在 server/.env 中设置 LLM_API_KEY 并保存')

    url = f"{cfg['api_base']}/chat/completions"

    payload = {
        'model': cfg['model'],
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 800,
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
            raise LLMError(_friendly_error(msg))

        return data['choices'][0]['message']['content'].strip()
    except requests.Timeout:
        raise LLMError('大模型响应超时，请稍后重试')
    except requests.RequestException as e:
        raise LLMError(f'无法连接大模型服务：{e}')
