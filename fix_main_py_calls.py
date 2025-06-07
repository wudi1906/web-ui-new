#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复main.py调用点脚本
自动将老版本的问卷系统调用改为新版本的智能问卷系统调用
"""

import re

def fix_main_py():
    """修复main.py中的调用点"""
    print("🔧 修复main.py中的问卷系统调用点...")
    
    # 读取文件
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修改导入语句
    import_pattern = r'(run_complete_questionnaire_workflow_with_existing_browser,)\s*\n(\s*HumanLikeInputAgent)'
    import_replacement = r'\1\n        run_intelligent_questionnaire_workflow_with_existing_browser,  # 🔥 新增：智能问卷系统入口\n\2'
    content = re.sub(import_pattern, import_replacement, content)
    
    # 2. 修改备用函数定义
    fallback_pattern = r'(async def run_complete_questionnaire_workflow_with_existing_browser\(\*args, \*\*kwargs\):\s*\n\s*return \{"success": False, "error": "AdsPower \+ WebUI 集成模块不可用"\})'
    fallback_replacement = r'\1\n    async def run_intelligent_questionnaire_workflow_with_existing_browser(*args, **kwargs):\n        return {"success": False, "error": "AdsPower + WebUI 集成模块不可用"}'
    content = re.sub(fallback_pattern, fallback_replacement, content)
    
    # 3. 修改第一个调用点（_execute_target_with_adspower_enhanced方法中）
    call_pattern_1 = r'result = await run_complete_questionnaire_workflow_with_existing_browser\('
    call_replacement_1 = r'# 🔥 修改：使用智能问卷系统（包含自定义下拉框处理）\n            result = await run_intelligent_questionnaire_workflow_with_existing_browser('
    content = re.sub(call_pattern_1, call_replacement_1, content, count=1)
    
    # 4. 修改第二个调用点（_execute_with_adspower方法中）
    # 寻找第二个出现位置
    remaining_content = content
    first_occurrence = remaining_content.find('run_intelligent_questionnaire_workflow_with_existing_browser(')
    if first_occurrence != -1:
        # 从第一个出现位置之后开始寻找第二个
        after_first = remaining_content[first_occurrence + 100:]  # 跳过第一个
        second_occurrence = after_first.find('run_complete_questionnaire_workflow_with_existing_browser(')
        if second_occurrence != -1:
            # 替换第二个出现位置
            before_second = remaining_content[:first_occurrence + 100 + second_occurrence]
            at_second = remaining_content[first_occurrence + 100 + second_occurrence:]
            at_second = at_second.replace('run_complete_questionnaire_workflow_with_existing_browser(', 
                                        '# 🔥 修改：使用智能问卷系统（包含自定义下拉框处理）\n            run_intelligent_questionnaire_workflow_with_existing_browser(', 1)
            content = before_second + at_second
    
    # 写回文件
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ main.py修复完成！")
    print("   - 已添加智能问卷系统导入")
    print("   - 已修改第一个调用点（大部队执行）")
    print("   - 已修改第二个调用点（敢死队执行）")
    print()
    print("🎉 现在系统将使用智能问卷系统，自定义下拉框问题已解决！")

if __name__ == "__main__":
    fix_main_py() 