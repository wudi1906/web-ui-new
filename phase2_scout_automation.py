#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第二阶段：敢死队自动化模块
实现2人敢死队自动答题、页面内容抓取和经验分析
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
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
from final_browser_isolation_system import FinalBrowserIsolationSystem

logger = logging.getLogger(__name__)

@dataclass
class QuestionInfo:
    """问题信息数据类"""
    question_number: int
    question_text: str
    question_type: str  # single_choice, multiple_choice, text_input, etc.
    options: List[str]
    required: bool = True
    page_screenshot: Optional[bytes] = None

@dataclass
class AnswerResult:
    """答题结果数据类"""
    question_number: int
    answer_choice: str
    success: bool
    error_message: Optional[str] = None
    time_taken: float = 0.0
    screenshot: Optional[bytes] = None

class BrowserUseIntegration:
    """Browser-use集成模块"""
    
    def __init__(self):
        self.browser_sessions = {}
        
    async def create_browser_session(self, browser_info: Dict) -> str:
        """创建browser-use会话"""
        try:
            # 这里集成browser-use库
            # 由于browser-use需要特定的安装和配置，我们先创建接口
            session_id = f"browser_session_{int(time.time())}"
            
            # 模拟browser-use会话创建
            self.browser_sessions[session_id] = {
                "browser_info": browser_info,
                "debug_port": browser_info.get('port'),
                "created_at": time.time(),
                "status": "active"
            }
            
            logger.info(f"✅ Browser-use会话创建成功: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Browser-use会话创建失败: {e}")
            return ""
    
    async def navigate_to_questionnaire(self, session_id: str, url: str) -> bool:
        """导航到问卷页面"""
        try:
            if session_id not in self.browser_sessions:
                logger.error(f"❌ 会话不存在: {session_id}")
                return False
            
            logger.info(f"🌐 导航到问卷: {url}")
            
            # 这里使用browser-use进行页面导航
            # 暂时模拟实现
            await asyncio.sleep(2)  # 模拟页面加载时间
            
            logger.info(f"✅ 页面导航成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 页面导航失败: {e}")
            return False
    
    async def extract_page_content(self, session_id: str) -> Dict:
        """提取页面内容"""
        try:
            if session_id not in self.browser_sessions:
                logger.error(f"❌ 会话不存在: {session_id}")
                return {}
            
            logger.info(f"📄 提取页面内容...")
            
            # 这里使用browser-use提取页面内容
            # 暂时模拟实现
            await asyncio.sleep(1)
            
            # 模拟提取的页面内容
            page_content = {
                "title": "问卷调查",
                "questions": [
                    {
                        "number": 1,
                        "text": "您的年龄段是？",
                        "type": "single_choice",
                        "options": ["18-25岁", "26-35岁", "36-45岁", "46岁以上"],
                        "required": True
                    },
                    {
                        "number": 2,
                        "text": "您的职业是？",
                        "type": "single_choice", 
                        "options": ["学生", "上班族", "自由职业", "其他"],
                        "required": True
                    }
                ],
                "current_page": 1,
                "total_pages": 1
            }
            
            logger.info(f"✅ 页面内容提取成功，发现 {len(page_content['questions'])} 个问题")
            return page_content
            
        except Exception as e:
            logger.error(f"❌ 页面内容提取失败: {e}")
            return {}
    
    async def take_screenshot(self, session_id: str) -> Optional[bytes]:
        """截取页面截图"""
        try:
            if session_id not in self.browser_sessions:
                logger.error(f"❌ 会话不存在: {session_id}")
                return None
            
            # 这里使用browser-use截图
            # 暂时模拟实现
            await asyncio.sleep(0.5)
            
            # 模拟截图数据
            screenshot_data = b"mock_screenshot_data"
            
            logger.info(f"📸 页面截图完成")
            return screenshot_data
            
        except Exception as e:
            logger.error(f"❌ 页面截图失败: {e}")
            return None
    
    async def answer_question(self, session_id: str, question: QuestionInfo, answer: str) -> AnswerResult:
        """回答问题"""
        try:
            if session_id not in self.browser_sessions:
                logger.error(f"❌ 会话不存在: {session_id}")
                return AnswerResult(
                    question_number=question.question_number,
                    answer_choice=answer,
                    success=False,
                    error_message="会话不存在"
                )
            
            start_time = time.time()
            logger.info(f"✏️ 回答问题 {question.question_number}: {answer}")
            
            # 这里使用browser-use进行自动答题
            # 暂时模拟实现
            await asyncio.sleep(1)  # 模拟答题时间
            
            # 模拟答题成功
            success = True
            error_message = None
            
            # 如果是模拟失败情况
            if "测试失败" in answer:
                success = False
                error_message = "选项不存在或页面元素未找到"
            
            time_taken = time.time() - start_time
            
            # 截取答题后的截图
            screenshot = await self.take_screenshot(session_id)
            
            result = AnswerResult(
                question_number=question.question_number,
                answer_choice=answer,
                success=success,
                error_message=error_message,
                time_taken=time_taken,
                screenshot=screenshot
            )
            
            if success:
                logger.info(f"✅ 问题 {question.question_number} 回答成功")
            else:
                logger.error(f"❌ 问题 {question.question_number} 回答失败: {error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 回答问题异常: {e}")
            return AnswerResult(
                question_number=question.question_number,
                answer_choice=answer,
                success=False,
                error_message=str(e)
            )
    
    async def submit_questionnaire(self, session_id: str) -> bool:
        """提交问卷"""
        try:
            if session_id not in self.browser_sessions:
                logger.error(f"❌ 会话不存在: {session_id}")
                return False
            
            logger.info(f"📤 提交问卷...")
            
            # 这里使用browser-use提交问卷
            # 暂时模拟实现
            await asyncio.sleep(2)  # 模拟提交时间
            
            logger.info(f"✅ 问卷提交成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 问卷提交失败: {e}")
            return False
    
    async def close_session(self, session_id: str):
        """关闭browser-use会话"""
        try:
            if session_id in self.browser_sessions:
                del self.browser_sessions[session_id]
                logger.info(f"✅ Browser-use会话已关闭: {session_id}")
        except Exception as e:
            logger.error(f"❌ 关闭会话失败: {e}")

class ScoutAnsweringStrategy:
    """敢死队答题策略"""
    
    def __init__(self):
        self.strategies = {
            "conservative": self._conservative_strategy,
            "aggressive": self._aggressive_strategy,
            "random": self._random_strategy
        }
    
    def _conservative_strategy(self, question: QuestionInfo, persona_info: Dict) -> str:
        """保守策略：选择最常见的选项"""
        if question.question_type == "single_choice" and question.options:
            # 选择第一个选项（通常是最保守的）
            return question.options[0]
        elif question.question_type == "text_input":
            return "不确定"
        return ""
    
    def _aggressive_strategy(self, question: QuestionInfo, persona_info: Dict) -> str:
        """激进策略：选择最特殊的选项"""
        if question.question_type == "single_choice" and question.options:
            # 选择最后一个选项（通常是"其他"类选项）
            return question.options[-1]
        elif question.question_type == "text_input":
            return "有特殊情况"
        return ""
    
    def _random_strategy(self, question: QuestionInfo, persona_info: Dict) -> str:
        """随机策略：随机选择选项"""
        import random
        if question.question_type == "single_choice" and question.options:
            return random.choice(question.options)
        elif question.question_type == "text_input":
            responses = ["还好", "一般", "不错", "很好", "不太好"]
            return random.choice(responses)
        return ""
    
    def get_answer(self, question: QuestionInfo, persona_info: Dict, strategy: str = "conservative") -> str:
        """根据策略获取答案"""
        if strategy in self.strategies:
            return self.strategies[strategy](question, persona_info)
        else:
            return self._conservative_strategy(question, persona_info)

class ScoutAutomationSystem:
    """敢死队自动化系统"""
    
    def __init__(self):
        self.questionnaire_manager = QuestionnaireManager()
        self.browser_system = FinalBrowserIsolationSystem()
        self.browser_use = BrowserUseIntegration()
        self.answering_strategy = ScoutAnsweringStrategy()
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.knowledge_base = QuestionnaireKnowledgeBase(self.db_manager)
        
        # 当前任务状态
        self.current_task = None
        self.scout_sessions = {}
    
    async def start_scout_mission(self, questionnaire_url: str, scout_count: int = 2) -> str:
        """启动敢死队任务"""
        try:
            logger.info(f"🚀 启动敢死队任务: {questionnaire_url}")
            
            # 1. 创建问卷任务
            task = await self.questionnaire_manager.create_questionnaire_task(
                url=questionnaire_url,
                scout_count=scout_count,
                target_count=0  # 敢死队阶段不需要目标团队
            )
            
            self.current_task = task
            logger.info(f"📋 任务创建成功: {task.task_id}")
            
            # 2. 选择敢死队成员
            scout_assignments = await self.questionnaire_manager.select_scout_team(task)
            logger.info(f"👥 选择了 {len(scout_assignments)} 个敢死队成员")
            
            # 3. 创建隔离浏览器环境
            browsers = await self.browser_system.create_isolated_browsers(len(scout_assignments))
            logger.info(f"🌐 创建了 {len(browsers)} 个隔离浏览器")
            
            # 4. 为每个敢死队成员分配浏览器和创建会话
            for i, assignment in enumerate(scout_assignments):
                if i < len(browsers):
                    browser = browsers[i]
                    
                    # 创建browser-use会话
                    session_id = await self.browser_use.create_browser_session(browser)
                    
                    self.scout_sessions[assignment.persona_id] = {
                        "assignment": assignment,
                        "browser": browser,
                        "session_id": session_id,
                        "status": "ready"
                    }
                    
                    logger.info(f"✅ 敢死队成员 {assignment.persona_name} 准备就绪")
            
            logger.info(f"🎯 敢死队任务启动完成，共 {len(self.scout_sessions)} 个成员")
            return task.task_id
            
        except Exception as e:
            logger.error(f"❌ 启动敢死队任务失败: {e}")
            return ""
    
    async def execute_scout_answering(self, task_id: str) -> Dict:
        """执行敢死队答题"""
        try:
            logger.info(f"🎯 开始执行敢死队答题任务: {task_id}")
            
            results = {
                "task_id": task_id,
                "scout_results": [],
                "success_count": 0,
                "failure_count": 0,
                "experiences": []
            }
            
            # 并发执行所有敢死队成员的答题
            tasks = []
            for persona_id, session_info in self.scout_sessions.items():
                task = self._execute_single_scout_answering(persona_id, session_info)
                tasks.append(task)
            
            # 等待所有敢死队成员完成答题
            scout_results = await asyncio.gather(*tasks, return_exceptions=True)
            
                         # 处理结果
            for i, result in enumerate(scout_results):
                if isinstance(result, Exception):
                    logger.error(f"❌ 敢死队成员答题异常: {result}")
                    results["failure_count"] += 1
                elif isinstance(result, dict):
                    results["scout_results"].append(result)
                    if result.get("success", False):
                        results["success_count"] += 1
                    else:
                        results["failure_count"] += 1
                    
                    # 收集经验
                    experiences = result.get("experiences", [])
                    if experiences:
                        results["experiences"].extend(experiences)
            
            # 保存经验到知识库
            await self._save_scout_experiences(results)
            
            logger.info(f"✅ 敢死队答题完成: 成功 {results['success_count']}, 失败 {results['failure_count']}")
            return results
            
        except Exception as e:
            logger.error(f"❌ 执行敢死队答题失败: {e}")
            return {"task_id": task_id, "error": str(e)}
    
    async def _execute_single_scout_answering(self, persona_id: int, session_info: Dict) -> Dict:
        """执行单个敢死队成员的答题"""
        try:
            assignment = session_info["assignment"]
            browser = session_info["browser"]
            session_id = session_info["session_id"]
            
            logger.info(f"👤 {assignment.persona_name} 开始答题...")
            
            result = {
                "persona_id": persona_id,
                "persona_name": assignment.persona_name,
                "success": False,
                "answers": [],
                "experiences": [],
                "error_message": None
            }
            
                         # 1. 导航到问卷页面
            if not self.current_task:
                result["error_message"] = "当前任务不存在"
                return result
                
            if not await self.browser_use.navigate_to_questionnaire(session_id, self.current_task.url):
                result["error_message"] = "页面导航失败"
                return result
            
            # 2. 提取页面内容
            page_content = await self.browser_use.extract_page_content(session_id)
            if not page_content:
                result["error_message"] = "页面内容提取失败"
                return result
            
            # 3. 逐个回答问题
            all_success = True
            for question_data in page_content.get("questions", []):
                question = QuestionInfo(
                    question_number=question_data["number"],
                    question_text=question_data["text"],
                    question_type=question_data["type"],
                    options=question_data["options"],
                    required=question_data.get("required", True)
                )
                
                # 保存问题内容到知识库
                self.knowledge_base.save_question_content(
                    session_id=self.current_task.session_id,
                    questionnaire_url=self.current_task.url,
                    question_content=question.question_text,
                    question_type=question.question_type,
                    question_number=question.question_number,
                    persona_id=persona_id,
                    persona_role=PersonaRole.SCOUT
                )
                
                # 根据策略选择答案
                strategy = "conservative" if persona_id % 2 == 0 else "aggressive"
                answer = self.answering_strategy.get_answer(question, assignment.__dict__, strategy)
                
                # 执行答题
                answer_result = await self.browser_use.answer_question(session_id, question, answer)
                result["answers"].append(answer_result.__dict__)
                
                if not answer_result.success:
                    all_success = False
                
                # 保存答题经验
                experience_desc = f"策略: {strategy}, 问题类型: {question.question_type}, 答案: {answer}"
                if answer_result.success:
                    experience_desc += ", 成功"
                else:
                    experience_desc += f", 失败: {answer_result.error_message}"
                
                self.knowledge_base.save_answer_experience(
                    session_id=self.current_task.session_id,
                    questionnaire_url=self.current_task.url,
                    persona_id=persona_id,
                    answer_choice=answer,
                    success=answer_result.success,
                    experience_description=experience_desc
                )
                
                result["experiences"].append({
                    "question_number": question.question_number,
                    "strategy": strategy,
                    "answer": answer,
                    "success": answer_result.success,
                    "description": experience_desc
                })
            
            # 4. 提交问卷
            if all_success:
                submit_success = await self.browser_use.submit_questionnaire(session_id)
                result["success"] = submit_success
                if not submit_success:
                    result["error_message"] = "问卷提交失败"
            else:
                result["error_message"] = "部分问题回答失败"
            
            if result["success"]:
                logger.info(f"✅ {assignment.persona_name} 答题成功")
            else:
                logger.error(f"❌ {assignment.persona_name} 答题失败: {result['error_message']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ {assignment.persona_name} 答题异常: {e}")
            return {
                "persona_id": persona_id,
                "persona_name": assignment.persona_name,
                "success": False,
                "error_message": str(e),
                "answers": [],
                "experiences": []
            }
    
    async def _save_scout_experiences(self, results: Dict):
        """保存敢死队经验到知识库"""
        try:
            logger.info(f"💾 保存敢死队经验到知识库...")
            
            # 这里可以进一步分析和处理经验数据
            # 例如：识别成功模式、失败原因等
            
            logger.info(f"✅ 敢死队经验保存完成")
            
        except Exception as e:
            logger.error(f"❌ 保存敢死队经验失败: {e}")
    
    async def analyze_scout_results(self, task_id: str) -> Dict:
        """分析敢死队结果"""
        try:
            logger.info(f"📊 分析敢死队结果: {task_id}")
            
            # 从知识库获取经验数据
            analysis = self.knowledge_base.analyze_questionnaire_requirements(
                session_id=self.current_task.session_id,
                questionnaire_url=self.current_task.url
            )
            
            logger.info(f"✅ 敢死队结果分析完成")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ 分析敢死队结果失败: {e}")
            return {}
    
    async def cleanup_scout_mission(self):
        """清理敢死队任务资源"""
        try:
            logger.info(f"🧹 清理敢死队任务资源...")
            
            # 关闭所有browser-use会话
            for persona_id, session_info in self.scout_sessions.items():
                await self.browser_use.close_session(session_info["session_id"])
            
            # 清理浏览器环境
            await self.browser_system.cleanup_browsers()
            
            # 清理任务状态
            self.scout_sessions.clear()
            self.current_task = None
            
            logger.info(f"✅ 敢死队任务资源清理完成")
            
        except Exception as e:
            logger.error(f"❌ 清理敢死队任务资源失败: {e}")

# 测试函数
async def test_scout_automation():
    """测试敢死队自动化系统"""
    print("🧪 测试敢死队自动化系统")
    print("="*50)
    
    system = ScoutAutomationSystem()
    
    try:
        # 1. 启动敢死队任务
        task_id = await system.start_scout_mission(
            questionnaire_url="https://example.com/questionnaire",
            scout_count=2
        )
        
        if not task_id:
            print("❌ 敢死队任务启动失败")
            return
        
        print(f"✅ 敢死队任务启动成功: {task_id}")
        
        # 2. 执行敢死队答题
        results = await system.execute_scout_answering(task_id)
        print(f"📊 敢死队答题结果: {results}")
        
        # 3. 分析结果
        analysis = await system.analyze_scout_results(task_id)
        print(f"📈 敢死队结果分析: {analysis}")
        
        # 4. 清理资源
        await system.cleanup_scout_mission()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        await system.cleanup_scout_mission()

if __name__ == "__main__":
    asyncio.run(test_scout_automation()) 