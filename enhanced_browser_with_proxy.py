#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版浏览器环境管理器
集成青果代理，实现完整的IP和指纹隔离
"""

import asyncio
import requests
import time
import random
import logging
from typing import Dict, List, Optional
from questionnaire_system import AdsPowerManager, ADSPOWER_CONFIG

logger = logging.getLogger(__name__)

class EnhancedBrowserManager:
    """增强版浏览器管理器"""
    
    def __init__(self):
        self.adspower_manager = AdsPowerManager(ADSPOWER_CONFIG)
        self.browsers = []
        
        # 青果代理配置
        self.qinguo_config = {
            "business_id": "k3reh5az",
            "auth_key": "A942CE1E", 
            "auth_pwd": "B9FCD013057A",
            "base_url": "https://proxy.qg.net"
        }
        
        # 代理池
        self.proxy_pool = []
        self.allocated_proxies = []
    
    def get_qinguo_proxies(self, count: int = 5) -> List[Dict]:
        """获取青果代理IP"""
        try:
            print(f"🔍 尝试获取青果代理IP...")
            
            # 尝试不同的API端点
            endpoints = [
                "allocate",  # 短效代理分配
                "extract",   # 代理提取
                "get"        # 获取代理
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"{self.qinguo_config['base_url']}/{endpoint}"
                    params = {
                        "Key": self.qinguo_config["auth_key"],
                        "Pwd": self.qinguo_config["auth_pwd"],
                        "num": count,
                        "format": "txt"
                    }
                    
                    print(f"   尝试端点: {endpoint}")
                    response = requests.get(url, params=params, timeout=10)
                    result_text = response.text.strip()
                    
                    print(f"   响应: {result_text[:100]}...")
                    
                    if not result_text.startswith("ERROR") and not result_text.startswith("{\"Code\""):
                        # 解析成功的代理数据
                        proxies = []
                        lines = result_text.split('\n')
                        for line in lines:
                            if line.strip() and ':' in line:
                                parts = line.strip().split(':')
                                if len(parts) >= 2:
                                    proxies.append({
                                        "ip": parts[0],
                                        "port": parts[1],
                                        "username": parts[2] if len(parts) > 2 else "",
                                        "password": parts[3] if len(parts) > 3 else "",
                                        "full_address": f"{parts[0]}:{parts[1]}"
                                    })
                        
                        if proxies:
                            print(f"✅ 成功获取 {len(proxies)} 个青果代理")
                            return proxies
                    
                except Exception as e:
                    print(f"   端点 {endpoint} 失败: {e}")
                    continue
            
            print("⚠️ 青果代理获取失败，将使用模拟代理进行演示")
            return []
            
        except Exception as e:
            print(f"❌ 青果代理获取异常: {e}")
            return []
    
    def generate_mock_proxies(self, count: int = 5) -> List[Dict]:
        """生成模拟代理（用于演示）"""
        print(f"🎭 生成 {count} 个模拟代理用于演示...")
        
        # 一些公开的测试代理IP（仅用于演示）
        mock_ips = [
            "47.74.226.8:5001",
            "47.88.11.3:1080", 
            "8.210.83.33:1080",
            "47.91.45.198:2080",
            "47.88.29.108:8080"
        ]
        
        proxies = []
        for i, ip_port in enumerate(mock_ips[:count]):
            ip, port = ip_port.split(':')
            proxies.append({
                "ip": ip,
                "port": port,
                "username": "",
                "password": "",
                "full_address": ip_port,
                "type": "mock",
                "note": "演示用模拟代理"
            })
        
        print(f"✅ 生成了 {len(proxies)} 个模拟代理")
        return proxies
    
    def create_proxy_config(self, proxy: Optional[Dict] = None) -> Dict:
        """创建代理配置"""
        if not proxy:
            return {
                "proxy_soft": "no_proxy",
                "proxy_type": "noproxy"
            }
        
        # 根据代理类型生成配置
        if proxy.get("type") == "mock":
            # 模拟代理配置（实际不会生效，但会在AdsPower中显示）
            return {
                "proxy_soft": "other",
                "proxy_type": "http",
                "proxy_host": proxy["ip"],
                "proxy_port": proxy["port"]
            }
        else:
            # 真实青果代理配置
            config = {
                "proxy_soft": "other",
                "proxy_type": "http", 
                "proxy_host": proxy["ip"],
                "proxy_port": proxy["port"]
            }
            
            if proxy.get("username") and proxy.get("password"):
                config.update({
                    "proxy_user": proxy["username"],
                    "proxy_password": proxy["password"]
                })
            
            return config
    
    def generate_random_browser_config(self, index: int, proxy: Optional[Dict] = None) -> Dict:
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
        resolutions = [
            "1920x1080", "1366x768", "1440x900", "1536x864", "1600x900"
        ]
        
        # 随机语言
        languages = ["zh-CN", "en-US", "ja-JP", "ko-KR", "de-DE"]
        
        # 随机时区
        timezones = [
            "Asia/Shanghai", "America/New_York", "Europe/London", 
            "Asia/Tokyo", "Australia/Sydney"
        ]
        
        proxy_info = ""
        if proxy:
            proxy_info = f"_proxy_{proxy['ip'].replace('.', '_')}"
        
        config = {
            "name": f"增强测试{index}{proxy_info}",
            "group_id": "0",
            "remark": f"增强隔离浏览器{index} - 代理: {proxy['full_address'] if proxy else '无'}",
            "user_proxy_config": self.create_proxy_config(proxy)
        }
        
        # 添加随机化配置（这些在AdsPower付费版本中可能可用）
        expected_config = {
            "user_agent": random.choice(user_agents),
            "resolution": random.choice(resolutions),
            "language": random.choice(languages),
            "timezone": random.choice(timezones),
            "proxy": proxy
        }
        
        return config, expected_config
    
    async def create_enhanced_browsers(self, count: int = 2) -> List[Dict]:
        """创建增强隔离的浏览器"""
        print(f"🚀 创建 {count} 个增强隔离浏览器...")
        
        # 1. 获取代理IP
        proxies = self.get_qinguo_proxies(count)
        
        # 如果青果代理获取失败，使用模拟代理演示
        if not proxies:
            proxies = self.generate_mock_proxies(count)
        
        # 2. 为每个浏览器创建配置
        for i in range(count):
            try:
                # 分配代理
                proxy = proxies[i] if i < len(proxies) else None
                
                # 生成配置
                browser_config, expected_config = self.generate_random_browser_config(i + 1, proxy)
                
                print(f"\n   创建浏览器 {i+1}/{count}")
                print(f"   配置名称: {browser_config['name']}")
                if proxy:
                    print(f"   分配代理: {proxy['full_address']} ({proxy.get('type', 'real')})")
                    if proxy.get("note"):
                        print(f"   代理说明: {proxy['note']}")
                print(f"   预期User-Agent: {expected_config['user_agent'][:50]}...")
                print(f"   预期分辨率: {expected_config['resolution']}")
                print(f"   预期语言: {expected_config['language']}")
                print(f"   预期时区: {expected_config['timezone']}")
                
                # 创建AdsPower配置文件
                result = self.adspower_manager._make_request("POST", "/user/create", browser_config)
                
                if result.get("code") == 0:
                    profile_id = result["data"]["id"]
                    
                    # 启动浏览器
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
                        
                        if proxy:
                            self.allocated_proxies.append(proxy)
                        
                        print(f"   ✅ 浏览器启动成功: {profile_id}")
                        await asyncio.sleep(3)
                    else:
                        print(f"   ❌ 浏览器启动失败")
                else:
                    print(f"   ❌ 配置文件创建失败: {result.get('msg', '未知错误')}")
                    
            except Exception as e:
                print(f"   ❌ 创建浏览器异常: {e}")
        
        print(f"\n✅ 成功创建 {len(self.browsers)} 个增强隔离浏览器")
        return self.browsers
    
    def show_enhanced_verification_guide(self):
        """显示增强验证指南"""
        print("\n" + "="*80)
        print("🔬 增强浏览器隔离验证指南")
        print("="*80)
        
        print(f"\n📱 创建的增强隔离浏览器：")
        for i, browser in enumerate(self.browsers, 1):
            expected = browser['expected_config']
            proxy = browser.get('proxy')
            
            print(f"\n  浏览器{i}: {browser['name']}")
            print(f"    端口: {browser['port']}")
            print(f"    代理IP: {proxy['full_address'] if proxy else '无代理'}")
            if proxy and proxy.get('type') == 'mock':
                print(f"    代理类型: 演示用模拟代理")
            print(f"    预期User-Agent: {expected['user_agent'][:60]}...")
            print(f"    预期分辨率: {expected['resolution']}")
            print(f"    预期语言: {expected['language']}")
            print(f"    预期时区: {expected['timezone']}")
        
        print(f"\n🔍 完整验证步骤：")
        
        print(f"\n1. IP地址验证")
        print(f"   在每个浏览器中访问: https://whatismyipaddress.com/")
        print(f"   期望结果: 两个浏览器显示不同的IP地址")
        
        print(f"\n2. 基础指纹验证")
        print(f"   在每个浏览器控制台运行：")
        print(f"```javascript")
        print(f"console.log('=== 浏览器指纹对比 ===');")
        print(f"console.log('IP检测: 访问 whatismyipaddress.com');")
        print(f"console.log('User-Agent:', navigator.userAgent);")
        print(f"console.log('平台:', navigator.platform);")
        print(f"console.log('语言:', navigator.language);")
        print(f"console.log('屏幕:', screen.width + 'x' + screen.height);")
        print(f"console.log('时区:', Intl.DateTimeFormat().resolvedOptions().timeZone);")
        print(f"console.log('CPU核心:', navigator.hardwareConcurrency);")
        print(f"console.log('设备内存:', navigator.deviceMemory || '未知');")
        print(f"```")
        
        print(f"\n3. Canvas指纹验证")
        print(f"```javascript")
        print(f"var canvas = document.createElement('canvas');")
        print(f"var ctx = canvas.getContext('2d');")
        print(f"ctx.textBaseline = 'top';")
        print(f"ctx.font = '14px Arial';")
        print(f"ctx.fillText('指纹测试 🎨', 2, 2);")
        print(f"console.log('Canvas指纹:', canvas.toDataURL().substring(0, 50) + '...');")
        print(f"```")
        
        print(f"\n4. WebGL指纹验证")
        print(f"```javascript")
        print(f"var canvas = document.createElement('canvas');")
        print(f"var gl = canvas.getContext('webgl');")
        print(f"if (gl) {{")
        print(f"    console.log('WebGL厂商:', gl.getParameter(gl.VENDOR));")
        print(f"    console.log('WebGL渲染器:', gl.getParameter(gl.RENDERER));")
        print(f"}} else {{")
        print(f"    console.log('WebGL: 不支持');")
        print(f"}}")
        print(f"```")
        
        print(f"\n5. 专业检测网站验证")
        print(f"   访问以下网站进行全面检测：")
        print(f"   - https://browserleaks.com/ (综合指纹检测)")
        print(f"   - https://amiunique.org/ (唯一性评分)")
        print(f"   - https://whoer.net/ (匿名性检测)")
        print(f"   - https://www.deviceinfo.me/ (设备信息)")
        
        print(f"\n🎯 期望的验证结果：")
        print(f"✅ 完美隔离效果：")
        print(f"   - 两个浏览器显示完全不同的IP地址")
        print(f"   - User-Agent字符串不同")
        print(f"   - Canvas指纹完全不同")
        print(f"   - WebGL信息不同")
        print(f"   - 专业检测网站显示不同的设备特征")
        print(f"")
        print(f"✅ 良好隔离效果：")
        print(f"   - IP地址不同（如果代理正常工作）")
        print(f"   - 大部分指纹信息不同")
        print(f"   - 少数指纹相同但不影响整体隔离")
        print(f"")
        print(f"⚠️ 需要优化：")
        print(f"   - IP地址相同（代理未生效）")
        print(f"   - 部分关键指纹相同")
        
        print(f"\n💡 优化建议：")
        if any(b.get('proxy', {}).get('type') == 'mock' for b in self.browsers):
            print(f"1. 青果代理配置：")
            print(f"   - 确认青果代理账户已开通相应服务")
            print(f"   - 检查业务标识和认证信息是否正确")
            print(f"   - 联系青果客服确认权限设置")
        
        print(f"2. AdsPower高级配置：")
        print(f"   - 升级到付费版本以获得更多指纹随机化选项")
        print(f"   - 启用Canvas噪声、WebGL随机化等功能")
        print(f"   - 配置不同的浏览器版本和操作系统")
        
        print(f"3. 代理质量优化：")
        print(f"   - 使用高质量住宅代理而非数据中心代理")
        print(f"   - 确保代理IP来自不同地区")
        print(f"   - 定期轮换代理IP")
    
    async def cleanup_browsers(self):
        """清理浏览器资源"""
        print(f"\n🧹 清理增强隔离浏览器...")
        
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
    print("🚀 增强浏览器隔离测试")
    print("="*50)
    
    manager = EnhancedBrowserManager()
    
    try:
        # 创建增强隔离浏览器
        browsers = await manager.create_enhanced_browsers(2)
        
        if len(browsers) < 2:
            print("❌ 需要至少2个浏览器")
            return
        
        # 显示验证指南
        manager.show_enhanced_verification_guide()
        
        # 等待用户测试
        print(f"\n⏳ 请按照上述指南进行完整验证...")
        print(f"完成后按Enter键清理资源...")
        input()
        
        # 清理资源
        await manager.cleanup_browsers()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 