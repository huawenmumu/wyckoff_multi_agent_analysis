from .base import ak, pd, logger, SymbolType, DataFrameType, retry
from typing import Optional

class HS300OptionDataFetcher:
    """沪深300指数期权数据获取类"""
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def get_hs300_option_data(cls, symbol: str) -> Optional[DataFrameType]:
        """
        获取沪深300指数期权实时数据
        
        参数:
            symbol (str): 期权合约代码，例如 "io2104"
            
        返回:
            pandas.DataFrame: 沪深300指数期权实时数据，获取失败时返回None
            
        数据包含以下列：
        - 看涨合约_买量: 看涨合约买量
        - 看涨合约_买价: 看涨合约买价
        - 看涨合约_最新价: 看涨合约最新价
        - 看涨合约_卖价: 看涨合约卖价
        - 看涨合约_卖量: 看涨合约卖量
        - 看涨合约_持仓量: 看涨合约持仓量
        - 看涨合约_涨跌: 看涨合约涨跌
        - 行权价: 期权行权价
        - 看涨合约_标识: 看涨合约代码
        - 看跌合约_买量: 看跌合约买量
        - 看跌合约_买价: 看跌合约买价
        - 看跌合约_最新价: 看跌合约最新价
        - 看跌合约_卖价: 看跌合约卖价
        - 看跌合约_卖量: 看跌合约卖量
        - 看跌合约_持仓量: 看跌合约持仓量
        - 看跌合约_涨跌: 看跌合约涨跌
        - 看跌合约_标识: 看跌合约代码
        """
        logger.info(f"正在获取沪深300指数期权 {symbol} 的实时数据...")
        
        try:
            # 调用接口获取数据
            df = ak.option_cffex_hs300_spot_sina(symbol=symbol)
            
            if df is None or df.empty:
                logger.error(f"未获取到沪深300指数期权 {symbol} 的数据")
                return None
                
            logger.info(f"成功获取沪深300指数期权 {symbol} 的实时数据")
            return df
            
        except Exception as e:
            logger.error(f"获取沪深300指数期权 {symbol} 数据失败: {e}")
            return None