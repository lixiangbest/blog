# coding=utf-8
# from tornado.gen import coroutine
from tornado.web import authenticated

from .base import BaseHandler
from config import config
from model.pager import Pager
from model.search_params.plugin_params import PluginSearchParams
from service.custom_service import BlogInfoService
from service.init_service import SiteCacheService
from service.plugin_service import PluginService

# 基本信息
class AdminCustomBlogInfoHandler(BaseHandler):
    @authenticated
    def get(self):
        self.render("admin/custom_blog_info.html", navbar_styles=config['navbar_styles'])

    @authenticated
    async def post(self):
        info = dict(title=self.get_argument("title"), signature=self.get_argument("signature"),
                    navbar=self.get_argument("navbar"),)
        future = self.async_do(BlogInfoService.update_blog_info, self.db, info)
        blog_info = future.result()
        if blog_info:
            # 更新本地及redis缓存，并发布消息通知其他节点更新
            await SiteCacheService.update_blog_info(self.cache_manager, blog_info, is_pub_all=True, pubsub_manager=self.pubsub_manager)
            self.add_message('success', u'修改博客信息成功!')
        else:
            self.add_message('danger', u'修改失败！')
        self.redirect(self.reverse_url("admin.custom.blog_info"))

# 插件管理
class AdminCustomBlogPluginHandler(BaseHandler):
    @authenticated
    # 首页
    def index_get(self):
        # 实例化
        pager = Pager(self)
        # 插件搜索参数
        plugin_search_params = PluginSearchParams(self)
        # 插件列表和记录条数
        future = self.async_do(PluginService.page_plugins, self.db, pager, plugin_search_params)
        plugin_data = future.result()
        # print(plugin_data)
        self.render("admin/custom_blog_plugin.html", pager=plugin_data)

    # 插件管理路由
    def get(self, *require):
        if require:
            if len(require) == 1:
                # 插件信息
                if require[0] == 'add':
                    self.add_get()
            elif len(require) == 2:
                # 插件id
                plugin_id = require[0]
                # 操作
                action = require[1]
                # 上升一位
                if action == 'sort-up':
                    self.sort_up_get(plugin_id)
                # 下降一位
                elif action == 'sort-down':
                    self.sort_down_get(plugin_id)
                # 插件禁用
                elif action == 'disable':
                    self.set_disabled_get(plugin_id, True)
                # 插件启用
                elif action == 'enable':
                    self.set_disabled_get(plugin_id, False)
                # 插件删除
                elif action == 'delete':
                    self.delete_get(plugin_id)
                # 插件编辑
                elif action == 'edit':
                    self.edit_get(plugin_id)
        else:
            self.index_get()

    # 新增或编辑 API
    def post(self, *require):
        if require:
            if len(require) == 1:
                if require[0] == 'add':
                    self.add_post()
            elif len(require) == 2:
                plugin_id = require[0]
                action = require[1]
                if action == 'edit':
                    self.edit_post(plugin_id)

    @authenticated
    # 新增的模板页
    def add_get(self):
        self.render("admin/blog_plugin_add.html")

    @authenticated
    # 编辑模板页
    def edit_get(self, plugin_id):
        future = self.async_do(PluginService.get, self.db, plugin_id)
        plugin = future.result()
        self.render("admin/blog_plugin_edit.html", plugin=plugin)

    @authenticated
    # 当前排序上升一位
    def sort_up_get(self, plugin_id):
        future = self.async_do(PluginService.sort_up, self.db, plugin_id)
        updated = future.result()
        if updated:
            # 刷新插件缓存
            # yield self.flush_plugins()
            self.add_message('success', u'插件升序成功!')
        else:
            self.add_message('danger', u'操作失败！')
        self.redirect(self.reverse_url('admin.custom.blog_plugin')+"?"+self.request.query)

    @authenticated
    # 当前排序下降一位
    def sort_down_get(self, plugin_id):
        future = self.async_do(PluginService.sort_down, self.db, plugin_id)
        updated = future.result()
        if updated:
            # 刷新插件缓存
            # self.flush_plugins()
            self.add_message('success', u'插件降序成功!')
        else:
            self.add_message('danger', u'操作失败！')
        self.redirect(self.reverse_url('admin.custom.blog_plugin')+"?"+self.request.query)

    @authenticated
    # 对某个插件禁用
    def set_disabled_get(self, plugin_id, disabled):
        future = self.async_do(PluginService.update_disabled, self.db, plugin_id, disabled)
        updated_count = future.result()
        if updated_count:
            # yield self.flush_plugins()
            if disabled is True:
                self.add_message('success', u'插件禁用成功!')
            else:
                self.add_message('success', u'插件启用成功!')
        else:
            self.add_message('danger', u'操作失败！')
        self.redirect(self.reverse_url('admin.custom.blog_plugin')+"?"+self.request.query)

    @authenticated
    # 插件删除
    def delete_get(self, plugin_id):
        future = self.async_do(PluginService.delete, self.db, plugin_id)
        updated = future.result()
        if updated:
            # yield self.flush_plugins()
            self.add_message('success', u'插件删除成功!')
        else:
            self.add_message('danger', u'操作失败！')
        self.redirect(self.reverse_url('admin.custom.blog_plugin')+"?"+self.request.query)

    @authenticated
    # 新增插件
    def add_post(self):
        plugin = dict(title=self.get_argument('title'),note=self.get_argument('note'),
                      content=self.get_argument('content'),)
        future = self.async_do(PluginService.save, self.db, plugin)
        plugin_saved = future.result()
        if plugin_saved and plugin_saved.id:
            # yield self.flush_plugins()
            self.add_message('success', u'添加成功!')
        else:
            self.add_message('danger', u'添加失败！')
        # self.redirect(self.reverse_url('admin.custom.plugin.action', 'add'))
        self.redirect(self.reverse_url('admin.custom.blog_plugin') + "?" + self.request.query)

    @authenticated
    # 插件编辑
    def edit_post(self, plugin_id):
        plugin = dict(
            id=plugin_id,
            title=self.get_argument("title", None),
            note=self.get_argument("note", None),
            content=self.get_argument("content", None),
        )
        future = self.async_do(PluginService.update, self.db, plugin_id, plugin)
        updated = future.result()
        if updated:
            # yield self.flush_plugins()
            self.add_message('success', u'插件修改成功!')
        else:
            self.add_message('danger', u'操作失败！')
        self.redirect(self.reverse_url('admin.custom.blog_plugin')+"?"+self.request.query)

    # 刷新插件缓存
    # async def flush_plugins(self, plugins=None):
    #     if plugins is None:
    #         plugins = yield self.async_do(PluginService.list_plugins, self.db)
    #     yield SiteCacheService.update_plugins(self.cache_manager, plugins,
    #                                           is_pub_all=True, pubsub_manager=self.pubsub_manager)


