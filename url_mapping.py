# coding=utf-8
import controller.home
import controller.admin
import controller.admin_custom
import controller.admin_article_type
import controller.admin_article
import controller.super

from tornado.web import url

# tornado中传递参数的几种方式
# 方法一 ：tornado路由可以使用正则表达式中的子表达式传递url参数。比如：
#   (r"/member//(\w*)/([01]*)", MemberHandler)
# 匹配以后，tornado会将字符串（）中匹配到的内容，作为参数传递到MemberHandler中去，因此我们在MemberHandler中定义get方法时增加参数：
# class MemberHandler(tornado.web.RequestHandler):
#     def get(self,data,num):
#         self.write(data)
#
# 方法二 ：self.get_argument()
# tornado的get和post提交的参数都可以通过self.get_argument()获得,只需要填写第一个参数值即可
# tornado中一次性获取所有的参数方法 self.get_arguments()
#
# 方法三 ：self.request.body
# tornado的参数存储在self.request.body内，通过json以后就可以直接取值，当初我在前端使用angular时,
# tornado就不能通过self.get_argument()获取到只能用这种办法获得angular post过来的数据。
# data = json.loads(self.request.body)
# keyword = data['content']
# url映射
handlers = [
    # 博客首页
    url(r"/", controller.home.HomeHandler, name="index"),
    # 登录
    url(r"/auth/login", controller.home.LoginHandler, name="login"),
    # 退出
    url(r"/auth/logout", controller.home.LogoutHandler, name="logout"),
    # 文章来源对应的文章列表
    url(r"/source/([0-9]+)/articles", controller.home.articleSourceHandler, name="articleSource"),
    # 文章类型对应的文章列表
    url(r"/type/([0-9]+)/articles", controller.home.ArticleTypeHandler, name="articleType"),
    # 文章详情
    url(r"/article/([0-9]+)", controller.home.ArticleHandler, name="article"),
    # 文章评论
    url(r"/article/([0-9]+)/comment", controller.home.ArticleCommentHandler, name="articleComment"),

    # admin
    # 后台管理员首页
    url(r"/admin/account", controller.admin.AdminAccountHandler, name="admin.account"),
    # 其他管理 -> 帮助
    url(r"/admin/help", controller.admin.AdminHelpHandler, name="admin.help"),
    # 用户账户 -> 修改密码，修改信息
    url(r"/admin/account/(change-password|edit-user-info)",
        controller.admin.AdminAccountHandler, name="admin.account.update"),
    # 基本信息 admin.custom
    url(r"/admin/custom/blog-info",
        controller.admin_custom.AdminCustomBlogInfoHandler, name="admin.custom.blog_info"),
    # 插件管理
    url(r"/admin/custom/blog-plugin",
        controller.admin_custom.AdminCustomBlogPluginHandler, name="admin.custom.blog_plugin"),
    url(r"/admin/custom/blog-plugin/(add)",
        controller.admin_custom.AdminCustomBlogPluginHandler, name="admin.custom.plugin.action"),
    # 对某个插件进行操作
    url(r"/admin/custom/blog-plugin/([0-9]+)/(sort-down|sort-up|disable|enable|edit|delete)",
        controller.admin_custom.AdminCustomBlogPluginHandler, name="admin.custom.plugin.update"),
    # 博文分类
    url(r"/admin/articleType", controller.admin_article_type.AdminArticleTypeHandler, name="admin.articleTypes"),
    url(r"/admin/articleType/(add)",
        controller.admin_article_type.AdminArticleTypeHandler, name="admin.articleType.action"),
    url(r"/admin/articleType/([0-9]+)/(delete|update)",
        controller.admin_article_type.AdminArticleTypeHandler, name="admin.articleType.update"),
    # 博文分类导航
    url(r"/admin/articleType/nav",
        controller.admin_article_type.AdminArticleTypeNavHandler, name="admin.articleTypeNavs"),
    url(r"/admin/articleType/nav/(add)",
        controller.admin_article_type.AdminArticleTypeNavHandler, name="admin.articleTypeNav.action"),
    url(r"/admin/articleType/nav/([0-9]+)/(sort-down|sort-up|delete|update)",
        controller.admin_article_type.AdminArticleTypeNavHandler, name="admin.articleTypeNav.update"),
    # 管理博文列表
    url(r"/admin/article", controller.admin_article.AdminArticleHandler, name="admin.articles"),
    # 发表文章
    url(r"/admin/article/(submit)", controller.admin_article.AdminArticleHandler, name="admin.article.action"),
    url(r"/admin/article/([0-9]+)", controller.admin_article.AdminArticleHandler, name="admin.article"),
    url(r"/admin/article/([0-9]+)/(delete)", controller.admin_article.AdminArticleHandler, name="admin.article.update"),
    # 评论列表
    url(r"/admin/comment", controller.admin_article.AdminArticleCommentHandler, name="admin.comments"),
    # 评论管理
    url(r"/admin/article/([0-9]+)/comment/([0-9]+)/(disable|enable|delete)",
        controller.admin_article.AdminArticleCommentHandler, name="admin.comment.update"),
    # 管理员用户初始化super.init
    url(r"/super/init", controller.super.SuperHandler, name="super.init"),
]