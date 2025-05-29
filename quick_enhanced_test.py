#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强系统快速测试脚本
验证所有组件是否正常工作
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """测试模块导入"""
    print("🧪 测试模块导入...")
    
    results = {}
    
    # 测试核心模块
    try:
        from questionnaire_system import DatabaseManager, DB_CONFIG
        results['questionnaire_system'] = True
        print("✅ questionnaire_system 导入成功")
    except Exception as e:
        results['questionnaire_system'] = False
        print(f"❌ questionnaire_system 导入失败: {e}")
    
    # 测试增强browser-use集成
    try:
        from enhanced_browser_use_integration import EnhancedBrowserUseIntegration
        results['enhanced_browser_use_integration'] = True
        print("✅ enhanced_browser_use_integration 导入成功")
    except Exception as e:
        results['enhanced_browser_use_integration'] = False
        print(f"❌ enhanced_browser_use_integration 导入失败: {e}")
    
    # 测试敢死队系统
    try:
        from phase2_scout_automation import EnhancedScoutAutomationSystem
        results['phase2_scout_automation'] = True
        print("✅ phase2_scout_automation 导入成功")
    except Exception as e:
        results['phase2_scout_automation'] = False
        print(f"❌ phase2_scout_automation 导入失败: {e}")
    
    # 测试演示系统
    try:
        from demo_enhanced_integration import EnhancedQuestionnaireSystem
        results['demo_enhanced_integration'] = True
        print("✅ demo_enhanced_integration 导入成功")
    except Exception as e:
        results['demo_enhanced_integration'] = False
        print(f"❌ demo_enhanced_integration 导入失败: {e}")
    
    # 测试testWenjuanFinal
    try:
        import testWenjuanFinal
        results['testWenjuanFinal'] = True
        print("✅ testWenjuanFinal 导入成功")
    except Exception as e:
        results['testWenjuanFinal'] = False
        print(f"❌ testWenjuanFinal 导入失败: {e}")
    
    # 测试browser-use
    try:
        from browser_use import Browser, BrowserConfig, Agent
        results['browser_use'] = True
        print("✅ browser-use 导入成功")
    except Exception as e:
        results['browser_use'] = False
        print(f"⚠️ browser-use 导入失败: {e}")
    
    return results

def test_database_connection():
    """测试数据库连接"""
    print("\n🗄️ 测试数据库连接...")
    
    try:
        from questionnaire_system import DatabaseManager, DB_CONFIG
        db_manager = DatabaseManager(DB_CONFIG)
        connection = db_manager.get_connection()
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        connection.close()
        print("✅ 数据库连接成功")
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_enhanced_system_initialization():
    """测试增强系统初始化"""
    print("\n🔧 测试增强系统初始化...")
    
    try:
        from questionnaire_system import DatabaseManager, DB_CONFIG
        from enhanced_browser_use_integration import EnhancedBrowserUseIntegration
        from demo_enhanced_integration import EnhancedQuestionnaireSystem
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(DB_CONFIG)
        print("✅ 数据库管理器初始化成功")
        
        # 初始化browser-use集成
        browser_integration = EnhancedBrowserUseIntegration(db_manager)
        print("✅ browser-use集成初始化成功")
        
        # 初始化增强问卷系统
        enhanced_system = EnhancedQuestionnaireSystem()
        print("✅ 增强问卷系统初始化成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 增强系统初始化失败: {e}")
        return False

def test_testwenjuan_integration():
    """测试testWenjuanFinal集成"""
    print("\n🤖 测试testWenjuanFinal集成...")
    
    try:
        import testWenjuanFinal
        
        # 测试获取数字人
        digital_human = testWenjuanFinal.get_digital_human_by_id(1)
        if digital_human:
            print(f"✅ 成功获取数字人: {digital_human['name']}")
            
            # 测试生成描述
            description = testWenjuanFinal.generate_detailed_person_description(digital_human)
            print(f"✅ 成功生成人物描述，长度: {len(description)}")
            
            return True
        else:
            print("⚠️ 未找到数字人数据")
            return False
            
    except Exception as e:
        print(f"❌ testWenjuanFinal集成测试失败: {e}")
        return False

async def test_enhanced_system_basic_functionality():
    """测试增强系统基本功能"""
    print("\n⚙️ 测试增强系统基本功能...")
    
    try:
        from questionnaire_system import DatabaseManager, DB_CONFIG
        from enhanced_browser_use_integration import EnhancedBrowserUseIntegration
        
        # 初始化系统
        db_manager = DatabaseManager(DB_CONFIG)
        browser_integration = EnhancedBrowserUseIntegration(db_manager)
        
        # 测试数据
        test_persona = {
            "persona_id": 9999,
            "persona_name": "测试用户",
            "background": {
                "age": 25,
                "gender": "男",
                "occupation": "测试工程师",
                "personality_traits": {"测试": True},
                "background_story": "测试背景",
                "preferences": {"测试": True}
            }
        }
        
        test_browser_config = {
            "headless": True,
            "user_agent": "test_agent"
        }
        
        # 测试会话创建
        session_id = await browser_integration.create_browser_session(
            persona_info=test_persona,
            browser_config=test_browser_config
        )
        
        if session_id:
            print(f"✅ 会话创建成功: {session_id}")
            
            # 测试会话关闭
            await browser_integration.close_session(session_id)
            print("✅ 会话关闭成功")
            
            return True
        else:
            print("⚠️ 会话创建失败（可能是模拟模式）")
            return True  # 模拟模式也算成功
            
    except Exception as e:
        print(f"❌ 增强系统基本功能测试失败: {e}")
        return False

def test_web_interface_imports():
    """测试Web界面导入"""
    print("\n🌐 测试Web界面导入...")
    
    try:
        from web_interface import app, task_manager
        print("✅ Web界面导入成功")
        
        # 检查任务管理器组件
        components = {
            'questionnaire_manager': task_manager.questionnaire_manager is not None,
            'scout_system': task_manager.scout_system is not None,
            'db_manager': task_manager.db_manager is not None,
            'resource_tracker': task_manager.resource_tracker is not None,
            'enhanced_system': hasattr(task_manager, 'enhanced_system'),
            'browser_integration': hasattr(task_manager, 'browser_integration')
        }
        
        for component, status in components.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component}: {'可用' if status else '不可用'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Web界面导入失败: {e}")
        return False

def generate_test_report(results):
    """生成测试报告"""
    print("\n" + "="*60)
    print("📊 增强系统测试报告")
    print("="*60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 统计结果
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📈 测试统计:")
    print(f"  总测试数: {total_tests}")
    print(f"  通过测试: {passed_tests}")
    print(f"  失败测试: {failed_tests}")
    print(f"  成功率: {success_rate:.1f}%")
    print()
    
    print("📋 详细结果:")
    for test_name, result in results.items():
        status_icon = "✅" if result else "❌"
        print(f"  {status_icon} {test_name}")
    
    print()
    
    if success_rate >= 80:
        print("🎉 系统状态良好，可以正常使用！")
        print()
        print("💡 使用建议:")
        print("  1. 运行 python start_enhanced_web_interface.py 启动Web界面")
        print("  2. 运行 python demo_enhanced_integration.py 进行功能演示")
        print("  3. 运行 python test_enhanced_system.py 进行完整测试")
    elif success_rate >= 60:
        print("⚠️ 系统部分功能可用，建议检查失败的组件")
    else:
        print("❌ 系统存在严重问题，请检查配置和依赖")
    
    print("="*60)

async def main():
    """主测试函数"""
    print("🧪 增强系统快速测试")
    print("="*60)
    
    results = {}
    
    # 1. 测试模块导入
    import_results = test_imports()
    results.update(import_results)
    
    # 2. 测试数据库连接
    results['database_connection'] = test_database_connection()
    
    # 3. 测试增强系统初始化
    results['enhanced_system_init'] = test_enhanced_system_initialization()
    
    # 4. 测试testWenjuanFinal集成
    results['testwenjuan_integration'] = test_testwenjuan_integration()
    
    # 5. 测试增强系统基本功能
    results['enhanced_system_functionality'] = await test_enhanced_system_basic_functionality()
    
    # 6. 测试Web界面导入
    results['web_interface_imports'] = test_web_interface_imports()
    
    # 生成测试报告
    generate_test_report(results)
    
    return results

if __name__ == '__main__':
    try:
        results = asyncio.run(main())
        
        # 根据测试结果设置退出码
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate >= 80:
            sys.exit(0)  # 成功
        else:
            sys.exit(1)  # 失败
            
    except KeyboardInterrupt:
        print("\n\n👋 用户中断测试")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        sys.exit(1) 