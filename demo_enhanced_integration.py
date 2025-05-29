#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强系统集成演示
展示如何将新开发的增强系统与testWenjuanFinal.py完美集成
"""

import asyncio
import logging
import sys
import os
from typing import Dict, List

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from enhanced_browser_use_integration import EnhancedBrowserUseIntegration
from phase2_scout_automation import EnhancedScoutAutomationSystem
from questionnaire_system import DatabaseManager, DB_CONFIG

# 尝试导入testWenjuanFinal
try:
    import testWenjuanFinal
    TESTWENJUAN_AVAILABLE = True
except ImportError:
    TESTWENJUAN_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedQuestionnaireSystem:
    """增强的问卷系统 - 集成testWenjuanFinal.py的功能"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.browser_integration = EnhancedBrowserUseIntegration(self.db_manager)
        self.scout_system = EnhancedScoutAutomationSystem()
        
    async def run_single_digital_human_questionnaire(self, digital_human_id: int, questionnaire_url: str) -> Dict:
        """运行单个数字人的问卷填写（基于testWenjuanFinal.py）"""
        try:
            logger.info(f"🚀 启动数字人 {digital_human_id} 的问卷填写任务")
            
            if not TESTWENJUAN_AVAILABLE:
                logger.error("❌ testWenjuanFinal.py不可用，无法获取数字人信息")
                return {"success": False, "error": "testWenjuanFinal.py不可用"}
            
            # 1. 获取数字人信息
            digital_human = testWenjuanFinal.get_digital_human_by_id(digital_human_id)
            if not digital_human:
                logger.error(f"❌ 未找到ID为 {digital_human_id} 的数字人")
                return {"success": False, "error": f"未找到数字人 {digital_human_id}"}
            
            logger.info(f"✅ 获取数字人信息: {digital_human['name']}")
            
            # 2. 转换为我们系统的格式（增强版，包含所有丰富信息）
            persona_info = {
                "persona_id": digital_human['id'],
                "persona_name": digital_human['name'],
                
                # 基础信息
                "name": digital_human['name'],
                "age": digital_human['age'],
                "gender": digital_human['gender'],
                "profession": digital_human['profession'],
                "birthplace_str": digital_human.get('birthplace_str', ''),
                "residence_str": digital_human.get('residence_str', ''),
                
                # 当前状态信息
                "current_mood": digital_human.get('current_mood', '平静'),
                "energy_level": digital_human.get('energy_level', 75),
                "current_activity": digital_human.get('current_activity', '日常生活'),
                "current_location": digital_human.get('current_location', '家中'),
                
                # 健康信息
                "health_status": digital_human.get('health_status', '健康'),
                "medical_history": digital_human.get('medical_history', []),
                "current_medications": digital_human.get('current_medications', []),
                
                # 品牌偏好
                "favorite_brands": digital_human.get('favorite_brands', []),
                
                # 详细属性
                "age_group": digital_human.get('age_group', '青年'),
                "profession_category": digital_human.get('profession_category', '其他'),
                "education_level": digital_human.get('education_level', '本科'),
                "income_level": digital_human.get('income_level', '中等'),
                "marital_status": digital_human.get('marital_status', '未婚'),
                "has_children": digital_human.get('has_children', False),
                
                # 生活方式
                "lifestyle": digital_human.get('lifestyle', {}),
                "interests": digital_human.get('interests', []),
                "values": digital_human.get('values', []),
                
                # 原始属性保持兼容性
                "attributes": digital_human.get('attributes', {}),
                "activity_level": digital_human.get('activity_level', 0.7),
                
                # 向后兼容的background结构
                "background": {
                    "age": digital_human['age'],
                    "gender": digital_human['gender'],
                    "occupation": digital_human['profession'],
                    "personality_traits": digital_human.get('attributes', {}),
                    "background_story": f"{digital_human['name']}的背景故事",
                    "preferences": {
                        "brands": digital_human.get('favorite_brands', []),
                        "interests": digital_human.get('interests', []),
                        "values": digital_human.get('values', [])
                    },
                    "current_state": {
                        "mood": digital_human.get('current_mood', '平静'),
                        "energy": digital_human.get('energy_level', 75),
                        "activity": digital_human.get('current_activity', '日常生活'),
                        "location": digital_human.get('current_location', '家中')
                    },
                    "health": {
                        "status": digital_human.get('health_status', '健康'),
                        "history": digital_human.get('medical_history', []),
                        "medications": digital_human.get('current_medications', [])
                    }
                }
            }
            
            # 3. 创建browser-use会话
            session_id = await self.browser_integration.create_browser_session(
                persona_info=persona_info,
                browser_config={
                    "headless": False,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            if not session_id:
                logger.error("❌ 创建browser-use会话失败")
                return {"success": False, "error": "创建会话失败"}
            
            logger.info(f"✅ 创建会话成功: {session_id}")
            
            # 4. 导航到问卷
            navigation_result = await self.browser_integration.navigate_and_analyze_questionnaire(
                session_id, questionnaire_url, f"task_{digital_human_id}"
            )
            
            if not navigation_result.get("success"):
                logger.error(f"❌ 页面导航失败: {navigation_result.get('error')}")
                await self.browser_integration.close_session(session_id)
                return {"success": False, "error": "页面导航失败"}
            
            logger.info("✅ 页面导航成功")
            
            # 5. 执行完整问卷填写
            execution_result = await self.browser_integration.execute_complete_questionnaire(
                session_id, f"task_{digital_human_id}", "conservative"
            )
            
            # 6. 获取会话总结
            session_summary = await self.browser_integration.get_session_summary(session_id)
            
            # 7. 关闭会话
            await self.browser_integration.close_session(session_id)
            
            # 8. 返回结果
            result = {
                "success": execution_result.get("success", False),
                "digital_human": {
                    "id": digital_human_id,
                    "name": digital_human['name'],
                    "profession": digital_human['profession']
                },
                "execution_result": execution_result,
                "session_summary": session_summary,
                "questionnaire_url": questionnaire_url
            }
            
            if result["success"]:
                logger.info(f"✅ {digital_human['name']} 问卷填写完成")
                logger.info(f"📊 执行步骤: {execution_result.get('step_count', 0)}")
                logger.info(f"⏱️ 用时: {execution_result.get('duration', 0):.2f}秒")
            else:
                logger.error(f"❌ {digital_human['name']} 问卷填写失败: {execution_result.get('error', '未知错误')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 单个数字人问卷填写失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_scout_mission_with_testWenjuan_integration(self, questionnaire_url: str, scout_count: int = 2) -> Dict:
        """运行敢死队任务（集成testWenjuanFinal.py的数字人）"""
        try:
            logger.info(f"🚀 启动敢死队任务，使用testWenjuanFinal.py的数字人")
            
            # 1. 启动敢死队任务
            mission_id = await self.scout_system.start_enhanced_scout_mission(
                questionnaire_url=questionnaire_url,
                scout_count=scout_count
            )
            
            if not mission_id:
                logger.error("❌ 敢死队任务启动失败")
                return {"success": False, "error": "任务启动失败"}
            
            logger.info(f"✅ 敢死队任务启动成功: {mission_id}")
            
            # 2. 执行敢死队答题
            scout_results = await self.scout_system.execute_enhanced_scout_answering(mission_id)
            
            # 3. 清理任务
            await self.scout_system.cleanup_scout_mission(mission_id)
            
            return scout_results
            
        except Exception as e:
            logger.error(f"❌ 敢死队任务失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_batch_questionnaire_with_testWenjuan_data(self, questionnaire_url: str, digital_human_ids: List[int]) -> Dict:
        """批量运行问卷填写（使用testWenjuanFinal.py的数字人数据）"""
        try:
            logger.info(f"🚀 启动批量问卷填写，数字人数量: {len(digital_human_ids)}")
            
            results = []
            successful_count = 0
            failed_count = 0
            
            # 并发执行所有数字人的问卷填写
            tasks = []
            for digital_human_id in digital_human_ids:
                task = self.run_single_digital_human_questionnaire(digital_human_id, questionnaire_url)
                tasks.append(task)
            
            # 等待所有任务完成
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for i, result in enumerate(task_results):
                if isinstance(result, Exception):
                    logger.error(f"❌ 数字人 {digital_human_ids[i]} 任务异常: {result}")
                    results.append({
                        "digital_human_id": digital_human_ids[i],
                        "success": False,
                        "error": str(result)
                    })
                    failed_count += 1
                else:
                    results.append(result)
                    if isinstance(result, dict) and result.get("success"):
                        successful_count += 1
                    else:
                        failed_count += 1
            
            # 汇总结果
            summary = {
                "success": True,
                "total_tasks": len(digital_human_ids),
                "successful_tasks": successful_count,
                "failed_tasks": failed_count,
                "success_rate": (successful_count / len(digital_human_ids) * 100) if digital_human_ids else 0,
                "results": results,
                "questionnaire_url": questionnaire_url
            }
            
            logger.info(f"✅ 批量问卷填写完成")
            logger.info(f"📊 成功率: {summary['success_rate']:.1f}%")
            logger.info(f"✅ 成功: {successful_count}")
            logger.info(f"❌ 失败: {failed_count}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ 批量问卷填写失败: {e}")
            return {"success": False, "error": str(e)}

async def demo_single_questionnaire():
    """演示单个数字人问卷填写"""
    print("\n" + "="*60)
    print("🧪 演示1: 单个数字人问卷填写")
    print("="*60)
    
    system = EnhancedQuestionnaireSystem()
    
    # 测试参数
    digital_human_id = 1  # 使用ID为1的数字人
    questionnaire_url = "http://www.jinshengsurveys.com/?type=qtaskgoto&id=38784&token=FBC7E73EE2CE537C114EF3CCE3393DD5D2FFBC2BDDBE9F3CB4EEFB4B39D29D670EC6C5EC88BB86194F109B43670E8AB58386D6CE6525397A56B81C1CD5E1B48E"
    
    result = await system.run_single_digital_human_questionnaire(digital_human_id, questionnaire_url)
    
    print(f"📊 结果: {result}")
    return result.get("success", False)

async def demo_scout_mission():
    """演示敢死队任务"""
    print("\n" + "="*60)
    print("🧪 演示2: 敢死队任务")
    print("="*60)
    
    system = EnhancedQuestionnaireSystem()
    
    # 测试参数
    questionnaire_url = "http://www.jinshengsurveys.com/?type=qtaskgoto&id=38784&token=FBC7E73EE2CE537C114EF3CCE3393DD5D2FFBC2BDDBE9F3CB4EEFB4B39D29D670EC6C5EC88BB86194F109B43670E8AB58386D6CE6525397A56B81C1CD5E1B48E"
    scout_count = 2
    
    result = await system.run_scout_mission_with_testWenjuan_integration(questionnaire_url, scout_count)
    
    print(f"📊 结果: {result}")
    return result.get("success", False)

async def demo_batch_questionnaire():
    """演示批量问卷填写"""
    print("\n" + "="*60)
    print("🧪 演示3: 批量问卷填写")
    print("="*60)
    
    system = EnhancedQuestionnaireSystem()
    
    # 测试参数
    questionnaire_url = "http://www.jinshengsurveys.com/?type=qtaskgoto&id=38784&token=FBC7E73EE2CE537C114EF3CCE3393DD5D2FFBC2BDDBE9F3CB4EEFB4B39D29D670EC6C5EC88BB86194F109B43670E8AB58386D6CE6525397A56B81C1CD5E1B48E"
    digital_human_ids = [1, 2, 3]  # 使用多个数字人
    
    result = await system.run_batch_questionnaire_with_testWenjuan_data(questionnaire_url, digital_human_ids)
    
    print(f"📊 结果: {result}")
    return result.get("success", False)

def print_integration_summary():
    """打印集成总结"""
    print("\n" + "="*60)
    print("🎉 增强系统集成总结")
    print("="*60)
    print("✅ 成功集成特性:")
    print("  1. 基于testWenjuanFinal.py的browser-use API")
    print("  2. 完整的Agent执行流程")
    print("  3. 真实的问卷填写能力")
    print("  4. 数字人数据库集成")
    print("  5. 敢死队自动化系统")
    print("  6. 批量处理能力")
    print()
    print("🔧 核心组件:")
    print("  - EnhancedBrowserUseIntegration: 基于testWenjuanFinal.py的browser-use集成")
    print("  - EnhancedScoutAutomationSystem: 增强的敢死队系统")
    print("  - EnhancedQuestionnaireSystem: 统一的问卷系统接口")
    print()
    print("🚀 使用方式:")
    print("  1. 单个数字人答题: run_single_digital_human_questionnaire()")
    print("  2. 敢死队任务: run_scout_mission_with_testWenjuan_integration()")
    print("  3. 批量答题: run_batch_questionnaire_with_testWenjuan_data()")
    print("  4. Web界面: 使用web_interface.py")
    print()
    print("💡 优势:")
    print("  - 完全兼容现有的testWenjuanFinal.py")
    print("  - 支持真实的browser-use webui答题")
    print("  - 详细的执行记录和知识库积累")
    print("  - 灵活的单个/批量/敢死队模式")
    print("="*60)

async def main():
    """主演示函数"""
    print("🎯 增强系统集成演示")
    print("展示如何将新开发的增强系统与testWenjuanFinal.py完美集成")
    
    # 检查testWenjuanFinal.py是否可用
    if not TESTWENJUAN_AVAILABLE:
        print("\n⚠️ testWenjuanFinal.py不可用，将跳过相关演示")
        print("请确保testWenjuanFinal.py在当前目录中")
        return False
    
    try:
        # 演示1: 单个数字人问卷填写
        demo1_success = await demo_single_questionnaire()
        
        # 演示2: 敢死队任务
        demo2_success = await demo_scout_mission()
        
        # 演示3: 批量问卷填写
        demo3_success = await demo_batch_questionnaire()
        
        # 打印总结
        print_integration_summary()
        
        # 总体结果
        all_success = demo1_success and demo2_success and demo3_success
        
        if all_success:
            print("\n🎉 所有演示成功完成！系统集成完美！")
        else:
            print("\n⚠️ 部分演示失败，请检查配置")
        
        return all_success
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    # 运行演示
    result = asyncio.run(main())
    sys.exit(0 if result else 1) 