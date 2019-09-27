# coding: utf-8
# import logging
from loguru import logger

# import tornadis
# import tornado.gen
import aioredis
from tornado import ioloop

# logger = logging.getLogger(__name__)

async def _init_with_loop(options):
    """
    redis 连接池
    :param loop: 循环
    :return: redis pool
    """
    # https://aioredis.readthedocs.io/en/v1.2.0/migration.html?highlight=create_redis_pool#aioredis-create-pool
    __pool = await aioredis.create_redis_pool(
        (options['host'], options['port']), password=options['password'], db=options['db_no'], minsize=1, maxsize=options['max_connections'], encoding='utf8')
    return __pool

# redis缓存管理
# py 2.2 后继承 object 的目的是使这个类成为 new style class,
# 没有继承 object 的为传统 classic class
# 实际上在python 3 中已经默认就帮你加载了object了（即便你没有写上object）
class CacheManager():
    # __new__方法默认返回实例对象供__init__方法、实例方法使用
    # 在元类的 __new__ 方法中，因为类实例还没有创建，所以可以更改最后生成类的各项属性：
    # 诸如名称，基类或属性，方法等。而在 __init__ 中由于类已经创建完成，所以无法改变。
    # 正常情况下不需要关心它们的区别。
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            # logger.debug("init redis pool")
            # _loop = kwargs.get("loop", ioloop.IOLoop.current())
            _loop = ioloop.IOLoop.current()
            # logger.info('init cache redis pool:%s, %s, %s, %s' % (cls, args, kwargs, _loop))
            # # 判断一个表达式，在表达式条件为 false 的时候触发异常。
            # assert _loop, "use get_event_loop()"
            # 类属性 = 获取redis连接池
            cls.connection_pool = _loop.run_sync(lambda: _init_with_loop(kwargs['options']))
            # 类属性 = 实例化对象
            cls._instance = super(CacheManager, cls).__new__(cls)
        return cls._instance

    def get_conn(self) -> aioredis.Redis:
        return self.connection_pool

    # def __init__(self, options):
    #     self.connection_pool = None
    #     self.options = options
    #     self.client = None

    # 获取redis数据库连接池
    # def get_connection_pool(self):
    #     if not self.connection_pool:
    #         self.connection_pool = tornadis.ClientPool(host=self.options['host'],port=self.options['port'],
    #                                                    password=self.options['password'], db=self.options['db_no'],
    #                                                    max_size=self.options['max_connections'])
    #     return self.connection_pool
    #
    # @tornado.gen.coroutine
    # def get_redis_client(self):
    #     connection_pool = self.get_connection_pool()
    #     with (yield connection_pool.connected_client()) as client:
    #         if isinstance(client, tornadis.TornadisException):
    #             logger.error(client.message)
    #         else:
    #             raise tornado.gen.Return(client)
    #
    # @tornado.gen.coroutine
    # def fetch_client(self):
    #     self.client = yield self.get_redis_client()
    #
    # @tornado.gen.coroutine
    # def call(self, *args, **kwargs):
    #     yield self.fetch_client()
    #     if self.client:
    #         reply = yield self.client.call(*args, **kwargs)
    #         if isinstance(reply, tornadis.TornadisException):
    #             logger.error(reply.message)
    #         else:
    #             raise tornado.gen.Return(reply)
    #
    # @tornado.gen.coroutine
    # def call(self, *args, **kwargs):
    #     yield self.fetch_client()
    #     if self.client:
    #         reply = yield self.client.call(*args, **kwargs)
    #         if isinstance(reply, tornadis.TornadisException):
    #             logger.error(reply.message)
    #         else:
    #             raise tornado.gen.Return(reply)
    #
    # @tornado.gen.coroutine
    # def call_watch_transaction(self, watch_key, *args, **kwargs):
    #     yield self.fetch_client()
    #     if self.client:
    #         while True:
    #             yield self.client.call("WATCH", watch_key)
    #             yield self.client.call("MULTI")
    #             yield self.client.call(*args, **kwargs)
    #             result = yield self.client.call("EXEC")
    #             if isinstance(result, tornadis.TornadisException):
    #                 logger.error(result.message)
    #             else:
    #                 raise tornado.gen.Return(result)

