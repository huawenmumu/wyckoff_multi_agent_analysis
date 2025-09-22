from .base import logger
from .stock_code_converter import StockCodeConverter
from typing import Optional

class MarketType:
    """市场类型常量"""
    SHANGHAI = "sh"
    SHENZHEN = "sz"
    
    @classmethod
    def get_market(cls, symbol: str) -> Optional[str]:
        """
        根据股票代码判断市场类型
        
        参数:
            symbol (str): 股票代码
            
        返回:
            str: 市场类型，识别失败时返回None
        """
        if symbol.startswith(('6', '5', '9')):  # 上海证券交易所
            return cls.SHANGHAI
        elif symbol.startswith(('0', '1', '2', '3')):  # 深证证券交易所
            return cls.SHENZHEN
        else:
            logger.error(f"无法识别股票 {symbol} 的市场类型")
            return None