"""
心理量表路由模块
提供量表列表、题目获取、提交测评、查看历史记录
"""
import json
from flask import Blueprint, request
from utils.db import execute_query, execute_update
from utils.auth import login_required
from utils.response import success, error
from utils.notify import create_notification

scale_bp = Blueprint('scale', __name__, url_prefix='/api/scales')

# 量表评分规则：(最低分, 最高分, 等级, 简要描述, 具体分析, 建议)
SCALE_RULES = {
    1: {  # PHQ-9 抑郁
        'ranges': [
            (0, 4, '无抑郁',
             '您的情绪状态良好，请继续保持积极的生活态度。',
             '测评结果显示，您近期几乎未出现明显的抑郁症状。情绪较为稳定，对日常学习与生活能保持适度的兴趣与动力，睡眠、食欲和精力方面也未见显著异常。这说明您当前的心理弹性较好，具备较好的情绪调节基础。',
             '1. 保持规律作息与适度运动，巩固现有良好状态；\n2. 继续维护支持性人际关系，与同学、朋友保持良好沟通；\n3. 可定期使用本平台心情日记功能关注自身情绪波动；\n4. 若未来出现持续情绪低落，可再次测评或寻求咨询支持。'),
            (5, 9, '轻度抑郁',
             '您可能存在轻度抑郁症状，建议关注情绪变化，适当放松。',
             '测评提示您近期可能存在轻度抑郁倾向，表现为偶尔的情绪低落、兴趣减退或精力不足。这类症状在学业压力较大的大学生群体中并不少见，通常与考试、人际关系或生活节奏变化有关。目前程度较轻，及时觉察和调节往往能有效缓解。',
             '1. 每天安排15–30分钟放松活动，如散步、听音乐或放松训练；\n2. 尝试记录心情日记，识别引发低落的具体情境；\n3. 保持规律睡眠，避免熬夜和过度使用电子设备；\n4. 若症状持续两周以上未见改善，建议预约心理咨询；\n5. 可使用本平台「放松训练」模块进行呼吸与正念练习。'),
            (10, 14, '中度抑郁',
             '您可能存在中度抑郁症状，建议寻求心理咨询帮助。',
             '测评显示您近期抑郁症状已达到中度水平，可能包括较明显的情绪低落、动力下降、注意力难以集中、睡眠或食欲改变等。这些症状可能已开始影响学习效率、社交意愿和日常生活质量。此时单纯依靠自我调节可能效果有限，专业支持会更有帮助。',
             '1. 建议尽快预约校内心理咨询师进行面对面评估与辅导；\n2. 向信任的家人、朋友或辅导员适度倾诉，获得情感支持；\n3. 减少自我批评，接纳当前状态，从小目标开始恢复日常节奏；\n4. 避免独处过久，适度参与轻度社交或户外活动；\n5. 若出现自伤念头，请立即联系心理援助热线或紧急求助。'),
            (15, 19, '中重度抑郁',
             '您可能存在中重度抑郁症状，请尽快联系心理咨询师。',
             '测评结果提示中重度抑郁症状，说明您可能正经历持续且显著的情绪困扰，如明显的无助感、强烈疲惫、兴趣严重丧失或反复出现负面自我评价。这种状态对学业和生活的干扰较大，需要及时的专业干预，不宜独自硬撑。',
             '1. 请尽快联系心理咨询师或心理中心，进行系统评估与干预；\n2. 告知身边可信赖的人您的状况，建立安全支持网络；\n3. 暂停过度自我要求，优先保证基本作息与饮食；\n4. 避免饮酒及滥用药物来应对情绪；\n5. 如有自伤或自杀想法，请立即拨打校内心理援助热线或前往医院急诊。'),
            (20, 27, '重度抑郁',
             '您可能存在重度抑郁症状，请立即寻求专业心理援助。',
             '测评显示重度抑郁症状，意味着您可能长期处于显著痛苦中，伴随严重的情绪崩溃、功能受损或绝望感。这是需要高度重视的心理健康信号，请务必在专业人士陪伴下制定安全与康复计划。',
             '1. 请立即联系心理咨询师、辅导员或前往专业机构求助，不要独自承受；\n2. 如有自伤、自杀计划或冲动，请立刻拨打急救/心理危机热线；\n3. 减少独处，让家人或室友知晓您需要陪伴；\n4. 在专业人士指导下考虑是否需要进一步医学评估；\n5. 您值得被帮助，求助是勇敢且正确的选择。'),
        ]
    },
    2: {  # GAD-7 焦虑
        'ranges': [
            (0, 4, '无焦虑',
             '您的焦虑水平正常，心理状态良好。',
             '测评表明您近期焦虑水平处于正常范围，对日常事务的担忧可控，身心紧张感不明显。您能够较好地应对一般性压力，这说明您的焦虑调节系统目前运行良好。',
             '1. 继续保持健康的生活方式与压力管理习惯；\n2. 考试季或任务密集期可提前规划，避免临时焦虑飙升；\n3. 学习基础放松技巧以备不时之需；\n4. 关注睡眠质量，它是情绪稳定的重要基础。'),
            (5, 9, '轻度焦虑',
             '您可能存在轻度焦虑，可尝试深呼吸、运动等方式缓解。',
             '测评提示轻度焦虑，您可能时常感到紧张、担忧或对某些事情过度思虑，但尚能完成日常任务。这种焦虑多与学业、社交或未来不确定性有关，通过自我调节和适度支持通常可以改善。',
             '1. 练习腹式呼吸、渐进式肌肉放松等技巧（见「放松训练」）；\n2. 每天安排30分钟有氧运动，有助于降低焦虑激素水平；\n3. 限制咖啡因摄入，尤其在下午和晚上；\n4. 将担忧写下来，区分「可解决的问题」与「无法控制的担忧」；\n5. 若焦虑持续加重，可考虑心理咨询。'),
            (10, 14, '中度焦虑',
             '您可能存在中度焦虑，建议寻求心理咨询。',
             '测评显示中度焦虑，您可能经常感到坐立不安、难以放松、注意力分散或伴有躯体反应（如心悸、胃部不适）。焦虑可能已明显干扰学习效率和睡眠质量，需要更系统的应对策略。',
             '1. 建议预约心理咨询，学习认知行为技巧管理焦虑；\n2. 建立稳定的作息与学习计划，减少因拖延带来的焦虑；\n3. 减少刷手机/刷短视频等加剧焦虑的行为；\n4. 与亲友分享感受，避免情绪内化；\n5. 如伴有严重失眠或恐慌发作，请及时告知咨询师。'),
            (15, 21, '重度焦虑',
             '您可能存在重度焦虑，请尽快联系心理咨询师。',
             '测评提示重度焦虑，您可能长期处于高度紧张与担忧中，伴随明显的身心不适，日常功能受到较大影响。这种状态需要专业评估与干预，自行硬扛可能加重痛苦。',
             '1. 请尽快联系心理咨询师或心理中心进行专业辅导；\n2. 在专业人士指导下制定分阶段的减压与安全计划；\n3. 暂停超负荷任务，优先稳定情绪与睡眠；\n4. 如有惊恐发作或强烈失控感，请立即寻求帮助；\n5. 请记住，焦虑是可以治疗的，您不必独自面对。'),
        ]
    },
    3: {  # 压力感知
        'ranges': [
            (0, 4, '压力较低',
             '您当前的压力水平较低，状态良好。',
             '测评显示您目前承受的压力较小，能够较好地平衡学习、生活与休息。身心处于相对松弛的状态，具备较好的抗压基础和恢复能力。',
             '1. 保持现有节奏，注意在忙碌期来临前做好时间规划；\n2. 培养1–2项可持续的减压爱好；\n3. 维持与支持性朋友、家人的联系；\n4. 可定期自评压力水平，做到早觉察、早调节。'),
            (5, 9, '压力适中',
             '您感受到适度的压力，注意劳逸结合。',
             '测评表明您处于适度压力区间。适度压力有助于激发动力，但也需要关注是否出现疲劳累积。若长期维持高负荷而休息不足，压力可能逐步升高。',
             '1. 使用番茄工作法，劳逸结合，避免连续长时间学习；\n2. 每周安排固定放松时间，如运动、冥想或户外活动；\n3. 学会说「不」，合理分配精力，避免过度承诺；\n4. 关注睡眠与饮食，它们是压力恢复的关键；\n5. 感到吃力时，可与同学倾诉或预约咨询。'),
            (10, 12, '压力较高',
             '您的压力水平较高，建议适当休息并寻求帮助。',
             '测评提示压力较高，您可能感到任务繁重、时间不够用、身心疲惫或易怒烦躁。压力可能来自学业、考试、就业或人际等多方面，若不及时调整，可能进一步影响情绪与睡眠。',
             '1. 重新梳理待办事项，优先完成重要且紧急的任务；\n2. 每天保证至少7小时睡眠，避免熬夜透支；\n3. 尝试「放松训练」中的冥想或自然音疗愈；\n4. 与辅导员、咨询师或信任的人讨论压力来源；\n5. 若出现持续情绪低落或焦虑，请进行心理测评并考虑专业支持。'),
            (13, 15, '压力过高',
             '您的压力水平过高，请尽快调整并寻求支持。',
             '测评显示压力过高，您可能已接近身心承受极限，出现明显疲惫、失眠、注意力下降或情绪失控等信号。长期高压不仅影响学业，也会损害身心健康，需要立即重视。',
             '1. 尽快减少非必要任务，给自己留出恢复空间；\n2. 预约心理咨询，系统梳理压力源并制定应对计划；\n3. 告知身边人您需要支持，不要独自硬扛；\n4. 如出现胸闷、持续失眠、极度烦躁等，请及时就医排查；\n5. 危机时刻请拨打校内心理援助热线，您值得获得帮助。'),
        ]
    }
}

_result_extra_ready = None


def _ensure_result_extra_columns():
    global _result_extra_ready
    if _result_extra_ready is not None:
        return _result_extra_ready
    try:
        execute_query('SELECT result_analysis FROM scale_records LIMIT 1', fetch_one=True)
        _result_extra_ready = True
    except Exception:
        try:
            execute_update(
                'ALTER TABLE scale_records '
                'ADD COLUMN result_analysis TEXT DEFAULT NULL COMMENT "具体分析", '
                'ADD COLUMN result_advice TEXT DEFAULT NULL COMMENT "改善建议"'
            )
            _result_extra_ready = True
        except Exception:
            _result_extra_ready = False
    return _result_extra_ready


def evaluate_score(scale_id, total_score):
    """
    根据量表ID和总分评估结果
    :return: (等级, 描述, 分析, 建议)
    """
    rules = SCALE_RULES.get(scale_id, {}).get('ranges', [])
    for low, high, level, desc, analysis, advice in rules:
        if low <= total_score <= high:
            return level, desc, analysis, advice
    return '未知', '请咨询专业人士获取详细解读。', '', ''


@scale_bp.route('', methods=['GET'])
@login_required()
def list_scales():
    """获取所有可用的心理量表列表"""
    scales = execute_query(
        'SELECT id, name, description, question_count, created_at FROM scales ORDER BY id'
    )
    return success(scales)


@scale_bp.route('/<int:scale_id>', methods=['GET'])
@login_required()
def get_scale(scale_id):
    """获取量表详情及其所有题目"""
    scale = execute_query(
        'SELECT id, name, description, question_count FROM scales WHERE id = %s',
        (scale_id,),
        fetch_one=True
    )
    if not scale:
        return error('量表不存在')

    questions = execute_query(
        'SELECT id, question_text, options_json, sort_order '
        'FROM scale_questions WHERE scale_id = %s ORDER BY sort_order',
        (scale_id,)
    )

    for q in questions:
        if isinstance(q['options_json'], str):
            q['options_json'] = json.loads(q['options_json'])

    scale['questions'] = questions
    return success(scale)


@scale_bp.route('/<int:scale_id>/submit', methods=['POST'])
@login_required()
def submit_scale(scale_id):
    """
    提交量表测评答案
    请求体: { answers: [{ question_id, answer_score }] }
    """
    data = request.get_json(silent=True) or {}
    answers = data.get('answers') or []

    if not isinstance(answers, list):
        return error('答案数据格式错误')

    valid_answers = []
    for item in answers:
        if not item or not isinstance(item, dict):
            continue
        if item.get('question_id') is None or item.get('answer_score') is None:
            continue
        valid_answers.append(item)
    answers = valid_answers

    if not answers:
        return error('请完成所有题目')

    scale = execute_query(
        'SELECT id, question_count FROM scales WHERE id = %s',
        (scale_id,),
        fetch_one=True
    )
    if not scale:
        return error('量表不存在')

    if len(answers) < scale['question_count']:
        return error('请完成所有题目后再提交')

    total_score = sum(int(a.get('answer_score', 0)) for a in answers)
    result_level, result_desc, result_analysis, result_advice = evaluate_score(scale_id, total_score)

    _ensure_result_extra_columns()
    record_id = execute_update(
        'INSERT INTO scale_records (user_id, scale_id, total_score, result_level, result_desc, '
        'result_analysis, result_advice) VALUES (%s, %s, %s, %s, %s, %s, %s)',
        (request.current_user['id'], scale_id, total_score, result_level, result_desc,
         result_analysis, result_advice)
    )

    for answer in answers:
        execute_update(
            'INSERT INTO scale_answers (record_id, question_id, answer_score) VALUES (%s, %s, %s)',
            (record_id, answer['question_id'], answer['answer_score'])
        )

    scale_info = execute_query('SELECT name FROM scales WHERE id = %s', (scale_id,), fetch_one=True)
    scale_title = scale_info['name'] if scale_info else '心理测评'
    create_notification(
        request.current_user['id'],
        '心理测评完成',
        f'您已完成「{scale_title}」测评，结果：{result_level}（总分 {total_score}）。',
        'scale', record_id
    )

    return success({
        'record_id': record_id,
        'total_score': total_score,
        'result_level': result_level,
        'result_desc': result_desc,
        'result_analysis': result_analysis,
        'result_advice': result_advice,
        'scale_name': scale_title,
    }, '测评完成')


@scale_bp.route('/records', methods=['GET'])
@login_required()
def list_records():
    """获取当前用户的测评历史记录"""
    _ensure_result_extra_columns()
    user = request.current_user
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size

    if user['role'] == 'admin':
        where = 'WHERE 1=1'
        params = []
    else:
        where = 'WHERE sr.user_id = %s'
        params = [user['id']]

    total = execute_query(
        f'SELECT COUNT(*) as count FROM scale_records sr {where}',
        tuple(params) if params else None,
        fetch_one=True
    )['count']

    params.extend([page_size, offset])
    items = execute_query(
        f'SELECT sr.*, s.name as scale_name, u.real_name as user_name '
        f'FROM scale_records sr '
        f'LEFT JOIN scales s ON sr.scale_id = s.id '
        f'LEFT JOIN users u ON sr.user_id = u.id '
        f'{where} ORDER BY sr.created_at DESC LIMIT %s OFFSET %s',
        tuple(params)
    )

    return success({
        'list': items,
        'total': total,
        'page': page,
        'page_size': page_size
    })


@scale_bp.route('/records/<int:record_id>', methods=['GET'])
@login_required()
def get_record(record_id):
    """获取单条测评记录详情（含分析与建议）"""
    _ensure_result_extra_columns()
    user = request.current_user
    record = execute_query(
        'SELECT sr.*, s.name as scale_name FROM scale_records sr '
        'LEFT JOIN scales s ON sr.scale_id = s.id WHERE sr.id = %s',
        (record_id,),
        fetch_one=True
    )
    if not record:
        return error('记录不存在')
    if user['role'] != 'admin' and record['user_id'] != user['id']:
        return error('无权查看此记录')

    if not record.get('result_analysis') and record.get('scale_id'):
        _, _, analysis, advice = evaluate_score(record['scale_id'], record['total_score'])
        record['result_analysis'] = analysis
        record['result_advice'] = advice

    return success(record)


@scale_bp.route('/trends', methods=['GET'])
@login_required()
def scale_trends():
    """
    获取测评结果趋势数据（用于折线图）
    可选参数 scale_id 筛选特定量表
    """
    user = request.current_user
    scale_id = request.args.get('scale_id', '')

    where = 'WHERE sr.user_id = %s'
    params = [user['id']]
    if scale_id:
        where += ' AND sr.scale_id = %s'
        params.append(int(scale_id))

    records = execute_query(
        f'SELECT sr.id, sr.scale_id, sr.total_score, sr.result_level, sr.created_at, s.name as scale_name '
        f'FROM scale_records sr LEFT JOIN scales s ON sr.scale_id = s.id '
        f'{where} ORDER BY sr.created_at ASC',
        tuple(params)
    )

    grouped = {}
    for r in records:
        sid = r['scale_id']
        if sid not in grouped:
            grouped[sid] = {'scale_id': sid, 'scale_name': r['scale_name'], 'records': []}
        grouped[sid]['records'].append({
            'date': r['created_at'].strftime('%Y-%m-%d') if hasattr(r['created_at'], 'strftime') else str(r['created_at'])[:10],
            'score': r['total_score'],
            'result_level': r['result_level']
        })

    return success(list(grouped.values()))
