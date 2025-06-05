#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""调试脚本：输出增强后的提示词内容"""

from adspower_browser_use_integration import AdsPowerWebUIIntegration

def debug_enhanced_prompt():
    integration = AdsPowerWebUIIntegration()
    
    test_digital_human = {
        "name": "测试长问卷",
        "age": 25,
        "job": "学生", 
        "income": "3000",
        "gender": "female"
    }
    
    enhanced_prompt = integration._generate_complete_prompt_with_human_like_input(
        test_digital_human, 
        "https://www.wjx.cn/vm/test.aspx"
    )
    
    print("=" * 80)
    print("增强后的提示词内容：")
    print("=" * 80)
    print(enhanced_prompt)
    print("=" * 80)
    
    # 检查关键词
    keywords = [
        "长问卷持续作答增强策略",
        "极限容错处理", 
        "循环执行：答题→滚动→答题",
        "💪 错误恢复策略",
        "50-100题",
        "绝不轻易放弃"
    ]
    
    print("\n关键词检查：")
    for keyword in keywords:
        found = keyword in enhanced_prompt
        status = "✅" if found else "❌"
        print(f"{status} {keyword}: {found}")

if __name__ == "__main__":
    debug_enhanced_prompt() 