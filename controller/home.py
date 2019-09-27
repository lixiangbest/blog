# coding=utf-8

# 系统包
from tornado.web import authenticated

# 自定义包
from .base import BaseHandler
from .admin_article import ArticleAndCommentsFlush

from model.pager import Pager
from model.constants import Constants
from model.search_params.article_params import ArticleSearchParams
from model.search_params.comment_params import CommentSearchParams
from service.user_service import UserService
from service.article_service import ArticleService
from service.comment_service import CommentService

# 首页
class HomeHandler(BaseHandler):
    def get(self):
        # 分页
        pager = Pager(self)
        article_search_params = ArticleSearchParams(self)
        article_search_params.show_article_type = True
        article_search_params.show_source = True
        article_search_params.show_summary = True
        article_search_params.show_comments_count = True
        future = self.async_do(ArticleService.page_articles, self.db, pager, article_search_params)
        # future.result() 会阻塞调用
        pager = future.result()
        # self.render("base.html", base_url=self.reverse_url('index'), pager=pager, article_search_params=article_search_params)
        self.render("index.html", base_url=self.reverse_url('index'), pager=pager, article_search_params=article_search_params)

# 文章详情
class ArticleHandler(BaseHandler):
    async def get(self, article_id):
        # 获取文章详情
        article = await self.loop_current.run_in_executor(self.thread_executor, ArticleService.get_article_all, self.db, article_id, True, 1)
        if article:
            comments_pager = Pager(self)
            comment_search_params = CommentSearchParams(self)
            comment_search_params.article_id = article_id
            # 获取文章对应的评论
            comments_pager = await self.loop_current.run_in_executor(self.thread_executor, CommentService.page_comments, self.db, comments_pager, comment_search_params)
            self.render("article_detials.html", article=article, comments_pager=comments_pager)
        else:
            self.write_error(404)

# 文章评论
class ArticleCommentHandler(BaseHandler, ArticleAndCommentsFlush):
    async def post(self, article_id):
        comment = dict(
            content=self.get_argument('content'), # 评论内容
            author_name=self.get_argument('author_name'), # 昵称
            author_email=self.get_argument('author_email'), # 邮箱
            article_id=article_id, # 文章id
            comment_type=self.get_argument('comment_type', None), # 评论类型
            rank = Constants.COMMENT_RANK_ADMIN if self.current_user else Constants.COMMENT_RANK_NORMAL,
            reply_to_id = self.get_argument('reply_to_id', None), # 回复的评论id
            reply_to_floor = self.get_argument('reply_to_floor', None), # 回复的评论floor
        )
        comment_saved = await self.loop_current.run_in_executor(self.thread_executor, CommentService.add_comment, self.db, article_id, comment)
        if comment_saved:
            # yield self.flush_comments_cache(Constants.FLUSH_COMMENT_ACTION_ADD, comment_saved)
            self.site_info.comment_count = self.site_info.comment_count + 1
            self.add_message('success', '评论成功')
        else:
            self.add_message('danger', '评论失败')
        next_url = self.get_argument('next', None)
        if next_url:
            self.redirect(next_url)
        else:
            # 跳转到文章详情页
            self.redirect(self.reverse_url('article', article_id)+"?pageNo=-1#comments")

# 文章类型
class ArticleTypeHandler(BaseHandler):
    async def get(self, type_id):
        pager = Pager(self)
        article_search_params = ArticleSearchParams(self)
        article_search_params.show_article_type=True
        article_search_params.show_source=True
        article_search_params.show_summary=True
        article_search_params.show_comments_count = True
        article_search_params.articleType_id = type_id
        pager = await self.loop_current.run_in_executor(self.thread_executor, ArticleService.page_articles, self.db, pager, article_search_params)
        self.render("index.html", base_url=self.reverse_url('articleType', type_id),
                    pager=pager, article_search_params=article_search_params)

# 文章来源
class articleSourceHandler(BaseHandler):
    async def get(self, source_id):
        pager = Pager(self)
        article_search_params = ArticleSearchParams(self)
        article_search_params.show_article_type=True
        article_search_params.show_source=True
        article_search_params.show_summary=True
        article_search_params.show_comments_count = True
        article_search_params.source_id = source_id
        pager = await self.loop_current.run_in_executor(self.thread_executor, ArticleService.page_articles, self.db, pager, article_search_params)
        self.render("index.html", base_url=self.reverse_url('articleSource', source_id),
                    pager=pager, article_search_params=article_search_params)

# 后台管理员用户登录
class LoginHandler(BaseHandler):
    # 管理后台登录页面
    def get(self):
        next_url = self.get_argument('next', '/')
        # 已登录则直接跳转
        if self.current_user:
            self.redirect(next_url)
        self.render("auth/login.html", next_url=next_url)

    # 管理后台登录API
    async def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        next_url = self.get_argument('next', '/')
        # 已登录则直接跳转
        if self.current_user:
            self.redirect(next_url)
        future = self.async_do(UserService.get_user, self.db, username)
        user = future.result()
        if user is not None and user.password == password:
            self.add_message('success', u'登陆成功！欢迎回来，{0}!'.format(username))
            # 登录成功，保存用户会话
            await self.save_login_user(user)
            self.redirect(next_url)
        else:
            self.add_message('danger', u'登陆失败！用户名或密码错误，请重新登陆。')
            # 重新登录
            self.get()

# 后台管理员用户退出
class LogoutHandler(BaseHandler):
    @authenticated
    async def get(self):
        await self.logout()
        self.add_message('success', u'您已退出登陆。')
        self.redirect("/")


