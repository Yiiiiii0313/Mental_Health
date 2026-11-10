"""
可视化 Agent：生成图表并保存到静态目录
"""
from pathlib import Path

from agents.state import AgentState, append_step

OUT_DIR = Path(__file__).resolve().parents[2] / 'static' / 'media' / 'agent_reports'


def _setup_matplotlib():
    """延迟导入，避免未安装 matplotlib 时整个 Flask 无法启动"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    return plt


def _bar_chart(title: str, data: dict, filename: str, xlabel='类别', ylabel='数量'):
    if not data:
        return None
    plt = _setup_matplotlib()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / filename
    labels = [str(k) for k in data.keys()]
    values = list(data.values())
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    colors = ['#456a5d', '#6ba888', '#7b9fd4', '#e88fa0', '#f0a030', '#5eb3c5', '#d4c5f0']
    ax.bar(labels, values, color=[colors[i % len(colors)] for i in range(len(labels))])
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=25, ha='right')
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return {
        'title': title,
        'filename': filename,
        'url': f'/static/media/agent_reports/{filename}',
        'path': str(path),
    }


def visualize_node(state: AgentState) -> AgentState:
    analysis = state.get('analysis') or {}
    run_id = state.get('run_id') or 'run'
    charts = []

    try:
        _setup_matplotlib()
    except ImportError:
        return {
            **state,
            'charts': [],
            'steps': append_step(
                state,
                '可视化Agent',
                'warn',
                '未安装 matplotlib，已跳过图表。请在当前 Python 环境执行：pip install matplotlib',
            ),
        }

    try:
        if 'users' in analysis and analysis['users'].get('by_role'):
            chart = _bar_chart(
                '用户角色分布',
                analysis['users']['by_role'],
                f'{run_id}_users_role.png',
                xlabel='角色',
            )
            if chart:
                charts.append(chart)

        if 'scale_records' in analysis and analysis['scale_records'].get('by_level'):
            chart = _bar_chart(
                '测评结果等级分布',
                analysis['scale_records']['by_level'],
                f'{run_id}_scale_level.png',
                xlabel='结果等级',
            )
            if chart:
                charts.append(chart)

        if 'scale_records' in analysis and analysis['scale_records'].get('by_scale'):
            chart = _bar_chart(
                '各量表测评次数',
                analysis['scale_records']['by_scale'],
                f'{run_id}_scale_count.png',
                xlabel='量表',
            )
            if chart:
                charts.append(chart)

        if 'mood' in analysis and analysis['mood'].get('by_level'):
            chart = _bar_chart(
                '心情等级分布',
                analysis['mood']['by_level'],
                f'{run_id}_mood_level.png',
                xlabel='心情等级(1-5)',
            )
            if chart:
                charts.append(chart)

        if 'appointments' in analysis and analysis['appointments'].get('by_status'):
            chart = _bar_chart(
                '预约状态分布',
                analysis['appointments']['by_status'],
                f'{run_id}_appointments_status.png',
                xlabel='状态',
            )
            if chart:
                charts.append(chart)

        if 'articles' in analysis and analysis['articles'].get('by_category'):
            chart = _bar_chart(
                '文章分类分布',
                analysis['articles']['by_category'],
                f'{run_id}_articles_category.png',
                xlabel='分类',
            )
            if chart:
                charts.append(chart)

        return {
            **state,
            'charts': charts,
            'steps': append_step(
                state,
                '可视化Agent',
                'done',
                f'已生成 {len(charts)} 张图表' if charts else '样本不足，未生成图表',
            ),
        }
    except Exception as e:
        return {
            **state,
            'charts': charts,
            'steps': append_step(state, '可视化Agent', 'warn', f'图表生成部分失败：{e}'),
        }
