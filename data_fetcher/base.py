import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
from functools import lru_cache
from typing import Optional, Dict, Any, List, Union
import logging
import os
import pickle
from pathlib import Path
import httpx

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 禁用httpx的详细日志输出
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

# 定义类型别名
SymbolType = str
DataFrameType = pd.DataFrame

# 缓存目录
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

class CacheManager:
    """缓存管理器"""
    
    @staticmethod
    def get_cache_path(symbol: str, data_type: str) -> Path:
        """获取缓存文件路径"""
        return CACHE_DIR / f"{data_type}_{symbol}.pkl"
    
    @staticmethod
    def load_cache(symbol: str, data_type: str, expiry_hours: int = 24) -> Optional[DataFrameType]:
        """从缓存加载数据"""
        cache_path = CacheManager.get_cache_path(symbol, data_type)
        
        if not cache_path.exists():
            return None
            
        # 检查缓存是否过期
        if datetime.now().timestamp() - cache_path.stat().st_mtime > expiry_hours * 3600:
            cache_path.unlink()  # 删除过期缓存
            return None
            
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"加载缓存失败 {cache_path}: {e}")
            return None
    
    @staticmethod
    def save_cache(data: DataFrameType, symbol: str, data_type: str) -> None:
        """保存数据到缓存"""
        cache_path = CacheManager.get_cache_path(symbol, data_type)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.error(f"保存缓存失败 {cache_path}: {e}")

def retry(max_retries: int = 3, retry_delay: int = 1):
    """
    重试装饰器
    
    参数:
        max_retries (int): 最大重试次数
        retry_delay (int): 重试间隔（秒）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"{func.__name__} 失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        logger.info(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"{func.__name__} 最终失败")
                        return None
            return None
        return wrapper
    return decorator

class DateUtils:
    """日期处理工具类"""
    
    @staticmethod
    def get_date_range(half_year: int = 183) -> Dict[str, str]:
        """
        获取日期范围
        
        参数:
            half_year (int): 半年天数，默认为183天
        
        返回:
            dict: 包含开始日期和结束日期的字典
        """
        today = datetime.now()
        half_year_ago = today - timedelta(days=half_year)
        
        return {
            "end_date": today.strftime("%Y%m%d"),
            "start_date": half_year_ago.strftime("%Y%m%d")
        }