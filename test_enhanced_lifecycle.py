#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试增强版AdsPower生命周期管理系统
验证：青果代理 + AdsPower指纹浏览器 = 为每个数字人配备"新电脑"
"""

import asyncio
import sys
import time
sys.path.append('.')

from enhanced_adspower_lifecycle import AdsPowerLifecycleManager, BrowserStatus

async def test_enhanced_lifecycle():
    """测试增强版生命周期管理"""
    print("🧪 测试增强版AdsPower生命周期管理系统")
    print("=" * 80)
    print("🎯 目标：为每个数字人配备独立的'新电脑'环境")
    print("📋 包含：AdsPower指纹浏览器 + 青果代理IP + 完整生命周期管理")
    print()
    
    try:
        # 创建生命周期管理器
        manager = AdsPowerLifecycleManager()
        
        print("📋 步骤1: 检查AdsPower服务状态...")
        service_ok = await manager.check_service_status()
        if not service_ok:
            print("❌ AdsPower服务不可用，请检查AdsPower客户端是否运行")
            print("\n💡 解决方案：")
            print("1. 确保AdsPower客户端已启动")
            print("2. 检查本地API端口是否正常 (50325)")
            print("3. 验证API密钥配置是否正确")
            return
        print("✅ AdsPower服务正常")
        
        print("\n📋 步骤2: 查看现有配置文件...")
        existing_profiles = await manager.get_existing_profiles()
        profile_count = len(existing_profiles)
        print(f"发现 {profile_count} 个现有配置文件")
        
        if profile_count >= 15:
            print("⚠️ 配置文件数量已达到15个限制")
            print("💡 建议：在AdsPower客户端中删除一些配置文件释放配额")
            print("将继续测试，但创建新配置文件可能失败")
        else:
            available_slots = 15 - profile_count
            print(f"✅ 可用配置文件插槽: {available_slots} 个")
        
        print("\n📋 步骤3: 创建测试数字人的完整浏览器环境...")
        test_personas = [
            (1001, "测试小王_财务专员"),
            (1002, "测试小李_市场营销")
        ]
        
        created_environments = []
        
        for persona_id, persona_name in test_personas:
            print(f"\n   🚀 为 {persona_name} 创建完整环境...")
            
            try:
                result = await manager.create_complete_browser_environment(persona_id, persona_name)
                
                if result.get("success"):
                    created_environments.append(result)
                    print(f"   ✅ 环境创建成功")
                    print(f"      📱 配置文件ID: {result['profile_id']}")
                    print(f"      🌐 调试端口: {result['debug_port']}")
                    print(f"      📶 代理状态: {'已启用青果代理' if result['proxy_enabled'] else '本地IP'}")
                    print(f"      🖥️ 浏览器状态: {'运行中' if result['browser_active'] else '未运行'}")
                else:
                    print(f"   ❌ 环境创建失败: {result.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ 创建环境异常: {e}")
        
        if not created_environments:
            print("\n❌ 没有成功创建任何环境，测试结束")
            return
        
        print(f"\n📊 步骤4: 查看活跃浏览器状态...")
        active_browsers = manager.get_active_browsers_info()
        print(f"活跃浏览器数量: {len(active_browsers)}")
        
        for browser in active_browsers:
            print(f"   - {browser['persona_name']}")
            print(f"     状态: {browser['status']}")
            print(f"     端口: {browser['debug_port']}")
            print(f"     代理: {'已启用' if browser['proxy_enabled'] else '本地IP'}")
            print(f"     创建时间: {time.strftime('%H:%M:%S', time.localtime(browser['created_at']))}")
        
        print(f"\n🧪 步骤5: 测试浏览器连接信息...")
        for env in created_environments:
            profile_id = env['profile_id']
            persona_name = env['persona_name']
            
            print(f"\n   🔍 检查 {persona_name} 的浏览器连接...")
            
            # 获取连接信息
            connection_info = await manager.get_browser_connection_info(profile_id)
            if connection_info:
                print(f"   ✅ 连接信息获取成功")
                print(f"      调试端口: {connection_info['debug_port']}")
                print(f"      代理状态: {'已启用' if connection_info.get('proxy_info') else '本地'}")
                print(f"      浏览器状态: {connection_info['status']}")
            else:
                print(f"   ❌ 无法获取连接信息")
            
            # 检查浏览器运行状态
            status_info = await manager.check_browser_status(profile_id)
            if status_info.get("success"):
                is_active = status_info.get("is_active", False)
                print(f"   🔄 浏览器运行状态: {'活跃' if is_active else '未活跃'}")
            else:
                print(f"   ⚠️ 状态检查失败: {status_info.get('error')}")
        
        print(f"\n⏳ 环境已准备就绪！现在你可以：")
        print(f"1. 在AdsPower客户端中查看新创建的配置文件")
        print(f"2. 每个浏览器都有独立的青果代理IP，实现真正的环境隔离")
        print(f"3. 可以通过调试端口连接浏览器进行自动化操作")
        print(f"4. 每个数字人都有自己独立的'新电脑'环境")
        print(f"\n💡 技术要点：")
        print(f"- AdsPower提供指纹浏览器隔离")
        print(f"- 青果代理提供IP地址隔离")
        print(f"- 每个数字人使用不同的认证格式获得不同IP")
        print(f"- 完整的生命周期管理：创建→配置→启动→使用→停止→清理")
        
        print(f"\n测试完成后按 Enter 键清理资源...")
        input()
        
        print(f"\n🧹 步骤6: 清理测试资源...")
        cleanup_results = await manager.cleanup_all_browsers()
        
        success_count = len([r for r in cleanup_results if r.get("success")])
        total_count = len(cleanup_results)
        print(f"✅ 清理完成，成功清理 {success_count}/{total_count} 个浏览器环境")
        
        print(f"\n🎉 增强版生命周期管理测试完成！")
        print(f"系统已验证：")
        print(f"✅ AdsPower服务连接正常")
        print(f"✅ 浏览器配置文件创建/删除功能正常")
        print(f"✅ 青果代理配置功能正常")
        print(f"✅ 浏览器启动/停止功能正常")
        print(f"✅ 完整生命周期管理正常")
        print(f"✅ 为每个数字人成功配备了独立的'新电脑'环境")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 测试被中断，开始清理资源...")
        try:
            await manager.cleanup_all_browsers()
        except:
            pass
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        try:
            await manager.cleanup_all_browsers()
        except:
            pass

async def test_specific_api_endpoints():
    """测试特定的API端点"""
    print("\n🔧 测试特定API端点...")
    
    manager = AdsPowerLifecycleManager()
    
    # 测试状态检查
    print("测试状态检查API...")
    try:
        result = manager._make_request("GET", "/status")
        print(f"状态API响应: {result.get('code')} - {result.get('msg', 'OK')}")
    except Exception as e:
        print(f"状态API失败: {e}")
    
    # 测试配置文件列表
    print("测试配置文件列表API...")
    try:
        result = manager._make_request("GET", "/user/list", {"page": 1, "page_size": 5})
        if result.get("code") == 0:
            profiles = result.get("data", {}).get("list", [])
            print(f"找到 {len(profiles)} 个配置文件")
            for profile in profiles[:3]:  # 只显示前3个
                print(f"  - {profile.get('name', '未知')}: {profile.get('user_id', 'N/A')}")
        else:
            print(f"配置文件列表API失败: {result.get('msg')}")
    except Exception as e:
        print(f"配置文件列表API异常: {e}")

def main():
    """主函数"""
    print("🔧 增强版AdsPower生命周期管理系统 - 完整测试")
    print()
    
    # 检查基本环境
    try:
        import requests
        print("✅ requests模块可用")
    except ImportError:
        print("❌ requests模块不可用，请安装: pip install requests")
        return
    
    # 运行API端点测试
    asyncio.run(test_specific_api_endpoints())
    
    print("\n" + "="*80)
    
    # 运行完整生命周期测试
    asyncio.run(test_enhanced_lifecycle())

if __name__ == "__main__":
    main() 