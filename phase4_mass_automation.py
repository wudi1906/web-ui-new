#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第四阶段：大规模自动化答题系统
基于前三阶段的成果，实现目标团队的并发答题、实时监控和智能优化
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import statistics

# 导入前面阶段的核心模块
from questionnaire_system import (
    QuestionnaireManager, 
    DatabaseManager, 
    QuestionnaireKnowledgeBase,
    TaskStatus, 
    PersonaRole,
    DB_CONFIG
)
from phase2_scout_automation import ScoutAutomationSystem
from phase3_knowledge_analysis import Phase3KnowledgeAnalysisSystem, QuestionnaireProfile, PersonaMatch
from browser_use_integration import RealBrowserUseIntegration

logger = logging.getLogger(__name__)

@dataclass
class AnsweringTask:
    """答题任务数据类"""
    task_id: str
    persona_id: int
    persona_name: str
    persona_info: Dict
    questionnaire_url: str
    strategy: str
    browser_profile_id: str = ""
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    success: bool = False
    error_message: str = ""
    answers_count: int = 0
    experience_data: List[Dict] = field(default_factory=list)

@dataclass
class MassAutomationStats:
    """大规模自动化统计数据"""
    total_tasks: int = 0
    completed_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0
    success_rate: float = 0.0
    avg_completion_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class RealTimeMonitor:
    """实时监控系统"""
    
    def __init__(self):
        self.stats = MassAutomationStats()
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.running_tasks: Dict[str, AnsweringTask] = {}
        self.completed_tasks: List[AnsweringTask] = []
        self.monitor_thread = None
        self.is_monitoring = False
    
    def start_monitoring(self):
        """启动实时监控"""
        self.is_monitoring = True
        self.stats.start_time = datetime.now()
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("📊 实时监控系统启动")
    
    def stop_monitoring(self):
        """停止实时监控"""
        self.is_monitoring = False
        self.stats.end_time = datetime.now()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("📊 实时监控系统停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 更新统计数据
                self._update_stats()
                
                # 处理结果队列（现在complete_task已经直接处理了，这里只是清空队列）
                while not self.result_queue.empty():
                    try:
                        self.result_queue.get_nowait()  # 只是清空队列，不重复处理
                    except queue.Empty:
                        break
                
                # 每5秒输出一次状态
                self._print_status()
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ 监控循环异常: {e}")
    
    def _update_stats(self):
        """更新统计数据"""
        self.stats.running_tasks = len(self.running_tasks)
        self.stats.completed_tasks = len(self.completed_tasks)
        self.stats.successful_tasks = sum(1 for task in self.completed_tasks if task.success)
        self.stats.failed_tasks = self.stats.completed_tasks - self.stats.successful_tasks
        
        if self.stats.completed_tasks > 0:
            self.stats.success_rate = self.stats.successful_tasks / self.stats.completed_tasks
            
            # 计算平均完成时间
            completion_times = []
            for task in self.completed_tasks:
                if task.start_time and task.end_time:
                    duration = (task.end_time - task.start_time).total_seconds()
                    completion_times.append(duration)
            
            if completion_times:
                self.stats.avg_completion_time = statistics.mean(completion_times)
    
    def _process_completed_task(self, task: AnsweringTask):
        """处理完成的任务"""
        if task.task_id in self.running_tasks:
            del self.running_tasks[task.task_id]
        
        self.completed_tasks.append(task)
        
        # 立即更新统计数据
        self._update_stats()
        
        status = "✅ 成功" if task.success else "❌ 失败"
        duration = 0
        if task.start_time and task.end_time:
            duration = (task.end_time - task.start_time).total_seconds()
        
        logger.info(f"📋 任务完成: {task.persona_name} - {status} ({duration:.1f}s)")
    
    def _print_status(self):
        """打印状态信息"""
        if self.stats.total_tasks > 0:
            progress = (self.stats.completed_tasks / self.stats.total_tasks) * 100
            logger.info(
                f"📊 进度: {progress:.1f}% "
                f"({self.stats.completed_tasks}/{self.stats.total_tasks}) "
                f"成功率: {self.stats.success_rate:.1%} "
                f"运行中: {self.stats.running_tasks}"
            )
    
    def add_task(self, task: AnsweringTask):
        """添加任务"""
        self.task_queue.put(task)
        self.stats.total_tasks += 1
        self.stats.pending_tasks += 1
    
    def start_task(self, task: AnsweringTask):
        """开始任务"""
        task.status = "running"
        task.start_time = datetime.now()
        self.running_tasks[task.task_id] = task
        self.stats.pending_tasks -= 1
    
    def complete_task(self, task: AnsweringTask):
        """完成任务"""
        task.status = "completed" if task.success else "failed"
        task.end_time = datetime.now()
        self.result_queue.put(task)
        
        # 立即处理完成的任务以更新统计数据
        self._process_completed_task(task)

class ConcurrentAnsweringEngine:
    """并发答题引擎"""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.browser_integration = RealBrowserUseIntegration()
        self.monitor = RealTimeMonitor()
        self.executor = None
    
    async def execute_mass_answering(
        self, 
        target_matches: List[PersonaMatch],
        questionnaire_url: str,
        questionnaire_profile: QuestionnaireProfile
    ) -> Dict[str, Any]:
        """执行大规模答题"""
        logger.info(f"🚀 开始大规模自动化答题")
        logger.info(f"📋 问卷URL: {questionnaire_url}")
        logger.info(f"👥 目标团队: {len(target_matches)}人")
        logger.info(f"🔧 并发数: {self.max_workers}")
        
        try:
            # 启动监控
            self.monitor.start_monitoring()
            
            # 创建答题任务
            tasks = self._create_answering_tasks(target_matches, questionnaire_url, questionnaire_profile)
            
            # 执行并发答题
            results = await self._execute_concurrent_tasks(tasks)
            
            # 停止监控
            self.monitor.stop_monitoring()
            
            # 生成结果报告
            report = self._generate_mass_automation_report(results)
            
            return {
                "success": True,
                "total_tasks": len(tasks),
                "completed_tasks": len(results),
                "successful_tasks": sum(1 for r in results if r.success),
                "success_rate": sum(1 for r in results if r.success) / len(results) if results else 0,
                "results": results,
                "report": report,
                "stats": self.monitor.stats
            }
            
        except Exception as e:
            logger.error(f"❌ 大规模答题执行失败: {e}")
            self.monitor.stop_monitoring()
            return {
                "success": False,
                "error": str(e),
                "stats": self.monitor.stats
            }
    
    def _create_answering_tasks(
        self, 
        target_matches: List[PersonaMatch],
        questionnaire_url: str,
        questionnaire_profile: QuestionnaireProfile
    ) -> List[AnsweringTask]:
        """创建答题任务"""
        tasks = []
        
        for i, match in enumerate(target_matches):
            # 根据问卷画像选择策略
            strategy = self._select_strategy_for_persona(match, questionnaire_profile)
            
            task = AnsweringTask(
                task_id=f"mass_task_{int(time.time())}_{i}",
                persona_id=match.persona_id,
                persona_name=match.persona_name,
                persona_info=match.persona_info,
                questionnaire_url=questionnaire_url,
                strategy=strategy
            )
            
            tasks.append(task)
            self.monitor.add_task(task)
        
        logger.info(f"📋 创建了 {len(tasks)} 个答题任务")
        return tasks
    
    def _select_strategy_for_persona(
        self, 
        match: PersonaMatch, 
        profile: QuestionnaireProfile
    ) -> str:
        """为数字人选择答题策略"""
        # 基于匹配度和问卷难度选择策略
        if match.match_score >= 0.8 and profile.difficulty_level == "easy":
            return "conservative"
        elif match.match_score >= 0.6 and profile.difficulty_level == "medium":
            return "conservative"
        elif profile.difficulty_level == "hard":
            return "conservative"  # 困难问卷都用保守策略
        else:
            return "random"
    
    async def _execute_concurrent_tasks(self, tasks: List[AnsweringTask]) -> List[AnsweringTask]:
        """执行并发任务"""
        logger.info(f"🔄 开始并发执行 {len(tasks)} 个任务")
        
        # 使用线程池执行任务
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        try:
            # 提交所有任务
            future_to_task = {}
            for task in tasks:
                future = self.executor.submit(self._execute_single_task, task)
                future_to_task[future] = task
            
            # 等待任务完成
            completed_tasks = []
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result_task = future.result()
                    completed_tasks.append(result_task)
                except Exception as e:
                    logger.error(f"❌ 任务执行异常: {task.persona_name} - {e}")
                    task.success = False
                    task.error_message = str(e)
                    task.end_time = datetime.now()
                    self.monitor.complete_task(task)
                    completed_tasks.append(task)
            
            return completed_tasks
            
        finally:
            if self.executor:
                self.executor.shutdown(wait=True)
    
    def _execute_single_task(self, task: AnsweringTask) -> AnsweringTask:
        """执行单个答题任务"""
        try:
            # 标记任务开始
            self.monitor.start_task(task)
            
            logger.info(f"🎯 开始执行任务: {task.persona_name} ({task.strategy}策略)")
            
            # 模拟答题过程（这里应该集成真实的Browser-use）
            success, experience = self._simulate_answering_process(task)
            
            # 更新任务结果
            task.success = success
            task.experience_data = experience
            task.answers_count = len(experience)
            
            if success:
                logger.info(f"✅ 任务成功: {task.persona_name} - 回答了{task.answers_count}个问题")
            else:
                logger.warning(f"❌ 任务失败: {task.persona_name} - {task.error_message}")
            
            # 标记任务完成
            self.monitor.complete_task(task)
            
            return task
            
        except Exception as e:
            task.success = False
            task.error_message = str(e)
            task.end_time = datetime.now()
            self.monitor.complete_task(task)
            logger.error(f"❌ 任务执行异常: {task.persona_name} - {e}")
            return task
    
    def _simulate_answering_process(self, task: AnsweringTask) -> Tuple[bool, List[Dict]]:
        """模拟答题过程（临时实现，后续替换为真实Browser-use）"""
        import random
        
        # 模拟答题时间
        answering_time = random.uniform(10, 30)  # 10-30秒
        time.sleep(answering_time)
        
        # 模拟答题结果
        success_probability = 0.8 if task.strategy == "conservative" else 0.6
        success = random.random() < success_probability
        
        # 模拟经验数据
        experience = []
        if success:
            question_count = random.randint(3, 8)
            for i in range(question_count):
                experience.append({
                    "question_number": i + 1,
                    "question_content": f"模拟问题{i+1}",
                    "question_type": "single_choice",
                    "answer_choice": f"选项{random.randint(1, 4)}",
                    "success": True,
                    "strategy": task.strategy
                })
        else:
            task.error_message = "模拟答题失败"
        
        return success, experience
    
    def _generate_mass_automation_report(self, results: List[AnsweringTask]) -> Dict[str, Any]:
        """生成大规模自动化报告"""
        if not results:
            return {"error": "没有任务结果"}
        
        # 基础统计
        total_tasks = len(results)
        successful_tasks = sum(1 for r in results if r.success)
        failed_tasks = total_tasks - successful_tasks
        success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0
        
        # 策略统计
        strategy_stats = {}
        for task in results:
            strategy = task.strategy
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"total": 0, "success": 0}
            strategy_stats[strategy]["total"] += 1
            if task.success:
                strategy_stats[strategy]["success"] += 1
        
        # 计算策略成功率
        for strategy, stats in strategy_stats.items():
            stats["success_rate"] = stats["success"] / stats["total"] if stats["total"] > 0 else 0
        
        # 时间统计
        completion_times = []
        for task in results:
            if task.start_time and task.end_time:
                duration = (task.end_time - task.start_time).total_seconds()
                completion_times.append(duration)
        
        time_stats = {}
        if completion_times:
            time_stats = {
                "avg_time": statistics.mean(completion_times),
                "min_time": min(completion_times),
                "max_time": max(completion_times),
                "median_time": statistics.median(completion_times)
            }
        
        # 答题质量统计
        total_answers = sum(task.answers_count for task in results if task.success)
        avg_answers_per_task = total_answers / successful_tasks if successful_tasks > 0 else 0
        
        return {
            "summary": {
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": success_rate,
                "total_answers": total_answers,
                "avg_answers_per_task": avg_answers_per_task
            },
            "strategy_performance": strategy_stats,
            "time_statistics": time_stats,
            "recommendations": self._generate_recommendations(strategy_stats, success_rate)
        }
    
    def _generate_recommendations(self, strategy_stats: Dict, overall_success_rate: float) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于整体成功率的建议
        if overall_success_rate >= 0.8:
            recommendations.append("整体表现优秀，可以考虑增加并发数量")
        elif overall_success_rate >= 0.6:
            recommendations.append("整体表现良好，建议优化失败任务的策略")
        else:
            recommendations.append("成功率偏低，建议重新分析问卷画像和目标团队匹配")
        
        # 基于策略表现的建议
        best_strategy = None
        best_rate = 0
        for strategy, stats in strategy_stats.items():
            if stats["success_rate"] > best_rate:
                best_rate = stats["success_rate"]
                best_strategy = strategy
        
        if best_strategy:
            recommendations.append(f"最佳策略是{best_strategy}，成功率{best_rate:.1%}")
        
        # 基于任务数量的建议
        if len(strategy_stats) > 1:
            recommendations.append("建议在后续任务中优先使用表现最好的策略")
        
        return recommendations

class Phase4MassAutomationSystem:
    """第四阶段大规模自动化系统"""
    
    def __init__(self):
        self.questionnaire_manager = QuestionnaireManager()
        self.phase3_system = Phase3KnowledgeAnalysisSystem()
        self.answering_engine = ConcurrentAnsweringEngine()
        self.db_manager = DatabaseManager(DB_CONFIG)
    
    async def execute_full_automation_pipeline(
        self,
        questionnaire_url: str,
        session_id: Optional[str] = None,
        target_count: int = 10,
        max_workers: int = 5
    ) -> Dict[str, Any]:
        """执行完整的自动化流水线"""
        logger.info(f"🚀 第四阶段：大规模自动化答题系统")
        logger.info(f"📋 问卷URL: {questionnaire_url}")
        logger.info(f"👥 目标人数: {target_count}")
        logger.info(f"🔧 并发数: {max_workers}")
        
        try:
            # 步骤1: 如果没有session_id，需要先运行第二阶段
            if not session_id:
                logger.info(f"📊 步骤1: 没有提供session_id，需要先运行敢死队...")
                return {
                    "success": False,
                    "error": "需要先运行第二阶段敢死队收集经验数据",
                    "suggestion": "请先运行 phase2_scout_automation.py 收集经验数据"
                }
            
            # 步骤2: 基于经验分析问卷画像和选择目标团队
            logger.info(f"📊 步骤2: 分析问卷画像和选择目标团队...")
            analysis_result = await self.phase3_system.analyze_and_select_target_team(
                session_id=session_id,
                questionnaire_url=questionnaire_url,
                target_count=target_count
            )
            
            if not analysis_result.get("success"):
                return {
                    "success": False,
                    "error": f"第三阶段分析失败: {analysis_result.get('error')}",
                    "analysis_result": analysis_result
                }
            
            questionnaire_profile = analysis_result.get("profile")
            target_matches = analysis_result.get("target_matches", [])
            
            if not target_matches or not questionnaire_profile:
                return {
                    "success": False,
                    "error": "没有找到合适的目标团队成员或问卷画像分析失败",
                    "analysis_result": analysis_result
                }
            
            logger.info(f"✅ 问卷画像分析完成: 难度{questionnaire_profile.difficulty_level}")
            logger.info(f"✅ 目标团队选择完成: {len(target_matches)}人")
            
            # 步骤3: 执行大规模并发答题
            logger.info(f"🚀 步骤3: 执行大规模并发答题...")
            self.answering_engine.max_workers = max_workers
            
            automation_result = await self.answering_engine.execute_mass_answering(
                target_matches=target_matches,
                questionnaire_url=questionnaire_url,
                questionnaire_profile=questionnaire_profile
            )
            
            # 步骤4: 保存结果到数据库
            logger.info(f"💾 步骤4: 保存结果到数据库...")
            await self._save_automation_results(
                session_id, 
                questionnaire_url, 
                automation_result
            )
            
            # 步骤5: 生成最终报告
            final_report = self._generate_final_report(
                analysis_result, 
                automation_result
            )
            
            logger.info(f"✅ 第四阶段大规模自动化完成")
            
            return {
                "success": True,
                "session_id": session_id,
                "questionnaire_url": questionnaire_url,
                "analysis_result": analysis_result,
                "automation_result": automation_result,
                "final_report": final_report
            }
            
        except Exception as e:
            logger.error(f"❌ 第四阶段执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _save_automation_results(
        self, 
        session_id: str, 
        questionnaire_url: str, 
        automation_result: Dict
    ):
        """保存自动化结果到数据库"""
        try:
            if not automation_result.get("success"):
                return
            
            results = automation_result.get("results", [])
            
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                for task in results:
                    if task.success and task.experience_data:
                        # 保存每个答题经验
                        for exp in task.experience_data:
                            sql = """
                            INSERT INTO questionnaire_knowledge 
                            (session_id, questionnaire_url, question_content, question_type, 
                             question_number, persona_id, persona_role, answer_choice, success, 
                             experience_type, experience_description)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            
                            experience_desc = (
                                f"策略: {task.strategy}, "
                                f"问题类型: {exp['question_type']}, "
                                f"答案: {exp['answer_choice']}, "
                                f"成功"
                            )
                            
                            cursor.execute(sql, (
                                session_id,
                                questionnaire_url,
                                exp["question_content"],
                                exp["question_type"],
                                exp["question_number"],
                                task.persona_id,
                                "target",  # 目标团队成员
                                exp["answer_choice"],
                                True,
                                "success",
                                experience_desc
                            ))
                
                connection.commit()
                logger.info(f"💾 保存了 {len(results)} 个任务的经验数据")
                
        except Exception as e:
            logger.error(f"❌ 保存自动化结果失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()
    
    def _generate_final_report(
        self, 
        analysis_result: Dict, 
        automation_result: Dict
    ) -> Dict[str, Any]:
        """生成最终报告"""
        # 安全地获取profile对象
        profile = analysis_result.get("profile")
        
        return {
            "pipeline_summary": {
                "phase2_completed": bool(analysis_result.get("success")),
                "phase3_completed": bool(analysis_result.get("success")),
                "phase4_completed": bool(automation_result.get("success")),
                "overall_success": (
                    analysis_result.get("success", False) and 
                    automation_result.get("success", False)
                )
            },
            "questionnaire_analysis": {
                "difficulty": profile.difficulty_level if profile else "unknown",
                "confidence": profile.confidence_score if profile else 0,
                "target_team_size": len(analysis_result.get("target_matches", []))
            },
            "automation_performance": automation_result.get("report", {}),
            "recommendations": self._generate_pipeline_recommendations(
                analysis_result, automation_result
            )
        }
    
    def _generate_pipeline_recommendations(
        self, 
        analysis_result: Dict, 
        automation_result: Dict
    ) -> List[str]:
        """生成流水线优化建议"""
        recommendations = []
        
        # 基于整体成功率
        success_rate = automation_result.get("success_rate", 0)
        if success_rate >= 0.8:
            recommendations.append("🎉 系统表现优秀，可以投入生产使用")
        elif success_rate >= 0.6:
            recommendations.append("⚠️ 系统表现良好，建议进一步优化策略")
        else:
            recommendations.append("🔧 系统需要优化，建议重新调整参数")
        
        # 基于目标团队匹配
        target_count = len(analysis_result.get("target_matches", []))
        if target_count < 5:
            recommendations.append("👥 目标团队人数较少，建议扩大筛选范围")
        
        # 基于问卷难度
        profile = analysis_result.get("profile")
        if profile and hasattr(profile, "difficulty_level") and profile.difficulty_level == "hard":
            recommendations.append("🎯 问卷难度较高，建议增加敢死队试探次数")
        
        return recommendations

async def main():
    """主函数 - 用于测试"""
    system = Phase4MassAutomationSystem()
    
    # 测试完整流水线
    result = await system.execute_full_automation_pipeline(
        questionnaire_url="https://www.wjx.cn/vm/test_phase4.aspx",
        session_id="test_session_phase3",  # 使用第三阶段的测试数据
        target_count=5,
        max_workers=3
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) 