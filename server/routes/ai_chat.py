"""
AI心理助手路由模块
接入大模型提供智能对话
"""
import json

from flask import Blueprint, request
from utils.db import execute_query, execute_update
from utils.auth import login_required
from utils.response import success, error
from utils.llm import SYSTEM_PROMPT, chat_completion, LLMError
from config import Config

ai_chat_bp = Blueprint('ai_chat', __name__, url_prefix='/api/ai-chat')

_table_ready = None
_rag_column_ready = False


def _ensure_tables():
    """检查 AI 对话表是否存在"""
    global _table_ready
    if _table_ready is None:
        try:
            execute_query('SELECT 1 FROM ai_chat_sessions LIMIT 1', fetch_one=True)
            _table_ready = True
        except Exception:
            _table_ready = False
    if not _table_ready:
        from utils.db import DatabaseError
        raise DatabaseError(
            'AI对话表未创建，请执行 server/sql/init.sql 或 python setup_ai_chat.py',
            1146
        )
    _ensure_rag_column()


def _ensure_rag_column():
    """为消息表补充 rag_sources 列（幂等）"""
    global _rag_column_ready
    if _rag_column_ready:
        return
    try:
        cols = execute_query(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='ai_chat_messages' AND COLUMN_NAME='rag_sources'",
            (Config.DB_NAME,)
        )
        if not cols:
            execute_update(
                'ALTER TABLE ai_chat_messages '
                'ADD COLUMN rag_sources JSON NULL COMMENT \'RAG检索来源\' AFTER content'
            )
        _rag_column_ready = True
    except Exception as e:
        print(f'[RAG] 补充 rag_sources 列失败: {e}')


def _parse_rag_sources(raw):
    if not raw:
        return []
    if isinstance(raw, (list, dict)):
        return raw if isinstance(raw, list) else []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except (TypeError, json.JSONDecodeError):
        return []



@ai_chat_bp.route('/status', methods=['GET'])
@login_required()
def rag_status():
    """返回 AI 助手 / RAG 状态（供前端角标展示）"""
    chunk_count = 0
    try:
        row = execute_query('SELECT COUNT(*) AS c FROM knowledge_chunks', fetch_one=True)
        chunk_count = int(row['c']) if row else 0
    except Exception:
        pass
    return success({
        'rag_enabled': Config.RAG_ENABLED,
        'rag_ready': Config.RAG_ENABLED and chunk_count > 0,
        'chunk_count': chunk_count,
    })


@ai_chat_bp.route('/sessions', methods=['GET'])
@login_required()
def list_sessions():
    """获取当前用户的 AI 对话会话列表"""
    _ensure_tables()
    user_id = request.current_user['id']
    sessions = execute_query(
        'SELECT id, title, created_at, updated_at FROM ai_chat_sessions '
        'WHERE user_id = %s ORDER BY updated_at DESC LIMIT 50',
        (user_id,)
    )
    return success(sessions)


@ai_chat_bp.route('/sessions', methods=['POST'])
@login_required()
def create_session():
    """创建新的 AI 对话会话"""
    _ensure_tables()
    data = request.get_json() or {}
    title = data.get('title', 'AI心理助手').strip() or 'AI心理助手'
    user_id = request.current_user['id']

    session_id = execute_update(
        'INSERT INTO ai_chat_sessions (user_id, title) VALUES (%s, %s)',
        (user_id, title)
    )

    # 插入欢迎语
    welcome = (
        '你好，我是AI心理助手小暖 🌿\n'
        '你可以和我聊聊最近的心情、学业压力、人际关系等困扰，我会认真倾听并给你建议。\n'
        '如需专业帮助，也可以随时预约校内心理咨询师哦。'
    )
    execute_update(
        'INSERT INTO ai_chat_messages (session_id, role, content) VALUES (%s, %s, %s)',
        (session_id, 'assistant', welcome)
    )

    return success({'session_id': session_id, 'title': title}, '会话创建成功')


@ai_chat_bp.route('/sessions/<int:session_id>/messages', methods=['GET'])
@login_required()
def get_messages(session_id):
    """获取 AI 会话消息历史"""
    _ensure_tables()
    session = _get_user_session(session_id)
    if not session:
        return error('会话不存在')

    messages = execute_query(
        'SELECT id, role, content, rag_sources, created_at FROM ai_chat_messages '
        'WHERE session_id = %s ORDER BY created_at ASC',
        (session_id,)
    )
    for msg in messages:
        msg['rag_sources'] = _parse_rag_sources(msg.pop('rag_sources', None))
    return success(messages)


@ai_chat_bp.route('/sessions/<int:session_id>/messages', methods=['POST'])
@login_required()
def send_message(session_id):
    """
    发送消息并获取 AI 回复
    请求体: { content }
    """
    _ensure_tables()
    session = _get_user_session(session_id)
    if not session:
        return error('会话不存在')

    data = request.get_json()
    content = (data.get('content') or '').strip()
    if not content:
        return error('消息内容不能为空')

    # 保存用户消息
    execute_update(
        'INSERT INTO ai_chat_messages (session_id, role, content) VALUES (%s, %s, %s)',
        (session_id, 'user', content)
    )

    # 首条用户消息时，用内容摘要更新会话标题
    user_count = execute_query(
        'SELECT COUNT(*) as c FROM ai_chat_messages WHERE session_id=%s AND role="user"',
        (session_id,), fetch_one=True
    )['c']
    if user_count == 1:
        short_title = content[:20] + ('...' if len(content) > 20 else '')
        execute_update(
            'UPDATE ai_chat_sessions SET title=%s WHERE id=%s',
            (short_title, session_id)
        )

    # 构建对话上下文（最近20条）
    history = execute_query(
        'SELECT role, content FROM ai_chat_messages WHERE session_id=%s '
        'ORDER BY created_at ASC LIMIT 20',
        (session_id,)
    )
    llm_messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

    # === RAG 知识检索（失败不影响正常对话） ===
    rag_context = None
    rag_sources = []
    if Config.RAG_ENABLED:
        try:
            from utils.rag import search_similar, build_rag_context_from_results, build_rag_sources_from_results
            hits = search_similar(content, top_k=Config.RAG_TOP_K)
            rag_context = build_rag_context_from_results(hits)
            rag_sources = build_rag_sources_from_results(hits)
        except Exception as e:
            print(f'[RAG] 知识检索失败: {e}')

    if rag_context:
        llm_messages.append({'role': 'system', 'content': rag_context})
        print(f'[RAG] 已注入 {len(rag_sources)} 条知识来源')
    elif Config.RAG_ENABLED:
        print('[RAG] 未检索到可用知识（或嵌入失败），本次按普通对话回复')

    for msg in history:
        llm_messages.append({'role': msg['role'], 'content': msg['content']})

    try:
        reply = chat_completion(llm_messages)
    except LLMError as e:
        return error(str(e))

    execute_update(
        'INSERT INTO ai_chat_messages (session_id, role, content, rag_sources) VALUES (%s, %s, %s, %s)',
        (
            session_id,
            'assistant',
            reply,
            json.dumps(rag_sources, ensure_ascii=False) if rag_sources else None,
        )
    )
    execute_update(
        'UPDATE ai_chat_sessions SET updated_at = NOW() WHERE id = %s',
        (session_id,)
    )

    return success({
        'reply': reply,
        'rag_used': bool(rag_context),
        'rag_sources': rag_sources,
    }, '发送成功')


@ai_chat_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@login_required()
def delete_session(session_id):
    """删除 AI 对话会话"""
    _ensure_tables()
    session = _get_user_session(session_id)
    if not session:
        return error('会话不存在')

    execute_update('DELETE FROM ai_chat_sessions WHERE id = %s', (session_id,))
    return success(message='会话已删除')


def _get_user_session(session_id):
    """获取属于当前用户的会话"""
    return execute_query(
        'SELECT * FROM ai_chat_sessions WHERE id = %s AND user_id = %s',
        (session_id, request.current_user['id']),
        fetch_one=True
    )
