"""
LangGraph 状态机：数据获取 → 清洗 → 分析 → 可视化 → 报告
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.state import AgentState, append_step
from agents.nodes import (
    fetch_node,
    clean_node,
    analyze_node,
    visualize_node,
    report_node,
)

AVAILABLE_DATASETS = [
    {'key': 'users', 'label': '用户数据'},
    {'key': 'scale_records', 'label': '心理测评记录'},
    {'key': 'mood', 'label': '心情日记'},
    {'key': 'appointments', 'label': '咨询预约'},
    {'key': 'consultations', 'label': '在线咨询'},
    {'key': 'tree_hole', 'label': '栖心树洞'},
    {'key': 'articles', 'label': '心理文章'},
]


def _build_graph():
    """构建并编译 LangGraph 工作流"""
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as e:
        raise RuntimeError(
            '未安装 langgraph，请在 server 目录执行：pip install -r requirements.txt'
        ) from e

    workflow = StateGraph(AgentState)
    workflow.add_node('fetch', fetch_node)
    workflow.add_node('clean', clean_node)
    workflow.add_node('analyze', analyze_node)
    workflow.add_node('visualize', visualize_node)
    workflow.add_node('report', report_node)

    workflow.add_edge(START, 'fetch')
    workflow.add_edge('fetch', 'clean')
    workflow.add_edge('clean', 'analyze')
    workflow.add_edge('analyze', 'visualize')
    workflow.add_edge('visualize', 'report')
    workflow.add_edge('report', END)

    return workflow.compile()


_compiled = None


def get_graph():
    global _compiled
    if _compiled is None:
        _compiled = _build_graph()
    return _compiled


def run_analysis_agent(
    topic: str = '心屿平台心理健康运营数据分析报告',
    datasets: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    运行多智能体协作流水线
    :return: 含 steps / analysis / charts / report_md 的结果字典
    """
    valid_keys = {d['key'] for d in AVAILABLE_DATASETS}
    selected = [d for d in (datasets or list(valid_keys)) if d in valid_keys]
    if not selected:
        selected = list(valid_keys)

    run_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:6]
    initial: AgentState = {
        'topic': (topic or '').strip() or '心屿平台心理健康运营数据分析报告',
        'datasets': selected,
        'raw_data': {},
        'cleaned_data': {},
        'analysis': {},
        'charts': [],
        'report_md': '',
        'steps': [],
        'error': None,
        'run_id': run_id,
    }
    initial['steps'] = append_step(
        initial,
        '编排器',
        'running',
        f'启动流水线，数据集：{", ".join(selected)}',
    )

    try:
        graph = get_graph()
        final = graph.invoke(initial)
    except Exception as e:
        initial['error'] = str(e)
        initial['steps'] = append_step(initial, '编排器', 'error', f'流水线失败：{e}')
        # 兜底：即使 LangGraph 未安装，也串行执行节点
        if 'langgraph' in str(e).lower() or '未安装' in str(e):
            state = initial
            for node in (fetch_node, clean_node, analyze_node, visualize_node, report_node):
                state = node(state)
            final = state
            final['steps'] = append_step(
                final, '编排器', 'warn', 'LangGraph 不可用，已降级为顺序执行'
            )
        else:
            raise

    final['steps'] = append_step(final, '编排器', 'done', '多智能体协作完成')
    return {
        'run_id': final.get('run_id'),
        'topic': final.get('topic'),
        'datasets': final.get('datasets'),
        'steps': final.get('steps') or [],
        'analysis': final.get('analysis') or {},
        'charts': final.get('charts') or [],
        'report_md': final.get('report_md') or '',
        'report_url': f"/static/media/agent_reports/{final.get('run_id')}_report.md",
        'error': final.get('error'),
    }
