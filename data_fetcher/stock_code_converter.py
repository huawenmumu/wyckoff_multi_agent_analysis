from .base import logger
from typing import Dict, Any, Optional

class StockCodeConverter:
    """股票代码转换工具类"""
    
    @staticmethod
    def convert(code: str) -> str:
        """
        将A股股票代码转换为带有sh或sz前缀的格式
        
        参数:
            code (str): 原始股票代码，例如'600000'或'000001'
            
        返回:
            str: 带有sh或sz前缀的股票代码
            
        异常:
            ValueError: 当股票代码格式不正确时抛出
        """
        # 确保输入的是字符串类型
        code = str(code).strip()
    
        # 移除可能存在的前缀
        if code.startswith(('sh', 'sz')):
            code = code[2:]
    
        # 确保代码是6位数字
        if not (code.isdigit() and len(code) == 6):
            raise ValueError("股票代码必须是6位数字")
    
        # 根据股票代码的开头判断应该添加的前缀
        if code.startswith(('6', '5', '9')):  # 上海证券交易所
            return f"sh{code}"
        elif code.startswith(('0', '1', '2', '3')):  # 深证证券交易所
            return f"sz{code}"
        else:
            raise ValueError(f"无法识别的股票代码格式: {code}")