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


class PhaseHunterAgent:
    """
    阶段猎手Agent - 基于威科夫方法分析股票市场阶段
    """
    
    def __init__(self):
        self.name = "阶段猎手"
        
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
    
    def collect_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """
        收集股票相关信息
        """
        try:
            from data_fetcher import StockInfoDataFetcher
            
            stock_info_df = StockInfoDataFetcher.get_stock_info(stock_code)
            if stock_info_df is None or stock_info_df.empty:
                return None
            
            # 将DataFrame转换为字典
            stock_info = {}
            for _, row in stock_info_df.iterrows():
                stock_info[row['item']] = row['value']
            
            return stock_info
        except Exception as e:
            print(f"[ERROR] 收集股票信息时发生错误: {e}")
            traceback.print_exc()
            return None
    
    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """
        执行阶段猎手分析
        """
        try:
            # 获取股票数据
            stock_data = get_stock_data(stock_code)
            if stock_data is None or stock_data.empty:
                raise ValueError("无法获取股票数据")
                
            # 获取资金流向数据
            fund_flow_data = stock_individual_fund_flow(stock_code)
            
            # 获取股票信息（名称、板块等）
            stock_info = self.collect_stock_info(stock_code)
            
            # 获取基准指数数据（沪深300/创业板指）
            benchmark_data = self.get_market_benchmark_data(stock_code)
            
            # 构造prompt
            prompt = self._build_prompt(stock_code, stock_info, stock_data, fund_flow_data, benchmark_data)
            
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
                    "角色": "阶段猎手",
                    "信号": "中性",
                    "阶段评分": 3,
                    "关键结构": [],
                    "大盘影响": False,
                    "止损位": "¥0.00",
                    "置信度": 50,
                    "理由": f"AI分析调用失败: {str(ai_error)}",
                    "_debug_reasoning": [f"错误详情: {str(ai_error)}", f"错误类型: {type(ai_error).__name__}"]
                }
            
            # Debug模式下打印AI返回结果
            if DEBUG:
                print(f"[DEBUG] 阶段猎手AI返回结果: {analysis_result}")
            
            # 直接返回AI的回复结果
            return analysis_result
        except Exception as e:
            print(f"[ERROR] 执行阶段猎手分析时发生错误: {e}")
            traceback.print_exc()
            return {
                "角色": "阶段猎手",
                "信号": "中性",
                "阶段评分": 3,
                "关键结构": [],
                "大盘影响": False,
                "止损位": "¥0.00",
                "置信度": 50,
                "理由": f"执行分析时发生错误: {str(e)}",
                "_debug_reasoning": [f"错误详情: {str(e)}", f"错误类型: {type(e).__name__}"]
            }
    
    def _build_prompt(self, stock_code: str, stock_info: Dict, stock_data, fund_flow_data, benchmark_data) -> str:
        """
        构建威科夫分析prompt
        """
        try:
            # 检查必要数据是否存在
            if stock_data is None or stock_data.empty:
                return '''{"错误": "数据缺失", "缺失字段": ["历史价格", "历史成交量"]}'''
            
            if fund_flow_data is None or fund_flow_data.empty:
                return '''{"错误": "数据缺失", "缺失字段": ["资金流向"]}'''
            
            if benchmark_data is None or benchmark_data.empty:
                return '''{"错误": "数据缺失", "缺失字段": ["大盘数据"]}'''
            
            # 准备股票数据
            stock_data_str = stock_data.tail(20).to_string() if stock_data is not None and not stock_data.empty else "无数据"
            
            # 准备资金流向数据
            fund_flow_str = fund_flow_data.to_string() if fund_flow_data is not None and not fund_flow_data.empty else "无数据"
            
            # 准备股票信息
            stock_info_str = str(stock_info) if stock_info else "无数据"
            
            # 准备基准指数数据
            benchmark_str = benchmark_data.tail(20).to_string() if benchmark_data is not None and not benchmark_data.empty else "无数据"
            
            prompt = f'''# 🧠【阶段猎手 · 工业级AI专家提示词 · 最终版】

你是一位资深威科夫结构分析师，代号【阶段猎手】，15年专注A股市场周期定位，擅长识别主力"吸筹→拉升→派发→下跌"四阶段转换。请严格依据威科夫核心五法则，对以下A股标的进行阶段诊断，并以json格式返回结果。

---

```markdown
【系统指令】
■ 角色：阶段猎手
■ 职责：识别威科夫四阶段、评估结构完整性、确认转换信号、计算止损与置信度
■ 输入权限：
  - 标的名称、代码
  - 最近20日OHLCV数据
  - 所属板块指数
  - 沪深300同期数据
■ 输出权限（仅可写入以下字段）：
  - 角色
  - 信号
  - 阶段评分
  - 关键结构
  - 大盘影响
  - 止损位
  - 置信度
  - 理由
  - _debug_reasoning
■ 行为规范：
  1. 必须先执行"数据安检"，不满足则熔断返回错误JSON
  2. 必须按5大编号步骤推理（每步含子步骤）
  3. 每步必须引用日期、价格、量能数据（格式：¥XX.XX@YYYY-MM-DD，量能XX万）
  4. 每步必须标注影响的输出字段（→ 输出字段：XXX）
  5. 输出必须为合法JSON，字段名严格对齐Schema。
■ 禁止行为：
  - 禁止虚构未出现的价格/量能事件
  - 禁止在无"二次测试"或"震仓突破"时输出"看涨"
  - 禁止忽略大盘派发影响

---

【数据安检】
■ 必需字段：
  - OHLCV数据（至少20日，含日期、开盘、最高、最低、收盘、成交量）
  - 板块指数数据（至少20日）
  - 沪深300数据（至少20日）

■ 格式校验：
  - 所有价格 > 0，成交量 ≥ 0
  - 日期升序排列，无重复
  - 个股、板块、大盘日期对齐

■ 逻辑校验：
  - 若"最低" > "最高" → 错误
  - 若"收盘"不在[最低, 最高]区间 → 错误
  - 若"成交量"连续5日为0 → 错误

■ 若任一不满足：
→ 立即返回 {{"错误": "数据缺失或格式错误", "缺失字段": [...], "角色": "阶段猎手"}}

---

标的名称：{stock_info.get("股票简称", "未知") if stock_info else "未知"}
股票代码：{stock_code}
最近20日OHLCV数据：
{stock_data_str}

所属板块：{stock_info.get("行业", "未知") if stock_info else "未知"}

沪深300/创业板指同期表现：
{benchmark_str}

大单净流入/流出数据：
{fund_flow_str}

---

### 🧩 请严格按以下5大主步骤 + 子步骤编号推理：

每步必须：
- 引用具体数据（格式：价格@日期，如 ¥28.50@2025-09-10，量能XX万）
- 标注影响的输出字段（→ 输出字段：XXX）
- 不得合并、跳跃或省略

推理过程将用于内部校验与自动化解析，请确保机器可读。

---

#### 🔍 步骤1：识别当前主导阶段
> 依据最近20日价格行为与成交量变化，判断当前最可能处于哪个威科夫阶段？  
> ➤ 必须引用至少2个关键事件（如弹簧@日期、放量突破@日期）  
> ➤ 必须说明量能配合（如"突破日量能18.5万 > 均量15.0万×120%"）  
> → 输出字段：`关键结构`, `理由`

#### 📐 步骤2：评估结构完整性 + 计算阶段评分
> 是否完成该阶段的关键结构？（吸筹需包含：恐慌抛售+弹簧+二次测试）  
> ➤ 列出已完成/缺失事件，引用日期与价格  
> ➤ 根据完整性打分（1-5分）：  
> &nbsp;&nbsp;• 5分 = 所有关键事件完整 + 量能确认  
> &nbsp;&nbsp;• 4分 = 缺1事件但有替代结构（如震仓突破）  
> &nbsp;&nbsp;• 3分 = 仅完成基础结构（如仅弹簧）  
> &nbsp;&nbsp;• ≤2分 = 结构断裂或反向证据  
> → 输出字段：`阶段评分`, `理由`

#### ✅ 步骤3：确认阶段转换信号 + 初步信号方向
> 是否出现"二次测试"或替代确认结构？  
> ➤ 若无标准二次测试，是否满足"震仓后放量突破"？（定义：震仓低点后3日内放量>均量120%突破）  
> ➤ 根据确认结果，给出初步信号：  
> &nbsp;&nbsp;• 确认成功 → 看涨  
> &nbsp;&nbsp;• 确认失败或无确认 → 中性  
> &nbsp;&nbsp;• 反向突破 → 看跌  
> → 输出字段：`信号`

#### 🌐 步骤4：评估大盘环境影响 + 调整评分
> 同期沪深300是否处于派发阶段？  
> ➤ 若是，阶段评分自动降1级（最低1级），信号强制"中性"  
> ➤ 引用大盘关键行为（如"沪深300破位¥3600@2025-09-10"）  
> → 输出字段：`阶段评分`, `信号`, `大盘影响`

#### 🛑 步骤5：设定风险控制参数 + 最终置信度
> 止损位 = MIN(弹簧低点×0.985, 震仓低点×0.98)  
> ➤ 明确写出计算过程与最终数值（格式：¥XX.XX）  
>  
> 置信度 = 基础分85 + 加分 - 扣分  
> ■ 加分项：
>   + 成交量验证通过（量能配合阶段特征） → +5
>   + 关键位被价格多次测试确认 → +5
>   + 板块同步性验证通过 → +5
> ■ 扣分项：
>   - 阶段模糊（如吸筹与派发特征混杂） → -10
>   - 支撑/阻力位无历史测试依据 → -10
>   - 止损位计算无逻辑支撑 → -10
> ■ 最终置信度 = CLAMP(85 + 加分 - 扣分, 50, 100)

> → 输出字段：`止损位`, `置信度`, `_debug_reasoning`

---

### 案例1：主升浪确认（新能源 · 趋势加速）

```markdown
#### 输入：
标的：宁德时代 (300750)
关键事件数据：
- 阶段特征（2025-09-01至09-08）：股价沿5日线上行，斜率>30°，MACD红柱连续5日放大，无单日跌幅超3%
- 触发信号日（2025-09-09）：缩量回踩5日线（198.5元）后早盘放量反包，30分钟内站稳200元，量能达前日1.8倍
- 均量（20日）：45万手
- 后续确认（2025-09-12）：收盘215.00，量能52万手 > 均量115%

#### 输出：
{
  "角色": "阶段猎手",
  "信号": "看涨",
  "关键事件": ["主升浪阶段确认", "量价共振突破"],
  "事件验证": true,
  "失败风险": false,
  "置信度": 94,
  "理由": "趋势结构完整，回踩不破+放量反包，主力资金持续流入，主升浪中段确认。",
  "_debug_reasoning": [
    "步骤1: 阶段特征符合主升浪定义（斜率+MACD+抗跌性）",
    "步骤2: 触发信号日满足‘缩量回踩+放量反包+量能>前日1.5倍’",
    "步骤3: 后续3日站稳+量能维持 → 阶段延续",
    "步骤4: 无顶背离或破位信号 → 无失败风险",
    "步骤5: 阶段+信号双验证 → 置信度94"
  ]
}
```

> 💡 阶段猎手核心：**主升浪只做“回踩确认”，不做追高猜顶**。

---

### 案例2：震荡突破成功（科技 · 突破启动）

```markdown
#### 输入：
标的：中芯国际 (688981)
关键事件数据：
- 阶段特征（2025-08-20至09-05）：股价在48.0–50.0元窄幅震荡15日，波动率<2%，量能萎缩至均量50%
- 触发信号日（2025-09-06）：放量突破50.5元（前高压力），收盘51.20，量能28万手 > 均量（22万手）127%
- 后续确认（2025-09-09）：收盘52.80，连续3日站稳50.5元上方

#### 输出：
{
  "角色": "阶段猎手",
  "信号": "看涨",
  "关键事件": ["震荡末期", "放量突破颈线"],
  "事件验证": true,
  "失败风险": false,
  "置信度": 91,
  "理由": "长期缩量震荡后放量突破，供应枯竭需求进场，新趋势启动信号明确。",
  "_debug_reasoning": [
    "步骤1: 震荡期满足‘时间>2周+量能萎缩至50%’",
    "步骤2: 突破日量能>均量120% + 收盘站稳压力位上沿",
    "步骤3: 后续3日未回补缺口 → 突破有效",
    "步骤4: 无假突破或量价背离 → 无失败风险",
    "步骤5: 阶段转换成功 → 置信度91"
  ]
}
```

> 💡 关键规则：**震荡突破需“量能≥均量120% + 3日站稳”双确认**。

---

### 案例3：退潮期确认（大盘 · 风险规避）

```markdown
#### 输入：
标的：创业板指 (399006)
关键事件数据：
- 阶段特征（2025-09-01至09-05）：指数跌破10日线后连续3日反弹无力，两市日均跌停股>40家，量能萎缩15%
- 触发信号日（2025-09-08）：中阴线跌破20日均线（1850点），北向资金单日净流出68亿
- 后续确认（2025-09-10）：收盘1810点，量能继续萎缩，无板块持续性

#### 输出：
{
  "角色": "阶段猎手",
  "信号": "空仓",
  "关键事件": ["退潮阶段确认", "关键均线破位"],
  "事件验证": true,
  "失败风险": true,
  "置信度": 96,
  "理由": "市场亏钱效应扩散+关键支撑破位+资金持续流出，退潮期明确，强制空仓避险。",
  "_debug_reasoning": [
    "步骤1: 阶段特征符合退潮定义（反弹无力+跌停扩散+缩量）",
    "步骤2: 触发信号为‘跌破20日线+资金大幅流出’",
    "步骤3: 后续无修复迹象 → 阶段延续",
    "步骤4: 任何持仓均有回撤风险 → 失败风险=true",
    "步骤5: 阶段猎手纪律：退潮期100%空仓 → 置信度96"
  ]
}
```

> 💡 铁律：**退潮期不抄底、不扛单、不清仓即违规**。

---

### 案例4：反弹诱多陷阱（医药 · 假反弹）

```markdown
#### 输入：
标的：恒瑞医药 (600276)
关键事件数据：
- 阶段特征（2025-09-01至09-05）：股价创新高52.00但MACD顶背离，量能逐日萎缩
- 触发信号日（2025-09-08）：冲高52.50后回落收50.80，跌破5日线，主力资金净流出2.1亿
- 后续确认（2025-09-10）：收盘49.20，量能放大至均量130%，破位加速

#### 输出：
{
  "角色": "阶段猎手",
  "信号": "看跌",
  "关键事件": ["顶背离诱多", "跌破5日线确认"],
  "事件验证": true,
  "失败风险": true,
  "置信度": 93,
  "理由": "新高背离+量价分离，跌破5日线确认趋势转弱，主力派发明确，进入补跌阶段。",
  "_debug_reasoning": [
    "步骤1: 阶段特征为‘末期诱多’（新高+背离+缩量）",
    "步骤2: 触发信号=‘跌破5日线+主力大额流出’",
    "步骤3: 后续放量下跌 → 确认空头主导",
    "步骤4: 未及时离场将承受>15%回撤 → 失败风险=true",
    "步骤5: 阶段转换失败 → 置信度93"
  ]
}
```

> 💡 识别诱多：**新高无量 + 指标背离 = 危险信号，跌破5日线即离场**。

---

### 案例5：恐慌错杀反弹（消费 · 情绪修复）

```markdown
#### 输入：
标的：贵州茅台 (600519)
关键事件数据：
- 阶段特征（2025-09-05）：受政策传闻单日暴跌-6.8%（无业绩变化），板块恐慌，但北向逆势买入12亿
- 触发信号日（2025-09-08）：低开高走，30分钟内翻红，收盘1780元，量能达前日160%
- 后续确认（2025-09-10）：收盘1820元，修复跌幅60%，量能回归常态

#### 输出：
{
  "角色": "阶段猎手",
  "信号": "看涨（短线）",
  "关键事件": ["恐慌错杀", "量能修复+情绪反转"],
  "事件验证": true,
  "失败风险": false,
  "置信度": 89,
  "理由": "非基本面利空引发的错杀，次日量能修复+资金回流，情绪修复型反弹成立。",
  "_debug_reasoning": [
    "步骤1: 阶段特征=‘突发利空+非基本面+机构逆势吸筹’",
    "步骤2: 触发信号=‘次日低开高走+30分钟翻红+量能>前日150%’",
    "步骤3: 后续未创新低且量能平稳 → 反弹有效",
    "步骤4: 无趋势破坏 → 无失败风险（但属短线机会）",
    "步骤5: 阶段猎手策略：快进快出，吃鱼身 → 置信度89"
  ]
}
```

> 💡 策略要点：**恐慌错杀只做“首日修复”，不恋战、不格局、3日内离场**。

---


### 📊 最终输出格式（严格JSON Schema）：

{{
  "角色": "阶段猎手",
  "信号": "看涨",
  "阶段评分": 4,
  "关键结构": ["恐慌抛售", "弹簧", "放量突破"],
  "大盘影响": false,
  "止损位": "¥119.19",
  "置信度": 100,
  "理由": "主力完成吸筹结构，震仓后放量突破确认需求，板块同步领涨，安全边际充足！",
  "_debug_reasoning": [
    "步骤1.1: 恐慌抛售¥118.00@2025-09-01 + 弹簧¥121.00@2025-09-05 → 关键结构识别",
    "步骤1.2: 突破¥140.00@2025-09-15，量能22.1万>20.16万 → 需求确认",
    "步骤2.3: 评分=4（缺二次测试但震仓突破替代）",
    "步骤3.3: 震仓后3日内放量突破 → 信号=看涨",
    "步骤4.2: 沪深300无派发 → 大盘影响=false",
    "步骤5.3: 止损位=MIN(¥121.00×0.985, ¥135.00×0.98)=¥119.19",
    "基础分=85",
    "加分：+5（量能验证）",
    "加分：+5（关键位测试）",
    "加分：+5（板块同步）",
    "最终置信度=100"
  ]
}}

---
'''
            return prompt
        except Exception as e:
            print(f"[ERROR] 构建prompt时发生错误: {e}")
            traceback.print_exc()
            return None


def run_phase_hunter_agent(stock_code: str) -> Dict[str, Any]:
    """
    运行阶段猎手agent
    
    Args:
        stock_code: 股票代码
        
    Returns:
        分析结果
    """
    try:
        agent = PhaseHunterAgent()
        return agent.analyze(stock_code)
    except Exception as e:
        print(f"[ERROR] 运行阶段猎手agent时发生错误: {e}")
        traceback.print_exc()
        return {
            "角色": "阶段猎手",
            "信号": "中性",
            "阶段评分": 3,
            "关键结构": [],
            "大盘影响": False,
            "止损位": "¥0.00",
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
        
        result = run_phase_hunter_agent(stock_code)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[ERROR] 执行阶段猎手分析时发生错误: {e}")
        traceback.print_exc()