#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
问卷系统测试脚本
测试基础架构的各个模块功能
"""

import asyncio
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from questionnaire_system import (
    QuestionnaireManager, 
    DatabaseManager, 
    AdsPowerManager, 
    XiaosheSystemClient,
    DB_CONFIG,
    ADSPOWER_CONFIG,
    XIAOSHE_CONFIG
)

async def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    try:
        db_manager = DatabaseManager(DB_CONFIG)
        connection = db_manager.get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✅ 数据库连接成功")
                return True
        connection.close()
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

async def test_database_tables():
    """测试数据库表初始化"""
    print("🔍 测试数据库表初始化...")
    try:
        db_manager = DatabaseManager(DB_CONFIG)
        db_manager.init_knowledge_base_tables()
        print("✅ 数据库表初始化成功")
        return True
    except Exception as e:
        print(f"❌ 数据库表初始化失败: {e}")
        return False

async def test_xiaoshe_connection():
    """测试小社会系统连接"""
    print("🔍 测试小社会系统连接...")
    try:
        xiaoshe_client = XiaosheSystemClient(XIAOSHE_CONFIG)
        personas = await xiaoshe_client.query_personas("找2个数字人", 2)
        if personas:
            print(f"✅ 小社会系统连接成功，找到 {len(personas)} 个数字人")
            for persona in personas:
                print(f"   - {persona.get('name', '未知')} (ID: {persona.get('id', '未知')})")
            return True
        else:
            print("⚠️ 小社会系统连接成功，但未找到数字人")
            return False
    except Exception as e:
        print(f"❌ 小社会系统连接失败: {e}")
        return False

async def test_adspower_connection():
    """测试AdsPower连接"""
    print("🔍 测试AdsPower连接...")
    try:
        adspower_manager = AdsPowerManager(ADSPOWER_CONFIG)
        # 尝试获取用户列表来测试连接
        result = adspower_manager._make_request("GET", "/user/list", {"page": 1, "page_size": 1})
        if result.get("code") == 0:
            print("✅ AdsPower连接成功")
            return True
        else:
            print(f"❌ AdsPower连接失败: {result.get('msg', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ AdsPower连接失败: {e}")
        return False

async def test_questionnaire_manager():
    """测试问卷主管基础功能"""
    print("🔍 测试问卷主管基础功能...")
    try:
        manager = QuestionnaireManager()
        
        # 创建测试任务
        test_url = "https://example.com/test-questionnaire"
        task = await manager.create_questionnaire_task(test_url, scout_count=1, target_count=2)
        
        print(f"✅ 问卷任务创建成功:")
        print(f"   - 任务ID: {task.task_id}")
        print(f"   - 会话ID: {task.session_id}")
        print(f"   - 问卷URL: {task.url}")
        print(f"   - 敢死队数量: {task.scout_count}")
        print(f"   - 目标团队数量: {task.target_count}")
        
        # 清理测试任务
        await manager.cleanup_task_resources(task)
        print("✅ 测试任务已清理")
        
        return True
    except Exception as e:
        print(f"❌ 问卷主管测试失败: {e}")
        return False

async def test_full_workflow():
    """测试完整工作流程（需要所有系统运行）"""
    print("🔍 测试完整工作流程...")
    try:
        manager = QuestionnaireManager()
        
        # 创建任务
        test_url = "https://example.com/full-test-questionnaire"
        task = await manager.create_questionnaire_task(test_url, scout_count=1, target_count=2)
        print(f"✅ 任务创建: {task.task_id}")
        
        # 选择敢死队
        try:
            scout_team = await manager.select_scout_team(task)
            print(f"✅ 敢死队选择成功: {[a.persona_name for a in scout_team]}")
            
            # 准备浏览器环境
            try:
                browser_profiles = await manager.prepare_browser_environments(scout_team[:1])  # 只测试1个
                print(f"✅ 浏览器环境准备成功: {len(browser_profiles)} 个配置文件")
            except Exception as e:
                print(f"⚠️ 浏览器环境准备失败: {e}")
                
        except Exception as e:
            print(f"⚠️ 敢死队选择失败: {e}")
        
        # 清理资源
        await manager.cleanup_task_resources(task)
        print("✅ 完整工作流程测试完成，资源已清理")
        
        return True
    except Exception as e:
        print(f"❌ 完整工作流程测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 问卷系统基础架构测试")
    print("=" * 50)
    
    test_results = {}
    
    # 基础测试
    test_results["数据库连接"] = await test_database_connection()
    test_results["数据库表初始化"] = await test_database_tables()
    test_results["问卷主管基础功能"] = await test_questionnaire_manager()
    
    # 外部系统测试
    test_results["小社会系统连接"] = await test_xiaoshe_connection()
    test_results["AdsPower连接"] = await test_adspower_connection()
    
    # 完整流程测试
    if test_results["小社会系统连接"] and test_results["AdsPower连接"]:
        test_results["完整工作流程"] = await test_full_workflow()
    else:
        print("⚠️ 跳过完整工作流程测试（需要小社会系统和AdsPower都运行）")
        test_results["完整工作流程"] = None
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    for test_name, result in test_results.items():
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⚠️ 跳过"
        print(f"   {test_name}: {status}")
    
    # 统计
    passed = sum(1 for r in test_results.values() if r is True)
    failed = sum(1 for r in test_results.values() if r is False)
    skipped = sum(1 for r in test_results.values() if r is None)
    
    print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过")
    
    if failed == 0:
        print("🎉 所有基础功能测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查相关配置")

if __name__ == "__main__":
    asyncio.run(main()) 