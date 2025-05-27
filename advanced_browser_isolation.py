#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
高级浏览器隔离配置脚本
展示如何配置更好的浏览器环境隔离效果
"""

import asyncio
import random
from questionnaire_system import AdsPowerManager, ADSPOWER_CONFIG

class AdvancedBrowserIsolation:
    """高级浏览器隔离配置器"""
    
    def __init__(self):
        self.manager = AdsPowerManager(ADSPOWER_CONFIG)
        self.browsers = []
    
    def generate_random_config(self, index):
        """生成随机化的浏览器配置"""
        
        # 随机屏幕分辨率
        resolutions = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864},
            {"width": 1600, "height": 900}
        ]
        
        # 随机操作系统
        platforms = [
            {"name": "Windows", "version": "10"},
            {"name": "Windows", "version": "11"},
            {"name": "macOS", "version": "13"},
            {"name": "macOS", "version": "14"}
        ]
        
        # 随机语言
        languages = ["zh-CN", "en-US", "ja-JP", "ko-KR", "de-DE"]
        
        # 随机时区
        timezones = [
            "Asia/Shanghai",
            "America/New_York", 
            "Europe/London",
            "Asia/Tokyo",
            "Australia/Sydney"
        ]
        
        resolution = random.choice(resolutions)
        platform = random.choice(platforms)
        language = random.choice(languages)
        timezone = random.choice(timezones)
        
        # 高级配置（这些在AdsPower中需要付费版本才能完全自定义）
        config = {
            "name": f"高级隔离测试{index}",
            "group_id": "0",
            "remark": f"高级隔离浏览器{index}",
            "user_proxy_config": {
                "proxy_soft": "no_proxy",
                "proxy_type": "noproxy"
                # 如果有代理，可以配置：
                # "proxy_type": "http",
                # "proxy_host": "proxy.example.com",
                # "proxy_port": "8080"
            },
            # 以下配置在免费版本中可能不可用
            "fingerprint_config": {
                "screen_resolution": f"{resolution['width']}x{resolution['height']}",
                "language": language,
                "timezone": timezone,
                "platform": platform['name'],
                "canvas_noise": True,
                "webgl_noise": True,
                "audio_noise": True
            }
        }
        
        return config, {
            "resolution": resolution,
            "platform": platform,
            "language": language,
            "timezone": timezone
        }
    
    async def create_advanced_browsers(self, count=2):
        """创建高级隔离的浏览器"""
        print(f"🚀 创建 {count} 个高级隔离浏览器...")
        
        for i in range(count):
            try:
                config, expected = self.generate_random_config(i + 1)
                
                print(f"\n   创建浏览器 {i+1}/{count}")
                print(f"   预期配置:")
                print(f"     分辨率: {expected['resolution']['width']}x{expected['resolution']['height']}")
                print(f"     平台: {expected['platform']['name']} {expected['platform']['version']}")
                print(f"     语言: {expected['language']}")
                print(f"     时区: {expected['timezone']}")
                
                # 创建基础配置（因为高级配置可能需要付费版本）
                basic_config = {
                    "name": config["name"],
                    "group_id": config["group_id"],
                    "remark": config["remark"],
                    "user_proxy_config": config["user_proxy_config"]
                }
                
                result = self.manager._make_request("POST", "/user/create", basic_config)
                
                if result.get("code") == 0:
                    profile_id = result["data"]["id"]
                    
                    # 启动浏览器
                    browser_info = await self.manager.start_browser(profile_id)
                    
                    if browser_info:
                        browser = {
                            "id": profile_id,
                            "name": config["name"],
                            "port": browser_info.get('debug_port'),
                            "expected_config": expected
                        }
                        self.browsers.append(browser)
                        print(f"   ✅ 浏览器启动成功: {profile_id}")
                        await asyncio.sleep(3)
                    else:
                        print(f"   ❌ 浏览器启动失败")
                else:
                    print(f"   ❌ 配置文件创建失败: {result.get('msg', '未知错误')}")
                    
            except Exception as e:
                print(f"   ❌ 创建浏览器异常: {e}")
        
        return self.browsers
    
    def show_advanced_verification_guide(self):
        """显示高级验证指南"""
        print("\n" + "="*80)
        print("🔬 高级浏览器隔离验证指南")
        print("="*80)
        
        print(f"\n📱 创建的高级隔离浏览器：")
        for i, browser in enumerate(self.browsers, 1):
            expected = browser['expected_config']
            print(f"\n  浏览器{i}: {browser['name']}")
            print(f"    端口: {browser['port']}")
            print(f"    预期分辨率: {expected['resolution']['width']}x{expected['resolution']['height']}")
            print(f"    预期平台: {expected['platform']['name']}")
            print(f"    预期语言: {expected['language']}")
            print(f"    预期时区: {expected['timezone']}")
        
        print(f"\n🔍 高级验证步骤：")
        
        print(f"\n1. 基础指纹对比")
        print(f"   在每个浏览器控制台运行：")
        print(f"```javascript")
        print(f"console.log('=== 基础信息 ===');")
        print(f"console.log('User-Agent:', navigator.userAgent);")
        print(f"console.log('平台:', navigator.platform);")
        print(f"console.log('语言:', navigator.language);")
        print(f"console.log('屏幕:', screen.width + 'x' + screen.height);")
        print(f"console.log('时区:', Intl.DateTimeFormat().resolvedOptions().timeZone);")
        print(f"```")
        
        print(f"\n2. Canvas指纹对比")
        print(f"```javascript")
        print(f"var canvas = document.createElement('canvas');")
        print(f"var ctx = canvas.getContext('2d');")
        print(f"ctx.textBaseline = 'top';")
        print(f"ctx.font = '14px Arial';")
        print(f"ctx.fillText('指纹测试 🎨', 2, 2);")
        print(f"console.log('Canvas指纹:', canvas.toDataURL().substring(0, 50));")
        print(f"```")
        
        print(f"\n3. WebGL指纹对比")
        print(f"```javascript")
        print(f"var canvas = document.createElement('canvas');")
        print(f"var gl = canvas.getContext('webgl');")
        print(f"if (gl) {{")
        print(f"    console.log('WebGL厂商:', gl.getParameter(gl.VENDOR));")
        print(f"    console.log('WebGL渲染器:', gl.getParameter(gl.RENDERER));")
        print(f"}} else {{")
        print(f"    console.log('WebGL不支持');")
        print(f"}}") 
        print(f"```")
        
        print(f"\n4. 高级检测网站")
        print(f"   访问以下专业检测网站：")
        print(f"   - https://browserleaks.com/ (综合检测)")
        print(f"   - https://amiunique.org/ (唯一性评分)")
        print(f"   - https://coveryourtracks.eff.org/ (EFF隐私检测)")
        print(f"   - https://www.deviceinfo.me/ (设备信息)")
        
        print(f"\n🎯 评估标准：")
        print(f"✅ 优秀隔离 (90-100分)：")
        print(f"   - 所有关键指纹都不同")
        print(f"   - Canvas/WebGL指纹完全不同")
        print(f"   - 检测网站显示不同的设备特征")
        print(f"")
        print(f"✅ 良好隔离 (70-89分)：")
        print(f"   - 大部分指纹不同")
        print(f"   - 少数指纹相同但不影响整体隔离")
        print(f"")
        print(f"⚠️ 一般隔离 (50-69分)：")
        print(f"   - 部分指纹相同")
        print(f"   - 需要优化配置")
        print(f"")
        print(f"❌ 隔离失败 (0-49分)：")
        print(f"   - 大部分指纹相同")
        print(f"   - 明显是同一设备")
        
        print(f"\n💡 优化建议：")
        print(f"1. 配置代理IP：")
        print(f"   - 使用不同地区的住宅代理")
        print(f"   - 确保IP地址完全不同")
        print(f"")
        print(f"2. 启用高级指纹随机化：")
        print(f"   - Canvas噪声注入")
        print(f"   - WebGL参数随机化")
        print(f"   - 音频指纹混淆")
        print(f"")
        print(f"3. 自定义浏览器配置：")
        print(f"   - 不同的屏幕分辨率")
        print(f"   - 不同的语言设置")
        print(f"   - 不同的时区配置")
        print(f"")
        print(f"4. 行为模拟：")
        print(f"   - 模拟真实用户的浏览行为")
        print(f"   - 随机的停留时间和点击模式")
        print(f"   - 不同的浏览器插件配置")
    
    async def cleanup_browsers(self):
        """清理浏览器"""
        print(f"\n🧹 清理高级隔离浏览器...")
        for browser in self.browsers:
            try:
                await self.manager.stop_browser(browser['id'])
                await asyncio.sleep(1)
                await self.manager.delete_browser_profile(browser['id'])
                print(f"✅ 已清理: {browser['name']}")
            except Exception as e:
                print(f"❌ 清理失败: {e}")

async def main():
    """主函数"""
    print("🚀 高级浏览器隔离配置")
    print("="*50)
    
    isolator = AdvancedBrowserIsolation()
    
    try:
        # 创建高级隔离浏览器
        browsers = await isolator.create_advanced_browsers(2)
        
        if len(browsers) < 2:
            print("❌ 需要至少2个浏览器")
            return
        
        # 显示验证指南
        isolator.show_advanced_verification_guide()
        
        # 等待用户测试
        print(f"\n⏳ 请按照上述指南进行高级验证...")
        print(f"完成后按Enter键清理资源...")
        input()
        
        # 清理资源
        await isolator.cleanup_browsers()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 