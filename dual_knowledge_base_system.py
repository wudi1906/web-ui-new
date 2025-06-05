#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
双知识库系统
通用知识库（Universal KB）+ 临时知识库（Temporary KB）

通用知识库：存储通用答题技巧和经验（长期保留）
临时知识库：存储当前问卷的特定经验（任务完成后清理）
"""

import asyncio
import json
import logging
import time
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import sqlite3
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UniversalExperience:
    """通用答题经验"""
    experience_id: str
    question_type: str  # 题目类型：单选、多选、填空、评分等
    strategy: str  # 答题策略
    success_pattern: str  # 成功模式
    failure_pattern: str  # 失败模式
    confidence_score: float  # 可信度
    usage_count: int  # 使用次数
    success_rate: float  # 成功率
    created_at: str
    updated_at: str

@dataclass
class TemporaryExperience:
    """临时问卷经验"""
    experience_id: str
    questionnaire_url: str  # 问卷URL
    question_content: str  # 题目内容
    correct_answer: str  # 正确答案
    wrong_answers: List[str]  # 错误答案
    answer_reasoning: str  # 答题理由
    digital_human_id: str  # 数字人ID
    digital_human_profile: Dict  # 数字人特征
    success: bool  # 是否成功
    page_number: int  # 页面编号
    timestamp: str

@dataclass
class QuestionnaireAnalysis:
    """问卷分析结果"""
    questionnaire_url: str
    target_audience: Dict  # 目标人群
    question_patterns: List[Dict]  # 题目模式
    trap_questions: List[Dict]  # 陷阱题目
    success_strategies: List[str]  # 成功策略
    recommended_answers: Dict  # 推荐答案
    analysis_confidence: float  # 分析可信度
    generated_at: str

class DualKnowledgeBaseSystem:
    """双知识库系统管理器"""
    
    def __init__(self, db_path: str = "knowledge_base.db"):
        self.db_path = db_path
        self.gemini_api_key = "AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8"
        
        # 初始化数据库
        self._init_database()
        
        # 初始化Gemini（如果可用）
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")
            self.gemini_available = True
            logger.info("✅ Gemini API 初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ Gemini API 不可用: {e}")
            self.model = None
            self.gemini_available = False
        
        logger.info("✅ 双知识库系统初始化完成")
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 通用知识库表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS universal_experiences (
                    experience_id TEXT PRIMARY KEY,
                    question_type TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    success_pattern TEXT,
                    failure_pattern TEXT,
                    confidence_score REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # 临时知识库表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temporary_experiences (
                    experience_id TEXT PRIMARY KEY,
                    questionnaire_url TEXT NOT NULL,
                    question_content TEXT NOT NULL,
                    correct_answer TEXT,
                    wrong_answers TEXT,  -- JSON格式
                    answer_reasoning TEXT,
                    digital_human_id TEXT NOT NULL,
                    digital_human_profile TEXT,  -- JSON格式
                    success BOOLEAN NOT NULL,
                    page_number INTEGER DEFAULT 1,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            # 为临时知识库表创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_temporary_experiences_url 
                ON temporary_experiences(questionnaire_url)
            ''')
            
            # 问卷分析表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questionnaire_analyses (
                    questionnaire_url TEXT PRIMARY KEY,
                    target_audience TEXT,  -- JSON格式
                    question_patterns TEXT,  -- JSON格式
                    trap_questions TEXT,  -- JSON格式
                    success_strategies TEXT,  -- JSON格式
                    recommended_answers TEXT,  -- JSON格式
                    analysis_confidence REAL DEFAULT 0.0,
                    generated_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("✅ 数据库表结构初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            raise
    
    async def save_temporary_experience(self, experience: TemporaryExperience) -> bool:
        """保存临时问卷经验"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO temporary_experiences 
                (experience_id, questionnaire_url, question_content, correct_answer, 
                 wrong_answers, answer_reasoning, digital_human_id, digital_human_profile, 
                 success, page_number, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                experience.experience_id,
                experience.questionnaire_url,
                experience.question_content,
                experience.correct_answer,
                json.dumps(experience.wrong_answers, ensure_ascii=False),
                experience.answer_reasoning,
                experience.digital_human_id,
                json.dumps(experience.digital_human_profile, ensure_ascii=False),
                experience.success,
                experience.page_number,
                experience.timestamp
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ 临时经验已保存: {experience.experience_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存临时经验失败: {e}")
            return False
    
    async def get_temporary_experiences(self, questionnaire_url: str) -> List[TemporaryExperience]:
        """获取指定问卷的临时经验"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM temporary_experiences 
                WHERE questionnaire_url = ?
                ORDER BY timestamp DESC
            ''', (questionnaire_url,))
            
            rows = cursor.fetchall()
            conn.close()
            
            experiences = []
            for row in rows:
                experience = TemporaryExperience(
                    experience_id=row[0],
                    questionnaire_url=row[1],
                    question_content=row[2],
                    correct_answer=row[3],
                    wrong_answers=json.loads(row[4]) if row[4] else [],
                    answer_reasoning=row[5],
                    digital_human_id=row[6],
                    digital_human_profile=json.loads(row[7]) if row[7] else {},
                    success=bool(row[8]),
                    page_number=row[9],
                    timestamp=row[10]
                )
                experiences.append(experience)
            
            logger.info(f"✅ 获取到 {len(experiences)} 条临时经验")
            return experiences
            
        except Exception as e:
            logger.error(f"❌ 获取临时经验失败: {e}")
            return []
    
    async def analyze_questionnaire_with_gemini(
        self, 
        questionnaire_url: str, 
        temporary_experiences: List[TemporaryExperience]
    ) -> Optional[QuestionnaireAnalysis]:
        """使用Gemini分析问卷，生成智能指导"""
        if not self.gemini_available:
            return await self._create_mock_analysis(questionnaire_url, temporary_experiences)
        
        try:
            # 分离成功和失败的经验
            successful_experiences = [exp for exp in temporary_experiences if exp.success]
            failed_experiences = [exp for exp in temporary_experiences if not exp.success]
            
            # 构建分析提示词
            analysis_prompt = self._build_analysis_prompt(
                questionnaire_url, successful_experiences, failed_experiences
            )
            
            # 调用Gemini进行分析
            logger.info("🧠 调用Gemini进行问卷智能分析...")
            response = await self.model.generate_content_async(analysis_prompt)
            
            # 解析分析结果
            analysis = self._parse_gemini_analysis_response(
                questionnaire_url, response.text
            )
            
            # 保存分析结果
            await self._save_questionnaire_analysis(analysis)
            
            logger.info("✅ Gemini分析完成")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Gemini分析失败: {e}")
            # 降级到模拟分析
            return await self._create_mock_analysis(questionnaire_url, temporary_experiences)
    
    def _build_analysis_prompt(
        self, 
        questionnaire_url: str, 
        successful_experiences: List[TemporaryExperience],
        failed_experiences: List[TemporaryExperience]
    ) -> str:
        """构建Gemini分析提示词"""
        
        prompt = f"""
你是专业的问卷分析专家，请对以下问卷进行深度智能分析：

📋 问卷URL: {questionnaire_url}

📊 成功经验数据 ({len(successful_experiences)}条):
"""
        
        # 添加成功经验
        for i, exp in enumerate(successful_experiences[:10], 1):  # 限制数量避免token过多
            prompt += f"""
成功案例{i}:
- 数字人: {exp.digital_human_profile.get('name', '未知')} (年龄{exp.digital_human_profile.get('age', '未知')}, {exp.digital_human_profile.get('job', '未知')})
- 题目: {exp.question_content[:100]}...
- 正确答案: {exp.correct_answer}
- 答题理由: {exp.answer_reasoning}
- 页面: {exp.page_number}
"""
        
        prompt += f"""

❌ 失败经验数据 ({len(failed_experiences)}条):
"""
        
        # 添加失败经验
        for i, exp in enumerate(failed_experiences[:5], 1):  # 失败经验数量更少
            prompt += f"""
失败案例{i}:
- 数字人: {exp.digital_human_profile.get('name', '未知')} (年龄{exp.digital_human_profile.get('age', '未知')}, {exp.digital_human_profile.get('job', '未知')})
- 题目: {exp.question_content[:100]}...
- 错误答案: {exp.wrong_answers}
- 失败原因: {exp.answer_reasoning}
"""
        
        prompt += """

🎯 请分析并输出以下JSON格式结果：

{
  "target_audience": {
    "age_range": "年龄范围",
    "occupation": ["职业类型"],
    "income_level": "收入水平",
    "characteristics": ["人群特征"]
  },
  "question_patterns": [
    {
      "pattern_type": "题目类型",
      "description": "模式描述",
      "examples": ["示例题目"]
    }
  ],
  "trap_questions": [
    {
      "question": "陷阱题目",
      "trap_type": "陷阱类型",
      "correct_strategy": "正确策略"
    }
  ],
  "success_strategies": [
    "成功策略1",
    "成功策略2"
  ],
  "recommended_answers": {
    "age_preference": "年龄偏好",
    "income_preference": "收入偏好",
    "occupation_preference": "职业偏好"
  },
  "analysis_confidence": 0.85
}

请确保分析结果准确、实用，能够指导后续的大部队作答。
        """
        
        return prompt
    
    def _parse_gemini_analysis_response(
        self, 
        questionnaire_url: str, 
        response_text: str
    ) -> QuestionnaireAnalysis:
        """解析Gemini分析响应"""
        try:
            # 提取JSON部分
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("响应中未找到有效JSON")
            
            json_str = response_text[json_start:json_end]
            analysis_data = json.loads(json_str)
            
            return QuestionnaireAnalysis(
                questionnaire_url=questionnaire_url,
                target_audience=analysis_data.get('target_audience', {}),
                question_patterns=analysis_data.get('question_patterns', []),
                trap_questions=analysis_data.get('trap_questions', []),
                success_strategies=analysis_data.get('success_strategies', []),
                recommended_answers=analysis_data.get('recommended_answers', {}),
                analysis_confidence=analysis_data.get('analysis_confidence', 0.0),
                generated_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.warning(f"⚠️ 解析Gemini响应失败: {e}，使用默认分析")
            return self._create_default_analysis(questionnaire_url)
    
    async def _create_mock_analysis(
        self, 
        questionnaire_url: str, 
        temporary_experiences: List[TemporaryExperience]
    ) -> QuestionnaireAnalysis:
        """创建模拟分析结果"""
        successful_experiences = [exp for exp in temporary_experiences if exp.success]
        
        # 基于实际经验生成模拟分析
        target_audience = self._extract_target_audience(successful_experiences)
        question_patterns = self._extract_question_patterns(temporary_experiences)
        
        analysis = QuestionnaireAnalysis(
            questionnaire_url=questionnaire_url,
            target_audience=target_audience,
            question_patterns=question_patterns,
            trap_questions=[
                {
                    "question": "收入验证题目",
                    "trap_type": "收入范围筛选",
                    "correct_strategy": "选择中等收入水平"
                }
            ],
            success_strategies=[
                "选择中等年龄段",
                "表现出适中的消费能力",
                "显示对产品的兴趣但不过度热情"
            ],
            recommended_answers={
                "age_preference": "25-35岁",
                "income_preference": "5000-15000元",
                "occupation_preference": "办公室职员或专业人员"
            },
            analysis_confidence=0.75,
            generated_at=datetime.now().isoformat()
        )
        
        await self._save_questionnaire_analysis(analysis)
        return analysis
    
    def _extract_target_audience(self, successful_experiences: List[TemporaryExperience]) -> Dict:
        """从成功经验中提取目标人群特征"""
        if not successful_experiences:
            return {
                "age_range": "25-35岁",
                "occupation": ["办公室职员"],
                "income_level": "中等",
                "characteristics": ["城市白领"]
            }
        
        # 分析成功数字人的特征
        ages = []
        occupations = []
        
        for exp in successful_experiences:
            profile = exp.digital_human_profile
            if 'age' in profile:
                try:
                    ages.append(int(profile['age']))
                except:
                    pass
            if 'job' in profile:
                occupations.append(profile['job'])
        
        # 计算年龄范围
        if ages:
            min_age = min(ages)
            max_age = max(ages)
            age_range = f"{min_age}-{max_age}岁"
        else:
            age_range = "25-35岁"
        
        # 提取职业类型
        unique_occupations = list(set(occupations)) if occupations else ["办公室职员"]
        
        return {
            "age_range": age_range,
            "occupation": unique_occupations[:3],  # 最多3个职业
            "income_level": "中等",
            "characteristics": ["目标用户群体"]
        }
    
    def _extract_question_patterns(self, experiences: List[TemporaryExperience]) -> List[Dict]:
        """提取题目模式"""
        patterns = []
        
        # 按页面分组
        pages = {}
        for exp in experiences:
            page_num = exp.page_number
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(exp)
        
        for page_num, page_experiences in pages.items():
            successful_count = sum(1 for exp in page_experiences if exp.success)
            total_count = len(page_experiences)
            
            patterns.append({
                "pattern_type": f"第{page_num}页题目",
                "description": f"成功率: {successful_count}/{total_count}",
                "examples": [exp.question_content[:50] + "..." for exp in page_experiences[:3]]
            })
        
        return patterns
    
    def _create_default_analysis(self, questionnaire_url: str) -> QuestionnaireAnalysis:
        """创建默认分析结果"""
        return QuestionnaireAnalysis(
            questionnaire_url=questionnaire_url,
            target_audience={
                "age_range": "25-35岁",
                "occupation": ["办公室职员", "专业人员"],
                "income_level": "中等",
                "characteristics": ["城市消费者"]
            },
            question_patterns=[
                {
                    "pattern_type": "基础信息题",
                    "description": "收集用户基本信息",
                    "examples": ["年龄选择", "职业选择", "收入水平"]
                }
            ],
            trap_questions=[],
            success_strategies=[
                "选择中等选项",
                "避免极端答案"
            ],
            recommended_answers={
                "age_preference": "25-35岁",
                "income_preference": "中等水平"
            },
            analysis_confidence=0.6,
            generated_at=datetime.now().isoformat()
        )
    
    async def _save_questionnaire_analysis(self, analysis: QuestionnaireAnalysis) -> bool:
        """保存问卷分析结果"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO questionnaire_analyses 
                (questionnaire_url, target_audience, question_patterns, trap_questions, 
                 success_strategies, recommended_answers, analysis_confidence, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis.questionnaire_url,
                json.dumps(analysis.target_audience, ensure_ascii=False),
                json.dumps(analysis.question_patterns, ensure_ascii=False),
                json.dumps(analysis.trap_questions, ensure_ascii=False),
                json.dumps(analysis.success_strategies, ensure_ascii=False),
                json.dumps(analysis.recommended_answers, ensure_ascii=False),
                analysis.analysis_confidence,
                analysis.generated_at
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ 问卷分析结果已保存")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存问卷分析失败: {e}")
            return False
    
    async def get_questionnaire_analysis(self, questionnaire_url: str) -> Optional[QuestionnaireAnalysis]:
        """获取问卷分析结果"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM questionnaire_analyses 
                WHERE questionnaire_url = ?
            ''', (questionnaire_url,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return QuestionnaireAnalysis(
                questionnaire_url=row[0],
                target_audience=json.loads(row[1]),
                question_patterns=json.loads(row[2]),
                trap_questions=json.loads(row[3]),
                success_strategies=json.loads(row[4]),
                recommended_answers=json.loads(row[5]),
                analysis_confidence=row[6],
                generated_at=row[7]
            )
            
        except Exception as e:
            logger.error(f"❌ 获取问卷分析失败: {e}")
            return None
    
    async def extract_experiences_from_scout_data(
        self, 
        questionnaire_url: str,
        scout_data: List[Dict]
    ) -> List[TemporaryExperience]:
        """从敢死队数据中提取经验"""
        experiences = []
        
        for scout in scout_data:
            scout_id = scout.get('scout_id', '')
            scout_name = scout.get('scout_name', '')
            pages = scout.get('pages', [])
            digital_human = scout.get('digital_human', {})
            
            for page in pages:
                page_number = page.get('page_number', 1)
                questions = page.get('questions_answered', [])
                success = page.get('success', False)
                
                for question in questions:
                    experience_id = f"exp_{int(time.time())}_{uuid.uuid4().hex[:8]}"
                    
                    experience = TemporaryExperience(
                        experience_id=experience_id,
                        questionnaire_url=questionnaire_url,
                        question_content=question.get('question', ''),
                        correct_answer=question.get('answer', ''),
                        wrong_answers=[],
                        answer_reasoning=question.get('reasoning', ''),
                        digital_human_id=scout_id,
                        digital_human_profile=digital_human,
                        success=success,
                        page_number=page_number,
                        timestamp=datetime.now().isoformat()
                    )
                    
                    experiences.append(experience)
                    await self.save_temporary_experience(experience)
        
        logger.info(f"✅ 从敢死队数据中提取了 {len(experiences)} 条经验")
        return experiences
    
    async def generate_guidance_for_target_team(
        self, 
        questionnaire_url: str,
        target_digital_human: Dict
    ) -> str:
        """为大部队成员生成智能指导提示词"""
        
        # 获取问卷分析结果
        analysis = await self.get_questionnaire_analysis(questionnaire_url)
        if not analysis:
            return self._generate_basic_guidance(target_digital_human)
        
        # 获取临时经验
        temp_experiences = await self.get_temporary_experiences(questionnaire_url)
        successful_experiences = [exp for exp in temp_experiences if exp.success]
        
        # 生成完整的指导提示词
        guidance = f"""
你是{target_digital_human.get('name', '未知')}，年龄{target_digital_human.get('age', '30')}岁，职业是{target_digital_human.get('job', '职员')}，月收入{target_digital_human.get('income', '8000')}元。

🎯 基于敢死队经验的智能指导：

📊 问卷目标人群分析：
- 年龄范围：{analysis.target_audience.get('age_range', '25-35岁')}
- 职业类型：{', '.join(analysis.target_audience.get('occupation', ['办公室职员']))}
- 收入水平：{analysis.target_audience.get('income_level', '中等')}

🧠 智能答题策略：
"""
        
        for strategy in analysis.success_strategies:
            guidance += f"- {strategy}\n"
        
        if analysis.trap_questions:
            guidance += "\n⚠️ 陷阱题目避坑指南：\n"
            for trap in analysis.trap_questions:
                guidance += f"- {trap.get('question', '')}：{trap.get('correct_strategy', '')}\n"
        
        guidance += f"""

✅ 推荐答案模式：
- 年龄偏好：{analysis.recommended_answers.get('age_preference', '中等年龄')}
- 收入偏好：{analysis.recommended_answers.get('income_preference', '中等收入')}
- 职业偏好：{analysis.recommended_answers.get('occupation_preference', '稳定职业')}

📋 敢死队成功经验：
"""
        
        # 添加具体成功经验
        for i, exp in enumerate(successful_experiences[:5], 1):
            guidance += f"""
经验{i}：{exp.digital_human_profile.get('name', '数字人')}的成功做法
- 题目：{exp.question_content[:100]}...
- 答案：{exp.correct_answer}
- 理由：{exp.answer_reasoning}
"""
        
        guidance += f"""

🎯 你的作答要求：
1. 严格按照{target_digital_human.get('name', '你')}的身份特征回答
2. 参考以上成功经验和策略
3. 避免已知的陷阱题目
4. 选择符合目标人群特征的答案
5. 完成所有题目，确保100%答题率

分析可信度：{analysis.analysis_confidence:.1%}
        """
        
        return guidance.strip()
    
    def _generate_basic_guidance(self, target_digital_human: Dict) -> str:
        """生成基础指导（当没有分析结果时）"""
        return f"""
你是{target_digital_human.get('name', '未知')}，年龄{target_digital_human.get('age', '30')}岁，职业是{target_digital_human.get('job', '职员')}。

请按照你的身份特征认真回答所有问题，选择最符合你个人情况的选项。
        """
    
    async def cleanup_temporary_data(self, questionnaire_url: str) -> bool:
        """清理指定问卷的临时数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 清理临时经验
            cursor.execute('''
                DELETE FROM temporary_experiences 
                WHERE questionnaire_url = ?
            ''', (questionnaire_url,))
            
            # 清理问卷分析
            cursor.execute('''
                DELETE FROM questionnaire_analyses 
                WHERE questionnaire_url = ?
            ''', (questionnaire_url,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ 已清理问卷临时数据: {questionnaire_url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 清理临时数据失败: {e}")
            return False

# 单例模式
_dual_kb_system = None

def get_dual_knowledge_base() -> DualKnowledgeBaseSystem:
    """获取双知识库系统单例"""
    global _dual_kb_system
    if _dual_kb_system is None:
        _dual_kb_system = DualKnowledgeBaseSystem()
    return _dual_kb_system

# 测试代码
async def test_dual_knowledge_base():
    """测试双知识库系统"""
    kb = get_dual_knowledge_base()
    
    print("🧪 测试双知识库系统")
    
    # 测试临时经验保存
    test_experience = TemporaryExperience(
        experience_id="test_exp_001",
        questionnaire_url="https://test.wjx.cn/test",
        question_content="您的年龄是？",
        correct_answer="25-30岁",
        wrong_answers=[],
        answer_reasoning="符合目标人群",
        digital_human_id="dh_001",
        digital_human_profile={
            "name": "测试小雅",
            "age": 28,
            "job": "产品经理"
        },
        success=True,
        page_number=1,
        timestamp=datetime.now().isoformat()
    )
    
    success = await kb.save_temporary_experience(test_experience)
    print(f"保存临时经验: {'成功' if success else '失败'}")
    
    # 测试经验检索
    experiences = await kb.get_temporary_experiences("https://test.wjx.cn/test")
    print(f"检索到经验数量: {len(experiences)}")
    
    # 测试问卷分析
    analysis = await kb.analyze_questionnaire_with_gemini(
        "https://test.wjx.cn/test", experiences
    )
    print(f"问卷分析: {'成功' if analysis else '失败'}")
    
    # 测试指导生成
    target_human = {
        "name": "测试小明",
        "age": 30,
        "job": "软件工程师",
        "income": "12000"
    }
    
    guidance = await kb.generate_guidance_for_target_team(
        "https://test.wjx.cn/test", target_human
    )
    print(f"指导生成长度: {len(guidance)} 字符")
    
    # 清理测试数据
    await kb.cleanup_temporary_data("https://test.wjx.cn/test")
    print("✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_dual_knowledge_base()) 