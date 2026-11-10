"""
数据清洗 Agent：去空、类型规范、异常值标记
"""
from collections import Counter

from agents.state import AgentState, append_step


def _clean_rows(key: str, rows: list) -> dict:
    cleaned = []
    dropped = 0
    for row in rows:
        if not isinstance(row, dict):
            dropped += 1
            continue
        item = {k: v for k, v in row.items() if v is not None and v != ''}
        if not item:
            dropped += 1
            continue

        if key == 'mood' and 'mood_level' in item:
            try:
                level = int(item['mood_level'])
                if level < 1 or level > 5:
                    dropped += 1
                    continue
                item['mood_level'] = level
            except (TypeError, ValueError):
                dropped += 1
                continue

        if key == 'scale_records' and 'total_score' in item:
            try:
                item['total_score'] = float(item['total_score'])
            except (TypeError, ValueError):
                dropped += 1
                continue

        if key == 'appointments' and 'status' in item:
            item['status'] = str(item['status']).strip().lower()

        cleaned.append(item)

    return {'rows': cleaned, 'kept': len(cleaned), 'dropped': dropped}


def clean_node(state: AgentState) -> AgentState:
    raw = state.get('raw_data') or {}
    cleaned_data = {}
    notes = []

    for key, payload in raw.items():
        rows = payload.get('rows') or []
        result = _clean_rows(key, rows)
        cleaned_data[key] = {
            'label': payload.get('label', key),
            'rows': result['rows'],
            'count': result['kept'],
            'dropped': result['dropped'],
        }
        notes.append(f"{payload.get('label', key)}: 保留{result['kept']}，剔除{result['dropped']}")

    return {
        **state,
        'cleaned_data': cleaned_data,
        'steps': append_step(
            state,
            '数据清洗Agent',
            'done',
            '清洗完成：' + ('；'.join(notes) if notes else '无数据'),
        ),
    }
