# blog_taylor
基于python3.6 Tornado的博客系统,体验地址:[blog_taylor](http://wifi.tiyukan.cn/)

前台效果:
![image](https://raw.githubusercontent.com/lixiangbest/blog/master/static/images/front.png)

后台效果:
![image](https://raw.githubusercontent.com/lixiangbest/blog/master/static/images/back.png)

### 一、为什么写blog_taylor
之前了解的开源blog有很多，比如WordPress、LifeType等等，这些都是PHP架构的,我也从事PHP开发,再用PHP写一个blog意义不大.最近几年，python比较火,就想学习一下python相关的知识,
在了解了python相关基础知识后就尝试写个博客。之所以没有选择同步类框架Django，因为想多熟悉python协程,异步,连接池等PHP里面比较缺失的知识,就选择了python的异步IO框架tornado。

### 二、blog_taylor简介
首先非常感谢[blog_xtg](https://github.com/xtg20121013/blog_xtg)开源分布式博客，其web框架使用的是tornado(一个基于异步IO的python web框架)。tornado相关的开源项目不是很多,搜索过程中就看到了blog_xtg,
由于blog_xtg是基于python2,现在python3是主流,blog_xtg里面有些库在python3没办法使用,blog_taylor是根据blog_xtg重构的。刚开始下载下来,blog_xtg在python3.6环境下有很多问题,后面我就根据它的路由和目录结构进行改造。

1. 改用tornado框架，是个基于异步IO的web server。
2. 提高多数主要页面访问性能。对频繁查询的组件（例如博客标题、菜单、公告、访问统计）进行缓存，优化sql查询（多条sql语句合并一次执行、仅查需要的字段，例如搜索博文列表不查博文的具体内容）以提高首页博文等主要页面访问性能。
3. 访问统计改为日pv和日uv。
4. 博文编辑器改为markdown编辑器。
5. 引入alembic管理数据库版本。
6. 使用数据库连接池,Redis异步缓存连接池,并使用单例模式管理数据库对象,避免出现多个对象情况。

### 三、blog_taylor部署与开发环境搭建
#### 1. 构建运行环境
###### 需要安装以下组件：

1. python3.6.1
2. mysql(或者其他sqlalchemy支持的数据库)
3. redis

###### clone项目，安装依赖：
	git clone https://github.com/lixiangbest/blog
	#项目依赖（如果用的不是mysql可以将MySQL-python替换使用的数据库成所对应的依赖包）
	pip3 install -r requirements.txt
###### 创建数据库blog_xtg(注意使用utf-8编码)
###### 启动redis
###### 修改config.py，配置数据库、redis、日志等
###### 创建数据库或更新表
	python3.6 main.py upgradedb
###### 启动server
	python3.6 main.py

###### 初始化管理员账户
访问http://[host]:[port]/super/init注册管理员账号。

注:仅没有任何管理员时才可以访问到该页面。

### 四、开发注意事项
#### 1.blog_taylor是个异步IO的架构，相对于常见的同步IO框架，需要注意以下几点：

- IO密集型的操作请务必使用异步的client(async/await)，否则无法利用到异步的优势
- 由于多数异步IO的框架都是单线程的，所以对于CPU密集型的操作最好交由外部系统处理，防止阻塞，大型项目可以配合消息队列使用更佳
- 如果必须用同步的IO组件，可以配合线程池使用（blog_taylor中使用了sqlalchemy就是配合线程池使用的）
- 如果你是ORM+线程池使用(blog_taylor中就是sqlalchemy+线程池)，一般的ORM都有lazy load的机制，在异步框架中请勿使用，因为lazy load的执行在主线程中，很可能会阻塞主线程，影响别的请求。

#### 2.对于博文编辑的markdown的问题：

我用的是[Bootstrap Markdown](http://www.codingdrama.com/bootstrap-markdown)，好像只支持标准的markdown语法，可能大家对代码段的标注语法只知道```的形式，而真正的标准语法是代码段的每一行开头添加4个空格，如果大家不喜欢的话可以尝试更换为[marked](https://github.com/chjj/marked)，参见：[修复markdown编辑器无法编写多行code的问题 #2](https://github.com/xtg20121013/blog_xtg/pull/2)

### 五、技术支持
如果你有任何疑问，可以给我留言

=======

