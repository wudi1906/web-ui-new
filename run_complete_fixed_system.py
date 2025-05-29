#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能问卷自动填写系统 - 完整修复版本运行脚本
整合所有修复的功能：
1. 数据库表结构完善
2. 端口冲突解决
3. 知识库保存和查询
4. 敢死队经验积累
5. 大部队经验利用
6. 并发执行优化
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Optional

# 导入核心模块
from questionnaire_system import DatabaseManager, QuestionnaireManager, DB_CONFIG
from enhanced_browser_use_integration import EnhancedBrowserUseIntegration
from phase4_mass_automation import Phase4MassAutomationSystem, ConcurrentAnsweringEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'complete_system_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompleteFixedQuestionnaireSystem:
    """完整修复版本的问卷系统"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.questionnaire_manager = QuestionnaireManager()
        self.browser_integration = EnhancedBrowserUseIntegration(self.db_manager)
        self.mass_automation = Phase4MassAutomationSystem()
        
        # 验证数据库连接
        if not self.db_manager.test_connection():
            raise Exception("数据库连接失败，请检查配置")
        
        # 检查必需的表
        if not self.db_manager.check_required_tables():
            logger.warning("⚠️ 数据库表不完整，请先执行 update_database_schema.sql")
    
    async def run_complete_questionnaire_automation(
        self,
        questionnaire_url: str,
        scout_count: int = 2,
        target_count: int = 5,
        max_workers: int = 3
    ) -> Dict:
        """运行完整的问卷自动化流程"""
        
        logger.info("🚀 启动完整的智能问卷自动填写系统")
        logger.info(f"📋 问卷URL: {questionnaire_url}")
        logger.info(f"🕵️ 敢死队人数: {scout_count}")
        logger.info(f"👥 目标团队人数: {target_count}")
        logger.info(f"🔧 最大并发数: {max_workers}")
        
        session_id = f"complete_session_{int(time.time())}"
        
        try:
            # 阶段1：敢死队探索
            logger.info("=" * 60)
            logger.info("🕵️ 阶段1：敢死队探索阶段")
            logger.info("=" * 60)
            
            scout_results = await self._run_scout_phase(
                questionnaire_url, session_id, scout_count
            )
            
            if not scout_results.get("success"):
                return {
                    "success": False,
                    "error": f"敢死队阶段失败: {scout_results.get('error')}",
                    "scout_results": scout_results
                }
            
            logger.info(f"✅ 敢死队阶段完成，成功率: {scout_results.get('success_rate', 0):.1%}")
            
            # 阶段2：经验分析和目标团队选择
            logger.info("=" * 60)
            logger.info("📊 阶段2：经验分析和目标团队选择")
            logger.info("=" * 60)
            
            analysis_results = await self._analyze_scout_experience(
                session_id, questionnaire_url, target_count
            )
            
            if not analysis_results.get("success"):
                return {
                    "success": False,
                    "error": f"经验分析失败: {analysis_results.get('error')}",
                    "scout_results": scout_results,
                    "analysis_results": analysis_results
                }
            
            logger.info(f"✅ 经验分析完成，选择了 {len(analysis_results.get('target_personas', []))} 名目标成员")
            
            # 阶段3：大部队并发答题
            logger.info("=" * 60)
            logger.info("🚀 阶段3：大部队并发答题")
            logger.info("=" * 60)
            
            mass_results = await self._run_mass_automation_phase(
                questionnaire_url, session_id, analysis_results, max_workers
            )
            
            # 阶段4：生成最终报告
            logger.info("=" * 60)
            logger.info("📊 阶段4：生成最终报告")
            logger.info("=" * 60)
            
            final_report = self._generate_complete_report(
                scout_results, analysis_results, mass_results
            )
            
            logger.info("🎉 完整问卷自动化流程执行完成！")
            
            return {
                "success": True,
                "session_id": session_id,
                "questionnaire_url": questionnaire_url,
                "scout_results": scout_results,
                "analysis_results": analysis_results,
                "mass_results": mass_results,
                "final_report": final_report
            }
            
        except Exception as e:
            logger.error(f"❌ 完整流程执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def _run_scout_phase(
        self, 
        questionnaire_url: str, 
        session_id: str, 
        scout_count: int
    ) -> Dict:
        """运行敢死队阶段"""
        try:
            # 模拟查询敢死队成员（实际应该从小社会系统获取）
            scout_personas = []
            for i in range(scout_count):
                scout_personas.append({
                    'persona_id': 1000 + i,
                    'persona_name': f'敢死队员{i+1}',
                    'age': 25 + i * 5,
                    'gender': '男' if i % 2 == 0 else '女',
                    'profession': ['学生', '上班族', '设计师'][i % 3],
                    'birthplace_str': '北京',
                    'residence_str': '上海'
                })
            
            scout_results = []
            successful_scouts = 0
            
            for persona in scout_personas:
                logger.info(f"🕵️ {persona['persona_name']} 开始探索问卷...")
                
                # 创建独立的浏览器配置
                browser_config = self._create_unique_browser_config(persona['persona_id'])
                
                # 创建浏览器会话
                browser_session_id = await self.browser_integration.create_browser_session(
                    persona, browser_config
                )
                
                if not browser_session_id:
                    logger.warning(f"⚠️ {persona['persona_name']} 浏览器会话创建失败")
                    continue
                
                try:
                    # 导航到问卷
                    navigation_result = await self.browser_integration.navigate_and_analyze_questionnaire(
                        browser_session_id, questionnaire_url, f"scout_task_{persona['persona_id']}"
                    )
                    
                    if navigation_result.get("success"):
                        # 执行问卷填写
                        execution_result = await self.browser_integration.execute_complete_questionnaire(
                            browser_session_id, f"scout_task_{persona['persona_id']}", "conservative"
                        )
                        
                        if execution_result.get("success"):
                            successful_scouts += 1
                            logger.info(f"✅ {persona['persona_name']} 探索成功！")
                        else:
                            logger.warning(f"⚠️ {persona['persona_name']} 问卷填写失败")
                        
                        scout_results.append({
                            "persona": persona,
                            "navigation_result": navigation_result,
                            "execution_result": execution_result,
                            "success": execution_result.get("success", False)
                        })
                    else:
                        logger.warning(f"⚠️ {persona['persona_name']} 页面导航失败")
                
                finally:
                    # 关闭浏览器会话
                    await self.browser_integration.close_session(browser_session_id)
            
            success_rate = successful_scouts / len(scout_personas) if scout_personas else 0
            
            return {
                "success": successful_scouts > 0,
                "scout_count": len(scout_personas),
                "successful_scouts": successful_scouts,
                "success_rate": success_rate,
                "scout_results": scout_results
            }
            
        except Exception as e:
            logger.error(f"❌ 敢死队阶段失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_scout_experience(
        self, 
        session_id: str, 
        questionnaire_url: str, 
        target_count: int
    ) -> Dict:
        """分析敢死队经验并选择目标团队"""
        try:
            # 获取敢死队的成功经验
            scout_experiences = self.browser_integration.get_questionnaire_knowledge(
                session_id, questionnaire_url
            )
            
            logger.info(f"📚 获取到 {len(scout_experiences)} 条敢死队经验")
            
            if not scout_experiences:
                logger.warning("⚠️ 没有可用的敢死队经验，使用默认策略")
                experience_summary = "没有敢死队经验，建议使用保守策略"
            else:
                # 分析成功经验
                successful_experiences = [exp for exp in scout_experiences if exp.get('answer_choice')]
                experience_summary = self._summarize_scout_experiences(successful_experiences)
            
            # 模拟选择目标团队（实际应该从小社会系统获取）
            target_personas = []
            for i in range(target_count):
                target_personas.append({
                    'persona_id': 2000 + i,
                    'persona_name': f'目标成员{i+1}',
                    'age': 22 + i * 3,
                    'gender': '女' if i % 2 == 0 else '男',
                    'profession': ['学生', '教师', '工程师', '医生', '律师'][i % 5],
                    'birthplace_str': ['北京', '上海', '广州', '深圳'][i % 4],
                    'residence_str': ['北京', '上海', '广州', '深圳'][(i+1) % 4]
                })
            
            return {
                "success": True,
                "scout_experiences": scout_experiences,
                "experience_summary": experience_summary,
                "target_personas": target_personas,
                "target_count": len(target_personas)
            }
            
        except Exception as e:
            logger.error(f"❌ 经验分析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _summarize_scout_experiences(self, experiences: List[Dict]) -> str:
        """总结敢死队经验"""
        if not experiences:
            return "没有可用的成功经验"
        
        # 统计成功选择
        successful_choices = [exp.get('answer_choice', '') for exp in experiences if exp.get('answer_choice')]
        
        from collections import Counter
        choice_counts = Counter(successful_choices)
        top_choices = choice_counts.most_common(5)
        
        summary_parts = [
            f"基于 {len(experiences)} 条敢死队经验分析：",
            "【成功选择统计】"
        ]
        
        for choice, count in top_choices:
            summary_parts.append(f"- '{choice}' (成功 {count} 次)")
        
        summary_parts.extend([
            "【建议策略】",
            "1. 优先选择上述高频成功选项",
            "2. 保持保守的答题策略",
            "3. 遇到相似问题时参考敢死队的成功做法"
        ])
        
        return "\n".join(summary_parts)
    
    async def _run_mass_automation_phase(
        self, 
        questionnaire_url: str, 
        session_id: str, 
        analysis_results: Dict, 
        max_workers: int
    ) -> Dict:
        """运行大部队自动化阶段"""
        try:
            target_personas = analysis_results.get("target_personas", [])
            experience_summary = analysis_results.get("experience_summary", "")
            
            if not target_personas:
                return {
                    "success": False,
                    "error": "没有可用的目标团队成员"
                }
            
            # 创建并发答题引擎
            answering_engine = ConcurrentAnsweringEngine(max_workers=max_workers)
            
            # 模拟PersonaMatch对象
            from phase4_mass_automation import AnsweringTask
            
            tasks = []
            for persona in target_personas:
                # 确保persona_info包含必要字段
                persona_info = persona.copy()
                if 'id' not in persona_info:
                    persona_info['id'] = persona['persona_id']
                if 'name' not in persona_info:
                    persona_info['name'] = persona['persona_name']
                
                task = AnsweringTask(
                    task_id=f"mass_task_{persona['persona_id']}",
                    persona_id=persona['persona_id'],
                    persona_name=persona['persona_name'],
                    persona_info=persona_info,
                    questionnaire_url=questionnaire_url,
                    strategy="conservative"
                )
                tasks.append(task)
            
            # 执行并发答题
            logger.info(f"🚀 开始 {len(tasks)} 个目标成员的并发答题...")
            
            completed_tasks = await answering_engine._execute_concurrent_tasks(tasks)
            
            # 统计结果
            successful_tasks = sum(1 for task in completed_tasks if task.success)
            success_rate = successful_tasks / len(completed_tasks) if completed_tasks else 0
            
            logger.info(f"✅ 大部队答题完成，成功率: {success_rate:.1%} ({successful_tasks}/{len(completed_tasks)})")
            
            return {
                "success": True,
                "total_tasks": len(completed_tasks),
                "successful_tasks": successful_tasks,
                "success_rate": success_rate,
                "completed_tasks": completed_tasks,
                "experience_summary": experience_summary
            }
            
        except Exception as e:
            logger.error(f"❌ 大部队自动化阶段失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_unique_browser_config(self, persona_id: int) -> Dict:
        """创建独立的浏览器配置，避免端口冲突"""
        import random
        
        unique_port = random.randint(9000, 9999)
        unique_user_data_dir = f"/tmp/browser_profile_{persona_id}_{int(time.time())}"
        
        return {
            "headless": False,
            "window_width": 1280,
            "window_height": 800,
            "user_data_dir": unique_user_data_dir,
            "remote_debugging_port": unique_port,
            "disable_web_security": True,
            "args": [
                f"--remote-debugging-port={unique_port}",
                f"--user-data-dir={unique_user_data_dir}",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security"
            ]
        }
    
    def _generate_complete_report(
        self, 
        scout_results: Dict, 
        analysis_results: Dict, 
        mass_results: Dict
    ) -> Dict:
        """生成完整的执行报告"""
        
        return {
            "execution_summary": {
                "total_phases": 3,
                "scout_phase_success": scout_results.get("success", False),
                "analysis_phase_success": analysis_results.get("success", False),
                "mass_phase_success": mass_results.get("success", False),
                "overall_success": all([
                    scout_results.get("success", False),
                    analysis_results.get("success", False),
                    mass_results.get("success", False)
                ])
            },
            "scout_phase_stats": {
                "scout_count": scout_results.get("scout_count", 0),
                "successful_scouts": scout_results.get("successful_scouts", 0),
                "scout_success_rate": scout_results.get("success_rate", 0)
            },
            "analysis_phase_stats": {
                "experiences_collected": len(analysis_results.get("scout_experiences", [])),
                "target_team_size": analysis_results.get("target_count", 0)
            },
            "mass_phase_stats": {
                "total_tasks": mass_results.get("total_tasks", 0),
                "successful_tasks": mass_results.get("successful_tasks", 0),
                "mass_success_rate": mass_results.get("success_rate", 0)
            },
            "performance_metrics": {
                "experience_utilization": len(analysis_results.get("scout_experiences", [])) > 0,
                "concurrent_execution": mass_results.get("total_tasks", 0) > 1,
                "overall_efficiency": self._calculate_overall_efficiency(scout_results, mass_results)
            },
            "recommendations": self._generate_recommendations(scout_results, mass_results)
        }
    
    def _calculate_overall_efficiency(self, scout_results: Dict, mass_results: Dict) -> float:
        """计算整体效率"""
        scout_rate = scout_results.get("success_rate", 0)
        mass_rate = mass_results.get("success_rate", 0)
        
        # 加权平均：敢死队权重0.3，大部队权重0.7
        return scout_rate * 0.3 + mass_rate * 0.7
    
    def _generate_recommendations(self, scout_results: Dict, mass_results: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        scout_rate = scout_results.get("success_rate", 0)
        mass_rate = mass_results.get("success_rate", 0)
        
        if scout_rate >= 0.8 and mass_rate >= 0.8:
            recommendations.append("🎉 系统表现优秀，可以投入生产使用")
        elif scout_rate >= 0.6 and mass_rate >= 0.6:
            recommendations.append("✅ 系统表现良好，建议进一步优化")
        else:
            recommendations.append("⚠️ 系统需要优化，建议调整策略")
        
        if scout_rate < 0.5:
            recommendations.append("🕵️ 敢死队成功率偏低，建议增加敢死队人数或优化选择策略")
        
        if mass_rate < 0.5:
            recommendations.append("👥 大部队成功率偏低，建议优化目标团队选择或答题策略")
        
        if mass_rate > scout_rate + 0.2:
            recommendations.append("📈 大部队表现优于敢死队，经验学习机制有效")
        
        return recommendations

async def main():
    """主函数 - 运行完整的系统测试"""
    
    print("🚀 智能问卷自动填写系统 - 完整修复版本")
    print("=" * 60)
    
    # 创建系统实例
    system = CompleteFixedQuestionnaireSystem()
    
    # 配置测试参数
    test_questionnaire_url = "https://www.wjx.cn/vm/w4e8hc9.aspx"  # 替换为实际问卷URL
    scout_count = 2  # 敢死队人数
    target_count = 3  # 目标团队人数（测试用较小数量）
    max_workers = 2  # 最大并发数（测试用较小数量）
    
    try:
        # 运行完整流程
        result = await system.run_complete_questionnaire_automation(
            questionnaire_url=test_questionnaire_url,
            scout_count=scout_count,
            target_count=target_count,
            max_workers=max_workers
        )
        
        # 输出结果
        print("\n" + "=" * 60)
        print("📊 执行结果报告")
        print("=" * 60)
        
        if result.get("success"):
            print("✅ 完整流程执行成功！")
            
            final_report = result.get("final_report", {})
            
            # 输出各阶段统计
            scout_stats = final_report.get("scout_phase_stats", {})
            print(f"🕵️ 敢死队阶段: {scout_stats.get('successful_scouts', 0)}/{scout_stats.get('scout_count', 0)} 成功")
            
            analysis_stats = final_report.get("analysis_phase_stats", {})
            print(f"📊 分析阶段: 收集了 {analysis_stats.get('experiences_collected', 0)} 条经验")
            
            mass_stats = final_report.get("mass_phase_stats", {})
            print(f"🚀 大部队阶段: {mass_stats.get('successful_tasks', 0)}/{mass_stats.get('total_tasks', 0)} 成功")
            
            # 输出性能指标
            performance = final_report.get("performance_metrics", {})
            print(f"📈 整体效率: {performance.get('overall_efficiency', 0):.1%}")
            
            # 输出建议
            recommendations = final_report.get("recommendations", [])
            if recommendations:
                print("\n💡 优化建议:")
                for rec in recommendations:
                    print(f"  {rec}")
        else:
            print("❌ 执行失败:")
            print(f"   错误: {result.get('error', '未知错误')}")
        
        # 保存详细结果到文件
        result_file = f"complete_system_result_{int(time.time())}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 详细结果已保存到: {result_file}")
        
    except Exception as e:
        print(f"❌ 系统执行异常: {e}")
        logger.error(f"系统执行异常: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main()) 