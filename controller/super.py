# coding=utf-8
# from tornado import gen

from .base import BaseHandler
from service.user_service import UserService

# 后台管理员初始化
class SuperHandler(BaseHandler):
    # 新增管理员静态页
    async def get(self):
        user_count = await self.loop_current.run_in_executor(self.thread_executor, UserService.get_count, self.db)
        if not user_count:
            self.render("super/init.html")
        else:
            self.write_error(404)

    # 新增管理员API
    async def post(self):
        user = dict(
            email=self.get_argument('email'),
            username=self.get_argument('username'),
            password=self.get_argument('password'),
        )
        user_saved = await self.loop_current.run_in_executor(self.thread_executor, UserService.save_user, self.db, user)
        if user_saved and user_saved.id:
            self.add_message('success', '创建成功!')
            self.redirect(self.reverse_url('login'))
        else:
            self.add_message('danger', '创建失败！')
            self.redirect(self.reverse_url('super.init'))

