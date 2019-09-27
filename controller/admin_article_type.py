# coding=utf-8
# from tornado.gen import coroutine
import asyncio
from tornado.web import authenticated
# from tornado.ioloop import IOLoop

from .base import BaseHandler
from model.pager import Pager
from model.search_params.menu_params import MenuSearchParams
from model.search_params.article_type_params import ArticleTypeSearchParams
from service.menu_service import MenuService
from service.init_service import SiteCacheService
from service.article_type_service import ArticleTypeService

class AdminArticleTypeBaseHandler(BaseHandler):
    # 菜单刷新
    async def flush_menus(self, menus=None, article_types_not_under_menu=None):
        if menus is None:
            menus = await self.loop_current.run_in_executor(self.thread_executor, MenuService.list_menus, self.db, True)

        if article_types_not_under_menu is None:
            article_types_not_under_menu = await self.loop_current.run_in_executor(self.thread_executor, ArticleTypeService.list_article_types_not_under_menu, self.db)

        # 更新菜单缓存
        # await SiteCacheService.update_menus(self.cache_manager, menus, article_types_not_under_menu,
        #                                     is_pub_all=True, pubsub_manager=self.pubsub_manager)

# 博文分类
class AdminArticleTypeHandler(AdminArticleTypeBaseHandler):
    # 博文分类模板显示
    async def get(self, *require):
        if require:
            if len(require) == 2:
                article_type_id = require[0]
                action = require[1]
                if action == 'delete':
                    await self.delete_get(article_type_id)
        else:
            await self.page_get()

    # 新增或更新
    async def post(self, *require):
        if require:
            if len(require) == 1:
                # 新增
                if require[0] == 'add':
                    await self.add_post()
            elif len(require) == 2:
                article_type_id = require[0]
                action = require[1]
                if action == 'update':
                    await self.update_post(article_type_id)

    @authenticated
    # 博文分类
    async def page_get(self):
        pager = Pager(self)
        search_param = ArticleTypeSearchParams(self)
        search_param.show_setting = True
        search_param.show_articles_count = True
        pager = await self.loop_current.run_in_executor(self.thread_executor, ArticleTypeService.page_article_types, self.db, pager, search_param)
        menus = await self.loop_current.run_in_executor(self.thread_executor, MenuService.list_menus, self.db)
        # menus = yield self.async_do(MenuService.list_menus, self.db)
        self.render("admin/manage_articleTypes.html", pager=pager, menus=menus)

    @authenticated
    # 删除博文分类
    async def delete_get(self, article_type_id):
        update_count = await self.loop_current.run_in_executor(self.thread_executor, ArticleTypeService.delete, self.db, article_type_id)
        if update_count:
            # yield self.flush_menus()
            self.add_message('success', '删除成功!')
        else:
            self.add_message('danger', '删除失败！')
        redirect_url = self.reverse_url('admin.articleTypes')
        if self.request.query:
            redirect_url += "?" + self.request.query
        self.redirect(redirect_url)

    @authenticated
    # 新增博文分类
    async def add_post(self):
        menu_id = int(self.get_argument("menu_id")) \
            if self.get_argument("menu_id") else None

        article_type = dict(
            name = self.get_argument("name"), # 分类名称
            setting_hide = self.get_argument("setting_hide") == 'true', # 是否隐藏
            introduction = self.get_argument("introduction"), # 分类介绍
            menu_id = menu_id if menu_id > 0 else None, # 所属导航
        )

        added = await self.loop_current.run_in_executor(self.thread_executor, ArticleTypeService.add_article_type, self.db, article_type)
        if added:
            # await self.flush_menus()
            self.add_message('success', '保存成功!')
        else:
            self.add_message('danger', '保存失败!分类已存在!')

        redirect_url = self.reverse_url('admin.articleTypes')
        if self.request.query:
            redirect_url += "?" + self.request.query
        self.redirect(redirect_url)

    @authenticated
    # 修改博文分类
    async def update_post(self, article_type_id):
        menu_id = int(self.get_argument("menu_id")) \
            if self.get_argument("menu_id") else None
        article_type = dict(
            id = article_type_id, # 类型id
            name = self.get_argument("name"), # 菜单名称
            setting_hide = self.get_argument("setting_hide") == 'true', # 属性
            introduction = self.get_argument("introduction"), # 分类介绍
            menu_id = menu_id if menu_id > 0 else None, # 所属导航
        )
        updated = await self.loop_current.run_in_executor(self.thread_executor, ArticleTypeService.update_article_type, self.db, article_type_id, article_type)
        if updated:
            # yield self.flush_menus()
            self.add_message('success', '修改成功!')
        else:
            self.add_message('danger', '保存失败!分类已存在!')
        redirect_url = self.reverse_url('admin.articleTypes')
        if self.request.query:
            redirect_url += "?" + self.request.query
        self.redirect(redirect_url)

# 博客分类菜单
class AdminArticleTypeNavHandler(AdminArticleTypeBaseHandler):
    # 模板显示
    async def get(self, *require):
        if require:
            if len(require) == 2:
                menu_id = require[0]
                action = require[1]
                if action == 'sort-up':
                    await self.sort_up_get(menu_id)
                elif action == 'sort-down':
                    await self.sort_down_get(menu_id)
                elif action == 'delete':
                    await self.delete_get(menu_id)
        else:
            await self.page_get()

    # 导航新增或编辑
    async def post(self, *require):
        if require:
            if len(require) == 1:
                if require[0] == 'add':
                    await self.add_post()
            elif len(require) == 2:
                menu_id = require[0]
                action = require[1]
                if action == 'update':
                    await self.update_post(menu_id)

    @authenticated
    # 导航新增
    async def add_post(self):
        menu = dict(name=self.get_argument('name'),)
        added = await self.loop_current.run_in_executor(self.thread_executor, MenuService.add_menu, self.db, menu)
        if added:
            # yield self.flush_menus()
            self.add_message('success', '保存成功!')
        else:
            self.add_message('danger', '保存失败!菜单已存在!')
        redirect_url = self.reverse_url('admin.articleTypeNavs')
        if self.request.query:
            redirect_url += "?"+self.request.query
        self.redirect(redirect_url)

    @authenticated
    # 导航更新
    async def update_post(self, menu_id):
        menu = dict(name=self.get_argument('name'), )
        update_count = await self.loop_current.run_in_executor(self.thread_executor, MenuService.update, self.db, menu_id, menu)
        if update_count:
            # yield self.flush_menus()
            self.add_message('success', '修改成功!')
        else:
            self.add_message('danger', '修改失败!菜单已存在!')
        redirect_url = self.reverse_url('admin.articleTypeNavs')
        if self.request.query:
            redirect_url += "?"+self.request.query
        self.redirect(redirect_url)

    @authenticated
    # 菜单首页
    async def page_get(self):
        pager = Pager(self)
        menu_search_params = MenuSearchParams(self)
        pager = await self.loop_current.run_in_executor(self.thread_executor, MenuService.page_menus, self.db, pager, menu_search_params)
        self.render("admin/manage_articleTypes_nav.html", pager=pager)

    @authenticated
    # 排序上升一位
    async def sort_up_get(self, menu_id):
        # updated = yield self.async_do(MenuService.sort_up, self.db, menu_id)
        updated = await self.loop_current.run_in_executor(self.thread_executor, MenuService.sort_up, self.db, menu_id)
        if updated:
            # yield self.flush_menus()
            self.add_message('success', '导航升序成功!')
        else:
            self.add_message('danger', '操作失败！')

        redirect_url = self.reverse_url('admin.articleTypeNavs')
        if self.request.query:
            redirect_url += "?"+self.request.query
        self.redirect(redirect_url)

    @authenticated
    # 排序下降一位
    async def sort_down_get(self, menu_id):
        updated = await self.loop_current.run_in_executor(self.thread_executor, MenuService.sort_down, self.db, menu_id)
        if updated:
            # yield self.flush_menus()
            self.add_message('success', '导航降序成功!')
        else:
            self.add_message('danger', '操作失败！')

        redirect_url = self.reverse_url('admin.articleTypeNavs')
        if self.request.query:
            redirect_url += "?"+self.request.query
        self.redirect(redirect_url)

    @authenticated
    # 排序上升一位
    async def sort_up_get(self, menu_id):
        updated = await self.loop_current.run_in_executor(self.thread_executor, MenuService.sort_up, self.db, menu_id)
        if updated:
            # yield self.flush_menus()
            self.add_message('success', '导航升序成功!')
        else:
            self.add_message('danger', '操作失败！')

        redirect_url = self.reverse_url('admin.articleTypeNavs')
        if self.request.query:
            redirect_url += "?"+self.request.query
        self.redirect(redirect_url)

    @authenticated
    # 导航删除
    async def delete_get(self, menu_id):
        # update_count = yield self.async_do(MenuService.delete, self.db, menu_id)
        update_count = await self.loop_current.run_in_executor(self.thread_executor, MenuService.delete, self.db, menu_id)
        if update_count:
            # yield self.flush_menus()
            self.add_message('success', u'删除成功!')
        else:
            self.add_message('danger', u'保存失败！')

        redirect_url = self.reverse_url('admin.articleTypeNavs')
        if self.request.query:
            redirect_url += "?"+self.request.query
        self.redirect(redirect_url)


