#!/usr/bin/env python3
"""
WebUI问卷系统增强功能测试
测试新的状态检测、重复防护和错误补救机制
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from webui_questionnaire_integration import run_questionnaire_with_webui

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'webui_enhanced_test_{int(datetime.now().timestamp())}.log')
    ]
)

logger = logging.getLogger(__name__)

async def test_enhanced_webui_questionnaire():
    """测试增强版WebUI问卷系统"""
    
    logger.info("🚀 开始测试增强版WebUI问卷系统")
    
    # 测试用例配置
    test_cases = [
        {
            'name': '问卷星测试 - 复杂下拉框',
            'url': 'https://www.wjx.cn/vm/ml5AbmN.aspx',
            'digital_human': {
                'name': '刘思颖',
                'age': 20,
                'gender': '男',
                'occupation': '普通职员',
                'income': 8000
            },
            'expected_improvements': [
                '避免下拉框无限循环',
                '智能状态检测防重复',
                '提交后错误检查',
                '精准错误补救'
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"📋 执行测试用例 {i}: {test_case['name']}")
        logger.info(f"🎯 预期改进: {', '.join(test_case['expected_improvements'])}")
        
        try:
            # 记录开始时间
            start_time = datetime.now()
            
            # 执行增强版问卷任务
            result = await run_questionnaire_with_webui(
                questionnaire_url=test_case['url'],
                digital_human_info=test_case['digital_human'],
                gemini_api_key="AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8",
                model_name="gemini-2.0-flash",
                max_steps=150,  # 预期步骤数应该减少
                keep_browser_open=True  # 保持浏览器打开便于观察
            )
            
            # 记录结束时间
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 分析结果
            logger.info("📊 测试结果分析:")
            logger.info(f"   ✅ 执行状态: {'成功' if result.get('success') else '失败'}")
            logger.info(f"   ⏱️ 执行时间: {execution_time:.1f}秒")
            logger.info(f"   📈 总步骤数: {result.get('total_steps', 0)}")
            
            # 效率评估
            if execution_time < 300:  # 5分钟内完成
                logger.info("   🚀 时间效率: 优秀 (预期改进达成)")
            elif execution_time < 600:  # 10分钟内完成  
                logger.info("   ⚡ 时间效率: 良好 (有改进)")
            else:
                logger.info("   ⚠️ 时间效率: 需要进一步优化")
            
            # 步骤数评估
            if result.get('total_steps', 0) < 30:
                logger.info("   📉 步骤效率: 优秀 (避免了重复循环)")
            elif result.get('total_steps', 0) < 50:
                logger.info("   📊 步骤效率: 良好 (有一定改进)")
            else:
                logger.info("   📈 步骤效率: 仍有优化空间")
            
            # 详细结果
            logger.info("📋 详细执行结果:")
            for key, value in result.items():
                if key not in ['action_history']:  # 跳过冗长的历史记录
                    logger.info(f"   {key}: {value}")
            
            # 预期改进验证
            logger.info("🔍 预期改进验证:")
            for improvement in test_case['expected_improvements']:
                logger.info(f"   - {improvement}: 需要人工观察验证")
            
            print("\n" + "="*80)
            print("🎯 增强功能验证指南:")
            print("1. 观察浏览器中的操作是否避免了重复点击")
            print("2. 检查是否有状态检测和智能跳过")
            print("3. 观察提交后是否检查了错误提示")
            print("4. 验证下拉框操作是否更加智能")
            print("="*80 + "\n")
            
        except Exception as e:
            logger.error(f"❌ 测试用例 {i} 执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info("🏁 WebUI增强功能测试完成")

def main():
    """主函数"""
    print("🔧 WebUI问卷系统增强功能测试")
    print("="*60)
    print("本测试将验证以下增强功能:")
    print("1. 🛡️ 智能状态检测防重复")
    print("2. ⚡ 循环防护机制")
    print("3. ✅ 提交后错误检查")
    print("4. 🔄 智能错误补救")
    print("5. 📦 下拉框特殊处理")
    print("="*60)
    
    # 运行测试
    asyncio.run(test_enhanced_webui_questionnaire())

if __name__ == "__main__":
    main() 