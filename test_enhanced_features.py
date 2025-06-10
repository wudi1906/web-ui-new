#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试增强功能 - 验证AdsPower状态检查器和智能数字人查询引擎
"""

import asyncio
import logging
from adspower_browser_use_integration import AdsPowerStatusChecker, SmartPersonaQueryEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_adspower_status_checker():
    """测试AdsPower状态检查器"""
    logger.info("🔍 开始测试AdsPower状态检查器")
    
    try:
        # 初始化状态检查器
        status_checker = AdsPowerStatusChecker()
        
        # 测试设备环境状态检查
        test_persona_id = 1
        test_profile_id = "profile_test_001"
        
        logger.info(f"📊 测试数字人 {test_persona_id} 的设备环境状态")
        environment_status = await status_checker.check_device_environment_status(
            test_persona_id, test_profile_id
        )
        
        logger.info("✅ AdsPower状态检查器测试完成")
        logger.info(f"📋 环境状态: {environment_status.get('overall_status', '未知')}")
        
        # 显示关键信息
        if environment_status.get("fingerprint_browser"):
            fingerprint = environment_status["fingerprint_browser"]
            logger.info(f"🖥️ 设备类型: {fingerprint.get('device_type', '未知')}")
            logger.info(f"🌐 浏览器: {fingerprint.get('browser_version', '未知')}")
        
        if environment_status.get("proxy_ip"):
            proxy = environment_status["proxy_ip"]
            logger.info(f"🌐 代理IP: {proxy.get('current_ip', '未知')}")
            logger.info(f"📍 IP位置: {proxy.get('ip_location', '未知')}")
        
        return environment_status
        
    except Exception as e:
        logger.error(f"❌ AdsPower状态检查器测试失败: {e}")
        return None

async def test_smart_persona_query_engine():
    """测试智能数字人查询引擎"""
    logger.info("🧠 开始测试智能数字人查询引擎")
    
    try:
        # 初始化查询引擎
        query_engine = SmartPersonaQueryEngine()
        
        # 测试增强数字人信息获取
        test_persona_id = 1
        
        logger.info(f"👤 测试数字人 {test_persona_id} 的增强信息获取")
        enhanced_info = await query_engine.get_enhanced_persona_info(test_persona_id)
        
        logger.info("✅ 智能数字人查询引擎测试完成")
        
        # 显示关键信息
        if enhanced_info.get("webui_prompt_data"):
            prompt_data = enhanced_info["webui_prompt_data"]
            persona_identity = prompt_data.get("persona_identity", {})
            logger.info(f"👤 数字人姓名: {persona_identity.get('name', '未知')}")
            logger.info(f"🎂 年龄: {persona_identity.get('age', '未知')}")
            logger.info(f"💼 职业: {persona_identity.get('occupation', '未知')}")
            
            lifestyle = prompt_data.get("lifestyle_preferences", {})
            interests = lifestyle.get("interests", [])
            if interests:
                logger.info(f"🎯 兴趣爱好: {', '.join(interests[:3])}")
        
        return enhanced_info
        
    except Exception as e:
        logger.error(f"❌ 智能数字人查询引擎测试失败: {e}")
        return None

async def test_integration_workflow():
    """测试完整的集成工作流程"""
    logger.info("🚀 开始测试完整集成工作流程")
    
    try:
        # 1. 测试AdsPower状态检查
        logger.info("📋 第1步: 设备环境状态检查")
        environment_status = await test_adspower_status_checker()
        
        # 2. 测试智能数字人查询
        logger.info("📋 第2步: 增强数字人信息获取")
        enhanced_persona = await test_smart_persona_query_engine()
        
        # 3. 模拟集成结果
        integration_result = {
            "environment_check": environment_status is not None,
            "enhanced_persona": enhanced_persona is not None,
            "integration_success": environment_status is not None and enhanced_persona is not None
        }
        
        logger.info("✅ 完整集成工作流程测试完成")
        logger.info(f"📊 集成结果: {integration_result}")
        
        if integration_result["integration_success"]:
            logger.info("🎉 所有增强功能正常工作！")
        else:
            logger.warning("⚠️ 部分增强功能可能存在问题")
        
        return integration_result
        
    except Exception as e:
        logger.error(f"❌ 集成工作流程测试失败: {e}")
        return {"integration_success": False, "error": str(e)}

async def main():
    """主测试函数"""
    logger.info("🧪 开始增强功能测试")
    
    try:
        # 运行完整的集成测试
        result = await test_integration_workflow()
        
        if result.get("integration_success"):
            logger.info("🎊 所有测试通过！增强功能已成功集成")
            print("\n" + "="*60)
            print("🎉 测试结果: 成功")
            print("✅ AdsPower状态检查器: 正常")
            print("✅ 智能数字人查询引擎: 正常")
            print("✅ 功能集成: 完成")
            print("="*60)
        else:
            logger.warning("⚠️ 测试发现问题，请检查配置")
            print("\n" + "="*60)
            print("⚠️ 测试结果: 部分功能异常")
            print("请检查网络连接和API配置")
            print("="*60)
            
    except Exception as e:
        logger.error(f"❌ 测试执行失败: {e}")
        print(f"\n❌ 测试失败: {e}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main()) 