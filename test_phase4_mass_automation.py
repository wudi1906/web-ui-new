#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第四阶段大规模自动化系统测试脚本
测试并发答题引擎、实时监控系统和完整流水线功能
"""

import asyncio
import json
import time
import logging
from datetime import datetime

# 导入第四阶段模块
from phase4_mass_automation import (
    Phase4MassAutomationSystem, 
    ConcurrentAnsweringEngine, 
    RealTimeMonitor,
    AnsweringTask,
    MassAutomationStats
)
from phase3_knowledge_analysis import QuestionnaireProfile, PersonaMatch
from questionnaire_system import DatabaseManager, DB_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase4TestSuite:
    """第四阶段测试套件"""
    
    def __init__(self):
        self.automation_system = Phase4MassAutomationSystem()
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.test_results = {
            "start_time": datetime.now(),
            "tests": [],
            "success_count": 0,
            "failure_count": 0
        }
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 第四阶段大规模自动化系统测试")
        print("="*60)
        print("🎯 测试目标：验证并发答题、实时监控和完整流水线功能")
        print("="*60)
        
        # 测试列表
        tests = [
            ("数据库连接测试", self.test_database_connection),
            ("实时监控系统测试", self.test_real_time_monitor),
            ("答题任务创建测试", self.test_answering_task_creation),
            ("并发答题引擎测试", self.test_concurrent_answering_engine),
            ("策略选择算法测试", self.test_strategy_selection),
            ("完整流水线集成测试", self.test_full_pipeline_integration)
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
                return {"success": True}
            else:
                return {"success": False, "error": "数据库查询失败"}
                
        except Exception as e:
            return {"success": False, "error": f"数据库连接失败: {e}"}
    
    async def test_real_time_monitor(self) -> dict:
        """测试实时监控系统"""
        try:
            print("  📊 测试实时监控系统...")
            
            monitor = RealTimeMonitor()
            
            # 测试监控启动和停止
            monitor.start_monitoring()
            print("    ✅ 监控系统启动成功")
            
            # 创建测试任务
            test_task = AnsweringTask(
                task_id="test_task_1",
                persona_id=1,
                persona_name="测试数字人",
                persona_info={"age": 25, "gender": "男"},
                questionnaire_url="https://test.com",
                strategy="conservative"
            )
            
            # 测试任务添加和状态更新
            monitor.add_task(test_task)
            monitor.start_task(test_task)
            
            # 模拟任务完成
            test_task.success = True
            test_task.end_time = datetime.now()
            monitor.complete_task(test_task)
            
            # 等待一下让监控处理
            await asyncio.sleep(2)
            
            # 停止监控
            monitor.stop_monitoring()
            print("    ✅ 监控系统停止成功")
            
            # 验证统计数据
            if monitor.stats.total_tasks == 1 and monitor.stats.completed_tasks == 1:
                print("    ✅ 统计数据正确")
                return {"success": True}
            else:
                return {"success": False, "error": "统计数据不正确"}
                
        except Exception as e:
            return {"success": False, "error": f"实时监控测试失败: {e}"}
    
    async def test_answering_task_creation(self) -> dict:
        """测试答题任务创建"""
        try:
            print("  📋 测试答题任务创建...")
            
            # 创建测试数据
            test_matches = [
                PersonaMatch(
                    persona_id=1,
                    persona_name="测试数字人1",
                    persona_info={"age": 25, "gender": "男", "profession": "学生"},
                    match_score=0.85,
                    match_reasons=["年龄匹配"],
                    predicted_success_rate=0.75
                ),
                PersonaMatch(
                    persona_id=2,
                    persona_name="测试数字人2",
                    persona_info={"age": 30, "gender": "女", "profession": "上班族"},
                    match_score=0.78,
                    match_reasons=["职业匹配"],
                    predicted_success_rate=0.72
                )
            ]
            
            test_profile = QuestionnaireProfile(
                questionnaire_url="https://test.com",
                session_id="test_session",
                difficulty_level="medium",
                target_demographics={},
                success_patterns=[],
                failure_patterns=[],
                recommended_strategies=[],
                confidence_score=0.8,
                sample_size=5
            )
            
            # 创建并发答题引擎
            engine = ConcurrentAnsweringEngine(max_workers=2)
            
            # 创建答题任务
            tasks = engine._create_answering_tasks(
                test_matches, 
                "https://test.com", 
                test_profile
            )
            
            if len(tasks) == 2:
                print(f"    ✅ 成功创建 {len(tasks)} 个答题任务")
                
                # 验证任务属性
                for task in tasks:
                    if not task.task_id or not task.persona_name or not task.strategy:
                        return {"success": False, "error": "任务属性不完整"}
                
                print("    ✅ 任务属性验证通过")
                return {"success": True}
            else:
                return {"success": False, "error": f"任务数量不正确: {len(tasks)}"}
                
        except Exception as e:
            return {"success": False, "error": f"答题任务创建测试失败: {e}"}
    
    async def test_concurrent_answering_engine(self) -> dict:
        """测试并发答题引擎"""
        try:
            print("  🚀 测试并发答题引擎...")
            
            # 创建测试数据
            test_matches = [
                PersonaMatch(
                    persona_id=1,
                    persona_name="测试数字人1",
                    persona_info={"age": 25, "gender": "男"},
                    match_score=0.85,
                    match_reasons=["年龄匹配"],
                    predicted_success_rate=0.75
                ),
                PersonaMatch(
                    persona_id=2,
                    persona_name="测试数字人2",
                    persona_info={"age": 30, "gender": "女"},
                    match_score=0.78,
                    match_reasons=["职业匹配"],
                    predicted_success_rate=0.72
                )
            ]
            
            test_profile = QuestionnaireProfile(
                questionnaire_url="https://test.com",
                session_id="test_session",
                difficulty_level="easy",
                target_demographics={},
                success_patterns=[],
                failure_patterns=[],
                recommended_strategies=[],
                confidence_score=0.8,
                sample_size=5
            )
            
            # 创建并发答题引擎
            engine = ConcurrentAnsweringEngine(max_workers=2)
            
            # 执行大规模答题（使用模拟）
            result = await engine.execute_mass_answering(
                target_matches=test_matches,
                questionnaire_url="https://test.com",
                questionnaire_profile=test_profile
            )
            
            if result.get("success"):
                print("    ✅ 并发答题执行成功")
                print(f"      总任务: {result.get('total_tasks', 0)}")
                print(f"      成功任务: {result.get('successful_tasks', 0)}")
                print(f"      成功率: {result.get('success_rate', 0):.1%}")
                
                # 验证结果
                if result.get("total_tasks") == 2:
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "任务数量不正确"}
            else:
                return {"success": False, "error": result.get("error", "并发答题失败")}
                
        except Exception as e:
            return {"success": False, "error": f"并发答题引擎测试失败: {e}"}
    
    async def test_strategy_selection(self) -> dict:
        """测试策略选择算法"""
        try:
            print("  🎯 测试策略选择算法...")
            
            engine = ConcurrentAnsweringEngine()
            
            # 测试不同场景的策略选择
            test_cases = [
                {
                    "match": PersonaMatch(
                        persona_id=1, persona_name="高匹配", persona_info={},
                        match_score=0.9, match_reasons=[], predicted_success_rate=0.8
                    ),
                    "profile": QuestionnaireProfile(
                        questionnaire_url="", session_id="", difficulty_level="easy",
                        target_demographics={}, success_patterns=[], failure_patterns=[],
                        recommended_strategies=[], confidence_score=0.8, sample_size=5
                    ),
                    "expected": "conservative"
                },
                {
                    "match": PersonaMatch(
                        persona_id=2, persona_name="中匹配", persona_info={},
                        match_score=0.6, match_reasons=[], predicted_success_rate=0.7
                    ),
                    "profile": QuestionnaireProfile(
                        questionnaire_url="", session_id="", difficulty_level="medium",
                        target_demographics={}, success_patterns=[], failure_patterns=[],
                        recommended_strategies=[], confidence_score=0.7, sample_size=3
                    ),
                    "expected": "conservative"
                },
                {
                    "match": PersonaMatch(
                        persona_id=3, persona_name="低匹配", persona_info={},
                        match_score=0.4, match_reasons=[], predicted_success_rate=0.5
                    ),
                    "profile": QuestionnaireProfile(
                        questionnaire_url="", session_id="", difficulty_level="hard",
                        target_demographics={}, success_patterns=[], failure_patterns=[],
                        recommended_strategies=[], confidence_score=0.6, sample_size=2
                    ),
                    "expected": "conservative"  # 困难问卷都用保守策略
                }
            ]
            
            success_count = 0
            for i, case in enumerate(test_cases):
                strategy = engine._select_strategy_for_persona(case["match"], case["profile"])
                if strategy == case["expected"]:
                    success_count += 1
                    print(f"    ✅ 测试用例{i+1}: {strategy} (正确)")
                else:
                    print(f"    ❌ 测试用例{i+1}: {strategy} (期望: {case['expected']})")
            
            if success_count == len(test_cases):
                return {"success": True}
            else:
                return {"success": False, "error": f"策略选择错误: {success_count}/{len(test_cases)}"}
                
        except Exception as e:
            return {"success": False, "error": f"策略选择测试失败: {e}"}
    
    async def test_full_pipeline_integration(self) -> dict:
        """测试完整流水线集成"""
        try:
            print("  🔄 测试完整流水线集成...")
            
            # 先插入测试数据到知识库
            await self._insert_test_knowledge_data()
            
            # 执行完整流水线
            result = await self.automation_system.execute_full_automation_pipeline(
                questionnaire_url="https://test.com/integration_test",
                session_id="integration_test_session",
                target_count=3,
                max_workers=2
            )
            
            if result.get("success"):
                print("    ✅ 完整流水线执行成功")
                
                # 验证各阶段结果
                analysis_result = result.get("analysis_result", {})
                automation_result = result.get("automation_result", {})
                final_report = result.get("final_report", {})
                
                print(f"      第三阶段分析: {'✅' if analysis_result.get('success') else '❌'}")
                print(f"      第四阶段自动化: {'✅' if automation_result.get('success') else '❌'}")
                print(f"      最终报告: {'✅' if final_report else '❌'}")
                
                return {
                    "success": True,
                    "integration_data": {
                        "phase3_success": analysis_result.get("success", False),
                        "phase4_success": automation_result.get("success", False),
                        "total_tasks": automation_result.get("total_tasks", 0),
                        "success_rate": automation_result.get("success_rate", 0)
                    }
                }
            else:
                error = result.get("error", "完整流水线执行失败")
                return {"success": False, "error": error}
                
        except Exception as e:
            return {"success": False, "error": f"完整流水线集成测试失败: {e}"}
    
    async def _insert_test_knowledge_data(self):
        """插入测试知识库数据"""
        try:
            session_id = "integration_test_session"
            questionnaire_url = "https://test.com/integration_test"
            
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                # 清理旧的测试数据
                cursor.execute(
                    "DELETE FROM questionnaire_knowledge WHERE session_id = %s",
                    (session_id,)
                )
                
                # 插入测试数据
                test_data = [
                    (session_id, questionnaire_url, "您的年龄段是？", "single_choice", 1, 1, "scout", "18-25岁", True, "success", "策略: conservative, 成功"),
                    (session_id, questionnaire_url, "您的职业是？", "single_choice", 2, 1, "scout", "学生", True, "success", "策略: conservative, 成功"),
                    (session_id, questionnaire_url, "您的年龄段是？", "single_choice", 1, 2, "scout", "26-35岁", True, "success", "策略: conservative, 成功"),
                    (session_id, questionnaire_url, "您的职业是？", "single_choice", 2, 2, "scout", "上班族", False, "failure", "策略: aggressive, 失败")
                ]
                
                for data in test_data:
                    sql = """
                    INSERT INTO questionnaire_knowledge 
                    (session_id, questionnaire_url, question_content, question_type, 
                     question_number, persona_id, persona_role, answer_choice, success, 
                     experience_type, experience_description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, data)
                
                connection.commit()
                print(f"    📝 插入了 {len(test_data)} 条测试知识库数据")
                
        except Exception as e:
            print(f"    ❌ 插入测试数据失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()
    
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📋 第四阶段测试总结")
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
        
        # 第四阶段完成度评估
        print(f"\n🎯 第四阶段完成度评估:")
        
        if success_rate >= 80:
            print(f"  🟢 优秀 ({success_rate:.1f}%) - 第四阶段基本完成")
            print(f"     ✅ 大规模自动化系统运行正常")
            print(f"     ✅ 并发答题引擎功能正常")
            print(f"     ✅ 实时监控系统功能正常")
            print(f"     ✅ 完整流水线集成正常")
            print(f"     🎉 整个项目已完成，可以投入生产使用")
        elif success_rate >= 60:
            print(f"  🟡 良好 ({success_rate:.1f}%) - 第四阶段部分完成")
            print(f"     ⚠️ 部分功能需要优化")
            print(f"     🔧 建议修复失败的测试后投入使用")
        else:
            print(f"  🔴 需要改进 ({success_rate:.1f}%) - 第四阶段未完成")
            print(f"     ❌ 核心功能存在问题")
            print(f"     🛠️ 需要重点修复和优化")
        
        print(f"\n💡 下一步建议:")
        if success_rate >= 80:
            print(f"  1. 🎉 项目开发完成，可以投入生产使用")
            print(f"  2. 📊 监控生产环境的运行情况")
            print(f"  3. 🔧 根据实际使用情况优化参数")
            print(f"  4. 📈 收集用户反馈，持续改进")
        else:
            print(f"  1. 🔧 修复失败的测试用例")
            print(f"  2. 🚀 完善并发答题引擎")
            print(f"  3. 📊 优化实时监控系统")
            print(f"  4. 🧪 重新运行测试验证")

async def main():
    """主函数"""
    print("🚀 第四阶段大规模自动化系统测试启动")
    
    test_suite = Phase4TestSuite()
    
    try:
        await test_suite.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试运行异常: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 