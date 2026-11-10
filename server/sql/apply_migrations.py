"""
执行项目中所有延迟数据库迁移（与路由里 _ensure_* 逻辑一致）。
供 watch_sync.py 在同步 init.sql 前调用，确保开发库结构最新。

用法（在 server 目录下）:
    python sql/apply_migrations.py
"""
from __future__ import annotations

import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent.parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))


def _run(label: str, fn) -> None:
    try:
        fn()
        print(f'  [ok] {label}')
    except Exception as exc:
        print(f'  [skip] {label}: {exc}')


def apply_all_migrations() -> int:
    print('正在应用延迟迁移…')

    from routes.auth import (
        _ensure_student_registry_table,
        _ensure_student_no_column,
        _ensure_nickname_column,
        _ensure_security_columns,
        _ensure_reset_codes_table,
    )
    from routes.appointment import _ensure_detail_bio_column, _ensure_appointment_name_column
    from routes.mood import _ensure_media_columns
    from routes.consultation import _ensure_consultation_anonymous_column
    from routes.scale import _ensure_result_extra_columns
    from routes.relaxation import _ensure_social_features
    from utils.media_list import ensure_media_list_column

    _run('学籍库表', _ensure_student_registry_table)
    _run('users.student_no', _ensure_student_no_column)
    _run('users.nickname', _ensure_nickname_column)
    _run('users.security_question', _ensure_security_columns)
    _run('password_reset_codes', _ensure_reset_codes_table)
    _run('counselor_profiles.detail_bio', _ensure_detail_bio_column)
    _run('appointments.student_real_name', _ensure_appointment_name_column)
    _run('mood_diaries 媒体字段', _ensure_media_columns)
    _run('consultations.is_anonymous', _ensure_consultation_anonymous_column)
    _run('scale_records 分析字段', _ensure_result_extra_columns)
    _run('relaxation 点赞/收藏', _ensure_social_features)

    try:
        from routes.tree_hole import _ensure_media_columns, _ensure_reply_media_columns

        _run('tree_hole_posts 媒体字段', _ensure_media_columns)
        _run('tree_hole_replies 媒体字段', _ensure_reply_media_columns)
    except Exception as exc:
        print(f'  [skip] 树洞媒体字段: {exc}')

    for table in ('mood_diaries', 'tree_hole_posts', 'tree_hole_replies'):
        _run(f'{table}.media_list', lambda t=table: ensure_media_list_column(t))

    print('迁移检查完成。')
    return 0


if __name__ == '__main__':
    raise SystemExit(apply_all_migrations())
