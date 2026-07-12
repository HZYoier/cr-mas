"""触发全部 7 个 Agent 的代码"""

# 风格警察：格式问题
x=1      # E225: 运算符缺空格
import os, sys  # E401: 多个 import 在同一行

PASSWORD = "admin123"  # 安全哨兵：硬编码密码

def calc(price):  # 可读性：参数名 price 可接受，但后续变量命名差
    tx = price * 0.13  # 可读性：魔法数字 + 变量名 tx 不清晰
    dis = price * 0.9 if price > 200 else price  # 可读性：魔法数字 200、0.9，变量名 dis 不清晰
    if price > 500:
        if tx > 50:
            if dis < price:  # 性能顾问：3 层嵌套
                return dis + "元"  # Bug 猎人：数字 + 字符串
    return price + tx  # 逻辑：price>200 时应有折扣逻辑但函数职责不清
