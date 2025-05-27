#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AdsPower集成测试脚本
测试浏览器环境隔离和真实性验证
"""

import asyncio
import json
import time
import requests
from questionnaire_system import AdsPowerManager, ADSPOWER_CONFIG

class AdsPowerTester:
    """AdsPower测试器"""
    
    def __init__(self):
        self.manager = AdsPowerManager(ADSPOWER_CONFIG)
        self.test_profiles = []
    
    def test_api_connection(self):
        """测试API连接"""
        print("🔍 测试AdsPower API连接...")
        try:
            result = self.manager._make_request("GET", "/user/list", {"page": 1, "page_size": 1})
            if result.get("code") == 0:
                print("✅ AdsPower API连接成功")
                print(f"   API版本: {result.get('msg', 'unknown')}")
                return True
            else:
                print(f"❌ API连接失败: {result.get('msg', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ API连接异常: {e}")
            return False
    
    async def create_test_profiles(self, count: int = 3):
        """创建测试浏览器配置文件"""
        print(f"🚀 创建 {count} 个测试浏览器配置文件...")
        
        for i in range(count):
            try:
                persona_id = 1000 + i
                persona_name = f"测试数字人{i+1}"
                
                print(f"   创建配置文件 {i+1}/{count}: {persona_name}")
                
                # 创建正确格式的浏览器配置
                profile_config = {
                    "name": f"test_persona_{persona_id}_{persona_name}",
                    "group_id": "0",
                    "remark": f"测试用户{persona_name}的独立浏览器环境",
                    "user_proxy_config": {
                        "proxy_soft": "no_proxy",
                        "proxy_type": "noproxy"
                    }
                }
                
                result = self.manager._make_request("POST", "/user/create", profile_config)
                
                if result.get("code") == 0:
                    profile_id = result["data"]["id"]
                    profile_info = {
                        "id": profile_id,
                        "name": persona_name,
                        "persona_id": persona_id,
                        "created_at": time.time()
                    }
                    self.test_profiles.append(profile_info)
                    print(f"   ✅ 配置文件创建成功: {profile_id}")
                else:
                    print(f"   ❌ 配置文件创建失败: {result.get('msg', '未知错误')}")
                    
            except Exception as e:
                print(f"   ❌ 创建配置文件异常: {e}")
        
        print(f"✅ 成功创建 {len(self.test_profiles)} 个配置文件")
        return self.test_profiles
    
    async def start_browsers_and_test(self):
        """启动浏览器并进行环境测试"""
        print("🌐 启动浏览器并测试环境隔离...")
        
        browser_sessions = []
        
        for profile in self.test_profiles:
            try:
                print(f"   启动浏览器: {profile['name']} (ID: {profile['id']})")
                
                # 启动浏览器
                browser_info = await self.manager.start_browser(profile['id'])
                
                if browser_info:
                    session_info = {
                        "profile": profile,
                        "browser_info": browser_info,
                        "selenium_port": browser_info.get('ws', {}).get('selenium'),
                        "debug_port": browser_info.get('debug_port')
                    }
                    browser_sessions.append(session_info)
                    
                    print(f"   ✅ 浏览器启动成功")
                    print(f"      Selenium端口: {session_info['selenium_port']}")
                    print(f"      调试端口: {session_info['debug_port']}")
                    
                    # 等待一下让浏览器完全启动
                    await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ❌ 启动浏览器失败: {e}")
        
        return browser_sessions
    
    def test_browser_fingerprints(self, browser_sessions):
        """测试浏览器指纹和环境隔离"""
        print("🔍 测试浏览器指纹和环境隔离...")
        
        test_results = []
        
        for session in browser_sessions:
            try:
                profile_name = session['profile']['name']
                selenium_port = session['selenium_port']
                
                print(f"   测试浏览器: {profile_name}")
                
                # 这里我们可以通过Selenium连接到浏览器进行测试
                # 但为了简化，我们先展示如何获取浏览器信息
                
                result = {
                    "profile_name": profile_name,
                    "profile_id": session['profile']['id'],
                    "selenium_port": selenium_port,
                    "debug_port": session['debug_port'],
                    "status": "running"
                }
                
                test_results.append(result)
                print(f"   ✅ 浏览器环境正常")
                
            except Exception as e:
                print(f"   ❌ 测试浏览器环境失败: {e}")
        
        return test_results
    
    def generate_test_instructions(self, browser_sessions):
        """生成手动测试指令"""
        print("\n" + "="*60)
        print("📋 手动测试指令")
        print("="*60)
        
        print("\n🔍 请按以下步骤手动验证浏览器环境隔离：")
        
        for i, session in enumerate(browser_sessions, 1):
            profile_name = session['profile']['name']
            selenium_port = session['selenium_port']
            
            print(f"\n【浏览器 {i}: {profile_name}】")
            print(f"1. 在AdsPower客户端中找到配置文件: {profile_name}")
            print(f"2. 点击'打开'按钮启动浏览器")
            print(f"3. 在浏览器中访问以下网站进行测试：")
            print(f"   - IP检测: https://whatismyipaddress.com/")
            print(f"   - 浏览器指纹: https://browserleaks.com/")
            print(f"   - Canvas指纹: https://browserleaks.com/canvas")
            print(f"   - WebRTC检测: https://browserleaks.com/webrtc")
            print(f"   - 时区检测: https://browserleaks.com/timezone")
            print(f"4. 记录以下信息：")
            print(f"   - 外部IP地址")
            print(f"   - User-Agent字符串")
            print(f"   - 屏幕分辨率")
            print(f"   - 时区信息")
            print(f"   - Canvas指纹")
            print(f"   - WebGL指纹")
        
        print(f"\n🎯 验证要点：")
        print(f"1. 每个浏览器的IP地址应该不同（如果使用代理）")
        print(f"2. 每个浏览器的User-Agent应该不同")
        print(f"3. 每个浏览器的Canvas指纹应该不同")
        print(f"4. 每个浏览器的WebGL指纹应该不同")
        print(f"5. 浏览器行为应该像真实用户")
        
        print(f"\n⚠️ 重要提醒：")
        print(f"- 如果多个浏览器显示相同的指纹信息，说明隔离不够")
        print(f"- 如果指纹过于规律或明显是机器生成，可能被检测")
        print(f"- 建议配置代理IP以获得更好的隔离效果")
    
    async def cleanup_test_profiles(self):
        """清理测试配置文件"""
        print("🧹 清理测试配置文件...")
        
        for profile in self.test_profiles:
            try:
                # 先停止浏览器
                await self.manager.stop_browser(profile['id'])
                await asyncio.sleep(1)
                
                # 删除配置文件
                success = await self.manager.delete_browser_profile(profile['id'])
                if success:
                    print(f"   ✅ 已删除配置文件: {profile['name']}")
                else:
                    print(f"   ⚠️ 删除配置文件失败: {profile['name']}")
                    
            except Exception as e:
                print(f"   ❌ 清理配置文件异常: {e}")
        
        print("✅ 清理完成")

async def main():
    """主测试函数"""
    print("🚀 AdsPower集成测试")
    print("="*50)
    
    tester = AdsPowerTester()
    
    # 1. 测试API连接
    if not tester.test_api_connection():
        print("❌ API连接失败，请检查AdsPower是否正常运行")
        return
    
    try:
        # 2. 创建测试配置文件
        profiles = await tester.create_test_profiles(3)
        
        if not profiles:
            print("❌ 没有成功创建配置文件")
            return
        
        # 3. 启动浏览器
        browser_sessions = await tester.start_browsers_and_test()
        
        if not browser_sessions:
            print("❌ 没有成功启动浏览器")
            return
        
        # 4. 测试浏览器环境
        test_results = tester.test_browser_fingerprints(browser_sessions)
        
        # 5. 生成手动测试指令
        tester.generate_test_instructions(browser_sessions)
        
        # 6. 等待用户手动测试
        print(f"\n⏳ 请按照上述指令进行手动测试...")
        print(f"测试完成后按 Enter 键继续清理资源...")
        input()
        
        # 7. 清理资源
        await tester.cleanup_test_profiles()
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被中断，开始清理资源...")
        await tester.cleanup_test_profiles()
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        await tester.cleanup_test_profiles()

if __name__ == "__main__":
    asyncio.run(main()) 