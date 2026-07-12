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



def dispatch_request(req_type, data):
    """处理不同类型请求的调度函数"""
    if req_type == "login":
        if data.get("user") == "admin":
            if data.get("pass") == "admin123":
                return "admin_access"
            else:
                return "wrong_password"
        else:
            return "user_login"
    elif req_type == "query":
        if data.get("sql"):
            if len(data["sql"]) > 100:
                if "DROP" in data["sql"]:
                    return "dangerous_query"
                else:
                    return "long_query"
            else:
                return "short_query"
        else:
            return "no_query"
    elif req_type == "update":
        if data.get("id"):
            return f"updated_{data['id']}"
        else:
            return "no_id"
    else:
        return "unknown"

# 冲突种子
result_cache = None  # 变量名不清晰且从未使用