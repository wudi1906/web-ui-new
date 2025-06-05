#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试增强的敢死队成功判断逻辑
基于答题数量和错误类型的智能分类
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 模拟ScoutExperience数据结构
class MockScoutExperience:
    def __init__(self, scout_name: str, questions_count: int, error_type: str = "none", 
                 technical_error_details: str = "", trap_triggered: bool = False):
        self.scout_id = f"scout_{scout_name.lower()}"
        self.scout_name = scout_name
        self.page_number = 1
        self.page_screenshot = ""
        self.page_content = f"{scout_name}的答题内容"
        self.questions_answered = [{"question": f"题目{i+1}", "answer": f"选项{i+1}"} for i in range(questions_count)]
        self.success = error_type in ["none", "normal_completion", "trap_termination"]
        self.failure_reason = technical_error_details if not self.success else None
        self.timestamp = datetime.now().isoformat()
        
        # 新增字段
        self.error_type = error_type
        self.questions_count = questions_count
        self.completion_depth = min(questions_count / 15, 1.0)
        self.trap_triggered = trap_triggered
        self.browser_error_displayed = error_type in ["code_error", "server_error", "api_error"]
        self.technical_error_details = technical_error_details

def analyze_scout_experiences(scout_experiences: List[MockScoutExperience]) -> Dict:
    """
    模拟新的成功判断逻辑测试
    """
    logger.info("🧪 开始测试增强的敢死队成功判断逻辑")
    logger.info("=" * 60)
    
    # 按照用户需求重新分类经验
    code_server_errors = []  # 代码/服务器错误
    normal_completion_experiences = []  # 正常答题经验（包括被陷阱题终止）
    
    for exp in scout_experiences:
        if exp.error_type in ["code_error", "server_error", "api_error"]:
            code_server_errors.append(exp)
            logger.warning(f"⚠️ 发现技术错误: {exp.scout_name} - {exp.error_type}: {exp.technical_error_details}")
        else:
            # 正常答题经验（包括被陷阱题终止的情况）
            normal_completion_experiences.append(exp)
    
    logger.info(f"📊 经验分类结果:")
    logger.info(f"   技术错误: {len(code_server_errors)} 个")
    logger.info(f"   正常答题: {len(normal_completion_experiences)} 个")
    
    # 处理技术错误
    if code_server_errors:
        logger.error(f"🚨 发现 {len(code_server_errors)} 个技术错误，需要调试:")
        for exp in code_server_errors:
            logger.error(f"   {exp.scout_name}: {exp.error_type} - {exp.technical_error_details}")
    
    # 如果没有正常答题经验，无法进行分析
    if len(normal_completion_experiences) == 0:
        logger.error(f"❌ 所有敢死队都遇到技术错误，无法进行有效分析")
        return {"analysis_possible": False, "reason": "all_technical_errors"}
    
    # 按答题数量排序，确定"相对成功"的经验
    normal_completion_experiences.sort(key=lambda x: x.questions_count, reverse=True)
    
    # 选择答题数量最多的经验作为"成功"经验
    max_questions = normal_completion_experiences[0].questions_count
    successful_experiences = [exp for exp in normal_completion_experiences if exp.questions_count == max_questions]
    failed_experiences = [exp for exp in normal_completion_experiences if exp.questions_count < max_questions]
    
    logger.info(f"📊 按答题数量分析结果:")
    logger.info(f"   最多答题数量: {max_questions} 题")
    logger.info(f"   最成功经验: {len(successful_experiences)} 个")
    logger.info(f"   相对失败经验: {len(failed_experiences)} 个")
    
    # 显示详细的答题情况
    for exp in successful_experiences:
        status = "🏆 最成功" if exp.questions_count == max_questions else "📊 次优"
        trap_info = " (触发陷阱题)" if exp.trap_triggered else ""
        logger.info(f"   {status}: {exp.scout_name} - {exp.questions_count}题{trap_info}")
    
    # 如果最多答题数量为0，说明所有人都无法开始答题
    if max_questions == 0:
        logger.error(f"❌ 所有敢死队答题数量都为0，可能存在页面加载或题目识别问题")
        return {"analysis_possible": False, "reason": "zero_questions"}
    
    logger.info(f"✅ 分析可以继续，基于{len(successful_experiences)}个最成功经验")
    
    return {
        "analysis_possible": True,
        "max_questions": max_questions,
        "successful_experiences": len(successful_experiences),
        "failed_experiences": len(failed_experiences),
        "technical_errors": len(code_server_errors),
        "most_successful_scouts": [exp.scout_name for exp in successful_experiences]
    }

async def test_scenario_1_mixed_results():
    """测试场景1：混合结果 - 有技术错误，有正常答题"""
    logger.info("\n🧪 测试场景1：混合结果")
    
    experiences = [
        MockScoutExperience("张小明", 8, "normal_completion"),  # 正常完成8题
        MockScoutExperience("李小红", 5, "trap_termination", trap_triggered=True),  # 陷阱题终止，答了5题
        MockScoutExperience("王小华", 0, "api_error", "429 API配额超限"),  # API错误
        MockScoutExperience("赵小敏", 8, "normal_completion"),  # 正常完成8题
        MockScoutExperience("陈小强", 0, "code_error", "ModuleNotFoundError: No module named 'xxx'")  # 代码错误
    ]
    
    result = analyze_scout_experiences(experiences)
    logger.info(f"🎯 结果: {result}")
    assert result["analysis_possible"] == True
    assert result["max_questions"] == 8
    assert result["most_successful_scouts"] == ["张小明", "赵小敏"]

async def test_scenario_2_all_technical_errors():
    """测试场景2：全部技术错误"""
    logger.info("\n🧪 测试场景2：全部技术错误")
    
    experiences = [
        MockScoutExperience("张小明", 0, "code_error", "语法错误"),
        MockScoutExperience("李小红", 0, "api_error", "网络超时"),
        MockScoutExperience("王小华", 0, "server_error", "服务器500错误")
    ]
    
    result = analyze_scout_experiences(experiences)
    logger.info(f"🎯 结果: {result}")
    assert result["analysis_possible"] == False
    assert result["reason"] == "all_technical_errors"

async def test_scenario_3_zero_questions():
    """测试场景3：都无法答题"""
    logger.info("\n🧪 测试场景3：都无法答题")
    
    experiences = [
        MockScoutExperience("张小明", 0, "normal_completion"),  # 正常但答题数为0
        MockScoutExperience("李小红", 0, "trap_termination"),   # 陷阱题但答题数也为0
    ]
    
    result = analyze_scout_experiences(experiences)
    logger.info(f"🎯 结果: {result}")
    assert result["analysis_possible"] == False
    assert result["reason"] == "zero_questions"

async def test_scenario_4_trap_questions():
    """测试场景4：陷阱题情况"""
    logger.info("\n🧪 测试场景4：陷阱题情况")
    
    experiences = [
        MockScoutExperience("张小明", 12, "normal_completion"),  # 正常完成12题
        MockScoutExperience("李小红", 15, "normal_completion"),  # 正常完成15题（最多）
        MockScoutExperience("王小华", 8, "trap_termination", trap_triggered=True),  # 陷阱题终止8题
        MockScoutExperience("赵小敏", 15, "trap_termination", trap_triggered=True)   # 陷阱题终止但答了15题
    ]
    
    result = analyze_scout_experiences(experiences)
    logger.info(f"🎯 结果: {result}")
    assert result["analysis_possible"] == True
    assert result["max_questions"] == 15
    assert result["most_successful_scouts"] == ["李小红", "赵小敏"]

async def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始测试增强的敢死队成功判断逻辑")
    logger.info("基于答题数量和错误类型的智能分类")
    logger.info("=" * 80)
    
    try:
        await test_scenario_1_mixed_results()
        await test_scenario_2_all_technical_errors()
        await test_scenario_3_zero_questions()
        await test_scenario_4_trap_questions()
        
        logger.info("\n✅ 所有测试通过！新的成功判断逻辑工作正常")
        logger.info("🎯 核心特点：")
        logger.info("   1. 技术错误会被正确识别和分类")
        logger.info("   2. 按答题数量判断相对成功性")
        logger.info("   3. 陷阱题终止被视为正常答题")
        logger.info("   4. 只有在有正常答题经验时才进行分析")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_all_tests()) 