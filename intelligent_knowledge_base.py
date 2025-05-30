#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷知识库系统
实现：页面信息抓取 -> 多模态分析 -> 经验提取 -> 指导生成
使用Gemini进行省钱的多模态内容理解
"""

import asyncio
import logging
import time
import json
import base64
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import pymysql
import pymysql.cursors

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入Gemini相关模块
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("⚠️ LangChain模块未安装，多模态分析功能将被禁用")

from config import get_config
from questionnaire_system import DatabaseManager, DB_CONFIG

class QuestionType(Enum):
    """题目类型枚举"""
    SINGLE_CHOICE = "single_choice"      # 单选题
    MULTIPLE_CHOICE = "multiple_choice"  # 多选题
    TEXT_INPUT = "text_input"           # 文本输入
    SCALE_RATING = "scale_rating"       # 量表评分
    DROPDOWN = "dropdown"               # 下拉选择
    CHECKBOX = "checkbox"               # 复选框
    RADIO = "radio"                     # 单选按钮
    UNKNOWN = "unknown"                 # 未知类型

@dataclass
class PageContent:
    """页面内容数据类"""
    page_number: int
    page_title: str
    questions: List[Dict]
    navigation_elements: Dict
    screenshot_base64: Optional[str] = None
    html_content: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class AnswerExperience:
    """答题经验数据类"""
    persona_id: int
    persona_name: str
    persona_features: Dict
    question_content: str
    question_type: QuestionType
    available_options: List[str]
    chosen_answer: str
    success: bool
    reasoning: Optional[str] = None
    time_taken: float = 0.0
    error_message: Optional[str] = None

@dataclass
class GuidanceRule:
    """指导规则数据类"""
    rule_id: str
    question_pattern: str
    target_personas: List[str]
    recommended_answer: str
    confidence_score: float
    reasoning: str
    success_rate: float
    sample_size: int
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class IntelligentKnowledgeBase:
    """智能知识库系统"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.llm_config = get_config("llm")
        self.gemini_model = self._init_gemini_model()
        self.cache = {}  # 简单缓存，避免重复分析
        
    def _init_gemini_model(self):
        """初始化Gemini模型"""
        try:
            return ChatGoogleGenerativeAI(
                model=self.llm_config.get("model", "gemini-2.0-flash"),
                google_api_key=self.llm_config.get("api_key"),
                temperature=0.3,  # 降低温度，提高一致性
                max_tokens=2048   # 控制token使用
            )
        except Exception as e:
            logger.error(f"❌ 初始化Gemini模型失败: {e}")
            return None
    
    async def capture_page_content(self, session_id: str, page_number: int, 
                                 screenshot_base64: str, html_content: str,
                                 current_url: str) -> PageContent:
        """
        抓取并分析页面内容
        省钱策略：只对关键页面进行多模态分析
        """
        try:
            # 生成内容哈希，避免重复分析
            content_hash = hashlib.md5(
                (screenshot_base64[:1000] + html_content[:1000]).encode()
            ).hexdigest()
            
            cache_key = f"page_analysis_{content_hash}"
            if cache_key in self.cache:
                logger.info(f"📋 使用缓存的页面分析结果")
                return self.cache[cache_key]
            
            # 先进行轻量级HTML分析
            basic_analysis = await self._analyze_html_content(html_content)
            
            # 只有在检测到重要内容时才进行多模态分析
            if self._should_use_multimodal_analysis(basic_analysis):
                logger.info(f"🔍 执行多模态页面分析 (页面 {page_number})")
                enhanced_analysis = await self._multimodal_page_analysis(
                    screenshot_base64, html_content, basic_analysis
                )
                analysis_result = {**basic_analysis, **enhanced_analysis}
            else:
                logger.info(f"📝 使用基础HTML分析 (页面 {page_number})")
                analysis_result = basic_analysis
            
            # 构建PageContent对象
            page_content = PageContent(
                page_number=page_number,
                page_title=analysis_result.get("page_title", f"页面 {page_number}"),
                questions=analysis_result.get("questions", []),
                navigation_elements=analysis_result.get("navigation", {}),
                screenshot_base64=screenshot_base64,
                html_content=html_content
            )
            
            # 保存到数据库
            await self._save_page_analysis(session_id, current_url, page_content, analysis_result)
            
            # 缓存结果
            self.cache[cache_key] = page_content
            
            logger.info(f"✅ 页面内容抓取完成: {len(page_content.questions)} 个问题")
            return page_content
            
        except Exception as e:
            logger.error(f"❌ 页面内容抓取失败: {e}")
            # 返回基础页面内容
            return PageContent(
                page_number=page_number,
                page_title=f"页面 {page_number}",
                questions=[],
                navigation_elements={},
                screenshot_base64=screenshot_base64,
                html_content=html_content
            )
    
    async def _analyze_html_content(self, html_content: str) -> Dict:
        """轻量级HTML内容分析，不消耗Gemini token"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取基本信息
            page_title = soup.find('title')
            page_title = page_title.text.strip() if page_title else "未知页面"
            
            # 查找问题元素
            questions = []
            question_selectors = [
                'div[class*="question"]',
                'div[class*="item"]', 
                'div[class*="field"]',
                'label',
                'span[class*="title"]'
            ]
            
            question_elements = []
            for selector in question_selectors:
                elements = soup.select(selector)
                question_elements.extend(elements)
            
            # 提取问题文本和选项
            for i, element in enumerate(question_elements[:10]):  # 限制处理数量
                text = element.get_text(strip=True)
                if len(text) > 10 and '?' in text or '：' in text or '。' in text:
                    # 查找相关的选项
                    options = []
                    parent = element.parent
                    if parent:
                        option_elements = parent.find_all(['input', 'option', 'button'])
                        for opt in option_elements:
                            opt_text = opt.get_text(strip=True)
                            if opt_text and len(opt_text) < 100:
                                options.append(opt_text)
                    
                    questions.append({
                        "question_number": i + 1,
                        "question_text": text[:200],  # 限制长度
                        "question_type": self._detect_question_type(element, options),
                        "options": options[:10],  # 限制选项数量
                        "element_info": {
                            "tag": element.name,
                            "class": element.get('class', []),
                            "id": element.get('id', '')
                        }
                    })
            
            # 查找导航元素
            navigation = {}
            nav_selectors = ['button', 'input[type="submit"]', 'a[class*="next"]', 'a[class*="prev"]']
            for selector in nav_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text and any(keyword in text for keyword in ['下一', '提交', '完成', '上一', '返回']):
                        navigation[text] = {
                            "tag": elem.name,
                            "class": elem.get('class', []),
                            "id": elem.get('id', '')
                        }
            
            return {
                "page_title": page_title,
                "questions": questions,
                "navigation": navigation,
                "analysis_type": "html_basic"
            }
            
        except Exception as e:
            logger.error(f"❌ HTML分析失败: {e}")
            return {
                "page_title": "分析失败",
                "questions": [],
                "navigation": {},
                "analysis_type": "failed"
            }
    
    def _should_use_multimodal_analysis(self, basic_analysis: Dict) -> bool:
        """判断是否需要使用多模态分析（省钱策略）"""
        # 如果基础分析已经提取到足够信息，就不使用多模态
        questions = basic_analysis.get("questions", [])
        
        # 条件1: 没有找到问题，需要多模态分析
        if len(questions) == 0:
            return True
            
        # 条件2: 问题信息不完整，需要多模态分析
        incomplete_questions = 0
        for q in questions:
            if not q.get("options") or len(q.get("question_text", "")) < 10:
                incomplete_questions += 1
        
        if incomplete_questions > len(questions) * 0.5:  # 超过50%的问题信息不完整
            return True
        
        # 条件3: 检测到复杂的视觉元素（通过HTML特征判断）
        # 这里可以添加更多判断逻辑
        
        return False
    
    async def _multimodal_page_analysis(self, screenshot_base64: str, 
                                      html_content: str, basic_analysis: Dict) -> Dict:
        """使用Gemini进行多模态页面分析"""
        try:
            if not self.gemini_model:
                logger.warning("⚠️ Gemini模型未初始化，跳过多模态分析")
                return {}
            
            # 构建多模态提示词
            prompt = self._build_multimodal_analysis_prompt(basic_analysis)
            
            # 准备图片数据
            image_data = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{screenshot_base64}"
                }
            }
            
            # 调用Gemini进行分析
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    image_data
                ]
            )
            
            response = await self.gemini_model.ainvoke([message])
            
            # 解析响应
            analysis_result = self._parse_multimodal_response(response.content)
            analysis_result["analysis_type"] = "multimodal_enhanced"
            
            logger.info(f"✅ 多模态分析完成，增强了 {len(analysis_result.get('enhanced_questions', []))} 个问题")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ 多模态分析失败: {e}")
            return {"analysis_type": "multimodal_failed", "error": str(e)}
    
    def _build_multimodal_analysis_prompt(self, basic_analysis: Dict) -> str:
        """构建多模态分析提示词"""
        questions_info = ""
        if basic_analysis.get("questions"):
            questions_info = f"已识别到 {len(basic_analysis['questions'])} 个问题:\n"
            for i, q in enumerate(basic_analysis["questions"][:5]):  # 只显示前5个
                questions_info += f"{i+1}. {q.get('question_text', '')[:50]}...\n"
        
        prompt = f"""
请分析这个问卷页面的截图，重点关注以下内容：

1. 页面中的问题和选项（特别是图片中可见但HTML中可能遗漏的内容）
2. 问题的类型（单选、多选、文本输入等）
3. 导航按钮和提交按钮的位置

当前HTML分析结果：
{questions_info}

请以JSON格式返回分析结果，包含：
{{
    "enhanced_questions": [
        {{
            "question_number": 1,
            "question_text": "完整的问题文本",
            "question_type": "single_choice/multiple_choice/text_input/scale_rating",
            "options": ["选项1", "选项2", ...],
            "visual_elements": "描述视觉特征"
        }}
    ],
    "navigation_buttons": {{
        "next_button": "下一步按钮描述",
        "submit_button": "提交按钮描述"
    }},
    "page_layout": "页面布局描述"
}}

请确保返回有效的JSON格式，不要包含其他文字。
"""
        return prompt
    
    def _parse_multimodal_response(self, response_content: str) -> Dict:
        """解析多模态分析响应"""
        try:
            # 尝试提取JSON内容
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试解析文本内容
                return {"raw_response": response_content, "parsed": False}
        except Exception as e:
            logger.error(f"❌ 解析多模态响应失败: {e}")
            return {"error": str(e), "raw_response": response_content}
    
    def _detect_question_type(self, element, options: List[str]) -> str:
        """检测问题类型"""
        # 根据HTML元素和选项判断问题类型
        element_html = str(element).lower()
        
        if 'radio' in element_html or len(options) > 1:
            return QuestionType.SINGLE_CHOICE.value
        elif 'checkbox' in element_html:
            return QuestionType.MULTIPLE_CHOICE.value
        elif 'input' in element_html and 'text' in element_html:
            return QuestionType.TEXT_INPUT.value
        elif 'select' in element_html:
            return QuestionType.DROPDOWN.value
        elif any(word in element_html for word in ['评分', '分数', 'rating', 'scale']):
            return QuestionType.SCALE_RATING.value
        else:
            return QuestionType.UNKNOWN.value
    
    async def save_answer_experience(self, session_id: str, questionnaire_url: str,
                                   experience: AnswerExperience) -> bool:
        """保存答题经验到知识库"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                # 保存到questionnaire_knowledge表
                sql = """
                INSERT INTO questionnaire_knowledge 
                (session_id, questionnaire_url, persona_id, persona_name, persona_role,
                 question_content, question_type, answer_choice, success, 
                 experience_type, experience_description, strategy_used, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                experience_type = "success" if experience.success else "failure"
                experience_desc = experience.reasoning or (
                    f"选择了'{experience.chosen_answer}'" if experience.success 
                    else f"选择'{experience.chosen_answer}'失败: {experience.error_message}"
                )
                
                cursor.execute(sql, (
                    session_id, questionnaire_url, experience.persona_id, 
                    experience.persona_name, "scout",  # 敢死队经验
                    experience.question_content, experience.question_type.value,
                    experience.chosen_answer, experience.success,
                    experience_type, experience_desc, "intelligent_analysis",
                    datetime.now()
                ))
                connection.commit()
                
                logger.info(f"✅ 保存答题经验: {experience.persona_name} - {'成功' if experience.success else '失败'}")
                return True
                
        except Exception as e:
            logger.error(f"❌ 保存答题经验失败: {e}")
            return False
        finally:
            if 'connection' in locals():
                connection.close()
    
    async def analyze_experiences_and_generate_guidance(self, session_id: str, 
                                                      questionnaire_url: str) -> List[GuidanceRule]:
        """分析经验并生成指导规则"""
        try:
            # 获取所有敢死队经验
            experiences = await self._get_scout_experiences(session_id, questionnaire_url)
            
            if not experiences:
                logger.warning("⚠️ 没有找到敢死队经验数据")
                return []
            
            # 使用Gemini分析经验并生成指导规则
            guidance_rules = await self._gemini_analyze_experiences(experiences)
            
            # 保存指导规则到数据库
            await self._save_guidance_rules(session_id, questionnaire_url, guidance_rules)
            
            logger.info(f"✅ 生成了 {len(guidance_rules)} 条指导规则")
            return guidance_rules
            
        except Exception as e:
            logger.error(f"❌ 分析经验并生成指导失败: {e}")
            return []
    
    async def _get_scout_experiences(self, session_id: str, questionnaire_url: str) -> List[Dict]:
        """获取敢死队经验数据"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT qk.*, dh.age, dh.gender, dh.profession, dh.birthplace_str, dh.residence_str
                FROM questionnaire_knowledge qk
                LEFT JOIN digital_humans dh ON qk.persona_id = dh.id
                WHERE qk.session_id = %s AND qk.questionnaire_url = %s 
                AND qk.persona_role = 'scout'
                ORDER BY qk.created_at
                """
                cursor.execute(sql, (session_id, questionnaire_url))
                return list(cursor.fetchall())
        except Exception as e:
            logger.error(f"❌ 获取敢死队经验失败: {e}")
            return []
        finally:
            if 'connection' in locals():
                connection.close()
    
    async def _gemini_analyze_experiences(self, experiences: List[Dict]) -> List[GuidanceRule]:
        """使用Gemini分析经验并生成指导规则"""
        try:
            if not self.gemini_model or not experiences:
                return []
            
            # 构建分析提示词
            prompt = self._build_experience_analysis_prompt(experiences)
            
            # 调用Gemini分析
            response = await self.gemini_model.ainvoke([HumanMessage(content=prompt)])
            
            # 解析响应生成指导规则
            guidance_rules = self._parse_guidance_response(response.content)
            
            return guidance_rules
            
        except Exception as e:
            logger.error(f"❌ Gemini经验分析失败: {e}")
            return []
    
    def _build_experience_analysis_prompt(self, experiences: List[Dict]) -> str:
        """构建经验分析提示词"""
        # 分析成功和失败的经验
        success_experiences = [exp for exp in experiences if exp.get('success')]
        failure_experiences = [exp for exp in experiences if not exp.get('success')]
        
        prompt = f"""
请分析以下问卷答题经验数据，生成针对性的答题指导规则。

成功经验 ({len(success_experiences)} 条):
"""
        
        for i, exp in enumerate(success_experiences[:5]):  # 限制数量节省token
            prompt += f"""
{i+1}. 数字人: {exp.get('persona_name')} ({exp.get('age')}岁{exp.get('gender')}, {exp.get('profession')})
   问题: {exp.get('question_content', '')[:100]}...
   选择: {exp.get('answer_choice')}
   类型: {exp.get('question_type')}
"""

        if failure_experiences:
            prompt += f"\n失败经验 ({len(failure_experiences)} 条):\n"
            for i, exp in enumerate(failure_experiences[:3]):  # 失败经验看更少
                prompt += f"""
{i+1}. 数字人: {exp.get('persona_name')} - 失败原因: {exp.get('experience_description', '')}
"""

        prompt += """

请基于以上数据生成答题指导规则，以JSON格式返回：
{
    "guidance_rules": [
        {
            "rule_id": "rule_001",
            "question_pattern": "问题的关键词或模式",
            "target_personas": ["适用的人群特征"],
            "recommended_answer": "推荐的答案",
            "reasoning": "推荐理由",
            "confidence_score": 0.85,
            "success_rate": 0.90
        }
    ]
}

要求：
1. 重点关注成功经验，提取可复用的模式
2. 考虑数字人的特征（年龄、性别、职业）与答案选择的关联
3. 生成具体可操作的指导建议
4. 确保返回有效的JSON格式
"""
        return prompt
    
    def _parse_guidance_response(self, response_content: str) -> List[GuidanceRule]:
        """解析指导规则响应"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group())
                rules = []
                
                for rule_data in json_data.get("guidance_rules", []):
                    rule = GuidanceRule(
                        rule_id=rule_data.get("rule_id", f"rule_{int(time.time())}"),
                        question_pattern=rule_data.get("question_pattern", ""),
                        target_personas=rule_data.get("target_personas", []),
                        recommended_answer=rule_data.get("recommended_answer", ""),
                        confidence_score=rule_data.get("confidence_score", 0.5),
                        reasoning=rule_data.get("reasoning", ""),
                        success_rate=rule_data.get("success_rate", 0.5),
                        sample_size=1
                    )
                    rules.append(rule)
                
                return rules
            else:
                logger.warning("⚠️ 未找到有效的JSON响应")
                return []
                
        except Exception as e:
            logger.error(f"❌ 解析指导规则响应失败: {e}")
            return []
    
    async def _save_guidance_rules(self, session_id: str, questionnaire_url: str, 
                                 rules: List[GuidanceRule]) -> bool:
        """保存指导规则到数据库"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                for rule in rules:
                    # 保存到questionnaire_knowledge表作为指导经验
                    sql = """
                    INSERT INTO questionnaire_knowledge 
                    (session_id, questionnaire_url, persona_id, persona_name, persona_role,
                     question_content, answer_choice, success, experience_type, 
                     experience_description, strategy_used, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(sql, (
                        session_id, questionnaire_url, 0, "智能分析系统", "guidance",
                        rule.question_pattern, rule.recommended_answer, True,
                        "guidance_rule", 
                        f"指导规则: {rule.reasoning} (置信度: {rule.confidence_score:.2f})",
                        "intelligent_guidance", datetime.now()
                    ))
                
                connection.commit()
                logger.info(f"✅ 保存了 {len(rules)} 条指导规则")
                return True
                
        except Exception as e:
            logger.error(f"❌ 保存指导规则失败: {e}")
            return False
        finally:
            if 'connection' in locals():
                connection.close()
    
    async def get_guidance_for_target_team(self, session_id: str, questionnaire_url: str,
                                         persona_features: Dict) -> str:
        """为大部队生成个性化的答题指导"""
        try:
            # 获取指导规则
            guidance_rules = await self._get_guidance_rules(session_id, questionnaire_url)
            
            if not guidance_rules:
                return ""
            
            # 根据数字人特征匹配相关指导
            relevant_guidance = self._match_guidance_to_persona(guidance_rules, persona_features)
            
            # 生成指导文本
            guidance_text = self._format_guidance_for_prompt(relevant_guidance)
            
            logger.info(f"✅ 为数字人生成了 {len(relevant_guidance)} 条相关指导")
            return guidance_text
            
        except Exception as e:
            logger.error(f"❌ 获取大部队指导失败: {e}")
            return ""
    
    async def _get_guidance_rules(self, session_id: str, questionnaire_url: str) -> List[Dict]:
        """获取指导规则"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT * FROM questionnaire_knowledge 
                WHERE session_id = %s AND questionnaire_url = %s 
                AND persona_role = 'guidance'
                ORDER BY created_at DESC
                """
                cursor.execute(sql, (session_id, questionnaire_url))
                return list(cursor.fetchall())
        except Exception as e:
            logger.error(f"❌ 获取指导规则失败: {e}")
            return []
        finally:
            if 'connection' in locals():
                connection.close()
    
    def _match_guidance_to_persona(self, guidance_rules: List[Dict], 
                                 persona_features: Dict) -> List[Dict]:
        """根据数字人特征匹配相关指导"""
        relevant_rules = []
        
        for rule in guidance_rules:
            # 简单的匹配逻辑，可以后续优化
            question_pattern = rule.get('question_content', '').lower()
            persona_age = persona_features.get('age', 0)
            persona_gender = persona_features.get('gender', '').lower()
            persona_profession = persona_features.get('profession', '').lower()
            
            # 匹配逻辑（可以根据需要扩展）
            is_relevant = True  # 默认相关，可以添加更复杂的匹配逻辑
            
            if is_relevant:
                relevant_rules.append(rule)
        
        return relevant_rules
    
    def _format_guidance_for_prompt(self, guidance_rules: List[Dict]) -> str:
        """格式化指导规则为提示词文本"""
        if not guidance_rules:
            return ""
        
        guidance_text = "\n【答题指导经验】\n"
        guidance_text += "根据敢死队的成功经验，请注意以下答题技巧：\n\n"
        
        for i, rule in enumerate(guidance_rules[:5], 1):  # 限制数量
            question_pattern = rule.get('question_content', '')
            recommended_answer = rule.get('answer_choice', '')
            reasoning = rule.get('experience_description', '')
            
            guidance_text += f"{i}. 当遇到包含「{question_pattern}」的题目时：\n"
            guidance_text += f"   推荐选择：{recommended_answer}\n"
            guidance_text += f"   理由：{reasoning}\n\n"
        
        guidance_text += "请根据以上经验，结合你的个人特征进行答题。\n"
        return guidance_text
    
    async def _save_page_analysis(self, session_id: str, questionnaire_url: str,
                                page_content: PageContent, analysis_result: Dict):
        """保存页面分析结果到数据库"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO page_analysis_records 
                (session_id, task_id, questionnaire_url, page_number, page_title,
                 total_questions, questions_data, page_structure, navigation_elements,
                 analysis_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(sql, (
                    session_id, session_id, questionnaire_url, page_content.page_number,
                    page_content.page_title, len(page_content.questions),
                    json.dumps(page_content.questions, ensure_ascii=False),
                    json.dumps(analysis_result, ensure_ascii=False),
                    json.dumps(page_content.navigation_elements, ensure_ascii=False),
                    datetime.now()
                ))
                connection.commit()
                
        except Exception as e:
            logger.error(f"❌ 保存页面分析失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()

# 测试函数
async def test_intelligent_knowledge_base():
    """测试智能知识库系统"""
    print("🧠 测试智能知识库系统")
    print("=" * 50)
    
    kb = IntelligentKnowledgeBase()
    
    # 测试基础功能
    print("✅ 智能知识库初始化成功")
    
    # 模拟答题经验
    test_experience = AnswerExperience(
        persona_id=1,
        persona_name="测试数字人",
        persona_features={"age": 25, "gender": "女", "profession": "学生"},
        question_content="您平时最常使用的电子设备是？",
        question_type=QuestionType.SINGLE_CHOICE,
        available_options=["手机", "电脑", "平板", "其他"],
        chosen_answer="手机",
        success=True,
        reasoning="作为年轻人，手机是最常用的设备"
    )
    
    # 保存经验
    success = await kb.save_answer_experience("test_session", "test_url", test_experience)
    print(f"保存答题经验: {'✅ 成功' if success else '❌ 失败'}")
    
    print("\n🎉 智能知识库测试完成")

if __name__ == "__main__":
    asyncio.run(test_intelligent_knowledge_base()) 