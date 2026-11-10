"""
RAG 检索工具
从知识库中检索与用户问题最相关的文本片段，构建增强上下文
"""
import json
import math

from config import Config
from utils.db import execute_query
from utils.embedding import get_embedding, EmbeddingError


def _cosine_similarity(a, b):
    """计算两个向量的余弦相似度"""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_similar(query, top_k=None):
    """
    在知识库中检索与查询最相似的文本块
    :param query: 查询文本
    :param top_k: 返回条数，默认使用 Config.RAG_TOP_K
    :return: [{"id": int, "content": str, "title": str, "source_type": str, "metadata": dict, "similarity": float}, ...]
    """
    if not Config.RAG_ENABLED:
        return []

    if top_k is None:
        top_k = Config.RAG_TOP_K

    try:
        query_embedding = get_embedding(query)
    except EmbeddingError as e:
        print(f"[RAG] 查询向量化失败: {e}")
        return []

    # 加载所有知识块
    try:
        rows = execute_query(
            'SELECT id, source_type, source_id, title, content, embedding, metadata '
            'FROM knowledge_chunks ORDER BY id'
        )
    except Exception as e:
        print(f"[RAG] 加载知识库失败: {e}")
        return []

    if not rows:
        return []

    # 计算余弦相似度并排序
    results = []
    for row in rows:
        try:
            stored_embedding = json.loads(row['embedding']) if isinstance(row['embedding'], str) else row['embedding']
        except (json.JSONDecodeError, TypeError):
            continue

        similarity = _cosine_similarity(query_embedding, stored_embedding)
        results.append({
            'id': row['id'],
            'content': row['content'],
            'title': row['title'] or '',
            'source_type': row['source_type'],
            'metadata': json.loads(row['metadata']) if isinstance(row.get('metadata'), str) else (row.get('metadata') or {}),
            'similarity': round(similarity, 4),
        })

    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]


def build_rag_context_from_results(results):
    """由检索结果构建增强上下文；无结果时返回 None。"""
    if not results:
        return None

    lines = ['【相关知识库信息】']
    lines.append('以下是从心理健康知识库中检索到的相关信息，请参考这些内容回答用户的问题：')
    lines.append('')

    for r in results:
        source_label = r['title'] if r['title'] else f"{r['source_type']}#{r['id']}"
        lines.append(f'--- {source_label}（相关度: {r["similarity"]}）---')
        lines.append(r['content'])
        lines.append('')

    return '\n'.join(lines)


def build_rag_sources_from_results(results):
    """由检索结果构建前端来源列表。"""
    if not results:
        return []

    sources = []
    for r in results:
        content = r['content']
        first_line = content.split('\n')[0].strip()
        summary = first_line if len(first_line) <= 80 else first_line[:77] + '...'
        sources.append({
            'title': r['title'],
            'summary': summary,
            'similarity': r['similarity'],
            'source_type': r['source_type'],
        })

    return sources


def build_rag_context(query, top_k=None):
    """
    构建 RAG 增强上下文文本
    :param query: 用户查询
    :param top_k: 检索条数
    :return: 格式化的上下文字符串，无结果时返回 None
    """
    return build_rag_context_from_results(search_similar(query, top_k))


def build_rag_sources(query, top_k=None):
    """
    构建 RAG 检索来源（供前端展示）
    :param query: 用户查询
    :param top_k: 检索条数
    :return: [{"title": str, "summary": str, "similarity": float}, ...]
    """
    return build_rag_sources_from_results(search_similar(query, top_k))