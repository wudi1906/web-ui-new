#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版问卷自动填写系统 - 集成智能知识库
实现：敢死队经验收集 -> 智能分析 -> 大部队指导应用
"""

import asyncio
import argparse
import json
import pymysql
import pymysql.cursors
import time
import sys
import os
import base64
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

# 导入所需模块
try:
    from browser_use import Browser, BrowserConfig, Agent
    from browser_use.browser.context import BrowserContextConfig
    from langchain_google_genai import ChatGoogleGenerativeAI
    from intelligent_knowledge_base import (
        IntelligentKnowledgeBase, 
        AnswerExperience, 
        QuestionType, 
        PageContent
    )
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装必要的依赖")
    sys.exit(1)

from testWenjuanFinal import (
    DB_CONFIG, 
    get_digital_human_by_id, 
    generate_detailed_person_description,
    get_llm
)
from config import get_config

# 配置日志
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedQuestionnaireAgent:
    """增强版问卷代理 - 集成智能知识库"""
    
    def __init__(self, session_id: str, questionnaire_url: str, is_scout: bool = False):
        self.session_id = session_id
        self.questionnaire_url = questionnaire_url
        self.is_scout = is_scout  # 是否为敢死队成员
        self.knowledge_base = IntelligentKnowledgeBase()
        self.page_counter = 0
        self.experiences = []  # 存储答题经验
        
    async def run_questionnaire_with_knowledge(self, digital_human: Dict[str, Any],
                                             model_type: str = "gemini",
                                             model_name: str = "gemini-2.0-flash",
                                             api_key: Optional[str] = None,
                                             temperature: float = 0.5,
                                             max_retries: int = 5) -> Dict:
        """运行带知识库的问卷填写"""
        try:
            logger.info(f"🚀 开始{'敢死队' if self.is_scout else '大部队'}问卷填写")
            logger.info(f"👤 数字人: {digital_human['name']}")
            
            # 生成基础提示词
            base_prompt = self._generate_base_prompt(digital_human)
            
            # 如果是大部队，获取敢死队的指导经验
            guidance_text = ""
            if not self.is_scout:
                guidance_text = await self.knowledge_base.get_guidance_for_target_team(
                    self.session_id, self.questionnaire_url, digital_human
                )
                logger.info(f"📚 获取到指导经验: {len(guidance_text)} 字符")
            
            # 组合完整提示词
            complete_prompt = self._combine_prompt_with_guidance(base_prompt, guidance_text)
            
            # 创建浏览器配置
            browser_config = BrowserConfig(
                headless=False,
                disable_security=True,
                extra_chromium_args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ]
            )
            
            # 创建LLM
            llm = get_llm(model_type, model_name, api_key, temperature)
            if not llm:
                raise Exception("LLM初始化失败")
            
            # 创建代理
            agent = Agent(
                task=complete_prompt,
                llm=llm,
                browser_config=browser_config,
                max_actions_per_step=20,
                max_steps=500
            )
            
            # 执行任务
            start_time = time.time()
            
            # 如果是敢死队，启用经验收集模式
            if self.is_scout:
                result = await self._run_with_experience_collection(agent)
            else:
                result = await agent.run(self.questionnaire_url)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 处理结果
            success = self._evaluate_success(result)
            
            # 保存会话记录
            await self._save_session_record(digital_human, success, duration)
            
            # 如果是敢死队且成功，分析经验并生成指导
            if self.is_scout and success and self.experiences:
                await self._analyze_and_generate_guidance()
            
            logger.info(f"✅ 问卷填写完成: {'成功' if success else '失败'}, 用时: {duration:.2f}秒")
            
            return {
                "success": success,
                "duration": duration,
                "experiences_count": len(self.experiences),
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ 问卷填写失败: {e}")
            return {
                "success": False,
                "duration": 0,
                "error": str(e)
            }
    
    def _generate_base_prompt(self, digital_human: Dict[str, Any]) -> str:
        """生成基础提示词"""
        person_description = generate_detailed_person_description(digital_human)
        
        base_prompt = f"""
你现在需要扮演一个真实的人来填写问卷调查。

{person_description}

请按照以下要求填写问卷：

1. 【角色扮演】
   - 完全按照上述人物设定来思考和回答
   - 答案要符合你的年龄、性别、职业、居住地等特征
   - 保持角色的一致性，不要出戏

2. 【答题策略】
   - 仔细阅读每个问题，理解题意
   - 根据你的人物设定选择最合适的答案
   - 对于个人信息类问题，严格按照设定回答
   - 对于观点态度类问题，要符合你的身份特征

3. 【操作要求】
   - 逐页填写，不要跳过任何问题
   - 填写完当前页面后，点击"下一页"或"提交"按钮
   - 如果遇到必填项提示，请检查并补充遗漏的答案
   - 确保问卷完全提交成功

4. 【注意事项】
   - 答题速度要自然，不要过快或过慢
   - 遇到不确定的问题，选择最符合你身份的选项
   - 保持耐心，完成整个问卷流程
"""
        
        if self.is_scout:
            base_prompt += """
5. 【敢死队特殊任务】
   - 你是敢死队成员，需要为后续的大部队积累经验
   - 在答题过程中要特别注意页面结构和问题类型
   - 记录你的答题选择和理由，为其他数字人提供参考
"""
        
        return base_prompt
    
    def _combine_prompt_with_guidance(self, base_prompt: str, guidance_text: str) -> str:
        """组合基础提示词和指导经验"""
        if not guidance_text:
            return base_prompt
        
        return f"""
{base_prompt}

{guidance_text}

请特别注意上述答题指导经验，这些是基于之前成功案例总结的宝贵经验。
在遇到相似问题时，优先参考这些指导建议。
"""
    
    async def _run_with_experience_collection(self, agent) -> Any:
        """运行敢死队模式，收集答题经验"""
        logger.info("🔍 启动敢死队经验收集模式")
        
        # 重写agent的step方法来收集经验
        original_step = agent.step
        
        async def enhanced_step(*args, **kwargs):
            # 执行原始步骤
            result = await original_step(*args, **kwargs)
            
            # 收集页面信息和答题经验
            try:
                await self._collect_page_experience(agent)
            except Exception as e:
                logger.warning(f"⚠️ 收集经验失败: {e}")
            
            return result
        
        # 替换step方法
        agent.step = enhanced_step
        
        # 执行任务
        return await agent.run(self.questionnaire_url)
    
    async def _collect_page_experience(self, agent):
        """收集页面经验"""
        try:
            # 获取当前页面信息
            browser = agent.browser
            if not browser or not browser.page:
                return
            
            # 获取页面截图和HTML
            screenshot = await browser.page.screenshot(type="png")
            screenshot_base64 = base64.b64encode(screenshot).decode()
            html_content = await browser.page.content()
            current_url = browser.page.url
            
            self.page_counter += 1
            
            # 使用知识库分析页面内容
            page_content = await self.knowledge_base.capture_page_content(
                self.session_id, self.page_counter, screenshot_base64, html_content, current_url
            )
            
            # 模拟答题经验收集（这里需要根据实际情况调整）
            # 在实际实现中，需要监控用户的选择行为
            await self._simulate_answer_experience_collection(page_content)
            
        except Exception as e:
            logger.error(f"❌ 收集页面经验失败: {e}")
    
    async def _simulate_answer_experience_collection(self, page_content: PageContent):
        """模拟答题经验收集（实际实现中需要监控真实的用户选择）"""
        try:
            # 这里是模拟实现，实际中需要监控browser-use的选择行为
            for question in page_content.questions:
                if question.get("options"):
                    # 模拟选择了第一个选项
                    chosen_answer = question["options"][0] if question["options"] else "未知"
                    
                    experience = AnswerExperience(
                        persona_id=1,  # 实际中从digital_human获取
                        persona_name="敢死队成员",  # 实际中从digital_human获取
                        persona_features={"age": 30, "gender": "未知", "profession": "未知"},
                        question_content=question.get("question_text", ""),
                        question_type=QuestionType(question.get("question_type", "unknown")),
                        available_options=question.get("options", []),
                        chosen_answer=chosen_answer,
                        success=True,  # 假设成功
                        reasoning=f"根据角色特征选择了{chosen_answer}"
                    )
                    
                    # 保存经验到知识库
                    await self.knowledge_base.save_answer_experience(
                        self.session_id, self.questionnaire_url, experience
                    )
                    
                    self.experiences.append(experience)
                    
        except Exception as e:
            logger.error(f"❌ 模拟答题经验收集失败: {e}")
    
    async def _analyze_and_generate_guidance(self):
        """分析敢死队经验并生成指导规则"""
        try:
            logger.info("🧠 开始分析敢死队经验并生成指导规则")
            
            guidance_rules = await self.knowledge_base.analyze_experiences_and_generate_guidance(
                self.session_id, self.questionnaire_url
            )
            
            logger.info(f"✅ 生成了 {len(guidance_rules)} 条指导规则")
            
        except Exception as e:
            logger.error(f"❌ 分析经验并生成指导失败: {e}")
    
    def _evaluate_success(self, result) -> bool:
        """评估问卷填写是否成功"""
        # 这里需要根据实际的result结构来判断
        # 简单实现：如果没有异常就认为成功
        try:
            if hasattr(result, 'success'):
                return result.success
            elif hasattr(result, 'status'):
                return result.status == 'success'
            else:
                # 默认认为成功（可以根据需要调整）
                return True
        except:
            return False
    
    async def _save_session_record(self, digital_human: Dict[str, Any], 
                                 success: bool, duration: float):
        """保存会话记录"""
        try:
            connection = pymysql.connect(**DB_CONFIG)
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO questionnaire_sessions 
                (session_id, questionnaire_url, persona_id, persona_name,
                 total_questions, successful_answers, success_rate, total_time,
                 session_type, strategy_used, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(sql, (
                    self.session_id,
                    self.questionnaire_url,
                    digital_human.get('id', 0),
                    digital_human.get('name', '未知'),
                    len(self.experiences),
                    len([exp for exp in self.experiences if exp.success]),
                    100.0 if success else 0.0,
                    duration,
                    "scout" if self.is_scout else "target",
                    "enhanced_with_knowledge",
                    datetime.now()
                ))
                connection.commit()
                
        except Exception as e:
            logger.error(f"❌ 保存会话记录失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()

async def run_enhanced_questionnaire_task(questionnaire_url: str, 
                                        digital_human_id: int,
                                        is_scout: bool = False,
                                        model_type: str = "gemini",
                                        model_name: str = "gemini-2.0-flash",
                                        api_key: Optional[str] = None) -> Dict:
    """运行增强版问卷任务"""
    try:
        # 获取数字人信息
        digital_human = get_digital_human_by_id(digital_human_id)
        if not digital_human:
            raise Exception(f"未找到ID为{digital_human_id}的数字人")
        
        # 生成会话ID
        session_id = f"enhanced_{int(time.time())}_{digital_human_id}"
        
        # 创建增强代理
        agent = EnhancedQuestionnaireAgent(session_id, questionnaire_url, is_scout)
        
        # 执行任务
        result = await agent.run_questionnaire_with_knowledge(
            digital_human, model_type, model_name, api_key
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 运行增强问卷任务失败: {e}")
        return {"success": False, "error": str(e)}

async def run_scout_team(questionnaire_url: str, scout_ids: List[int]) -> Dict:
    """运行敢死队"""
    logger.info(f"🚀 启动敢死队，成员数量: {len(scout_ids)}")
    
    results = []
    for scout_id in scout_ids:
        logger.info(f"👤 敢死队成员 {scout_id} 开始执行任务")
        
        result = await run_enhanced_questionnaire_task(
            questionnaire_url, scout_id, is_scout=True
        )
        
        results.append({
            "scout_id": scout_id,
            "result": result
        })
        
        # 间隔执行
        await asyncio.sleep(5)
    
    successful_scouts = sum(1 for r in results if r["result"]["success"])
    
    logger.info(f"🎉 敢死队任务完成: {successful_scouts}/{len(scout_ids)} 成功")
    
    return {
        "success": successful_scouts > 0,
        "total_scouts": len(scout_ids),
        "successful_scouts": successful_scouts,
        "results": results
    }

async def run_target_team(questionnaire_url: str, target_ids: List[int]) -> Dict:
    """运行大部队"""
    logger.info(f"🚀 启动大部队，成员数量: {len(target_ids)}")
    
    results = []
    for target_id in target_ids:
        logger.info(f"👤 大部队成员 {target_id} 开始执行任务")
        
        result = await run_enhanced_questionnaire_task(
            questionnaire_url, target_id, is_scout=False
        )
        
        results.append({
            "target_id": target_id,
            "result": result
        })
        
        # 间隔执行
        await asyncio.sleep(3)
    
    successful_targets = sum(1 for r in results if r["result"]["success"])
    
    logger.info(f"🎉 大部队任务完成: {successful_targets}/{len(target_ids)} 成功")
    
    return {
        "success": successful_targets > 0,
        "total_targets": len(target_ids),
        "successful_targets": successful_targets,
        "results": results
    }

async def run_complete_enhanced_workflow(questionnaire_url: str,
                                       scout_ids: List[int] = [1, 2],
                                       target_ids: List[int] = [3, 4, 5]) -> Dict:
    """运行完整的增强工作流：敢死队 -> 分析 -> 大部队"""
    logger.info("🚀 启动完整增强工作流")
    
    try:
        # 阶段1: 敢死队探路
        logger.info("📍 阶段1: 敢死队探路")
        scout_result = await run_scout_team(questionnaire_url, scout_ids)
        
        if not scout_result["success"]:
            logger.error("❌ 敢死队任务失败，终止流程")
            return {"success": False, "error": "敢死队任务失败"}
        
        # 等待一段时间让知识库分析完成
        logger.info("⏳ 等待知识库分析...")
        await asyncio.sleep(10)
        
        # 阶段2: 大部队执行
        logger.info("📍 阶段2: 大部队执行")
        target_result = await run_target_team(questionnaire_url, target_ids)
        
        # 汇总结果
        total_success = scout_result["successful_scouts"] + target_result["successful_targets"]
        total_count = scout_result["total_scouts"] + target_result["total_targets"]
        
        logger.info(f"🎉 完整工作流完成: {total_success}/{total_count} 成功")
        
        return {
            "success": True,
            "scout_result": scout_result,
            "target_result": target_result,
            "total_success": total_success,
            "total_count": total_count,
            "success_rate": total_success / total_count if total_count > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"❌ 完整工作流失败: {e}")
        return {"success": False, "error": str(e)}

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="增强版问卷自动填写系统")
    parser.add_argument("--url", type=str, required=True, help="问卷URL")
    parser.add_argument("--mode", type=str, choices=["scout", "target", "complete"], 
                       default="complete", help="运行模式")
    parser.add_argument("--scout-ids", type=str, default="1,2", 
                       help="敢死队成员ID，逗号分隔")
    parser.add_argument("--target-ids", type=str, default="3,4,5", 
                       help="大部队成员ID，逗号分隔")
    
    args = parser.parse_args()
    
    # 解析ID列表
    scout_ids = [int(x.strip()) for x in args.scout_ids.split(",")]
    target_ids = [int(x.strip()) for x in args.target_ids.split(",")]
    
    print("🤖 增强版问卷自动填写系统")
    print("=" * 50)
    print(f"问卷URL: {args.url}")
    print(f"运行模式: {args.mode}")
    print(f"敢死队: {scout_ids}")
    print(f"大部队: {target_ids}")
    print("=" * 50)
    
    # 设置API密钥
    llm_config = get_config("llm")
    if llm_config and llm_config.get("api_key"):
        os.environ["GOOGLE_API_KEY"] = llm_config["api_key"]
    
    # 运行任务
    if args.mode == "scout":
        result = asyncio.run(run_scout_team(args.url, scout_ids))
    elif args.mode == "target":
        result = asyncio.run(run_target_team(args.url, target_ids))
    else:  # complete
        result = asyncio.run(run_complete_enhanced_workflow(args.url, scout_ids, target_ids))
    
    # 显示结果
    print("\n🎉 任务执行完成!")
    print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    main() 