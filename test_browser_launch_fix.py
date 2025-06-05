#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试浏览器启动和导航修复效果
验证：
1. launch_args参数格式修复
2. 浏览器成功启动 
3. 强制导航到问卷URL
4. 窗口位置正确设置
"""

import asyncio
import logging
from intelligent_three_stage_core import ThreeStageIntelligentCore

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_browser_launch_and_navigation():
    """测试浏览器启动和导航修复"""
    
    print("=" * 80)
    print("🧪 测试浏览器启动和导航修复效果")
    print("=" * 80)
    
    try:
        # 1. 初始化三阶段智能核心
        core = ThreeStageIntelligentCore()
        logger.info("✅ 三阶段智能核心初始化成功")
        
        # 2. 测试参数
        questionnaire_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"
        scout_count = 1  # 只测试1个敢死队成员
        target_count = 1  # 只测试1个大部队成员
        
        print(f"\n📋 测试参数:")
        print(f"   问卷URL: {questionnaire_url}")
        print(f"   敢死队: {scout_count} 人")
        print(f"   大部队: {target_count} 人")
        
        # 3. 执行完整三阶段工作流
        print(f"\n🚀 开始执行三阶段智能工作流...")
        print(f"⚠️ 重点观察：")
        print(f"   1. AdsPower浏览器是否成功启动（launch_args修复）")
        print(f"   2. 浏览器是否正确导航到问卷URL（不再是空白页）")
        print(f"   3. 窗口位置是否正确设置（20窗口平铺布局）")
        print(f"   4. 是否开始实际的答题流程")
        
        result = await core.execute_complete_three_stage_workflow(
            questionnaire_url=questionnaire_url,
            scout_count=scout_count,
            target_count=target_count
        )
        
        # 4. 分析测试结果
        print(f"\n📊 测试结果分析:")
        print(f"=" * 50)
        
        if result.get("success"):
            print(f"✅ 三阶段工作流执行成功！")
            
            # 分析敢死队阶段结果
            scout_phase = result.get("scout_phase", {})
            scout_experiences = scout_phase.get("experiences", [])
            
            if scout_experiences:
                print(f"\n🔍 敢死队阶段分析:")
                for exp in scout_experiences:
                    print(f"   敢死队成员: {exp.get('scout_name')}")
                    print(f"   执行成功: {exp.get('success')}")
                    print(f"   失败原因: {exp.get('failure_reason', '无')}")
                    print(f"   答题数量: {len(exp.get('questions_answered', []))}")
                    
                    # 🔧 关键：检查是否还有launch_args错误
                    failure_reason = exp.get('failure_reason', '')
                    if 'launch_args must be list string' in failure_reason:
                        print(f"❌ launch_args错误仍未修复！")
                    elif 'AdsPower' in failure_reason and '启动' in failure_reason:
                        print(f"⚠️ AdsPower启动仍有问题：{failure_reason}")
                    elif len(exp.get('questions_answered', [])) > 0:
                        print(f"✅ 成功开始答题流程！")
                    else:
                        print(f"⚠️ 浏览器启动但未开始答题")
            else:
                print(f"❌ 没有敢死队经验数据")
                
            # 分析分析阶段结果
            analysis_phase = result.get("analysis_phase", {})
            intelligence = analysis_phase.get("intelligence")
            
            if intelligence:
                print(f"\n🧠 分析阶段结果:")
                print(f"   分析成功: 是")
                print(f"   问卷主题: {intelligence.get('questionnaire_theme')}")
                print(f"   指导规则数量: {len(analysis_phase.get('guidance_rules', []))}")
            else:
                print(f"\n🧠 分析阶段结果:")
                print(f"   分析成功: 否（可能敢死队全部失败）")
                
            # 分析大部队阶段结果
            target_phase = result.get("target_phase", {})
            if target_phase.get("skipped"):
                print(f"\n🎯 大部队阶段结果:")
                print(f"   执行状态: 已跳过")
                print(f"   跳过原因: {target_phase.get('skip_reason')}")
            else:
                print(f"\n🎯 大部队阶段结果:")
                print(f"   执行状态: 已执行")
                print(f"   成功数量: {target_phase.get('success_count')}")
                print(f"   总数量: {target_phase.get('total_count')}")
                
        else:
            print(f"❌ 三阶段工作流执行失败")
            print(f"   错误信息: {result.get('error', '未知错误')}")
            
            # 检查是否是launch_args相关错误
            error_msg = result.get('error', '')
            if 'launch_args must be list string' in error_msg:
                print(f"\n🚨 关键问题：launch_args格式错误仍未修复！")
                print(f"   需要进一步检查enhanced_adspower_lifecycle.py中的修复")
            elif '浏览器启动失败' in error_msg:
                print(f"\n🚨 关键问题：浏览器启动失败")
                print(f"   可能需要检查AdsPower服务状态")
            else:
                print(f"\n⚠️ 其他错误，需要进一步调查")
        
        # 5. 总结和建议
        print(f"\n💡 测试总结和建议:")
        print(f"=" * 50)
        
        if result.get("success"):
            print(f"✅ 修复效果良好，系统可以正常运行")
            print(f"✅ 建议进行更大规模的测试（增加敢死队和大部队数量）")
        else:
            print(f"⚠️ 仍有问题需要解决：")
            error_msg = str(result.get('error', ''))
            
            if 'launch_args' in error_msg:
                print(f"   🔧 修复launch_args参数格式（字符串 vs 列表）")
            if '导航' in error_msg or 'URL' in error_msg:
                print(f"   🔧 检查browser_context的导航方法")
            if 'AdsPower' in error_msg:
                print(f"   🔧 确保AdsPower服务正常运行")
            if 'API' in error_msg or '配额' in error_msg:
                print(f"   🔧 检查Gemini API配额或使用本地化策略")
                
            print(f"   🔧 详细错误信息: {error_msg}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 测试执行失败: {e}")
        print(f"\n❌ 测试执行失败: {e}")
        return None

async def main():
    """主函数"""
    print("🧪 开始测试浏览器启动和导航修复...")
    
    result = await test_browser_launch_and_navigation()
    
    if result:
        print(f"\n✅ 测试完成")
    else:
        print(f"\n❌ 测试失败")
    
    print(f"\n📝 测试重点：")
    print(f"   1. 查看日志中是否还有 'launch_args must be list string' 错误")
    print(f"   2. 查看是否成功导航到问卷URL而不是空白页")
    print(f"   3. 查看是否开始了实际的答题流程")
    print(f"   4. 查看窗口是否按384×270尺寸正确定位")

if __name__ == "__main__":
    asyncio.run(main()) 