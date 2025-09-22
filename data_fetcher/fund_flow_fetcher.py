from .base import ak, pd, datetime, logger, SymbolType, DataFrameType, DateUtils, retry, CacheManager
from .market_type import MarketType
from typing import Dict, Optional

class FundFlowFetcher:
    """资金流向获取类"""
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def stock_individual_fund_flow(cls, symbol: SymbolType, date_range: Optional[Dict[str, str]] = None) -> Optional[DataFrameType]:
        """
        获取指定股票最近一段时间的资金流向数据
        
        参数:
            symbol (str): 股票代码
            date_range (dict, optional): 日期范围，包含start_date和end_date，格式为YYYYMMDD
                                       如果未提供，则使用默认的半年时间范围
            
        返回:
            pandas.DataFrame: 包含资金流向数据的DataFrame，获取失败时返回None
        """
        logger.info(f"正在获取股票 {symbol} 的资金流向数据...")
        
        # 如果没有提供日期范围，则使用默认范围（半年）
        if date_range is None:
            date_range = DateUtils.get_date_range(183)  # 半年时间范围
            
        # 计算天数
        start_date = datetime.strptime(date_range["start_date"], "%Y%m%d")
        end_date = datetime.strptime(date_range["end_date"], "%Y%m%d")
        days = (end_date - start_date).days
        
        # 尝试从缓存加载数据
        cached_data = CacheManager.load_cache(symbol, "fund_flow")
        if cached_data is not None:
            logger.info(f"从缓存加载 {symbol} 的资金流向数据")
            # 过滤指定日期范围内的数据
            return cls._filter_data_by_date_range(cached_data, date_range)
        
        market = MarketType.get_market(symbol)
        if not market:
            return None
            
        try:
            # 调用AkShare接口获取个股资金流向数据
            df = ak.stock_individual_fund_flow(stock=symbol, market=market)
            
            if df is None or df.empty:
                logger.error(f"未获取到股票 {symbol} 的数据")
                return None
                
            # 确保日期列为datetime类型
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'])
            else:
                logger.error("数据中未找到'日期'列")
                return None
                
            # 缓存数据
            CacheManager.save_cache(df, symbol, "fund_flow")
            
            # 筛选指定日期范围内的数据
            filtered_data = cls._filter_data_by_date_range(df, date_range)
            
            logger.info(f"成功获取 {len(filtered_data)} 条指定日期范围内的数据")
            return filtered_data
            
        except Exception as e:
            logger.error(f"获取股票 {symbol} 资金流向数据失败: {e}")
            return None
            
    @staticmethod
    def _filter_data_by_date_range(df: DataFrameType, date_range: Dict[str, str]) -> DataFrameType:
        """
        根据日期范围过滤数据
        
        参数:
            df (DataFrame): 原始数据
            date_range (dict): 日期范围，包含start_date和end_date
            
        返回:
            DataFrame: 过滤后的数据
        """
        start_date = datetime.strptime(date_range["start_date"], "%Y%m%d")
        end_date = datetime.strptime(date_range["end_date"], "%Y%m%d")
        
        # 确保日期列为datetime类型
        df_copy = df.copy()
        df_copy['日期'] = pd.to_datetime(df_copy['日期'])
        
        # 筛选日期范围内的数据
        filtered_df = df_copy[(df_copy['日期'] >= start_date) & (df_copy['日期'] <= end_date)]
        return filtered_df.sort_values('日期', ascending=False)