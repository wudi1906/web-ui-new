#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
手动浏览器对比验证脚本
创建两个独立的浏览器，指导用户手动验证环境隔离效果
"""

import asyncio
import time
from questionnaire_system import AdsPowerManager, ADSPOWER_CONFIG

class ManualBrowserComparator:
    """手动浏览器对比器"""
    
    def __init__(self):
        self.manager = AdsPowerManager(ADSPOWER_CONFIG)
        self.browser_profiles = []
    
    async def create_comparison_browsers(self):
        """创建用于对比的浏览器"""
        print("🚀 创建两个独立的浏览器进行对比...")
        
        browser_sessions = []
        
        for i in range(2):
            try:
                persona_id = 4000 + i
                persona_name = f"对比浏览器{i+1}"
                
                print(f"\n   创建浏览器 {i+1}/2: {persona_name}")
                
                # 创建配置文件
                profile_config = {
                    "name": f"manual_compare_{persona_id}",
                    "group_id": "0",
                    "remark": f"手动对比测试浏览器{i+1}",
                    "user_proxy_config": {
                        "proxy_soft": "no_proxy",
                        "proxy_type": "noproxy"
                    }
                }
                
                # 创建配置文件
                result = self.manager._make_request("POST", "/user/create", profile_config)
                
                if result.get("code") == 0:
                    profile_id = result["data"]["id"]
                    
                    # 启动浏览器
                    browser_info = await self.manager.start_browser(profile_id)
                    
                    if browser_info:
                        session = {
                            "profile_id": profile_id,
                            "profile_name": persona_name,
                            "browser_info": browser_info,
                            "selenium_port": browser_info.get('ws', {}).get('selenium'),
                            "debug_port": browser_info.get('debug_port')
                        }
                        browser_sessions.append(session)
                        self.browser_profiles.append({"id": profile_id, "name": persona_name})
                        
                        print(f"   ✅ 浏览器启动成功: {profile_id}")
                        print(f"   📍 调试端口: {browser_info.get('debug_port')}")
                        
                        await asyncio.sleep(3)  # 等待浏览器完全启动
                    else:
                        print(f"   ❌ 浏览器启动失败")
                else:
                    print(f"   ❌ 配置文件创建失败: {result.get('msg', '未知错误')}")
                    
            except Exception as e:
                print(f"   ❌ 创建浏览器异常: {e}")
        
        print(f"\n✅ 成功启动 {len(browser_sessions)} 个浏览器")
        return browser_sessions
    
    def generate_manual_test_guide(self, browser_sessions):
        """生成手动测试指南"""
        print("\n" + "="*80)
        print("🔍 手动浏览器环境对比指南")
        print("="*80)
        
        if len(browser_sessions) < 2:
            print("❌ 需要至少2个浏览器才能进行对比")
            return
        
        print("\n📋 现在你有两个独立的浏览器实例：")
        for i, session in enumerate(browser_sessions, 1):
            print(f"  浏览器{i}: {session['profile_name']} (端口: {session['debug_port']})")
        
        print(f"\n🎯 第一步：在AdsPower客户端中找到这两个浏览器")
        print(f"1. 打开AdsPower客户端")
        print(f"2. 在浏览器列表中找到以下配置文件：")
        for i, session in enumerate(browser_sessions, 1):
            print(f"   - {session['profile_name']} (ID: {session['profile_id']})")
        print(f"3. 这两个浏览器应该已经自动启动了")
        
        print(f"\n🌐 第二步：访问指纹检测网站")
        print(f"在每个浏览器中分别访问以下网站，记录结果：")
        
        test_sites = [
            {
                "name": "IP地址检测",
                "url": "https://whatismyipaddress.com/",
                "check": "记录显示的IP地址"
            },
            {
                "name": "浏览器指纹检测",
                "url": "https://browserleaks.com/",
                "check": "查看整体指纹评分"
            },
            {
                "name": "Canvas指纹",
                "url": "https://browserleaks.com/canvas",
                "check": "记录Canvas指纹哈希值"
            },
            {
                "name": "WebGL指纹",
                "url": "https://browserleaks.com/webgl",
                "check": "记录WebGL渲染器信息"
            },
            {
                "name": "字体检测",
                "url": "https://browserleaks.com/fonts",
                "check": "查看检测到的字体数量"
            },
            {
                "name": "时区检测",
                "url": "https://browserleaks.com/timezone",
                "check": "记录时区信息"
            }
        ]
        
        for i, site in enumerate(test_sites, 1):
            print(f"\n   {i}. {site['name']}")
            print(f"      网址: {site['url']}")
            print(f"      检查: {site['check']}")
        
        print(f"\n📊 第三步：对比结果")
        print(f"创建一个对比表格，记录两个浏览器的差异：")
        print(f"""
┌─────────────────┬─────────────────┬─────────────────┐
│     检测项目    │    浏览器1      │    浏览器2      │
├─────────────────┼─────────────────┼─────────────────┤
│ IP地址          │                 │                 │
├─────────────────┼─────────────────┼─────────────────┤
│ Canvas指纹      │                 │                 │
├─────────────────┼─────────────────┼─────────────────┤
│ WebGL渲染器     │                 │                 │
├─────────────────┼─────────────────┼─────────────────┤
│ 检测到的字体数  │                 │                 │
├─────────────────┼─────────────────┼─────────────────┤
│ 时区信息        │                 │                 │
├─────────────────┼─────────────────┼─────────────────┤
│ 整体指纹评分    │                 │                 │
└─────────────────┴─────────────────┴─────────────────┘
        """)
        
        print(f"\n🎯 第四步：评估隔离效果")
        print(f"根据对比结果评估：")
        print(f"✅ 优秀隔离：所有关键指纹都不同")
        print(f"   - IP地址不同（如果使用代理）")
        print(f"   - Canvas指纹完全不同")
        print(f"   - WebGL信息不同")
        print(f"   - 字体检测结果不同")
        print(f"")
        print(f"⚠️ 一般隔离：部分指纹相同")
        print(f"   - IP地址相同但其他指纹不同")
        print(f"   - 大部分指纹不同")
        print(f"")
        print(f"❌ 隔离失败：大部分指纹相同")
        print(f"   - 除了窗口大小外，其他都相同")
        print(f"   - 明显是同一台电脑")
        
        print(f"\n💡 第五步：高级测试（可选）")
        print(f"如果想要更深入的测试，可以：")
        print(f"1. 在两个浏览器中登录不同的网站账号")
        print(f"2. 设置不同的语言偏好")
        print(f"3. 访问一些需要地理位置的网站")
        print(f"4. 测试WebRTC泄露检测")
        print(f"5. 检查DNS泄露")
        
        print(f"\n⚠️ 重要提醒：")
        print(f"- 如果两个浏览器显示完全相同的指纹，说明隔离不够")
        print(f"- 真正的隔离应该让每个浏览器看起来像不同的电脑")
        print(f"- 可以通过配置代理、调整指纹设置来改善隔离效果")
    
    def generate_quick_test_script(self):
        """生成快速测试脚本"""
        print(f"\n🚀 快速测试脚本")
        print(f"你也可以在浏览器控制台中运行以下JavaScript代码：")
        
        js_code = """
// 快速指纹检测脚本
console.log("=== 浏览器指纹信息 ===");
console.log("User-Agent:", navigator.userAgent);
console.log("平台:", navigator.platform);
console.log("语言:", navigator.language);
console.log("屏幕分辨率:", screen.width + "x" + screen.height);
console.log("CPU核心数:", navigator.hardwareConcurrency);
console.log("设备内存:", navigator.deviceMemory || "未知");
console.log("时区:", Intl.DateTimeFormat().resolvedOptions().timeZone);

// Canvas指纹
var canvas = document.createElement('canvas');
var ctx = canvas.getContext('2d');
ctx.textBaseline = 'top';
ctx.font = '14px Arial';
ctx.fillText('指纹测试', 2, 2);
console.log("Canvas指纹:", canvas.toDataURL().substring(0, 50) + "...");

// WebGL信息
var gl = canvas.getContext('webgl');
if (gl) {
    console.log("WebGL厂商:", gl.getParameter(gl.VENDOR));
    console.log("WebGL渲染器:", gl.getParameter(gl.RENDERER));
} else {
    console.log("WebGL: 不支持");
}

console.log("=== 检测完成 ===");
        """
        
        print(f"```javascript")
        print(js_code)
        print(f"```")
        
        print(f"\n使用方法：")
        print(f"1. 在每个浏览器中按 F12 打开开发者工具")
        print(f"2. 切换到 Console（控制台）标签")
        print(f"3. 复制粘贴上面的代码并按回车")
        print(f"4. 对比两个浏览器的输出结果")
    
    async def cleanup_resources(self):
        """清理测试资源"""
        print("\n🧹 清理测试资源...")
        
        for profile in self.browser_profiles:
            try:
                # 停止浏览器
                await self.manager.stop_browser(profile['id'])
                await asyncio.sleep(1)
                
                # 删除配置文件
                success = await self.manager.delete_browser_profile(profile['id'])
                if success:
                    print(f"   ✅ 已删除: {profile['name']}")
                else:
                    print(f"   ⚠️ 删除失败: {profile['name']}")
                    
            except Exception as e:
                print(f"   ❌ 清理异常: {e}")
        
        print("✅ 资源清理完成")

async def main():
    """主函数"""
    print("🚀 手动浏览器环境对比测试")
    print("="*50)
    
    comparator = ManualBrowserComparator()
    
    try:
        # 1. 创建对比浏览器
        browser_sessions = await comparator.create_comparison_browsers()
        
        if len(browser_sessions) < 2:
            print("❌ 需要至少2个浏览器才能进行对比")
            return
        
        # 2. 生成手动测试指南
        comparator.generate_manual_test_guide(browser_sessions)
        
        # 3. 生成快速测试脚本
        comparator.generate_quick_test_script()
        
        # 4. 等待用户完成测试
        print(f"\n⏳ 请按照上述指南进行手动测试...")
        print(f"测试完成后，请告诉我你观察到的差异！")
        print(f"按 Enter 键继续清理资源...")
        input()
        
        # 5. 清理资源
        await comparator.cleanup_resources()
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被中断，开始清理资源...")
        await comparator.cleanup_resources()
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        await comparator.cleanup_resources()

if __name__ == "__main__":
    asyncio.run(main()) 