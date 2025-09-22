from .base import ak, pd, logger, SymbolType, DataFrameType, retry
from typing import Optional
from datetime import datetime


class StockIntradayDataFetcher:
    """股票分时数据获取类"""
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def get_intraday_data(cls, symbol: str) -> Optional[DataFrameType]:
        """
        获取个股分时数据
        
        参数:
            symbol (str): 股票代码，例如 "000001"
            
        返回:
            pandas.DataFrame: 个股分时数据，获取失败时返回None
            
        数据包含以下列：
        - 时间: 交易时间
        - 开盘: 开盘价
        - 收盘: 收盘价
        - 最高: 最高价
        - 最低: 最低价
        - 成交量: 成交量(手)
        - 成交额: 成交额
        - 均价: 均价
        """
        logger.info(f"正在获取股票 {symbol} 的分时数据...")
        
        try:
            # 获取今天的日期
            today = datetime.now().strftime("%Y-%m-%d")
            start_date = f"{today} 09:30:00"
            end_date = f"{today} 15:00:00"
            
            # 调用接口获取数据
            df = ak.stock_zh_a_hist_min_em(symbol=symbol, start_date=start_date, end_date=end_date, period="1", adjust="")
            
            if df is None or df.empty:
                logger.error(f"未获取到股票 {symbol} 的分时数据")
                return None
                
            logger.info(f"成功获取股票 {symbol} 的分时数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取股票 {symbol} 分时数据失败: {e}")
            return None