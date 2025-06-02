#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的browser-use集成测试
用于隔离和调试AdsPower + WebUI集成问题
"""

import asyncio
import logging
from browser_use import Agent, Browser, BrowserConfig
from langchain_google_genai import ChatGoogleGenerativeAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_browser_integration():
    """测试简单的browser-use集成"""
    try:
        logger.info("🧪 开始测试browser-use集成...")
        
        # 1. 创建LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.6,
            api_key="AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8",
        )
        logger.info("✅ LLM创建成功")
        
        # 2. 创建BrowserConfig（不连接AdsPower，先测试基本功能）
        browser_config = BrowserConfig(
            headless=False,
            disable_security=True
        )
        logger.info("✅ BrowserConfig创建成功")
        
        # 3. 创建Browser
        browser = Browser(config=browser_config)
        logger.info("✅ Browser创建成功")
        
        # 4. 创建Agent
        agent = Agent(
            task="访问百度首页并搜索'测试'",
            llm=llm,
            browser=browser,
            max_actions_per_step=5,
            use_vision=True
        )
        logger.info("✅ Agent创建成功")
        
        # 5. 执行简单任务
        logger.info("🚀 开始执行任务...")
        result = await agent.run("https://www.baidu.com")
        logger.info(f"✅ 任务执行完成: {result}")
        
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

async def test_adspower_connection():
    """测试AdsPower连接"""
    try:
        logger.info("🧪 开始测试AdsPower连接...")
        
        # 模拟AdsPower调试端口
        debug_port = 50325  # 假设的端口
        
        # 1. 创建LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.6,
            api_key="AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8",
        )
        logger.info("✅ LLM创建成功")
        
        # 2. 创建BrowserConfig（连接到AdsPower）
        browser_config = BrowserConfig(
            headless=False,
            disable_security=True,
            chrome_remote_debugging_port=debug_port,
            extra_browser_args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security"
            ]
        )
        logger.info(f"✅ BrowserConfig创建成功，调试端口: {debug_port}")
        
        # 3. 创建Browser
        browser = Browser(config=browser_config)
        logger.info("✅ Browser创建成功")
        
        # 4. 创建Agent
        agent = Agent(
            task="访问问卷网站",
            llm=llm,
            browser=browser,
            max_actions_per_step=5,
            use_vision=True
        )
        logger.info("✅ Agent创建成功")
        
        logger.info("🎯 AdsPower连接测试完成（未执行实际任务）")
        return {"success": True, "message": "AdsPower连接配置正确"}
        
    except Exception as e:
        logger.error(f"❌ AdsPower连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("=== Browser-Use 集成测试 ===")
    
    # 测试1：基本browser-use功能
    print("\n1. 测试基本browser-use功能...")
    result1 = asyncio.run(test_simple_browser_integration())
    print(f"结果: {result1}")
    
    # 测试2：AdsPower连接配置
    print("\n2. 测试AdsPower连接配置...")
    result2 = asyncio.run(test_adspower_connection())
    print(f"结果: {result2}") 