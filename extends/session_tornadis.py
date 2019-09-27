# coding: utf-8
import uuid
import json
# import tornadis
import aioredis
# import tornado.gen
# import logging
from loguru import logger
from tornado import ioloop

# redis session
class Session(dict):
    # 类属性
    msg = {}
    # 草稿
    article_draft = {}
    def __init__(self, request_handler):
        super().__init__()
        self.session_id = None
        # self.session_manager = request_handler.application.session_manager
        self.session_manager = SessionManager()
        self.request_handler = request_handler
        self.client = None

    # async def init_fetch(self):
    #     self.client = yield self.session_manager.get_redis_client()
    #     yield self.fetch_client()

    # 从cookie里面获取session
    def get_session_id(self):
        if not self.session_id:
            # get_secure_cookie获取的是bytes
            self.session_id = self.request_handler.get_secure_cookie(self.session_manager.options['session_key_name'])
            if self.session_id:
                self.session_id = self.session_id.decode('utf-8')
        return self.session_id

    # 产生session id并保持到cookie
    def generate_session_id(self):
        if not self.get_session_id():
            self.session_id = str(uuid.uuid1())
            self.request_handler.set_secure_cookie(self.session_manager.options['session_key_name'], self.session_id,
                                                   expires_days=self.session_manager.options['session_expires_days'])
        return self.session_id

    # async def fetch_client(self):
    #     if self.get_session_id():
    #         data = yield self.call_client("GET", self.session_id)
    #         if data:
    #             self.update(json.loads(data))

    # 删除cookie和redis
    async def delete(self):
        self.get_session_id()
        self.request_handler.clear_cookie(self.session_manager.options['session_key_name'])
        await self.session_manager.get_conn().delete('session:' + self.session_id)

    # 获取会话信息
    async def get(self):
        uinfo = await self.session_manager.get_conn().get('session:' + self.session_id)
        uinfo = json.loads(uinfo)
        return uinfo

    # 保存会话信息到redis
    async def save(self, expire_time=None):
        session_id = self.generate_session_id()
        data_json = json.dumps(self)
        if expire_time:
            await self.session_manager.get_conn().setex('session:'+session_id, expire_time, data_json)
        else:
            await self.session_manager.get_conn().set('session:' + session_id, data_json)

    # async def call_client(self, *args, **kwargs):
    #     if self.client:
    #         reply = yield self.client.call(*args, **kwargs)
    #         if isinstance(reply, tornadis.TornadisException):
    #             logger.error(reply.message)
    #         else:
    #             raise tornado.gen.Return(reply)

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

# redis session管理
class SessionManager():
    # __new__方法默认返回实例对象供__init__方法、实例方法使用
    # 在元类的 __new__ 方法中，因为类实例还没有创建，所以可以更改最后生成类的各项属性：
    # 诸如名称，基类或属性，方法等。而在 __init__ 中由于类已经创建完成，所以无法改变。
    # 正常情况下不需要关心它们的区别。
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            # logger.debug("init redis pool")
            # _loop = kwargs.get("loop", ioloop.IOLoop.current())
            _loop = ioloop.IOLoop.current()
            # logger.info('init session redis pool:%s, %s, %s, %s' % (cls, args, kwargs, _loop))
            # # 判断一个表达式，在表达式条件为 false 的时候触发异常。
            cls.options = kwargs['options']
            # assert _loop, "use get_event_loop()"
            # 类属性 = 获取redis连接池
            cls.connection_pool = _loop.run_sync(lambda : _init_with_loop(kwargs['options']))
            # 类属性 = 实例化对象
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_conn(self) -> aioredis.Redis:
        return self.connection_pool

    # def __init__(self, options):
    #     self.connection_pool = None
    #     self.options = options
    #     self.session_key_name = options['session_key_name']
    #     self.session_expires_days = options['session_expires_days']
    #
    # def get_connection_pool(self):
    #     if not self.connection_pool:
    #         self.connection_pool = tornadis.ClientPool(host=self.options['host'],port=self.options['port'],
    #                                                    password=self.options['password'], db=self.options['db_no'],
    #                                                    max_size=self.options['max_connections'])
    #     return self.connection_pool
    #
    # async def get_redis_client(self):
    #     connection_pool = self.get_connection_pool()
    #     with (yield connection_pool.connected_client()) as client:
    #         if isinstance(client, tornadis.TornadisException):
    #             logger.error(client.message)
    #         else:
    #             raise tornado.gen.Return(client)

