#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第三阶段：知识库分析和目标团队选择模块
基于敢死队经验，智能分析问卷特征，选择最佳目标团队
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import statistics
from collections import Counter

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

logger = logging.getLogger(__name__)

@dataclass
class QuestionnaireProfile:
    """问卷画像数据类"""
    questionnaire_url: str
    session_id: str
    difficulty_level: str  # easy, medium, hard
    target_demographics: Dict
    success_patterns: List[str]
    failure_patterns: List[str]
    recommended_strategies: List[str]
    confidence_score: float
    sample_size: int

@dataclass
class PersonaMatch:
    """数字人匹配结果"""
    persona_id: int
    persona_name: str
    persona_info: Dict
    match_score: float
    match_reasons: List[str]
    predicted_success_rate: float

class QuestionnaireAnalyzer:
    """问卷分析器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.knowledge_base = QuestionnaireKnowledgeBase(db_manager)
    
    async def analyze_questionnaire_profile(self, session_id: str, questionnaire_url: str) -> QuestionnaireProfile:
        """分析问卷画像"""
        try:
            logger.info(f"📊 开始分析问卷画像: {questionnaire_url}")
            
            # 获取基础分析数据
            basic_analysis = self.knowledge_base.analyze_questionnaire_requirements(session_id, questionnaire_url)
            
            if not basic_analysis:
                logger.warning("⚠️ 没有找到分析数据，使用默认画像")
                return self._create_default_profile(questionnaire_url, session_id)
            
            # 计算难度等级
            difficulty = self._calculate_difficulty_level(basic_analysis)
            
            # 提取成功模式
            success_patterns = await self._extract_success_patterns(session_id, questionnaire_url)
            
            # 提取失败模式
            failure_patterns = await self._extract_failure_patterns(session_id, questionnaire_url)
            
            # 生成推荐策略
            strategies = self._generate_recommended_strategies(basic_analysis, success_patterns, failure_patterns)
            
            # 计算置信度分数
            confidence = self._calculate_confidence_score(basic_analysis)
            
            profile = QuestionnaireProfile(
                questionnaire_url=questionnaire_url,
                session_id=session_id,
                difficulty_level=difficulty,
                target_demographics=basic_analysis.get("target_demographics", {}),
                success_patterns=success_patterns,
                failure_patterns=failure_patterns,
                recommended_strategies=strategies,
                confidence_score=confidence,
                sample_size=basic_analysis.get("success_count", 0) + basic_analysis.get("failure_count", 0)
            )
            
            logger.info(f"✅ 问卷画像分析完成: 难度{difficulty}, 置信度{confidence:.2f}")
            return profile
            
        except Exception as e:
            logger.error(f"❌ 问卷画像分析失败: {e}")
            return self._create_default_profile(questionnaire_url, session_id)
    
    def _create_default_profile(self, questionnaire_url: str, session_id: str) -> QuestionnaireProfile:
        """创建默认问卷画像"""
        return QuestionnaireProfile(
            questionnaire_url=questionnaire_url,
            session_id=session_id,
            difficulty_level="medium",
            target_demographics={
                "age_range": {"min": 18, "max": 65, "avg": 35},
                "preferred_genders": ["男", "女"],
                "preferred_professions": ["学生", "上班族", "自由职业"],
                "sample_size": 0
            },
            success_patterns=["保守策略适用", "简短回答更好"],
            failure_patterns=["过于特殊的选择可能失败"],
            recommended_strategies=["使用保守策略", "选择常见选项", "避免极端答案"],
            confidence_score=0.5,
            sample_size=0
        )
    
    def _calculate_difficulty_level(self, analysis: Dict) -> str:
        """计算问卷难度等级"""
        success_rate = analysis.get("success_rate", 0.5)
        
        if success_rate >= 0.8:
            return "easy"
        elif success_rate >= 0.5:
            return "medium"
        else:
            return "hard"
    
    async def _extract_success_patterns(self, session_id: str, questionnaire_url: str) -> List[str]:
        """提取成功模式"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                sql = """
                SELECT experience_description, answer_choice, question_type
                FROM questionnaire_knowledge 
                WHERE session_id = %s AND questionnaire_url = %s 
                AND experience_type = 'success'
                """
                cursor.execute(sql, (session_id, questionnaire_url))
                results = cursor.fetchall()
                
                patterns = []
                for result in results:
                    if result[0]:  # experience_description
                        patterns.append(result[0])
                
                # 分析模式
                analyzed_patterns = self._analyze_patterns(patterns)
                return analyzed_patterns
                
        except Exception as e:
            logger.error(f"❌ 提取成功模式失败: {e}")
            return ["保守策略适用"]
        finally:
            if 'connection' in locals():
                connection.close()
    
    async def _extract_failure_patterns(self, session_id: str, questionnaire_url: str) -> List[str]:
        """提取失败模式"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                sql = """
                SELECT experience_description, answer_choice, question_type
                FROM questionnaire_knowledge 
                WHERE session_id = %s AND questionnaire_url = %s 
                AND experience_type = 'failure'
                """
                cursor.execute(sql, (session_id, questionnaire_url))
                results = cursor.fetchall()
                
                patterns = []
                for result in results:
                    if result[0]:  # experience_description
                        patterns.append(result[0])
                
                # 分析模式
                analyzed_patterns = self._analyze_patterns(patterns)
                return analyzed_patterns
                
        except Exception as e:
            logger.error(f"❌ 提取失败模式失败: {e}")
            return ["激进策略可能失败"]
        finally:
            if 'connection' in locals():
                connection.close()
    
    def _analyze_patterns(self, patterns: List[str]) -> List[str]:
        """分析模式，提取关键信息"""
        if not patterns:
            return []
        
        analyzed = []
        
        # 统计策略类型
        conservative_count = sum(1 for p in patterns if "保守" in p)
        aggressive_count = sum(1 for p in patterns if "激进" in p)
        random_count = sum(1 for p in patterns if "随机" in p)
        
        if conservative_count > 0:
            analyzed.append(f"保守策略表现良好 ({conservative_count}次)")
        if aggressive_count > 0:
            analyzed.append(f"激进策略需要谨慎 ({aggressive_count}次)")
        if random_count > 0:
            analyzed.append(f"随机策略有一定效果 ({random_count}次)")
        
        # 统计问题类型
        single_choice_count = sum(1 for p in patterns if "single_choice" in p)
        text_input_count = sum(1 for p in patterns if "text_input" in p)
        
        if single_choice_count > 0:
            analyzed.append(f"单选题处理经验丰富 ({single_choice_count}次)")
        if text_input_count > 0:
            analyzed.append(f"文本输入题需要注意 ({text_input_count}次)")
        
        return analyzed[:5]  # 返回前5个最重要的模式
    
    def _generate_recommended_strategies(self, analysis: Dict, success_patterns: List[str], failure_patterns: List[str]) -> List[str]:
        """生成推荐策略"""
        strategies = []
        
        success_rate = analysis.get("success_rate", 0.5)
        
        # 基于成功率推荐策略
        if success_rate >= 0.8:
            strategies.append("问卷相对简单，可以使用多种策略")
        elif success_rate >= 0.5:
            strategies.append("问卷难度适中，建议使用保守策略为主")
        else:
            strategies.append("问卷较难，需要仔细分析每个问题")
        
        # 基于成功模式推荐
        if any("保守" in p for p in success_patterns):
            strategies.append("优先使用保守策略")
        
        if any("简短" in p for p in success_patterns):
            strategies.append("文本输入使用简短回答")
        
        # 基于失败模式避免
        if any("激进" in p for p in failure_patterns):
            strategies.append("避免过于激进的选择")
        
        if any("特殊" in p for p in failure_patterns):
            strategies.append("避免选择特殊或极端选项")
        
        return strategies[:5]  # 返回前5个策略
    
    def _calculate_confidence_score(self, analysis: Dict) -> float:
        """计算置信度分数"""
        sample_size = analysis.get("success_count", 0) + analysis.get("failure_count", 0)
        
        if sample_size == 0:
            return 0.5  # 默认置信度
        elif sample_size < 5:
            return 0.6  # 样本较少
        elif sample_size < 10:
            return 0.8  # 样本适中
        else:
            return 0.9  # 样本充足

class PersonaMatchingEngine:
    """数字人匹配引擎"""
    
    def __init__(self, questionnaire_manager: QuestionnaireManager):
        self.questionnaire_manager = questionnaire_manager
        self.xiaoshe_client = questionnaire_manager.xiaoshe_client
    
    async def find_best_target_team(self, profile: QuestionnaireProfile, target_count: int = 10) -> List[PersonaMatch]:
        """寻找最佳目标团队"""
        try:
            logger.info(f"🎯 开始寻找最佳目标团队，需要{target_count}人")
            
            # 生成智能查询
            smart_query = self._generate_smart_query(profile)
            logger.info(f"🔍 智能查询: {smart_query}")
            
            # 查询候选数字人
            candidates = await self._query_candidate_personas(smart_query, target_count * 3)  # 查询3倍数量用于筛选
            
            if not candidates:
                logger.warning("⚠️ 没有找到候选数字人，使用备用查询")
                candidates = await self._query_candidate_personas("找一些活跃的数字人", target_count * 2)
            
            # 计算匹配分数
            matches = []
            for candidate in candidates:
                match = self._calculate_persona_match(candidate, profile)
                if match.match_score > 0.3:  # 只保留匹配度较高的
                    matches.append(match)
            
            # 按匹配分数排序
            matches.sort(key=lambda x: x.match_score, reverse=True)
            
            # 返回前N个最佳匹配
            best_matches = matches[:target_count]
            
            logger.info(f"✅ 找到 {len(best_matches)} 个最佳匹配的数字人")
            return best_matches
            
        except Exception as e:
            logger.error(f"❌ 寻找目标团队失败: {e}")
            return []
    
    def _generate_smart_query(self, profile: QuestionnaireProfile) -> str:
        """生成智能查询语句"""
        demographics = profile.target_demographics
        
        query_parts = []
        
        # 年龄条件
        age_range = demographics.get("age_range", {})
        if age_range.get("min") and age_range.get("max"):
            query_parts.append(f"年龄在{age_range['min']}-{age_range['max']}岁")
        elif age_range.get("avg"):
            avg_age = age_range["avg"]
            query_parts.append(f"年龄在{max(18, int(avg_age-10))}-{min(65, int(avg_age+10))}岁")
        
        # 性别条件
        genders = demographics.get("preferred_genders", [])
        if genders and len(genders) < 3:  # 如果不是所有性别都包含
            query_parts.append(f"性别为{'/'.join(genders)}")
        
        # 职业条件
        professions = demographics.get("preferred_professions", [])
        if professions:
            top_professions = professions[:3]  # 取前3个职业
            query_parts.append(f"职业包括{'/'.join(top_professions)}")
        
        # 基于问卷难度调整查询
        if profile.difficulty_level == "easy":
            query_parts.append("活跃度较高")
        elif profile.difficulty_level == "hard":
            query_parts.append("经验丰富且耐心")
        
        # 组合查询
        if query_parts:
            query = f"找一些{', '.join(query_parts)}的数字人来参与问卷调查"
        else:
            query = "找一些活跃的数字人来参与问卷调查"
        
        return query
    
    async def _query_candidate_personas(self, query: str, limit: int) -> List[Dict]:
        """查询候选数字人"""
        try:
            candidates = await self.xiaoshe_client.query_personas(query, limit)
            logger.info(f"📋 查询到 {len(candidates)} 个候选数字人")
            return candidates
        except Exception as e:
            logger.error(f"❌ 查询候选数字人失败: {e}")
            return []
    
    def _calculate_persona_match(self, persona: Dict, profile: QuestionnaireProfile) -> PersonaMatch:
        """计算数字人匹配度"""
        try:
            match_score = 0.0
            match_reasons = []
            
            # 基础信息匹配
            age = persona.get("age", 30)
            gender = persona.get("gender", "")
            profession = persona.get("profession", "")
            
            demographics = profile.target_demographics
            
            # 年龄匹配 (权重: 0.3)
            age_range = demographics.get("age_range", {})
            if age_range.get("min") and age_range.get("max"):
                if age_range["min"] <= age <= age_range["max"]:
                    match_score += 0.3
                    match_reasons.append(f"年龄匹配 ({age}岁)")
                else:
                    # 部分匹配
                    age_diff = min(abs(age - age_range["min"]), abs(age - age_range["max"]))
                    if age_diff <= 5:
                        match_score += 0.15
                        match_reasons.append(f"年龄接近 ({age}岁)")
            else:
                match_score += 0.15  # 默认部分匹配
            
            # 性别匹配 (权重: 0.2)
            preferred_genders = demographics.get("preferred_genders", [])
            if not preferred_genders or gender in preferred_genders:
                match_score += 0.2
                if gender:
                    match_reasons.append(f"性别匹配 ({gender})")
            
            # 职业匹配 (权重: 0.3)
            preferred_professions = demographics.get("preferred_professions", [])
            if not preferred_professions or profession in preferred_professions:
                match_score += 0.3
                if profession:
                    match_reasons.append(f"职业匹配 ({profession})")
            else:
                # 职业相关性匹配
                if self._is_profession_related(profession, preferred_professions):
                    match_score += 0.15
                    match_reasons.append(f"职业相关 ({profession})")
            
            # 活跃度匹配 (权重: 0.2)
            activity_level = persona.get("activity_level", 0.5)
            if profile.difficulty_level == "easy" and activity_level > 0.7:
                match_score += 0.2
                match_reasons.append("高活跃度适合简单问卷")
            elif profile.difficulty_level == "hard" and activity_level > 0.8:
                match_score += 0.2
                match_reasons.append("高活跃度适合复杂问卷")
            else:
                match_score += 0.1  # 基础活跃度
            
            # 预测成功率
            predicted_success_rate = self._predict_success_rate(persona, profile, match_score)
            
            return PersonaMatch(
                persona_id=persona.get("id", 0),
                persona_name=persona.get("name", "未知"),
                persona_info=persona,
                match_score=min(1.0, match_score),  # 确保不超过1.0
                match_reasons=match_reasons,
                predicted_success_rate=predicted_success_rate
            )
            
        except Exception as e:
            logger.error(f"❌ 计算数字人匹配度失败: {e}")
            return PersonaMatch(
                persona_id=persona.get("id", 0),
                persona_name=persona.get("name", "未知"),
                persona_info=persona,
                match_score=0.5,
                match_reasons=["默认匹配"],
                predicted_success_rate=0.5
            )
    
    def _is_profession_related(self, profession: str, preferred_professions: List[str]) -> bool:
        """判断职业是否相关"""
        if not profession or not preferred_professions:
            return False
        
        # 定义职业相关性映射
        profession_groups = {
            "学生": ["研究生", "本科生", "博士生", "实习生"],
            "上班族": ["白领", "职员", "经理", "主管", "专员"],
            "自由职业": ["自媒体", "设计师", "写手", "摄影师", "咨询师"],
            "技术": ["程序员", "工程师", "开发者", "架构师", "技术员"],
            "教育": ["教师", "教授", "讲师", "培训师", "教育工作者"],
            "医疗": ["医生", "护士", "药师", "医疗工作者"],
            "金融": ["银行员工", "投资顾问", "会计师", "金融分析师"]
        }
        
        for group, related_professions in profession_groups.items():
            if group in preferred_professions and profession in related_professions:
                return True
            if profession in preferred_professions and group in related_professions:
                return True
        
        return False
    
    def _predict_success_rate(self, persona: Dict, profile: QuestionnaireProfile, match_score: float) -> float:
        """预测成功率"""
        base_rate = 0.7  # 基础成功率
        
        # 基于匹配分数调整
        score_adjustment = (match_score - 0.5) * 0.4  # 匹配分数的影响
        
        # 基于问卷难度调整
        if profile.difficulty_level == "easy":
            difficulty_adjustment = 0.2
        elif profile.difficulty_level == "medium":
            difficulty_adjustment = 0.0
        else:  # hard
            difficulty_adjustment = -0.2
        
        # 基于置信度调整
        confidence_adjustment = (profile.confidence_score - 0.5) * 0.2
        
        predicted_rate = base_rate + score_adjustment + difficulty_adjustment + confidence_adjustment
        
        return max(0.1, min(0.95, predicted_rate))  # 限制在0.1-0.95之间

class Phase3KnowledgeAnalysisSystem:
    """第三阶段知识库分析系统"""
    
    def __init__(self):
        self.questionnaire_manager = QuestionnaireManager()
        self.scout_system = ScoutAutomationSystem()
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.analyzer = QuestionnaireAnalyzer(self.db_manager)
        self.matching_engine = PersonaMatchingEngine(self.questionnaire_manager)
    
    async def analyze_and_select_target_team(self, session_id: str, questionnaire_url: str, target_count: int = 10) -> Dict:
        """分析问卷并选择目标团队"""
        try:
            logger.info(f"🎯 第三阶段：分析问卷并选择目标团队")
            logger.info(f"📋 问卷URL: {questionnaire_url}")
            logger.info(f"👥 目标团队人数: {target_count}")
            
            # 1. 分析问卷画像
            logger.info(f"📊 步骤1: 分析问卷画像...")
            profile = await self.analyzer.analyze_questionnaire_profile(session_id, questionnaire_url)
            
            # 2. 寻找最佳目标团队
            logger.info(f"🔍 步骤2: 寻找最佳目标团队...")
            target_matches = await self.matching_engine.find_best_target_team(profile, target_count)
            
            # 3. 生成分析报告
            logger.info(f"📈 步骤3: 生成分析报告...")
            report = self._generate_analysis_report(profile, target_matches)
            
            logger.info(f"✅ 第三阶段分析完成")
            return {
                "success": True,
                "profile": profile,
                "target_matches": target_matches,
                "report": report
            }
            
        except Exception as e:
            logger.error(f"❌ 第三阶段分析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_analysis_report(self, profile: QuestionnaireProfile, target_matches: List[PersonaMatch]) -> Dict:
        """生成分析报告"""
        try:
            # 统计匹配情况
            if target_matches:
                avg_match_score = statistics.mean([m.match_score for m in target_matches])
                avg_predicted_success = statistics.mean([m.predicted_success_rate for m in target_matches])
                
                # 统计匹配原因
                all_reasons = []
                for match in target_matches:
                    all_reasons.extend(match.match_reasons)
                reason_counts = Counter(all_reasons)
                top_reasons = reason_counts.most_common(5)
            else:
                avg_match_score = 0.0
                avg_predicted_success = 0.0
                top_reasons = []
            
            report = {
                "questionnaire_analysis": {
                    "difficulty_level": profile.difficulty_level,
                    "confidence_score": profile.confidence_score,
                    "sample_size": profile.sample_size,
                    "success_patterns_count": len(profile.success_patterns),
                    "failure_patterns_count": len(profile.failure_patterns),
                    "strategies_count": len(profile.recommended_strategies)
                },
                "team_selection": {
                    "requested_count": len(target_matches),
                    "found_count": len(target_matches),
                    "avg_match_score": avg_match_score,
                    "avg_predicted_success": avg_predicted_success,
                    "top_match_reasons": [{"reason": reason, "count": count} for reason, count in top_reasons]
                },
                "recommendations": self._generate_recommendations(profile, target_matches),
                "generated_at": datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 生成分析报告失败: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, profile: QuestionnaireProfile, target_matches: List[PersonaMatch]) -> List[str]:
        """生成推荐建议"""
        recommendations = []
        
        # 基于问卷难度的建议
        if profile.difficulty_level == "easy":
            recommendations.append("问卷难度较低，可以使用标准策略进行大规模投放")
        elif profile.difficulty_level == "medium":
            recommendations.append("问卷难度适中，建议使用保守策略，关注答题质量")
        else:
            recommendations.append("问卷难度较高，建议分批投放，密切监控答题情况")
        
        # 基于匹配情况的建议
        if target_matches:
            avg_match_score = statistics.mean([m.match_score for m in target_matches])
            if avg_match_score >= 0.8:
                recommendations.append("目标团队匹配度很高，预期成功率良好")
            elif avg_match_score >= 0.6:
                recommendations.append("目标团队匹配度适中，建议优化答题策略")
            else:
                recommendations.append("目标团队匹配度较低，建议重新筛选或调整策略")
        else:
            recommendations.append("未找到合适的目标团队，建议扩大搜索范围或调整筛选条件")
        
        # 基于置信度的建议
        if profile.confidence_score < 0.6:
            recommendations.append("分析置信度较低，建议增加敢死队样本数量")
        
        return recommendations

# 测试函数
async def test_phase3_system():
    """测试第三阶段系统"""
    print("🧪 测试第三阶段知识库分析系统")
    print("="*50)
    
    system = Phase3KnowledgeAnalysisSystem()
    
    try:
        # 使用模拟的session_id和URL进行测试
        test_session_id = "test_session_123"
        test_url = "https://www.wjx.cn/vm/test_questionnaire.aspx"
        
        result = await system.analyze_and_select_target_team(
            session_id=test_session_id,
            questionnaire_url=test_url,
            target_count=5
        )
        
        if result["success"]:
            print("✅ 第三阶段测试成功")
            print(f"📊 问卷画像: {result['profile'].difficulty_level}")
            print(f"👥 找到目标团队: {len(result['target_matches'])}人")
            print(f"📈 分析报告已生成")
        else:
            print(f"❌ 第三阶段测试失败: {result['error']}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    asyncio.run(test_phase3_system()) 