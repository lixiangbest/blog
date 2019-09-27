from loguru import logger
import sys
import concurrent.futures
# 导入线程池和进程池模块
import threading
# 导入线程模块，作用是获取当前线程的名称
import os,time

class A:
    def __init__(self):
        self.x = 0

    def spam(self):
        print('A.spam')

class B(A):
    def __init__(self):
        super().__init__()
        self.y = 1

    def spam(self):
        print('B.spam', self.x, self.y)
        super().spam()

class Par:
    number = 3
    @classmethod
    def cm(cls):
        print('类方法cm(cls)调用者：', cls.__name__)

    @staticmethod
    def sm():
        print('静态方法sm()被调用', Par.number)

class ParA(Par):
    pass

class Date:
    def __init__(self, day = 0, month = 0, year = 0):
        self.day = day
        self.month = month
        self.year = year

    @classmethod
    def from_string(cls, date_as_string):
        day, month, year = map(int, date_as_string.split('-'))
        my_date = cls(day, month, year)
        return my_date

    @staticmethod
    def is_date_valid(date_as_string):
        day, month, year = map(int, date_as_string.split('-'))
        return day <= 31 and month <= 12 and year <= 3999

class Singleton():
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(Singleton, cls).__new__(cls)
        return cls.__instance

    def __init__(self, number):
        self.number = number

# 线程池和进程池
def count(number):
    for i in range(0, 10000000):
        i = i+1
    return i * number

def evaluate_item(x):
    # 打印当前线程名和运行的id号码
    print('%s:%s is running' % (threading.currentThread().getName(), os.getpid()))
    # 计算总和，这里只是为了消耗时间
    result_item = count(x)
    # 打印输入和输出结果
    return result_item

if __name__ == '__main__':
    b = B()
    b.spam()

    # 类方法示例类对象
    my_date = Date.from_string('11-09-2012')
    print(my_date.day, my_date.month, my_date.year)
    # 类的静态方法
    is_date = Date.is_date_valid('13-13-2012')
    print(is_date)

    # 调用类方法
    Par.cm()
    ParA.cm()
    # 调用类静态方法
    Par.sm()
    ParA.sm()

    # 单例模式
    s1 = Singleton(2)
    s2 = Singleton(9)

    print(s1, s2)
    print(s1.number, s2.number)

    # 日志管理包
    # # logger.add("file-{time:YYYY-MM-DD}.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {extra[ip]} | extra[user] | {message}", serialize=True)
    # # logger_ctx = logger.bind(ip="129.168.0.1", user="someone")
    # # logger_ctx.debug('a file message')
    # config = {
    #     "handlers": [
    #         # {"sink": sys.stdout, "format": "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {extra[ip]} | extra[user] | {message}"},
    #         {"sink": "file-{time:YYYY-MM-DD}.log", "serialize": True}
    #     ],
    #     "extra": {"ip": "192.168.0.1", "user": "taylor"}
    # }
    # logger.configure(**config)
    # logger.info("my library.")

    number_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # 顺序执行
    start_time = time.time()
    for item in number_list:
        print(evaluate_item(item))
    print("Sequential execution in " + str(time.time() - start_time), "seconds")
    # 对于IO密集型任务宜使用多线程模型。对于计算密集型任务应该使用多进程模型。
    # 线程池执行
    start_time_1 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(evaluate_item, item) for item in number_list]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())
    print("Thread pool execution in " + str(time.time() - start_time_1), "seconds")
    # 进程池
    start_time_2 = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(evaluate_item, item) for item in number_list]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())
    print("Process pool execution in " + str(time.time() - start_time_2), "seconds")


