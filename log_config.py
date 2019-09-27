# coding=utf-8
# import logging
# import logging.handlers
# import tornado.log
from loguru import logger
import sys

# 日志等级（level）	描述
# DEBUG	最详细的日志信息，典型应用场景是 问题诊断
# INFO	信息详细程度仅次于DEBUG，通常只记录关键节点信息，用于确认一切都是按照我们预期的那样进行工作
# WARNING	当某些不期望的事情发生时记录的信息（如，磁盘可用空间较低），但是此时应用程序还是正常运行的
# ERROR	由于一个更严重的问题导致某些功能不能正常运行时记录的信息
# CRITICAL	当发生严重错误，导致应用程序不能继续运行时记录的信息

# 开发应用程序或部署开发环境时，可以使用DEBUG或INFO级别的日志获取尽可能详细的日志信息来进行开发或部署调试；
# 应用上线或部署生产环境时，应该使用WARNING或ERROR或CRITICAL级别的日志来降低机器的I/O压力和提高获取错误日志信息的效率。

FILE = dict(
    log_path="logs/", # 末尾自动添加 @端口号.txt_日期
    when="D", # 以什么单位分割文件
    interval=1, # 以上面的时间单位，隔几个单位分割文件
    backupCount=30, # 保留多少历史记录文件
    fmt="%(asctime)s - %(name)s - %(filename)s[line:%(lineno)d] - %(levelname)s - %(message)s",
)

# 初始化日志配置
# def init(port, console_handler=False, file_handler=True, log_path=FILE['log_path'], base_level="INFO"):
#     logger = logging.getLogger()
#     logger.setLevel(base_level)
#     # 配置控制台输出
#     if console_handler:
#         channel_console = logging.StreamHandler()
#         channel_console.setFormatter(tornado.log.LogFormatter())
#         logger.addHandler(channel_console)
#     # 配置文件输出
#     if file_handler:
#         if not log_path:
#             log_path = FILE['log_path']
#         log_path = log_path+"@"+str(port)+".txt"
#         formatter = logging.Formatter(FILE['fmt']);
#         channel_file = logging.handlers.TimedRotatingFileHandler(
#             filename=log_path,
#             when=FILE['when'],
#             interval=FILE['interval'],
#             backupCount=FILE['backupCount'])
#         channel_file.setFormatter(formatter)
#         logger.addHandler(channel_file)

# 使用更友好的 loguru 库
def init(port, console_handler=False, file_handler=True, log_path=FILE['log_path'], base_level="INFO"):
    handlers = []
    # 配置控制台输出
    if console_handler:
        handlers.append({"sink": sys.stdout, "level": base_level})
    # 配置文件输出
    if file_handler:
        if not log_path:
            log_path = FILE['log_path']
        log_path = log_path+"/{time:YYYYMMDD}log@"+str(port)+".txt"
        handlers.append({"sink": log_path, "level": base_level})

    if handlers:
        config = {"handlers": handlers}
        logger.configure(**config)


