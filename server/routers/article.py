"""
心理文章路由模块
提供文章的浏览、点赞、收藏功能
"""
from flask import Blueprint, request
from utils.db import execute_query, execute_update
from utils.auth import login_required
from utils.response import success, error

article_bp = Blueprint('article', __name__, url_prefix='/api/articles')

_db_features = {}


def _check_db_feature(key, sql):
    """检测数据库是否支持某项特性"""
    if key not in _db_features:
        try:
            execute_query(sql, fetch_one=True)
            _db_features[key] = True
        except Exception:
            _db_features[key] = False
    return _db_features[key]


def _like_count_field():
    """返回点赞数字段SQL，兼容未迁移的旧数据库"""
    if _check_db_feature('like_count', 'SELECT like_count FROM articles LIMIT 1'):
        return 'a.like_count'
    return '0 AS like_count'


def _attach_user_actions(items, user_id):
    """为文章列表附加当前用户的点赞/收藏状态"""
    if not items or not user_id:
        return items
    if not _check_db_feature('article_likes', 'SELECT 1 FROM article_likes LIMIT 1'):
        for item in items:
            item['is_liked'] = False
            item['is_favorited'] = False
        return items
    ids = [i['id'] for i in items]
    placeholders = ','.join(['%s'] * len(ids))
    try:
        likes = execute_query(
            f'SELECT article_id FROM article_likes WHERE user_id = %s AND article_id IN ({placeholders})',
            tuple([user_id] + ids)
        )
        favs = execute_query(
            f'SELECT article_id FROM article_favorites WHERE user_id = %s AND article_id IN ({placeholders})',
            tuple([user_id] + ids)
        )
        liked_ids = {r['article_id'] for r in likes}
        fav_ids = {r['article_id'] for r in favs}
        for item in items:
            item['is_liked'] = item['id'] in liked_ids
            item['is_favorited'] = item['id'] in fav_ids
    except Exception:
        for item in items:
            item['is_liked'] = False
            item['is_favorited'] = False
    return items


@article_bp.route('', methods=['GET'])
@login_required()
def list_articles():
    """获取文章列表，支持分类筛选和分页"""
    user = request.current_user
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    category = request.args.get('category', '')
    only_favorites = request.args.get('favorites', '') == '1'
    offset = (page - 1) * page_size

    if only_favorites:
        if not _check_db_feature('article_favorites', 'SELECT 1 FROM article_favorites LIMIT 1'):
            return success({'list': [], 'total': 0, 'categories': [], 'page': page, 'page_size': page_size})
        where_clause = 'WHERE a.status = 1 AND af.user_id = %s'
        params = [user['id']]
        join_fav = 'INNER JOIN article_favorites af ON a.id = af.article_id'
    else:
        where_clause = 'WHERE a.status = 1'
        params = []
        join_fav = ''

    if category:
        where_clause += ' AND a.category = %s'
        params.append(category)

    total = execute_query(
        f'SELECT COUNT(*) as count FROM articles a {join_fav} {where_clause}',
        tuple(params) if params else None,
        fetch_one=True
    )['count']

    params.extend([page_size, offset])
    items = execute_query(
        f'SELECT a.id, a.title, a.category, a.cover_image, a.view_count, {_like_count_field()}, '
        f'a.created_at, u.real_name as author_name, LEFT(a.content, 120) as summary '
        f'FROM articles a LEFT JOIN users u ON a.author_id = u.id {join_fav} '
        f'{where_clause} ORDER BY a.created_at DESC LIMIT %s OFFSET %s',
        tuple(params)
    )
    _attach_user_actions(items, user['id'])

    categories = execute_query('SELECT DISTINCT category FROM articles WHERE status = 1')

    return success({
        'list': items,
        'total': total,
        'categories': [c['category'] for c in categories],
        'page': page,
        'page_size': page_size
    })


@article_bp.route('/<int:article_id>', methods=['GET'])
@login_required()
def get_article(article_id):
    """获取文章详情，同时增加浏览次数"""
    user = request.current_user
    item = execute_query(
        'SELECT a.*, u.real_name as author_name '
        'FROM articles a LEFT JOIN users u ON a.author_id = u.id '
        'WHERE a.id = %s AND a.status = 1',
        (article_id,),
        fetch_one=True
    )
    if not item:
        return error('文章不存在')

    execute_update('UPDATE articles SET view_count = view_count + 1 WHERE id = %s', (article_id,))
    item['view_count'] += 1
    item['is_liked'] = False
    item['is_favorited'] = False
    item.setdefault('like_count', 0)

    if _check_db_feature('article_likes', 'SELECT 1 FROM article_likes LIMIT 1'):
        try:
            liked = execute_query(
                'SELECT id FROM article_likes WHERE user_id = %s AND article_id = %s',
                (user['id'], article_id), fetch_one=True
            )
            favorited = execute_query(
                'SELECT id FROM article_favorites WHERE user_id = %s AND article_id = %s',
                (user['id'], article_id), fetch_one=True
            )
            item['is_liked'] = bool(liked)
            item['is_favorited'] = bool(favorited)
        except Exception:
            pass

    return success(item)


@article_bp.route('/<int:article_id>/like', methods=['POST'])
@login_required()
def like_article(article_id):
    """点赞文章"""
    user_id = request.current_user['id']
    existing = execute_query(
        'SELECT id FROM article_likes WHERE user_id = %s AND article_id = %s',
        (user_id, article_id), fetch_one=True
    )
    if existing:
        return error('已经点赞过了')

    execute_update('INSERT INTO article_likes (user_id, article_id) VALUES (%s, %s)', (user_id, article_id))
    execute_update('UPDATE articles SET like_count = like_count + 1 WHERE id = %s', (article_id,))
    count = execute_query('SELECT like_count FROM articles WHERE id = %s', (article_id,), fetch_one=True)
    return success({'like_count': count['like_count']}, '点赞成功')


@article_bp.route('/<int:article_id>/like', methods=['DELETE'])
@login_required()
def unlike_article(article_id):
    """取消点赞"""
    user_id = request.current_user['id']
    result = execute_update(
        'DELETE FROM article_likes WHERE user_id = %s AND article_id = %s', (user_id, article_id)
    )
    if result:
        execute_update('UPDATE articles SET like_count = GREATEST(like_count - 1, 0) WHERE id = %s', (article_id,))
    count = execute_query('SELECT like_count FROM articles WHERE id = %s', (article_id,), fetch_one=True)
    return success({'like_count': count['like_count']}, '已取消点赞')


@article_bp.route('/<int:article_id>/favorite', methods=['POST'])
@login_required()
def favorite_article(article_id):
    """收藏文章"""
    user_id = request.current_user['id']
    existing = execute_query(
        'SELECT id FROM article_favorites WHERE user_id = %s AND article_id = %s',
        (user_id, article_id), fetch_one=True
    )
    if existing:
        return error('已经收藏过了')

    execute_update('INSERT INTO article_favorites (user_id, article_id) VALUES (%s, %s)', (user_id, article_id))
    return success(message='收藏成功')


@article_bp.route('/<int:article_id>/favorite', methods=['DELETE'])
@login_required()
def unfavorite_article(article_id):
    """取消收藏"""
    user_id = request.current_user['id']
    execute_update(
        'DELETE FROM article_favorites WHERE user_id = %s AND article_id = %s', (user_id, article_id)
    )
    return success(message='已取消收藏')
