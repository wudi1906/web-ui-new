#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第四阶段大规模自动化系统启动脚本
提供命令行界面来执行完整的自动化答题流水线
"""

import asyncio
import argparse
import json
import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional

from phase4_mass_automation import Phase4MassAutomationSystem

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase4CommandLineInterface:
    """第四阶段命令行界面"""
    
    def __init__(self):
        self.automation_system = Phase4MassAutomationSystem()
    
    async def execute_full_pipeline(
        self, 
        questionnaire_url: str, 
        session_id: Optional[str] = None,
        target_count: int = 10,
        max_workers: int = 5
    ):
        """执行完整的自动化流水线"""
        print(f"🚀 第四阶段：大规模自动化答题系统")
        print(f"📋 问卷URL: {questionnaire_url}")
        print(f"🆔 会话ID: {session_id or '自动生成'}")
        print(f"👥 目标人数: {target_count}")
        print(f"🔧 并发数: {max_workers}")
        print("=" * 60)
        
        try:
            result = await self.automation_system.execute_full_automation_pipeline(
                questionnaire_url=questionnaire_url,
                session_id=session_id,
                target_count=target_count,
                max_workers=max_workers
            )
            
            if result.get("success"):
                print(f"🎉 第四阶段执行成功!")
                
                # 显示分析结果
                analysis_result = result.get("analysis_result", {})
                if analysis_result.get("success"):
                    profile = analysis_result.get("profile")
                    target_matches = analysis_result.get("target_matches", [])
                    
                    print(f"\n📊 问卷分析结果:")
                    print(f"  🎯 难度等级: {profile.difficulty_level if profile else '未知'}")
                    print(f"  📈 置信度: {profile.confidence_score:.2f}" if profile else "  📈 置信度: 未知")
                    print(f"  👥 目标团队: {len(target_matches)}人")
                
                # 显示自动化结果
                automation_result = result.get("automation_result", {})
                if automation_result.get("success"):
                    print(f"\n🚀 自动化执行结果:")
                    print(f"  📋 总任务数: {automation_result.get('total_tasks', 0)}")
                    print(f"  ✅ 成功任务: {automation_result.get('successful_tasks', 0)}")
                    print(f"  📈 成功率: {automation_result.get('success_rate', 0):.1%}")
                    
                    # 显示策略表现
                    report = automation_result.get("report", {})
                    strategy_performance = report.get("strategy_performance", {})
                    if strategy_performance:
                        print(f"\n💡 策略表现:")
                        for strategy, stats in strategy_performance.items():
                            print(f"    {strategy}: {stats['success']}/{stats['total']} ({stats['success_rate']:.1%})")
                
                # 显示最终建议
                final_report = result.get("final_report", {})
                recommendations = final_report.get("recommendations", [])
                if recommendations:
                    print(f"\n💡 系统建议:")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"  {i}. {rec}")
                
                return True
            else:
                error = result.get("error", "未知错误")
                print(f"❌ 第四阶段执行失败: {error}")
                
                # 显示建议
                suggestion = result.get("suggestion")
                if suggestion:
                    print(f"💡 建议: {suggestion}")
                
                return False
                
        except Exception as e:
            print(f"❌ 执行异常: {e}")
            return False
    
    async def check_prerequisites(self):
        """检查前置条件"""
        print(f"🔍 检查前置条件...")
        print("-" * 50)
        
        try:
            # 检查数据库连接
            connection = self.automation_system.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            connection.close()
            
            if result:
                print("  ✅ 数据库连接正常")
            else:
                print("  ❌ 数据库连接失败")
                return False
            
            # 检查小社会系统
            try:
                xiaoshe_client = self.automation_system.questionnaire_manager.xiaoshe_client
                personas = await xiaoshe_client.query_personas("测试查询", 1)
                print(f"  ✅ 小社会系统连接正常 (找到{len(personas)}个数字人)")
            except Exception as e:
                print(f"  ❌ 小社会系统连接失败: {e}")
                return False
            
            # 检查知识库数据
            with self.automation_system.db_manager.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM questionnaire_knowledge")
                    knowledge_count = cursor.fetchone()
                    if knowledge_count:
                        knowledge_count = knowledge_count[0]
                    else:
                        knowledge_count = 0
            
            print(f"  📊 知识库记录: {knowledge_count}条")
            if knowledge_count == 0:
                print("  ⚠️ 知识库为空，建议先运行第二阶段收集经验数据")
            
            return True
            
        except Exception as e:
            print(f"  ❌ 前置条件检查失败: {e}")
            return False
    
    def show_help(self):
        """显示帮助信息"""
        print(f"🤖 第四阶段大规模自动化系统 - 使用指南")
        print("=" * 60)
        print(f"📋 功能说明:")
        print(f"  本系统基于前三阶段的成果，实现大规模并发答题")
        print(f"  包含实时监控、智能策略选择、成功率统计等功能")
        
        print(f"\n🚀 使用方法:")
        print(f"  1. 完整自动化模式:")
        print(f"     python start_phase4_mass_automation.py \\")
        print(f"       --url <问卷URL> \\")
        print(f"       --session-id <会话ID> \\")
        print(f"       --target-count 10 \\")
        print(f"       --max-workers 5 \\")
        print(f"       --execute")
        
        print(f"  2. 前置条件检查:")
        print(f"     python start_phase4_mass_automation.py --check")
        
        print(f"  3. 测试模式:")
        print(f"     python start_phase4_mass_automation.py --test")
        
        print(f"\n⚙️ 参数说明:")
        print(f"  --url URL              问卷URL地址")
        print(f"  --session-id ID        第二阶段敢死队会话ID")
        print(f"  --target-count N       目标团队人数 (默认: 10)")
        print(f"  --max-workers N        最大并发数 (默认: 5)")
        print(f"  --execute              执行完整自动化流水线")
        print(f"  --check                检查前置条件")
        print(f"  --test                 运行测试模式")
        print(f"  --help-guide           显示帮助信息")
        
        print(f"\n💡 示例:")
        print(f"  # 基于第二阶段和第三阶段结果执行大规模自动化")
        print(f"  python start_phase4_mass_automation.py \\")
        print(f"    --url https://www.wjx.cn/vm/ml5AbmN.aspx \\")
        print(f"    --session-id task_1748395420_459dd4bc \\")
        print(f"    --target-count 10 --max-workers 5 --execute")
        
        print(f"\n📞 技术支持:")
        print(f"  如遇问题，请检查:")
        print(f"  1. 前三阶段是否已完成")
        print(f"  2. 数据库中是否有经验数据")
        print(f"  3. 小社会系统是否正常运行")
        print(f"  4. 会话ID是否正确")
        print(f"  5. 网络连接是否正常")
        
        print(f"\n🎯 流水线说明:")
        print(f"  第四阶段完整流水线包含:")
        print(f"  1. 📊 基于第三阶段分析问卷画像")
        print(f"  2. 🎯 选择最佳目标团队")
        print(f"  3. 🚀 执行大规模并发答题")
        print(f"  4. 📈 实时监控和统计")
        print(f"  5. 💾 保存结果到数据库")
        print(f"  6. 📋 生成最终分析报告")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="第四阶段大规模自动化系统")
    
    # 基本参数
    parser.add_argument("--url", type=str, help="问卷URL地址")
    parser.add_argument("--session-id", type=str, help="第二阶段敢死队会话ID")
    parser.add_argument("--target-count", type=int, default=10, help="目标团队人数 (默认: 10)")
    parser.add_argument("--max-workers", type=int, default=5, help="最大并发数 (默认: 5)")
    
    # 操作模式
    parser.add_argument("--execute", action="store_true", help="执行完整自动化流水线")
    parser.add_argument("--check", action="store_true", help="检查前置条件")
    parser.add_argument("--test", action="store_true", help="运行测试模式")
    parser.add_argument("--help-guide", action="store_true", help="显示详细帮助")
    
    args = parser.parse_args()
    
    cli = Phase4CommandLineInterface()
    
    try:
        if args.help_guide:
            cli.show_help()
            return
        
        if args.check:
            print("🔍 启动前置条件检查...")
            success = await cli.check_prerequisites()
            if success:
                print("\n✅ 前置条件检查通过，可以执行第四阶段")
            else:
                print("\n❌ 前置条件检查失败，请修复问题后重试")
            return
        
        if args.test:
            print("🧪 启动测试模式...")
            from test_phase4_mass_automation import Phase4TestSuite
            test_suite = Phase4TestSuite()
            await test_suite.run_all_tests()
            return
        
        if args.execute:
            if not args.url:
                print("❌ 执行模式需要提供问卷URL")
                print("   使用 --url <URL>")
                return
            
            success = await cli.execute_full_pipeline(
                questionnaire_url=args.url,
                session_id=args.session_id,
                target_count=args.target_count,
                max_workers=args.max_workers
            )
            
            if success:
                print("\n🎉 第四阶段大规模自动化全部完成!")
                print("📊 系统已准备好投入生产使用")
            else:
                print("\n❌ 第四阶段执行失败")
                print("🔧 请检查错误信息并修复问题")
            return
        
        # 默认显示帮助
        cli.show_help()
        
    except KeyboardInterrupt:
        print("\n⚠️ 操作被用户中断")
    except Exception as e:
        print(f"\n❌ 系统异常: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 