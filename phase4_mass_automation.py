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
from enum import Enum
import random
import os
import shutil

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
from enhanced_browser_use_integration import EnhancedBrowserUseIntegration

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
        # 使用真实的browser-use集成，而不是模拟
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.browser_integration = EnhancedBrowserUseIntegration(self.db_manager)
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
            
            # 确保persona_info包含必要的字段
            persona_info = match.persona_info.copy()
            
            # 添加缺失的字段
            if 'persona_id' not in persona_info:
                persona_info['persona_id'] = match.persona_id
            if 'persona_name' not in persona_info:
                persona_info['persona_name'] = match.persona_name
            if 'id' not in persona_info:
                persona_info['id'] = match.persona_id
            if 'name' not in persona_info:
                persona_info['name'] = match.persona_name
            
            task = AnsweringTask(
                task_id=f"mass_task_{int(time.time())}_{i}",
                persona_id=match.persona_id,
                persona_name=match.persona_name,
                persona_info=persona_info,  # 使用修正后的persona_info
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
        
        try:
            # 使用asyncio.gather进行真正的并发执行
            completed_tasks = await asyncio.gather(
                *[self._execute_single_task(task) for task in tasks],
                return_exceptions=True
            )
            
            # 处理结果和异常
            results = []
            for i, result in enumerate(completed_tasks):
                if isinstance(result, Exception):
                    task = tasks[i]
                    task.success = False
                    task.error_message = str(result)
                    task.end_time = datetime.now()
                    self.monitor.complete_task(task)
                    logger.error(f"❌ 任务执行异常: {task.persona_name} - {result}")
                    results.append(task)
                else:
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 并发执行异常: {e}")
            # 标记所有任务为失败
            for task in tasks:
                task.success = False
                task.error_message = f"并发执行异常: {str(e)}"
                task.end_time = datetime.now()
                self.monitor.complete_task(task)
            return tasks
    
    async def _execute_single_task(self, task: AnsweringTask) -> AnsweringTask:
        """执行单个答题任务（修改为支持错误蒙版和窗口布局）"""
        start_time = time.time()
        task.start_time = datetime.now()
        task.status = "running"
        
        try:
            logger.info(f"🚀 开始执行任务: {task.persona_name}")
            
            # 生成独立的浏览器配置（支持6个窗口的flow布局）
            browser_config = self._generate_browser_config(task.persona_id)
            
            # 创建增强的浏览器集成实例
            browser_integration = EnhancedBrowserUseIntegration(self.db_manager)
            
            # 创建浏览器会话
            session_id = await browser_integration.create_browser_session(task.persona_info, browser_config)
            
            if not session_id:
                task.success = False
                task.error_message = "浏览器会话创建失败"
                logger.error(f"❌ {task.persona_name} 浏览器会话创建失败")
                return task
            
            task.browser_profile_id = session_id
            
            # 执行真实的浏览器答题流程
            success, experience_data = await self._real_browser_answering_process(task)
            
            task.success = success
            task.experience_data = experience_data
            task.answers_count = len(experience_data) if experience_data else 0
            
            # 如果出现错误，在蒙版中显示而不是关闭浏览器
            if not success:
                error_message = task.error_message or "答题过程中出现未知错误"
                await browser_integration._show_error_in_overlay(session_id, error_message, "答题失败")
                logger.warning(f"⚠️ {task.persona_name} 答题失败，错误已显示在蒙版中: {error_message}")
            else:
                # 成功时在蒙版中显示成功信息
                await browser_integration._show_error_in_overlay(session_id, "问卷填写成功完成！", "成功")
                logger.info(f"✅ {task.persona_name} 答题成功")
            
            # 不自动关闭浏览器，让用户可以查看结果
            # logger.info(f"🔒 关闭 {task.persona_name} 的浏览器会话")
            # await browser_integration.close_session(session_id)
            logger.info(f"📋 {task.persona_name} 的浏览器保持打开状态，可查看答题结果")
            
            # 不清理临时文件，保持浏览器状态
            # try:
            #     if os.path.exists(unique_user_data_dir):
            #         shutil.rmtree(unique_user_data_dir)
            # except Exception as cleanup_error:
            #     logger.warning(f"⚠️ 清理临时文件失败: {cleanup_error}")
            
            if success:
                logger.info(f"🎉 {task.persona_name} 问卷填写成功！回答了 {task.answers_count}/{task.answers_count} 个问题")
            else:
                logger.warning(f"❌ 任务失败: {task.persona_name} - {task.error_message}")
            
        except Exception as e:
            task.success = False
            task.error_message = str(e)
            logger.warning(f"❌ 任务失败: {task.persona_name} - {task.error_message}")
            
            # 尝试在蒙版中显示错误，而不是关闭浏览器
            try:
                if hasattr(task, 'browser_profile_id') and task.browser_profile_id:
                    browser_integration = EnhancedBrowserUseIntegration(self.db_manager)
                    await browser_integration._show_error_in_overlay(task.browser_profile_id, task.error_message, "系统错误")
            except:
                pass  # 如果蒙版显示失败，不影响主流程
        
        finally:
            task.end_time = datetime.now()
            task.status = "completed" if task.success else "failed"
            duration = time.time() - start_time
            
            logger.info(f"📋 任务完成: {task.persona_name} - {'✅ 成功' if task.success else '❌ 失败'} ({duration:.1f}s)")
        
        return task

    def _generate_browser_config(self, persona_id: int) -> Dict:
        """生成独立的浏览器配置（支持6个窗口的flow布局）"""
        import random
        
        # 生成唯一端口（避免冲突）
        base_port = 9000
        unique_port = base_port + (persona_id % 1000)  # 确保端口唯一性
        
        # 生成唯一的用户数据目录
        user_data_dir = f"/tmp/mass_browser_profile_{persona_id}_{int(time.time())}"
        
        # 计算窗口位置（6个窗口的flow布局：3列2行）
        window_layout = self._calculate_mass_window_layout(persona_id)
        
        config = {
            "headless": False,
            "window_width": window_layout["width"],
            "window_height": window_layout["height"],
            "window_x": window_layout["x"],
            "window_y": window_layout["y"],
            "user_data_dir": user_data_dir,
            "remote_debugging_port": unique_port,
            "args": [
                f"--remote-debugging-port={unique_port}",
                f"--user-data-dir={user_data_dir}",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                f"--window-position={window_layout['x']},{window_layout['y']}",
                f"--window-size={window_layout['width']},{window_layout['height']}"
            ]
        }
        
        logger.info(f"🖥️ 数字人{persona_id} 浏览器配置: {window_layout['width']}x{window_layout['height']} at ({window_layout['x']}, {window_layout['y']}) 端口:{unique_port}")
        
        return config

    def _calculate_mass_window_layout(self, persona_id: int) -> Dict:
        """计算大部队窗口布局（6个窗口的flow布局）"""
        # 屏幕分辨率假设
        screen_width = 1920
        screen_height = 1080
        
        # 6个窗口的布局：3列2行
        cols = 3
        rows = 2
        window_width = screen_width // cols
        window_height = screen_height // rows
        
        # 计算当前窗口的行列位置
        window_index = (persona_id - 1) % 6  # 确保在0-5范围内
        row = window_index // cols
        col = window_index % cols
        
        # 计算窗口位置
        x = col * window_width
        y = row * window_height
        
        return {
            "width": window_width - 20,  # 留边距
            "height": window_height - 60,  # 留出标题栏和任务栏空间
            "x": x + 10,  # 小偏移避免重叠
            "y": y + 30
        }
    
    async def _real_browser_answering_process(self, task: AnsweringTask) -> Tuple[bool, List[Dict]]:
        """真实的browser-use答题过程"""
        try:
            logger.info(f"📄 {task.persona_name} 开始导航到问卷页面")
            
            # 创建增强的浏览器集成实例
            browser_integration = EnhancedBrowserUseIntegration(self.db_manager)
            
            # 查询敢死队的成功经验
            scout_experiences = browser_integration.get_questionnaire_knowledge("", task.questionnaire_url)
            
            # 生成基于经验的答题策略提示
            experience_prompt = self._generate_experience_based_prompt(scout_experiences)
            
            logger.info(f"📚 为 {task.persona_name} 加载了 {len(scout_experiences)} 条敢死队经验")
            
            # 第一步：导航到问卷并分析页面
            navigation_result = await browser_integration.navigate_and_analyze_questionnaire(
                task.browser_profile_id, task.questionnaire_url, task.task_id
            )
            
            if not navigation_result.get("success"):
                task.error_message = f"页面导航失败: {navigation_result.get('error', '未知错误')}"
                return False, []
            
            # 第二步：执行完整的问卷填写流程（带经验指导）
            execution_result = await browser_integration.execute_complete_questionnaire_with_experience(
                task.browser_profile_id, task.task_id, task.strategy, experience_prompt
            )
            
            if execution_result.get("success"):
                # 解析执行结果
                detailed_steps = execution_result.get("detailed_steps", [])
                successful_steps = [step for step in detailed_steps if step.get("success", False)]
                total_questions = len(detailed_steps)
                successful_answers = len(successful_steps)
                
                logger.info(f"✅ {task.persona_name} 问卷填写成功: {successful_answers}/{total_questions}")
                
                return True, [{
                    "execution_result": execution_result,
                    "strategy": task.strategy,
                    "duration": execution_result.get("duration", 0),
                    "successful_answers": successful_answers,
                    "total_questions": total_questions,
                    "session_summary": await browser_integration.get_session_summary(task.browser_profile_id),
                    "used_experiences": len(scout_experiences)
                }]
            else:
                task.error_message = f"问卷填写失败: {execution_result.get('error', '未知错误')}"
                logger.warning(f"⚠️ {task.persona_name} 问卷填写失败: {task.error_message}")
                return False, []
                
        except Exception as e:
            task.error_message = f"答题过程异常: {str(e)}"
            logger.error(f"❌ {task.persona_name} 答题过程异常: {e}")
            return False, []
    
    def _generate_experience_based_prompt(self, scout_experiences: List[Dict]) -> str:
        """基于敢死队经验生成答题策略提示"""
        if not scout_experiences:
            return "没有可用的敢死队经验，请使用保守策略。"
        
        # 分析成功经验
        successful_choices = []
        common_strategies = []
        
        for exp in scout_experiences:
            answer_choice = exp.get('answer_choice', '')
            strategy = exp.get('strategy_used', '')
            description = exp.get('experience_description', '')
            
            if answer_choice and answer_choice != 'unknown':
                successful_choices.append(answer_choice)
            
            if strategy and strategy not in common_strategies:
                common_strategies.append(strategy)
        
        # 生成经验指导提示
        prompt_parts = [
            "【敢死队成功经验指导】",
            f"基于 {len(scout_experiences)} 条敢死队经验，以下是成功策略："
        ]
        
        if successful_choices:
            # 统计最常见的成功选择
            from collections import Counter
            choice_counts = Counter(successful_choices)
            top_choices = choice_counts.most_common(5)
            
            prompt_parts.append("【成功选择经验】")
            for choice, count in top_choices:
                prompt_parts.append(f"- '{choice}' (成功 {count} 次)")
        
        if common_strategies:
            prompt_parts.append(f"【推荐策略】: {', '.join(common_strategies)}")
        
        # 添加具体的答题建议
        prompt_parts.extend([
            "【答题建议】",
            "1. 优先选择上述成功经验中的选项",
            "2. 如果遇到相似问题，参考敢死队的成功做法",
            "3. 避免过于特殊或极端的选择",
            "4. 保持与成功案例一致的答题风格"
        ])
        
        return "\n".join(prompt_parts)
    
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