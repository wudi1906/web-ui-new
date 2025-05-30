#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能知识库系统测试脚本
演示：敢死队经验收集 -> 智能分析 -> 大部队指导生成
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List

# 尝试导入智能知识库
try:
    from intelligent_knowledge_base import (
        IntelligentKnowledgeBase,
        AnswerExperience,
        QuestionType,
        GuidanceRule
    )
    KNOWLEDGE_BASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 智能知识库模块导入失败: {e}")
    KNOWLEDGE_BASE_AVAILABLE = False

from config import get_config

class MockQuestionnaireSystem:
    """模拟问卷系统，用于测试智能知识库"""
    
    def __init__(self):
        self.session_id = f"test_session_{int(time.time())}"
        self.questionnaire_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"
        
        if KNOWLEDGE_BASE_AVAILABLE:
            self.knowledge_base = IntelligentKnowledgeBase()
        else:
            self.knowledge_base = None
            print("❌ 智能知识库不可用，将使用模拟模式")
    
    def generate_mock_scout_experiences(self) -> List[AnswerExperience]:
        """生成模拟的敢死队经验数据"""
        experiences = [
            # 成功经验1: 年轻女性选择手机
            AnswerExperience(
                persona_id=1,
                persona_name="林心怡",
                persona_features={"age": 25, "gender": "女", "profession": "学生"},
                question_content="您平时最常使用的电子设备是？",
                question_type=QuestionType.SINGLE_CHOICE,
                available_options=["手机", "电脑", "平板", "其他"],
                chosen_answer="手机",
                success=True,
                reasoning="作为年轻人，手机是最常用的设备，用于社交和学习"
            ),
            
            # 成功经验2: 中年男性选择电脑
            AnswerExperience(
                persona_id=2,
                persona_name="张明",
                persona_features={"age": 35, "gender": "男", "profession": "软件工程师"},
                question_content="您平时最常使用的电子设备是？",
                question_type=QuestionType.SINGLE_CHOICE,
                available_options=["手机", "电脑", "平板", "其他"],
                chosen_answer="电脑",
                success=True,
                reasoning="作为软件工程师，电脑是工作必需品"
            ),
            
            # 成功经验3: 购物习惯
            AnswerExperience(
                persona_id=1,
                persona_name="林心怡",
                persona_features={"age": 25, "gender": "女", "profession": "学生"},
                question_content="您通常在哪里购买日用品？",
                question_type=QuestionType.SINGLE_CHOICE,
                available_options=["超市", "网购", "便利店", "其他"],
                chosen_answer="网购",
                success=True,
                reasoning="年轻人更喜欢网购，方便且选择多样"
            ),
            
            # 失败经验: 错误选择
            AnswerExperience(
                persona_id=3,
                persona_name="王老师",
                persona_features={"age": 50, "gender": "男", "profession": "教师"},
                question_content="您对新技术的接受程度如何？",
                question_type=QuestionType.SCALE_RATING,
                available_options=["很低", "较低", "一般", "较高", "很高"],
                chosen_answer="很高",
                success=False,
                reasoning="选择过于激进，不符合中年教师的特征",
                error_message="答案与人物设定不符"
            )
        ]
        
        return experiences
    
    async def simulate_scout_phase(self) -> bool:
        """模拟敢死队阶段"""
        print("🚀 开始模拟敢死队阶段")
        print("=" * 50)
        
        if not self.knowledge_base:
            print("❌ 知识库不可用，跳过敢死队阶段")
            return False
        
        # 生成模拟经验
        experiences = self.generate_mock_scout_experiences()
        
        # 保存经验到知识库
        for i, experience in enumerate(experiences, 1):
            print(f"📝 保存敢死队经验 {i}/{len(experiences)}: {experience.persona_name}")
            print(f"   问题: {experience.question_content}")
            print(f"   选择: {experience.chosen_answer}")
            print(f"   结果: {'✅ 成功' if experience.success else '❌ 失败'}")
            
            success = await self.knowledge_base.save_answer_experience(
                self.session_id, self.questionnaire_url, experience
            )
            
            if success:
                print(f"   ✅ 经验已保存到知识库")
            else:
                print(f"   ❌ 经验保存失败")
            print()
        
        print(f"🎉 敢死队阶段完成，共收集 {len(experiences)} 条经验")
        return True
    
    async def simulate_analysis_phase(self) -> List[GuidanceRule]:
        """模拟分析阶段"""
        print("\n🧠 开始模拟分析阶段")
        print("=" * 50)
        
        if not self.knowledge_base:
            print("❌ 知识库不可用，返回空指导规则")
            return []
        
        print("🔍 分析敢死队经验，生成指导规则...")
        
        # 分析经验并生成指导规则
        guidance_rules = await self.knowledge_base.analyze_experiences_and_generate_guidance(
            self.session_id, self.questionnaire_url
        )
        
        print(f"✅ 分析完成，生成了 {len(guidance_rules)} 条指导规则")
        
        # 显示生成的指导规则
        for i, rule in enumerate(guidance_rules, 1):
            print(f"\n📋 指导规则 {i}:")
            print(f"   问题模式: {rule.question_pattern}")
            print(f"   推荐答案: {rule.recommended_answer}")
            print(f"   推荐理由: {rule.reasoning}")
            print(f"   置信度: {rule.confidence_score:.2f}")
        
        return guidance_rules
    
    async def simulate_target_phase(self) -> bool:
        """模拟大部队阶段"""
        print("\n🎯 开始模拟大部队阶段")
        print("=" * 50)
        
        if not self.knowledge_base:
            print("❌ 知识库不可用，跳过大部队阶段")
            return False
        
        # 模拟大部队成员
        target_personas = [
            {"age": 28, "gender": "女", "profession": "设计师", "name": "小美"},
            {"age": 32, "gender": "男", "profession": "销售", "name": "小李"},
            {"age": 26, "gender": "女", "profession": "护士", "name": "小王"}
        ]
        
        for i, persona in enumerate(target_personas, 1):
            print(f"👤 大部队成员 {i}: {persona['name']}")
            print(f"   特征: {persona['age']}岁{persona['gender']}, {persona['profession']}")
            
            # 获取个性化指导
            guidance_text = await self.knowledge_base.get_guidance_for_target_team(
                self.session_id, self.questionnaire_url, persona
            )
            
            if guidance_text:
                print(f"   📚 获取到指导经验:")
                # 显示指导内容的前200字符
                preview = guidance_text[:200] + "..." if len(guidance_text) > 200 else guidance_text
                print(f"   {preview}")
            else:
                print(f"   ⚠️ 未获取到相关指导经验")
            print()
        
        print("🎉 大部队阶段完成")
        return True
    
    def generate_mock_guidance_manually(self) -> str:
        """手动生成模拟指导文本（当知识库不可用时）"""
        return """
【答题指导经验】
根据敢死队的成功经验，请注意以下答题技巧：

1. 当遇到包含「电子设备使用」的题目时：
   推荐选择：根据年龄和职业特征选择（年轻人选手机，技术人员选电脑）
   理由: 不同年龄和职业群体有不同的设备使用习惯

2. 当遇到包含「购物习惯」的题目时：
   推荐选择：年轻人选择网购，中老年人选择实体店
   理由: 年轻人更习惯网络购物，中老年人更信任实体店

3. 当遇到包含「新技术接受度」的题目时：
   推荐选择：根据年龄适度选择，避免过于极端
   理由: 要符合人物设定的合理性

请根据以上经验，结合你的个人特征进行答题。
"""

async def test_complete_workflow():
    """测试完整的智能知识库工作流"""
    print("🤖 智能知识库系统完整测试")
    print("=" * 60)
    
    # 显示配置信息
    llm_config = get_config("llm")
    print(f"📋 配置信息:")
    print(f"   LLM模型: {llm_config.get('model', '未配置')}")
    print(f"   API密钥: {'已配置' if llm_config.get('api_key') else '未配置'}")
    print(f"   知识库可用: {'是' if KNOWLEDGE_BASE_AVAILABLE else '否'}")
    print()
    
    # 创建模拟系统
    system = MockQuestionnaireSystem()
    
    try:
        # 阶段1: 敢死队收集经验
        scout_success = await system.simulate_scout_phase()
        
        if scout_success:
            # 等待一下模拟处理时间
            print("⏳ 等待经验分析...")
            await asyncio.sleep(2)
            
            # 阶段2: 分析经验生成指导
            guidance_rules = await system.simulate_analysis_phase()
            
            # 等待一下
            await asyncio.sleep(1)
            
            # 阶段3: 大部队应用指导
            target_success = await system.simulate_target_phase()
            
            if target_success:
                print("\n🎉 完整工作流测试成功!")
                print("✅ 敢死队经验收集 -> ✅ 智能分析 -> ✅ 大部队指导应用")
            else:
                print("\n⚠️ 大部队阶段失败")
        else:
            print("\n❌ 敢死队阶段失败，演示手动指导生成")
            guidance_text = system.generate_mock_guidance_manually()
            print("📚 模拟指导内容:")
            print(guidance_text)
    
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

async def test_knowledge_base_components():
    """测试知识库各个组件"""
    print("\n🔧 测试知识库组件")
    print("=" * 40)
    
    if not KNOWLEDGE_BASE_AVAILABLE:
        print("❌ 知识库不可用，跳过组件测试")
        return
    
    try:
        kb = IntelligentKnowledgeBase()
        print("✅ 知识库初始化成功")
        
        # 测试Gemini模型初始化
        if kb.gemini_model:
            print("✅ Gemini模型初始化成功")
        else:
            print("⚠️ Gemini模型初始化失败，将使用基础功能")
        
        # 测试数据库连接
        try:
            connection = kb.db_manager.get_connection()
            if connection:
                print("✅ 数据库连接成功")
                connection.close()
            else:
                print("❌ 数据库连接失败")
        except Exception as e:
            print(f"❌ 数据库连接测试失败: {e}")
        
    except Exception as e:
        print(f"❌ 知识库组件测试失败: {e}")

def show_system_architecture():
    """显示系统架构说明"""
    print("\n📐 智能知识库系统架构")
    print("=" * 50)
    
    architecture = """
🏗️ 系统架构设计:

1. 【数据收集层】
   ├── 页面信息抓取器 (HTML + 截图)
   ├── 答题行为记录器 (选择 + 时间 + 路径)
   └── 结果状态监测器 (成功/失败/卡住位置)

2. 【智能分析层】
   ├── 多模态内容理解 (Gemini Vision - 省钱策略)
   ├── 数字人特征匹配器
   ├── 成功模式识别器
   └── 失败原因分析器

3. 【指导生成层】
   ├── 规则提取器
   ├── 提示词生成器
   └── 策略优化器

💡 省钱策略:
- 优先使用HTML分析，只在必要时使用多模态
- 缓存分析结果，避免重复调用
- 控制token使用量，精简提示词
- 批量处理，减少API调用次数

🔄 工作流程:
敢死队探路 -> 收集经验 -> 智能分析 -> 生成指导 -> 大部队应用
"""
    
    print(architecture)

async def main():
    """主函数"""
    print("🧠 智能问卷知识库系统测试")
    print("🎯 目标：实现省钱高效的Gemini多模态分析")
    print("=" * 60)
    
    # 显示系统架构
    show_system_architecture()
    
    # 测试知识库组件
    await test_knowledge_base_components()
    
    # 测试完整工作流
    await test_complete_workflow()
    
    print("\n" + "=" * 60)
    print("🎉 智能知识库系统测试完成!")
    print("💡 下一步：集成到实际的问卷填写流程中")

if __name__ == "__main__":
    asyncio.run(main()) 