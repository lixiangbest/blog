# coding=utf-8
import hashlib
import urllib

import datetime
# from tornado import ioloop
import tornado.web
from tornado.ioloop import IOLoop
# from tornado import gen
from tornado.escape import url_escape

from model.site_info import SiteCollection
from config import session_keys, config, cookie_keys
from extends.session_tornadis import Session
from model.logined_user import LoginUser
from service.init_service import SiteCacheService
from service.blog_view_service import BlogViewService
from service.custom_service import BlogInfoService
from service.plugin_service import PluginService
from service.article_service import ArticleService
from service.comment_service import CommentService

# 基础请求类
# https://tornado-zh.readthedocs.io/zh/latest/guide/structure.html
# 复写RequestHandler的方法
# 1. 在每次请求时生成一个新的 RequestHandler 对象
# 2. initialize() 被 Application 配置中的初始化参数被调用. initialize通常应该只保存成员变量传递的参数; 它不可能产生任何输出或者调用方法, 例如 send_error.
# 3. prepare() 被调用. 这在你所有处理子类共享的基 类中是最有用的, 无论是使用哪种HTTP方法, prepare 都会被调用. prepare 可能会产生输出; 如果它调用 finish (或者 redirect, 等), 处理会在这里结束.
# 4. 其中一种HTTP方法被调用: get(), post(), put(), 等. 如果URL的正则表达式包含捕获组, 它们会被作为参数传递给这个方法.
# 5. 当请求结束, on_finish() 方法被调用. 对于同步处理程序会在 get() (等)后立即返回; 对于异步处理程序,会在调用 finish() 后返回.
# 调用顺序，initialize->prepare->get/post->on_finish
class BaseHandler(tornado.web.RequestHandler):
    # 每次请求初始化
    def initialize(self):
        self.session = None
        self.db_session = None
        self.session_save_tag = False
        self.session_expire_time = 604800  # 7*24*60*60秒
        self.thread_executor = self.application.thread_executor
        self.cache_manager = self.application.cache_manager
        self.async_do = self.thread_executor.submit
        self.loop_current = IOLoop.current()
        self.site_info = SiteCollection

    # 登录界面
    def login_url(self):
        return self.get_login_url()+"?next="+url_escape(self.request.uri)

    # 每次请求时先调用
    async def prepare(self):
        # await self.init_session()
        if not self.session:
            self.session = Session(self)

        # 如果已登录
        session_id = self.session.get_session_id()
        if session_id:
            uinfo = await self.session.get()
            self.current_user = LoginUser(uinfo['login_user'])

        # if session_keys['login_user'] in self.session:
        #     self.current_user = LoginUser(self.session[session_keys['login_user']])

        # 添加pv和uv
        await self.add_pv_uv()
        # 获取博客信息
        if self.site_info.navbar is None:
            # 博客概况
            blog = BlogInfoService.get_blog_info(self.db)
            self.site_info.title = blog.title
            self.site_info.signature = blog.signature
            self.site_info.navbar = blog.navbar
            # 插件列表
            plugin = PluginService.list_plugins(self.db)
            self.site_info.plugins = plugin
            # 今日uv和pv
            view = BlogViewService.get_blog_view(self.db)
            self.site_info.todaypv = view.pv
            self.site_info.todayuv = view.uv
            # 文章来源
            self.site_info.article_sources = ArticleService.get_article_sources(self.db)
            # 文章数量
            self.site_info.article_count = ArticleService.get_article_count(self.db)
            # 评论数
            self.site_info.comment_count = CommentService.get_comment_count(self.db)

    #  增加pv，uv, 调用该方法可以不用yield阻塞以达到与主代码异步执行
    #  每次调用pv+1, uv根据cookie每24小时只+1
    #  因为要与主代码异步执行，所以要使用独立的db连接
    async def add_pv_uv(self):
        # 统计pv
        add_pv = 1
        # 统计uv
        add_uv = 0
        date = datetime.date.today()
        # 上次访问的日期
        last_view_day = self.get_secure_cookie(cookie_keys['uv_key_name'], None)
        # 统计uv
        if not last_view_day or int(last_view_day) != date.day:
            add_uv = 1
            # 上次访问的日期记录cookie
            self.set_secure_cookie(cookie_keys['uv_key_name'], str(date.day), 1)

        # 记录pv和uv
        # await SiteCacheService.add_pv_uv(self.cache_manager, add_pv, add_uv, is_pub_all=True, pubsub_manager=self.pubsub_manager)
        await SiteCacheService.add_pv_uv(self.cache_manager, add_pv, add_uv, is_pub_all=False, pubsub_manager=self.pubsub_manager)

        # 使用线程池统计博客访问量
        future = self.async_do(BlogViewService.add_blog_view, self.db, add_pv, add_uv, date)
        # future.result() 会阻塞调用
        future.result()

    # redis session连接初始化
    # async def init_session(self):
    #     if not self.session:
    #         self.session = Session(self)
    #         yield self.session.init_fetch()

    @property
    def db(self):
        if not self.db_session:
            # 从连接池获取数据库连接
            self.db_session = self.application.db_pool()
        return self.db_session

    @property
    def pubsub_manager(self):
        return self.application.pubsub_manager

    # 保存session
    # def save_session(self):
    #     self.session_save_tag = True

    # 保存管理员用户登录成功的session会话
    async def save_login_user(self, user):
        login_user = LoginUser(None)
        login_user['id'] = user.id
        login_user['name'] = user.username
        # 获取通用头像
        login_user['avatar'] = self.get_gravatar_url(user.email)
        login_user['email'] = user.email
        self.session[session_keys['login_user']] = login_user
        self.current_user = login_user
        # self.save_session()
        # 保存到redis
        await self.session.save(self.session_expire_time)

    # 登出
    async def logout(self):
        await self.session.delete()
        # if session_keys['login_user'] in self.session:
        #     del self.session[session_keys['login_user']]
            # self.save_session()
        self.current_user = None

    # 判断消息是否存在
    def has_message(self):
        if not self.session:
            self.session = Session(self)
        
        session_id = self.session.get_session_id()
        if session_id in self.session.msg:
            return bool(self.session.msg[session_id])
        else:
            return False

        # if self.session and session_keys['messages'] in self.session:
        #     return bool(self.session[session_keys['messages']])
        # else:
        #     return False

    # 添加消息 category:['success','info', 'warning', 'danger']
    def add_message(self, category, message):
        item = {'category': category, 'message': message}
        item = str(item)
        session_id = self.session.get_session_id()
        if session_id in self.session.msg:
            self.session.msg[session_id].append(item)
        else:
            self.session.msg[session_id] = [item]
        # if session_keys['messages'] in self.session and \
        #         isinstance(self.session[session_keys['messages']], dict):
        #     self.session[session_keys['messages']].append(item)
        # else:
        #     self.session[session_keys['messages']] = [item]
        # self.save_session()

    # 读取消息列表
    def read_messages(self):
        session_id = self.session.get_session_id()
        if session_id in self.session.msg:
            all_messages = self.session.msg[session_id]
            self.session.msg[session_id] = []
            return all_messages
        # if session_keys['messages'] in self.session:
        #     all_messages = self.session.pop(session_keys['messages'], None)
        #     # self.save_session()
        #     return all_messages
        return None

    def write_json(self, json):
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json)

    # 错误处理
    def write_error(self, status_code, **kwargs):
        # 500 {'exc_info': (<class 'UnicodeEncodeError'>, UnicodeEncodeError('locale', '%Y年%m月%d日', 2, 3, 'Illegal byte sequence'),
        # <traceback object at 0x00000262B156D088>)}
        if status_code == 403:
            self.render("403.html")
        elif status_code == 404 or status_code == 405:
            self.render("404.html")
        elif status_code == 500:
            self.render("500.html")

        # if not self._finished:
        #     super(BaseHandler, self).write_error(status_code, **kwargs)

    # 获取通用头像
    def get_gravatar_url(self, email, default=None, size=40):
        body = {'s': str(size)}
        if default:
            body["d"] = default;
        elif config['default_avatar_url']:
            body["d"] = config['default_avatar_url']
        gravatar_url = "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower().encode('utf-8')).hexdigest() + "?"
        gravatar_url += urllib.parse.urlencode(body)
        return gravatar_url

    # 请求结束时调用
    def on_finish(self):
        if self.db_session:
            # 关闭会话，连接池回收数据库连接
            self.db_session.close()
            # 数据库连接池状态
            # print("db_info:", self.application.db_pool.kw['bind'].pool.status())


