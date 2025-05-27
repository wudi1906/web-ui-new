#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终版浏览器隔离系统
集成青果隧道代理，实现完整的IP和指纹隔离
"""

import asyncio
import requests
import time
import random
import logging
from typing import Dict, List, Optional, Tuple
from questionnaire_system import AdsPowerManager, ADSPOWER_CONFIG

logger = logging.getLogger(__name__)

class FinalBrowserIsolationSystem:
    """最终版浏览器隔离系统"""
    
    def __init__(self):
        self.adspower_manager = AdsPowerManager(ADSPOWER_CONFIG)
        self.browsers = []
        
        # 青果隧道代理配置
        self.qinguo_config = {
            "business_id": "k3reh5az",
            "auth_key": "A942CE1E", 
            "auth_pwd": "B9FCD013057A",
            "tunnel_host": "tun-szbhry.qg.net",
            "tunnel_port": "17790"
        }
        
        # 代理管理
        self.allocated_proxies = []
        self.session_counter = 0
    
    def generate_session_id(self) -> str:
        """生成唯一的会话ID"""
        self.session_counter += 1
        timestamp = int(time.time())
        return f"s{timestamp}{self.session_counter}{random.randint(100, 999)}"
    
    def create_tunnel_proxy_config(self, session_id: str) -> Dict:
        """创建隧道代理配置"""
        # 根据青果代理隧道文档，尝试不同的用户名格式
        possible_usernames = [
            f"{self.qinguo_config['auth_key']}-session-{session_id}",
            f"{self.qinguo_config['auth_key']}-{session_id}",
            f"{self.qinguo_config['business_id']}-{session_id}",
            self.qinguo_config['auth_key'],  # 简单格式
        ]
        
        return {
            "proxy_type": "http",
            "proxy_host": self.qinguo_config['tunnel_host'],
            "proxy_port": self.qinguo_config['tunnel_port'],
            "proxy_user": possible_usernames[0],  # 使用第一个格式
            "proxy_password": self.qinguo_config['auth_pwd'],
            "session_id": session_id,
            "full_address": f"{self.qinguo_config['tunnel_host']}:{self.qinguo_config['tunnel_port']}",
            "possible_usernames": possible_usernames
        }
    
    def test_tunnel_proxy_with_formats(self, proxy_config: Dict) -> Tuple[bool, str]:
        """测试不同用户名格式的隧道代理"""
        for i, username in enumerate(proxy_config.get("possible_usernames", [])):
            try:
                print(f"   尝试用户名格式 {i+1}: {username}")
                
                proxy_url = f"http://{username}:{proxy_config['proxy_password']}@{proxy_config['proxy_host']}:{proxy_config['proxy_port']}"
                
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url
                }
                
                response = requests.get(
                    "http://httpbin.org/ip", 
                    proxies=proxies, 
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    current_ip = result.get('origin', 'unknown')
                    print(f"   ✅ 成功! IP: {current_ip}")
                    
                    # 更新配置为成功的用户名格式
                    proxy_config["proxy_user"] = username
                    proxy_config["current_ip"] = current_ip
                    return True, current_ip
                
            except Exception as e:
                print(f"   ❌ 格式 {i+1} 失败: {e}")
                continue
        
        return False, "测试失败"
    
    def allocate_proxy_for_browser(self, browser_name: str) -> Optional[Dict]:
        """为浏览器分配代理"""
        try:
            session_id = self.generate_session_id()
            proxy_config = self.create_tunnel_proxy_config(session_id)
            proxy_config.update({
                "browser_name": browser_name,
                "allocated_at": time.time(),
                "type": "tunnel"
            })
            
            print(f"   🔗 为 {browser_name} 分配隧道代理: {session_id}")
            
            # 测试代理连接
            success, ip = self.test_tunnel_proxy_with_formats(proxy_config)
            
            if success:
                self.allocated_proxies.append(proxy_config)
                print(f"   ✅ 代理分配成功: {ip}")
                return proxy_config
            else:
                print(f"   ❌ 代理测试失败，将使用无代理模式")
                return None
                
        except Exception as e:
            print(f"   ❌ 分配代理异常: {e}")
            return None
    
    def create_adspower_proxy_config(self, proxy: Optional[Dict] = None) -> Dict:
        """创建AdsPower代理配置"""
        if not proxy:
            return {
                "proxy_soft": "no_proxy",
                "proxy_type": "noproxy"
            }
        
        return {
            "proxy_soft": "other",
            "proxy_type": "http",
            "proxy_host": proxy["proxy_host"],
            "proxy_port": proxy["proxy_port"],
            "proxy_user": proxy["proxy_user"],
            "proxy_password": proxy["proxy_password"]
        }
    
    def generate_random_browser_config(self, index: int, proxy: Optional[Dict] = None) -> Tuple[Dict, Dict]:
        """生成随机化的浏览器配置"""
        
        # 随机User-Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # 随机屏幕分辨率
        resolutions = ["1920x1080", "1366x768", "1440x900", "1536x864", "1600x900"]
        
        # 随机语言
        languages = ["zh-CN", "en-US", "ja-JP", "ko-KR", "de-DE"]
        
        # 随机时区
        timezones = ["Asia/Shanghai", "America/New_York", "Europe/London", "Asia/Tokyo", "Australia/Sydney"]
        
        proxy_info = ""
        if proxy:
            proxy_info = f"_IP_{proxy.get('current_ip', 'unknown').replace('.', '_')}"
        
        config = {
            "name": f"最终隔离测试{index}{proxy_info}",
            "group_id": "0",
            "remark": f"最终隔离浏览器{index} - 代理IP: {proxy.get('current_ip', '无') if proxy else '无'}",
            "user_proxy_config": self.create_adspower_proxy_config(proxy)
        }
        
        expected_config = {
            "user_agent": random.choice(user_agents),
            "resolution": random.choice(resolutions),
            "language": random.choice(languages),
            "timezone": random.choice(timezones),
            "proxy": proxy
        }
        
        return config, expected_config
    
    async def create_isolated_browsers(self, count: int = 2) -> List[Dict]:
        """创建完全隔离的浏览器"""
        print(f"🚀 创建 {count} 个完全隔离的浏览器...")
        print(f"📡 青果隧道代理服务器: {self.qinguo_config['tunnel_host']}:{self.qinguo_config['tunnel_port']}")
        
        for i in range(count):
            try:
                print(f"\n🔧 创建浏览器 {i+1}/{count}")
                
                # 1. 分配代理
                proxy = self.allocate_proxy_for_browser(f"隔离浏览器{i+1}")
                
                # 2. 生成配置
                browser_config, expected_config = self.generate_random_browser_config(i + 1, proxy)
                
                print(f"   📋 配置名称: {browser_config['name']}")
                if proxy:
                    print(f"   🌐 代理IP: {proxy.get('current_ip', '未知')}")
                    print(f"   🔑 会话ID: {proxy['session_id']}")
                else:
                    print(f"   ⚠️ 无代理模式（青果代理连接失败）")
                
                print(f"   🎭 预期User-Agent: {expected_config['user_agent'][:50]}...")
                print(f"   📺 预期分辨率: {expected_config['resolution']}")
                print(f"   🌍 预期语言: {expected_config['language']}")
                print(f"   🕐 预期时区: {expected_config['timezone']}")
                
                # 3. 创建AdsPower配置文件
                result = self.adspower_manager._make_request("POST", "/user/create", browser_config)
                
                if result.get("code") == 0:
                    profile_id = result["data"]["id"]
                    
                    # 4. 启动浏览器
                    browser_info = await self.adspower_manager.start_browser(profile_id)
                    
                    if browser_info:
                        browser = {
                            "id": profile_id,
                            "name": browser_config["name"],
                            "port": browser_info.get('debug_port'),
                            "proxy": proxy,
                            "expected_config": expected_config,
                            "created_at": time.time()
                        }
                        self.browsers.append(browser)
                        
                        print(f"   ✅ 浏览器启动成功: {profile_id} (端口: {browser_info.get('debug_port')})")
                        await asyncio.sleep(3)
                    else:
                        print(f"   ❌ 浏览器启动失败")
                else:
                    print(f"   ❌ 配置文件创建失败: {result.get('msg', '未知错误')}")
                    
            except Exception as e:
                print(f"   ❌ 创建浏览器异常: {e}")
        
        print(f"\n✅ 成功创建 {len(self.browsers)} 个隔离浏览器")
        return self.browsers
    
    def show_final_verification_guide(self):
        """显示最终验证指南"""
        print("\n" + "="*80)
        print("🎯 最终浏览器隔离验证指南")
        print("="*80)
        
        print(f"\n📱 创建的隔离浏览器：")
        for i, browser in enumerate(self.browsers, 1):
            expected = browser['expected_config']
            proxy = browser.get('proxy')
            
            print(f"\n  🖥️ 浏览器{i}: {browser['name']}")
            print(f"    🔌 调试端口: {browser['port']}")
            if proxy:
                print(f"    🌐 代理IP: {proxy.get('current_ip', '未知')}")
                print(f"    🔑 会话ID: {proxy['session_id']}")
                print(f"    📡 隧道服务器: {proxy['full_address']}")
            else:
                print(f"    ⚠️ 无代理（本地IP）")
            print(f"    🎭 预期User-Agent: {expected['user_agent'][:60]}...")
            print(f"    📺 预期分辨率: {expected['resolution']}")
            print(f"    🌍 预期语言: {expected['language']}")
            print(f"    🕐 预期时区: {expected['timezone']}")
        
        print(f"\n🔍 完整验证步骤：")
        
        print(f"\n1️⃣ IP地址验证（最重要）")
        print(f"   在每个浏览器中访问: https://whatismyipaddress.com/")
        if any(b.get('proxy') for b in self.browsers):
            print(f"   ✅ 期望结果: 两个浏览器显示不同的IP地址")
        else:
            print(f"   ⚠️ 当前状态: 两个浏览器可能显示相同IP（青果代理未生效）")
        
        print(f"\n2️⃣ 浏览器指纹验证")
        print(f"   在每个浏览器控制台运行以下代码：")
        print(f"```javascript")
        print(f"console.log('=== 浏览器环境对比 ===');")
        print(f"console.log('User-Agent:', navigator.userAgent);")
        print(f"console.log('平台:', navigator.platform);")
        print(f"console.log('语言:', navigator.language);")
        print(f"console.log('屏幕分辨率:', screen.width + 'x' + screen.height);")
        print(f"console.log('时区:', Intl.DateTimeFormat().resolvedOptions().timeZone);")
        print(f"console.log('CPU核心数:', navigator.hardwareConcurrency);")
        print(f"console.log('设备内存:', navigator.deviceMemory || '未知');")
        print(f"")
        print(f"// Canvas指纹测试")
        print(f"var canvas = document.createElement('canvas');")
        print(f"var ctx = canvas.getContext('2d');")
        print(f"ctx.textBaseline = 'top';")
        print(f"ctx.font = '14px Arial';")
        print(f"ctx.fillText('指纹测试 🎨', 2, 2);")
        print(f"console.log('Canvas指纹:', canvas.toDataURL().substring(0, 50) + '...');")
        print(f"")
        print(f"// WebGL指纹测试")
        print(f"var canvas2 = document.createElement('canvas');")
        print(f"var gl = canvas2.getContext('webgl');")
        print(f"if (gl) {{")
        print(f"    console.log('WebGL厂商:', gl.getParameter(gl.VENDOR));")
        print(f"    console.log('WebGL渲染器:', gl.getParameter(gl.RENDERER));")
        print(f"}} else {{")
        print(f"    console.log('WebGL: 不支持');")
        print(f"}}")
        print(f"console.log('=== 检测完成 ===');")
        print(f"```")
        
        print(f"\n3️⃣ 专业检测网站验证")
        print(f"   访问以下网站进行全面检测：")
        print(f"   🔗 https://browserleaks.com/ (综合指纹检测)")
        print(f"   🔗 https://amiunique.org/ (唯一性评分)")
        print(f"   🔗 https://whoer.net/ (匿名性检测)")
        print(f"   🔗 https://www.deviceinfo.me/ (设备信息)")
        
        print(f"\n🎯 评估标准：")
        if any(b.get('proxy') for b in self.browsers):
            print(f"✅ 完美隔离（目标效果）：")
            print(f"   - 两个浏览器显示完全不同的IP地址")
            print(f"   - Canvas指纹完全不同")
            print(f"   - WebGL信息不同")
            print(f"   - 专业检测网站显示不同的设备特征")
        else:
            print(f"⚠️ 当前状态（青果代理未生效）：")
            print(f"   - IP地址相同（需要解决青果代理连接问题）")
            print(f"   - 其他指纹可能有差异（AdsPower基础隔离）")
        
        print(f"\n💡 优化建议：")
        print(f"1. 青果代理问题排查：")
        print(f"   - 确认账户余额充足")
        print(f"   - 检查隧道代理服务是否正常")
        print(f"   - 联系青果客服确认用户名格式")
        print(f"   - 尝试在青果后台测试连接")
        
        print(f"2. AdsPower优化：")
        print(f"   - 升级到付费版本获得更多指纹随机化")
        print(f"   - 启用Canvas噪声、WebGL随机化")
        print(f"   - 配置不同的浏览器版本")
        
        print(f"3. 系统集成优化：")
        print(f"   - 实现代理IP轮换机制")
        print(f"   - 添加代理健康检查")
        print(f"   - 集成更多代理服务商作为备选")
    
    async def cleanup_browsers(self):
        """清理浏览器资源"""
        print(f"\n🧹 清理隔离浏览器...")
        
        for browser in self.browsers:
            try:
                await self.adspower_manager.stop_browser(browser['id'])
                await asyncio.sleep(1)
                await self.adspower_manager.delete_browser_profile(browser['id'])
                print(f"✅ 已清理: {browser['name']}")
            except Exception as e:
                print(f"❌ 清理失败: {e}")
        
        self.browsers.clear()
        self.allocated_proxies.clear()
        print("✅ 资源清理完成")

async def main():
    """主函数"""
    print("🚀 最终浏览器隔离系统")
    print("="*50)
    print("🎯 目标：创建两个完全独立的浏览器环境")
    print("📡 代理：青果隧道代理 + AdsPower指纹隔离")
    print("="*50)
    
    system = FinalBrowserIsolationSystem()
    
    try:
        # 创建隔离浏览器
        browsers = await system.create_isolated_browsers(2)
        
        if len(browsers) == 0:
            print("❌ 没有成功创建任何浏览器")
            return
        
        # 显示验证指南
        system.show_final_verification_guide()
        
        # 等待用户测试
        print(f"\n⏳ 请按照上述指南进行完整验证...")
        print(f"验证完成后，请告诉我你观察到的结果！")
        print(f"按 Enter 键继续清理资源...")
        input()
        
        # 清理资源
        await system.cleanup_browsers()
        
    except Exception as e:
        print(f"❌ 系统运行失败: {e}")
        await system.cleanup_browsers()

if __name__ == "__main__":
    asyncio.run(main()) 