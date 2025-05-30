#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AdsPower连接测试脚本
验证AdsPower API连接和浏览器管理功能
"""

import requests
import json
import time
import asyncio
from datetime import datetime

# AdsPower配置（用户提供的正确配置）
ADSPOWER_CONFIG = {
    "base_url": "http://local.adspower.net:50325",
    "api_key": "cd606f2e6e4558c9c9f2980e7017b8e9",
    "timeout": 30
}

class AdsPowerTester:
    """AdsPower连接测试器"""
    
    def __init__(self, config):
        self.config = config
        self.base_url = config["base_url"]
        self.api_key = config["api_key"]
        self.timeout = config.get("timeout", 30)
    
    def _make_request(self, method: str, endpoint: str, data=None):
        """发送API请求"""
        url = f"{self.base_url}/api/v1{endpoint}"  # 恢复/api/v1前缀
        
        if data is None:
            data = {}
        
        # AdsPower要求在请求参数中包含API Key
        request_data = data.copy()
        request_data["serial_number"] = self.api_key
        
        print(f"🔗 发送请求: {method} {url}")
        print(f"📦 请求参数: {request_data}")
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=request_data, timeout=self.timeout)
            else:
                response = requests.post(url, json=request_data, timeout=self.timeout)
            
            print(f"📡 响应状态: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            print(f"📋 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            raise
        except Exception as e:
            print(f"❌ 请求处理失败: {e}")
            raise
    
    def test_api_status(self):
        """测试API状态"""
        print("\n" + "="*50)
        print("🧪 测试1: API状态检查")
        print("="*50)
        
        try:
            # 注意：/status端点不需要/api/v1前缀
            result = self._make_request_simple("GET", "/status")
            
            if result.get("code") == 0:
                print("✅ AdsPower API连接成功!")
                print(f"   状态信息: {result.get('msg', '正常')}")
                return True
            else:
                print(f"❌ API状态异常: {result}")
                return False
                
        except Exception as e:
            print(f"❌ API状态检查失败: {e}")
            return False
    
    def _make_request_simple(self, method: str, endpoint: str, data=None):
        """发送简单API请求（用于状态检查）"""
        url = f"{self.base_url}{endpoint}"  # 直接使用端点
        
        if data is None:
            data = {}
        
        # AdsPower要求在请求参数中包含API Key
        request_data = data.copy()
        request_data["serial_number"] = self.api_key
        
        print(f"🔗 发送请求: {method} {url}")
        print(f"📦 请求参数: {request_data}")
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=request_data, timeout=self.timeout)
            else:
                response = requests.post(url, json=request_data, timeout=self.timeout)
            
            print(f"📡 响应状态: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            print(f"📋 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            raise
        except Exception as e:
            print(f"❌ 请求处理失败: {e}")
            raise
    
    def test_user_list(self):
        """测试获取用户列表"""
        print("\n" + "="*50)
        print("🧪 测试2: 获取浏览器配置文件列表")
        print("="*50)
        
        try:
            result = self._make_request("GET", "/user/list", {
                "page": 1,
                "page_size": 10
            })
            
            if result.get("code") == 0:
                profiles = result.get("data", {}).get("list", [])
                print(f"✅ 成功获取浏览器配置文件列表!")
                print(f"   配置文件数量: {len(profiles)}")
                
                for i, profile in enumerate(profiles[:3], 1):  # 只显示前3个
                    print(f"   配置文件{i}: {profile.get('name', '未知')} (ID: {profile.get('user_id', '未知')})")
                
                return True, profiles
            else:
                print(f"❌ 获取配置文件列表失败: {result}")
                return False, []
                
        except Exception as e:
            print(f"❌ 获取配置文件列表异常: {e}")
            return False, []
    
    def test_create_profile(self):
        """测试创建浏览器配置文件"""
        print("\n" + "="*50)
        print("🧪 测试3: 创建测试浏览器配置文件")
        print("="*50)
        
        test_profile_name = f"test_profile_{int(time.time())}"
        
        try:
            profile_config = {
                "name": test_profile_name,
                "group_id": "0",
                "remark": "AdsPower连接测试用配置文件",
                "user_proxy_config": {
                    "proxy_soft": "no_proxy",
                    "proxy_type": "noproxy"
                }
            }
            
            result = self._make_request("POST", "/user/create", profile_config)
            
            if result.get("code") == 0:
                profile_id = result["data"]["id"]
                print(f"✅ 成功创建测试配置文件!")
                print(f"   配置文件名: {test_profile_name}")
                print(f"   配置文件ID: {profile_id}")
                return True, profile_id
            else:
                print(f"❌ 创建配置文件失败: {result}")
                return False, None
                
        except Exception as e:
            print(f"❌ 创建配置文件异常: {e}")
            return False, None
    
    def test_start_browser(self, profile_id):
        """测试启动浏览器"""
        print("\n" + "="*50)
        print("🧪 测试4: 启动浏览器实例")
        print("="*50)
        
        try:
            result = self._make_request("GET", "/browser/start", {"user_id": profile_id})
            
            if result.get("code") == 0:
                browser_data = result["data"]
                
                # 提取调试端口信息
                debug_port = None
                ws_info = browser_data.get("ws", {})
                
                if ws_info.get("selenium"):
                    debug_port = ws_info["selenium"]
                elif ws_info.get("puppeteer"):
                    debug_port = ws_info["puppeteer"]
                elif browser_data.get("debug_port"):
                    debug_port = browser_data["debug_port"]
                
                print(f"✅ 成功启动浏览器!")
                print(f"   配置文件ID: {profile_id}")
                print(f"   调试端口: {debug_port}")
                print(f"   WebSocket信息: {ws_info}")
                
                return True, debug_port, browser_data
            else:
                print(f"❌ 启动浏览器失败: {result}")
                return False, None, None
                
        except Exception as e:
            print(f"❌ 启动浏览器异常: {e}")
            return False, None, None
    
    def test_stop_browser(self, profile_id):
        """测试停止浏览器"""
        print("\n" + "="*50)
        print("🧪 测试5: 停止浏览器实例")
        print("="*50)
        
        try:
            result = self._make_request("GET", "/browser/stop", {"user_id": profile_id})
            
            if result.get("code") == 0:
                print(f"✅ 成功停止浏览器!")
                print(f"   配置文件ID: {profile_id}")
                return True
            else:
                print(f"❌ 停止浏览器失败: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 停止浏览器异常: {e}")
            return False
    
    def test_delete_profile(self, profile_id):
        """测试删除配置文件"""
        print("\n" + "="*50)
        print("🧪 测试6: 删除测试配置文件")
        print("="*50)
        
        try:
            result = self._make_request("POST", "/user/delete", {"user_ids": [profile_id]})
            
            if result.get("code") == 0:
                print(f"✅ 成功删除配置文件!")
                print(f"   配置文件ID: {profile_id}")
                return True
            else:
                print(f"❌ 删除配置文件失败: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 删除配置文件异常: {e}")
            return False
    
    def run_complete_test(self):
        """运行完整的连接测试"""
        print("🚀 AdsPower连接完整测试")
        print("="*80)
        print(f"🔧 配置信息:")
        print(f"   API地址: {self.base_url}")
        print(f"   API密钥: {self.api_key[:10]}...{self.api_key[-10:]}")
        print(f"   超时时间: {self.timeout}秒")
        
        test_results = []
        profile_id = None
        
        # 测试1: API状态
        result1 = self.test_api_status()
        test_results.append(("API状态检查", result1))
        
        if not result1:
            print("\n❌ API连接失败，无法继续后续测试")
            return self._print_summary(test_results)
        
        # 测试2: 获取配置文件列表
        result2, profiles = self.test_user_list()
        test_results.append(("获取配置文件列表", result2))
        
        # 测试3: 创建配置文件
        result3, profile_id = self.test_create_profile()
        test_results.append(("创建配置文件", result3))
        
        if not result3 or not profile_id:
            print("\n❌ 创建配置文件失败，无法继续浏览器测试")
            return self._print_summary(test_results)
        
        # 测试4: 启动浏览器
        result4, debug_port, browser_data = self.test_start_browser(profile_id)
        test_results.append(("启动浏览器", result4))
        
        if result4:
            # 等待一段时间让浏览器完全启动
            print("⏳ 等待浏览器完全启动...")
            time.sleep(5)
            
            # 测试5: 停止浏览器
            result5 = self.test_stop_browser(profile_id)
            test_results.append(("停止浏览器", result5))
        else:
            test_results.append(("停止浏览器", False))
        
        # 测试6: 删除配置文件
        result6 = self.test_delete_profile(profile_id)
        test_results.append(("删除配置文件", result6))
        
        return self._print_summary(test_results)
    
    def _print_summary(self, test_results):
        """打印测试总结"""
        print("\n" + "="*80)
        print("📊 测试结果总结")
        print("="*80)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
            if result:
                passed += 1
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"\n📈 总体统计:")
        print(f"   测试项目: {total}")
        print(f"   通过项目: {passed}")
        print(f"   成功率: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 所有测试通过! AdsPower连接配置正确")
            print("💡 建议: 可以开始集成到主系统中")
        elif success_rate >= 80:
            print("\n⚠️ 部分测试通过，可能存在小问题")
            print("💡 建议: 检查失败的测试项，优化配置")
        else:
            print("\n❌ 多项测试失败，需要检查配置")
            print("💡 建议: 确认AdsPower是否正常运行，检查API密钥")
        
        return success_rate == 100

def main():
    """主函数"""
    print("🔧 AdsPower连接测试工具")
    print("="*50)
    print("📋 将测试以下功能:")
    print("   1. API连接状态")
    print("   2. 获取配置文件列表")
    print("   3. 创建浏览器配置文件")
    print("   4. 启动浏览器实例")
    print("   5. 停止浏览器实例")
    print("   6. 删除配置文件")
    print()
    
    # 创建测试器
    tester = AdsPowerTester(ADSPOWER_CONFIG)
    
    # 运行测试
    success = tester.run_complete_test()
    
    if success:
        print("\n🎊 测试完成! AdsPower连接正常")
    else:
        print("\n🔧 测试发现问题，请查看上述日志进行排查")

if __name__ == "__main__":
    main() 