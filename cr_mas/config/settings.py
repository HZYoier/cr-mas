"""集中管理所有配置——从环境变量/.env 读取"""

import os
from dotenv import load_dotenv

load_dotenv()  # 自动找项目根目录的 .env 文件并加载


class Settings:
    """CR-MAS 全局配置"""

    # DeepSeek
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_fast_model: str = os.getenv("DEEPSEEK_FAST_MODEL", "deepseek-chat")
    deepseek_pro_model: str = os.getenv("DEEPSEEK_PRO_MODEL", "deepseek-reasoner")


settings = Settings()
