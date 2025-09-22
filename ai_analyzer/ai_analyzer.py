from openai import OpenAI
import json
import time
from typing import Optional, Dict, Any
import logging
import matplotlib.pyplot as plt
import pandas as pd
import httpx

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 禁用httpx的详细日志输出
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

def process_response(response, max_retries, attempt):
    """
    处理AI响应流
    
    参数:
    response: AI响应流
    max_retries: 最大重试次数
    attempt: 当前尝试次数
    
    返回:
    str: 处理后的内容
    """
    try:
        reasoning_content = ""
        content = ""
        finished = False
        # logger.info("提问完成,等待回复...")
        for chunk in response:
            if not chunk.choices:
                continue
            first_choice = chunk.choices[0]
            if first_choice.delta is None:
                continue
            if first_choice.finish_reason == 'stop':
                finished = True
                break
            if hasattr(first_choice.delta, 'reasoning_content') and first_choice.delta.reasoning_content is not None:
                reasoning_content += first_choice.delta.reasoning_content
            if hasattr(first_choice.delta, 'content') and first_choice.delta.content is not None:
                content += first_choice.delta.content

        if finished:
            return content
        else:
            logger.warning(f"尝试 {attempt + 1}/{max_retries}: 请求未正常结束,正在重试...")
            return None
            
    except Exception as e:
        logger.error(f"处理响应时发生错误: {e}")
        return None

def askDeepSeek(stock_df, stock_fund_flow_df, stock_code, prompt_content, max_retries=5):
    """
    调用DeepSeek AI对股票数据进行分析

    参数:
    stock_df: 股票历史数据
    stock_fund_flow_df: 股票资金流向数据
    stock_code: 股票代码
    prompt_content: 分析提示词
    max_retries: 最大重试次数

    返回:
    str: AI分析结果
    """
    if stock_df is None or stock_df.empty:
        logger.warning("无有效股票历史数据，无法进行分析")
        return "无有效股票历史数据，无法进行分析"

    # 转换股票历史数据为JSON格式
    stock_json = stock_df.to_json(orient='records', date_format='iso')

    stock_fund_flow_json = ""
    if stock_fund_flow_df is not None and not stock_fund_flow_df.empty:
        stock_fund_flow_json = stock_fund_flow_df.to_json(orient='records', date_format='iso')

    # 构建用户消息内容
    user_content = f"""请根据股票代码 {stock_code} 的最新历史数据和资金流向数据，给出分析和投资建议。

历史行情数据如下：
{stock_json}
"""
    # 如果有资金流向数据，添加到用户消息中
    if stock_fund_flow_json:
        user_content += f"""
资金流向数据如下：
{stock_fund_flow_json}
"""

    for attempt in range(max_retries):
        try:
            # logger.info(f"正在向AI提问... (尝试 {attempt + 1}/{max_retries})")
            client = OpenAI(api_key="sk-3353495a7a4d46bda88094071ccad7bc", base_url="https://api.deepseek.com")

            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": prompt_content},
                    {"role": "user", "content": user_content}
                ],
                response_format={
                    'type': 'json_object'
                },
                stream=True
            )
            
            content = process_response(response, max_retries, attempt)
            
            if content:
                # logger.info(f"成功获取AI分析结果 (尝试 {attempt + 1}/{max_retries})")
                return content

        except Exception as e:
            logger.error(f"尝试 {attempt + 1}/{max_retries} 失败,错误: {e}")
            if attempt < max_retries - 1:  # 不是最后一次尝试
                wait_time = 5 if "API" in str(e) else 2
                logger.info(f"等待{wait_time}秒后重试...")
                time.sleep(wait_time)
            continue

    logger.error("请求未正常结束,请稍后再试。")
    return "请求未正常结束,请稍后再试。"

def visualize_stock_data(stock_df: pd.DataFrame, stock_code: str) -> None:
    """
    可视化股票数据
    
    参数:
    stock_df: 股票历史数据
    stock_code: 股票代码
    """
    if stock_df is None or stock_df.empty:
        logger.warning("无有效股票数据，无法生成图表")
        return
    
    try:
        # 确保日期列为datetime类型
        if '日期' in stock_df.columns:
            stock_df['日期'] = pd.to_datetime(stock_df['日期'])
            stock_df = stock_df.sort_values('日期')
        else:
            logger.error("数据中未找到'日期'列")
            return
        
        # 创建图表
        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        
        # 绘制股价走势
        axes[0].plot(stock_df['日期'], stock_df['收盘'], label='收盘价', linewidth=1)
        axes[0].set_title(f'{stock_code} 股价走势')
        axes[0].set_ylabel('价格')
        axes[0].grid(True)
        axes[0].legend()
        
        # 绘制成交量
        if '成交量' in stock_df.columns:
            axes[1].bar(stock_df['日期'], stock_df['成交量'], alpha=0.5)
            axes[1].set_title(f'{stock_code} 成交量')
            axes[1].set_ylabel('成交量')
            axes[1].grid(True)
        
        # 设置x轴格式
        for ax in axes:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.savefig(f'{stock_code}_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"图表已保存为 {stock_code}_analysis.png")
        
    except Exception as e:
        logger.error(f"生成图表失败: {e}")