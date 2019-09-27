# coding=utf-8
# from tornado.gen import coroutine
from tornado.web import authenticated

from .base import BaseHandler

from config import session_keys
from model.models import Article
from model.constants import Constants
from service.article_service import ArticleService
from service.article_type_service import ArticleTypeService
from service.init_service import SiteCacheService
from service.comment_service import CommentService
from model.search_params.article_params import ArticleSearchParams
from model.search_params.comment_params import CommentSearchParams
from model.pager import Pager


class ArticleAndCommentsFlush(object):
    async def flush_article_cache(self, action, article):
        yield SiteCacheService.update_article_action(self.cache_manager, action, article,
                                                     is_pub_all=True, pubsub_manager=self.pubsub_manager)

    async def flush_comments_cache(self, action, comments):
        yield SiteCacheService.update_comment_action(self.cache_manager, action, comments,
                                                     is_pub_all=True, pubsub_manager=self.pubsub_manager)

# 管理后台文章控制器
class AdminArticleHandler(BaseHandler, ArticleAndCommentsFlush):
    # 管理博文静态页
    async def get(self, *require):
        if require:
            if len(require) == 1:
                action = require[0]
                # 新增静态页
                if action == 'submit':
                    await self.submit_get()
                # 编辑静态页
                elif action.isdigit():
                    article_id = int(action)
                    await self.article_get(article_id)
        else:
            self.page_get()

    # 文章提交API
    async def post(self, *require):
        if require:
            if len(require) == 1:
                # 新增
                if require[0] == 'submit':
                    await self.submit_post()
                # 编辑
                elif require[0].isdigit():
                    article_id = int(require[0])
                    await self.update_post(article_id)
            elif len(require) == 2:
                article_id = require[0] # 文章id
                action = require[1] # 文章操作
                # 删除
                if action == 'delete':
                    await self.delete_post(article_id)

    @authenticated
    # 文章列表页
    def page_get(self):
        pager = Pager(self)
        article_search_params = ArticleSearchParams(self)
        # article_types = await IOLoop.current().run_in_executor(self.thread_executor, ArticleTypeService.list_simple, self.db)
        future1 = self.async_do(ArticleTypeService.list_simple, self.db)
        article_types = future1.result()
        future2 = self.async_do(ArticleService.page_articles, self.db, pager, article_search_params)
        pager = future2.result()
        self.render("admin/manage_articles.html", article_types=article_types, pager=pager,
                    article_search_params=article_search_params)

    @authenticated
    # 文章编辑模板页
    async def article_get(self, article_id):
        article_types = await self.loop_current.run_in_executor(self.thread_executor, ArticleTypeService.list_simple, self.db)
        article = await self.loop_current.run_in_executor(self.thread_executor, ArticleService.get_article_all, self.db, article_id, True)
        self.render("admin/submit_articles.html", article_types=article_types, article=article)

    @authenticated
    # 文章新增模板页
    async def submit_get(self):
        # 草稿
        article_draft = self.session.pop(session_keys['article_draft'], None)
        article = None
        if article_draft:
            source_id = article_draft.get("source_id")
            type_id = article_draft.get("articleType_id")
            article = Article(source_id=int(source_id) if source_id else None,
                              title=article_draft.get("title"),
                              articleType_id=int(type_id) if type_id else None,
                              content=article_draft.get("content"),
                              summary=article_draft.get("summary"))

        article_types = await self.loop_current.run_in_executor(self.thread_executor, ArticleTypeService.list_simple, self.db)
        self.render("admin/submit_articles.html", article_types=article_types, article=article)

    @authenticated
    # 文章新增
    async def submit_post(self):
        article = dict(
            source_id=self.get_argument("source_id"), # 来源
            title=self.get_argument("title"), # 标题
            articleType_id=self.get_argument("articleType_id"), # 博文分类
            content=self.get_argument("content"), # 内容
            summary=self.get_argument("summary"), # 摘要
        )
        article_saved = await self.loop_current.run_in_executor(self.thread_executor, ArticleService.add_article, self.db, article)
        if article_saved and article_saved.id:
            # yield self.flush_article_cache(Constants.FLUSH_ARTICLE_ACTION_ADD, article_saved)
            self.site_info.article_count =  self.site_info.article_count + 1
            self.site_info.article_sources = ArticleService.get_article_sources(self.db)
            self.add_message('success', '保存成功!')
            # self.redirect(self.reverse_url('article', article_saved.id))
            self.redirect(self.reverse_url('admin.articles'))
        else:
            self.add_message('danger', '保存失败！')
            self.session.article_draft[session_keys['article_draft']] = article # 保存到草稿箱
            # self.redirect(self.reverse_url('admin.article.action', 'submit'))
            self.redirect(self.reverse_url('admin.articles'))

    @authenticated
    # 文章编辑
    async def update_post(self, article_id):
        article = dict(
            id=article_id, # 来源
            source_id=self.get_argument("source_id"), # 标题
            title=self.get_argument("title"), # 博文分类
            articleType_id=self.get_argument("articleType_id"), # 博文分类
            content=self.get_argument("content"), # 内容
            summary=self.get_argument("summary"), # 摘要
        )
        article_updateds = await self.loop_current.run_in_executor(self.thread_executor, ArticleService.update_article, self.db, article)
        if article_updateds:
            # yield self.flush_article_cache(Constants.FLUSH_ARTICLE_ACTION_UPDATE, article=article_updateds)
            self.site_info.article_sources = ArticleService.get_article_sources(self.db)
            article_updated = article_updateds[0]
            self.add_message('success', '修改成功!')
            self.redirect(self.reverse_url('admin.article', article_updated.id))
        else:
            self.add_message('danger', '修改失败！')
            self.redirect(self.reverse_url('admin.article', article_id))

    @authenticated
    # 文章删除API
    async def delete_post(self, article_id):
        article_deleted, comments_deleted = await self.loop_current.run_in_executor(self.thread_executor, ArticleService.delete_article, self.db, article_id)
        if article_deleted:
            # yield self.flush_article_cache(Constants.FLUSH_ARTICLE_ACTION_REMOVE, article_deleted)
            # yield self.flush_comments_cache(Constants.FLUSH_COMMENT_ACTION_REMOVE, comments_deleted)
            self.site_info.article_count = self.site_info.article_count - 1
            self.site_info.comment_count = self.site_info.comment_count - len(comments_deleted)
            self.site_info.article_sources = ArticleService.get_article_sources(self.db)
            self.add_message('success', '删除成功,并删除{}条评论!'.format(len(comments_deleted)))
            # js脚本自动重载,不需要跳转
            # self.redirect(self.reverse_url('admin.articles'))
        else:
            self.add_message('danger', '删除失败！')
            # self.redirect(self.reverse_url('admin.articles'))

# 评论管理
class AdminArticleCommentHandler(BaseHandler, ArticleAndCommentsFlush):
    async def get(self):
        await self.page_get()

    # 提交
    async def post(self, *require):
        if require and len(require) == 3:
            article_id = require[0] # 文章id
            comment_id = require[1] # 评论id
            action = require[2]
            # 隐藏
            if action == 'disable':
                await self.disable_post(article_id, comment_id, True)
            # 显示
            elif action == 'enable':
                await self.disable_post(article_id, comment_id, False)
            # 删除
            elif action == 'delete':
                await self.delete_post(article_id, comment_id)

    @authenticated
    async def page_get(self):
        pager = Pager(self)
        comment_search_params = CommentSearchParams(self)
        comment_search_params.show_article_id_title = True
        comment_search_params.order_mode = CommentSearchParams.ORDER_MODE_CREATE_TIME_DESC
        comments_pager = await self.loop_current.run_in_executor(self.thread_executor, CommentService.page_comments, self.db, pager, comment_search_params)
        self.render("admin/manage_comments.html", pager=comments_pager)

    @authenticated
    # 隐藏和显示
    async def disable_post(self, article_id, comment_id, disabled):
        updated = await self.loop_current.run_in_executor(self.thread_executor, CommentService.update_comment_disabled, self.db, article_id, comment_id, disabled)
        if updated:
            self.add_message('success', '修改成功')
            self.write("success")
        else:
            self.add_message('danger', '修改失败！')
            self.write("error")

    @authenticated
    async def delete_post(self, article_id, comment_id):
        comment_deleted = await self.loop_current.run_in_executor(self.thread_executor, CommentService.delete_comment, self.db, article_id, comment_id)
        if comment_deleted:
            # yield self.flush_comments_cache(Constants.FLUSH_COMMENT_ACTION_REMOVE, comment_deleted)
            self.site_info.comment_count = self.site_info.comment_count - 1
            self.add_message('success', '删除成功')
            self.write("success")
        else:
            self.add_message('danger', '删除失败！')
            self.write("error")

