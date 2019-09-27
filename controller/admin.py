# coding=utf-8
from tornado.web import authenticated

from .base import BaseHandler
# from tornado.gen import coroutine
from service.user_service import UserService

# 管理平台首页
class AdminAccountHandler(BaseHandler):
    @authenticated
    def get(self):
        self.render("admin/admin_account.html")

    @authenticated
    async def post(self, require):
        # 修改信息
        if require == "edit-user-info":
            await self.edit_user_info()
        # 修改密码
        elif require == "change-password":
            self.change_password()

    @authenticated
    # 修改信息
    async def edit_user_info(self):
        user_info = {"username": self.get_argument("username"), "email": self.get_argument("email")}
        future = self.async_do(UserService.update_user_info, self.db, self.current_user.name,
                                   self.get_argument("password"), user_info)
        user = future.result()
        if user:
            await self.save_login_user(user)
            self.add_message('success', u'修改用户信息成功!')
        else:
            self.add_message('danger', u'修改用户信息失败！密码不正确!')
        # 页面跳转
        self.redirect(self.reverse_url("admin.account"))

    @authenticated
    # 修改密码
    def change_password(self):
        old_password = self.get_argument("old_password")
        new_password = self.get_argument("password")
        future = self.async_do(UserService.update_password, self.db, self.current_user.name,
                                    old_password, new_password)
        count = future.result()
        if count > 0:
            self.add_message('success', u'修改密码成功!')
        else:
            self.add_message('danger', u'修改密码失败！')
        self.redirect(self.reverse_url("admin.account"))

class AdminHelpHandler(BaseHandler):
    @authenticated
    def get(self):
        self.render('admin/help_page.html')
