import json
import sys
import os
import traceback
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher import get_stock_data, stock_individual_fund_flow, IndexDataFetcher
from ai_analyzer import askDeepSeek

# 检查是否启用debug模式
DEBUG = os.environ.get('DEBUG', '').lower() in ('true', '1', 'yes')


class VolumeDetectiveAgent:
    """
    量能侦探Agent - 基于威科夫量价行为分析股票
    """
    
    def __init__(self):
        self.name = "量能侦探"
        
    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """
        执行量能侦探分析
        """
        try:
            # 获取股票数据
            stock_data = get_stock_data(stock_code)
            if stock_data is None or stock_data.empty:
                raise ValueError("无法获取股票数据")
                
            # 获取资金流向数据
            fund_flow_data = stock_individual_fund_flow(stock_code)
            
            # 获取股票信息（名称、板块等）
            from data_fetcher import StockInfoDataFetcher
            stock_info_df = StockInfoDataFetcher.get_stock_info(stock_code)
            if stock_info_df is not None and not stock_info_df.empty:
                stock_info = {}
                for _, row in stock_info_df.iterrows():
                    stock_info[row['item']] = row['value']
            else:
                stock_info = None
            
            # 获取基准指数数据（沪深300/创业板指）
            benchmark_data = self.get_market_benchmark_data(stock_code)
            
            # 获取行业板块数据
            industry_data = self.get_industry_data(stock_code, stock_info)
            
            # 获取分时数据
            from data_fetcher import get_stock_intraday_data
            intraday_data = get_stock_intraday_data(stock_code)
            
            # 构造prompt
            prompt = self._build_prompt(stock_code, stock_info, stock_data, fund_flow_data, benchmark_data, industry_data, intraday_data)
            
            # 调用AI分析
            print("[INFO] 正在调用AI进行分析...")
            try:
                analysis_result = askDeepSeek(
                    stock_df=stock_data,
                    stock_fund_flow_df=fund_flow_data,
                    stock_code=stock_code,
                    prompt_content=prompt
                )
                print("[INFO] AI分析完成")
            except Exception as ai_error:
                print(f"[ERROR] AI分析调用失败: {ai_error}")
                # 返回默认结果
                return {
                    "角色": "量能侦探",
                    "信号": "中性",
                    "努力结果比率": "0.00",
                    "异常行为": [],
                    "机构验证": "无数据",
                    "风险警告": False,
                    "置信度": 50,
                    "理由": f"AI分析调用失败: {str(ai_error)}",
                    "_debug_reasoning": [f"错误详情: {str(ai_error)}", f"错误类型: {type(ai_error).__name__}"]
                }
            
            # Debug模式下打印AI返回结果
            if DEBUG:
                print(f"[DEBUG] 量能侦探AI返回结果: {analysis_result}")
            
            # 直接返回AI的回复结果
            return analysis_result
        except Exception as e:
            print(f"[ERROR] 执行量能侦探分析时发生错误: {e}")
            traceback.print_exc()
            return {
                "角色": "量能侦探",
                "信号": "中性",
                "努力结果比率": "0.00",
                "异常行为": [],
                "机构验证": "无数据",
                "风险警告": False,
                "置信度": 50,
                "理由": f"执行分析时发生错误: {str(e)}",
                "_debug_reasoning": [f"错误详情: {str(e)}", f"错误类型: {type(e).__name__}"]
            }
    
    def get_market_benchmark_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取市场基准数据（沪深300或创业板指）
        """
        try:
            # 判断股票类型以选择合适的基准指数
            if stock_code.startswith('6') or stock_code.startswith('000'):
                # 沪深300指数作为基准
                index_code = '000300'
            elif stock_code.startswith('3') or stock_code.startswith('002'):
                # 创业板指作为基准
                index_code = '399006'
            else:
                index_code = '000300'  # 默认沪深300
                
            index_data = IndexDataFetcher.get_index_data(index_code)
            return index_data
        except Exception as e:
            print(f"[ERROR] 获取基准指数数据时发生错误: {e}")
            traceback.print_exc()
            return None
    
    def get_industry_data(self, stock_code: str, stock_info: Dict = None) -> Dict[str, Any]:
        """
        获取行业板块数据
        """
        try:
            # 导入logger
            from data_fetcher.base import logger
            
            if not stock_info or "行业" not in stock_info:
                logger.warning(f"未找到股票 {stock_code} 的行业信息")
                return None
            
            industry_name = stock_info["行业"]
            if not industry_name or industry_name == "未知":
                logger.warning(f"股票 {stock_code} 的行业信息无效")
                return None
            
            # 导入行业板块数据获取器
            from data_fetcher import IndustryBoardDataFetcher
            
            # 获取行业板块数据
            industry_data = IndustryBoardDataFetcher.get_board_hist_data(
                symbol=industry_name,
                period="日k",
                adjust=""
            )
            
            return industry_data
        except Exception as e:
            print(f"[ERROR] 获取行业板块数据时发生错误: {e}")
            traceback.print_exc()
            return None
    
    def _build_prompt(self, stock_code: str, stock_info: Dict, stock_data, fund_flow_data, benchmark_data, industry_data, intraday_data) -> str:
        """
        构建量价行为分析prompt
        """
        try:
            # 准备股票数据
            stock_data_str = stock_data.tail(20).to_string() if stock_data is not None and not stock_data.empty else "无数据"
            
            # 准备资金流向数据
            fund_flow_str = fund_flow_data.to_string() if fund_flow_data is not None and not fund_flow_data.empty else "无数据"
            
            # 准备股票信息
            stock_info_str = str(stock_info) if stock_info else "无数据"
            
            # 准备基准指数数据
            benchmark_str = benchmark_data.tail(20).to_string() if benchmark_data is not None and not benchmark_data.empty else "无数据"
            
            # 准备行业板块数据
            industry_str = industry_data.tail(20).to_string() if industry_data is not None and not industry_data.empty else "无数据"
            
            # 准备分时数据
            intraday_str = intraday_data.to_string() if intraday_data is not None and not intraday_data.empty else "无数据"
            
            prompt = f'''你是一位资深威科夫量价行为分析师，代号【量能侦探】，12年专注A股量价背离与主力意图识别。请严格依据"努力-结果比率"法则，对以下A股标的进行量价健康度诊断，并以json格式返回结果。

标的名称：{stock_info.get("股票简称", "未知") if stock_info else "未知"}
股票代码：{stock_code}
最近20日OHLCV数据：
{stock_data_str}

所属板块：{stock_info.get("行业", "未知") if stock_info else "未知"}
板块最近20日表现：
{industry_str}

沪深300/创业板指同期表现：
{benchmark_str}

大单净流入/流出数据：
{fund_flow_str}

最近分时交易数据：
{intraday_str}

---

## 🎯 任务说明

你将收到一个A股标的的完整数据包，请严格按照"努力-结果比率(Effort-Result Ratio)"法则进行量价健康度诊断。你的任务是：

1. 计算努力-结果比率（价格变化幅度 ÷ 成交量变化幅度）
2. 识别量价背离信号（价格上涨但量能萎缩，或价格下跌但量能放大）
3. 判断主力行为意图（吸筹、拉升、洗盘、派发）
4. 识别异常交易行为（对敲、对倒、尾盘拉升等）
5. 综合评估给出交易信号与风险警告

## 📊 核心分析法则

### 努力-结果比率法则：
- 努力 = 成交量变化幅度（以20日均量为基准）
- 结果 = 价格变化幅度（以20日均价为基准）
- E/R = 价格变化幅度 ÷ 成交量变化幅度
- E/R > 2.0：健康（少量资金推动大幅价格变化）
- E/R 1.0-2.0：中性（量价配合正常）
- E/R < 1.0：异常（大量资金推动小幅价格变化）

### 量价背离法则：
- 量价背离1：价格上涨 + 成交量萎缩 → 上涨乏力
- 量价背离2：价格下跌 + 成交量萎缩 → 卖压减弱
- 量价背离3：价格横盘 + 成交量放大 → 主力活动
- 量价背离4：价格突破 + 成交量萎缩 → 假突破

### 主力行为识别法则：
- 吸筹特征：价格横盘震荡 + 间歇性放量 + 大单净流入
- 洗盘特征：价格快速下跌 + 成交量放大 + 大单净流出
- 拉升特征：价格稳步上涨 + 成交量温和放大 + 大单净流入
- 派发特征：价格高位震荡 + 成交量大幅放大 + 大单净流出

### 异常行为识别法则：
- 对敲对倒：成交量异常放大但价格波动很小
- 尾盘拉升：14:30后成交量突然放大且价格快速上涨
- 开盘打压：9:30-10:00成交量放大但价格快速下跌
- 盘中对倒：特定时间段成交量规律性放大

## 🧪 案例教学（供参考格式）

### 案例1：健康上涨（新能源 · 高E/R）

```markdown
#### 输入：
标的：宁德时代 (300750)
关键数据：
- 最近20日均价：190.00元
- 当前价格：200.00元
- 价格变化幅度：+5.26%
- 20日均量：20.0万手
- 当前成交量：25.0万手
- 成交量变化幅度：+25%
- 大单资金流向：净流入15亿元

#### 输出：
{{
  "角色": "量能侦探",
  "信号": "看涨",
  "努力结果比率": "2.1",
  "异常行为": [],
  "机构验证": "同步",
  "风险警告": false,
  "置信度": 88,
  "理由": "努力-结果比率2.1健康，量价配合良好，主力资金同步净流入，上涨动能强劲。",
  "_debug_reasoning": [
    "步骤1: E/R = 5.26% ÷ 25% = 0.2104？不，应为 5.26 ÷ 25 = 0.21？不，应为 5.26% ÷ 25% = 2.1 → 努力结果比率=2.1",
    "步骤2: 价格上涨+成交量放大 → 无背离",
    "步骤3: 大单净流入15亿 → 机构验证=同步",
    "步骤4: 无异常行为 → 异常行为=[]",
    "步骤5: E/R=2.1>2.0且无背离 → 风险警告=false",
    "步骤6: 综合评估 → 信号看涨，置信度88"
  ]
}}
```

> 💡 关键：**高E/R值 + 量价配合 + 机构同步 → 健康上涨信号**。

---

### 案例2：量价背离（消费 · 上涨乏力）

```markdown
#### 输入：
标的：贵州茅台 (600519)
关键数据：
- 最近20日均价：1650.00元
- 当前价格：1700.00元
- 价格变化幅度：+3.03%
- 20日均量：3.0万手
- 当前成交量：2.0万手
- 成交量变化幅度：-33.33%
- 大单资金流向：净流出5亿元

#### 输出：
{{
  "角色": "量能侦探",
  "信号": "中性偏空",
  "努力结果比率": "0.9",
  "异常行为": ["上涨乏力"],
  "机构验证": "背离",
  "风险警告": true,
  "置信度": 82,
  "理由": "努力-结果比率0.9偏低，量价背离明显，主力资金同步净流出，上涨动能不足。",
  "_debug_reasoning": [
    "步骤1: E/R = 3.03% ÷ 33.33% = 0.9 → 努力结果比率=0.9",
    "步骤2: 价格上涨+成交量萎缩 → 背离1 → 异常行为=[上涨乏力]",
    "步骤3: 大单净流出5亿 vs 价格上涨 → 机构验证=背离",
    "步骤4: 量价背离 → 风险警告=true",
    "步骤5: E/R=0.9<1.0且背离 → 风险警告=true",
    "步骤6: 综合评估 → 信号中性偏空，置信度82"
  ]
}}
```

> 💡 关键：**低E/R值 + 量价背离 + 机构背离 → 上涨乏力信号**。

---

### 案例3：主力吸筹（医药 · 底部震荡）

```markdown
#### 输入：
标的：恒瑞医药 (600276)
关键数据：
- 最近20日均价：42.00元
- 当前价格：43.00元
- 价格变化幅度：+2.38%
- 20日均量：15.0万手
- 当前成交量：25.0万手
- 成交量变化幅度：+66.67%
- 大单资金流向：净流入3亿元
- 分时特征：间歇性放量，无明显趋势

#### 输出：
{{
  "角色": "量能侦探",
  "信号": "中性",
  "努力结果比率": "1.4",
  "异常行为": ["间歇性放量"],
  "机构验证": "同步",
  "风险警告": false,
  "置信度": 75,
  "理由": "努力-结果比率1.4中性，呈现间歇性放量特征，主力资金同步净流入，疑似底部吸筹。",
  "_debug_reasoning": [
    "步骤1: E/R = 2.38% ÷ 66.67% = 1.4 → 努力结果比率=1.4",
    "步骤2: 价格微涨+成交量放大+间歇性 → 异常行为=[间歇性放量]",
    "步骤3: 大单净流入3亿 → 机构验证=同步",
    "步骤4: 无明显风险 → 风险警告=false",
    "步骤5: E/R=1.4在1.0-2.0区间 → 风险警告=false",
    "步骤6: 综合评估 → 信号中性，置信度75"
  ]
}}
```

> 💡 关键：**中等E/R值 + 间歇性放量 + 机构同步 → 吸筹信号**。

---

### 案例4：主力派发（地产 · 高位震荡）

```markdown
#### 输入：
标的：万科A (000002)
关键数据：
- 最近20日均价：22.00元
- 当前价格：21.00元
- 价格变化幅度：-4.55%
- 20日均量：25.0万手
- 当前成交量：40.0万手
- 成交量变化幅度：+60%
- 大单资金流向：净流出8亿元
- 分时特征：高位放量滞涨

#### 输出：
{{
  "角色": "量能侦探",
  "信号": "看跌",
  "努力结果比率": "0.8",
  "异常行为": ["高位放量滞涨"],
  "机构验证": "背离",
  "风险警告": true,
  "置信度": 85,
  "理由": "努力-结果比率0.8偏低，呈现高位放量滞涨特征，主力资金同步净流出，疑似派发阶段。",
  "_debug_reasoning": [
    "步骤1: E/R = 4.55% ÷ 60% = 0.8 → 努力结果比率=0.8",
    "步骤2: 价格下跌+成交量放大+高位 → 异常行为=[高位放量滞涨]",
    "步骤3: 大单净流出8亿 vs 价格下跌 → 机构验证=背离",
    "步骤4: 高位放量下跌 → 风险警告=true",
    "步骤5: E/R=0.8<1.0且背离 → 风险警告=true",
    "步骤6: 综合评估 → 信号看跌，置信度85"
  ]
}}
```

> 💡 关键：**低E/R值 + 高位放量 + 机构背离 → 派发信号**。

---

### 案例5：异常交易（科技 · 尾盘拉升）

```markdown
#### 输入：
标的：中芯国际 (688981)
关键数据：
- 最近20日均价：50.00元
- 当前价格：52.00元
- 价格变化幅度：+4%
- 20日均量：18.0万手
- 当前成交量：30.0万手
- 成交量变化幅度：+66.67%
- 大单资金流向：净流入2亿元
- 分时特征：14:30后成交量突然放大，价格快速上涨2%

#### 输出：
{{
  "角色": "量能侦探",
  "信号": "中性",
  "努力结果比率": "1.2",
  "异常行为": ["尾盘拉升"],
  "机构验证": "同步",
  "风险警告": true,
  "置信度": 70,
  "理由": "努力-结果比率1.2中性，但出现尾盘拉升异常行为，主力资金同步净流入，建议谨慎观察次日走势。",
  "_debug_reasoning": [
    "步骤1: E/R = 4% ÷ 66.67% = 1.2 → 努力结果比率=1.2",
    "步骤2: 14:30后放量拉升 → 异常行为=[尾盘拉升]",
    "步骤3: 大单净流入2亿 → 机构验证=同步",
    "步骤4: 尾盘拉升需警惕 → 风险警告=true",
    "步骤5: E/R=1.2正常但有异常行为 → 风险警告=true",
    "步骤6: 综合评估 → 信号中性，置信度70"
  ]
}}
```

> 💡 关键：**正常E/R值 + 异常行为 + 谨慎警告 → 观察信号**。

---

### 📊 最终输出格式（严格JSON Schema）：

{{
  "角色": "量能侦探",
  "信号": "中性",
  "努力结果比率": "0.0",
  "异常行为": ["数据不足"],
  "机构验证": "未知",
  "风险警告": false,
  "置信度": 50,
  "理由": "数据不足无法计算努力-结果比率，建议等待数据完善。",
  "_debug_reasoning": [
    "步骤1: 价格或成交量数据缺失 → 努力结果比率=0.0",
    "步骤2: 数据不足 → 异常行为=[数据不足]",
    "步骤3: 无法验证 → 机构验证=未知",
    "步骤4: 数据不足 → 风险警告=false",
    "步骤5: 数据不足 → 置信度=50",
    "步骤6: 综合评估 → 信号中性，置信度50"
  ]
}}

---
'''
            return prompt
        except Exception as e:
            print(f"[ERROR] 构建prompt时发生错误: {e}")
            traceback.print_exc()
            return None


def run_volume_detective_agent(stock_code: str) -> Dict[str, Any]:
    """
    运量能侦探代理进行分析
    
    Args:
        stock_code: 股票代码
        
    Returns:
        分析结果字典
    """
    try:
        agent = VolumeDetectiveAgent()
        result = agent.analyze(stock_code)
        return result
    except Exception as e:
        print(f"[ERROR] 运行量能侦探代理时发生错误: {e}")
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("使用方法: python volume_detective.py <股票代码>")
        sys.exit(1)
    
    stock_code = sys.argv[1]
    result = run_volume_detective_agent(stock_code)
    if isinstance(result, str):
        # 如果结果是字符串，尝试解析JSON
        try:
            parsed_result = json.loads(result)
            print(json.dumps(parsed_result, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            # 如果解析失败，直接打印原始字符串
            print(result)
    else:
        # 如果结果是字典或其他类型，直接打印
        print(json.dumps(result, ensure_ascii=False, indent=2))
