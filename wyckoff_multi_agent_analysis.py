#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
威科夫多视角AI专家系统
该脚本调用agent目录中的5个专家进行分析，然后用chief_strategist进行综合分析
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.append('.')

from agent import (
    run_phase_hunter_agent,
    run_volume_detective_agent,
    run_target_engineer_agent,
    run_strength_commander_agent,
    run_spring_hunter_agent,
    run_chief_strategist_agent
)


def run_wyckoff_multi_agent_analysis(stock_code: str) -> Dict[str, Any]:
    """
    运行威科夫多视角AI专家系统分析
    
    Args:
        stock_code: 股票代码
        
    Returns:
        完整分析结果
    """
    print(f"=== 威科夫多视角AI专家系统分析开始 ===")
    print(f"股票代码: {stock_code}")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 存储所有专家的分析报告
    expert_reports = []
    
    # 1. 阶段猎手分析
    print("1. 正在运行阶段猎手分析...")
    try:
        phase_hunter_result = run_phase_hunter_agent(stock_code)
        expert_reports.append(phase_hunter_result)
        print("阶段猎手分析完成:")
        print(json.dumps(phase_hunter_result, ensure_ascii=False, indent=2))
        print()
    except Exception as e:
        print(f"阶段猎手分析出错: {e}")
        print()
    
    # 2. 量能侦探分析
    print("2. 正在运行量能侦探分析...")
    try:
        volume_detective_result = run_volume_detective_agent(stock_code)
        expert_reports.append(volume_detective_result)
        print("量能侦探分析完成:")
        print(json.dumps(volume_detective_result, ensure_ascii=False, indent=2))
        print()
    except Exception as e:
        print(f"量能侦探分析出错: {e}")
        print()

    # 3. 弹簧猎人分析
    print("3. 正在运行弹簧猎人分析...")
    try:
        spring_hunter_result = run_spring_hunter_agent(stock_code)
        expert_reports.append(spring_hunter_result)
        print("弹簧猎人分析完成:")
        print(json.dumps(spring_hunter_result, ensure_ascii=False, indent=2))
        print()
    except Exception as e:
        print(f"弹簧猎人分析出错: {e}")
        print()

    # 4. 目标工程师分析
    print("4. 正在运行目标工程师分析...")
    try:
        target_engineer_result = run_target_engineer_agent(stock_code)
        expert_reports.append(target_engineer_result)
        print("目标工程师分析完成:")
        print(json.dumps(target_engineer_result, ensure_ascii=False, indent=2))
        print()
    except Exception as e:
        print(f"目标工程师分析出错: {e}")
        print()
    
    # 5. 强度指挥官分析
    print("5. 正在运行强度指挥官分析...")
    try:
        strength_commander_result = run_strength_commander_agent(stock_code)
        expert_reports.append(strength_commander_result)
        print("强度指挥官分析完成:")
        print(json.dumps(strength_commander_result, ensure_ascii=False, indent=2))
        print()
    except Exception as e:
        print(f"强度指挥官分析出错: {e}")
        print()
    
    # 6. 总参谋长综合分析
    print("6. 正在运行总参谋长综合分析...")
    try:
        chief_strategist_result = run_chief_strategist_agent(expert_reports)
        print("总参谋长综合分析完成:")
        print(json.dumps(chief_strategist_result, ensure_ascii=False, indent=2))
        print()
    except Exception as e:
        print(f"总参谋长综合分析出错: {e}")
        chief_strategist_result = {}
        print()
    
    # 整合所有结果
    final_result = {
        "股票代码": stock_code,
        "分析时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "专家分析报告": expert_reports,
        "综合策略": chief_strategist_result
    }
    
    # 保存结果到文件
    filename = f"wyckoff_multi_agent_analysis_{stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        print(f"完整分析结果已保存到: {filename}")
    except Exception as e:
        print(f"保存分析结果到文件时出错: {e}")
    
    print("=== 威科夫多视角AI专家系统分析结束 ===")
    
    return final_result


def main():
    """
    主函数
    """
    # 获取用户输入的股票代码
    stock_symbol = input("请输入股票代码（例如：002050）: ").strip()
    
    # 验证输入的股票代码格式
    if not stock_symbol or not stock_symbol.isdigit() or len(stock_symbol) != 6:
        print("错误：请输入6位数字的股票代码")
        return
    
    # 执行分析
    result = run_wyckoff_multi_agent_analysis(stock_symbol)
    
    # 打印最终结果摘要
    print("\n=== 分析结果摘要 ===")
    if "综合策略" in result and result["综合策略"]:
        strategy = result["综合策略"]
        print(f"综合信号: {strategy.get('综合信号', 'N/A')}")
        print(f"共识强度: {strategy.get('共识强度', 'N/A')}")
        print(f"综合止损位: {strategy.get('综合止损位', 'N/A')}")
        print(f"综合目标价: {strategy.get('综合目标价', 'N/A')}")
        print(f"建议仓位: {strategy.get('建议仓位', 'N/A')}")
        print(f"最终置信度: {strategy.get('最终置信度', 'N/A')}")
    else:
        print("未能生成综合策略")


if __name__ == "__main__":
    main()