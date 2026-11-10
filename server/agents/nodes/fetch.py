"""
数据获取 Agent：从平台 MySQL 拉取选定数据集
"""
from agents.state import AgentState, append_step
from utils.db import execute_query

DATASET_QUERIES = {
    'users': (
        '用户数据',
        'SELECT id, username, role, gender, status, created_at FROM users ORDER BY id',
    ),
    'scale_records': (
        '心理测评记录',
        'SELECT sr.id, sr.user_id, sr.scale_id, s.name AS scale_name, sr.total_score, '
        'sr.result_level, sr.created_at '
        'FROM scale_records sr LEFT JOIN scales s ON sr.scale_id = s.id '
        'ORDER BY sr.created_at DESC LIMIT 500',
    ),
    'mood': (
        '心情日记',
        'SELECT id, user_id, mood_level, tags, created_at FROM mood_diaries '
        'ORDER BY created_at DESC LIMIT 500',
    ),
    'appointments': (
        '咨询预约',
        'SELECT id, student_id, counselor_id, appointment_date, time_slot, status, created_at '
        'FROM appointments ORDER BY created_at DESC LIMIT 500',
    ),
    'consultations': (
        '在线咨询',
        'SELECT id, student_id, counselor_id, title, status, created_at, updated_at '
        'FROM consultations ORDER BY updated_at DESC LIMIT 300',
    ),
    'tree_hole': (
        '栖心树洞',
        'SELECT id, user_id, is_anonymous, status, reply_count, created_at '
        'FROM tree_hole_posts ORDER BY created_at DESC LIMIT 300',
    ),
    'articles': (
        '心理文章',
        'SELECT id, title, category, view_count, like_count, status, created_at '
        'FROM articles ORDER BY created_at DESC LIMIT 200',
    ),
}


def fetch_node(state: AgentState) -> AgentState:
    datasets = state.get('datasets') or list(DATASET_QUERIES.keys())
    raw = {}
    labels = []
    errors = []

    for key in datasets:
        meta = DATASET_QUERIES.get(key)
        if not meta:
            continue
        label, sql = meta
        try:
            rows = execute_query(sql) or []
            # 规范化日期等不可 JSON 序列化字段
            normalized = []
            for row in rows:
                item = {}
                for k, v in row.items():
                    if hasattr(v, 'isoformat'):
                        item[k] = v.isoformat(sep=' ', timespec='seconds')
                    else:
                        item[k] = v
                normalized.append(item)
            raw[key] = {'label': label, 'rows': normalized, 'count': len(normalized)}
            labels.append(f'{label}({len(normalized)})')
        except Exception as e:
            raw[key] = {'label': label, 'rows': [], 'count': 0, 'error': str(e)}
            errors.append(f'{label}: {e}')

    msg = '已获取：' + ('、'.join(labels) if labels else '无数据')
    if errors:
        msg += '；部分失败：' + '；'.join(errors)

    return {
        **state,
        'raw_data': raw,
        'steps': append_step(state, '数据获取Agent', 'done' if not errors else 'warn', msg),
        'error': None,
    }
