from .base import ak, pd, logger, SymbolType, DataFrameType, retry
from typing import Optional

class IndexDataFetcher:
    """指数数据获取类"""
    
    # 定义常用指数代码
    HS300_CODE = "000300"  # 沪深300指数
    GROWTH_ENTERPRISE_CODE = "399006"  # 创业板指数
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def get_index_data(cls, symbol: str) -> Optional[DataFrameType]:
        """
        获取指数历史数据
        
        参数:
            symbol (str): 指数代码
                - 沪深300指数: "000300"
                - 创业板指数: "399006"
            
        返回:
            pandas.DataFrame: 指数历史数据，获取失败时返回None
            
        数据包含以下列：
        - date: 日期
        - open: 开盘价
        - high: 最高价
        - low: 最低价
        - close: 收盘价
        - volume: 成交量
        """
        logger.info(f"正在获取指数 {symbol} 的历史数据...")
        
        try:
            # 调用接口获取数据
            original_symbol = symbol
            if symbol.startswith('0'):
                symbol = 'sh' + symbol
            elif symbol.startswith('3'):
                symbol = 'sz' + symbol
                
            df = ak.stock_zh_index_daily(symbol=symbol)
            
            if df is None or df.empty:
                logger.error(f"未获取到指数 {original_symbol} 的历史数据")
                return None
                
            logger.info(f"成功获取指数 {original_symbol} 的历史数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取指数 {symbol} 历史数据失败: {e}")
            return None
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def get_hs300_data(cls) -> Optional[DataFrameType]:
        """
        获取沪深300指数历史数据
        
        返回:
            pandas.DataFrame: 沪深300指数历史数据，获取失败时返回None
        """
        return cls.get_index_data(cls.HS300_CODE)
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def get_growth_enterprise_data(cls) -> Optional[DataFrameType]:
        """
        获取创业板指数历史数据
        
        返回:
            pandas.DataFrame: 创业板指数历史数据，获取失败时返回None
        """
        return cls.get_index_data(cls.GROWTH_ENTERPRISE_CODE)
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def get_all_index_spot_data(cls) -> Optional[DataFrameType]:
        """
        获取所有指数的实时行情数据
        
        返回:
            pandas.DataFrame: 所有指数的实时行情数据，获取失败时返回None
            
        数据包含以下列：
        - 代码: 指数代码
        - 名称: 指数名称
        - 最新价: 最新价格
        - 涨跌额: 涨跌额
        - 涨跌幅: 涨跌幅(%)
        - 昨收: 昨日收盘价
        - 今开: 今日开盘价
        - 最高: 最高价格
        - 最低: 最低价格
        - 成交量: 成交量(手)
        - 成交额: 成交额(元)
        """
        logger.info("正在获取所有指数的实时行情数据...")
        
        try:
            # 调用接口获取数据
            df = ak.stock_zh_index_spot_sina()
            
            if df is None or df.empty:
                logger.error("未获取到所有指数的实时行情数据")
                return None
                
            logger.info(f"成功获取所有指数的实时行情数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取所有指数的实时行情数据失败: {e}")
            return None