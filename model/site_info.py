# coding=utf-8

# 站点集合配置
class SiteCollection():
    title = 'blog_xtg开源博客系统'                # string
    signature = 'Taylor'            # string
    navbar = None               # string
    menus = None                # json(list)
    article_types_not_under_menu = None # 不在menu下的article_types     #json(list)
    # 插件列表
    plugins = None              # JSON(list)
    pv = None                   # 总pv
    uv = None                   # 总uv
    todaypv = None              # 今日pv
    todayuv = None              # 今日uv
    article_count = None        # 文章总数
    comment_count = None        # 评论总数
    article_sources = None      # JSON(list)

