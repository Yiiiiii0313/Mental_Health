"""
知识库初始化脚本
从数据库中读取心理量表信息（描述、题目、评分规则），
生成文本块 → 向量嵌入 → 存入 knowledge_chunks 表

用法: cd server && python seed_knowledge_base.py
"""
import json
import sys
import os

# 确保可以在 server/ 目录下运行
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_db_connection
from utils.embedding import get_embedding, get_embeddings, EmbeddingError

# 量表评分规则（与 routes/scale.py 中的 SCALE_RULES 保持一致）
# 这里复制一份以避免循环导入
SCALE_RULES = {
    1: {  # PHQ-9 抑郁
        'name': 'PHQ-9 抑郁自评量表',
        'ranges': [
            (0, 4, '无抑郁',
             '您的情绪状态良好，请继续保持积极的生活态度。',
             '测评结果显示，您近期几乎未出现明显的抑郁症状。情绪较为稳定，对日常学习与生活能保持适度的兴趣与动力，睡眠、食欲和精力方面也未见显著异常。',
             '1. 保持规律作息与适度运动，巩固现有良好状态；\n2. 继续维护支持性人际关系；\n3. 可定期使用本平台心情日记功能关注自身情绪波动。'),
            (5, 9, '轻度抑郁',
             '您可能存在轻度抑郁症状，建议关注情绪变化，适当放松。',
             '测评提示您近期可能存在轻度抑郁倾向，表现为偶尔的情绪低落、兴趣减退或精力不足。目前程度较轻，及时觉察和调节往往能有效缓解。',
             '1. 每天安排15–30分钟放松活动；\n2. 尝试记录心情日记，识别引发低落的具体情境；\n3. 保持规律睡眠；\n4. 若症状持续两周以上，建议预约心理咨询。'),
            (10, 14, '中度抑郁',
             '您可能存在中度抑郁症状，建议寻求心理咨询帮助。',
             '测评显示您近期抑郁症状已达到中度水平，可能包括较明显的情绪低落、动力下降、注意力难以集中、睡眠或食欲改变等。单纯依靠自我调节可能效果有限，专业支持会更有帮助。',
             '1. 建议尽快预约校内心理咨询师进行面对面评估；\n2. 向信任的家人、朋友或辅导员适度倾诉；\n3. 减少自我批评，从小目标开始恢复日常节奏；\n4. 若出现自伤念头，请立即联系心理援助热线。'),
            (15, 19, '中重度抑郁',
             '您可能存在中重度抑郁症状，请尽快联系心理咨询师。',
             '测评结果提示中重度抑郁症状，说明您可能正经历持续且显著的情绪困扰，如明显的无助感、强烈疲惫、兴趣严重丧失。这种状态对学业和生活的干扰较大，需要及时的专业干预。',
             '1. 请尽快联系心理咨询师进行系统评估与干预；\n2. 告知身边可信赖的人您的状况；\n3. 暂停过度自我要求；\n4. 如有自伤或自杀想法，请立即拨打校内心理援助热线。'),
            (20, 27, '重度抑郁',
             '您可能存在重度抑郁症状，请立即寻求专业心理援助。',
             '测评显示重度抑郁症状，意味着您可能长期处于显著痛苦中，伴随严重的情绪崩溃、功能受损或绝望感。这是需要高度重视的心理健康信号。',
             '1. 请立即联系心理咨询师、辅导员或前往专业机构求助；\n2. 如有自伤、自杀计划或冲动，请立刻拨打急救/心理危机热线；\n3. 您值得被帮助，求助是勇敢且正确的选择。'),
        ]
    },
    2: {  # GAD-7 焦虑
        'name': 'GAD-7 焦虑自评量表',
        'ranges': [
            (0, 4, '无焦虑',
             '您的焦虑水平正常，心理状态良好。',
             '测评表明您近期焦虑水平处于正常范围，对日常事务的担忧可控，身心紧张感不明显。您能够较好地应对一般性压力。',
             '1. 继续保持健康的生活方式与压力管理习惯；\n2. 考试季或任务密集期可提前规划；\n3. 学习基础放松技巧以备不时之需。'),
            (5, 9, '轻度焦虑',
             '您可能存在轻度焦虑，可尝试深呼吸、运动等方式缓解。',
             '测评提示轻度焦虑，您可能时常感到紧张、担忧或对某些事情过度思虑，但尚能完成日常任务。通过自我调节和适度支持通常可以改善。',
             '1. 练习腹式呼吸、渐进式肌肉放松等技巧；\n2. 每天安排30分钟有氧运动；\n3. 限制咖啡因摄入；\n4. 将担忧写下来，区分可解决与不可控的问题。'),
            (10, 14, '中度焦虑',
             '您可能存在中度焦虑，建议寻求心理咨询。',
             '测评显示中度焦虑，您可能经常感到坐立不安、难以放松、注意力分散或伴有躯体反应。焦虑可能已明显干扰学习效率和睡眠质量，需要更系统的应对策略。',
             '1. 建议预约心理咨询，学习认知行为技巧管理焦虑；\n2. 建立稳定的作息与学习计划；\n3. 减少刷手机等加剧焦虑的行为；\n4. 与亲友分享感受，避免情绪内化。'),
            (15, 21, '重度焦虑',
             '您可能存在重度焦虑，请尽快联系心理咨询师。',
             '测评提示重度焦虑，您可能长期处于高度紧张与担忧中，伴随明显的身心不适，日常功能受到较大影响。这种状态需要专业评估与干预。',
             '1. 请尽快联系心理咨询师进行专业辅导；\n2. 暂停超负荷任务，优先稳定情绪与睡眠；\n3. 焦虑是可以治疗的，您不必独自面对。'),
        ]
    },
    3: {  # 压力感知
        'name': '压力感知量表',
        'ranges': [
            (0, 4, '压力较低',
             '您当前的压力水平较低，状态良好。',
             '测评显示您目前承受的压力较小，能够较好地平衡学习、生活与休息。身心处于相对松弛的状态，具备较好的抗压基础。',
             '1. 保持现有节奏；\n2. 培养1–2项可持续的减压爱好；\n3. 可定期自评压力水平，做到早觉察、早调节。'),
            (5, 9, '压力适中',
             '您感受到适度的压力，注意劳逸结合。',
             '测评表明您处于适度压力区间。适度压力有助于激发动力，但也需要关注是否出现疲劳累积。',
             '1. 使用番茄工作法，劳逸结合；\n2. 每周安排固定放松时间；\n3. 学会合理分配精力，避免过度承诺；\n4. 关注睡眠与饮食。'),
            (10, 12, '压力较高',
             '您的压力水平较高，建议适当休息并寻求帮助。',
             '测评提示压力较高，您可能感到任务繁重、时间不够用、身心疲惫或易怒烦躁。若不及时调整，可能进一步影响情绪与睡眠。',
             '1. 重新梳理待办事项，优先完成重要紧急任务；\n2. 每天保证至少7小时睡眠；\n3. 尝试放松训练中的冥想或自然音疗愈；\n4. 与辅导员、咨询师或信任的人讨论压力来源。'),
            (13, 15, '压力过高',
             '您的压力水平过高，请尽快调整并寻求支持。',
             '测评显示压力过高，您可能已接近身心承受极限，出现明显疲惫、失眠、注意力下降或情绪失控等信号。长期高压不仅影响学业，也会损害身心健康。',
             '1. 尽快减少非必要任务，给自己留出恢复空间；\n2. 预约心理咨询；\n3. 告知身边人您需要支持；\n4. 危机时刻请拨打校内心理援助热线。'),
        ]
    }
}


def build_chunks(cursor):
    """从数据库读取量表数据，生成所有知识块"""
    chunks = []

    # 读取所有量表
    cursor.execute('SELECT id, name, description FROM scales ORDER BY id')
    scales = cursor.fetchall()

    for scale in scales:
        scale_id = scale['id']
        scale_name = scale['name']
        description = scale['description']
        rules = SCALE_RULES.get(scale_id)
        if not rules:
            continue

        # --- 1. 量表概览 chunk ---
        overview = (
            f"【{scale_name}】\n"
            f"量表说明：{description}\n"
            f"该量表用于心理健康自评，请在平台「心理测评」模块完成答题后查看完整评分与分析。"
        )
        chunks.append({
            'source_type': 'scale_overview',
            'source_id': scale_id,
            'chunk_index': 0,
            'title': f'{scale_name} - 量表说明',
            'content': overview,
            'metadata': json.dumps({'scale_id': scale_id, 'scale_name': scale_name, 'type': 'overview'}, ensure_ascii=False),
        })

        # --- 2. 题目汇总 chunk ---
        cursor.execute(
            'SELECT question_text, options_json FROM scale_questions WHERE scale_id = %s ORDER BY sort_order',
            (scale_id,)
        )
        questions = cursor.fetchall()
        question_texts = []
        for i, q in enumerate(questions, 1):
            try:
                options = json.loads(q['options_json']) if isinstance(q['options_json'], str) else q['options_json']
            except (json.JSONDecodeError, TypeError):
                options = []
            option_str = ' | '.join(
                f"{o.get('label', '')}({o.get('score', 0)}分)" for o in options
            )
            question_texts.append(f"第{i}题: {q['question_text']} [选项: {option_str}]")

        chunks.append({
            'source_type': 'scale_questions',
            'source_id': scale_id,
            'chunk_index': 0,
            'title': f'{scale_name} - 全部题目',
            'content': f"【{scale_name}】共 {len(questions)} 道题目：\n" + '\n'.join(question_texts),
            'metadata': json.dumps({'scale_id': scale_id, 'scale_name': scale_name, 'type': 'questions'}, ensure_ascii=False),
        })

        # --- 3. 评分规则概览 chunk ---
        scoring_lines = []
        for low, high, level, desc, analysis, advice in rules['ranges']:
            scoring_lines.append(f"{low}-{high}分: {level} — {desc}")

        chunks.append({
            'source_type': 'scoring_rule',
            'source_id': scale_id,
            'chunk_index': 0,
            'title': f'{scale_name} - 评分规则总览',
            'content': f"【{scale_name}】评分标准：\n" + '\n'.join(scoring_lines),
            'metadata': json.dumps({'scale_id': scale_id, 'scale_name': scale_name, 'type': 'scoring_summary'}, ensure_ascii=False),
        })

        # --- 4. 每个评分等级的分析和建议（各一个 chunk） ---
        for idx, (low, high, level, desc, analysis, advice) in enumerate(rules['ranges']):
            # 分析 chunk
            chunks.append({
                'source_type': 'scoring_rule',
                'source_id': scale_id,
                'chunk_index': idx + 1,
                'title': f'{scale_name} - {level}（{low}-{high}分）分析',
                'content': f"【{scale_name} · {level}（{low}-{high}分）】\n{desc}\n\n详细分析：{analysis}",
                'metadata': json.dumps({'scale_id': scale_id, 'scale_name': scale_name, 'level': level, 'score_range': f'{low}-{high}', 'type': 'analysis'}, ensure_ascii=False),
            })

            # 建议 chunk
            chunks.append({
                'source_type': 'scoring_rule',
                'source_id': scale_id,
                'chunk_index': idx + 100,  # 避免与 analysis chunk index 冲突
                'title': f'{scale_name} - {level}（{low}-{high}分）建议',
                'content': f"【{scale_name} · {level}（{low}-{high}分）· 改善建议】\n{advice}",
                'metadata': json.dumps({'scale_id': scale_id, 'scale_name': scale_name, 'level': level, 'score_range': f'{low}-{high}', 'type': 'advice'}, ensure_ascii=False),
            })

    return chunks


ENSURE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id INT NOT NULL AUTO_INCREMENT COMMENT '知识块ID',
    source_type VARCHAR(50) NOT NULL COMMENT '来源类型：scale_overview/scale_questions/scoring_rule',
    source_id INT DEFAULT NULL COMMENT '来源业务ID（如量表ID）',
    chunk_index INT DEFAULT 0 COMMENT '同一来源内的分片序号',
    title VARCHAR(200) DEFAULT NULL COMMENT '标题',
    content TEXT NOT NULL COMMENT '知识正文',
    embedding LONGTEXT NOT NULL COMMENT '嵌入向量 JSON 数组',
    metadata JSON DEFAULT NULL COMMENT '扩展元数据',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_source (source_type, source_id),
    KEY idx_chunk (source_type, source_id, chunk_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='RAG知识库文本块'
'''


def seed():
    """主流程：建表 → 清空知识库 → 构建 chunks → 生成 embeddings → 写入数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(ENSURE_TABLE_SQL)
        conn.commit()

        # 1. 清空现有知识库
        cursor.execute('DELETE FROM knowledge_chunks')
        print('[1/4] 已清空现有知识库')

        # 2. 构建文本块
        chunks = build_chunks(cursor)
        print(f'[2/4] 已生成 {len(chunks)} 个知识块')

        # 3. 批量生成向量嵌入
        print('[3/4] 正在生成向量嵌入...')
        texts = [c['content'] for c in chunks]

        try:
            embeddings = get_embeddings(texts)
            print(f'      已获取 {len(embeddings)} 个向量嵌入')
        except EmbeddingError as e:
            print(f'      错误：{e}')
            print('      请检查 LLM_EMBEDDING_MODEL 配置或切换到支持 embedding 的 provider')
            conn.rollback()
            return

        # 4. 写入数据库
        print('[4/4] 正在写入数据库...')
        for chunk, embedding in zip(chunks, embeddings):
            cursor.execute(
                '''INSERT INTO knowledge_chunks
                   (source_type, source_id, chunk_index, title, content, embedding, metadata)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (
                    chunk['source_type'],
                    chunk['source_id'],
                    chunk['chunk_index'],
                    chunk['title'],
                    chunk['content'],
                    json.dumps(embedding),
                    chunk['metadata'],
                )
            )

        conn.commit()
        print(f'      成功写入 {len(chunks)} 个知识块')

        # 打印统计
        cursor.execute('SELECT source_type, COUNT(*) as cnt FROM knowledge_chunks GROUP BY source_type')
        stats = cursor.fetchall()
        print('\n知识库统计：')
        for row in stats:
            print(f'   {row["source_type"]}: {row["cnt"]} 条')

    except Exception as e:
        conn.rollback()
        print(f'知识库初始化失败: {e}')
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    seed()