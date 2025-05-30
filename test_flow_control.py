#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试严格流程控制的智能问卷系统
验证：敢死队 → 等待确认 → 手动启动大部队的完整流程
"""

import asyncio
import sys
import time
sys.path.append('.')

from main import QuestionnaireSystem

async def test_strict_flow_control():
    """测试严格的流程控制"""
    print("🧪 测试严格流程控制的智能问卷系统")
    print("=" * 60)
    
    try:
        # 创建系统实例
        system = QuestionnaireSystem()
        
        print("📋 测试场景：严格阶段控制")
        print("1. 敢死队阶段 → 完成后等待确认")
        print("2. 问卷主管确认 → 手动启动大部队")
        print("3. 大部队阶段 → 完成整个流程")
        print()
        
        # 测试参数
        test_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"
        scout_count = 1
        target_count = 2
        
        print(f"🎯 测试参数:")
        print(f"   问卷URL: {test_url}")
        print(f"   敢死队数量: {scout_count}")
        print(f"   大部队数量: {target_count}")
        print()
        
        # 阶段1：启动敢死队（应该在完成后停止）
        print("🚀 阶段1：启动敢死队探索...")
        start_time = time.time()
        
        result = await system.execute_complete_workflow(
            questionnaire_url=test_url,
            scout_count=scout_count,
            target_count=target_count
        )
        
        # 验证敢死队阶段结果
        print("\n📊 敢死队阶段结果:")
        print(f"   状态: {result.get('status', '未知')}")
        print(f"   阶段: {result.get('stage', '未知')}")
        print(f"   会话ID: {result.get('session_id', '未知')}")
        print(f"   执行模式: {result.get('execution_mode', '未知')}")
        
        if result.get('status') == 'scout_completed_waiting_confirmation':
            print("✅ 敢死队阶段正确完成，等待确认")
            
            # 显示敢死队结果
            scout_phase = result.get('scout_phase', {})
            print(f"   敢死队成功率: {scout_phase.get('success_rate', 0):.1f}%")
            print(f"   成功/总数: {scout_phase.get('success_count', 0)}/{scout_phase.get('total_count', 0)}")
            
            # 显示经验分析
            guidance = result.get('guidance_analysis', {})
            print(f"   生成指导规则: {guidance.get('rules_generated', 0)} 条")
            
            session_id = result.get('session_id')
            
            # 模拟等待问卷主管确认
            print("\n⏸️ 模拟问卷主管审查结果...")
            print("   问卷主管正在查看:")
            print("   - 敢死队答题结果")
            print("   - 经验分析和指导规则")
            print("   - 确认是否启动大部队")
            
            await asyncio.sleep(2)  # 模拟审查时间
            
            # 阶段2：问卷主管确认并启动大部队
            print("\n🎯 阶段2：问卷主管确认启动大部队...")
            target_result = await system.execute_target_phase_manually(session_id)
            
            # 验证大部队阶段结果
            print("\n📊 大部队阶段结果:")
            print(f"   状态: {target_result.get('status', '未知')}")
            print(f"   阶段: {target_result.get('stage', '未知')}")
            
            if target_result.get('status') == 'completed':
                print("✅ 大部队阶段完成，整个流程成功")
                
                # 显示最终统计
                target_phase = target_result.get('target_phase', {})
                overall = target_result.get('overall', {})
                
                print(f"   大部队成功率: {target_phase.get('success_rate', 0):.1f}%")
                print(f"   总体成功率: {overall.get('success_rate', 0):.1f}%")
                print(f"   总耗时: {overall.get('duration', 0) / 60:.1f} 分钟")
                
            elif target_result.get('error'):
                print(f"❌ 大部队阶段失败: {target_result['error']}")
            else:
                print(f"⚠️ 大部队阶段状态异常: {target_result}")
                
        elif result.get('error'):
            print(f"❌ 敢死队阶段失败: {result['error']}")
            
            if "AdsPower配置文件不足" in result['error']:
                print("\n💡 解决方案:")
                print("1. 打开AdsPower客户端")
                print("2. 删除一些现有的配置文件释放配额")
                print("3. 确保至少有1个可用配置文件")
                print("4. 重新运行测试")
        else:
            print(f"⚠️ 敢死队阶段返回异常状态: {result}")
        
        total_time = time.time() - start_time
        print(f"\n⏱️ 总测试时间: {total_time:.1f} 秒")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🔧 智能问卷系统 - 严格流程控制测试")
    print()
    
    # 检查基本环境
    try:
        import questionnaire_system
        import testWenjuanFinal
        print("✅ 基本模块导入成功")
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return
    
    # 运行测试
    asyncio.run(test_strict_flow_control())

if __name__ == "__main__":
    main() 