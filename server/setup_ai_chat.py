"""
AI对话表初始化脚本（已有数据库执行一次）
运行: cd server && python setup_ai_chat.py
"""
from utils.db import get_db_connection


SQL = """
CREATE TABLE IF NOT EXISTS ai_chat_sessions (
    id          INT PRIMARY KEY AUTO_INCREMENT COMMENT '会话ID',
    user_id     INT NOT NULL COMMENT '用户ID',
    title       VARCHAR(200) DEFAULT 'AI心理助手' COMMENT '会话标题',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI心理助手会话表';

CREATE TABLE IF NOT EXISTS ai_chat_messages (
    id          INT PRIMARY KEY AUTO_INCREMENT COMMENT '消息ID',
    session_id  INT NOT NULL COMMENT '会话ID',
    role        ENUM('user', 'assistant') NOT NULL COMMENT '角色',
    content     TEXT NOT NULL COMMENT '消息内容',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
    FOREIGN KEY (session_id) REFERENCES ai_chat_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI心理助手消息表';
"""


def main():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for stmt in SQL.strip().split(';'):
                stmt = stmt.strip()
                if stmt:
                    cursor.execute(stmt)
        conn.commit()
        print('[OK] AI对话表创建成功')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
