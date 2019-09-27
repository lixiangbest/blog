# coding=utf-8
import os, sys

# 启动并行任务
import concurrent.futures
import tornado.ioloop
import tornado.web
from tornado.options import options
# 数据库包
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

# 导入当前目录下的配置文件log_config.py
import log_config
# config.py
from config import config, redis_pub_sub_config, site_cache_config, redis_session_config
# controller/
from controller.base import BaseHandler
# extends/
from extends.cache_tornadis import CacheManager
from extends.session_tornadis import SessionManager
# service/
from service.init_service import flush_all_cache
from service.pubsub_service import PubSubService
# url_mapping.py
from url_mapping import handlers

# tornado server相关参数
# https://tornado-zh.readthedocs.io/zh/latest/web.html#tornado.web.Application.settings
settings = dict(
    # 服务进程将会在任意资源文件 改变的时候重启
    autoreload=True,
    # 如果为true, 默认的错误页将包含错误信息 的回溯.
    serve_traceback = False,
    # 是否开启debug模式
    debug=config['debug'],
    # 模板目录
    template_path=os.path.join(os.path.dirname(__file__), "template"),
    # 静态文件目录
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    # 文本格式的响应将被自动压缩
    compress_response=config['compress_response'],
    # 如果true, 跨站请求伪造(防护) 将被开启
    xsrf_cookies=config['xsrf_cookies'],
    # cookie密钥，被RequestHandler.get_secure_cookie使用, set_secure_cookie用来给cookies签名
    cookie_secret=config['cookie_secret'],
    # 如果该用户没有登陆 authenticated 装饰器将会重定向到这个url.
    # 更多自定义特性可以通过复写 RequestHandler.get_login_url 实现
    login_url=config['login_url'],
    # 如果没有发现其他匹配则会使用这个处理程序; 使用这个来实现自定义404页面
    default_handler_class=BaseHandler,
)


# sqlalchemy连接池配置以及生成链接池工厂实例
# sqlalchemy数据库连接池的使用方式是延迟初始化
# 在连接池启用的情况下，session 只是对连接池中的连接进行操作： session = Session()
# 将 Session 实例化的过程只是从连接池中取一个连接，在用完之后使用 session.close() 还回到连接池中，
# 而不是真正的关闭连接。
# 真正对数据库连接进行操作的应该是使用 engine 实例，比如 engine.dispose()。
# SQLAlchemy 默认在使用 create_engine 创建新的 engine 时提供了一个 QueuePool，
# 而且可以指定 Pool 的一些属性，包括 pool_size、max_overflow、pool_recycle 等
def db_poll_init():
    engine_config = config['database']['engine_url']
    # 构建好 Engine 对象的同时，连接池和Dialect也创建好了，但是这时候并不会立马与数据库建立真正的连接，
    # 只有你调用 Engine.connect() 或者 Engine.execute(sql) 执行SQL请求的时候，才会建立真正的连接。
    # 因此 Engine 和 Pool 的行为称之为延迟初始化，用现在流行的话来说就是延迟满足感，
    # 等真正要派上用场的时候才去建立连接。
    engine = create_engine(engine_config, **config['database']["engine_setting"])
    config['database']['engine'] = engine
    # 通过session.connection()或者engine.connect()或者 Session = sessionmaker(bind=engine)才开始创建连接。
    db_poll = sessionmaker(bind=engine, expire_on_commit=False)
    return db_poll

# 实例化redis缓存
def cache_manager_init():
    cache_manager = CacheManager(options = site_cache_config).get_conn()
    return cache_manager

# 继承tornado.web.Application类，可以在构造函数里做站点初始化（初始数据库连接池，初始站点配置，初始异步线程池，加载站点缓存等）
class Application(tornado.web.Application):
    def __init__(self):
        # handlers是整站路由配置，settings是Application类tornado框架设置
        super().__init__(handlers, **settings)
        # redis session连接池管理器
        self.session_manager = SessionManager(options = config['redis_session']).get_conn()
        # logger.info(self.session_manager)
        # 使用线程池来异步执行调用
        self.thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=config['max_threads_num'])
        # 数据库连接池
        self.db_pool = db_poll_init()
        # 站点redis缓存
        self.cache_manager = cache_manager_init()
        # logger.info(self.cache_manager)
        self.pubsub_manager = None


#  从命令行读取配置，如果这些参数不传，默认使用config.py的配置项
def parse_command_line():
    # python main.py --help
    # python main.py --port=80
    options.define("port", help="run server on a specific port", type=int)
    options.define("log_console", help="print log to console", type=bool)
    options.define("log_file", help="print log to file", type=bool)
    options.define("log_file_path", help="path of log_file", type=str)
    options.define("log_level", help="level of logging", type=str)
    # 集群中最好有且仅有一个实例为master，一般用于执行全局的定时任务
    options.define("master", help="is master node? (true:master / false:slave)", type=bool)
    # sqlalchemy engine_url, 例如pgsql 'postgresql+psycopg2://mhq:1qaz2wsx@localhost:5432/blog'
    options.define("engine_url", help="engine_url for sqlalchemy", type=str)
    # redis相关配置, 覆盖所有用到redis位置的配置
    options.define("redis_host", help="redis host e.g 127.0.0.1", type=str)
    options.define("redis_port", help="redis port e.g 6379", type=int)
    options.define("redis_password", help="redis password set this option if has pwd ", type=str)
    options.define("redis_db", help="redis db e.g 0", type=int)

    # 读取项目启动时，命令行上添加的参数项
    options.logging = None  # 不用tornado自带的logging配置
    options.parse_command_line()
    # 覆盖默认的config配置
    if options.port is not None:
        config['port'] = options.port
    if options.log_console is not None:
        config['log_console'] = options.log_console
    if options.log_file is not None:
        config['log_file'] = options.log_file
    if options.log_file_path is not None:
        config['log_file_path'] = options.log_file_path
    if options.log_level is not None:
        config['log_level'] = options.log_level
    if options.master is not None:
        config['master'] = options.master
    if options.engine_url is not None:
        config['database']['engine_url'] = options.engine_url
    if options.redis_host is not None:
        redis_session_config['host'] = options.redis_host
        site_cache_config['host'] = options.redis_host
        redis_pub_sub_config['host'] = options.redis_host
    if options.redis_port is not None:
        redis_session_config['port'] = options.redis_port
        site_cache_config['port'] = options.redis_port
        redis_pub_sub_config['port'] = options.redis_port
    if options.redis_password is not None:
        redis_session_config['password'] = options.redis_password
        site_cache_config['password'] = options.redis_password
        redis_pub_sub_config['password'] = options.redis_password
    if options.redis_db is not None:
        redis_session_config['db_no'] = options.redis_db
        site_cache_config['db_no'] = options.redis_db

# Windows10 关闭端口占用
# netstat -ano | findstr "8888"
# taskkill  -F -PID 6832
if __name__ == '__main__':
    if len(sys.argv) >= 2:
        if sys.argv[1] == 'upgradedb':
            # Alembic 是 Sqlalchemy 的作者实现的一个数据库版本化管理工具，
            # 它可以对基于Sqlalchemy的Model与数据库之间的历史关系进行版本化的维护。
            # 更新数据库结构，初次获取或更新版本后调用一次python main.py upgradedb即可
            from alembic.config import main
            # Alembic的控制台运行功能
            main("upgrade head".split(' '), 'alembic')
            exit(0)
    # 加载命令行配置
    parse_command_line()
    # 加载日志管理配置
    log_config.init(config['port'], config['log_console'],
                    config['log_file'], config['log_file_path'], config['log_level'])

    # 创建application
    try:
        logger.info("server start")
        application = Application()
        application.listen(config['port'])
        # 全局注册application
        config['application'] = application
        loop = tornado.ioloop.IOLoop.current()
        # 加载redis消息监听客户端
        # pubsub_manager = PubSubService(redis_pub_sub_config, application, loop)
        # pubsub_manager.long_listen()
        # application.pubsub_manager = pubsub_manager
        # # 为master节点注册定时任务
        # if config['master']:
        #     from extends.time_task import TimeTask
        #     TimeTask(config['database']['engine']).add_cache_flush_task(flush_all_cache).start_tasks()
        loop.start()
    except KeyboardInterrupt:
        logger.info("server stop")

