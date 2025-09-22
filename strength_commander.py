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

# 导入logger
from data_fetcher.base import logger


class StrengthCommanderAgent:
    """
    强度指挥官Agent - 基于威科夫相对强度分析个股与板块轮动强度
    """
    
    def __init__(self):
        self.name = "强度指挥官"
        
    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """
        执行强度指挥官分析
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
            
            # 构造prompt
            prompt = self._build_prompt(stock_code, stock_info, stock_data, fund_flow_data, benchmark_data, industry_data)
            
            # 调用AI分析
            analysis_result = askDeepSeek(
                stock_df=stock_data,
                stock_fund_flow_df=fund_flow_data,
                stock_code=stock_code,
                prompt_content=prompt
            )
            
            # Debug模式下打印AI返回结果
            if DEBUG:
                print(f"[DEBUG] 强度指挥官AI返回结果: {analysis_result}")
            
            # 直接返回AI的回复结果
            return analysis_result
        except Exception as e:
            print(f"[ERROR] 执行强度指挥官分析时发生错误: {e}")
            traceback.print_exc()
            return {
                "角色": "强度指挥官",
                "信号": "中性",
                "相对强度RS": 0.00,
                "板块同步": False,
                "资金流向": "无数据",
                "评分调整": "维持",
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
    
    def _build_prompt(self, stock_code: str, stock_info: Dict, stock_data, fund_flow_data, benchmark_data, industry_data) -> str:
        """
        构建相对强度分析prompt
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
            
            prompt = f'''你是一位资深威科夫相对强度分析师，代号【强度指挥官】，8年专注A股个股与板块轮动强度分析。请严格依据"相对强度RS法则"与"市场同步性法则"，对以下A股标的进行资金流向诊断，并以json格式返回结果。

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

---

## 🎯 任务说明

你将收到一个A股标的的完整数据包，请严格按照"相对强度RS法则"与"市场同步性法则"进行强度诊断。你的任务是：

1. 计算个股相对强度RS值（个股涨跌幅/基准指数涨跌幅）
2. 判断个股与板块、大盘的同步性（同涨同跌为正相关）
3. 识别主力资金流向（净流入/净流出）
4. 综合评估给出强度评分与交易信号

## 📊 核心分析法则

### 相对强度RS法则：
- RS = 个股涨跌幅 ÷ 基准指数涨跌幅
- RS > 1.2：强势（跑赢大盘20%以上）
- RS 0.8-1.2：中性（与大盘基本同步）
- RS < 0.8：弱势（跑输大盘20%以上）

### 市场同步性法则：
- 个股与板块同涨：正向同步，加分
- 个股涨板块跌：逆向强势，高分
- 个股跌板块涨：逆向弱势，扣分
- 个股与板块同跌：负向同步，减分

### 资金流向法则：
- 大单净流入 + 股价上涨：健康上涨
- 大单净流入 + 股价下跌：主力吸筹
- 大单净流出 + 股价上涨：散户推动，风险高
- 大单净流出 + 股价下跌：主力派发，风险极高

## 🧪 案例教学（供参考格式）

### 案例1：相对强势股（新能源 · 机构同步）

```markdown
#### 输入：
标的：比亚迪 (002594)
关键数据：
- 近20日涨跌幅：+35%
- 沪深300同期涨跌幅：+10%
- 所属板块：新能源汽车
- 板块近20日涨跌幅：+28%
- 大单资金流向：净流入85亿元

#### 输出：
{{
  "角色": "强度指挥官",
  "信号": "看涨",
  "相对强度RS": 3.5,
  "板块同步": true,
  "资金流向": "净流入",
  "评分调整": "加分",
  "置信度": 92,
  "理由": "相对强度RS=3.5远超阈值1.2，与板块高度同步，主力资金持续净流入，强势特征明显。",
  "_debug_reasoning": [
    "步骤1: RS = 35% ÷ 10% = 3.5 > 1.2 → 强势",
    "步骤2: 个股+35% vs 板块+28% → 正向同步 → 板块同步=true",
    "步骤3: 大单净流入85亿 → 资金流向=净流入",
    "步骤4: 强势+同步+资金流入 → 评分调整=加分",
    "步骤5: 综合评估 → 信号看涨，置信度92"
  ]
}}
```

> 💡 关键：**RS值高 + 板块同步 + 资金流入 → 极强态势**。

---

### 案例2：相对弱势股（地产 · 逆向背离）

```markdown
#### 输入：
标的：万科A (000002)
关键数据：
- 近20日涨跌幅：-5%
- 沪深300同期涨跌幅：+10%
- 所属板块：房地产
- 板块近20日涨跌幅：+12%
- 大单资金流向：净流出32亿元

#### 输出：
{{
  "角色": "强度指挥官",
  "信号": "看跌",
  "相对强度RS": -0.5,
  "板块同步": false,
  "资金流向": "净流出",
  "评分调整": "扣分",
  "置信度": 88,
  "理由": "相对强度RS=-0.5严重偏离，与板块走势背离，主力资金持续净流出，弱势特征明显。",
  "_debug_reasoning": [
    "步骤1: RS = -5% ÷ 10% = -0.5 < 0.8 → 弱势",
    "步骤2: 个股-5% vs 板块+12% → 背离 → 板块同步=false",
    "步骤3: 大单净流出32亿 → 资金流向=净流出",
    "步骤4: 弱势+背离+资金流出 → 评分调整=扣分",
    "步骤5: 综合评估 → 信号看跌，置信度88"
  ]
}}
```

> 💡 关键：**RS值低 + 板块背离 + 资金流出 → 极弱态势**。

---

### 案例3：假强真弱（消费 · 散户推动）

```markdown
#### 输入：
标的：贵州茅台 (600519)
关键数据：
- 近20日涨跌幅：+15%
- 沪深300同期涨跌幅：+10%
- 所属板块：白酒
- 板块近20日涨跌幅：+8%
- 大单资金流向：净流出18亿元

#### 输出：
{{
  "角色": "强度指挥官",
  "信号": "中性偏空",
  "相对强度RS": 1.5,
  "板块同步": false,
  "资金流向": "净流出",
  "评分调整": "维持",
  "置信度": 75,
  "理由": "相对强度RS=1.5看似强势，但主力资金持续净流出，呈现散户推动特征，上涨不可持续。",
  "_debug_reasoning": [
    "步骤1: RS = 15% ÷ 10% = 1.5 > 1.2 → 表面强势",
    "步骤2: 个股+15% vs 板块+8% → 微弱同步 → 板块同步=false",
    "步骤3: 大单净流出18亿 → 资金流向=净流出",
    "步骤4: 表面强势但资金背离 → 评分调整=维持",
    "步骤5: 综合评估 → 信号中性偏空，置信度75"
  ]
}}
```

> 💡 关键：**表面强势但资金背离 → 警惕回调风险**。

---

### 案例4：底部吸筹（医药 · 逆市吸筹）

```markdown
#### 输入：
标的：恒瑞医药 (600276)
关键数据：
- 近20日涨跌幅：-3%
- 沪深300同期涨跌幅：+10%
- 所属板块：化学制药
- 板块近20日涨跌幅：+5%
- 大单资金流向：净流入12亿元

#### 输出：
{{
  "角色": "强度指挥官",
  "信号": "中性偏多",
  "相对强度RS": -0.3,
  "板块同步": true,
  "资金流向": "净流入",
  "评分调整": "加分",
  "置信度": 80,
  "理由": "相对强度RS=-0.3看似弱势，但主力资金持续净流入，呈现逆市吸筹特征，底部构筑中。",
  "_debug_reasoning": [
    "步骤1: RS = -3% ÷ 10% = -0.3 < 0.8 → 表面弱势",
    "步骤2: 个股-3% vs 板块+5% → 负向同步 → 板块同步=true",
    "步骤3: 大单净流入12亿 → 资金流向=净流入",
    "步骤4: 表面弱势但资金流入 → 评分调整=加分",
    "步骤5: 综合评估 → 信号中性偏多，置信度80"
  ]
}}
```

> 💡 关键：**表面弱势但资金流入 → 底部吸筹信号**。

---

### 案例5：风险释放（科技 · 利空出尽）

```markdown
#### 输入：
标的：中芯国际 (688981)
关键数据：
- 近20日涨跌幅：+22%
- 沪深300同期涨跌幅：+10%
- 所属板块：半导体
- 板块近20日涨跌幅：+18%
- 大单资金流向：净流入5亿元

#### 输出：
{{
  "角色": "强度指挥官",
  "信号": "看涨",
  "相对强度RS": 2.2,
  "板块同步": true,
  "资金流向": "净流入",
  "评分调整": "加分",
  "置信度": 85,
  "理由": "相对强度RS=2.2强势，与板块同步上涨，主力资金持续净流入，利空出尽反弹可期。",
  "_debug_reasoning": [
    "步骤1: RS = 22% ÷ 10% = 2.2 > 1.2 → 强势",
    "步骤2: 个股+22% vs 板块+18% → 正向同步 → 板块同步=true",
    "步骤3: 大单净流入5亿 → 资金流向=净流入",
    "步骤4: 强势+同步+资金流入 → 评分调整=加分",
    "步骤5: 综合评估 → 信号看涨，置信度85"
  ]
}}
```

> 💡 关键：**RS值高 + 板块同步 + 资金流入 → 利空出尽反弹**。

---

### 📊 最终输出格式（严格JSON Schema）：

{{
  "角色": "强度指挥官",
  "信号": "中性",
  "相对强度RS": 1.00,
  "板块同步": false,
  "资金流向": "无数据",
  "评分调整": "维持",
  "置信度": 70,
  "理由": "相对强度RS=1.0处于中性区间，与板块走势背离，资金流向不明确，建议观望。",
  "_debug_reasoning": [
    "步骤1: RS = 5% ÷ 5% = 1.0 → 中性范围",
    "步骤2: 个股+5% vs 板块+8% → 轻微背离 → 板块同步=false",
    "步骤3: 资金流向数据缺失 → 资金流向=无数据",
    "步骤4: 中性+背离+数据缺失 → 评分调整=维持",
    "步骤5: 综合评估 → 信号中性，置信度70"
  ]
}}

---
'''
            return prompt
        except Exception as e:
            print(f"[ERROR] 构建prompt时发生错误: {e}")
            traceback.print_exc()
            return None


def run_strength_commander_agent(stock_code: str) -> Dict[str, Any]:
    """
    运行强度指挥官agent
    
    Args:
        stock_code: 股票代码
        
    Returns:
        分析结果
    """
    try:
        agent = StrengthCommanderAgent()
        return agent.analyze(stock_code)
    except Exception as e:
        print(f"[ERROR] 运行强度指挥官agent时发生错误: {e}")
        traceback.print_exc()
        return {
            "角色": "强度指挥官",
            "信号": "中性",
            "相对强度RS": 0.00,
            "板块同步": False,
            "资金流向": "无数据",
            "评分调整": "维持",
            "置信度": 50,
            "理由": f"运行agent时发生错误: {str(e)}",
            "_debug_reasoning": [f"错误详情: {str(e)}", f"错误类型: {type(e).__name__}"]
        }


if __name__ == "__main__":
    # 单独测试时使用
    try:
        import sys
        if len(sys.argv) > 1:
            stock_code = sys.argv[1]
        else:
            stock_code = input("请输入股票代码（例如：002050）: ")
        
        result = run_strength_commander_agent(stock_code)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[ERROR] 执行强度指挥官分析时发生错误: {e}")
        traceback.print_exc()
