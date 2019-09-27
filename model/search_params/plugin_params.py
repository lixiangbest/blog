# coding=utf-8

# 插件搜索参数
class PluginSearchParams():

    ORDER_MODE_ORDER_ASC = 1

    def __init__(self, request):
        # 排序方式
        self.order_mode = request.get_argument("order_mode", PluginSearchParams.ORDER_MODE_ORDER_ASC)
