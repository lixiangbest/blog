# coding=utf-8

# __all__ = ['article_service', 'article_type_service', 'blog_view_service',
#            'comment_service', 'custom_service', 'init_service',
#            'menu_service', 'plugin_service', 'pubsub_service', 'user_service']

class BaseService():
    @staticmethod
    def query_pager(query, pager, count=None):
        # 记录条数
        if count:
            pager.set_total_count(count)
        else:
            pager.set_total_count(query.count())
        # 生成分页SQL
        query_result = pager.build_query(query)
        # 获取SQL结果
        pager.set_result(query_result.all())
        return pager
