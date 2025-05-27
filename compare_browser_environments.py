#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
浏览器环境对比测试脚本
创建两个独立的浏览器，自动检测并对比它们的指纹信息
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

class BrowserEnvironmentComparator:
    """浏览器环境对比器"""
    
    def __init__(self):
        self.manager = AdsPowerManager(ADSPOWER_CONFIG)
        self.browser_profiles = []
        self.fingerprint_data = []
    
    async def create_test_browsers(self, count: int = 2):
        """创建测试浏览器"""
        print(f"🚀 创建 {count} 个测试浏览器...")
        
        browser_sessions = []
        
        for i in range(count):
            try:
                persona_id = 3000 + i
                persona_name = f"对比测试{i+1}"
                
                print(f"   创建浏览器 {i+1}/{count}: {persona_name}")
                
                # 创建配置文件
                profile_config = {
                    "name": f"compare_test_{persona_id}",
                    "group_id": "0",
                    "remark": f"对比测试浏览器{i+1}",
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
                        await asyncio.sleep(3)  # 等待浏览器完全启动
                    else:
                        print(f"   ❌ 浏览器启动失败")
                else:
                    print(f"   ❌ 配置文件创建失败: {result.get('msg', '未知错误')}")
                    
            except Exception as e:
                print(f"   ❌ 创建浏览器异常: {e}")
        
        print(f"✅ 成功启动 {len(browser_sessions)} 个浏览器")
        return browser_sessions
    
    def connect_to_browser(self, debug_port):
        """连接到AdsPower浏览器"""
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
            
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"❌ 连接浏览器失败: {e}")
            return None
    
    def get_comprehensive_fingerprint(self, driver, browser_name):
        """获取全面的浏览器指纹信息"""
        print(f"   🔍 检测 {browser_name} 的指纹信息...")
        
        fingerprint = {
            "browser_name": browser_name,
            "timestamp": time.time()
        }
        
        try:
            # 获取基础信息
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
                    availWidth: screen.availWidth,
                    availHeight: screen.availHeight,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    timezoneOffset: new Date().getTimezoneOffset(),
                    windowOuterWidth: window.outerWidth,
                    windowOuterHeight: window.outerHeight,
                    windowInnerWidth: window.innerWidth,
                    windowInnerHeight: window.innerHeight
                };
            """)
            fingerprint.update(basic_info)
            
            # 获取Canvas指纹
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
            fingerprint["canvas_fingerprint"] = canvas_fingerprint[:50] + "..." if len(canvas_fingerprint) > 50 else canvas_fingerprint
            
            # 获取WebGL指纹
            webgl_info = driver.execute_script("""
                var canvas = document.createElement('canvas');
                var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (!gl) return 'WebGL not supported';
                
                return {
                    vendor: gl.getParameter(gl.VENDOR),
                    renderer: gl.getParameter(gl.RENDERER),
                    version: gl.getParameter(gl.VERSION),
                    shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
                    maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
                    maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS)
                };
            """)
            fingerprint["webgl_info"] = webgl_info
            
            # 获取字体信息
            fonts_info = driver.execute_script("""
                var fonts = ['Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Verdana', 'Georgia', 'Palatino', 'Garamond', 'Bookman', 'Comic Sans MS', 'Trebuchet MS', 'Arial Black', 'Impact'];
                var available = [];
                var testString = 'mmmmmmmmmmlli';
                var testSize = '72px';
                var h = document.getElementsByTagName('body')[0];
                
                var s = document.createElement('span');
                s.style.fontSize = testSize;
                s.innerHTML = testString;
                var defaultWidth = {};
                var defaultHeight = {};
                
                for (var index in fonts) {
                    var font = fonts[index];
                    s.style.fontFamily = font;
                    h.appendChild(s);
                    defaultWidth[font] = s.offsetWidth;
                    defaultHeight[font] = s.offsetHeight;
                    h.removeChild(s);
                    available.push(font);
                }
                
                return available.slice(0, 5); // 只返回前5个字体
            """)
            fingerprint["available_fonts"] = fonts_info
            
            print(f"   ✅ {browser_name} 指纹检测完成")
            return fingerprint
            
        except Exception as e:
            print(f"   ❌ {browser_name} 指纹检测失败: {e}")
            fingerprint["error"] = str(e)
            return fingerprint
    
    def check_ip_address(self, driver, browser_name):
        """检测IP地址"""
        try:
            print(f"   🌐 检测 {browser_name} 的IP地址...")
            
            # 访问IP检测网站
            driver.get("https://httpbin.org/ip")
            
            # 等待页面加载
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "pre"))
            )
            
            # 获取IP信息
            ip_text = driver.find_element(By.TAG_NAME, "pre").text
            ip_data = json.loads(ip_text)
            ip_address = ip_data.get("origin", "unknown")
            
            print(f"   ✅ {browser_name} IP地址: {ip_address}")
            return ip_address
            
        except Exception as e:
            print(f"   ❌ {browser_name} IP检测失败: {e}")
            return "error"
    
    async def compare_browsers(self, browser_sessions):
        """对比浏览器环境"""
        print("\n🔍 开始对比浏览器环境...")
        
        for i, session in enumerate(browser_sessions, 1):
            try:
                profile_name = session['profile_name']
                debug_port = session['debug_port']
                
                print(f"\n📱 检测浏览器 {i}: {profile_name}")
                
                # 连接到浏览器
                driver = self.connect_to_browser(debug_port)
                if not driver:
                    continue
                
                # 获取指纹信息
                fingerprint = self.get_comprehensive_fingerprint(driver, profile_name)
                
                # 检测IP地址
                ip_address = self.check_ip_address(driver, profile_name)
                fingerprint["ip_address"] = ip_address
                
                self.fingerprint_data.append(fingerprint)
                
                # 关闭浏览器连接
                driver.quit()
                
            except Exception as e:
                print(f"   ❌ 检测浏览器 {i} 失败: {e}")
        
        return self.fingerprint_data
    
    def generate_comparison_report(self):
        """生成对比报告"""
        print("\n" + "="*80)
        print("📊 浏览器环境对比报告")
        print("="*80)
        
        if len(self.fingerprint_data) < 2:
            print("❌ 需要至少2个浏览器的数据才能进行对比")
            return
        
        browser1 = self.fingerprint_data[0]
        browser2 = self.fingerprint_data[1]
        
        print(f"\n🔍 对比结果：")
        print(f"浏览器1: {browser1['browser_name']}")
        print(f"浏览器2: {browser2['browser_name']}")
        
        # 对比关键指标
        comparison_fields = [
            ('ip_address', 'IP地址'),
            ('userAgent', 'User-Agent'),
            ('platform', '操作系统平台'),
            ('language', '语言设置'),
            ('screenWidth', '屏幕宽度'),
            ('screenHeight', '屏幕高度'),
            ('hardwareConcurrency', 'CPU核心数'),
            ('deviceMemory', '设备内存'),
            ('timezone', '时区'),
            ('canvas_fingerprint', 'Canvas指纹'),
        ]
        
        print(f"\n📋 详细对比：")
        differences = 0
        
        for field, field_name in comparison_fields:
            value1 = browser1.get(field, 'unknown')
            value2 = browser2.get(field, 'unknown')
            
            if field == 'userAgent':
                # User-Agent太长，只显示前50个字符
                value1_display = str(value1)[:50] + "..." if len(str(value1)) > 50 else str(value1)
                value2_display = str(value2)[:50] + "..." if len(str(value2)) > 50 else str(value2)
            elif field == 'canvas_fingerprint':
                # Canvas指纹只显示前20个字符
                value1_display = str(value1)[:20] + "..." if len(str(value1)) > 20 else str(value1)
                value2_display = str(value2)[:20] + "..." if len(str(value2)) > 20 else str(value2)
            else:
                value1_display = str(value1)
                value2_display = str(value2)
            
            if value1 != value2:
                status = "✅ 不同"
                differences += 1
            else:
                status = "❌ 相同"
            
            print(f"  {status} {field_name}:")
            print(f"    浏览器1: {value1_display}")
            print(f"    浏览器2: {value2_display}")
        
        # WebGL对比
        webgl1 = browser1.get('webgl_info', {})
        webgl2 = browser2.get('webgl_info', {})
        
        if isinstance(webgl1, dict) and isinstance(webgl2, dict):
            webgl_vendor1 = webgl1.get('vendor', 'unknown')
            webgl_vendor2 = webgl2.get('vendor', 'unknown')
            webgl_renderer1 = webgl1.get('renderer', 'unknown')
            webgl_renderer2 = webgl2.get('renderer', 'unknown')
            
            if webgl_vendor1 != webgl_vendor2:
                print(f"  ✅ 不同 WebGL厂商:")
                print(f"    浏览器1: {webgl_vendor1}")
                print(f"    浏览器2: {webgl_vendor2}")
                differences += 1
            else:
                print(f"  ❌ 相同 WebGL厂商: {webgl_vendor1}")
            
            if webgl_renderer1 != webgl_renderer2:
                print(f"  ✅ 不同 WebGL渲染器:")
                print(f"    浏览器1: {webgl_renderer1}")
                print(f"    浏览器2: {webgl_renderer2}")
                differences += 1
            else:
                print(f"  ❌ 相同 WebGL渲染器: {webgl_renderer1}")
        
        # 总体评估
        total_fields = len(comparison_fields) + 2  # 加上WebGL的两个字段
        similarity_rate = (total_fields - differences) / total_fields * 100
        
        print(f"\n🎯 总体评估：")
        print(f"相同字段: {total_fields - differences}/{total_fields}")
        print(f"不同字段: {differences}/{total_fields}")
        print(f"相似度: {similarity_rate:.1f}%")
        
        if similarity_rate < 30:
            print("✅ 优秀：浏览器环境隔离效果很好，看起来像不同的电脑")
        elif similarity_rate < 50:
            print("✅ 良好：浏览器环境有一定隔离，但还可以进一步优化")
        elif similarity_rate < 70:
            print("⚠️ 一般：浏览器环境隔离不够，需要优化配置")
        else:
            print("❌ 差：浏览器环境几乎相同，隔离失败")
        
        print(f"\n💡 建议：")
        if differences < 5:
            print("  - 启用更多的指纹随机化选项")
            print("  - 配置不同的代理IP地址")
            print("  - 调整浏览器配置文件的高级设置")
        
        return differences, total_fields
    
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
    print("🚀 浏览器环境对比测试")
    print("="*50)
    
    comparator = BrowserEnvironmentComparator()
    
    try:
        # 1. 创建并启动浏览器
        browser_sessions = await comparator.create_test_browsers(2)
        
        if len(browser_sessions) < 2:
            print("❌ 需要至少2个浏览器才能进行对比")
            return
        
        # 2. 对比浏览器环境
        await comparator.compare_browsers(browser_sessions)
        
        # 3. 生成对比报告
        differences, total = comparator.generate_comparison_report()
        
        # 4. 等待用户查看结果
        print(f"\n⏳ 请查看对比结果，按 Enter 键继续清理资源...")
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