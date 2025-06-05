#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
四阶段并行智能工作流系统
完整实现：并行敢死队 → Gemini分析 → 智能招募 → 并行大部队

技术架构：
- 20窗口并行支持
- 页面数据抓取
- 双知识库系统
- AdsPower+WebUI集成
- 完整的四阶段流程
"""

import asyncio
import logging
import time
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入必要的模块
try:
    from adspower_browser_use_integration import AdsPowerWebUIIntegration
    from dual_knowledge_base_system import get_dual_knowledge_base, TemporaryExperience, QuestionnaireAnalysis
    from window_layout_manager import get_window_manager
    from questionnaire_system import XiaosheSystemClient
    all_modules_available = True
    logger.info("✅ 所有模块导入成功")
except ImportError as e:
    logger.warning(f"⚠️ 模块导入失败: {e}")
    all_modules_available = False

@dataclass
class WorkflowStatus:
    """工作流状态"""
    session_id: str
    current_stage: int  # 1-4
    stage_name: str
    progress_percentage: int
    scout_count: int
    target_count: int
    scout_completed: int = 0
    target_completed: int = 0
    analysis_completed: bool = False
    error_message: Optional[str] = None
    start_time: str = ""
    estimated_completion: str = ""

class ParallelFourStageWorkflow:
    """四阶段并行智能工作流系统"""
    
    def __init__(self):
        # 初始化各个系统组件
        self.adspower_integration = AdsPowerWebUIIntegration() if all_modules_available else None
        self.dual_kb = get_dual_knowledge_base() if all_modules_available else None
        self.window_manager = get_window_manager() if all_modules_available else None
        
        # 初始化小社会系统
        try:
            self.xiaoshe_client = XiaosheSystemClient({
                "base_url": "http://localhost:5001",
                "timeout": 30
            })
            logger.info("✅ 小社会系统初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 小社会系统初始化失败: {e}")
            self.xiaoshe_client = None
        
        # 工作流状态管理
        self.active_workflows: Dict[str, WorkflowStatus] = {}
        
        logger.info("✅ 四阶段并行工作流系统初始化完成")
    
    async def execute_complete_workflow(
        self,
        questionnaire_url: str,
        scout_count: int = 2,
        target_count: int = 5
    ) -> Dict[str, Any]:
        """执行完整的四阶段并行工作流"""
        
        # 生成会话ID
        session_id = f"workflow_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # 初始化工作流状态
        status = WorkflowStatus(
            session_id=session_id,
            current_stage=1,
            stage_name="敢死队并行情报收集",
            progress_percentage=0,
            scout_count=scout_count,
            target_count=target_count,
            start_time=datetime.now().isoformat()
        )
        self.active_workflows[session_id] = status
        
        try:
            logger.info(f"🚀 开始四阶段并行工作流 - 会话ID: {session_id}")
            logger.info(f"📋 配置: 敢死队{scout_count}人, 大部队{target_count}人")
            logger.info(f"🎯 问卷: {questionnaire_url}")
            
            # 第一阶段：敢死队并行情报收集
            logger.info("=" * 80)
            logger.info("🔍 第一阶段：敢死队并行情报收集")
            logger.info("=" * 80)
            
            scout_results = await self._execute_parallel_scout_stage(
                session_id, questionnaire_url, scout_count
            )
            
            if not scout_results or len(scout_results) == 0:
                raise Exception("敢死队阶段完全失败，无法继续")
            
            # 更新状态
            status.current_stage = 2
            status.stage_name = "Gemini智能分析"
            status.progress_percentage = 25
            status.scout_completed = len(scout_results)
            
            # 第二阶段：Gemini智能分析
            logger.info("=" * 80)
            logger.info("🧠 第二阶段：Gemini智能分析")
            logger.info("=" * 80)
            
            analysis_result = await self._execute_analysis_stage(
                session_id, questionnaire_url, scout_results
            )
            
            if not analysis_result:
                raise Exception("智能分析失败，使用基础策略继续")
            
            # 更新状态
            status.current_stage = 3
            status.stage_name = "大部队智能招募"
            status.progress_percentage = 50
            status.analysis_completed = True
            
            # 第三阶段：大部队智能招募
            logger.info("=" * 80)
            logger.info("👥 第三阶段：大部队智能招募")
            logger.info("=" * 80)
            
            target_team = await self._execute_recruitment_stage(
                session_id, analysis_result, target_count
            )
            
            # 更新状态
            status.current_stage = 4
            status.stage_name = "大部队并行作战"
            status.progress_percentage = 75
            
            # 第四阶段：大部队并行作战
            logger.info("=" * 80)
            logger.info("🎯 第四阶段：大部队并行作战")
            logger.info("=" * 80)
            
            target_results = await self._execute_parallel_target_stage(
                session_id, questionnaire_url, target_team, analysis_result
            )
            
            # 更新最终状态
            status.progress_percentage = 100
            status.target_completed = len(target_results)
            status.estimated_completion = datetime.now().isoformat()
            
            # 生成最终报告
            final_report = self._generate_final_report(
                session_id, scout_results, analysis_result, target_results
            )
            
            logger.info("🎉 四阶段并行工作流完成！")
            
            return {
                "success": True,
                "session_id": session_id,
                "workflow_status": status,
                "scout_results": scout_results,
                "analysis_result": analysis_result,
                "target_results": target_results,
                "final_report": final_report,
                "execution_mode": "four_stage_parallel_workflow"
            }
            
        except Exception as e:
            logger.error(f"❌ 四阶段工作流失败: {e}")
            status.error_message = str(e)
            
            return {
                "success": False,
                "session_id": session_id,
                "workflow_status": status,
                "error": str(e),
                "execution_mode": "four_stage_parallel_workflow_failed"
            }
    
    async def _execute_parallel_scout_stage(
        self,
        session_id: str,
        questionnaire_url: str,
        scout_count: int
    ) -> List[Dict]:
        """第一阶段：敢死队并行情报收集"""
        
        # 1. 招募敢死队成员
        scouts = await self._recruit_scout_team(scout_count)
        logger.info(f"✅ 招募敢死队完成：{len(scouts)}人")
        
        # 2. 为每个敢死队成员创建"新电脑"
        scout_sessions = []
        for i, scout in enumerate(scouts):
            try:
                session_id_scout = await self.adspower_integration.create_adspower_browser_session(
                    scout["id"], scout["name"]
                )
                if session_id_scout:
                    scout_sessions.append({
                        "scout": scout,
                        "session_id": session_id_scout,
                        "browser_ready": True
                    })
                    logger.info(f"✅ 敢死队成员 {scout['name']} 的'新电脑'准备就绪")
                else:
                    logger.warning(f"⚠️ 敢死队成员 {scout['name']} 的'新电脑'创建失败")
            except Exception as e:
                logger.error(f"❌ 为敢死队成员 {scout['name']} 创建'新电脑'失败: {e}")
        
        logger.info(f"📱 成功创建 {len(scout_sessions)} 台'新电脑'，开始并行答题")
        
        # 3. 并行执行敢死队任务
        tasks = []
        for scout_session in scout_sessions:
            task = self._execute_single_scout_mission(
                session_id, questionnaire_url, scout_session
            )
            tasks.append(task)
        
        # 等待所有敢死队成员完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤成功的结果
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 敢死队成员 {scout_sessions[i]['scout']['name']} 执行失败: {result}")
            elif result and result.get("success"):
                successful_results.append(result)
                logger.info(f"✅ 敢死队成员 {scout_sessions[i]['scout']['name']} 完成任务")
        
        logger.info(f"📊 敢死队阶段完成：{len(successful_results)}/{len(scouts)} 成功")
        
        return successful_results
    
    async def _recruit_scout_team(self, scout_count: int) -> List[Dict]:
        """招募敢死队成员"""
        scouts = []
        
        if self.xiaoshe_client:
            try:
                # 使用小社会系统招募多样化的敢死队
                for i in range(scout_count):
                    query = f"找一个适合做问卷调查的数字人，第{i+1}个"
                    persona = await self._query_xiaoshe_persona(query, f"scout_{i}")
                    if persona:
                        scouts.append(persona)
                        logger.info(f"✅ 招募敢死队成员：{persona['name']}")
                
            except Exception as e:
                logger.warning(f"⚠️ 小社会招募失败，使用备用方案: {e}")
        
        # 备用方案：创建默认敢死队成员
        while len(scouts) < scout_count:
            backup_scout = self._create_backup_scout(len(scouts))
            scouts.append(backup_scout)
            logger.info(f"✅ 创建备用敢死队成员：{backup_scout['name']}")
        
        return scouts
    
    async def _query_xiaoshe_persona(self, query: str, persona_id: str) -> Optional[Dict]:
        """查询小社会数字人"""
        try:
            if not self.xiaoshe_client:
                return None
            
            response = await self.xiaoshe_client.query_digital_human(query)
            if response and response.get("success"):
                persona_data = response.get("data", {})
                return {
                    "id": persona_id,
                    "name": persona_data.get("name", f"数字人{persona_id}"),
                    "age": persona_data.get("age", 28),
                    "job": persona_data.get("job", "办公室职员"),
                    "income": persona_data.get("income", "8000"),
                    "description": persona_data.get("description", "普通用户"),
                    "source": "xiaoshe_system"
                }
        except Exception as e:
            logger.warning(f"⚠️ 查询小社会失败: {e}")
        
        return None
    
    def _create_backup_scout(self, index: int) -> Dict:
        """创建备用敢死队成员"""
        scout_profiles = [
            {"name": "张小雅", "age": 28, "job": "产品经理", "income": "12000"},
            {"name": "李小明", "age": 26, "job": "软件工程师", "income": "15000"},
            {"name": "王小丽", "age": 30, "job": "市场专员", "income": "8000"},
            {"name": "赵小华", "age": 32, "job": "销售经理", "income": "10000"},
            {"name": "陈小芳", "age": 24, "job": "设计师", "income": "7000"}
        ]
        
        profile = scout_profiles[index % len(scout_profiles)]
        return {
            "id": f"backup_scout_{index}",
            "name": profile["name"],
            "age": profile["age"],
            "job": profile["job"],
            "income": profile["income"],
            "description": f"备用敢死队成员，{profile['job']}",
            "source": "backup_system"
        }
    
    async def _execute_single_scout_mission(
        self,
        session_id: str,
        questionnaire_url: str,
        scout_session: Dict
    ) -> Dict:
        """执行单个敢死队成员的任务"""
        
        scout = scout_session["scout"]
        session_id_scout = scout_session["session_id"]
        
        try:
            logger.info(f"🔍 敢死队成员 {scout['name']} 开始执行任务")
            
            # 获取浏览器信息
            browser_info = self.adspower_integration.get_session_info(session_id_scout)
            if not browser_info:
                raise Exception("获取浏览器信息失败")
            
            existing_browser_info = {
                "profile_id": browser_info["profile_id"],
                "debug_port": browser_info["debug_port"],
                "proxy_enabled": browser_info["browser_env"].get("proxy_enabled", False)
            }
            
            # 执行问卷任务（包含页面数据抓取）
            result = await self.adspower_integration.execute_questionnaire_task_with_data_extraction(
                persona_id=scout["id"],
                persona_name=scout["name"],
                digital_human_info=scout,
                questionnaire_url=questionnaire_url,
                existing_browser_info=existing_browser_info
            )
            
            if result.get("success"):
                # 提取并保存经验到双知识库
                if self.dual_kb and result.get("page_data"):
                    await self._save_scout_experience_to_kb(
                        questionnaire_url, scout, result["page_data"]
                    )
                
                logger.info(f"✅ 敢死队成员 {scout['name']} 任务完成")
                return {
                    "success": True,
                    "scout": scout,
                    "result": result,
                    "page_data": result.get("page_data"),
                    "execution_time": result.get("duration", 0)
                }
            else:
                logger.warning(f"⚠️ 敢死队成员 {scout['name']} 任务部分失败")
                return {
                    "success": False,
                    "scout": scout,
                    "error": result.get("error", "未知错误")
                }
                
        except Exception as e:
            logger.error(f"❌ 敢死队成员 {scout['name']} 任务执行异常: {e}")
            return {
                "success": False,
                "scout": scout,
                "error": str(e)
            }
    
    async def _save_scout_experience_to_kb(
        self,
        questionnaire_url: str,
        scout: Dict,
        page_data: Dict
    ):
        """保存敢死队经验到双知识库"""
        try:
            if not page_data.get("extraction_success"):
                return
            
            answered_questions = page_data.get("answered_questions", [])
            
            for question in answered_questions:
                experience_id = f"scout_exp_{int(time.time())}_{uuid.uuid4().hex[:8]}"
                
                # 构建答案字符串
                answer_parts = []
                if question.get("selected_answers"):
                    answer_parts.extend(question["selected_answers"])
                if question.get("input_text"):
                    answer_parts.append(question["input_text"])
                
                answer_text = "; ".join(answer_parts) if answer_parts else "未回答"
                
                # 创建临时经验记录
                experience = TemporaryExperience(
                    experience_id=experience_id,
                    questionnaire_url=questionnaire_url,
                    question_content=question.get("question_text", ""),
                    correct_answer=answer_text,
                    wrong_answers=[],
                    answer_reasoning=f"敢死队成员{scout['name']}的答题选择",
                    digital_human_id=str(scout["id"]),
                    digital_human_profile=scout,
                    success=True,  # 假设敢死队完成了就是成功的
                    page_number=page_data.get("page_number", 1),
                    timestamp=datetime.now().isoformat()
                )
                
                await self.dual_kb.save_temporary_experience(experience)
            
            logger.info(f"✅ 敢死队成员 {scout['name']} 的经验已保存到知识库")
            
        except Exception as e:
            logger.warning(f"⚠️ 保存敢死队经验失败: {e}")
    
    async def _execute_analysis_stage(
        self,
        session_id: str,
        questionnaire_url: str,
        scout_results: List[Dict]
    ) -> Optional[QuestionnaireAnalysis]:
        """第二阶段：Gemini智能分析"""
        
        if not self.dual_kb:
            logger.warning("⚠️ 双知识库不可用，跳过智能分析")
            return None
        
        try:
            # 获取所有临时经验
            temp_experiences = await self.dual_kb.get_temporary_experiences(questionnaire_url)
            
            if not temp_experiences:
                logger.warning("⚠️ 没有可分析的敢死队经验")
                return None
            
            logger.info(f"📊 开始分析 {len(temp_experiences)} 条敢死队经验")
            
            # 调用Gemini进行智能分析
            analysis = await self.dual_kb.analyze_questionnaire_with_gemini(
                questionnaire_url, temp_experiences
            )
            
            if analysis:
                logger.info(f"✅ 智能分析完成，可信度: {analysis.analysis_confidence:.1%}")
                logger.info(f"   目标人群: {analysis.target_audience}")
                logger.info(f"   成功策略数量: {len(analysis.success_strategies)}")
                logger.info(f"   陷阱题目数量: {len(analysis.trap_questions)}")
                
                return analysis
            else:
                logger.warning("⚠️ 智能分析失败")
                return None
                
        except Exception as e:
            logger.error(f"❌ 智能分析阶段异常: {e}")
            return None
    
    async def _execute_recruitment_stage(
        self,
        session_id: str,
        analysis: QuestionnaireAnalysis,
        target_count: int
    ) -> List[Dict]:
        """第三阶段：大部队智能招募"""
        
        targets = []
        
        if analysis and self.xiaoshe_client:
            # 基于分析结果进行智能招募
            target_audience = analysis.target_audience
            age_range = target_audience.get("age_range", "25-35岁")
            occupations = target_audience.get("occupation", ["办公室职员"])
            
            logger.info(f"🎯 基于分析结果招募大部队：年龄{age_range}，职业{occupations}")
            
            # 70%相似 + 30%多样化策略
            similar_count = int(target_count * 0.7)
            diverse_count = target_count - similar_count
            
            # 招募相似成员
            for i in range(similar_count):
                occupation = occupations[i % len(occupations)]
                query = f"找一个{age_range}的{occupation}，适合填写问卷"
                persona = await self._query_xiaoshe_persona(query, f"target_similar_{i}")
                if persona:
                    targets.append(persona)
            
            # 招募多样化成员
            diverse_queries = [
                "找一个有不同背景的数字人",
                "找一个年龄稍有差异的数字人",
                "找一个不同收入水平的数字人"
            ]
            
            for i in range(diverse_count):
                query = diverse_queries[i % len(diverse_queries)]
                persona = await self._query_xiaoshe_persona(query, f"target_diverse_{i}")
                if persona:
                    targets.append(persona)
        
        # 备用方案：创建默认大部队成员
        while len(targets) < target_count:
            backup_target = self._create_backup_target(len(targets))
            targets.append(backup_target)
        
        logger.info(f"✅ 大部队招募完成：{len(targets)}人")
        return targets
    
    def _create_backup_target(self, index: int) -> Dict:
        """创建备用大部队成员"""
        target_profiles = [
            {"name": "刘小娟", "age": 29, "job": "会计", "income": "9000"},
            {"name": "周小伟", "age": 31, "job": "运营专员", "income": "11000"},
            {"name": "吴小萍", "age": 27, "job": "客服主管", "income": "7500"},
            {"name": "郑小强", "age": 33, "job": "项目经理", "income": "13000"},
            {"name": "黄小美", "age": 25, "job": "UI设计师", "income": "8500"}
        ]
        
        profile = target_profiles[index % len(target_profiles)]
        return {
            "id": f"backup_target_{index}",
            "name": profile["name"],
            "age": profile["age"],
            "job": profile["job"],
            "income": profile["income"],
            "description": f"大部队成员，{profile['job']}",
            "source": "backup_system"
        }
    
    async def _execute_parallel_target_stage(
        self,
        session_id: str,
        questionnaire_url: str,
        target_team: List[Dict],
        analysis: QuestionnaireAnalysis
    ) -> List[Dict]:
        """第四阶段：大部队并行作战"""
        
        # 1. 为每个大部队成员创建"新电脑"
        target_sessions = []
        for i, target in enumerate(target_team):
            try:
                session_id_target = await self.adspower_integration.create_adspower_browser_session(
                    target["id"], target["name"]
                )
                if session_id_target:
                    target_sessions.append({
                        "target": target,
                        "session_id": session_id_target,
                        "browser_ready": True
                    })
                    logger.info(f"✅ 大部队成员 {target['name']} 的'新电脑'准备就绪")
            except Exception as e:
                logger.error(f"❌ 为大部队成员 {target['name']} 创建'新电脑'失败: {e}")
        
        logger.info(f"📱 成功创建 {len(target_sessions)} 台'新电脑'，开始智能作战")
        
        # 2. 并行执行大部队任务
        tasks = []
        for target_session in target_sessions:
            task = self._execute_single_target_mission(
                session_id, questionnaire_url, target_session, analysis
            )
            tasks.append(task)
        
        # 等待所有大部队成员完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤成功的结果
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 大部队成员 {target_sessions[i]['target']['name']} 执行失败: {result}")
            elif result and result.get("success"):
                successful_results.append(result)
                logger.info(f"✅ 大部队成员 {target_sessions[i]['target']['name']} 完成任务")
        
        logger.info(f"📊 大部队阶段完成：{len(successful_results)}/{len(target_team)} 成功")
        
        return successful_results
    
    async def _execute_single_target_mission(
        self,
        session_id: str,
        questionnaire_url: str,
        target_session: Dict,
        analysis: QuestionnaireAnalysis
    ) -> Dict:
        """执行单个大部队成员的任务"""
        
        target = target_session["target"]
        session_id_target = target_session["session_id"]
        
        try:
            logger.info(f"🎯 大部队成员 {target['name']} 开始智能作战")
            
            # 获取浏览器信息
            browser_info = self.adspower_integration.get_session_info(session_id_target)
            if not browser_info:
                raise Exception("获取浏览器信息失败")
            
            existing_browser_info = {
                "profile_id": browser_info["profile_id"],
                "debug_port": browser_info["debug_port"],
                "proxy_enabled": browser_info["browser_env"].get("proxy_enabled", False)
            }
            
            # 生成智能指导提示词
            guided_prompt = None
            if self.dual_kb and analysis:
                guided_prompt = await self.dual_kb.generate_guidance_for_target_team(
                    questionnaire_url, target
                )
                logger.info(f"✅ 为 {target['name']} 生成智能指导：{len(guided_prompt)} 字符")
            
            # 执行问卷任务
            result = await self.adspower_integration.execute_questionnaire_task_with_data_extraction(
                persona_id=target["id"],
                persona_name=target["name"],
                digital_human_info=target,
                questionnaire_url=questionnaire_url,
                existing_browser_info=existing_browser_info,
                prompt=guided_prompt
            )
            
            if result.get("success"):
                logger.info(f"✅ 大部队成员 {target['name']} 智能作战完成")
                return {
                    "success": True,
                    "target": target,
                    "result": result,
                    "guided_prompt_used": bool(guided_prompt),
                    "execution_time": result.get("duration", 0)
                }
            else:
                logger.warning(f"⚠️ 大部队成员 {target['name']} 作战部分失败")
                return {
                    "success": False,
                    "target": target,
                    "error": result.get("error", "未知错误")
                }
                
        except Exception as e:
            logger.error(f"❌ 大部队成员 {target['name']} 作战异常: {e}")
            return {
                "success": False,
                "target": target,
                "error": str(e)
            }
    
    def _generate_final_report(
        self,
        session_id: str,
        scout_results: List[Dict],
        analysis: QuestionnaireAnalysis,
        target_results: List[Dict]
    ) -> Dict:
        """生成最终报告"""
        
        successful_scouts = [r for r in scout_results if r.get("success")]
        successful_targets = [r for r in target_results if r.get("success")]
        
        scout_success_rate = len(successful_scouts) / len(scout_results) if scout_results else 0
        target_success_rate = len(successful_targets) / len(target_results) if target_results else 0
        
        # 计算平均执行时间
        scout_avg_time = sum(r.get("execution_time", 0) for r in successful_scouts) / len(successful_scouts) if successful_scouts else 0
        target_avg_time = sum(r.get("execution_time", 0) for r in successful_targets) / len(successful_targets) if successful_targets else 0
        
        report = {
            "session_id": session_id,
            "execution_summary": {
                "total_participants": len(scout_results) + len(target_results),
                "scout_phase": {
                    "total": len(scout_results),
                    "successful": len(successful_scouts),
                    "success_rate": scout_success_rate,
                    "avg_execution_time": scout_avg_time
                },
                "target_phase": {
                    "total": len(target_results),
                    "successful": len(successful_targets),
                    "success_rate": target_success_rate,
                    "avg_execution_time": target_avg_time
                },
                "overall_success_rate": (len(successful_scouts) + len(successful_targets)) / (len(scout_results) + len(target_results)) if (scout_results or target_results) else 0
            },
            "analysis_summary": {
                "analysis_available": bool(analysis),
                "analysis_confidence": analysis.analysis_confidence if analysis else 0,
                "target_audience_identified": bool(analysis and analysis.target_audience),
                "strategies_generated": len(analysis.success_strategies) if analysis else 0,
                "trap_questions_identified": len(analysis.trap_questions) if analysis else 0
            },
            "technology_summary": {
                "workflow_type": "四阶段并行智能工作流",
                "browser_technology": "AdsPower + WebUI + 20窗口并行",
                "analysis_technology": "双知识库 + Gemini AI",
                "data_extraction": "HTML内容 + 答题结果抓取",
                "window_layout": "20窗口高密度平铺 (4行×5列)"
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def get_workflow_status(self, session_id: str) -> Optional[WorkflowStatus]:
        """获取工作流状态"""
        return self.active_workflows.get(session_id)
    
    def list_active_workflows(self) -> List[WorkflowStatus]:
        """列出所有活跃工作流"""
        return list(self.active_workflows.values())

# 便捷函数
async def run_four_stage_workflow(
    questionnaire_url: str,
    scout_count: int = 2,
    target_count: int = 5
) -> Dict[str, Any]:
    """运行四阶段并行工作流的便捷函数"""
    
    workflow = ParallelFourStageWorkflow()
    
    return await workflow.execute_complete_workflow(
        questionnaire_url=questionnaire_url,
        scout_count=scout_count,
        target_count=target_count
    )

# 测试代码
async def test_four_stage_workflow():
    """测试四阶段并行工作流"""
    print("🧪 测试四阶段并行工作流系统")
    
    test_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"
    
    result = await run_four_stage_workflow(
        questionnaire_url=test_url,
        scout_count=1,  # 测试模式：1个敢死队
        target_count=2  # 测试模式：2个大部队
    )
    
    print(f"执行结果: {'成功' if result.get('success') else '失败'}")
    if result.get("success"):
        report = result.get("final_report", {})
        execution_summary = report.get("execution_summary", {})
        print(f"总体成功率: {execution_summary.get('overall_success_rate', 0):.1%}")
        print(f"敢死队成功率: {execution_summary.get('scout_phase', {}).get('success_rate', 0):.1%}")
        print(f"大部队成功率: {execution_summary.get('target_phase', {}).get('success_rate', 0):.1%}")
    else:
        print(f"失败原因: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_four_stage_workflow()) 