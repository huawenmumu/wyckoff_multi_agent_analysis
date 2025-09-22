# 股票智能分析系统 📈

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 📋 项目简介

本项目是一个基于 Python 的股票智能分析系统，专为A股市场设计，集成了威科夫分析法和AI技术，能够获取股票历史行情数据、资金流向数据，并利用AI模型对股票进行多维度分析。系统采用多专家Agent架构，每个Agent专注于不同的分析维度，最终由总参谋长Agent整合所有分析结果，输出具备可执行性的交易策略。

## 🚀 核心特性

- **威科夫多专家系统** - 6大AI专家Agent，各司其职，全面分析
- **AI智能分析** - 集成 DeepSeek AI 模型，提供专业的股票分析和投资建议
- **多维度数据分析** - 获取股票历史行情数据和资金流向数据
- **实时数据获取** - 从专业数据源获取最新市场数据
- **完整分析流程** - 从数据获取到策略输出的一站式分析
- **灵活输入输出** - 支持单个股票分析，结果保存为 JSON 格式文件

## 🏗️ 项目架构

```
.
├── wyckoff_multi_agent_analysis.py  # 威科夫多专家分析系统主入口
├── ReadMe.md                        # 项目说明文档
├── agent/                           # 威科夫专家Agent目录
│   ├── __init__.py
│   ├── phase_hunter.py              # 阶段猎手Agent - 市场阶段诊断
│   ├── volume_detective.py          # 量能侦探Agent - 量价行为分析
│   ├── target_engineer.py           # 目标工程师Agent - 因果空间测算
│   ├── strength_commander.py        # 强度指挥官Agent - 相对强度分析
│   ├── spring_hunter.py             # 弹簧猎人Agent - 微观反转信号捕捉
│   └── chief_strategist.py          # 总参谋长Agent - 综合策略决策
├── data_fetcher/                    # 数据获取模块
│   ├── __init__.py
│   └── [various fetchers]
├── ai_analyzer/                     # AI分析模块
│   ├── __init__.py
│   └── ai_analyzer.py
├── config/                          # 配置文件目录
│   └── config.yaml                  # 主配置文件
├── cache/                           # 数据缓存目录
├── ai_results/                      # AI分析结果目录
├── tests/                           # 单元测试目录
│   ├── __init__.py
│   ├── test_data_fetcher.py
│   ├── test_ai_analyzer.py
│   └── test_main.py
└── reports/                         # 分析报告存储目录
```

## 🤖 威科夫多专家系统

本系统实现了基于威科夫分析法的6大专家AI系统，每个专家Agent专注于不同的分析维度：

| 专家代号 | 职能 | 对应文件 |
|---------|------|---------|
| 阶段猎手 | 市场阶段诊断，识别主力"吸筹→拉升→派发→下跌"四阶段转换 | [phase_hunter.py](file:///Users/shijian/python/analysis/agent/phase_hunter.py) |
| 量能侦探 | 量价行为分析，识别量价背离与主力意图 | [volume_detective.py](file:///Users/shijian/python/analysis/agent/volume_detective.py) |
| 目标工程师 | 因果空间测算与盈亏比建模 | [target_engineer.py](file:///Users/shijian/python/analysis/agent/target_engineer.py) |
| 强度指挥官 | 相对强度分析，评估个股与板块轮动强度 | [strength_commander.py](file:///Users/shijian/python/analysis/agent/strength_commander.py) |
| 弹簧猎人 | 微观反转信号捕捉，识别关键事件 | [spring_hunter.py](file:///Users/shijian/python/analysis/agent/spring_hunter.py) |
| 总参谋长 | 综合策略决策，整合5位专家的独立分析报告，输出最终交易策略 | [chief_strategist.py](file:///Users/shijian/python/analysis/agent/chief_strategist.py) |

## 📖 核心模块说明

### data_fetcher（数据获取模块）

负责从各种数据源获取股票相关数据：

- `StockDataFetcher.get_stock_data(stock_code)` - 获取指定股票的历史行情数据
- `FundFlowFetcher.stock_individual_fund_flow(stock_code)` - 获取指定股票的资金流向数据
- `StockCodeConverter.convert(code)` - 将股票代码转换为带市场前缀的格式

### ai_analyzer（AI分析模块）

负责调用AI模型进行股票分析：

- `askDeepSeek(stock_df, stock_fund_flow_df, stock_code, prompt_content)` - 调用 DeepSeek AI 对股票数据进行深度分析

### 主要执行脚本

- [wyckoff_multi_agent_analysis.py](file:///Users/shijian/python/analysis/wyckoff_multi_agent_analysis.py) - 威科夫多专家分析系统主入口

## 🛠️ 使用方法

### 威科夫多专家分析

```bash
python3 wyckoff_multi_agent_analysis.py
```

执行后按提示输入6位股票代码（例如：002050），系统将自动调用6大专家Agent进行分析，并由总参谋长Agent生成综合策略。

分析过程会依次显示每个专家的分析结果，并在最后输出总参谋长的综合策略。所有分析结果将保存为JSON文件，文件名包含股票代码和时间戳。

## ⚙️ 配置文件

项目使用 [config/config.yaml](file:///Users/shijian/python/analysis/config/config.yaml) 作为主要配置文件，包含以下配置项：

- DeepSeek API 密钥
- 默认分析的股票列表
- 并发线程数设置
- 其他系统参数

## 📦 输出结果

分析结果会保存在以下目录中：

- `reports/` - 详细分析报告（JSON格式）
- `ai_results/` - AI分析结果
- 控制台输出 - 简要分析结果和进度信息

每个分析结果文件都包含完整的分析过程和最终策略建议，便于后续研究和验证。

## 🧪 单元测试

项目包含完整的单元测试，确保代码质量和功能正确性：

```bash
# 运行所有测试
python3 -m unittest discover tests/

# 运行特定测试文件
python3 -m unittest tests.test_data_fetcher
```

## 📄 许可证

本项目采用 MIT 许可证，详情请见 [LICENSE](LICENSE) 文件。