"""
报告生成 Agent：调用 LangChain LLM 撰写分析报告（失败则回退模板）
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from agents.state import AgentState, append_step

_ENV_PATH = Path(__file__).resolve().parents[2] / '.env'


def _build_fallback_report(state: AgentState) -> str:
    topic = state.get('topic') or '平台运营数据分析'
    analysis = state.get('analysis') or {}
    meta = analysis.get('_meta') or {}
    insights = meta.get('insights') or []
    charts = state.get('charts') or []

    lines = [
        f'# {topic}',
        '',
        '> 由心屿「多智能体协作」系统自动生成（模板回退模式）',
        '',
        '## 一、执行摘要',
        '',
    ]
    if insights:
        for i in insights:
            lines.append(f'- {i}')
    else:
        lines.append('- 当前选定数据集样本量有限，建议积累更多业务数据后再分析。')

    lines.extend(['', '## 二、分项数据洞察', ''])
    for key, stats in analysis.items():
        if key.startswith('_'):
            continue
        label = stats.get('label', key)
        lines.append(f'### {label}')
        lines.append('')
        lines.append('```json')
        # 去掉过大的嵌套
        dump = {k: v for k, v in stats.items() if k != 'label'}
        lines.append(json.dumps(dump, ensure_ascii=False, indent=2))
        lines.append('```')
        lines.append('')

    if charts:
        lines.extend(['## 三、可视化图表', ''])
        for c in charts:
            lines.append(f"- {c.get('title')}：`{c.get('url')}`")
        lines.append('')

    lines.extend([
        '## 四、管理建议',
        '',
        '1. 关注测评结果中偏高风险等级的学生，及时安排咨询跟进。',
        '2. 结合心情日记与预约数据，识别压力高峰时段。',
        '3. 持续运营心理文章与放松训练内容，提升平台黏性。',
        '4. 定期复跑本多智能体流水线，形成周报/月报机制。',
        '',
        '---',
        '*报告仅供校园心理服务管理参考，不能替代专业临床诊断。*',
    ])
    return '\n'.join(lines)


def _llm_report(state: AgentState) -> str:
    load_dotenv(_ENV_PATH, override=True)
    api_key = (os.environ.get('LLM_API_KEY') or '').strip()
    api_base = (os.environ.get('LLM_API_BASE') or 'https://api.deepseek.com/v1').rstrip('/')
    model = os.environ.get('LLM_MODEL') or 'deepseek-chat'
    timeout = int(os.environ.get('LLM_TIMEOUT') or 120)

    is_local = 'localhost' in api_base.lower() or '127.0.0.1' in api_base.lower()
    if not api_key and not is_local:
        raise RuntimeError('未配置 LLM_API_KEY')

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = ChatOpenAI(
        model=model,
        api_key=api_key or 'ollama',
        base_url=api_base,
        temperature=0.4,
        timeout=timeout,
        max_tokens=1800,
    )

    analysis = state.get('analysis') or {}
    charts = state.get('charts') or []
    topic = state.get('topic') or '平台运营数据分析'

    payload = {
        'topic': topic,
        'analysis': {k: v for k, v in analysis.items()},
        'charts': [{'title': c.get('title'), 'url': c.get('url')} for c in charts],
    }

    system = (
        '你是校园心理健康服务平台的数据分析顾问。'
        '请根据提供的统计 JSON，用中文撰写一份专业、简洁的管理分析报告。'
        '使用 Markdown，包含：执行摘要、分项洞察、风险提示、可执行建议。'
        '不要编造数据中不存在的数字；语气客观、关怀。'
    )
    human = (
        f'请基于以下多智能体分析结果撰写报告：\n'
        f'```json\n{json.dumps(payload, ensure_ascii=False)[:12000]}\n```'
    )

    resp = llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content=human),
    ])
    content = getattr(resp, 'content', None) or str(resp)
    if not content.strip():
        raise RuntimeError('模型返回空内容')
    return content.strip()


def report_node(state: AgentState) -> AgentState:
    mode = 'llm'
    try:
        report_md = _llm_report(state)
        msg = '已调用大模型生成分析报告'
    except Exception as e:
        mode = 'fallback'
        report_md = _build_fallback_report(state)
        msg = f'LLM 不可用，已使用模板报告（{e}）'

    # 落盘报告
    run_id = state.get('run_id') or 'run'
    out_dir = Path(__file__).resolve().parents[2] / 'static' / 'media' / 'agent_reports'
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f'{run_id}_report.md'
    report_path.write_text(report_md, encoding='utf-8')

    return {
        **state,
        'report_md': report_md,
        'steps': append_step(
            state,
            '报告生成Agent',
            'done' if mode == 'llm' else 'warn',
            msg,
        ),
    }
