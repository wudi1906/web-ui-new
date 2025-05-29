#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能问卷自动填写系统 - 修复版本运行脚本
包含以下修复：
1. 去掉所有突然关闭浏览器的代码
2. 在页面右侧显示错误蒙版
3. 调整浏览器窗口大小，支持6个窗口的flow布局
4. 保持浏览器打开状态供用户查看结果
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Optional

# 导入核心模块
from questionnaire_system import DatabaseManager, QuestionnaireManager, DB_CONFIG
from enhanced_browser_use_integration import EnhancedBrowserUseIntegration
from phase4_mass_automation import Phase4MassAutomationSystem, ConcurrentAnsweringEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'fixed_system_overlay_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FixedSystemWithOverlay:
    """修复版本的智能问卷系统（支持错误蒙版和窗口布局）"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(DB_CONFIG)
        # self.questionnaire_manager = QuestionnaireManager(self.db_manager)  # 注释掉，不需要
        
    async def run_scout_phase_with_overlay(self, questionnaire_url: str, scout_count: int = 2) -> Dict:
        """运行敢死队阶段（支持错误蒙版）"""
        logger.info(f"🕵️ 开始敢死队阶段 - {scout_count} 个敢死队员")
        
        try:
            # 创建增强的浏览器集成
            browser_integration = EnhancedBrowserUseIntegration(self.db_manager)
            
            scout_results = []
            
            for i in range(scout_count):
                scout_id = i + 1
                logger.info(f"🚀 启动敢死队员 {scout_id}")
                
                # 模拟从小社会系统获取数字人信息
                persona_info = await self._get_persona_from_xiaoshe(scout_id)
                
                # 生成浏览器配置（支持窗口布局）
                browser_config = self._generate_scout_browser_config(scout_id)
                
                # 创建浏览器会话
                session_id = await browser_integration.create_browser_session(persona_info, browser_config)
                
                if session_id:
                    # 导航到问卷页面
                    await browser_integration.navigate_and_analyze_questionnaire(
                        session_id, questionnaire_url, f"scout_task_{scout_id}"
                    )
                    
                    # 执行完整问卷填写
                    result = await browser_integration.execute_complete_questionnaire(
                        session_id, f"scout_task_{scout_id}", "conservative"
                    )
                    
                    # 如果出现错误，在蒙版中显示而不是关闭浏览器
                    if not result.get("success", False):
                        error_message = result.get("error", "敢死队答题过程中出现未知错误")
                        await browser_integration._show_error_in_overlay(session_id, error_message, "敢死队错误")
                        logger.warning(f"⚠️ 敢死队员 {scout_id} 答题失败，错误已显示在蒙版中")
                    else:
                        await browser_integration._show_error_in_overlay(session_id, "敢死队任务完成！", "成功")
                        logger.info(f"✅ 敢死队员 {scout_id} 答题成功")
                    
                    scout_results.append({
                        "scout_id": scout_id,
                        "session_id": session_id,
                        "persona_name": persona_info.get('persona_name', f'敢死队员{scout_id}'),
                        "success": result.get("success", False),
                        "error": result.get("error", None),
                        "duration": result.get("duration", 0.0)
                    })
                    
                    # 不关闭浏览器，保持打开状态
                    logger.info(f"📋 敢死队员 {scout_id} 的浏览器保持打开状态")
                
                # 间隔启动，避免资源冲突
                await asyncio.sleep(2)
            
            # 统计敢死队结果
            successful_scouts = sum(1 for r in scout_results if r["success"])
            logger.info(f"🎯 敢死队阶段完成: {successful_scouts}/{scout_count} 成功")
            
            return {
                "success": True,
                "scout_results": scout_results,
                "successful_count": successful_scouts,
                "total_count": scout_count,
                "success_rate": successful_scouts / scout_count if scout_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ 敢死队阶段失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_mass_phase_with_overlay(self, questionnaire_url: str, target_count: int = 5) -> Dict:
        """运行大部队阶段（支持错误蒙版和窗口布局）"""
        logger.info(f"🚀 开始大部队阶段 - {target_count} 个数字人")
        
        try:
            # 创建大部队自动化系统
            mass_system = Phase4MassAutomationSystem()
            
            # 执行大规模自动化
            result = await mass_system.execute_full_automation_pipeline(
                questionnaire_url=questionnaire_url,
                target_count=target_count,
                max_workers=target_count  # 并发执行
            )
            
            logger.info(f"🎉 大部队阶段完成")
            return result
            
        except Exception as e:
            logger.error(f"❌ 大部队阶段失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_persona_from_xiaoshe(self, persona_id: int) -> Dict:
        """从小社会系统获取数字人信息"""
        try:
            import requests
            
            # 调用小社会系统API
            response = requests.get(f"http://localhost:5001/api/persona/{persona_id}", timeout=10)
            
            if response.status_code == 200:
                persona_data = response.json()
                logger.info(f"✅ 成功获取数字人 {persona_id} 信息")
                return persona_data
            else:
                logger.warning(f"⚠️ 小社会系统返回错误: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ 调用小社会系统失败: {e}")
        
        # 返回模拟数据
        return {
            "persona_id": persona_id,
            "persona_name": f"敢死队员{persona_id}",
            "age": 25 + persona_id,
            "gender": "男" if persona_id % 2 == 1 else "女",
            "profession": ["学生", "工程师", "设计师", "教师", "医生"][persona_id % 5],
            "birthplace_str": "北京",
            "residence_str": "上海"
        }
    
    def _generate_scout_browser_config(self, scout_id: int) -> Dict:
        """生成敢死队浏览器配置（支持窗口布局）"""
        # 计算窗口位置（敢死队使用前2个位置）
        window_layout = self._calculate_scout_window_layout(scout_id)
        
        config = {
            "headless": False,
            "window_width": window_layout["width"],
            "window_height": window_layout["height"],
            "window_x": window_layout["x"],
            "window_y": window_layout["y"],
            "user_data_dir": f"/tmp/scout_browser_profile_{scout_id}_{int(time.time())}",
            "remote_debugging_port": 9000 + scout_id,
            "args": [
                f"--remote-debugging-port={9000 + scout_id}",
                f"--user-data-dir=/tmp/scout_browser_profile_{scout_id}_{int(time.time())}",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                f"--window-position={window_layout['x']},{window_layout['y']}",
                f"--window-size={window_layout['width']},{window_layout['height']}"
            ]
        }
        
        logger.info(f"🖥️ 敢死队员{scout_id} 浏览器配置: {window_layout['width']}x{window_layout['height']} at ({window_layout['x']}, {window_layout['y']})")
        
        return config
    
    def _calculate_scout_window_layout(self, scout_id: int) -> Dict:
        """计算敢死队窗口布局（使用前2个位置）"""
        # 屏幕分辨率假设
        screen_width = 1920
        screen_height = 1080
        
        # 6个窗口的布局：3列2行，敢死队使用前2个
        cols = 3
        window_width = screen_width // cols
        window_height = screen_height // 2
        
        # 敢死队员1在左上角，敢死队员2在中上角
        col = (scout_id - 1) % cols
        row = 0  # 敢死队在第一行
        
        x = col * window_width
        y = row * window_height
        
        return {
            "width": window_width - 20,
            "height": window_height - 60,
            "x": x + 10,
            "y": y + 30
        }
    
    async def run_complete_pipeline_with_overlay(self, questionnaire_url: str, 
                                               scout_count: int = 2, target_count: int = 5) -> Dict:
        """运行完整的敢死队+大部队流程（支持错误蒙版和窗口布局）"""
        logger.info("🎯 开始完整的智能问卷自动填写流程")
        
        start_time = time.time()
        
        try:
            # 第一阶段：敢死队探索
            scout_result = await self.run_scout_phase_with_overlay(questionnaire_url, scout_count)
            
            if not scout_result.get("success"):
                return {
                    "success": False,
                    "error": "敢死队阶段失败",
                    "scout_result": scout_result
                }
            
            # 等待一段时间，让敢死队完成经验积累
            logger.info("⏳ 等待敢死队完成经验积累...")
            await asyncio.sleep(5)
            
            # 第二阶段：大部队自动化
            mass_result = await self.run_mass_phase_with_overlay(questionnaire_url, target_count)
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # 生成最终报告
            final_report = {
                "success": True,
                "total_duration": total_duration,
                "questionnaire_url": questionnaire_url,
                "scout_phase": scout_result,
                "mass_phase": mass_result,
                "summary": {
                    "scout_success_rate": scout_result.get("success_rate", 0),
                    "mass_success_rate": mass_result.get("automation_result", {}).get("success_rate", 0),
                    "total_participants": scout_count + target_count,
                    "browser_windows_open": scout_count + target_count,
                    "error_overlay_enabled": True,
                    "window_layout_enabled": True
                }
            }
            
            logger.info("🎉 完整流程执行完成！")
            logger.info(f"📊 敢死队成功率: {scout_result.get('success_rate', 0):.1%}")
            logger.info(f"📊 大部队成功率: {mass_result.get('automation_result', {}).get('success_rate', 0):.1%}")
            logger.info(f"⏱️ 总耗时: {total_duration:.1f}秒")
            logger.info(f"🖥️ 浏览器窗口保持打开状态，可查看答题结果")
            
            return final_report
            
        except Exception as e:
            logger.error(f"❌ 完整流程执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }

async def main():
    """主函数"""
    logger.info("🚀 启动修复版本的智能问卷自动填写系统")
    
    # 测试问卷URL
    questionnaire_url = "https://www.wjx.cn/vm/w4e8hc9.aspx"
    
    # 创建系统实例
    system = FixedSystemWithOverlay()
    
    try:
        # 运行完整流程
        result = await system.run_complete_pipeline_with_overlay(
            questionnaire_url=questionnaire_url,
            scout_count=2,  # 2个敢死队员
            target_count=4   # 4个大部队成员，总共6个窗口
        )
        
        print("\n" + "="*80)
        print("🎉 智能问卷自动填写系统运行完成！")
        print("="*80)
        
        if result.get("success"):
            print("✅ 系统运行成功")
            print(f"📊 敢死队成功率: {result['summary']['scout_success_rate']:.1%}")
            print(f"📊 大部队成功率: {result['summary']['mass_success_rate']:.1%}")
            print(f"🖥️ 总共打开了 {result['summary']['browser_windows_open']} 个浏览器窗口")
            print(f"🚨 错误蒙版功能: {'已启用' if result['summary']['error_overlay_enabled'] else '未启用'}")
            print(f"📐 窗口布局功能: {'已启用' if result['summary']['window_layout_enabled'] else '未启用'}")
            print(f"⏱️ 总耗时: {result['total_duration']:.1f}秒")
            print("\n💡 提示:")
            print("- 所有浏览器窗口保持打开状态，您可以查看答题结果")
            print("- 如果出现错误，会在页面右侧显示红色蒙版")
            print("- 浏览器窗口已按照flow布局自动排列")
        else:
            print("❌ 系统运行失败")
            print(f"错误信息: {result.get('error', '未知错误')}")
        
        print("="*80)
        
    except Exception as e:
        logger.error(f"❌ 系统运行异常: {e}")
        print(f"\n❌ 系统运行异常: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 