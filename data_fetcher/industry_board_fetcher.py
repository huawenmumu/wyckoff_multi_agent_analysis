from .base import ak, pd, datetime, timedelta, logger, SymbolType, DataFrameType, retry
from typing import Optional

class IndustryBoardDataFetcher:
    """行业板块数据获取类"""
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def get_board_hist_data(cls, 
                           symbol: str, 
                           start_date: str = None, 
                           end_date: str = None, 
                           period: str = "日k", 
                           adjust: str = "") -> Optional[DataFrameType]:
        """
        获取行业板块历史行情数据
        
        参数:
            symbol (str): 行业板块名称，例如 "小金属"
                         可以通过调用 ak.stock_board_industry_name_em() 查看所有行业代码
            start_date (str): 开始日期，格式为 "YYYYMMDD"，默认为 180 天前
            end_date (str): 结束日期，格式为 "YYYYMMDD"，默认为今天
            period (str): 周期，choice of {"日k", "周k", "月k"}，默认为 "日k"
            adjust (str): 复权类型，choice of {'': 不复权, 默认; "qfq": 前复权, "hfq": 后复权}
            
        返回:
            pandas.DataFrame: 行业板块历史行情数据，获取失败时返回None
            
        数据包含以下列：
        - 日期: 交易日期
        - 开盘: 开盘价
        - 收盘: 收盘价
        - 最高: 最高价
        - 最低: 最低价
        - 涨跌幅: 涨跌幅(%)
        - 涨跌额: 涨跌额
        - 成交量: 成交量
        - 成交额: 成交额
        - 振幅: 振幅(%)
        - 换手率: 换手率(%)
        """
        # 如果未指定开始日期和结束日期，则使用默认值
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
            
        logger.info(f"正在获取行业板块 {symbol} 的历史行情数据...")
        logger.info(f"日期范围: {start_date} 到 {end_date}, 周期: {period}, 复权: {adjust}")
        
        try:
            # 调用接口获取数据
            df = ak.stock_board_industry_hist_em(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                period=period,
                adjust=adjust
            )
            
            if df is None or df.empty:
                logger.error(f"未获取到行业板块 {symbol} 的历史行情数据")
                return None
                
            logger.info(f"成功获取行业板块 {symbol} 的历史行情数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取行业板块 {symbol} 历史行情数据失败: {e}")
            return None
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def get_industry_list(cls) -> Optional[DataFrameType]:
        """
        获取东方财富行业板块列表
        
        返回:
            pandas.DataFrame: 行业板块列表，获取失败时返回None
        """
        logger.info("正在获取东方财富行业板块列表...")
        
        try:
            # 调用接口获取行业板块列表
            df = ak.stock_board_industry_name_em()
            
            if df is None or df.empty:
                logger.error("未获取到东方财富行业板块列表")
                return None
                
            logger.info(f"成功获取东方财富行业板块列表，共 {len(df)} 个行业")
            return df
            
        except Exception as e:
            logger.error(f"获取东方财富行业板块列表失败: {e}")
            return None