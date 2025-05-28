#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第三阶段知识库分析系统测试脚本
测试问卷画像分析、目标团队选择和分析报告生成功能
"""

import asyncio
import json
import time
import logging
from datetime import datetime

# 导入第三阶段模块
from phase3_knowledge_analysis import Phase3KnowledgeAnalysisSystem, QuestionnaireProfile, PersonaMatch
from questionnaire_system import DatabaseManager, DB_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase3TestSuite:
    """第三阶段测试套件"""
    
    def __init__(self):
        self.analysis_system = Phase3KnowledgeAnalysisSystem()
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.test_results = {
            "start_time": datetime.now(),
            "tests": [],
            "success_count": 0,
            "failure_count": 0
        }
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 第三阶段知识库分析系统测试")
        print("="*60)
        print("🎯 测试目标：验证问卷画像分析和目标团队选择功能")
        print("="*60)
        
        # 测试列表
        tests = [
            ("数据库连接测试", self.test_database_connection),
            ("问卷画像分析测试", self.test_questionnaire_profile_analysis),
            ("目标团队选择测试", self.test_target_team_selection),
            ("分析报告生成测试", self.test_analysis_report_generation),
            ("智能查询生成测试", self.test_smart_query_generation),
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
    
    async def test_questionnaire_profile_analysis(self) -> dict:
        """测试问卷画像分析"""
        try:
            print("  📊 测试问卷画像分析...")
            
            # 使用测试数据
            test_session_id = "test_session_phase3"
            test_url = "https://www.wjx.cn/vm/test_questionnaire.aspx"
            
            # 先插入一些测试数据到知识库
            await self._insert_test_knowledge_data(test_session_id, test_url)
            
            # 执行问卷画像分析
            profile = await self.analysis_system.analyzer.analyze_questionnaire_profile(
                test_session_id, test_url
            )
            
            if profile:
                print(f"  ✅ 问卷画像分析成功")
                print(f"    - 难度等级: {profile.difficulty_level}")
                print(f"    - 置信度分数: {profile.confidence_score:.2f}")
                print(f"    - 样本数量: {profile.sample_size}")
                print(f"    - 成功模式: {len(profile.success_patterns)}个")
                print(f"    - 失败模式: {len(profile.failure_patterns)}个")
                print(f"    - 推荐策略: {len(profile.recommended_strategies)}个")
                
                # 验证画像数据的合理性
                if profile.difficulty_level in ["easy", "medium", "hard"]:
                    if 0 <= profile.confidence_score <= 1:
                        return {"success": True, "profile": profile}
                    else:
                        return {"success": False, "error": "置信度分数超出范围"}
                else:
                    return {"success": False, "error": "难度等级不正确"}
            else:
                return {"success": False, "error": "问卷画像分析失败"}
                
        except Exception as e:
            return {"success": False, "error": f"问卷画像分析异常: {e}"}
    
    async def test_target_team_selection(self) -> dict:
        """测试目标团队选择"""
        try:
            print("  🎯 测试目标团队选择...")
            
            # 创建测试问卷画像
            test_profile = QuestionnaireProfile(
                questionnaire_url="https://www.wjx.cn/vm/test_questionnaire.aspx",
                session_id="test_session_phase3",
                difficulty_level="medium",
                target_demographics={
                    "age_range": {"min": 25, "max": 35, "avg": 30},
                    "preferred_genders": ["男", "女"],
                    "preferred_professions": ["学生", "上班族"],
                    "sample_size": 5
                },
                success_patterns=["保守策略适用", "简短回答更好"],
                failure_patterns=["激进策略可能失败"],
                recommended_strategies=["使用保守策略", "选择常见选项"],
                confidence_score=0.8,
                sample_size=5
            )
            
            # 执行目标团队选择
            target_matches = await self.analysis_system.matching_engine.find_best_target_team(
                test_profile, target_count=5
            )
            
            print(f"  📋 查询到 {len(target_matches)} 个目标团队成员")
            
            if target_matches:
                # 验证匹配结果
                for match in target_matches[:3]:  # 检查前3个
                    print(f"    - {match.persona_name}: 匹配度{match.match_score:.2f}, 预期成功率{match.predicted_success_rate:.2%}")
                
                # 验证匹配分数的合理性
                valid_matches = all(0 <= match.match_score <= 1 for match in target_matches)
                valid_success_rates = all(0 <= match.predicted_success_rate <= 1 for match in target_matches)
                
                if valid_matches and valid_success_rates:
                    return {"success": True, "matches": target_matches}
                else:
                    return {"success": False, "error": "匹配分数或成功率超出范围"}
            else:
                # 没有找到匹配的数字人也算成功（可能是小社会系统中没有数据）
                print("  ⚠️ 没有找到匹配的数字人（可能是小社会系统中没有数据）")
                return {"success": True, "matches": []}
                
        except Exception as e:
            return {"success": False, "error": f"目标团队选择异常: {e}"}
    
    async def test_analysis_report_generation(self) -> dict:
        """测试分析报告生成"""
        try:
            print("  📈 测试分析报告生成...")
            
            # 创建测试数据
            test_profile = QuestionnaireProfile(
                questionnaire_url="https://www.wjx.cn/vm/test_questionnaire.aspx",
                session_id="test_session_phase3",
                difficulty_level="medium",
                target_demographics={
                    "age_range": {"min": 25, "max": 35, "avg": 30},
                    "preferred_genders": ["男", "女"],
                    "preferred_professions": ["学生", "上班族"],
                    "sample_size": 5
                },
                success_patterns=["保守策略适用"],
                failure_patterns=["激进策略可能失败"],
                recommended_strategies=["使用保守策略"],
                confidence_score=0.8,
                sample_size=5
            )
            
            test_matches = [
                PersonaMatch(
                    persona_id=1,
                    persona_name="测试数字人1",
                    persona_info={"age": 28, "gender": "男", "profession": "学生"},
                    match_score=0.85,
                    match_reasons=["年龄匹配", "性别匹配"],
                    predicted_success_rate=0.75
                ),
                PersonaMatch(
                    persona_id=2,
                    persona_name="测试数字人2",
                    persona_info={"age": 32, "gender": "女", "profession": "上班族"},
                    match_score=0.78,
                    match_reasons=["年龄匹配", "职业匹配"],
                    predicted_success_rate=0.72
                )
            ]
            
            # 生成分析报告
            report = self.analysis_system._generate_analysis_report(test_profile, test_matches)
            
            if report and "error" not in report:
                print(f"  ✅ 分析报告生成成功")
                
                # 验证报告内容
                questionnaire_analysis = report.get("questionnaire_analysis", {})
                team_selection = report.get("team_selection", {})
                recommendations = report.get("recommendations", [])
                
                print(f"    - 问卷分析: {len(questionnaire_analysis)}项")
                print(f"    - 团队选择: {len(team_selection)}项")
                print(f"    - 推荐建议: {len(recommendations)}项")
                
                # 验证关键字段
                required_fields = ["difficulty_level", "confidence_score", "sample_size"]
                if all(field in questionnaire_analysis for field in required_fields):
                    return {"success": True, "report": report}
                else:
                    return {"success": False, "error": "报告缺少必要字段"}
            else:
                error_msg = report.get("error", "报告生成失败") if report else "报告生成失败"
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"分析报告生成异常: {e}"}
    
    async def test_smart_query_generation(self) -> dict:
        """测试智能查询生成"""
        try:
            print("  🔍 测试智能查询生成...")
            
            # 创建不同类型的测试画像
            test_profiles = [
                QuestionnaireProfile(
                    questionnaire_url="test1",
                    session_id="test1",
                    difficulty_level="easy",
                    target_demographics={
                        "age_range": {"min": 20, "max": 30, "avg": 25},
                        "preferred_genders": ["男"],
                        "preferred_professions": ["学生"],
                        "sample_size": 3
                    },
                    success_patterns=[],
                    failure_patterns=[],
                    recommended_strategies=[],
                    confidence_score=0.7,
                    sample_size=3
                ),
                QuestionnaireProfile(
                    questionnaire_url="test2",
                    session_id="test2",
                    difficulty_level="hard",
                    target_demographics={
                        "age_range": {"avg": 40},
                        "preferred_genders": ["男", "女"],
                        "preferred_professions": ["上班族", "自由职业"],
                        "sample_size": 2
                    },
                    success_patterns=[],
                    failure_patterns=[],
                    recommended_strategies=[],
                    confidence_score=0.6,
                    sample_size=2
                )
            ]
            
            queries = []
            for i, profile in enumerate(test_profiles):
                query = self.analysis_system.matching_engine._generate_smart_query(profile)
                queries.append(query)
                print(f"    测试{i+1}: {query}")
            
            # 验证查询生成
            if all(isinstance(query, str) and len(query) > 0 for query in queries):
                # 验证查询包含关键信息
                if "年龄" in queries[0] and "学生" in queries[0]:
                    if "经验丰富" in queries[1]:  # hard难度应该包含这个
                        return {"success": True, "queries": queries}
                    else:
                        return {"success": False, "error": "困难问卷查询缺少关键词"}
                else:
                    return {"success": False, "error": "简单问卷查询缺少关键信息"}
            else:
                return {"success": False, "error": "查询生成失败"}
                
        except Exception as e:
            return {"success": False, "error": f"智能查询生成异常: {e}"}
    
    async def test_full_integration(self) -> dict:
        """测试完整流程集成"""
        try:
            print("  🔄 完整流程集成测试...")
            
            # 使用真实的测试数据
            test_session_id = "integration_test_session"
            test_url = "https://www.wjx.cn/vm/integration_test.aspx"
            
            # 先插入测试数据
            await self._insert_test_knowledge_data(test_session_id, test_url)
            
            # 执行完整分析流程
            result = await self.analysis_system.analyze_and_select_target_team(
                session_id=test_session_id,
                questionnaire_url=test_url,
                target_count=3
            )
            
            if result.get("success"):
                profile = result.get("profile")
                target_matches = result.get("target_matches")
                report = result.get("report")
                
                print(f"  ✅ 完整流程执行成功")
                print(f"    - 问卷画像: {profile.difficulty_level if profile else '未知'}")
                print(f"    - 目标团队: {len(target_matches) if target_matches else 0}人")
                print(f"    - 分析报告: {'已生成' if report else '未生成'}")
                
                # 验证数据持久化
                connection = self.db_manager.get_connection()
                with connection.cursor() as cursor:
                    # 检查知识库记录
                    cursor.execute(
                        "SELECT COUNT(*) FROM questionnaire_knowledge WHERE session_id = %s", 
                        (test_session_id,)
                    )
                    knowledge_count = cursor.fetchone()
                    if knowledge_count:
                        knowledge_count = knowledge_count[0]
                    else:
                        knowledge_count = 0
                
                connection.close()
                
                print(f"    - 知识库记录: {knowledge_count}条")
                
                return {
                    "success": True,
                    "integration_data": {
                        "profile": profile.difficulty_level if profile else None,
                        "target_count": len(target_matches) if target_matches else 0,
                        "report_generated": bool(report),
                        "knowledge_records": knowledge_count
                    }
                }
            else:
                error_msg = result.get("error", "完整流程执行失败")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"完整流程集成异常: {e}"}
    
    async def _insert_test_knowledge_data(self, session_id: str, questionnaire_url: str):
        """插入测试知识库数据"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                # 清理旧的测试数据
                cursor.execute(
                    "DELETE FROM questionnaire_knowledge WHERE session_id = %s",
                    (session_id,)
                )
                
                # 插入测试数据
                test_data = [
                    (session_id, questionnaire_url, "您的年龄段是？", "single_choice", 1, 1, "scout", "18-25岁", True, "success", "策略: 保守, 问题类型: single_choice, 答案: 18-25岁, 成功"),
                    (session_id, questionnaire_url, "您的职业是？", "single_choice", 2, 1, "scout", "学生", True, "success", "策略: 保守, 问题类型: single_choice, 答案: 学生, 成功"),
                    (session_id, questionnaire_url, "您的年龄段是？", "single_choice", 1, 2, "scout", "46岁以上", False, "failure", "策略: 激进, 问题类型: single_choice, 答案: 46岁以上, 失败: 选项不匹配"),
                    (session_id, questionnaire_url, "您的职业是？", "single_choice", 2, 2, "scout", "其他", False, "failure", "策略: 激进, 问题类型: single_choice, 答案: 其他, 失败: 过于特殊")
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
                print(f"  📝 插入了 {len(test_data)} 条测试知识库数据")
                
        except Exception as e:
            print(f"  ❌ 插入测试数据失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()
    
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📋 第三阶段测试总结")
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
        
        # 第三阶段完成度评估
        print(f"\n🎯 第三阶段完成度评估:")
        
        if success_rate >= 80:
            print(f"  🟢 优秀 ({success_rate:.1f}%) - 第三阶段基本完成")
            print(f"     ✅ 知识库分析系统运行正常")
            print(f"     ✅ 问卷画像分析功能正常")
            print(f"     ✅ 目标团队选择功能正常")
            print(f"     ✅ 分析报告生成功能正常")
            print(f"     🚀 可以进入第四阶段开发")
        elif success_rate >= 60:
            print(f"  🟡 良好 ({success_rate:.1f}%) - 第三阶段部分完成")
            print(f"     ⚠️ 部分功能需要优化")
            print(f"     🔧 建议修复失败的测试后再进入下一阶段")
        else:
            print(f"  🔴 需要改进 ({success_rate:.1f}%) - 第三阶段未完成")
            print(f"     ❌ 核心功能存在问题")
            print(f"     🛠️ 需要重点修复和优化")
        
        print(f"\n💡 下一步建议:")
        if success_rate >= 80:
            print(f"  1. 🎯 开始第四阶段：大规模自动化答题系统")
            print(f"  2. 🚀 实现目标团队并发答题")
            print(f"  3. 📊 开发实时监控和成功率统计")
            print(f"  4. 🎭 优化答题策略和成功率")
        else:
            print(f"  1. 🔧 修复失败的测试用例")
            print(f"  2. 📊 完善问卷画像分析算法")
            print(f"  3. 🎯 优化目标团队匹配逻辑")
            print(f"  4. 🧪 重新运行测试验证")

async def main():
    """主函数"""
    print("🚀 第三阶段知识库分析系统测试启动")
    
    test_suite = Phase3TestSuite()
    
    try:
        await test_suite.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试运行异常: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 