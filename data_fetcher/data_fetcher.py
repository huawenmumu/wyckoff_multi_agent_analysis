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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class MarketType:
    """市场类型常量"""
    SHANGHAI = "sh"
    SHENZHEN = "sz"
    
    @classmethod
    def get_market(cls, symbol: SymbolType) -> Optional[str]:
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

class HS300OptionDataFetcher:
    """沪深300指数期权数据获取类"""
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def get_hs300_option_data(cls, symbol: str) -> Optional[DataFrameType]:
        """
        获取沪深300指数期权历史数据
        
        参数:
            symbol (str): 期权代码
            
        返回:
            pandas.DataFrame: 期权历史数据，获取失败时返回None
            
        数据包含以下列：
        - date: 日期
        - open: 开盘价
        - high: 最高价
        - low: 最低价
        - close: 收盘价
        - volume: 成交量
        """
        logger.info(f"正在获取沪深300指数期权 {symbol} 的历史数据...")
        
        try:
            # 调用接口获取数据
            df = ak.option_history(symbol=symbol)
            
            if df is None or df.empty:
                logger.error(f"未获取到沪深300指数期权 {symbol} 的历史数据")
                return None
                
            logger.info(f"成功获取沪深300指数期权 {symbol} 的历史数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取沪深300指数期权 {symbol} 数据失败: {e}")
            return None

class IndexDataFetcher:
    """指数数据获取类"""
    
    # 定义常用指数代码
    HS300_CODE = "sh000300"  # 沪深300指数
    GROWTH_ENTERPRISE_CODE = "sz399006"  # 创业板指数
    
    @classmethod
    @retry(max_retries=3, retry_delay=1)
    def get_index_data(cls, symbol: str) -> Optional[DataFrameType]:
        """
        获取指数历史数据
        
        参数:
            symbol (str): 指数代码
                - 沪深300指数: "sh000300"
                - 创业板指数: "sz399006"
            
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
            df = ak.stock_zh_index_daily(symbol=symbol)
            
            if df is None or df.empty:
                logger.error(f"未获取到指数 {symbol} 的历史数据")
                return None
                
            logger.info(f"成功获取指数 {symbol} 的历史数据，共 {len(df)} 条记录")
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

# 为了保持向后兼容性，提供函数别名
get_stock_data = StockDataFetcher.get_stock_data
stock_individual_fund_flow = FundFlowFetcher.stock_individual_fund_flow
convert_stock_code = StockCodeConverter.convert
get_hs300_option_data = HS300OptionDataFetcher.get_hs300_option_data
