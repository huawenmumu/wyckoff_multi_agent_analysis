from .base import ak, pd, logger, SymbolType, DataFrameType, retry
from typing import Optional

class StockInfoDataFetcher:
    """股票基本信息数据获取类"""
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def get_stock_info(cls, symbol: str, timeout: Optional[float] = None) -> Optional[DataFrameType]:
        """
        获取个股基本信息
        
        参数:
            symbol (str): 股票代码，例如 "000001"
            timeout (float, optional): 超时时间，单位秒，默认为None
            
        返回:
            pandas.DataFrame: 个股基本信息，获取失败时返回None
            
        数据包含以下列：
        - item: 信息项名称（如最新、股票代码、股票简称、总股本、流通股、总市值、流通市值、行业、上市时间等）
        - value: 对应的值
        """
        logger.info(f"正在获取股票 {symbol} 的基本信息...")
        
        try:
            # 调用接口获取数据
            df = ak.stock_individual_info_em(symbol=symbol, timeout=timeout)
            
            if df is None or df.empty:
                logger.error(f"未获取到股票 {symbol} 的基本信息")
                return None
                
            logger.info(f"成功获取股票 {symbol} 的基本信息")
            return df
            
        except Exception as e:
            logger.error(f"获取股票 {symbol} 基本信息失败: {e}")
            return None