#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第二阶段敢死队系统启动脚本
提供命令行界面来启动和管理敢死队任务
"""

import asyncio
import argparse
import json
import sys
import logging
from datetime import datetime

from phase2_scout_automation import ScoutAutomationSystem

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase2CommandLineInterface:
    """第二阶段命令行界面"""
    
    def __init__(self):
        self.scout_system = ScoutAutomationSystem()
        self.current_task_id = None
    
    async def start_scout_mission(self, url: str, scout_count: int = 2):
        """启动敢死队任务"""
        print(f"🚀 启动敢死队任务")
        print(f"📋 问卷URL: {url}")
        print(f"👥 敢死队人数: {scout_count}")
        print("-" * 50)
        
        try:
            task_id = await self.scout_system.start_scout_mission(url, scout_count)
            
            if task_id:
                self.current_task_id = task_id
                print(f"✅ 敢死队任务启动成功!")
                print(f"🆔 任务ID: {task_id}")
                print(f"👥 敢死队成员: {len(self.scout_system.scout_sessions)}人")
                
                # 显示敢死队成员信息
                print(f"\n👤 敢死队成员列表:")
                for i, (persona_id, session_info) in enumerate(self.scout_system.scout_sessions.items(), 1):
                    assignment = session_info["assignment"]
                    browser = session_info["browser"]
                    print(f"  {i}. {assignment.persona_name} (ID: {persona_id})")
                    print(f"     🌐 浏览器: {browser['name']}")
                    print(f"     🔌 端口: {browser.get('port', '未知')}")
                
                return task_id
            else:
                print("❌ 敢死队任务启动失败")
                return None
                
        except Exception as e:
            print(f"❌ 启动异常: {e}")
            return None
    
    async def execute_scout_answering(self, task_id: str = None):
        """执行敢死队答题"""
        if not task_id:
            task_id = self.current_task_id
        
        if not task_id:
            print("❌ 没有活跃的任务ID")
            return None
        
        print(f"🎯 执行敢死队答题")
        print(f"🆔 任务ID: {task_id}")
        print("-" * 50)
        
        try:
            results = await self.scout_system.execute_scout_answering(task_id)
            
            if results and "error" not in results:
                print(f"✅ 敢死队答题完成!")
                print(f"📊 答题统计:")
                print(f"  - 成功: {results.get('success_count', 0)}人")
                print(f"  - 失败: {results.get('failure_count', 0)}人")
                print(f"  - 经验收集: {len(results.get('experiences', []))}条")
                
                # 显示详细结果
                print(f"\n📝 详细结果:")
                for scout_result in results.get("scout_results", []):
                    persona_name = scout_result.get("persona_name", "未知")
                    success = scout_result.get("success", False)
                    answers = scout_result.get("answers", [])
                    error_msg = scout_result.get("error_message", "")
                    
                    status = "✅ 成功" if success else f"❌ 失败: {error_msg}"
                    print(f"  👤 {persona_name}: {status}")
                    print(f"     📝 回答了 {len(answers)} 个问题")
                
                return results
            else:
                error_msg = results.get("error", "答题执行失败") if results else "答题执行失败"
                print(f"❌ 答题失败: {error_msg}")
                return None
                
        except Exception as e:
            print(f"❌ 答题异常: {e}")
            return None
    
    async def analyze_scout_results(self, task_id: str = None):
        """分析敢死队结果"""
        if not task_id:
            task_id = self.current_task_id
        
        if not task_id:
            print("❌ 没有活跃的任务ID")
            return None
        
        print(f"📈 分析敢死队结果")
        print(f"🆔 任务ID: {task_id}")
        print("-" * 50)
        
        try:
            analysis = await self.scout_system.analyze_scout_results(task_id)
            
            if analysis:
                print(f"✅ 敢死队结果分析完成!")
                
                # 显示分析结果
                print(f"\n📊 分析结果:")
                
                if "target_demographics" in analysis:
                    demographics = analysis["target_demographics"]
                    print(f"🎯 目标人群特征:")
                    for key, value in demographics.items():
                        print(f"  - {key}: {value}")
                
                if "success_patterns" in analysis:
                    patterns = analysis["success_patterns"]
                    print(f"\n✅ 成功模式 ({len(patterns)}个):")
                    for i, pattern in enumerate(patterns[:3], 1):  # 只显示前3个
                        print(f"  {i}. {pattern}")
                
                if "failure_patterns" in analysis:
                    failures = analysis["failure_patterns"]
                    print(f"\n❌ 失败模式 ({len(failures)}个):")
                    for i, failure in enumerate(failures[:3], 1):  # 只显示前3个
                        print(f"  {i}. {failure}")
                
                if "persona_query" in analysis:
                    query = analysis["persona_query"]
                    print(f"\n🔍 推荐数字人查询:")
                    print(f"  {query}")
                
                return analysis
            else:
                print("❌ 分析失败")
                return None
                
        except Exception as e:
            print(f"❌ 分析异常: {e}")
            return None
    
    async def cleanup_resources(self):
        """清理资源"""
        print(f"🧹 清理任务资源")
        print("-" * 50)
        
        try:
            await self.scout_system.cleanup_scout_mission()
            self.current_task_id = None
            print(f"✅ 资源清理完成")
        except Exception as e:
            print(f"❌ 清理异常: {e}")
    
    async def run_full_mission(self, url: str, scout_count: int = 2):
        """运行完整的敢死队任务"""
        print(f"🎯 运行完整敢死队任务")
        print(f"📋 问卷URL: {url}")
        print(f"👥 敢死队人数: {scout_count}")
        print("=" * 60)
        
        try:
            # 1. 启动任务
            print(f"\n📍 阶段1: 启动敢死队任务")
            task_id = await self.start_scout_mission(url, scout_count)
            if not task_id:
                return False
            
            # 2. 执行答题
            print(f"\n📍 阶段2: 执行敢死队答题")
            results = await self.execute_scout_answering(task_id)
            if not results:
                return False
            
            # 3. 分析结果
            print(f"\n📍 阶段3: 分析敢死队结果")
            analysis = await self.analyze_scout_results(task_id)
            if not analysis:
                return False
            
            # 4. 清理资源
            print(f"\n📍 阶段4: 清理任务资源")
            await self.cleanup_resources()
            
            print(f"\n🎉 完整敢死队任务执行成功!")
            print(f"📊 任务总结:")
            print(f"  - 任务ID: {task_id}")
            print(f"  - 成功答题: {results.get('success_count', 0)}人")
            print(f"  - 收集经验: {len(results.get('experiences', []))}条")
            print(f"  - 分析完成: {'是' if analysis else '否'}")
            
            return True
            
        except Exception as e:
            print(f"❌ 完整任务执行异常: {e}")
            await self.cleanup_resources()
            return False
    
    def show_help(self):
        """显示帮助信息"""
        print(f"🤖 第二阶段敢死队系统 - 使用指南")
        print("=" * 60)
        print(f"📋 功能说明:")
        print(f"  本系统实现敢死队自动答题、经验收集和分析功能")
        print(f"  通过2人敢死队试探问卷，收集成功/失败经验")
        print(f"  为后续精准投放提供数据支持")
        
        print(f"\n🚀 使用方法:")
        print(f"  1. 完整任务模式:")
        print(f"     python start_phase2_scout_system.py --url <问卷URL> --full")
        
        print(f"  2. 分步执行模式:")
        print(f"     python start_phase2_scout_system.py --url <问卷URL> --start")
        print(f"     python start_phase2_scout_system.py --execute")
        print(f"     python start_phase2_scout_system.py --analyze")
        print(f"     python start_phase2_scout_system.py --cleanup")
        
        print(f"  3. 测试模式:")
        print(f"     python start_phase2_scout_system.py --test")
        
        print(f"\n⚙️ 参数说明:")
        print(f"  --url URL          问卷URL地址")
        print(f"  --scouts N         敢死队人数 (默认: 2)")
        print(f"  --full             运行完整任务流程")
        print(f"  --start            启动敢死队任务")
        print(f"  --execute          执行敢死队答题")
        print(f"  --analyze          分析敢死队结果")
        print(f"  --cleanup          清理任务资源")
        print(f"  --test             运行测试模式")
        print(f"  --help             显示帮助信息")
        
        print(f"\n💡 示例:")
        print(f"  # 运行完整敢死队任务")
        print(f"  python start_phase2_scout_system.py \\")
        print(f"    --url https://www.wjx.cn/vm/ml5AbmN.aspx \\")
        print(f"    --scouts 2 --full")
        
        print(f"\n📞 技术支持:")
        print(f"  如遇问题，请检查:")
        print(f"  1. 数据库连接是否正常")
        print(f"  2. AdsPower是否启动")
        print(f"  3. 青果代理是否配置正确")
        print(f"  4. Browser-use是否安装")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="第二阶段敢死队系统")
    
    # 基本参数
    parser.add_argument("--url", type=str, help="问卷URL地址")
    parser.add_argument("--scouts", type=int, default=2, help="敢死队人数 (默认: 2)")
    
    # 操作模式
    parser.add_argument("--full", action="store_true", help="运行完整任务流程")
    parser.add_argument("--start", action="store_true", help="启动敢死队任务")
    parser.add_argument("--execute", action="store_true", help="执行敢死队答题")
    parser.add_argument("--analyze", action="store_true", help="分析敢死队结果")
    parser.add_argument("--cleanup", action="store_true", help="清理任务资源")
    parser.add_argument("--test", action="store_true", help="运行测试模式")
    parser.add_argument("--help-guide", action="store_true", help="显示详细帮助")
    
    args = parser.parse_args()
    
    cli = Phase2CommandLineInterface()
    
    try:
        if args.help_guide:
            cli.show_help()
            return
        
        if args.test:
            print("🧪 启动测试模式...")
            from test_phase2_scout_system import Phase2TestSuite
            test_suite = Phase2TestSuite()
            await test_suite.run_all_tests()
            return
        
        if args.full:
            if not args.url:
                print("❌ 完整任务模式需要提供问卷URL (--url)")
                return
            
            success = await cli.run_full_mission(args.url, args.scouts)
            if success:
                print("\n🎉 敢死队任务全部完成!")
            else:
                print("\n❌ 敢死队任务执行失败")
            return
        
        if args.start:
            if not args.url:
                print("❌ 启动任务需要提供问卷URL (--url)")
                return
            
            task_id = await cli.start_scout_mission(args.url, args.scouts)
            if task_id:
                print(f"\n💾 任务ID已保存，可使用以下命令继续:")
                print(f"python start_phase2_scout_system.py --execute")
            return
        
        if args.execute:
            results = await cli.execute_scout_answering()
            if results:
                print(f"\n💾 答题完成，可使用以下命令分析:")
                print(f"python start_phase2_scout_system.py --analyze")
            return
        
        if args.analyze:
            analysis = await cli.analyze_scout_results()
            if analysis:
                print(f"\n💾 分析完成，可使用以下命令清理:")
                print(f"python start_phase2_scout_system.py --cleanup")
            return
        
        if args.cleanup:
            await cli.cleanup_resources()
            print(f"\n✅ 资源清理完成")
            return
        
        # 默认显示帮助
        cli.show_help()
        
    except KeyboardInterrupt:
        print("\n⚠️ 操作被用户中断")
        await cli.cleanup_resources()
    except Exception as e:
        print(f"\n❌ 系统异常: {e}")
        await cli.cleanup_resources()

if __name__ == "__main__":
    asyncio.run(main()) 