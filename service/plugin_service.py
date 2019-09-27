# coding=utf-8
# import logging
from loguru import logger

from sqlalchemy import func
from model.models import Plugin
from model.search_params.plugin_params import PluginSearchParams
from . import BaseService

# logger = logging.getLogger(__name__)

class PluginService():
    @staticmethod
    def get(db_session, plugin_id):
        plugin = db_session.query(Plugin).get(plugin_id)
        return plugin

    @staticmethod
    def get_editable(db_session, plugin_id):
        plugin = db_session.query(Plugin).get(plugin_id)
        if plugin:
            plugin = plugin if plugin.content != 'system_plugin' else None
        return plugin

    @staticmethod
    def list_plugins(db_session):
        plugins = db_session.query(Plugin).order_by(Plugin.order.asc()).all()
        return plugins

    @staticmethod
    # 插件分页
    def page_plugins(db_session, pager, search_params):
        query = db_session.query(Plugin)
        # 搜索参数
        if search_params:
            # 升序排序
            if search_params.order_mode == PluginSearchParams.ORDER_MODE_ORDER_ASC:
                query = query.order_by(Plugin.order.asc())
        pager = BaseService.query_pager(query, pager)
        return pager

    @staticmethod
    def save(db_session, plugin):
        try:
            plugin_to_save = Plugin(**plugin)
            plugin_to_save.order = PluginService.get_max_order(db_session) + 1
            db_session.add(plugin_to_save)
            db_session.commit()
            return plugin_to_save
        except Exception as e:
            logger.exception(e)
        return None

    @staticmethod
    def get_max_order(db_session):
        max_order = db_session.query(func.max(Plugin.order)).scalar()
        if max_order is None:
            max_order = 0
        return max_order

    @staticmethod
    # 插件顺序上升一位
    def sort_up(db_session, plugin_id):
        plugin = db_session.query(Plugin).get(plugin_id)
        if plugin:
            # 找到比当前排序值小的
            plugin_up = db_session.query(Plugin).\
                filter(Plugin.order < plugin.order).order_by(Plugin.order.desc()).first()
            if plugin_up:
                # 修改排序,排序值交换
                order_tmp = plugin.order
                plugin.order = plugin_up.order
                plugin_up.order = order_tmp
                db_session.commit()
            return True
        return False

    @staticmethod
    # 插件顺序下降一位
    def sort_down(db_session, plugin_id):
        plugin = db_session.query(Plugin).get(plugin_id)
        if plugin:
            # 找到比当前排序值大的
            plugin_up = db_session.query(Plugin).\
                filter(Plugin.order > plugin.order).order_by(Plugin.order.asc()).first()
            if plugin_up:
                # 修改排序,排序值交换
                order_tmp = plugin.order
                plugin.order = plugin_up.order
                plugin_up.order = order_tmp
                db_session.commit()
            return True
        return False

    @staticmethod
    # 插件禁用和启用
    def update_disabled(db_session, plugin_id, disabled):
        update_count = db_session.query(Plugin).filter(Plugin.id == plugin_id).update({Plugin.disabled:disabled})
        if update_count:
            db_session.commit()
        return update_count

    @staticmethod
    # 插件删除
    def delete(db_session, plugin_id):
        plugin = PluginService.get_editable(db_session, plugin_id)
        if plugin:
            db_session.delete(plugin)
            db_session.commit()
            return True
        return False

    @staticmethod
    # 插件编辑
    def update(db_session, plugin_id, plugin_to_update):
        plugin = PluginService.get_editable(db_session, plugin_id)
        if plugin:
            plugin.title = plugin_to_update['title']
            plugin.note = plugin_to_update['note']
            plugin.content = plugin_to_update['content']
            db_session.commit()
            return True
        return False

