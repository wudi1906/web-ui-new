#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷自动填写系统 - 集成知识库版本
实现：敢死队经验收集 -> 智能分析 -> 大部队指导应用
基于run_questionnaire_with_testWenjuanFinal.py增强
"""

import asyncio
import logging
import time
import json
import requests
import os
from datetime import datetime
from typing import Dict, List, Optional

# 导入testWenjuanFinal.py的方法
from testWenjuanFinal import run_browser_task, generate_detailed_person_description, generate_complete_prompt
from questionnaire_system import DatabaseManager, DB_CONFIG
from config import get_config

# 尝试导入智能知识库
try:
    from intelligent_knowledge_base import (
        IntelligentKnowledgeBase,
        AnswerExperience,
        QuestionType
    )
    KNOWLEDGE_BASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 智能知识库模块导入失败: {e}")
    KNOWLEDGE_BASE_AVAILABLE = False

# 设置Gemini API密钥环境变量
llm_config = get_config("llm")
if llm_config and llm_config.get("api_key"):
    os.environ["GOOGLE_API_KEY"] = llm_config["api_key"]
    print(f"✅ 已设置Gemini API密钥: {llm_config['api_key'][:20]}...")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'enhanced_questionnaire_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedQuestionnaireSystem:
    """增强版问卷系统 - 集成智能知识库"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.active_tasks = {}
        
        # 初始化智能知识库
        if KNOWLEDGE_BASE_AVAILABLE:
            self.knowledge_base = IntelligentKnowledgeBase()
            logger.info("✅ 智能知识库初始化成功")
        else:
            self.knowledge_base = None
            logger.warning("⚠️ 智能知识库不可用，将使用基础模式")
    
    async def run_scout_team(self, questionnaire_url: str, scout_count: int = 2) -> Dict:
        """运行敢死队，收集经验"""
        logger.info(f"🚀 启动敢死队，目标收集经验")
        logger.info(f"📋 问卷URL: {questionnaire_url}")
        logger.info(f"👥 敢死队数量: {scout_count}")
        
        try:
            # 获取敢死队成员
            scouts = await self._get_suitable_personas(scout_count, is_scout=True)
            
            if not scouts:
                logger.error("❌ 没有找到合适的敢死队成员")
                return {"success": False, "error": "没有找到合适的敢死队成员"}
            
            logger.info(f"✅ 找到 {len(scouts)} 个敢死队成员")
            
            # 生成会话ID
            session_id = f"scout_{int(time.time())}"
            
            # 执行敢死队任务
            results = []
            
            for i, scout in enumerate(scouts):
                logger.info(f"👤 敢死队成员 {i+1}/{len(scouts)}: {scout['persona_name']}")
                
                try:
                    # 转换为testWenjuanFinal.py期望的格式
                    digital_human_data = self._convert_persona_to_digital_human(scout)
                    
                    # 生成敢死队专用提示词
                    scout_prompt = self._generate_scout_prompt(digital_human_data)
                    
                    logger.info(f"📝 {scout['persona_name']} 开始敢死队任务")
                    
                    # 执行任务
                    start_time = time.time()
                    
                    await run_browser_task(
                        url=questionnaire_url,
                        prompt=scout_prompt,
                        formatted_prompt=scout_prompt,
                        model_type="gemini",
                        model_name=llm_config.get("model", "gemini-2.0-flash"),
                        api_key=llm_config.get("api_key"),
                        temperature=llm_config.get("temperature", 0.5),
                        base_url=None,
                        auto_close=False,
                        disable_memory=True,
                        max_retries=5,
                        retry_delay=5,
                        headless=False
                    )
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    logger.info(f"✅ {scout['persona_name']} 敢死队任务完成，用时: {duration:.2f}秒")
                    
                    # 模拟保存经验到知识库
                    if self.knowledge_base:
                        await self._save_scout_experience(session_id, questionnaire_url, scout, True)
                    
                    # 保存执行记录
                    await self._save_execution_record(scout, questionnaire_url, True, duration, None, "scout")
                    
                    results.append({
                        "persona_name": scout['persona_name'],
                        "persona_id": scout['persona_id'],
                        "success": True,
                        "duration": duration,
                        "error": None
                    })
                    
                except Exception as e:
                    logger.error(f"❌ {scout['persona_name']} 敢死队任务失败: {e}")
                    
                    # 保存失败记录
                    await self._save_execution_record(scout, questionnaire_url, False, 0, str(e), "scout")
                    
                    results.append({
                        "persona_name": scout['persona_name'],
                        "persona_id": scout['persona_id'],
                        "success": False,
                        "duration": 0,
                        "error": str(e)
                    })
                
                # 间隔执行
                if i < len(scouts) - 1:
                    logger.info("⏳ 等待5秒后处理下一个敢死队成员...")
                    await asyncio.sleep(5)
            
            # 统计结果
            successful_count = sum(1 for r in results if r["success"])
            success_rate = successful_count / len(results) if results else 0
            
            logger.info(f"🎉 敢死队任务完成!")
            logger.info(f"📊 成功率: {successful_count}/{len(results)} ({success_rate*100:.1f}%)")
            
            # 如果有成功的敢死队，分析经验并生成指导
            if successful_count > 0 and self.knowledge_base:
                logger.info("🧠 开始分析敢死队经验...")
                await self._analyze_scout_experiences(session_id, questionnaire_url)
            
            return {
                "success": successful_count > 0,
                "session_id": session_id,
                "total_count": len(results),
                "successful_count": successful_count,
                "success_rate": success_rate,
                "results": results,
                "questionnaire_url": questionnaire_url
            }
            
        except Exception as e:
            logger.error(f"❌ 敢死队任务失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_target_team(self, questionnaire_url: str, scout_session_id: str, 
                            target_count: int = 5) -> Dict:
        """运行大部队，应用敢死队经验"""
        logger.info(f"🚀 启动大部队，应用敢死队经验")
        logger.info(f"📋 问卷URL: {questionnaire_url}")
        logger.info(f"🎯 大部队数量: {target_count}")
        logger.info(f"📚 敢死队会话ID: {scout_session_id}")
        
        try:
            # 获取大部队成员
            targets = await self._get_suitable_personas(target_count, is_scout=False)
            
            if not targets:
                logger.error("❌ 没有找到合适的大部队成员")
                return {"success": False, "error": "没有找到合适的大部队成员"}
            
            logger.info(f"✅ 找到 {len(targets)} 个大部队成员")
            
            # 执行大部队任务
            results = []
            
            for i, target in enumerate(targets):
                logger.info(f"👤 大部队成员 {i+1}/{len(targets)}: {target['persona_name']}")
                
                try:
                    # 转换为testWenjuanFinal.py期望的格式
                    digital_human_data = self._convert_persona_to_digital_human(target)
                    
                    # 生成带指导经验的提示词
                    enhanced_prompt = await self._generate_enhanced_prompt(
                        digital_human_data, scout_session_id, questionnaire_url
                    )
                    
                    logger.info(f"📝 {target['persona_name']} 开始大部队任务")
                    
                    # 执行任务
                    start_time = time.time()
                    
                    await run_browser_task(
                        url=questionnaire_url,
                        prompt=enhanced_prompt,
                        formatted_prompt=enhanced_prompt,
                        model_type="gemini",
                        model_name=llm_config.get("model", "gemini-2.0-flash"),
                        api_key=llm_config.get("api_key"),
                        temperature=llm_config.get("temperature", 0.5),
                        base_url=None,
                        auto_close=False,
                        disable_memory=True,
                        max_retries=5,
                        retry_delay=5,
                        headless=False
                    )
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    logger.info(f"✅ {target['persona_name']} 大部队任务完成，用时: {duration:.2f}秒")
                    
                    # 保存执行记录
                    await self._save_execution_record(target, questionnaire_url, True, duration, None, "target")
                    
                    results.append({
                        "persona_name": target['persona_name'],
                        "persona_id": target['persona_id'],
                        "success": True,
                        "duration": duration,
                        "error": None
                    })
                    
                except Exception as e:
                    logger.error(f"❌ {target['persona_name']} 大部队任务失败: {e}")
                    
                    # 保存失败记录
                    await self._save_execution_record(target, questionnaire_url, False, 0, str(e), "target")
                    
                    results.append({
                        "persona_name": target['persona_name'],
                        "persona_id": target['persona_id'],
                        "success": False,
                        "duration": 0,
                        "error": str(e)
                    })
                
                # 间隔执行
                if i < len(targets) - 1:
                    logger.info("⏳ 等待3秒后处理下一个大部队成员...")
                    await asyncio.sleep(3)
            
            # 统计结果
            successful_count = sum(1 for r in results if r["success"])
            success_rate = successful_count / len(results) if results else 0
            
            logger.info(f"🎉 大部队任务完成!")
            logger.info(f"📊 成功率: {successful_count}/{len(results)} ({success_rate*100:.1f}%)")
            
            return {
                "success": successful_count > 0,
                "total_count": len(results),
                "successful_count": successful_count,
                "success_rate": success_rate,
                "results": results,
                "questionnaire_url": questionnaire_url
            }
            
        except Exception as e:
            logger.error(f"❌ 大部队任务失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_complete_enhanced_workflow(self, questionnaire_url: str, 
                                           scout_count: int = 2, target_count: int = 5) -> Dict:
        """运行完整的增强工作流：敢死队 -> 分析 -> 大部队"""
        logger.info("🚀 启动完整增强工作流")
        
        try:
            # 阶段1: 敢死队探路
            logger.info("📍 阶段1: 敢死队探路")
            scout_result = await self.run_scout_team(questionnaire_url, scout_count)
            
            if not scout_result["success"]:
                logger.error("❌ 敢死队任务失败，终止流程")
                return {"success": False, "error": "敢死队任务失败"}
            
            # 等待一段时间让知识库分析完成
            logger.info("⏳ 等待知识库分析...")
            await asyncio.sleep(10)
            
            # 阶段2: 大部队执行
            logger.info("📍 阶段2: 大部队执行")
            target_result = await self.run_target_team(
                questionnaire_url, scout_result["session_id"], target_count
            )
            
            # 汇总结果
            total_success = scout_result["successful_count"] + target_result["successful_count"]
            total_count = scout_result["total_count"] + target_result["total_count"]
            
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
    
    def _generate_scout_prompt(self, digital_human: Dict) -> str:
        """生成敢死队专用提示词"""
        base_prompt = generate_detailed_person_description(digital_human)
        
        scout_prompt = f"""
你现在需要扮演一个真实的人来填写问卷调查。

{base_prompt}

【敢死队特殊任务】
你是敢死队成员，需要为后续的大部队积累宝贵经验：

1. 【探路使命】
   - 你的任务是探索问卷的结构和难点
   - 记录每个问题的类型和最佳答案选择
   - 为后续的大部队提供成功经验

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
   - 你的成功将为大部队提供宝贵指导

记住：你是开路先锋，你的经验将帮助后续的数字人更好地完成任务！
"""
        return scout_prompt
    
    async def _generate_enhanced_prompt(self, digital_human: Dict, scout_session_id: str, 
                                      questionnaire_url: str) -> str:
        """生成带指导经验的增强提示词"""
        base_prompt = generate_detailed_person_description(digital_human)
        
        # 获取敢死队指导经验
        guidance_text = ""
        if self.knowledge_base:
            guidance_text = await self.knowledge_base.get_guidance_for_target_team(
                scout_session_id, questionnaire_url, digital_human
            )
        
        if not guidance_text:
            # 如果没有获取到指导，使用基础提示词
            guidance_text = """
【基础答题指导】
请根据你的个人特征进行答题：
- 年龄相关：选择符合你年龄段的选项
- 职业相关：选择符合你职业特点的选项
- 性别相关：选择符合你性别特征的选项
"""
        
        enhanced_prompt = f"""
你现在需要扮演一个真实的人来填写问卷调查。

{base_prompt}

{guidance_text}

【大部队任务要求】
1. 【角色扮演】
   - 完全按照上述人物设定来思考和回答
   - 答案要符合你的年龄、性别、职业、居住地等特征
   - 保持角色的一致性，不要出戏

2. 【答题策略】
   - 仔细阅读每个问题，理解题意
   - 优先参考上述敢死队的成功经验
   - 根据你的人物设定选择最合适的答案
   - 对于个人信息类问题，严格按照设定回答

3. 【操作要求】
   - 逐页填写，不要跳过任何问题
   - 填写完当前页面后，点击"下一页"或"提交"按钮
   - 如果遇到必填项提示，请检查并补充遗漏的答案
   - 确保问卷完全提交成功

4. 【注意事项】
   - 答题速度要自然，不要过快或过慢
   - 遇到不确定的问题，选择最符合你身份的选项
   - 保持耐心，完成整个问卷流程

请特别注意上述答题指导经验，这些是基于敢死队成功案例总结的宝贵经验！
"""
        return enhanced_prompt
    
    async def _save_scout_experience(self, session_id: str, questionnaire_url: str, 
                                   scout: Dict, success: bool):
        """保存敢死队经验到知识库"""
        try:
            if not self.knowledge_base:
                return
            
            # 模拟经验数据（实际中需要从browser-use获取真实数据）
            mock_experiences = [
                {
                    "question_content": "您平时最常使用的电子设备是？",
                    "question_type": QuestionType.SINGLE_CHOICE,
                    "available_options": ["手机", "电脑", "平板", "其他"],
                    "chosen_answer": "手机" if scout.get('age', 30) < 35 else "电脑",
                    "reasoning": f"根据{scout['persona_name']}的年龄和职业特征选择"
                },
                {
                    "question_content": "您通常在哪里购买日用品？",
                    "question_type": QuestionType.SINGLE_CHOICE,
                    "available_options": ["超市", "网购", "便利店", "其他"],
                    "chosen_answer": "网购" if scout.get('age', 30) < 40 else "超市",
                    "reasoning": f"根据{scout['persona_name']}的年龄特征选择购物方式"
                }
            ]
            
            for exp_data in mock_experiences:
                experience = AnswerExperience(
                    persona_id=scout['persona_id'],
                    persona_name=scout['persona_name'],
                    persona_features={
                        "age": scout.get('age', 30),
                        "gender": scout.get('gender', '未知'),
                        "profession": scout.get('profession', '未知')
                    },
                    question_content=exp_data["question_content"],
                    question_type=exp_data["question_type"],
                    available_options=exp_data["available_options"],
                    chosen_answer=exp_data["chosen_answer"],
                    success=success,
                    reasoning=exp_data["reasoning"]
                )
                
                await self.knowledge_base.save_answer_experience(
                    session_id, questionnaire_url, experience
                )
            
            logger.info(f"✅ 保存了 {len(mock_experiences)} 条敢死队经验")
            
        except Exception as e:
            logger.error(f"❌ 保存敢死队经验失败: {e}")
    
    async def _analyze_scout_experiences(self, session_id: str, questionnaire_url: str):
        """分析敢死队经验并生成指导规则"""
        try:
            if not self.knowledge_base:
                return
            
            guidance_rules = await self.knowledge_base.analyze_experiences_and_generate_guidance(
                session_id, questionnaire_url
            )
            
            logger.info(f"✅ 分析完成，生成了 {len(guidance_rules)} 条指导规则")
            
        except Exception as e:
            logger.error(f"❌ 分析敢死队经验失败: {e}")
    
    # 复用原有的方法
    async def _get_suitable_personas(self, count: int, is_scout: bool = False) -> List[Dict]:
        """获取符合条件的数字人"""
        try:
            # 方法1: 尝试从小社会系统获取
            personas = await self._get_personas_from_xiaoshe(count)
            
            if personas:
                logger.info(f"✅ 从小社会系统获取到 {len(personas)} 个数字人")
                return personas
            
            # 方法2: 从数据库获取
            personas = await self._get_personas_from_database(count)
            
            if personas:
                logger.info(f"✅ 从数据库获取到 {len(personas)} 个数字人")
                return personas
            
            # 方法3: 使用模拟数据
            logger.warning("⚠️ 使用模拟数字人数据")
            return self._generate_mock_personas(count)
            
        except Exception as e:
            logger.error(f"❌ 获取数字人失败: {e}")
            return []
    
    async def _get_personas_from_xiaoshe(self, count: int) -> List[Dict]:
        """从小社会系统获取数字人"""
        try:
            personas = []
            
            for i in range(1, count + 1):
                try:
                    response = requests.get(f"http://localhost:5001/api/persona/{i}", timeout=10)
                    
                    if response.status_code == 200:
                        persona_data = response.json()
                        personas.append(persona_data)
                        logger.info(f"✅ 获取数字人 {i}: {persona_data.get('persona_name', '未知')}")
                    else:
                        logger.warning(f"⚠️ 数字人 {i} 获取失败: {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ 数字人 {i} 获取异常: {e}")
            
            return personas
            
        except Exception as e:
            logger.error(f"❌ 从小社会系统获取数字人失败: {e}")
            return []
    
    async def _get_personas_from_database(self, count: int) -> List[Dict]:
        """从数据库获取数字人"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT id, name, age, gender, profession, birthplace_str, residence_str, attributes
                FROM digital_humans 
                ORDER BY RAND() 
                LIMIT %s
                """, (count,))
                
                results = cursor.fetchall()
                
                personas = []
                for row in results:
                    persona = {
                        "persona_id": row[0],
                        "persona_name": row[1],
                        "age": row[2],
                        "gender": row[3],
                        "profession": row[4],
                        "birthplace_str": row[5] or "未知",
                        "residence_str": row[6] or "未知",
                        "attributes": json.loads(row[7]) if row[7] else {}
                    }
                    personas.append(persona)
                
                return personas
                
        except Exception as e:
            logger.error(f"❌ 从数据库获取数字人失败: {e}")
            return []
        finally:
            if 'connection' in locals():
                connection.close()
    
    def _generate_mock_personas(self, count: int) -> List[Dict]:
        """生成模拟数字人数据"""
        mock_personas = [
            {
                "persona_id": 1,
                "persona_name": "林心怡",
                "age": 35,
                "gender": "女",
                "profession": "高级时尚顾问",
                "birthplace_str": "上海",
                "residence_str": "北京",
                "attributes": {
                    "education": "本科",
                    "income": "高收入",
                    "interests": ["时尚", "购物", "旅行"]
                }
            },
            {
                "persona_id": 2,
                "persona_name": "张明",
                "age": 38,
                "gender": "男",
                "profession": "技术总监",
                "birthplace_str": "北京",
                "residence_str": "深圳",
                "attributes": {
                    "education": "硕士",
                    "income": "高收入",
                    "interests": ["编程", "游戏", "科技"]
                }
            },
            {
                "persona_id": 3,
                "persona_name": "王小明",
                "age": 12,
                "gender": "男",
                "profession": "学生",
                "birthplace_str": "广州",
                "residence_str": "广州",
                "attributes": {
                    "education": "小学",
                    "income": "无收入",
                    "interests": ["游戏", "动画", "体育"]
                }
            },
            {
                "persona_id": 4,
                "persona_name": "马志远",
                "age": 42,
                "gender": "男",
                "profession": "CEO",
                "birthplace_str": "杭州",
                "residence_str": "杭州",
                "attributes": {
                    "education": "MBA",
                    "income": "高收入",
                    "interests": ["管理", "投资", "高尔夫"]
                }
            },
            {
                "persona_id": 5,
                "persona_name": "陈雅",
                "age": 26,
                "gender": "女",
                "profession": "UI设计师",
                "birthplace_str": "成都",
                "residence_str": "北京",
                "attributes": {
                    "education": "本科",
                    "income": "中等收入",
                    "interests": ["设计", "艺术", "摄影"]
                }
            }
        ]
        
        return mock_personas[:count]
    
    def _convert_persona_to_digital_human(self, persona_info: Dict) -> Dict:
        """将persona_info转换为testWenjuanFinal.py期望的digital_human格式"""
        try:
            # 处理不同的persona_info结构
            if "background" in persona_info and isinstance(persona_info["background"], dict):
                # 敢死队格式，丰富信息在background中
                background = persona_info["background"]
                base_info = {
                    "id": persona_info.get('persona_id', background.get('id', 0)),
                    "name": persona_info.get('persona_name', background.get('name', '未知')),
                    "age": background.get('age', 30),
                    "gender": background.get('gender', '未知'),
                    "profession": background.get('profession', background.get('occupation', '未知')),
                    "birthplace_str": background.get('birthplace_str', background.get('birthplace', '未知')),
                    "residence_str": background.get('residence_str', background.get('residence', '未知')),
                    "attributes": background
                }
            else:
                # 直接格式，信息在根级别
                base_info = {
                    "id": persona_info.get('persona_id', persona_info.get('id', 0)),
                    "name": persona_info.get('persona_name', persona_info.get('name', '未知')),
                    "age": persona_info.get('age', 30),
                    "gender": persona_info.get('gender', '未知'),
                    "profession": persona_info.get('profession', persona_info.get('occupation', '未知')),
                    "birthplace_str": persona_info.get('birthplace_str', persona_info.get('birthplace', '未知')),
                    "residence_str": persona_info.get('residence_str', persona_info.get('residence', '未知')),
                    "attributes": persona_info.get('attributes', {})
                }
            
            logger.info(f"✅ 转换persona为digital_human格式: {base_info['name']}")
            return base_info
            
        except Exception as e:
            logger.error(f"❌ 转换persona格式失败: {e}")
            # 返回基本格式
            return {
                "id": persona_info.get('persona_id', 0),
                "name": persona_info.get('persona_name', '未知'),
                "age": 30,
                "gender": "未知",
                "profession": "未知",
                "birthplace_str": "未知",
                "residence_str": "未知",
                "attributes": {}
            }
    
    async def _save_execution_record(self, persona: Dict, questionnaire_url: str, 
                                   success: bool, duration: float, error: Optional[str], 
                                   team_type: str = "target"):
        """保存执行记录到数据库"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO questionnaire_sessions 
                (session_id, questionnaire_url, persona_id, persona_name,
                 total_questions, successful_answers, success_rate, total_time,
                 session_type, strategy_used, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    f"enhanced_{team_type}_{int(time.time())}_{persona['persona_id']}",
                    questionnaire_url,
                    persona['persona_id'],
                    persona['persona_name'],
                    1 if success else 0,
                    1 if success else 0,
                    100.0 if success else 0.0,
                    duration,
                    f"enhanced_{team_type}",
                    "enhanced_with_knowledge",
                    datetime.now()
                ))
                connection.commit()
                logger.info(f"✅ 执行记录已保存: {persona['persona_name']} ({team_type})")
        except Exception as e:
            logger.error(f"❌ 保存执行记录失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()

async def main():
    """主函数"""
    print("🤖 智能问卷自动填写系统 - 增强版")
    print("🎯 集成智能知识库：敢死队 -> 分析 -> 大部队")
    print("=" * 60)
    
    # 获取问卷URL
    questionnaire_url = input("请输入问卷URL (回车使用默认): ").strip()
    if not questionnaire_url:
        questionnaire_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"
        print(f"使用默认问卷: {questionnaire_url}")
    
    # 获取敢死队数量
    try:
        scout_count = int(input("请输入敢死队数量 (默认2): ").strip() or "2")
    except ValueError:
        scout_count = 2
        print("使用默认敢死队数量: 2")
    
    # 获取大部队数量
    try:
        target_count = int(input("请输入大部队数量 (默认3): ").strip() or "3")
    except ValueError:
        target_count = 3
        print("使用默认大部队数量: 3")
    
    print("=" * 60)
    
    # 创建增强系统
    enhanced_system = EnhancedQuestionnaireSystem()
    
    # 执行完整工作流
    result = await enhanced_system.run_complete_enhanced_workflow(
        questionnaire_url, scout_count, target_count
    )
    
    # 显示结果
    if result["success"]:
        print(f"\n🎉 增强工作流执行完成!")
        print(f"📊 总数: {result['total_count']}")
        print(f"✅ 成功: {result['total_success']}")
        print(f"📈 成功率: {result['success_rate']*100:.1f}%")
        
        print(f"\n📋 敢死队结果:")
        scout_result = result["scout_result"]
        print(f"  成功率: {scout_result['successful_count']}/{scout_result['total_count']}")
        
        print(f"\n📋 大部队结果:")
        target_result = result["target_result"]
        print(f"  成功率: {target_result['successful_count']}/{target_result['total_count']}")
        
    else:
        print(f"\n❌ 增强工作流失败: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main()) 