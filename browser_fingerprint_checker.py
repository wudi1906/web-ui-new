#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
浏览器指纹自动检测脚本
通过Selenium连接AdsPower浏览器，自动检测指纹信息
"""

import asyncio
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from questionnaire_system import AdsPowerManager, ADSPOWER_CONFIG

class BrowserFingerprintChecker:
    """浏览器指纹检测器"""
    
    def __init__(self):
        self.manager = AdsPowerManager(ADSPOWER_CONFIG)
        self.test_profiles = []
        self.fingerprint_results = []
    
    async def create_and_start_browsers(self, count: int = 3):
        """创建并启动浏览器"""
        print(f"🚀 创建并启动 {count} 个测试浏览器...")
        
        browser_sessions = []
        
        for i in range(count):
            try:
                persona_id = 2000 + i
                persona_name = f"指纹测试{i+1}"
                
                print(f"   创建浏览器 {i+1}/{count}: {persona_name}")
                
                # 创建配置文件
                profile_config = {
                    "name": f"fingerprint_test_{persona_id}",
                    "group_id": "0",
                    "remark": f"指纹测试浏览器{i+1}",
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
                        self.test_profiles.append({"id": profile_id, "name": persona_name})
                        
                        print(f"   ✅ 浏览器启动成功: {profile_id}")
                        await asyncio.sleep(2)  # 等待浏览器完全启动
                    else:
                        print(f"   ❌ 浏览器启动失败")
                else:
                    print(f"   ❌ 配置文件创建失败: {result.get('msg', '未知错误')}")
                    
            except Exception as e:
                print(f"   ❌ 创建浏览器异常: {e}")
        
        print(f"✅ 成功启动 {len(browser_sessions)} 个浏览器")
        return browser_sessions
    
    def connect_to_browser(self, selenium_port):
        """连接到AdsPower浏览器"""
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{selenium_port}")
            
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"❌ 连接浏览器失败: {e}")
            return None
    
    def check_basic_info(self, driver):
        """检测基础浏览器信息"""
        try:
            # 执行JavaScript获取基础信息
            basic_info = driver.execute_script("""
                return {
                    userAgent: navigator.userAgent,
                    platform: navigator.platform,
                    language: navigator.language,
                    languages: navigator.languages,
                    cookieEnabled: navigator.cookieEnabled,
                    doNotTrack: navigator.doNotTrack,
                    hardwareConcurrency: navigator.hardwareConcurrency,
                    deviceMemory: navigator.deviceMemory || 'unknown',
                    screenWidth: screen.width,
                    screenHeight: screen.height,
                    screenColorDepth: screen.colorDepth,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    timezoneOffset: new Date().getTimezoneOffset()
                };
            """)
            return basic_info
        except Exception as e:
            print(f"❌ 获取基础信息失败: {e}")
            return {}
    
    def check_canvas_fingerprint(self, driver):
        """检测Canvas指纹"""
        try:
            canvas_fingerprint = driver.execute_script("""
                var canvas = document.createElement('canvas');
                var ctx = canvas.getContext('2d');
                ctx.textBaseline = 'top';
                ctx.font = '14px Arial';
                ctx.fillText('Canvas fingerprint test 🎨', 2, 2);
                ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
                ctx.fillText('Canvas fingerprint test 🎨', 4, 4);
                return canvas.toDataURL();
            """)
            return canvas_fingerprint[:100] + "..." if len(canvas_fingerprint) > 100 else canvas_fingerprint
        except Exception as e:
            print(f"❌ 获取Canvas指纹失败: {e}")
            return "error"
    
    def check_webgl_fingerprint(self, driver):
        """检测WebGL指纹"""
        try:
            webgl_info = driver.execute_script("""
                var canvas = document.createElement('canvas');
                var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (!gl) return 'WebGL not supported';
                
                return {
                    vendor: gl.getParameter(gl.VENDOR),
                    renderer: gl.getParameter(gl.RENDERER),
                    version: gl.getParameter(gl.VERSION),
                    shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION)
                };
            """)
            return webgl_info
        except Exception as e:
            print(f"❌ 获取WebGL指纹失败: {e}")
            return {}
    
    def check_ip_address(self, driver):
        """检测IP地址"""
        try:
            # 访问IP检测网站
            driver.get("https://httpbin.org/ip")
            
            # 等待页面加载
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "pre"))
            )
            
            # 获取IP信息
            ip_text = driver.find_element(By.TAG_NAME, "pre").text
            ip_data = json.loads(ip_text)
            return ip_data.get("origin", "unknown")
            
        except Exception as e:
            print(f"❌ 获取IP地址失败: {e}")
            return "error"
    
    async def check_all_fingerprints(self, browser_sessions):
        """检测所有浏览器的指纹"""
        print("🔍 开始检测浏览器指纹...")
        
        for i, session in enumerate(browser_sessions, 1):
            try:
                profile_name = session['profile_name']
                selenium_port = session['selenium_port']
                
                print(f"\n   检测浏览器 {i}: {profile_name}")
                print(f"   Selenium端口: {selenium_port}")
                
                # 连接到浏览器
                driver = self.connect_to_browser(selenium_port)
                if not driver:
                    continue
                
                # 检测各种指纹
                print("     - 检测基础信息...")
                basic_info = self.check_basic_info(driver)
                
                print("     - 检测Canvas指纹...")
                canvas_fingerprint = self.check_canvas_fingerprint(driver)
                
                print("     - 检测WebGL指纹...")
                webgl_fingerprint = self.check_webgl_fingerprint(driver)
                
                print("     - 检测IP地址...")
                ip_address = self.check_ip_address(driver)
                
                # 汇总结果
                fingerprint_result = {
                    "browser_name": profile_name,
                    "profile_id": session['profile_id'],
                    "ip_address": ip_address,
                    "user_agent": basic_info.get('userAgent', 'unknown'),
                    "platform": basic_info.get('platform', 'unknown'),
                    "language": basic_info.get('language', 'unknown'),
                    "screen_resolution": f"{basic_info.get('screenWidth', 0)}x{basic_info.get('screenHeight', 0)}",
                    "hardware_concurrency": basic_info.get('hardwareConcurrency', 'unknown'),
                    "device_memory": basic_info.get('deviceMemory', 'unknown'),
                    "timezone": basic_info.get('timezone', 'unknown'),
                    "canvas_fingerprint": canvas_fingerprint,
                    "webgl_vendor": webgl_fingerprint.get('vendor', 'unknown') if isinstance(webgl_fingerprint, dict) else str(webgl_fingerprint),
                    "webgl_renderer": webgl_fingerprint.get('renderer', 'unknown') if isinstance(webgl_fingerprint, dict) else 'unknown'
                }
                
                self.fingerprint_results.append(fingerprint_result)
                print(f"     ✅ 指纹检测完成")
                
                # 关闭浏览器连接
                driver.quit()
                
            except Exception as e:
                print(f"     ❌ 指纹检测失败: {e}")
        
        return self.fingerprint_results
    
    def analyze_fingerprint_diversity(self):
        """分析指纹多样性"""
        print("\n" + "="*80)
        print("📊 指纹多样性分析报告")
        print("="*80)
        
        if not self.fingerprint_results:
            print("❌ 没有指纹数据可分析")
            return
        
        # 分析各项指纹的唯一性
        fields_to_check = [
            ('ip_address', 'IP地址'),
            ('user_agent', 'User-Agent'),
            ('platform', '平台信息'),
            ('screen_resolution', '屏幕分辨率'),
            ('hardware_concurrency', 'CPU核心数'),
            ('device_memory', '设备内存'),
            ('timezone', '时区'),
            ('canvas_fingerprint', 'Canvas指纹'),
            ('webgl_vendor', 'WebGL厂商'),
            ('webgl_renderer', 'WebGL渲染器')
        ]
        
        print(f"\n🔍 检测到 {len(self.fingerprint_results)} 个浏览器的指纹信息：")
        
        # 显示详细信息
        for i, result in enumerate(self.fingerprint_results, 1):
            print(f"\n【浏览器 {i}: {result['browser_name']}】")
            print(f"  IP地址: {result['ip_address']}")
            print(f"  User-Agent: {result['user_agent'][:80]}...")
            print(f"  平台: {result['platform']}")
            print(f"  分辨率: {result['screen_resolution']}")
            print(f"  CPU核心: {result['hardware_concurrency']}")
            print(f"  设备内存: {result['device_memory']}")
            print(f"  时区: {result['timezone']}")
            print(f"  Canvas指纹: {result['canvas_fingerprint'][:50]}...")
            print(f"  WebGL厂商: {result['webgl_vendor']}")
            print(f"  WebGL渲染器: {result['webgl_renderer']}")
        
        # 分析唯一性
        print(f"\n📈 唯一性分析：")
        for field, field_name in fields_to_check:
            values = [result[field] for result in self.fingerprint_results]
            unique_values = set(values)
            uniqueness_rate = len(unique_values) / len(values) * 100
            
            status = "✅" if uniqueness_rate == 100 else "⚠️" if uniqueness_rate >= 50 else "❌"
            print(f"  {status} {field_name}: {len(unique_values)}/{len(values)} 唯一 ({uniqueness_rate:.1f}%)")
        
        # 总体评估
        unique_ips = len(set(result['ip_address'] for result in self.fingerprint_results))
        unique_uas = len(set(result['user_agent'] for result in self.fingerprint_results))
        unique_canvas = len(set(result['canvas_fingerprint'] for result in self.fingerprint_results))
        
        total_browsers = len(self.fingerprint_results)
        
        print(f"\n🎯 总体评估：")
        if unique_ips == total_browsers and unique_uas == total_browsers and unique_canvas == total_browsers:
            print("  ✅ 优秀：所有关键指纹都完全不同，隔离效果很好")
        elif unique_canvas == total_browsers and unique_uas >= total_browsers * 0.8:
            print("  ✅ 良好：大部分指纹不同，隔离效果较好")
        elif unique_canvas >= total_browsers * 0.5:
            print("  ⚠️ 一般：部分指纹相同，需要优化配置")
        else:
            print("  ❌ 差：大量指纹相同，隔离失败，需要重新配置")
        
        print(f"\n💡 建议：")
        if unique_ips < total_browsers:
            print("  - 配置不同的代理IP以获得不同的外部IP地址")
        if unique_uas < total_browsers:
            print("  - 检查User-Agent随机化配置")
        if unique_canvas < total_browsers:
            print("  - 确保Canvas指纹噪声功能正常工作")
    
    async def cleanup_resources(self):
        """清理测试资源"""
        print("\n🧹 清理测试资源...")
        
        for profile in self.test_profiles:
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
    print("🚀 浏览器指纹自动检测")
    print("="*50)
    
    checker = BrowserFingerprintChecker()
    
    try:
        # 1. 创建并启动浏览器
        browser_sessions = await checker.create_and_start_browsers(3)
        
        if not browser_sessions:
            print("❌ 没有成功启动浏览器")
            return
        
        # 2. 检测指纹
        await checker.check_all_fingerprints(browser_sessions)
        
        # 3. 分析结果
        checker.analyze_fingerprint_diversity()
        
        # 4. 等待用户查看结果
        print(f"\n⏳ 请查看分析结果，按 Enter 键继续清理资源...")
        input()
        
        # 5. 清理资源
        await checker.cleanup_resources()
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被中断，开始清理资源...")
        await checker.cleanup_resources()
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        await checker.cleanup_resources()

if __name__ == "__main__":
    asyncio.run(main()) 