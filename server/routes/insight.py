"""
心理健康洞察路由
综合风险评分与趋势预测
"""
from flask import Blueprint, request
from utils.db import execute_query
from utils.auth import login_required
from utils.response import success
from utils.risk_analysis import compute_risk_insight

insight_bp = Blueprint('insight', __name__, url_prefix='/api/insight')


@insight_bp.route('/risk', methods=['GET'])
@login_required()
def risk_insight():
    """获取当前用户综合心理健康风险评分与趋势预测"""
    user_id = request.current_user['id']

    scale_records = execute_query(
        'SELECT sr.scale_id, sr.total_score, sr.result_level, sr.created_at, s.name as scale_name '
        'FROM scale_records sr LEFT JOIN scales s ON sr.scale_id = s.id '
        'WHERE sr.user_id = %s ORDER BY sr.created_at ASC',
        (user_id,)
    )

    mood_entries = execute_query(
        'SELECT mood_level, created_at FROM mood_diaries '
        'WHERE user_id = %s ORDER BY created_at ASC',
        (user_id,)
    )

    result = compute_risk_insight(scale_records, mood_entries)
    return success(result)
