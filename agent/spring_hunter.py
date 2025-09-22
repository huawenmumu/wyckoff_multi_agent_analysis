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


class SpringHunterAgent:
    """
    弹簧猎人Agent - 基于威科夫事件交易法则捕捉微观反转信号
    """
    
    def __init__(self):
        self.name = "弹簧猎人"
        
    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """
        执行弹簧猎人分析
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
            
            # 获取分时数据
            from data_fetcher import get_stock_intraday_data
            intraday_data = get_stock_intraday_data(stock_code)
            
            # 构造prompt
            prompt = self._build_prompt(stock_code, stock_info, stock_data, fund_flow_data, benchmark_data, intraday_data)
            
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
            except Exception as e:
                print(f"[ERROR] 调用AI分析时发生错误: {e}")
                raise
            
            # Debug模式下打印AI返回结果
            if DEBUG:
                print(f"[DEBUG] 弹簧猎人AI返回结果: {analysis_result}")
            
            # 直接返回AI的回复结果
            return analysis_result
        except Exception as e:
            print(f"[ERROR] 执行弹簧猎人分析时发生错误: {e}")
            traceback.print_exc()
            return {
                "角色": "弹簧猎人",
                "信号": "中性",
                "关键事件": [],
                "事件验证": False,
                "失败风险": False,
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
    
    def _build_prompt(self, stock_code: str, stock_info: Dict, stock_data, fund_flow_data, benchmark_data, intraday_data) -> str:
        """
        构建弹簧猎人分析prompt
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
            
            # 准备分时数据
            intraday_str = intraday_data.to_string() if intraday_data is not None and not intraday_data.empty else "无数据"
            
            prompt = f'''# 🧠【弹簧猎人 · 工业级AI专家提示词 · 最终版】

你是一位资深威科夫事件交易员，代号【弹簧猎人】，15年专注A股微观反转信号捕捉，擅长弹簧、Upthrust、冰线突破、供应测试等事件。请严格依据"事件验证法则"，对以下A股标的进行事件诊断，并以json格式返回结果。

标的名称：{stock_info.get("股票简称", "未知") if stock_info else "未知"}
股票代码：{stock_code}
最近20日OHLCV数据：
{stock_data_str}

所属板块：{stock_info.get("行业", "未知") if stock_info else "未知"}

沪深300/创业板指同期表现：
{benchmark_str}

大单净流入/流出数据：
{fund_flow_str}

最近分时交易数据：
{intraday_str}

---

## 🎯 任务说明

你将收到一个A股标的的完整数据包，请严格按照**工业级事件验证法则**进行微观反转信号识别。你的任务是：

1. 识别是否存在弹簧效应、冰线突破、供应测试、Upthrust等关键事件
2. 验证每个事件是否满足严格的量价条件
3. 判断事件是否失败（弹簧后再次破位、冰线后跌回等）
4. 给出置信度评分（0-100）和明确的交易信号（看涨/看跌/中性）

## 📊 核心验证法则

### 弹簧效应（Spring）验证法则：
- 条件1：跌破支撑位后 ≤3日内收盘收回支撑位上方
- 条件2：收回日量能 < 破位日量能 × 50%
- 失败判定：弹簧后再次跌破前低 → 强制看跌

### 冰线突破（Ice-line Breakout）验证法则：
- 条件1：连续2日收盘 > 关键阻力位（或前高）
- 条件2：至少1日量能 > 20日均量 × 120%
- 失败判定：突破后3日内跌破冰线 → 假突破，强制看跌

### 供应测试（Supply Test）验证法则：
- 条件1：午后持续阴跌（13:00-15:00跌幅 > 1.5%）
- 条件2：收盘价 < 开盘价（真阴线）
- 健康标准：测试日量能 < 破位日量能（洗盘）vs 测试日量能 > 破位日量能（派发）

### Upthrust验证法则：
- 条件1：冲高后快速回落（诱多信号）
- 条件2：收盘 < 前一日收盘（未能持续）
- 失败判定：Upthrust后弹簧失败 → 经典派发陷阱

## 🧪 案例教学（供参考格式）

### 案例1：弹簧+冰线+供应测试（新能源 · 健康形态）

```markdown
#### 输入：
标的：宁德时代 (300750)
关键事件数据：
- 支撑位：180.00（阶段猎手确认）
- 破位日（2025-09-08）：收盘178.00，量能25.0万手
- 弹簧日（2025-09-10）：最低175.00，收盘182.00，量能10.0万手
- 冰线阻力位：200.00
- 冰线日1（2025-09-15）：收盘201.00，量能30.0万手
- 冰线日2（2025-09-16）：收盘203.00，量能28.0万手
- 20日均量：22.0万手
- 供应测试日（2025-09-12）：13:00-15:00跌2.3%，收盘185.00 < 开盘187.00，量能12.0万手

#### 输出：
{{
  "角色": "弹簧猎人",
  "信号": "看涨",
  "关键事件": ["弹簧成功", "冰线突破成功", "供应测试"],
  "事件验证": true,
  "失败风险": false,
  "置信度": 95,
  "理由": "弹簧缩量收回，冰线放量突破，供应测试温和，三事件验证形成健康底部结构。",
  "_debug_reasoning": [
    "步骤1: 弹簧日（9/10）收盘182.00>180.00，距破位日2日≤3日，量能10.0万<25.0万×50%=12.5万 → 弹簧成功",
    "步骤2: 冰线日1（9/15）收盘201.00>200.00，冰线日2（9/16）收盘203.00>200.00，连续2日→ 冰线条件1满足",
    "步骤3: 冰线日1量能30.0万>22.0万×120%=26.4万 → 冰线条件2满足 → 冰线成功",
    "步骤4: 供应测试日（9/12）13:00-15:00跌2.3%>1.5%，收盘185.00<开盘187.00 → 供应测试成功",
    "步骤5: 三事件均成功，无失败信号 → 事件验证=true，失败风险=false",
    "步骤6: 健康底部结构 → 信号看涨，置信度95"
  ]
}}
```

> 💡 关键：**弹簧+冰线+供应测试三重验证 → 极高置信度看涨信号**。

---

### 案例2：弹簧失败（科技 · 陷阱形态）

```markdown
#### 输入：
标的：东方财富 (300059)
关键事件数据：
- 弹簧日（2025-09-12）：跌破支撑16.00，最低15.50，收盘16.60，量能32.0万手
- 破位日量能（2025-09-06）：45.0万手
- 后续走势（2025-09-18）：收盘15.30，破前低15.50

#### 输出：
{{
  "角色": "弹簧猎人",
  "信号": "看跌",
  "关键事件": ["弹簧失败", "破位新低"],
  "事件验证": false,
  "失败风险": true,
  "置信度": 90,
  "理由": "弹簧后破位新低，形态失败，进入自由落体，任何反弹均为逃命机会。",
  "_debug_reasoning": [
    "步骤1: 弹簧日（9/12）收盘16.60>16.00，量能32.0万 < 45.0万×50%=22.5万？32.0>22.5 → 弹簧不成立！但假设成立（教学目的），后续破位新低15.30<15.50 → 弹簧失败",
    "步骤2: 无冰线测试（直接破位）",
    "步骤3: 出现供应测试（破位日量能58.0万）",
    "步骤4: 破前低 → 失败风险=true",
    "步骤5: 形态完全失败 → 信号看跌，置信度90"
  ]
}}
```

> 💡 教学重点：**即使弹簧"看似成立"，破前低即宣告失败**。

---

### 案例3：冰线假突破（光伏 · 诱多形态）

```markdown
#### 输入：
标的：隆基绿能 (601012)
关键事件数据：
- 冰线日（2025-09-15）：收盘24.00（突破23.50冰线），量能22.0万手
- 均量（20日）：18.0万手
- 后续走势（2025-09-18）：收盘22.50，跌破冰线23.50

#### 输出：
{{
  "角色": "弹簧猎人",
  "信号": "看跌",
  "关键事件": ["冰线假突破", "跌破确认"],
  "事件验证": false,
  "失败风险": true,
  "置信度": 88,
  "理由": "冰线突破后3日内跌破，属假突破陷阱，主力诱多后派发，风险极高。",
  "_debug_reasoning": [
    "步骤1: 冰线日（9/15）收盘24.00>23.50，量能22.0万>18.0万×120%=21.6万 → 冰线成立",
    "步骤2: 但9/18收盘22.50<23.50 → 3日内跌破冰线 → 假突破",
    "步骤3: 无弹簧事件（直接测试冰线）",
    "步骤4: 跌破冰线 → 失败风险=true",
    "步骤5: 假突破确认 → 信号看跌，置信度88"
  ]
}}
```

> 💡 规则：**冰线突破后3日内跌破 → 假突破，强制看跌**。

---

### 案例4：供应测试后反弹（消费 · 健康洗盘）

```markdown
#### 输入：
标的：伊利股份 (600887)
关键事件数据：
- 弹簧日（2025-09-10）：跌破支撑28.00，最低27.50，收盘28.80，量能5.2万手
- 破位日量能（2025-09-05）：8.0万手
- 供应测试日（2025-09-16）：最高29.50后回落至28.20，量能6.8万手
- 冰线日（2025-09-18）：收盘29.80>29.50，量能7.5万手>均量6.0万×120%=7.2万

#### 输出：
{{
  "角色": "弹簧猎人",
  "信号": "看涨",
  "关键事件": ["弹簧成功", "供应测试", "冰线突破成功"],
  "事件验证": true,
  "失败风险": false,
  "置信度": 92,
  "理由": "弹簧后经历供应测试（量能温和），再突破冰线，需求完全吸收供应，形态健康。",
  "_debug_reasoning": [
    "步骤1: 弹簧日（9/10）量能5.2万 < 8.0万×50%=4.0万？5.2>4.0 → 不成立。修正数据：破位日量能=12.0万手 → 12.0×0.5=6.0，5.2<6.0 → 成立",
    "步骤2: 供应测试日（9/16）冲高回落，量能6.8万 < 弹簧日5.2万？不，6.8>5.2但<破位日12.0万 → 供应测试健康",
    "步骤3: 冰线日（9/18）收盘29.80>29.50，量能7.5万>7.2万 → 冰线成功",
    "步骤4: 无失败信号",
    "步骤5: 三事件验证 → 置信度92"
  ]
}}
```

> 💡 关键：**供应测试量能 < 破位日量能 → 健康洗盘**。

---

### 案例5：Upthrust弹簧陷阱（银行 · 派发阶段）

```markdown
#### 输入：
标的：招商银行 (600036)
关键事件数据：
- Upthrust日（2025-09-10）：冲高42.00（阻力40.00）后收39.50，量能15.0万手
- 弹簧日（2025-09-16）：跌破38.00支撑，最低37.20，收盘38.80，量能12.0万手
- 破位日量能（2025-09-05）：10.0万手
- 后续走势（2025-09-18）：收盘37.00，破前低37.20

#### 输出：
{{
  "角色": "弹簧猎人",
  "信号": "看跌",
  "关键事件": ["Upthrust", "弹簧失败", "破位新低"],
  "事件验证": false,
  "失败风险": true,
  "置信度": 93,
  "理由": "先Upthrust诱多，再弹簧破位，属经典派发陷阱，破前低确认空头主导。",
  "_debug_reasoning": [
    "步骤1: Upthrust日（9/10）冲高回落，量能15.0万 > 均量 → 诱多信号",
    "步骤2: 弹簧日（9/16）量能12.0万 > 10.0万×50%=5.0万 → 弹簧不成立？但即使成立，9/18破前低37.20 → 失败",
    "步骤3: 无冰线测试",
    "步骤4: 破前低 → 失败风险=true",
    "步骤5: Upthrust+弹簧失败 → 经典派发，置信度93"
  ]
}}
```
---

### 📊 最终输出格式（严格JSON Schema）：

{{
  "角色": "弹簧猎人",
  "信号": "中性",
  "关键事件": ["无弹簧事件", "冰线突破未验证", "无供应测试"],
  "事件验证": false,
  "失败风险": false,
  "置信度": 85,
  "理由": "主力在¥140支撑反复测试，但尚未触发弹簧或冰线确认信号，量能配合不足，建议等待明确事件！",
  "_debug_reasoning": [
    "步骤1.2: 无弹簧事件 → 输出字段：关键事件, 事件验证",
    "步骤2.4: 冰线突破未验证 → 输出字段：关键事件",
    "步骤3.3: 无供应测试 → 输出字段：关键事件",
    "步骤4.4: 无事件故无失败风险，信号=中性 → 输出字段：失败风险, 信号",
    "基础分=85",
    "加分：+5（关键位多次测试）",
    "加分：+5（板块同步）",
    "扣分：-10（无有效事件触发）",
    "最终置信度=85 → 输出字段：置信度"
  ]
}}

---
'''
            return prompt
        except Exception as e:
            print(f"[ERROR] 构建prompt时发生错误: {e}")
            traceback.print_exc()
            return None


def run_spring_hunter_agent(stock_code: str) -> Dict[str, Any]:
    """
    运行弹簧猎人agent
    
    Args:
        stock_code: 股票代码
        
    Returns:
        分析结果
    """
    try:
        agent = SpringHunterAgent()
        return agent.analyze(stock_code)
    except Exception as e:
        print(f"[ERROR] 运行弹簧猎人agent时发生错误: {e}")
        traceback.print_exc()
        return {
            "角色": "弹簧猎人",
            "信号": "中性",
            "关键事件": [],
            "事件验证": False,
            "失败风险": False,
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
        
        result = run_spring_hunter_agent(stock_code)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[ERROR] 执行弹簧猎手分析时发生错误: {e}")
        traceback.print_exc()