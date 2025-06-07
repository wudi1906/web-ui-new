#!/usr/bin/env python3
"""
WebUI问卷系统增强功能测试 - 2025年版本
专门测试新的状态检测、重复防护和错误补救机制
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
    
    # 测试数字人信息
    digital_human = {
        'name': '刘思颖',
        'age': 20,
        'gender': '男',
        'occupation': '普通职员',
        'income': 8000
    }
    
    # 测试问卷URL
    questionnaire_url = 'https://www.wjx.cn/vm/ml5AbmN.aspx'
    
    logger.info(f"📋 测试配置:")
    logger.info(f"   🎭 数字人: {digital_human['name']}")
    logger.info(f"   🌐 问卷URL: {questionnaire_url}")
    logger.info(f"   🎯 重点测试: 状态检测、重复防护、错误补救")
    
    try:
        # 记录开始时间
        start_time = datetime.now()
        
        # 执行增强版问卷任务
        result = await run_questionnaire_with_webui(
            questionnaire_url=questionnaire_url,
            digital_human_info=digital_human,
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
        
        # 验证改进点
        print("\n" + "="*80)
        print("🔍 关键改进验证清单:")
        print("✅ 1. 状态检测防重复 - 观察是否避免对已答题目重复操作")
        print("✅ 2. 智能循环防护 - 检查是否避免了在同一题目上死循环")
        print("✅ 3. 提交后错误检查 - 验证提交后是否检查了错误提示")
        print("✅ 4. 精准错误补救 - 观察错误提示后是否精准定位补答")
        print("✅ 5. 下拉框特殊处理 - 检查自定义下拉框操作是否更智能")
        print("="*80)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 测试执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main():
    """主函数"""
    print("🔧 WebUI问卷系统增强功能测试 - 2025年版本")
    print("="*80)
    print("🎯 本次测试专门验证以下核心改进:")
    print("")
    print("1. 🛡️ 智能状态检测防重复")
    print("   - 每次操作前检查题目状态")
    print("   - 已答题目立即跳过")
    print("   - 避免重复作答循环")
    print("")
    print("2. ⚡ 循环防护机制")
    print("   - 连续失败自动跳过")
    print("   - 同区域操作限制")
    print("   - 智能滚动重扫描")
    print("")
    print("3. ✅ 提交后错误检查")
    print("   - 等待页面反应")
    print("   - 识别错误提示")
    print("   - 分析具体问题")
    print("")
    print("4. 🔄 智能错误补救")
    print("   - 根据提示定位题目")
    print("   - 精准补答策略")
    print("   - 重复验证直到成功")
    print("")
    print("5. 📦 下拉框特殊处理")
    print("   - 自定义组件识别")
    print("   - 多重备选策略")
    print("   - 键盘操作备选")
    print("="*80)
    
    # 运行测试
    result = asyncio.run(test_enhanced_webui_questionnaire())
    
    if result:
        print(f"\n🎉 测试完成！请观察浏览器中的操作过程以验证改进效果。")
    else:
        print(f"\n❌ 测试失败，请查看日志了解详情。")

if __name__ == "__main__":
    main() 