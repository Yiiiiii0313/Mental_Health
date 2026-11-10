"""
多媒体列表工具：支持一条记录附加多张图片/多个视频
"""
import json

from utils.db import execute_query, execute_update

MAX_MEDIA_COUNT = 9

_column_cache = {}


def ensure_media_list_column(table):
    """为表自动补充 media_list 字段"""
    if table in _column_cache:
        return _column_cache[table]
    try:
        execute_query(f'SELECT media_list FROM {table} LIMIT 1', fetch_one=True)
        _column_cache[table] = True
    except Exception:
        try:
            execute_update(
                f'ALTER TABLE {table} '
                'ADD COLUMN media_list JSON DEFAULT NULL COMMENT "多媒体列表"'
            )
            _column_cache[table] = True
        except Exception:
            _column_cache[table] = False
    return _column_cache[table]


def _parse_json_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def validate_media_list(media_list, url_prefix):
    """校验媒体列表格式与数量"""
    if media_list is None:
        return []
    if not isinstance(media_list, list):
        raise ValueError('媒体列表格式无效')
    if len(media_list) > MAX_MEDIA_COUNT:
        raise ValueError(f'最多上传 {MAX_MEDIA_COUNT} 个文件')

    cleaned = []
    for item in media_list:
        if not isinstance(item, dict):
            raise ValueError('媒体列表格式无效')
        media_url = (item.get('media_url') or '').strip()
        media_type = item.get('media_type')
        if not media_url or not media_type:
            raise ValueError('媒体信息不完整')
        if not media_url.startswith(url_prefix):
            raise ValueError('无效的媒体文件')
        if media_type not in ('image', 'video'):
            raise ValueError('无效的媒体类型')
        cleaned.append({'media_url': media_url, 'media_type': media_type})
    return cleaned


def pack_media_for_db(media_list):
    """写入数据库：JSON + 兼容旧字段首项"""
    if not media_list:
        return None, None, None
    return json.dumps(media_list, ensure_ascii=False), media_list[0]['media_url'], media_list[0]['media_type']


def attach_media_list(row):
    """读取记录时附加 media_list 字段"""
    if not row:
        return row
    media_list = _parse_json_list(row.get('media_list'))
    if not media_list and row.get('media_url'):
        media_list = [{
            'media_url': row['media_url'],
            'media_type': row.get('media_type'),
        }]
    row['media_list'] = media_list
    return row


def remove_all_media(media_list, legacy_url, remove_fn):
    """删除记录关联的全部媒体文件"""
    urls = set()
    for item in _parse_json_list(media_list):
        url = item.get('media_url')
        if url:
            urls.add(url)
    if legacy_url:
        urls.add(legacy_url)
    for url in urls:
        remove_fn(url)
