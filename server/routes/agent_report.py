"""
多智能体协作 - 自动化数据分析与报告生成 API（管理员）
"""
from flask import Blueprint, request

from agents.graph import AVAILABLE_DATASETS, run_analysis_agent
from utils.auth import login_required
from utils.response import success, error

agent_report_bp = Blueprint('agent_report', __name__, url_prefix='/api/admin/agent')


@agent_report_bp.route('/datasets', methods=['GET'])
@login_required(roles=['admin'])
def list_datasets():
    """可选数据集清单与流水线说明"""
    return success({
        'datasets': AVAILABLE_DATASETS,
        'pipeline': [
            {'id': 'fetch', 'name': '数据获取Agent', 'desc': '从平台数据库拉取选定业务数据'},
            {'id': 'clean', 'name': '数据清洗Agent', 'desc': '去空、类型规范与异常值过滤'},
            {'id': 'analyze', 'name': '数据分析Agent', 'desc': '统计汇总与关键指标计算'},
            {'id': 'visualize', 'name': '可视化Agent', 'desc': '生成柱状图等运营图表'},
            {'id': 'report', 'name': '报告生成Agent', 'desc': '基于 LangChain 调用大模型撰写 Markdown 报告'},
        ],
        'engine': 'LangChain + LangGraph',
    })


@agent_report_bp.route('/run', methods=['POST'])
@login_required(roles=['admin'])
def run_agent():
    """
    启动多智能体协作流水线
    请求体: { topic?: string, datasets?: string[] }
    """
    data = request.get_json(silent=True) or {}
    topic = (data.get('topic') or '').strip()
    datasets = data.get('datasets')

    if datasets is not None and not isinstance(datasets, list):
        return error('datasets 须为数组')

    try:
        result = run_analysis_agent(topic=topic, datasets=datasets)
        return success(result, '多智能体协作完成')
    except Exception as e:
        return error(f'多智能体协作失败：{e}', 500)
