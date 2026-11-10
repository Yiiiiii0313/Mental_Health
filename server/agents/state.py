"""
LangGraph 共享状态定义
"""
from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """多智能体协作流水线状态"""
    topic: str
    datasets: List[str]
    raw_data: Dict[str, Any]
    cleaned_data: Dict[str, Any]
    analysis: Dict[str, Any]
    charts: List[Dict[str, Any]]
    report_md: str
    steps: List[Dict[str, Any]]
    error: Optional[str]
    run_id: str


def append_step(state: AgentState, agent: str, status: str, message: str) -> List[Dict[str, Any]]:
    """追加一条流水线步骤日志"""
    from datetime import datetime
    steps = list(state.get('steps') or [])
    steps.append({
        'agent': agent,
        'status': status,
        'message': message,
        'at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })
    return steps
