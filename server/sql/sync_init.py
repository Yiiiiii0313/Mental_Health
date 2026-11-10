"""
将当前 MySQL 数据库同步到 init.sql（表结构 + 全部数据）。

用法（在 server 目录下）:
    python sql/sync_init.py              # 同步 DDL + 数据到 init.sql
    python sql/sync_init.py --schema-only  # 仅同步表结构，保留 init.sql 现有数据段
    python sql/sync_init.py --check      # 仅检查是否已同步
    python sql/sync_init.py --dry-run    # 预览到 init.preview.sql，不写 init.sql
    python sql/watch_sync.py             # 开发时监听文件保存并自动执行本脚本
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

# 保证可从 server 目录导入 config / utils
SERVER_DIR = Path(__file__).resolve().parent.parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from utils.db import get_db_connection  # noqa: E402
from pymysql.converters import escape_item  # noqa: E402

INIT_SQL_PATH = Path(__file__).resolve().parent / 'init.sql'
DATA_MARKER = '-- 测试数据'
ROWS_PER_INSERT = 100


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass


def _emit(message: str, *, stream=None) -> None:
    stream = stream or sys.stdout
    try:
        print(message, file=stream, flush=True)
    except UnicodeEncodeError:
        encoding = getattr(stream, 'encoding', None) or 'utf-8'
        print(message.encode(encoding, errors='replace').decode(encoding), file=stream, flush=True)

# 建表顺序（父表在前）；删表顺序为其逆序
TABLE_CREATE_ORDER = [
    'users',
    'password_reset_codes',
    'student_registry',
    'counselor_profiles',
    'announcements',
    'articles',
    'article_likes',
    'article_favorites',
    'appointments',
    'scales',
    'scale_questions',
    'scale_records',
    'scale_answers',
    'mood_diaries',
    'consultations',
    'consultation_messages',
    'ai_chat_sessions',
    'ai_chat_messages',
    'relaxation_audios',
    'relaxation_likes',
    'relaxation_favorites',
    'tree_hole_posts',
    'tree_hole_replies',
    'notifications',
]

TABLE_LABELS = {
    'users': '用户表',
    'password_reset_codes': '找回密码验证码表',
    'student_registry': '学籍库（全校学生名册，用于注册校验）',
    'counselor_profiles': '咨询师档案表',
    'announcements': '公告表',
    'articles': '心理文章表',
    'article_likes': '文章点赞表',
    'article_favorites': '文章收藏表',
    'appointments': '咨询预约表',
    'scales': '心理量表表',
    'scale_questions': '量表题目表',
    'scale_records': '量表测评记录表',
    'scale_answers': '量表答题详情表',
    'mood_diaries': '心情日记表',
    'consultations': '在线咨询会话表',
    'consultation_messages': '咨询消息表',
    'ai_chat_sessions': 'AI心理助手会话表',
    'ai_chat_messages': 'AI心理助手消息表',
    'relaxation_audios': '放松训练音频表',
    'relaxation_likes': '放松训练点赞表',
    'relaxation_favorites': '放松训练收藏表',
    'tree_hole_posts': '栖心树洞帖子表',
    'tree_hole_replies': '树洞回复表',
    'notifications': '消息通知表',
}

TABLE_DATA_LABELS = {
    'users': '用户数据',
    'password_reset_codes': '找回密码验证码',
    'student_registry': '学籍库',
    'counselor_profiles': '咨询师档案',
    'announcements': '公告',
    'articles': '心理文章',
    'article_likes': '文章点赞',
    'article_favorites': '文章收藏',
    'appointments': '预约记录',
    'scales': '心理量表',
    'scale_questions': '量表题目',
    'scale_records': '测评记录',
    'scale_answers': '答题详情',
    'mood_diaries': '心情日记',
    'consultations': '在线咨询',
    'consultation_messages': '咨询消息',
    'ai_chat_sessions': 'AI对话会话',
    'ai_chat_messages': 'AI对话消息',
    'relaxation_audios': '放松训练音频',
    'relaxation_likes': '放松训练点赞',
    'relaxation_favorites': '放松训练收藏',
    'tree_hole_posts': '栖心树洞帖子',
    'tree_hole_replies': '树洞回复',
    'notifications': '消息通知',
}

FILE_HEADER = """-- =============================================
-- 校园心理健康服务平台 - 数据库初始化脚本
-- 数据库: mental_health_server
-- MySQL 8.0, 端口 3306
-- 默认密码 123456 的 MD5: e10adc3949ba59abbe56e057f20f883e
--
-- 同步方式: python sql/sync_init.py  （DDL + 数据，重跑本文件可恢复当前库）
-- 开发监听: python sql/watch_sync.py
-- 仅同步结构: python sql/sync_init.py --schema-only
-- =============================================

CREATE DATABASE IF NOT EXISTS mental_health_server
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE mental_health_server;

"""

SQL_TYPES = (
    'TINYINT', 'SMALLINT', 'MEDIUMINT', 'INT', 'INTEGER', 'BIGINT',
    'DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL',
    'CHAR', 'VARCHAR', 'TEXT', 'TINYTEXT', 'MEDIUMTEXT', 'LONGTEXT',
    'BLOB', 'TINYBLOB', 'MEDIUMBLOB', 'LONGBLOB',
    'DATE', 'TIME', 'DATETIME', 'TIMESTAMP', 'YEAR',
    'ENUM', 'SET', 'JSON', 'BOOL', 'BOOLEAN',
)


def split_init_sql(content: str) -> tuple[str, str]:
    """拆分为「表结构段」与「测试数据段」。"""
    marker_idx = content.find(DATA_MARKER)
    if marker_idx == -1:
        raise ValueError(f'init.sql 中未找到「{DATA_MARKER}」分段标记')

    section_start = content.rfind('-- =============================================', 0, marker_idx)
    if section_start == -1:
        section_start = content.rfind('\n', 0, marker_idx) + 1

    return content[:section_start].rstrip(), content[section_start:]


def extract_table_comments(schema_part: str) -> dict[str, str]:
    """从现有 init.sql 提取每张表上方的中文注释。"""
    comments: dict[str, str] = {}
    pattern = re.compile(
        r'-- -+\s*\n-- (.+?)\s*\n-- -+\s*\nCREATE TABLE (\w+)',
        re.MULTILINE,
    )
    for title, table in pattern.findall(schema_part):
        comments[table] = title.strip()
    return comments


def fetch_create_statements() -> dict[str, str]:
    """从数据库读取每张表的 CREATE TABLE 语句。"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SHOW TABLES')
            rows = cursor.fetchall()
            table_key = next(iter(rows[0])) if rows else None
            db_tables = {row[table_key] for row in rows} if table_key else set()

            result: dict[str, str] = {}
            for table in db_tables:
                cursor.execute(f'SHOW CREATE TABLE `{table}`')
                row = cursor.fetchone()
                create_key = next((k for k in row if k.lower().replace(' ', '') == 'createtable'), None)
                if not create_key:
                    create_key = 'Create Table'
                result[table] = row[create_key]
            return result
    finally:
        conn.close()


def normalize_create_sql(sql: str) -> str:
    """整理 SHOW CREATE TABLE 输出，便于阅读并与 init.sql 风格接近。"""
    sql = sql.strip().rstrip(';')
    sql = sql.replace('`', '')
    sql = re.sub(r'\s+AUTO_INCREMENT=\d+', '', sql, flags=re.IGNORECASE)

    match = re.match(
        r'(CREATE TABLE\s+(\w+)\s*\()(.*)(\)\s*ENGINE\s*=.*)',
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return sql + ';'

    prefix, _table, body, suffix = match.groups()
    parts = _split_column_definitions(body)
    lines = [f'    {part}{"," if i < len(parts) - 1 else ""}' for i, part in enumerate(parts)]
    suffix = _uppercase_sql_types(suffix.strip())
    return f'{prefix}\n' + '\n'.join(lines) + '\n' + suffix + ';'


def _split_column_definitions(body: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    in_string = False
    string_char = ''
    i = 0
    while i < len(body):
        char = body[i]
        if in_string:
            current.append(char)
            if char == string_char and (i == 0 or body[i - 1] != '\\'):
                in_string = False
            i += 1
            continue
        if char in ("'", '"'):
            in_string = True
            string_char = char
            current.append(char)
        elif char == '(':
            depth += 1
            current.append(char)
        elif char == ')':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            part = ''.join(current).strip()
            if part:
                parts.append(part)
            current = []
        else:
            current.append(char)
        i += 1
    tail = ''.join(current).strip()
    if tail:
        parts.append(tail)
    return [_uppercase_sql_types(part) for part in parts]


def _uppercase_sql_types(text: str) -> str:
    def repl(match: re.Match) -> str:
        return match.group(0).upper()

    for sql_type in SQL_TYPES:
        text = re.sub(rf'\b{sql_type}\b', repl, text, flags=re.IGNORECASE)
    return text


def build_schema_section(
    create_map: dict[str, str],
    table_comments: dict[str, str],
) -> str:
    """生成 DROP + CREATE 表结构段落。"""
    known_tables = [t for t in TABLE_CREATE_ORDER if t in create_map]
    extra_tables = sorted(set(create_map) - set(TABLE_CREATE_ORDER))
    create_order = known_tables + extra_tables
    drop_order = list(reversed(create_order))

    lines = [
        '',
        '-- ----------------------------',
        '-- 删除旧表（按外键依赖顺序）',
        '-- ----------------------------',
    ]
    for table in drop_order:
        lines.append(f'DROP TABLE IF EXISTS {table};')

    for table in create_order:
        title = TABLE_LABELS.get(table) or table_comments.get(table, table)
        lines.extend([
            '',
            '-- ----------------------------',
            f'-- {title}',
            '-- ----------------------------',
        ])
        lines.append(normalize_create_sql(create_map[table]))
        lines.append('')

    return '\n'.join(lines).rstrip()


def build_init_sql(data_section: str, schema_section: str) -> str:
    return FILE_HEADER.rstrip() + schema_section + '\n\n' + data_section.lstrip('\n')


def _sql_literal(conn, value) -> str:
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, datetime):
        return escape_item(value.strftime('%Y-%m-%d %H:%M:%S'), conn.charset)
    if isinstance(value, date):
        return escape_item(value.strftime('%Y-%m-%d'), conn.charset)
    if isinstance(value, time):
        return escape_item(value.strftime('%H:%M:%S'), conn.charset)
    if isinstance(value, Decimal):
        return escape_item(str(value), conn.charset)
    if isinstance(value, (dict, list)):
        return escape_item(json.dumps(value, ensure_ascii=False), conn.charset)
    if isinstance(value, bytes):
        return escape_item(value.decode('utf-8', errors='replace'), conn.charset)
    if isinstance(value, str) and value.startswith(('{', '[')):
        try:
            json.loads(value)
            return escape_item(value, conn.charset)
        except (json.JSONDecodeError, TypeError):
            pass
    try:
        return escape_item(value, conn.charset)
    except TypeError:
        return escape_item(str(value), conn.charset)


def _fetch_table_rows(conn, table: str) -> tuple[list[str], list[dict]]:
    with conn.cursor() as cursor:
        cursor.execute(f'SELECT * FROM `{table}`')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return columns, rows


def _format_insert_batches(table: str, columns: list[str], rows: list[dict], conn) -> list[str]:
    if not rows:
        return []

    col_sql = ', '.join(columns)
    lines: list[str] = []
    for start in range(0, len(rows), ROWS_PER_INSERT):
        chunk = rows[start:start + ROWS_PER_INSERT]
        value_lines = []
        for row in chunk:
            vals = ', '.join(_sql_literal(conn, row.get(col)) for col in columns)
            value_lines.append(f'({vals})')
        lines.append(f'INSERT INTO {table} ({col_sql}) VALUES')
        lines.append(',\n'.join(value_lines) + ';')
    return lines


def build_data_section(conn, tables: list[str]) -> str:
    """从数据库导出全部表数据，生成 init.sql 数据段。"""
    lines = [
        '-- =============================================',
        '-- 测试数据（由 sync_init.py 从数据库自动导出）',
        '-- =============================================',
    ]
    total_rows = 0

    for table in tables:
        label = TABLE_DATA_LABELS.get(table, table)
        try:
            columns, rows = _fetch_table_rows(conn, table)
        except Exception as exc:
            raise RuntimeError(f'导出表 {table} 失败: {exc}') from exc
        lines.extend(['', f'-- {label}'])
        if not rows:
            lines.append(f'-- {table}: (empty)')
            continue
        total_rows += len(rows)
        lines.extend(_format_insert_batches(table, columns, rows, conn))

    lines.append('')
    lines.append(f'-- 共导出 {total_rows} 行数据')
    return '\n'.join(lines)


def main() -> int:
    _configure_stdio()

    parser = argparse.ArgumentParser(description='将数据库同步到 init.sql')
    parser.add_argument('--check', action='store_true', help='仅检查，不写入文件')
    parser.add_argument('--dry-run', action='store_true', help='预览，不写文件')
    parser.add_argument(
        '--output',
        metavar='FILE',
        help='将结果写入指定文件（可与 --dry-run 联用）',
    )
    parser.add_argument(
        '--schema-only',
        action='store_true',
        help='仅同步表结构，保留 init.sql 现有数据段',
    )
    args = parser.parse_args()

    if not INIT_SQL_PATH.exists():
        _emit(f'错误: 找不到 {INIT_SQL_PATH}', stream=sys.stderr)
        return 1

    original = INIT_SQL_PATH.read_text(encoding='utf-8')
    try:
        schema_part, data_section = split_init_sql(original)
    except ValueError as exc:
        _emit(f'错误: {exc}', stream=sys.stderr)
        return 1

    table_comments = extract_table_comments(schema_part)

    conn = None
    create_map: dict[str, str] = {}
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SHOW TABLES')
            rows = cursor.fetchall()
            if not rows:
                _emit('错误: 数据库中没有表，请先执行 init.sql 或启动应用完成初始化。', stream=sys.stderr)
                return 1
            table_key = next(iter(rows[0]))
            db_tables = {row[table_key] for row in rows}

            for table in db_tables:
                cursor.execute(f'SHOW CREATE TABLE `{table}`')
                row = cursor.fetchone()
                create_key = next(
                    (k for k in row if k.lower().replace(' ', '') == 'createtable'),
                    'Create Table',
                )
                create_map[table] = row[create_key]

        known_tables = [t for t in TABLE_CREATE_ORDER if t in create_map]
        extra_tables = sorted(set(create_map) - set(TABLE_CREATE_ORDER))
        table_order = known_tables + extra_tables

        if args.schema_only:
            data_section_out = data_section
        else:
            data_section_out = build_data_section(conn, table_order)
    except Exception as exc:
        if '导出表' in str(exc) or '导出数据' in str(exc):
            _emit(f'错误: {exc}', stream=sys.stderr)
        else:
            _emit(f'错误: 无法连接数据库 — {exc}', stream=sys.stderr)
            _emit('请确认 MySQL 已启动，且在 server 目录下执行，server/.env 配置正确。', stream=sys.stderr)
        return 1
    finally:
        if conn is not None:
            conn.close()

    schema_section = build_schema_section(create_map, table_comments)

    new_content = build_init_sql(data_section_out, schema_section)
    output_path = Path(args.output).resolve() if args.output else None

    if args.dry_run or output_path:
        target = output_path or INIT_SQL_PATH
        if args.dry_run and not output_path:
            _emit(f'预览内容较长，已写入: {INIT_SQL_PATH.with_suffix(".preview.sql")}')
            target = INIT_SQL_PATH.with_suffix('.preview.sql')
        target.write_text(new_content, encoding='utf-8', newline='\n')
        _emit(f'已生成 {target}')
        return 0

    if new_content == original:
        _emit('init.sql 已与数据库一致，无需更新。')
        return 0

    if args.check:
        _emit('init.sql 与数据库不一致，请运行: python sql/sync_init.py', stream=sys.stderr)
        return 1

    INIT_SQL_PATH.write_text(new_content, encoding='utf-8', newline='\n')
    if args.schema_only:
        _emit(f'已同步 {len(create_map)} 张表的结构到 {INIT_SQL_PATH}')
    else:
        _emit(f'已同步 {len(create_map)} 张表的结构与数据到 {INIT_SQL_PATH}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
