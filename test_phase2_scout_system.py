#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第二阶段敢死队系统测试脚本
测试敢死队自动答题、经验收集和分析功能
"""

import asyncio
import json
import time
import logging
from datetime import datetime

# 导入第二阶段模块
from phase2_scout_automation import ScoutAutomationSystem
from questionnaire_system import DatabaseManager, DB_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase2TestSuite:
    """第二阶段测试套件"""
    
    def __init__(self):
        self.scout_system = ScoutAutomationSystem()
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.test_results = {
            "start_time": datetime.now(),
            "tests": [],
            "success_count": 0,
            "failure_count": 0
        }
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 第二阶段敢死队系统测试")
        print("="*60)
        print("🎯 测试目标：验证敢死队自动答题和经验收集功能")
        print("="*60)
        
        # 测试列表
        tests = [
            ("数据库连接测试", self.test_database_connection),
            ("敢死队任务启动测试", self.test_scout_mission_startup),
            ("敢死队答题执行测试", self.test_scout_answering_execution),
            ("经验分析测试", self.test_experience_analysis),
            ("资源清理测试", self.test_resource_cleanup),
            ("完整流程集成测试", self.test_full_integration)
        ]
        
        for test_name, test_func in tests:
            await self.run_single_test(test_name, test_func)
        
        # 输出测试总结
        self.print_test_summary()
    
    async def run_single_test(self, test_name: str, test_func):
        """运行单个测试"""
        print(f"\n🔍 {test_name}")
        print("-" * 50)
        
        start_time = time.time()
        success = False
        error_message = None
        
        try:
            result = await test_func()
            success = result.get("success", False)
            error_message = result.get("error", None)
            
            if success:
                print(f"✅ {test_name} - 通过")
                self.test_results["success_count"] += 1
            else:
                print(f"❌ {test_name} - 失败: {error_message}")
                self.test_results["failure_count"] += 1
                
        except Exception as e:
            success = False
            error_message = str(e)
            print(f"❌ {test_name} - 异常: {error_message}")
            self.test_results["failure_count"] += 1
        
        duration = time.time() - start_time
        
        self.test_results["tests"].append({
            "name": test_name,
            "success": success,
            "duration": duration,
            "error": error_message
        })
    
    async def test_database_connection(self) -> dict:
        """测试数据库连接"""
        try:
            # 测试数据库连接
            connection = self.db_manager.get_connection()
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            connection.close()
            
            if result:
                print("  📊 数据库连接正常")
                
                # 测试知识库表是否存在
                self.db_manager.init_knowledge_base_tables()
                print("  📋 知识库表初始化完成")
                
                return {"success": True}
            else:
                return {"success": False, "error": "数据库查询失败"}
                
        except Exception as e:
            return {"success": False, "error": f"数据库连接失败: {e}"}
    
    async def test_scout_mission_startup(self) -> dict:
        """测试敢死队任务启动"""
        try:
            print("  🚀 启动敢死队任务...")
            
            # 使用测试问卷URL
            test_url = "https://www.wjx.cn/vm/test_questionnaire.aspx"
            
            task_id = await self.scout_system.start_scout_mission(
                questionnaire_url=test_url,
                scout_count=2
            )
            
            if task_id:
                print(f"  ✅ 任务创建成功: {task_id}")
                print(f"  👥 敢死队成员数量: {len(self.scout_system.scout_sessions)}")
                
                # 验证任务状态
                if self.scout_system.current_task:
                    print(f"  📋 当前任务URL: {self.scout_system.current_task.url}")
                    print(f"  🆔 会话ID: {self.scout_system.current_task.session_id}")
                    
                return {"success": True, "task_id": task_id}
            else:
                return {"success": False, "error": "任务创建失败"}
                
        except Exception as e:
            return {"success": False, "error": f"任务启动异常: {e}"}
    
    async def test_scout_answering_execution(self) -> dict:
        """测试敢死队答题执行"""
        try:
            if not self.scout_system.current_task:
                return {"success": False, "error": "没有活跃的任务"}
            
            print("  🎯 执行敢死队答题...")
            
            task_id = self.scout_system.current_task.task_id
            results = await self.scout_system.execute_scout_answering(task_id)
            
            if results and "error" not in results:
                print(f"  📊 答题结果:")
                print(f"    - 成功: {results.get('success_count', 0)}")
                print(f"    - 失败: {results.get('failure_count', 0)}")
                print(f"    - 经验数量: {len(results.get('experiences', []))}")
                
                # 检查敢死队结果
                scout_results = results.get("scout_results", [])
                for scout_result in scout_results:
                    persona_name = scout_result.get("persona_name", "未知")
                    success = scout_result.get("success", False)
                    answers_count = len(scout_result.get("answers", []))
                    print(f"    - {persona_name}: {'成功' if success else '失败'} ({answers_count}个答案)")
                
                return {"success": True, "results": results}
            else:
                error_msg = results.get("error", "答题执行失败") if results else "答题执行失败"
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"答题执行异常: {e}"}
    
    async def test_experience_analysis(self) -> dict:
        """测试经验分析"""
        try:
            if not self.scout_system.current_task:
                return {"success": False, "error": "没有活跃的任务"}
            
            print("  📈 分析敢死队经验...")
            
            task_id = self.scout_system.current_task.task_id
            analysis = await self.scout_system.analyze_scout_results(task_id)
            
            if analysis:
                print(f"  📊 分析结果:")
                
                # 显示分析结果的关键信息
                if "target_demographics" in analysis:
                    demographics = analysis["target_demographics"]
                    print(f"    - 目标人群特征: {demographics}")
                
                if "success_patterns" in analysis:
                    patterns = analysis["success_patterns"]
                    print(f"    - 成功模式: {len(patterns)}个")
                
                if "failure_patterns" in analysis:
                    failures = analysis["failure_patterns"]
                    print(f"    - 失败模式: {len(failures)}个")
                
                if "persona_query" in analysis:
                    query = analysis["persona_query"]
                    print(f"    - 推荐查询: {query[:100]}...")
                
                return {"success": True, "analysis": analysis}
            else:
                return {"success": False, "error": "经验分析失败"}
                
        except Exception as e:
            return {"success": False, "error": f"经验分析异常: {e}"}
    
    async def test_resource_cleanup(self) -> dict:
        """测试资源清理"""
        try:
            print("  🧹 清理测试资源...")
            
            # 记录清理前的状态
            sessions_before = len(self.scout_system.scout_sessions)
            browsers_before = len(self.scout_system.browser_system.browsers)
            
            print(f"    清理前: {sessions_before}个会话, {browsers_before}个浏览器")
            
            # 执行清理
            await self.scout_system.cleanup_scout_mission()
            
            # 检查清理后的状态
            sessions_after = len(self.scout_system.scout_sessions)
            browsers_after = len(self.scout_system.browser_system.browsers)
            
            print(f"    清理后: {sessions_after}个会话, {browsers_after}个浏览器")
            
            if sessions_after == 0 and browsers_after == 0:
                print("  ✅ 资源清理完成")
                return {"success": True}
            else:
                return {"success": False, "error": "资源清理不完整"}
                
        except Exception as e:
            return {"success": False, "error": f"资源清理异常: {e}"}
    
    async def test_full_integration(self) -> dict:
        """测试完整流程集成"""
        try:
            print("  🔄 完整流程集成测试...")
            
            # 1. 启动新任务
            test_url = "https://www.wjx.cn/vm/integration_test.aspx"
            task_id = await self.scout_system.start_scout_mission(test_url, scout_count=2)
            
            if not task_id:
                return {"success": False, "error": "任务启动失败"}
            
            print(f"    ✅ 步骤1: 任务启动成功 ({task_id})")
            
            # 2. 执行答题
            results = await self.scout_system.execute_scout_answering(task_id)
            
            if not results or "error" in results:
                return {"success": False, "error": "答题执行失败"}
            
            print(f"    ✅ 步骤2: 答题执行完成")
            
            # 3. 分析经验
            analysis = await self.scout_system.analyze_scout_results(task_id)
            
            if not analysis:
                return {"success": False, "error": "经验分析失败"}
            
            print(f"    ✅ 步骤3: 经验分析完成")
            
            # 4. 清理资源
            await self.scout_system.cleanup_scout_mission()
            print(f"    ✅ 步骤4: 资源清理完成")
            
            # 5. 验证数据持久化
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                # 检查任务记录
                cursor.execute("SELECT COUNT(*) FROM questionnaire_tasks WHERE task_id = %s", (task_id,))
                task_count = cursor.fetchone()[0]
                
                # 检查答题记录
                cursor.execute("SELECT COUNT(*) FROM answer_records WHERE task_id = %s", (task_id,))
                answer_count = cursor.fetchone()[0]
                
                # 检查知识库记录
                cursor.execute("SELECT COUNT(*) FROM questionnaire_knowledge WHERE session_id = %s", 
                             (self.scout_system.current_task.session_id if self.scout_system.current_task else "",))
                knowledge_count = cursor.fetchone()[0]
            
            connection.close()
            
            print(f"    📊 数据持久化验证:")
            print(f"      - 任务记录: {task_count}")
            print(f"      - 答题记录: {answer_count}")
            print(f"      - 知识库记录: {knowledge_count}")
            
            return {
                "success": True,
                "integration_data": {
                    "task_id": task_id,
                    "results": results,
                    "analysis": analysis,
                    "persistence": {
                        "tasks": task_count,
                        "answers": answer_count,
                        "knowledge": knowledge_count
                    }
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"集成测试异常: {e}"}
    
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📋 第二阶段测试总结")
        print("="*60)
        
        total_tests = len(self.test_results["tests"])
        success_count = self.test_results["success_count"]
        failure_count = self.test_results["failure_count"]
        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 测试统计:")
        print(f"  - 总测试数: {total_tests}")
        print(f"  - 成功: {success_count}")
        print(f"  - 失败: {failure_count}")
        print(f"  - 成功率: {success_rate:.1f}%")
        
        print(f"\n⏱️ 测试时间:")
        start_time = self.test_results["start_time"]
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"  - 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  - 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  - 总耗时: {duration:.1f}秒")
        
        print(f"\n📝 详细结果:")
        for test in self.test_results["tests"]:
            status = "✅" if test["success"] else "❌"
            duration = test["duration"]
            print(f"  {status} {test['name']} ({duration:.1f}s)")
            if test["error"]:
                print(f"      错误: {test['error']}")
        
        # 第二阶段完成度评估
        print(f"\n🎯 第二阶段完成度评估:")
        
        if success_rate >= 80:
            print(f"  🟢 优秀 ({success_rate:.1f}%) - 第二阶段基本完成")
            print(f"     ✅ 敢死队自动化系统运行正常")
            print(f"     ✅ 答题和经验收集功能正常")
            print(f"     ✅ 数据持久化和分析功能正常")
            print(f"     🚀 可以进入第三阶段开发")
        elif success_rate >= 60:
            print(f"  🟡 良好 ({success_rate:.1f}%) - 第二阶段部分完成")
            print(f"     ⚠️ 部分功能需要优化")
            print(f"     🔧 建议修复失败的测试后再进入下一阶段")
        else:
            print(f"  🔴 需要改进 ({success_rate:.1f}%) - 第二阶段未完成")
            print(f"     ❌ 核心功能存在问题")
            print(f"     🛠️ 需要重点修复和优化")
        
        print(f"\n💡 下一步建议:")
        if success_rate >= 80:
            print(f"  1. 🎯 开始第三阶段：知识库分析和目标团队选择")
            print(f"  2. 🔍 实现问卷特征识别和人群画像分析")
            print(f"  3. 🎭 开发智能数字人匹配算法")
            print(f"  4. 📈 实现大规模自动化答题系统")
        else:
            print(f"  1. 🔧 修复失败的测试用例")
            print(f"  2. 🌐 优化Browser-use集成")
            print(f"  3. 📊 完善数据库和知识库功能")
            print(f"  4. 🧪 重新运行测试验证")

async def main():
    """主函数"""
    print("🚀 第二阶段敢死队系统测试启动")
    
    test_suite = Phase2TestSuite()
    
    try:
        await test_suite.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试运行异常: {e}")
    finally:
        # 确保清理资源
        try:
            await test_suite.scout_system.cleanup_scout_mission()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())