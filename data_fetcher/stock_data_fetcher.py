from .base import ak, pd, datetime, timedelta, logger, SymbolType, DataFrameType, DateUtils, retry, CacheManager
from typing import Dict, Optional

class StockDataFetcher:
    """股票数据获取类"""
    
    _cache: Dict[SymbolType, DataFrameType] = {}
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def get_stock_data(cls, symbol: SymbolType) -> Optional[DataFrameType]:
        """
        获取股票历史数据
        
        参数:
            symbol (str): 股票代码
            
        返回:
            pandas.DataFrame: 股票历史数据，获取失败时返回None
        """
        logger.info(f"正在获取 {symbol} 的历史行情数据...")
        
        # 检查缓存
        if symbol in cls._cache:
            return cls._cache[symbol]
            
        date_range = DateUtils.get_date_range()
        
        try:
            # 调用接口获取数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=date_range["start_date"],
                end_date=date_range["end_date"],
                adjust="qfq"
            )
            
            # 缓存数据
            cls._cache[symbol] = df
            
            logger.info(f"成功获取 {symbol} 的历史行情数据")
            return df
            
        except Exception as e:
            logger.error(f"获取股票 {symbol} 历史数据失败: {e}")
            return None