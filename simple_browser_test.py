#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单浏览器差异验证脚本
快速创建两个浏览器并提供简单的验证方法
"""

import asyncio
import time
from questionnaire_system import AdsPowerManager, ADSPOWER_CONFIG

async def create_two_browsers():
    """创建两个浏览器进行对比"""
    print("🚀 创建两个独立浏览器...")
    
    manager = AdsPowerManager(ADSPOWER_CONFIG)
    browsers = []
    
    for i in range(2):
        try:
            # 创建配置文件
            profile_config = {
                "name": f"简单测试{i+1}",
                "group_id": "0",
                "remark": f"简单测试浏览器{i+1}",
                "user_proxy_config": {
                    "proxy_soft": "no_proxy",
                    "proxy_type": "noproxy"
                }
            }
            
            result = manager._make_request("POST", "/user/create", profile_config)
            
            if result.get("code") == 0:
                profile_id = result["data"]["id"]
                
                # 启动浏览器
                browser_info = await manager.start_browser(profile_id)
                
                if browser_info:
                    browsers.append({
                        "id": profile_id,
                        "name": f"简单测试{i+1}",
                        "port": browser_info.get('debug_port')
                    })
                    print(f"✅ 浏览器{i+1}启动成功: {profile_id}")
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"❌ 创建浏览器{i+1}失败: {e}")
    
    return manager, browsers

def show_verification_steps(browsers):
    """显示验证步骤"""
    print("\n" + "="*60)
    print("🔍 验证两个浏览器是否像不同的电脑")
    print("="*60)
    
    print(f"\n📱 你现在有两个独立的浏览器：")
    for i, browser in enumerate(browsers, 1):
        print(f"  浏览器{i}: {browser['name']} (端口: {browser['port']})")
    
    print(f"\n🎯 最简单的验证方法：")
    print(f"1. 打开AdsPower客户端")
    print(f"2. 找到这两个浏览器配置文件")
    print(f"3. 在每个浏览器中访问: https://whatismyipaddress.com/")
    print(f"4. 在每个浏览器中按F12，在控制台运行以下代码：")
    
    print(f"\n```javascript")
    print(f"// 复制这段代码到浏览器控制台")
    print(f"console.log('浏览器信息:');")
    print(f"console.log('User-Agent:', navigator.userAgent.substring(0, 80) + '...');")
    print(f"console.log('屏幕分辨率:', screen.width + 'x' + screen.height);")
    print(f"console.log('CPU核心数:', navigator.hardwareConcurrency);")
    print(f"console.log('语言:', navigator.language);")
    print(f"console.log('时区:', Intl.DateTimeFormat().resolvedOptions().timeZone);")
    print(f"")
    print(f"// Canvas指纹测试")
    print(f"var canvas = document.createElement('canvas');")
    print(f"var ctx = canvas.getContext('2d');")
    print(f"ctx.fillText('测试', 10, 10);")
    print(f"console.log('Canvas指纹:', canvas.toDataURL().substring(0, 30) + '...');")
    print(f"```")
    
    print(f"\n🎯 期望的结果：")
    print(f"✅ 如果隔离成功，你应该看到：")
    print(f"   - 两个浏览器的User-Agent可能不同")
    print(f"   - Canvas指纹应该不同")
    print(f"   - 其他指纹信息可能有差异")
    print(f"")
    print(f"❌ 如果隔离不够，你会看到：")
    print(f"   - 大部分信息都相同")
    print(f"   - 只有窗口大小等少数信息不同")
    
    print(f"\n💡 提示：")
    print(f"- 当前使用的是基础配置，没有代理IP")
    print(f"- IP地址会相同，但其他指纹应该有差异")
    print(f"- 如果要更好的隔离效果，需要配置代理和高级指纹设置")

async def cleanup_browsers(manager, browsers):
    """清理浏览器"""
    print(f"\n🧹 清理浏览器...")
    for browser in browsers:
        try:
            await manager.stop_browser(browser['id'])
            await asyncio.sleep(1)
            await manager.delete_browser_profile(browser['id'])
            print(f"✅ 已清理: {browser['name']}")
        except Exception as e:
            print(f"❌ 清理失败: {e}")

async def main():
    """主函数"""
    print("🚀 简单浏览器差异验证")
    print("="*40)
    
    try:
        # 创建浏览器
        manager, browsers = await create_two_browsers()
        
        if len(browsers) < 2:
            print("❌ 需要至少2个浏览器")
            return
        
        # 显示验证步骤
        show_verification_steps(browsers)
        
        # 等待用户测试
        print(f"\n⏳ 请按照上述步骤进行测试...")
        print(f"完成后按Enter键清理资源...")
        input()
        
        # 清理资源
        await cleanup_browsers(manager, browsers)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 