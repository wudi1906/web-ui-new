#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的浏览器问卷测试脚本
验证修复后的系统是否能正常打开浏览器并导航到问卷URL进行作答
"""

import asyncio
import logging
import time
from datetime import datetime

# 导入核心模块
from questionnaire_system import DatabaseManager, DB_CONFIG
from enhanced_browser_use_integration import EnhancedBrowserUseIntegration

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_single_browser_questionnaire():
    """测试单个浏览器问卷填写"""
    logger.info("🧪 开始测试单个浏览器问卷填写...")
    
    try:
        # 初始化系统
        db_manager = DatabaseManager(DB_CONFIG)
        browser_integration = EnhancedBrowserUseIntegration(db_manager)
        
        # 测试问卷URL
        questionnaire_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"
        
        # 模拟数字人信息
        persona_info = {
            "persona_id": 1,
            "persona_name": "测试数字人林心怡",
            "name": "林心怡",
            "age": 35,
            "gender": "女",
            "profession": "高级时尚顾问",
            "birthplace_str": "上海",
            "residence_str": "北京"
        }
        
        # 浏览器配置
        browser_config = {
            "headless": False,  # 显示浏览器
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1200,800",
                "--window-position=100,100"
            ]
        }
        
        logger.info(f"👤 使用数字人: {persona_info['persona_name']}")
        logger.info(f"🌐 问卷URL: {questionnaire_url}")
        
        # 步骤1: 创建浏览器会话
        logger.info("📱 步骤1: 创建浏览器会话...")
        session_id = await browser_integration.create_browser_session(persona_info, browser_config)
        
        if not session_id:
            logger.error("❌ 浏览器会话创建失败")
            return False
        
        logger.info(f"✅ 浏览器会话创建成功: {session_id}")
        
        # 等待用户确认浏览器已打开
        input("🔍 请确认浏览器已打开，然后按回车继续...")
        
        # 步骤2: 导航到问卷页面
        logger.info("🧭 步骤2: 导航到问卷页面...")
        navigation_result = await browser_integration.navigate_and_analyze_questionnaire(
            session_id, questionnaire_url, f"test_task_{int(time.time())}"
        )
        
        if not navigation_result.get("success"):
            logger.error(f"❌ 页面导航失败: {navigation_result.get('error')}")
            return False
        
        logger.info("✅ 页面导航成功")
        
        # 等待用户确认页面已加载
        input("📋 请确认问卷页面已加载，然后按回车开始答题...")
        
        # 步骤3: 执行问卷填写
        logger.info("📝 步骤3: 执行问卷填写...")
        answering_result = await browser_integration.execute_complete_questionnaire(
            session_id, f"test_task_{int(time.time())}", "conservative"
        )
        
        if answering_result.get("success"):
            logger.info(f"✅ 问卷填写成功!")
            logger.info(f"📊 填写统计:")
            logger.info(f"   - 用时: {answering_result.get('duration', 0):.2f}秒")
            logger.info(f"   - 步骤数: {answering_result.get('step_count', 0)}")
            logger.info(f"   - 成功答题: {answering_result.get('successful_answers', 0)}")
        else:
            logger.error(f"❌ 问卷填写失败: {answering_result.get('error')}")
            return False
        
        # 保持浏览器打开
        logger.info("🎉 测试完成！浏览器将保持打开状态供您查看结果。")
        input("按回车键结束测试...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试过程中出现异常: {e}")
        return False

async def test_multiple_browsers():
    """测试多个浏览器同时填写问卷"""
    logger.info("🧪 开始测试多个浏览器同时填写问卷...")
    
    try:
        # 初始化系统
        db_manager = DatabaseManager(DB_CONFIG)
        browser_integration = EnhancedBrowserUseIntegration(db_manager)
        
        # 测试问卷URL
        questionnaire_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"
        
        # 多个数字人信息
        personas = [
            {
                "persona_id": 1,
                "persona_name": "林心怡",
                "age": 35,
                "gender": "女",
                "profession": "高级时尚顾问"
            },
            {
                "persona_id": 2,
                "persona_name": "张明",
                "age": 28,
                "gender": "男",
                "profession": "软件工程师"
            },
            {
                "persona_id": 3,
                "persona_name": "王丽",
                "age": 42,
                "gender": "女",
                "profession": "市场经理"
            }
        ]
        
        sessions = []
        
        # 创建多个浏览器会话
        for i, persona in enumerate(personas):
            logger.info(f"👤 创建数字人 {persona['persona_name']} 的浏览器会话...")
            
            browser_config = {
                "headless": False,
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    f"--window-size=600,600",
                    f"--window-position={100 + i * 620},{100}"
                ]
            }
            
            session_id = await browser_integration.create_browser_session(persona, browser_config)
            
            if session_id:
                sessions.append({
                    "session_id": session_id,
                    "persona": persona
                })
                logger.info(f"✅ {persona['persona_name']} 浏览器会话创建成功")
            else:
                logger.error(f"❌ {persona['persona_name']} 浏览器会话创建失败")
        
        if not sessions:
            logger.error("❌ 没有成功创建任何浏览器会话")
            return False
        
        logger.info(f"🎯 成功创建 {len(sessions)} 个浏览器会话")
        input("🔍 请确认所有浏览器已打开，然后按回车继续...")
        
        # 并发导航到问卷页面
        logger.info("🧭 开始并发导航到问卷页面...")
        navigation_tasks = []
        
        for session in sessions:
            task = browser_integration.navigate_and_analyze_questionnaire(
                session["session_id"], questionnaire_url, f"multi_test_{session['persona']['persona_id']}"
            )
            navigation_tasks.append(task)
        
        navigation_results = await asyncio.gather(*navigation_tasks, return_exceptions=True)
        
        successful_navigations = 0
        for i, result in enumerate(navigation_results):
            if isinstance(result, Exception):
                logger.error(f"❌ {sessions[i]['persona']['persona_name']} 导航异常: {result}")
            elif result.get("success"):
                logger.info(f"✅ {sessions[i]['persona']['persona_name']} 导航成功")
                successful_navigations += 1
            else:
                logger.error(f"❌ {sessions[i]['persona']['persona_name']} 导航失败: {result.get('error')}")
        
        logger.info(f"📊 导航结果: {successful_navigations}/{len(sessions)} 成功")
        
        if successful_navigations == 0:
            logger.error("❌ 没有任何会话成功导航")
            return False
        
        input("📋 请确认问卷页面已在各浏览器中加载，然后按回车开始并发答题...")
        
        # 并发执行问卷填写
        logger.info("📝 开始并发执行问卷填写...")
        answering_tasks = []
        
        for session in sessions:
            task = browser_integration.execute_complete_questionnaire(
                session["session_id"], f"multi_test_{session['persona']['persona_id']}", "conservative"
            )
            answering_tasks.append(task)
        
        answering_results = await asyncio.gather(*answering_tasks, return_exceptions=True)
        
        successful_answers = 0
        for i, result in enumerate(answering_results):
            persona_name = sessions[i]['persona']['persona_name']
            if isinstance(result, Exception):
                logger.error(f"❌ {persona_name} 答题异常: {result}")
            elif result.get("success"):
                logger.info(f"✅ {persona_name} 答题成功，用时: {result.get('duration', 0):.2f}秒")
                successful_answers += 1
            else:
                logger.error(f"❌ {persona_name} 答题失败: {result.get('error')}")
        
        logger.info(f"🎉 并发答题完成!")
        logger.info(f"📊 最终结果: {successful_answers}/{len(sessions)} 成功")
        
        # 保持浏览器打开
        logger.info("🎉 测试完成！所有浏览器将保持打开状态供您查看结果。")
        input("按回车键结束测试...")
        
        return successful_answers > 0
        
    except Exception as e:
        logger.error(f"❌ 多浏览器测试过程中出现异常: {e}")
        return False

async def main():
    """主函数"""
    print("🧪 浏览器问卷填写系统测试")
    print("=" * 50)
    print("1. 单个浏览器测试")
    print("2. 多个浏览器并发测试")
    print("=" * 50)
    
    choice = input("请选择测试模式 (1 或 2): ").strip()
    
    if choice == "1":
        success = await test_single_browser_questionnaire()
    elif choice == "2":
        success = await test_multiple_browsers()
    else:
        print("❌ 无效选择")
        return
    
    if success:
        print("🎉 测试成功完成！")
    else:
        print("❌ 测试失败")

if __name__ == "__main__":
    asyncio.run(main()) 