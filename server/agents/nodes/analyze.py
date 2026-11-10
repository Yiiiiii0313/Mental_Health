"""
数据分析 Agent：统计汇总与关键指标
"""
from collections import Counter
from statistics import mean, median

from agents.state import AgentState, append_step


def _analyze_users(rows):
    roles = Counter(r.get('role') for r in rows)
    status = Counter(r.get('status') for r in rows)
    return {
        'total': len(rows),
        'by_role': dict(roles),
        'active': status.get(1, 0),
        'disabled': status.get(0, 0),
    }


def _analyze_scales(rows):
    by_scale = Counter(r.get('scale_name') or f"量表{r.get('scale_id')}" for r in rows)
    by_level = Counter(r.get('result_level') or '未知' for r in rows)
    scores = [r['total_score'] for r in rows if isinstance(r.get('total_score'), (int, float))]
    return {
        'total': len(rows),
        'by_scale': dict(by_scale),
        'by_level': dict(by_level),
        'score_avg': round(mean(scores), 2) if scores else None,
        'score_median': round(median(scores), 2) if scores else None,
        'score_max': max(scores) if scores else None,
        'score_min': min(scores) if scores else None,
    }


def _analyze_mood(rows):
    levels = Counter(r.get('mood_level') for r in rows)
    vals = [r['mood_level'] for r in rows if isinstance(r.get('mood_level'), int)]
    tag_counter = Counter()
    for r in rows:
        tags = r.get('tags') or ''
        for t in str(tags).split(','):
            t = t.strip()
            if t:
                tag_counter[t] += 1
    return {
        'total': len(rows),
        'by_level': {str(k): v for k, v in levels.items()},
        'avg_level': round(mean(vals), 2) if vals else None,
        'top_tags': dict(tag_counter.most_common(8)),
    }


def _analyze_appointments(rows):
    by_status = Counter(r.get('status') or 'unknown' for r in rows)
    return {
        'total': len(rows),
        'by_status': dict(by_status),
    }


def _analyze_consultations(rows):
    by_status = Counter(r.get('status') or 'unknown' for r in rows)
    return {
        'total': len(rows),
        'by_status': dict(by_status),
    }


def _analyze_tree_hole(rows):
    anon = sum(1 for r in rows if r.get('is_anonymous'))
    replies = [r.get('reply_count') or 0 for r in rows]
    return {
        'total': len(rows),
        'anonymous_ratio': round(anon / len(rows), 3) if rows else 0,
        'avg_replies': round(mean(replies), 2) if replies else 0,
    }


def _analyze_articles(rows):
    by_cat = Counter(r.get('category') or '未分类' for r in rows)
    views = [r.get('view_count') or 0 for r in rows]
    return {
        'total': len(rows),
        'by_category': dict(by_cat),
        'total_views': sum(views),
        'avg_views': round(mean(views), 1) if views else 0,
    }


ANALYZERS = {
    'users': _analyze_users,
    'scale_records': _analyze_scales,
    'mood': _analyze_mood,
    'appointments': _analyze_appointments,
    'consultations': _analyze_consultations,
    'tree_hole': _analyze_tree_hole,
    'articles': _analyze_articles,
}


def analyze_node(state: AgentState) -> AgentState:
    cleaned = state.get('cleaned_data') or {}
    analysis = {}
    highlights = []

    for key, payload in cleaned.items():
        fn = ANALYZERS.get(key)
        rows = payload.get('rows') or []
        if not fn:
            analysis[key] = {'label': payload.get('label', key), 'total': len(rows)}
            continue
        stats = fn(rows)
        stats['label'] = payload.get('label', key)
        analysis[key] = stats
        highlights.append(f"{stats['label']}共{stats.get('total', 0)}条")

    # 综合洞察（规则层，供报告 Agent 引用）
    insights = []
    if 'scale_records' in analysis:
        s = analysis['scale_records']
        if s.get('by_level'):
            top_level = max(s['by_level'].items(), key=lambda x: x[1])
            insights.append(f"测评结果中「{top_level[0]}」出现最多（{top_level[1]}次）")
        if s.get('score_avg') is not None:
            insights.append(f"测评平均分 {s['score_avg']}（中位数 {s.get('score_median')}）")
    if 'mood' in analysis and analysis['mood'].get('avg_level') is not None:
        insights.append(f"心情日记平均等级 {analysis['mood']['avg_level']}（1低落~5开心）")
    if 'appointments' in analysis:
        pending = analysis['appointments'].get('by_status', {}).get('pending', 0)
        if pending:
            insights.append(f"当前待确认预约 {pending} 条，建议及时处理")
    if 'users' in analysis:
        insights.append(
            f"用户构成：学生{analysis['users'].get('by_role', {}).get('student', 0)}人，"
            f"咨询师{analysis['users'].get('by_role', {}).get('counselor', 0)}人"
        )

    analysis['_meta'] = {
        'highlights': highlights,
        'insights': insights,
        'dataset_count': len([k for k in analysis if not k.startswith('_')]),
    }

    return {
        **state,
        'analysis': analysis,
        'steps': append_step(
            state,
            '数据分析Agent',
            'done',
            '分析完成：' + ('；'.join(highlights) if highlights else '无有效样本'),
        ),
    }
