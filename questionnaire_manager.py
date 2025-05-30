#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
问卷主管系统 - 完善的时间线控制
确保敢死队 -> 经验分析 -> 大部队的严格时间线执行
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

# 导入相关模块
from enhanced_run_questionnaire_with_knowledge import EnhancedQuestionnaireSystem
from intelligent_knowledge_base import IntelligentKnowledgeBase
from config import get_config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 等待中
    RUNNING = "running"           # 执行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 失败
    ANALYZING = "analyzing"       # 分析中
    READY = "ready"              # 准备就绪

class TaskPhase(Enum):
    """任务阶段枚举"""
    SCOUT_RECRUITMENT = "scout_recruitment"     # 敢死队招募
    SCOUT_EXECUTION = "scout_execution"         # 敢死队执行
    EXPERIENCE_COLLECTION = "experience_collection"  # 经验收集
    EXPERIENCE_ANALYSIS = "experience_analysis"      # 经验分析
    GUIDANCE_GENERATION = "guidance_generation"      # 指导生成
    TARGET_RECRUITMENT = "target_recruitment"        # 大部队招募
    TARGET_EXECUTION = "target_execution"            # 大部队执行
    WORKFLOW_COMPLETE = "workflow_complete"          # 工作流完成

class QuestionnaireManager:
    """问卷主管 - 负责整个工作流的时间线控制"""
    
    def __init__(self):
        self.enhanced_system = EnhancedQuestionnaireSystem()
        self.knowledge_base = IntelligentKnowledgeBase()
        self.current_phase = TaskPhase.SCOUT_RECRUITMENT
        self.task_status = TaskStatus.PENDING
        self.session_id = None
        self.questionnaire_url = None
        self.scout_results = []
        self.target_results = []
        self.guidance_rules = []
        self.start_time = None
        self.phase_times = {}
        
    async def execute_complete_workflow(self, questionnaire_url: str, 
                                      scout_count: int = 2, 
                                      target_count: int = 5) -> Dict:
        """执行完整的工作流，严格控制时间线"""
        logger.info("🎯 问卷主管启动完整工作流")
        logger.info("=" * 60)
        
        self.questionnaire_url = questionnaire_url
        self.start_time = time.time()
        
        try:
            # 阶段1: 敢死队招募和执行
            await self._execute_scout_phase(scout_count)
            
            # 确保session_id已设置
            if not self.session_id:
                raise Exception("敢死队执行后未获得session_id")
            
            # 阶段2: 经验收集和分析（关键等待点）
            await self._execute_analysis_phase()
            
            # 阶段3: 大部队招募和执行
            await self._execute_target_phase(target_count)
            
            # 阶段4: 工作流完成
            await self._finalize_workflow()
            
            return self._generate_final_report()
            
        except Exception as e:
            logger.error(f"❌ 工作流执行失败: {e}")
            self.task_status = TaskStatus.FAILED
            return {"success": False, "error": str(e)}
    
    async def _execute_scout_phase(self, scout_count: int):
        """执行敢死队阶段"""
        logger.info("📍 阶段1: 敢死队招募和执行")
        logger.info("-" * 40)
        
        # 更新阶段状态
        self._update_phase(TaskPhase.SCOUT_RECRUITMENT, TaskStatus.RUNNING)
        
        # 招募敢死队
        logger.info(f"👥 招募敢死队成员: {scout_count} 人")
        
        # 执行敢死队任务
        self._update_phase(TaskPhase.SCOUT_EXECUTION, TaskStatus.RUNNING)
        logger.info("🚀 敢死队开始执行任务...")
        
        # 确保questionnaire_url不为None
        if not self.questionnaire_url:
            raise Exception("问卷URL未设置")
        
        scout_result = await self.enhanced_system.run_scout_team(
            self.questionnaire_url, scout_count
        )
        
        if not scout_result["success"]:
            raise Exception(f"敢死队执行失败: {scout_result.get('error', '未知错误')}")
        
        self.scout_results = scout_result["results"]
        self.session_id = scout_result["session_id"]
        
        # 检查敢死队成功率
        successful_scouts = scout_result["successful_count"]
        if successful_scouts == 0:
            raise Exception("所有敢死队成员都失败了，无法继续")
        
        logger.info(f"✅ 敢死队执行完成: {successful_scouts}/{scout_count} 成功")
        self._update_phase(TaskPhase.SCOUT_EXECUTION, TaskStatus.COMPLETED)
    
    async def _execute_analysis_phase(self):
        """执行经验分析阶段 - 关键等待点"""
        logger.info("📍 阶段2: 经验收集和分析")
        logger.info("-" * 40)
        
        # 确保必要的变量已设置
        if not self.session_id or not self.questionnaire_url:
            raise Exception("session_id或questionnaire_url未设置")
        
        # 更新阶段状态
        self._update_phase(TaskPhase.EXPERIENCE_COLLECTION, TaskStatus.RUNNING)
        
        # 等待经验收集完成
        logger.info("📚 等待敢死队经验收集完成...")
        await self._wait_for_experience_collection()
        
        self._update_phase(TaskPhase.EXPERIENCE_COLLECTION, TaskStatus.COMPLETED)
        
        # 开始经验分析
        self._update_phase(TaskPhase.EXPERIENCE_ANALYSIS, TaskStatus.RUNNING)
        logger.info("🧠 开始分析敢死队经验...")
        
        # 分析经验并生成指导规则
        guidance_rules = await self.knowledge_base.analyze_experiences_and_generate_guidance(
            self.session_id, self.questionnaire_url
        )
        
        if not guidance_rules:
            logger.warning("⚠️ 未生成任何指导规则，将使用基础策略")
        else:
            logger.info(f"✅ 生成了 {len(guidance_rules)} 条指导规则")
            self.guidance_rules = guidance_rules
        
        self._update_phase(TaskPhase.EXPERIENCE_ANALYSIS, TaskStatus.COMPLETED)
        
        # 生成指导完成
        self._update_phase(TaskPhase.GUIDANCE_GENERATION, TaskStatus.COMPLETED)
        logger.info("📋 指导规则生成完成，可以启动大部队")
    
    async def _wait_for_experience_collection(self):
        """等待经验收集完成 - 关键同步点"""
        logger.info("⏳ 等待经验数据完全收集...")
        
        max_wait_time = 30  # 最大等待30秒
        wait_interval = 2   # 每2秒检查一次
        waited_time = 0
        
        while waited_time < max_wait_time:
            # 检查数据库中是否有足够的经验数据
            experience_count = await self._check_experience_count()
            
            if experience_count > 0:
                logger.info(f"✅ 检测到 {experience_count} 条经验数据，可以开始分析")
                break
            
            logger.info(f"⏳ 等待经验数据... ({waited_time}/{max_wait_time}秒)")
            await asyncio.sleep(wait_interval)
            waited_time += wait_interval
        
        if waited_time >= max_wait_time:
            logger.warning("⚠️ 等待经验数据超时，继续执行")
    
    async def _check_experience_count(self) -> int:
        """检查数据库中的经验数据数量"""
        try:
            # 确保必要的变量已设置
            if not self.session_id or not self.questionnaire_url:
                return 0
                
            connection = self.enhanced_system.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT COUNT(*) FROM questionnaire_knowledge 
                WHERE session_id = %s AND questionnaire_url = %s 
                AND persona_role = 'scout'
                """, (self.session_id, self.questionnaire_url))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"❌ 检查经验数据失败: {e}")
            return 0
        finally:
            if 'connection' in locals():
                connection.close()
    
    async def _execute_target_phase(self, target_count: int):
        """执行大部队阶段"""
        logger.info("📍 阶段3: 大部队招募和执行")
        logger.info("-" * 40)
        
        # 确保指导规则已准备就绪
        if self.current_phase != TaskPhase.GUIDANCE_GENERATION or self.task_status != TaskStatus.COMPLETED:
            raise Exception("指导规则未准备就绪，无法启动大部队")
        
        # 确保必要的变量已设置
        if not self.questionnaire_url or not self.session_id:
            raise Exception("questionnaire_url或session_id未设置")
        
        # 更新阶段状态
        self._update_phase(TaskPhase.TARGET_RECRUITMENT, TaskStatus.RUNNING)
        
        # 招募大部队
        logger.info(f"👥 招募大部队成员: {target_count} 人")
        
        # 执行大部队任务
        self._update_phase(TaskPhase.TARGET_EXECUTION, TaskStatus.RUNNING)
        logger.info("🚀 大部队开始执行任务...")
        
        target_result = await self.enhanced_system.run_target_team(
            self.questionnaire_url, self.session_id, target_count
        )
        
        if not target_result["success"]:
            logger.warning(f"⚠️ 大部队执行部分失败: {target_result.get('error', '未知错误')}")
        
        self.target_results = target_result["results"]
        
        successful_targets = target_result["successful_count"]
        logger.info(f"✅ 大部队执行完成: {successful_targets}/{target_count} 成功")
        
        self._update_phase(TaskPhase.TARGET_EXECUTION, TaskStatus.COMPLETED)
    
    async def _finalize_workflow(self):
        """完成工作流"""
        logger.info("📍 阶段4: 工作流完成")
        logger.info("-" * 40)
        
        self._update_phase(TaskPhase.WORKFLOW_COMPLETE, TaskStatus.COMPLETED)
        
        # 确保start_time已设置
        if self.start_time is None:
            total_time = 0.0
        else:
            total_time = time.time() - self.start_time
            
        logger.info(f"🎉 完整工作流执行完成，总用时: {total_time:.2f}秒")
        
        # 保存工作流记录
        await self._save_workflow_record()
    
    def _update_phase(self, phase: TaskPhase, status: TaskStatus):
        """更新阶段状态"""
        self.current_phase = phase
        self.task_status = status
        self.phase_times[phase.value] = {
            "status": status.value,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"📊 阶段更新: {phase.value} -> {status.value}")
    
    def _generate_final_report(self) -> Dict:
        """生成最终报告"""
        total_scouts = len(self.scout_results)
        successful_scouts = sum(1 for r in self.scout_results if r["success"])
        
        total_targets = len(self.target_results)
        successful_targets = sum(1 for r in self.target_results if r["success"])
        
        total_count = total_scouts + total_targets
        total_success = successful_scouts + successful_targets
        
        # 确保start_time已设置
        if self.start_time is None:
            total_time = 0.0
        else:
            total_time = time.time() - self.start_time
        
        report = {
            "success": True,
            "session_id": self.session_id,
            "questionnaire_url": self.questionnaire_url,
            "total_time": total_time,
            "phases": self.phase_times,
            "scout_phase": {
                "total": total_scouts,
                "successful": successful_scouts,
                "success_rate": successful_scouts / total_scouts if total_scouts > 0 else 0,
                "results": self.scout_results
            },
            "analysis_phase": {
                "guidance_rules_count": len(self.guidance_rules),
                "guidance_rules": [
                    {
                        "question_pattern": rule.question_pattern,
                        "recommended_answer": rule.recommended_answer,
                        "confidence_score": rule.confidence_score
                    } for rule in self.guidance_rules
                ]
            },
            "target_phase": {
                "total": total_targets,
                "successful": successful_targets,
                "success_rate": successful_targets / total_targets if total_targets > 0 else 0,
                "results": self.target_results
            },
            "overall": {
                "total_count": total_count,
                "total_success": total_success,
                "overall_success_rate": total_success / total_count if total_count > 0 else 0
            }
        }
        
        return report
    
    async def _save_workflow_record(self):
        """保存工作流记录"""
        try:
            # 确保start_time已设置
            if self.start_time is None:
                total_time = 0.0
            else:
                total_time = time.time() - self.start_time
                
            connection = self.enhanced_system.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO workflow_records 
                (session_id, questionnaire_url, workflow_type, total_phases,
                 scout_count, target_count, guidance_rules_count, total_time,
                 overall_success_rate, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    self.session_id,
                    self.questionnaire_url,
                    "enhanced_with_timeline",
                    len(self.phase_times),
                    len(self.scout_results),
                    len(self.target_results),
                    len(self.guidance_rules),
                    total_time,
                    (sum(1 for r in self.scout_results + self.target_results if r["success"]) / 
                     len(self.scout_results + self.target_results) if self.scout_results + self.target_results else 0),
                    datetime.now()
                ))
                connection.commit()
                logger.info("✅ 工作流记录已保存")
        except Exception as e:
            logger.error(f"❌ 保存工作流记录失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()
    
    def get_current_status(self) -> Dict:
        """获取当前状态"""
        return {
            "current_phase": self.current_phase.value,
            "task_status": self.task_status.value,
            "session_id": self.session_id,
            "questionnaire_url": self.questionnaire_url,
            "scout_results_count": len(self.scout_results),
            "target_results_count": len(self.target_results),
            "guidance_rules_count": len(self.guidance_rules),
            "phase_times": self.phase_times
        }

async def test_questionnaire_manager():
    """测试问卷主管系统"""
    print("🎯 测试问卷主管系统")
    print("=" * 50)
    
    manager = QuestionnaireManager()
    
    # 测试问卷URL
    test_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"
    
    # 执行完整工作流
    result = await manager.execute_complete_workflow(
        questionnaire_url=test_url,
        scout_count=2,
        target_count=3
    )
    
    # 显示结果
    print("\n🎉 工作流执行结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_questionnaire_manager()) 