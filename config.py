# coding=utf-8

# 生成Cooke的keys
cookie_keys = dict(
    session_key_name="TR_SESSION_ID",
    uv_key_name="uv_tag",
)

# session相关配置（redis实现）
redis_session_config = dict(
    db_no=0,
    host="127.0.0.1",
    port=6379,
    password=None,
    max_connections=10,
    session_key_name=cookie_keys['session_key_name'],
    session_expires_days=7,
)

# 站点缓存(redis)
site_cache_config = dict(
    db_no=1,
    host="127.0.0.1",
    port=6379,
    password=None,
    max_connections=10,
)

# 基于redis的消息订阅（发布接收缓存更新消息）
redis_pub_sub_channels = dict(
    cache_message_channel="site_cache_message_channel",
)

# 消息订阅(基于redis)配置
redis_pub_sub_config = dict(
    db_no = 2,
    host="127.0.0.1",
    port=6379,
    password=None,
    autoconnect=True,
    channels=[redis_pub_sub_channels['cache_message_channel'],],
)

# 数据库配置
database_config = dict(
    engine=None,
    # engine_url='postgresql+psycopg2://mhq:1qaz2wsx@localhost:5432/blog',
    # 如果是使用mysql+pymysql，在确认所有的库表列都是uft8编码后，依然有字符编码报错，
    # 可以尝试在该url末尾加上queryString charset=utf8
    # mysql+pymysql://<username>:<password>@<host>/<dbname>[?<options>]
    engine_url='mysql+pymysql://root:kevin@localhost:3306/blog_xtg?charset=utf8',
    engine_setting=dict(
        echo=False,  # print sql
        echo_pool=False, # 连接池状态日志
        # 连接重置周期
        # 设置7*60*60秒后回收连接池，默认-1，从不重置
        # 该参数会在每个session调用执行sql前校验当前时间与上一次连接时间间隔是否超过pool_recycle，如果超过就会重置。
        # 这里设置7小时是为了避免mysql默认会断开超过8小时未活跃过的连接，避免"MySQL server has gone away”错误
        # 如果mysql重启或断开过连接，那么依然会在第一次时报"MySQL server has gone away"，
        # 假如需要非常严格的mysql断线重连策略，可以设置心跳。
        # 心跳设置参考https://stackoverflow.com/questions/18054224/python-sqlalchemy-mysql-server-has-gone-away
        pool_recycle=25200,
        # 连接池中数据库连接数量
        pool_size=5,
        # 允许超过连接池限额即 poolsize 的数量，超过连接数限额 max_overflow 之后不再允许创建新连接，
        # 而是要等待之前的连接完成操作。
        max_overflow=10,
        # 每次有一个连接从连接池检出的时候， pre_ping 会发出一个 “SELECT 1” 来检查 SQL 连接是否有效，
        # 如果有无效链接，则会重置此链接以及所有早于此连接的连接。
        pool_pre_ping=True,
    ),
)

session_keys = dict(
    login_user="login_user",
    messages="messages",
    article_draft="article_draft",
)

# 关联model.site_info中的字段
site_cache_keys = dict(
    title="title",
    signature="signature",
    navbar="navbar",
    menus="menus",
    article_types_not_under_menu="article_types_not_under_menu",
    plugins="plugins",
    pv="pv",
    uv="uv",
    article_count="article_count",
    comment_count="comment_count",
    article_sources="article_sources",
    source_articles_count="source_{}_articles_count",
)

# 站点相关配置以及tornado的相关参数
config = dict(
    # 是否开启debug模式
    debug=True,
    # 日志级别
    log_level="DEBUG",
    # 是否输出到stdout
    log_console=False,
    log_file=True,
    log_file_path="logs",  # 末尾自动添加 @端口号.txt_日期
    #响应报文压缩
    compress_response=True,
    # cookie是否加密
    xsrf_cookies=True,
    # cookie密钥
    cookie_secret="kjsdhfweiofjhewnfiwehfneiwuhniu",
    # 登录地址
    login_url="/auth/login",
    # web端口
    port=8888,
    # 线程数量
    # max_threads_num=500,
    max_threads_num=5,
    # 数据库配置
    database=database_config,
    # redis配置
    redis_session=redis_session_config,
    # session相关的keys
    session_keys=session_keys,
    master=True,  # 是否为主从节点中的master节点, 整个集群有且仅有一个,(要提高可用性的话可以用zookeeper来选主,该项目就暂时不做了)
    navbar_styles={"default": "优雅白", "inverse": "魅力黑"},  # 导航栏样式
    default_avatar_url="identicon",
    application=None,  # 项目启动后会在这里注册整个server，以便在需要的地方调用，勿修改
)