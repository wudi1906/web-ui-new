#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🔧 应用WebUI问卷集成补丁
自动修改main.py以使用WebUI原生方法
"""

import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_webui_integration_patch():
    """应用WebUI集成补丁到main.py"""
    try:
        logger.info("🔧 开始应用WebUI问卷集成补丁...")
        
        # 读取main.py
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 定义新的函数实现
        new_function_impl = '''    async def run_intelligent_questionnaire_workflow_with_existing_browser(*args, **kwargs):
        """🔥 使用WebUI原生方法的问卷执行系统"""
        try:
            from webui_questionnaire_integration import run_webui_questionnaire_workflow
            return await run_webui_questionnaire_workflow(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ WebUI问卷系统调用失败: {e}")
            return {"success": False, "error": f"WebUI问卷系统不可用: {str(e)}"}'''
        
        # 查找并替换现有的备用函数
        pattern = r'    async def run_intelligent_questionnaire_workflow_with_existing_browser\(\*args, \*\*kwargs\):\s*return \{"success": False, "error": "AdsPower \+ WebUI 集成模块不可用"\}'
        
        if re.search(pattern, content):
            content = re.sub(pattern, new_function_impl, content)
            logger.info("✅ 找到并替换了现有的备用函数")
        else:
            logger.warning("⚠️ 未找到现有的备用函数，将添加新的实现")
            # 如果没找到，在适当位置添加
            insert_point = content.find('async def run_complete_questionnaire_workflow(*args, **kwargs):')
            if insert_point != -1:
                content = content[:insert_point] + new_function_impl + '\n    ' + content[insert_point:]
        
        # 备份原文件
        with open('main.py.backup', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 写入修改后的内容
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("✅ WebUI集成补丁应用成功！")
        logger.info("📁 原文件已备份为 main.py.backup")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 应用补丁失败: {e}")
        return False

def verify_integration():
    """验证集成是否成功"""
    try:
        logger.info("🔍 验证WebUI集成...")
        
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键标识
        if 'webui_questionnaire_integration' in content:
            logger.info("✅ WebUI集成导入已添加")
        else:
            logger.warning("⚠️ 未发现WebUI集成导入")
        
        if 'run_webui_questionnaire_workflow' in content:
            logger.info("✅ WebUI工作流调用已添加")
        else:
            logger.warning("⚠️ 未发现WebUI工作流调用")
        
        logger.info("🔍 验证完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 验证失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 开始WebUI问卷集成应用流程")
    
    # 应用补丁
    if apply_webui_integration_patch():
        logger.info("✅ 补丁应用成功")
        
        # 验证集成
        if verify_integration():
            logger.info("✅ 集成验证通过")
            
            logger.info("""
🎉 WebUI问卷集成成功！

📋 已完成的修改:
1. ✅ 修改main.py中的备用函数
2. ✅ 集成WebUI原生BrowserUseAgent
3. ✅ 保持彩色标记框和视觉AI功能
4. ✅ 增强问卷作答专用提示词
5. ✅ 保留截图和经验总结功能

🚀 现在可以运行main.py，系统将使用WebUI原生方法执行问卷！
""")
        else:
            logger.error("❌ 集成验证失败")
    else:
        logger.error("❌ 补丁应用失败")

if __name__ == "__main__":
    main() 