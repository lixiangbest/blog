# coding=utf-8
import tornado.ioloop
# import tornado.gen
# import tornadis
import aioredis
import logging

logger = logging.getLogger(__name__)


class PubSubTornadis():

    def __init__(self, redis_pub_sub_config, loop=None):
        self.redis_pub_sub_config = redis_pub_sub_config
        if not loop:
            loop = tornado.ioloop.IOLoop.current()
        self.loop = loop
        self.autoconnect = self.redis_pub_sub_config['autoconnect']
        # 创建redis连接
        # 这里是关键, 收到连接请求后, 不直接调用handle_connection(直接使用就不是异步了),
        # 而是将请求放在了io_loop中, 由io_loop去调度这部分代码.
        self.client = None
        self.pub_client = None
        self.connect_times = 0
        self.max_connect_wait_time = 10
        self.loop.spawn_callback(self.get_client)

    async def get_client(self):
        if not self.client:
            self.client = await aioredis.create_redis((self.redis_pub_sub_config['host'], self.redis_pub_sub_config['port']),
                                             db=self.redis_pub_sub_config['db_no'], password=self.redis_pub_sub_config['password'])

        return self.client

    async def get_pub_client(self):
        if not self.pub_client:
            self.pub_client = await aioredis.create_redis((self.redis_pub_sub_config['host'], self.redis_pub_sub_config['port']),
                                             db=self.redis_pub_sub_config['db_no'], password=self.redis_pub_sub_config['password'])
        return self.pub_client

    async def pub_call(self, msg, *channels):
        pub_client = self.get_pub_client()
        if not pub_client.is_connected():
            yield pub_client.connect()
        if not channels:
            channels = self.redis_pub_sub_config['channels']
        for channel in channels:
            yield pub_client.call("PUBLISH", channel, msg)

    def long_listen(self):
        self.loop.add_callback(self.connect_and_listen, self.redis_pub_sub_config['channels'])


    async def connect_and_listen(self, channels):
        connected = yield self.client.connect()
        if connected:
            subscribed = yield self.client.pubsub_subscribe(*channels)
            if subscribed:
                self.connect_times = 0
                yield self.first_do_after_subscribed()
                while True:
                    msgs = yield self.client.pubsub_pop_message()
                    try:
                        yield self.do_msg(msgs)
                        if isinstance(msgs, tornadis.TornadisException):
                            # closed connection by the server
                            break
                    except Exception as e:
                        logger.exception(e)
            self.client.disconnect()
        if self.autoconnect:
            wait_time = self.connect_times \
                if self.connect_times < self.max_connect_wait_time else self.max_connect_wait_time
            logger.warning("等待{}s，重新连接redis消息订阅服务".format(wait_time))
            yield tornado.gen.sleep(wait_time)
            self.long_listen()
            self.connect_times += 1


    async def first_do_after_subscribed(self):
        logger.info("订阅成功")


    async def do_msg(self, msgs):
        logger.info("收到订阅消息"+ str(msgs))

if __name__ == '__main__':
    try:
        logger.info("server start")
        redis_pub_sub_config = dict(
            db_no=2,
            host="127.0.0.1",
            port=6379,
            password=None,
            autoconnect=True,
            channels='site_cache_message_channel',
        )
        # 加载redis消息监听客户端
        app = PubSubTornadis(redis_pub_sub_config)
        tornado.ioloop.IOLoop.instance().start()
        print(app.loop, app.client)
    except KeyboardInterrupt:
        logger.info("server stop")


