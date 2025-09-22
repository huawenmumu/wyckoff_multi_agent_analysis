from .stock_code_converter import StockCodeConverter
from .stock_data_fetcher import StockDataFetcher
from .fund_flow_fetcher import FundFlowFetcher
from .hs300_option_fetcher import HS300OptionDataFetcher
from .index_data_fetcher import IndexDataFetcher
from .industry_board_fetcher import IndustryBoardDataFetcher
from .stock_info_fetcher import StockInfoDataFetcher
from .stock_intraday_fetcher import StockIntradayDataFetcher

# 为了保持向后兼容性，创建函数别名
convert_stock_code = StockCodeConverter.convert
get_stock_data = StockDataFetcher.get_stock_data
stock_individual_fund_flow = FundFlowFetcher.stock_individual_fund_flow
get_hs300_option_data = HS300OptionDataFetcher.get_hs300_option_data
get_index_data = IndexDataFetcher.get_index_data
get_industry_board_data = IndustryBoardDataFetcher.get_board_hist_data
get_stock_info = StockInfoDataFetcher.get_stock_info
get_stock_intraday_data = StockIntradayDataFetcher.get_intraday_data

__all__ = [
    'StockCodeConverter', 
    'StockDataFetcher', 
    'FundFlowFetcher',
    'HS300OptionDataFetcher',
    'IndexDataFetcher',
    'IndustryBoardDataFetcher',
    'StockInfoDataFetcher',
    'convert_stock_code', 
    'get_stock_data', 
    'stock_individual_fund_flow'
]