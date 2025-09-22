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


class TargetEngineerAgent:
    """
    目标工程师Agent - 基于威科夫因果法则进行目标/风险测算
    """
    
    def __init__(self):
        self.name = "目标工程师"
        
    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """
        执行目标工程师分析
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
                print(f"[DEBUG] 目标工程师AI返回结果: {analysis_result}")
            
            # 直接返回AI的回复结果
            return analysis_result
        except Exception as e:
            print(f"[ERROR] 执行目标工程师分析时发生错误: {e}")
            traceback.print_exc()
            return {
                "角色": "目标工程师",
                "信号": "中性",
                "因果空间": "¥0.00",
                "K값": 1.0,
                "目标价": "¥0.00",
                "盈亏比": "0.0",
                "可执行": False,
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
    
    def _build_prompt(self, stock_code: str, stock_info: Dict, stock_data, fund_flow_data, benchmark_data, industry_data) -> str:
        """
        构建因果分析prompt
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
            
            prompt = f'''你是一位资深威科夫因果分析师，代号【目标工程师】，10年专注A股因果空间测算与盈亏比建模。请严格依据"因果法则"，对以下A股标的进行目标/风险测算，并以json格式返回结果。

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

你将收到一个A股标的的完整数据包，请严格按照"威科夫因果法则"进行目标价与风险位测算。你的任务是：

1. 识别最近一次供给（供应）区域与需求（支撑）区域
2. 计算因果空间（供给区域顶部 - 需求区域底部）
3. 测算目标价（当前价格 + 因果空间 × K系数）
4. 确定止损位（需求区域底部或关键支撑位）
5. 计算盈亏比（目标价 - 当前价）÷（当前价 - 止损位）
6. 综合评估给出交易信号与执行建议

## 📊 核心测算法则

### 因果空间法则：
- 因果空间 = 最近供给区顶部 - 最近需求区底部
- 供给区：成交量密集的高点区域（主力派发）
- 需求区：成交量密集的低点区域（主力吸筹）

### 目标价法则：
- 目标价 = 当前价格 + 因果空间 × K系数
- K系数：根据市场环境与个股特性动态调整（1.0-3.0）
- 牛市或强势股：K=2.0-3.0
- 震荡市或中性股：K=1.5-2.0
- 熊市或弱势股：K=1.0-1.5

### 止损位法则：
- 止损位 = 需求区底部 - 缓冲空间
- 缓冲空间 = 因果空间 × 0.1-0.2
- 也可设置在关键支撑位下方1-2%

### 盈亏比法则：
- 盈亏比 = （目标价 - 当前价）÷（当前价 - 止损位）
- 盈亏比 > 3.0：极佳（强烈执行）
- 盈亏比 2.0-3.0：良好（可以执行）
- 盈亏比 1.5-2.0：一般（谨慎执行）
- 盈亏比 < 1.5：较差（不建议执行）

## 🧪 案例教学（供参考格式）

### 案例1：标准上涨形态（新能源 · 清晰因果）

```markdown
#### 输入：
标的：宁德时代 (300750)
关键数据：
- 当前价格：200.00元
- 最近供给区（2025-08-20至08-25）：顶部220.00元
- 最近需求区（2025-09-01至09-05）：底部180.00元
- K系数：2.5（强势股）
- 关键支撑位：175.00元

#### 输出：
{{
  "角色": "目标工程师",
  "信号": "看涨",
  "因果空间": "¥40.00",
  "K值": 2.5,
  "目标价": "¥300.00",
  "盈亏比": "4.0",
  "可执行": true,
  "置信度": 90,
  "理由": "因果空间40元清晰，K=2.5合理，目标价300元，盈亏比4.0极佳，强烈建议执行。",
  "_debug_reasoning": [
    "步骤1: 因果空间 = 220.00 - 180.00 = 40.00元 → 因果空间=¥40.00",
    "步骤2: 目标价 = 200.00 + 40.00 × 2.5 = 300.00元 → 目标价=¥300.00",
    "步骤3: 止损位 = 180.00 - 40.00 × 0.1 = 176.00元（接近关键支撑175.00）→ 止损位=¥175.00",
    "步骤4: 盈亏比 = (300.00 - 200.00) ÷ (200.00 - 175.00) = 4.0 → 盈亏比=4.0",
    "步骤5: 盈亏比4.0 > 3.0 → 可执行=true",
    "步骤6: 综合评估 → 信号看涨，置信度90"
  ]
}}
```

> 💡 关键：**清晰的因果空间 + 合理的K值 + 极佳盈亏比 → 强烈执行信号**。

---

### 案例2：震荡形态（消费 · 缩小空间）

```markdown
#### 输入：
标的：五粮液 (000858)
关键数据：
- 当前价格：160.00元
- 最近供给区（2025-08-15至08-20）：顶部175.00元
- 最近需求区（2025-09-05至09-10）：底部155.00元
- K系数：1.8（中性股）
- 关键支撑位：152.00元

#### 输出：
{{
  "角色": "目标工程师",
  "信号": "中性",
  "因果空间": "¥20.00",
  "K值": 1.8,
  "目标价": "¥196.00",
  "盈亏比": "2.4",
  "可执行": true,
  "置信度": 75,
  "理由": "因果空间20元较小，K=1.8适中，目标价196元，盈亏比2.4良好，可以执行但需控制仓位。",
  "_debug_reasoning": [
    "步骤1: 因果空间 = 175.00 - 155.00 = 20.00元 → 因果空间=¥20.00",
    "步骤2: 目标价 = 160.00 + 20.00 × 1.8 = 196.00元 → 目标价=¥196.00",
    "步骤3: 止损位 = 155.00 - 20.00 × 0.15 = 152.00元（等于关键支撑）→ 止损位=¥152.00",
    "步骤4: 盈亏比 = (196.00 - 160.00) ÷ (160.00 - 152.00) = 2.4 → 盈亏比=2.4",
    "步骤5: 盈亏比2.4在2.0-3.0区间 → 可执行=true",
    "步骤6: 综合评估 → 信号中性，置信度75"
  ]
}}
```

> 💡 关键：**较小的因果空间 + 适中的盈亏比 → 谨慎执行信号**。

---

### 案例3：下跌形态（地产 · 倒置空间）

```markdown
#### 输入：
标的：万科A (000002)
关键数据：
- 当前价格：20.00元
- 最近供给区（2025-07-20至07-25）：顶部25.00元
- 最近需求区（2025-09-01至09-05）：底部22.00元
- K系数：1.2（弱势股）
- 关键支撑位：18.00元

#### 输出：
{{
  "角色": "目标工程师",
  "信号": "看跌",
  "因果空间": "¥3.00",
  "K值": 1.2,
  "目标价": "¥23.60",
  "盈亏比": "1.2",
  "可执行": false,
  "置信度": 85,
  "理由": "因果空间3元倒置（需求区高于供给区），K=1.2保守，目标价23.6元，盈亏比1.2极差，强烈建议观望。",
  "_debug_reasoning": [
    "步骤1: 因果空间 = 25.00 - 22.00 = 3.00元 → 因果空间=¥3.00",
    "步骤2: 目标价 = 20.00 + 3.00 × 1.2 = 23.60元 → 目标价=¥23.60",
    "步骤3: 止损位 = 22.00 - 3.00 × 0.2 = 21.40元（高于当前价）→ 止损位=¥18.00（关键支撑）",
    "步骤4: 盈亏比 = (23.60 - 20.00) ÷ (20.00 - 18.00) = 1.2 → 盈亏比=1.2",
    "步骤5: 盈亏比1.2 < 1.5 → 可执行=false",
    "步骤6: 综合评估 → 信号看跌，置信度85"
  ]
}}
```

> 💡 关键：**倒置的因果空间 + 极差盈亏比 → 强烈观望信号**。

---

### 案例4：突破形态（科技 · 扩大空间）

```markdown
#### 输入：
标的：中芯国际 (688981)
关键数据：
- 当前价格：50.00元
- 最近供给区（2025-08-10至08-15）：顶部45.00元
- 最近需求区（2025-08-25至08-30）：底部40.00元
- K系数：2.8（强势突破）
- 关键支撑位：48.00元

#### 输出：
{{
  "角色": "目标工程师",
  "信号": "看涨",
  "因果空间": "¥5.00",
  "K值": 2.8,
  "目标价": "¥64.00",
  "盈亏比": "3.5",
  "可执行": true,
  "置信度": 88,
  "理由": "突破形态因果空间5元，K=2.8体现突破力度，目标价64元，盈亏比3.5极佳，建议积极执行。",
  "_debug_reasoning": [
    "步骤1: 因果空间 = 45.00 - 40.00 = 5.00元 → 因果空间=¥5.00",
    "步骤2: 目标价 = 50.00 + 5.00 × 2.8 = 64.00元 → 目标价=¥64.00",
    "步骤3: 止损位 = 48.00元（关键支撑）→ 止损位=¥48.00",
    "步骤4: 盈亏比 = (64.00 - 50.00) ÷ (50.00 - 48.00) = 3.5 → 盈亏比=3.5",
    "步骤5: 盈亏比3.5 > 3.0 → 可执行=true",
    "步骤6: 综合评估 → 信号看涨，置信度88"
  ]
}}
```

> 💡 关键：**突破形态 + 较大K值 + 极佳盈亏比 → 积极执行信号**。

---

### 案例5：底部形态（医药 · 筑底完成）

```markdown
#### 输入：
标的：恒瑞医药 (600276)
关键数据：
- 当前价格：45.00元
- 最近供给区（2025-06-10至06-15）：顶部55.00元
- 最近需求区（2025-07-20至08-10）：底部42.00元
- K系数：2.2（筑底完成）
- 关键支撑位：40.00元

#### 输出：
{{
  "角色": "目标工程师",
  "信号": "看涨",
  "因果空间": "¥13.00",
  "K值": 2.2,
  "目标价": "¥73.60",
  "盈亏比": "2.8",
  "可执行": true,
  "置信度": 82,
  "理由": "筑底完成形态因果空间13元较大，K=2.2合理，目标价73.6元，盈亏比2.8良好，建议执行。",
  "_debug_reasoning": [
    "步骤1: 因果空间 = 55.00 - 42.00 = 13.00元 → 因果空间=¥13.00",
    "步骤2: 目标价 = 45.00 + 13.00 × 2.2 = 73.60元 → 目标价=¥73.60",
    "步骤3: 止损位 = 42.00 - 13.00 × 0.15 = 40.05元（接近关键支撑40.00）→ 止损位=¥40.00",
    "步骤4: 盈亏比 = (73.60 - 45.00) ÷ (45.00 - 40.00) = 2.8 → 盈亏比=2.8",
    "步骤5: 盈亏比2.8在2.0-3.0区间 → 可执行=true",
    "步骤6: 综合评估 → 信号看涨，置信度82"
  ]
}}
```

> 💡 关键：**较大因果空间 + 合理K值 + 良好盈亏比 → 建议执行信号**。

---

### 📊 最终输出格式（严格JSON Schema）：

{{
  "角色": "目标工程师",
  "信号": "中性",
  "因果空间": "¥0.00",
  "K值": 1.0,
  "目标价": "¥0.00",
  "盈亏比": "0.0",
  "可执行": false,
  "置信度": 50,
  "理由": "数据不足无法测算因果空间，建议等待形态明确。",
  "_debug_reasoning": [
    "步骤1: 无法识别清晰的供给区与需求区 → 因果空间=¥0.00",
    "步骤2: 因果空间为0 → 目标价=¥0.00",
    "步骤3: 因果空间为0 → 止损位=¥0.00",
    "步骤4: 无法计算盈亏比 → 盈亏比=0.0",
    "步骤5: 盈亏比0.0 < 1.5 → 可执行=false",
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


def run_target_engineer_agent(stock_code: str) -> Dict[str, Any]:
    """
    运行目标工程师agent
    
    Args:
        stock_code: 股票代码
        
    Returns:
        分析结果
    """
    try:
        agent = TargetEngineerAgent()
        return agent.analyze(stock_code)
    except Exception as e:
        print(f"[ERROR] 运行目标工程师agent时发生错误: {e}")
        traceback.print_exc()
        return {
            "角色": "目标工程师",
            "信号": "中性",
            "因果空间": "¥0.00",
            "K값": 1.0,
            "目标价": "¥0.00",
            "盈亏比": "0.0",
            "可执行": False,
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
        
        result = run_target_engineer_agent(stock_code)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[ERROR] 执行目标工程师分析时发生错误: {e}")
        traceback.print_exc()
