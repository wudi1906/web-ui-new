#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第二阶段：敢死队自动化模块 - 增强版
实现真正的browser-use webui答题、详细知识库积累和经验分析
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import base64

# 导入第一阶段的核心模块
from questionnaire_system import (
    QuestionnaireManager, 
    DatabaseManager, 
    QuestionnaireKnowledgeBase,
    TaskStatus, 
    PersonaRole,
    DB_CONFIG
)
from enhanced_browser_use_integration import EnhancedBrowserUseIntegration
from questionnaire_system import XiaosheSystemClient

logger = logging.getLogger(__name__)

@dataclass
class ScoutMissionResult:
    """敢死队任务结果"""
    persona_id: int
    persona_name: str
    success: bool
    total_questions: int
    successful_answers: int
    total_time: float
    error_message: Optional[str] = None
    detailed_answers: List[Dict] = field(default_factory=list)
    session_summary: Dict = field(default_factory=dict)

class EnhancedScoutAutomationSystem:
    """增强的敢死队自动化系统"""
    
    def __init__(self):
        self.questionnaire_manager = QuestionnaireManager()
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.browser_use_integration = EnhancedBrowserUseIntegration(self.db_manager)
        self.scout_sessions = {}
        self.active_missions = {}
        
    async def start_enhanced_scout_mission(self, questionnaire_url: str, scout_count: int = 2) -> str:
        """启动增强的敢死队任务"""
        try:
            mission_id = f"enhanced_scout_mission_{int(time.time())}"
            
            logger.info(f"🚀 启动增强敢死队任务: {mission_id}")
            logger.info(f"📋 问卷URL: {questionnaire_url}")
            logger.info(f"👥 敢死队人数: {scout_count}")
            
            # 创建任务记录
            self.active_missions[mission_id] = {
                "mission_id": mission_id,
                "questionnaire_url": questionnaire_url,
                "scout_count": scout_count,
                "status": "preparing",
                "created_at": datetime.now().isoformat(),
                "scout_sessions": {},
                "results": []
            }
            
            # 获取敢死队人员配置
            scout_personas = await self._get_scout_personas(scout_count)
            
            # 为每个敢死队员创建独立的browser-use会话
            for i, persona in enumerate(scout_personas):
                try:
                    # 创建browser-use会话
                    session_id = await self.browser_use_integration.create_browser_session(
                        persona_info=persona,
                        browser_config={
                            "headless": False,  # 显示浏览器便于调试
                            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        }
                    )
                    
                    if not session_id:
                        logger.error(f"❌ 为 {persona['persona_name']} 创建browser-use会话失败")
                        continue
                    
                    # 保存会话信息
                    self.scout_sessions[persona["persona_id"]] = {
                        "persona": persona,
                        "session_id": session_id,
                        "status": "ready",
                        "created_at": time.time()
                    }
                    
                    logger.info(f"✅ {persona['persona_name']} 准备就绪")
                    
                except Exception as e:
                    logger.error(f"❌ 为 {persona['persona_name']} 准备环境失败: {e}")
                    continue
            
            if not self.scout_sessions:
                logger.error(f"❌ 没有成功准备的敢死队员")
                return ""
            
            # 更新任务状态
            self.active_missions[mission_id]["status"] = "ready"
            self.active_missions[mission_id]["scout_sessions"] = self.scout_sessions
            
            logger.info(f"✅ 敢死队任务准备完成: {len(self.scout_sessions)} 名队员就绪")
            return mission_id
            
        except Exception as e:
            logger.error(f"❌ 启动敢死队任务失败: {e}")
            return ""
    
    async def execute_enhanced_scout_answering(self, mission_id: str) -> Dict:
        """执行增强的敢死队答题"""
        try:
            if mission_id not in self.active_missions:
                logger.error(f"❌ 任务不存在: {mission_id}")
                return {"success": False, "error": "任务不存在"}
            
            mission = self.active_missions[mission_id]
            questionnaire_url = mission["questionnaire_url"]
            
            logger.info(f"📝 开始执行敢死队答题: {mission_id}")
            
            # 更新任务状态
            mission["status"] = "answering"
            
            # 并发执行所有敢死队员的答题任务
            scout_tasks = []
            for persona_id, session_info in self.scout_sessions.items():
                task = self._execute_single_scout_enhanced_answering(
                    mission_id, persona_id, session_info, questionnaire_url
                )
                scout_tasks.append(task)
            
            # 等待所有敢死队员完成答题
            scout_results = await asyncio.gather(*scout_tasks, return_exceptions=True)
            
            # 处理结果
            successful_results = []
            failed_results = []
            
            for result in scout_results:
                if isinstance(result, Exception):
                    logger.error(f"❌ 敢死队员答题异常: {result}")
                    failed_results.append({"error": str(result)})
                elif isinstance(result, ScoutMissionResult) and result.success:
                    successful_results.append(result)
                else:
                    failed_results.append(result)
            
            # 保存敢死队经验到知识库
            await self._save_enhanced_scout_experiences(mission_id, successful_results)
            
            # 更新任务状态
            mission["status"] = "completed"
            mission["results"] = successful_results + failed_results
            mission["completed_at"] = datetime.now().isoformat()
            
            result_summary = {
                "success": True,
                "mission_id": mission_id,
                "total_scouts": len(self.scout_sessions),
                "successful_scouts": len(successful_results),
                "failed_scouts": len(failed_results),
                "success_rate": len(successful_results) / len(self.scout_sessions) * 100 if self.scout_sessions else 0,
                "scout_results": successful_results + failed_results,
                "knowledge_accumulated": len(successful_results) > 0
            }
            
            logger.info(f"✅ 敢死队答题完成: 成功 {len(successful_results)}/{len(self.scout_sessions)} 人")
            
            return result_summary
            
        except Exception as e:
            logger.error(f"❌ 执行敢死队答题失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_single_scout_enhanced_answering(self, mission_id: str, persona_id: int, 
                                                     session_info: Dict, questionnaire_url: str) -> ScoutMissionResult:
        """执行单个敢死队员的增强答题"""
        try:
            persona = session_info["persona"]
            session_id = session_info["session_id"]
            persona_name = persona["persona_name"]
            
            logger.info(f"🎯 {persona_name} 开始答题")
            
            start_time = time.time()
            
            # 第一步：导航到问卷并分析页面
            logger.info(f"🌐 {persona_name} 导航到问卷页面")
            navigation_result = await self.browser_use_integration.navigate_and_analyze_questionnaire(
                session_id, questionnaire_url, mission_id
            )
            
            if not navigation_result.get("success"):
                error_msg = f"页面导航失败: {navigation_result.get('error', '未知错误')}"
                logger.error(f"❌ {persona_name} {error_msg}")
                return ScoutMissionResult(
                    persona_id=persona_id,
                    persona_name=persona_name,
                    success=False,
                    total_questions=0,
                    successful_answers=0,
                    total_time=time.time() - start_time,
                    error_message=error_msg
                )
            
            page_data = navigation_result.get("page_data", {})
            total_questions = len(page_data.get("questions", []))
            
            logger.info(f"📄 {persona_name} 页面分析完成，发现 {total_questions} 个问题")
            
            # 第二步：执行完整的问卷填写流程（使用新的方法）
            logger.info(f"✏️ {persona_name} 开始完整问卷填写")
            
            # 根据persona_id选择答题策略
            strategy = "conservative" if persona_id % 2 == 0 else "aggressive"
            
            # 使用新的完整问卷执行方法
            execution_result = await self.browser_use_integration.execute_complete_questionnaire(
                session_id, mission_id, strategy
            )
            
            if execution_result.get("success"):
                successful_answers = execution_result.get("successful_answers", 0)
                total_questions = execution_result.get("total_questions", 0)
                duration = execution_result.get("duration", 0.0)
                
                logger.info(f"📝 {persona_name} 答题完成: {successful_answers}/{total_questions} 题成功")
            else:
                successful_answers = 0
                total_questions = 0
                duration = time.time() - start_time
                logger.error(f"❌ {persona_name} 答题失败: {execution_result.get('error', '未知错误')}")
            
            # 第三步：获取会话总结
            session_summary = await self.browser_use_integration.get_session_summary(session_id)
            
            total_time = time.time() - start_time
            
            # 关闭browser-use会话
            await self.browser_use_integration.close_session(session_id)
            
            result = ScoutMissionResult(
                persona_id=persona_id,
                persona_name=persona_name,
                success=execution_result.get("success", False),
                total_questions=total_questions,
                successful_answers=successful_answers,
                total_time=total_time,
                detailed_answers=[{
                    "execution_result": execution_result,
                    "strategy": strategy,
                    "duration": duration
                }],
                session_summary=session_summary
            )
            
            logger.info(f"✅ {persona_name} 任务完成: 成功率 {successful_answers/total_questions*100:.1f}%" if total_questions > 0 else f"✅ {persona_name} 任务完成")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ {persona_name} 答题失败: {e}")
            return ScoutMissionResult(
                persona_id=persona_id,
                persona_name=persona.get("persona_name", f"Scout_{persona_id}"),
                success=False,
                total_questions=0,
                successful_answers=0,
                total_time=time.time() - start_time if 'start_time' in locals() else 0,
                error_message=str(e)
            )
    
    async def _get_scout_personas(self, scout_count: int) -> List[Dict]:
        """获取敢死队人员配置（增强版：调用小社会系统获取丰富信息）"""
        try:
            # 优先从小社会系统获取丰富的数字人信息
            logger.info(f"🔍 从小社会系统查询 {scout_count} 个敢死队数字人...")
            
            # 调用小社会系统
            xiaoshe_config = {
                "base_url": "http://localhost:5001",  # 修复：统一使用localhost:5001
                "timeout": 30
            }
            xiaoshe_client = XiaosheSystemClient(xiaoshe_config)
            query = f"找一些活跃的、不同背景的数字人来参与问卷调查，需要{scout_count}个人"
            
            xiaoshe_personas = await xiaoshe_client.query_personas(query, scout_count)
            
            if xiaoshe_personas and len(xiaoshe_personas) >= scout_count:
                logger.info(f"✅ 从小社会系统获取到 {len(xiaoshe_personas)} 个丰富数字人")
                
                # 转换为敢死队格式，保留所有丰富信息
                scout_personas = []
                for i, persona in enumerate(xiaoshe_personas[:scout_count]):
                    scout_personas.append({
                        "persona_id": persona.get("id", 1000 + i),
                        "persona_name": persona.get("name", f"敢死队员{i+1}"),
                        "background": persona  # 保留完整的小社会数据
                    })
                
                return scout_personas
            else:
                logger.warning(f"⚠️ 小社会系统返回数据不足，获取到 {len(xiaoshe_personas) if xiaoshe_personas else 0} 个")
            
        except Exception as e:
            logger.error(f"❌ 从小社会系统获取数字人失败: {e}")
        
        # 如果小社会系统失败，尝试从数据库获取
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT persona_id, persona_name, age, gender, occupation, 
                       personality_traits, background_story, preferences
                FROM digital_personas 
                WHERE is_active = 1 
                ORDER BY RAND() 
                LIMIT %s
                """, (scout_count,))
                
                personas = cursor.fetchall()
                
                if not personas:
                    logger.warning("⚠️ 数据库中没有找到数字人数据")
                    logger.info("📝 创建默认敢死队人员")
                    return self._create_default_scout_personas(scout_count)
                
                scout_personas = []
                for persona in personas:
                    scout_personas.append({
                        "persona_id": persona[0],
                        "persona_name": persona[1],
                        "background": {
                            "age": persona[2],
                            "gender": persona[3],
                            "occupation": persona[4],
                            "personality_traits": json.loads(persona[5]) if persona[5] else {},
                            "background_story": persona[6],
                            "preferences": json.loads(persona[7]) if persona[7] else {}
                        }
                    })
                
                return scout_personas
                
        except Exception as e:
            logger.error(f"❌ 获取敢死队人员配置失败: {e}")
            # 返回默认配置
            return self._create_default_scout_personas(scout_count)
        finally:
            if 'connection' in locals():
                connection.close()
    
    def _create_default_scout_personas(self, scout_count: int) -> List[Dict]:
        """创建默认的敢死队人员配置"""
        default_personas = [
            {
                "persona_id": 1001,
                "persona_name": "张小明",
                "background": {
                    "age": 28,
                    "gender": "男",
                    "occupation": "软件工程师",
                    "personality_traits": {"开朗": True, "细心": True},
                    "background_story": "热爱技术的程序员",
                    "preferences": {"科技": True, "游戏": True}
                }
            },
            {
                "persona_id": 1002,
                "persona_name": "李小红",
                "background": {
                    "age": 25,
                    "gender": "女",
                    "occupation": "市场专员",
                    "personality_traits": {"外向": True, "积极": True},
                    "background_story": "活泼的市场营销人员",
                    "preferences": {"购物": True, "旅游": True}
                }
            },
            {
                "persona_id": 1003,
                "persona_name": "王大力",
                "background": {
                    "age": 35,
                    "gender": "男",
                    "occupation": "销售经理",
                    "personality_traits": {"稳重": True, "负责": True},
                    "background_story": "经验丰富的销售管理者",
                    "preferences": {"运动": True, "读书": True}
                }
            }
        ]
        
        return default_personas[:scout_count]
    
    async def _save_enhanced_scout_experiences(self, mission_id: str, scout_results: List[ScoutMissionResult]):
        """保存增强的敢死队经验到知识库"""
        try:
            if not scout_results:
                logger.warning("⚠️ 没有成功的敢死队结果需要保存")
                return
            
            mission = self.active_missions.get(mission_id, {})
            questionnaire_url = mission.get("questionnaire_url", "")
            
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                for result in scout_results:
                    if not result.success:
                        continue
                    
                    # 保存整体会话经验
                    cursor.execute("""
                    INSERT INTO questionnaire_sessions 
                    (session_id, questionnaire_url, persona_id, persona_name,
                     total_questions, successful_answers, success_rate, total_time,
                     session_type, strategy_used, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        mission_id, questionnaire_url, result.persona_id, result.persona_name,
                        result.total_questions, result.successful_answers,
                        result.successful_answers / result.total_questions * 100 if result.total_questions > 0 else 0,
                        result.total_time, "enhanced_scout_mission",
                        "conservative" if result.persona_id % 2 == 0 else "aggressive",
                        datetime.now()
                    ))
                    
                    # 保存详细的执行记录
                    for detail in result.detailed_answers:
                        cursor.execute("""
                        INSERT INTO questionnaire_knowledge 
                        (session_id, questionnaire_url, persona_id, persona_name,
                         question_number, question_text, answer_choice, success,
                         time_taken, experience_type, strategy_used, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            mission_id, questionnaire_url, result.persona_id, result.persona_name,
                            1, "完整问卷执行", 
                            f"执行步骤: {detail.get('execution_result', {}).get('step_count', 0)}",
                            result.success, detail.get('duration', 0.0),
                            "enhanced_scout_experience", detail.get('strategy', 'unknown'),
                            datetime.now()
                        ))
                
                connection.commit()
                logger.info(f"✅ 敢死队经验已保存到知识库: {len(scout_results)} 个会话")
                
        except Exception as e:
            logger.error(f"❌ 保存敢死队经验失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()
    
    async def get_mission_status(self, mission_id: str) -> Dict:
        """获取任务状态"""
        if mission_id not in self.active_missions:
            return {"success": False, "error": "任务不存在"}
        
        mission = self.active_missions[mission_id]
        return {
            "success": True,
            "mission": mission
        }
    
    async def cleanup_scout_mission(self, mission_id: str):
        """清理敢死队任务"""
        try:
            if mission_id in self.active_missions:
                # 关闭所有browser-use会话
                for persona_id, session_info in self.scout_sessions.items():
                    session_id = session_info.get("session_id")
                    if session_id:
                        await self.browser_use_integration.close_session(session_id)
                
                # 清理任务记录
                del self.active_missions[mission_id]
                self.scout_sessions.clear()
                
                logger.info(f"✅ 敢死队任务清理完成: {mission_id}")
        except Exception as e:
            logger.error(f"❌ 清理敢死队任务失败: {e}")

# 保持向后兼容的类名
ScoutAutomationSystem = EnhancedScoutAutomationSystem

# 测试函数
async def test_scout_automation():
    """测试敢死队自动化系统"""
    print("🧪 测试敢死队自动化系统")
    print("="*50)
    
    system = ScoutAutomationSystem()
    
    try:
        # 1. 启动敢死队任务
        task_id = await system.start_enhanced_scout_mission(
            questionnaire_url="https://example.com/questionnaire",
            scout_count=2
        )
        
        if not task_id:
            print("❌ 敢死队任务启动失败")
            return
        
        print(f"✅ 敢死队任务启动成功: {task_id}")
        
        # 2. 执行敢死队答题
        results = await system.execute_enhanced_scout_answering(task_id)
        print(f"📊 敢死队答题结果: {results}")
        
        # 3. 分析结果
        analysis = await system.get_mission_status(task_id)
        print(f"📈 敢死队结果分析: {analysis}")
        
        # 4. 清理资源
        await system.cleanup_scout_mission(task_id)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        if 'task_id' in locals():
            await system.cleanup_scout_mission(task_id)

if __name__ == "__main__":
    asyncio.run(test_scout_automation()) 