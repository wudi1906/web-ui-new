#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
青果代理API测试工具
独立测试青果代理接口，检查返回内容和连接状态
"""

import requests
import json
from datetime import datetime

class QingguoProxyTester:
    """青果代理测试器"""
    
    def __init__(self):
        # 青果代理API配置
        self.api_url = "https://share.proxy-seller.com/api/proxy/get_proxy/51966ae4c2b78e0c30b1f40afeabf5fb/"
        
        # 青果代理认证信息
        self.proxy_config = {
            "host": "tun-szbhry.qg.net",
            "port": "17790",
            "business_id": "k3reh5az",
            "auth_key": "A942CE1E", 
            "auth_pwd": "B9FCD013057A"
        }
    
    def test_api_response(self):
        """测试青果代理API的原始返回内容"""
        print("=" * 60)
        print("🧪 青果代理API测试")
        print("=" * 60)
        print(f"📡 API地址: {self.api_url}")
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            print("🔄 正在调用青果代理API...")
            response = requests.get(self.api_url, timeout=10)
            
            print(f"📊 HTTP状态码: {response.status_code}")
            print(f"📋 响应头: {dict(response.headers)}")
            print()
            
            if response.status_code == 200:
                print("✅ API调用成功!")
                print("📄 原始响应内容:")
                print("-" * 40)
                print(response.text)
                print("-" * 40)
                print()
                
                # 尝试解析JSON
                try:
                    data = response.json()
                    print("📊 JSON解析结果:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    print()
                    
                    # 检查代理IP信息
                    if isinstance(data, dict):
                        proxy_ip_https = data.get("HTTPS", "")
                        proxy_ip_http = data.get("HTTP", "")
                        proxy_ip = proxy_ip_https or proxy_ip_http
                        
                        if proxy_ip:
                            print(f"🌐 获取到代理IP: {proxy_ip}")
                            return {"success": True, "proxy_ip": proxy_ip, "raw_data": data}
                        else:
                            print("⚠️ 未找到代理IP信息")
                            return {"success": False, "error": "未找到代理IP", "raw_data": data}
                    else:
                        print("⚠️ 返回数据格式不是字典")
                        return {"success": False, "error": "数据格式异常", "raw_data": data}
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    return {"success": False, "error": f"JSON解析失败: {e}", "raw_text": response.text}
            else:
                print(f"❌ API调用失败，HTTP状态码: {response.status_code}")
                print(f"📄 错误响应: {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}", "raw_text": response.text}
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 连接错误: {e}")
            return {"success": False, "error": f"连接错误: {e}"}
        except Exception as e:
            print(f"❌ 其他错误: {e}")
            return {"success": False, "error": f"其他错误: {e}"}
    
    def test_proxy_connection(self, proxy_ip_info):
        """测试青果代理连接（使用多种认证格式）"""
        print("\n" + "=" * 60)
        print("🔌 青果代理连接测试")
        print("=" * 60)
        
        # 多种认证格式
        auth_formats = [
            {
                "name": "格式1: business_id:auth_key",
                "user": f"{self.proxy_config['business_id']}:{self.proxy_config['auth_key']}",
                "password": self.proxy_config['auth_pwd']
            },
            {
                "name": "格式2: auth_key:auth_pwd", 
                "user": self.proxy_config['auth_key'],
                "password": self.proxy_config['auth_pwd']
            },
            {
                "name": "格式3: business_id-auth_key:auth_pwd",
                "user": f"{self.proxy_config['business_id']}-{self.proxy_config['auth_key']}",
                "password": self.proxy_config['auth_pwd']
            }
        ]
        
        for i, auth_format in enumerate(auth_formats, 1):
            print(f"\n🧪 测试 {auth_format['name']}")
            print(f"   代理地址: {self.proxy_config['host']}:{self.proxy_config['port']}")
            print(f"   用户名: {auth_format['user']}")
            print(f"   密码: {auth_format['password']}")
            
            try:
                proxy_url = f"http://{auth_format['user']}:{auth_format['password']}@{self.proxy_config['host']}:{self.proxy_config['port']}"
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url
                }
                
                print("   🔄 正在测试连接...")
                response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
                
                if response.status_code == 200:
                    ip_data = response.json()
                    actual_ip = ip_data.get("origin", "未知")
                    print(f"   ✅ 连接成功! 当前IP: {actual_ip}")
                    return {"success": True, "format": auth_format['name'], "actual_ip": actual_ip}
                else:
                    print(f"   ❌ HTTP错误: {response.status_code}")
                    
            except requests.exceptions.ProxyError as e:
                print(f"   ❌ 代理错误: {e}")
            except requests.exceptions.Timeout:
                print(f"   ❌ 连接超时")
            except Exception as e:
                print(f"   ❌ 其他错误: {e}")
        
        print("\n❌ 所有认证格式都测试失败")
        return {"success": False, "error": "所有认证格式都失败"}
    
    def run_complete_test(self):
        """运行完整测试"""
        print("🚀 开始青果代理完整测试")
        print("=" * 60)
        
        # 1. 测试API调用
        api_result = self.test_api_response()
        
        # 2. 如果API成功，测试代理连接
        if api_result.get("success") and api_result.get("proxy_ip"):
            proxy_result = self.test_proxy_connection(api_result["proxy_ip"])
            
            # 最终结果
            print("\n" + "=" * 60)
            print("📋 测试结果总结")
            print("=" * 60)
            print(f"✅ API调用: {'成功' if api_result['success'] else '失败'}")
            if api_result.get("proxy_ip"):
                print(f"🌐 获取IP: {api_result['proxy_ip']}")
            print(f"🔌 代理连接: {'成功' if proxy_result.get('success') else '失败'}")
            if proxy_result.get("actual_ip"):
                print(f"📍 实际IP: {proxy_result['actual_ip']}")
            if not proxy_result.get("success"):
                print(f"❌ 连接错误: {proxy_result.get('error', '未知')}")
            
            return {
                "api_success": api_result["success"],
                "proxy_ip": api_result.get("proxy_ip"),
                "connection_success": proxy_result.get("success"),
                "actual_ip": proxy_result.get("actual_ip"),
                "error": proxy_result.get("error") if not proxy_result.get("success") else None
            }
        else:
            print("\n" + "=" * 60)
            print("📋 测试结果总结")
            print("=" * 60)
            print("❌ API调用失败，无法进行代理连接测试")
            print(f"❌ API错误: {api_result.get('error', '未知')}")
            
            return {
                "api_success": False,
                "error": api_result.get("error", "API调用失败")
            }

def main():
    """主函数"""
    tester = QingguoProxyTester()
    result = tester.run_complete_test()
    
    print("\n" + "=" * 60)
    print("🎯 最终建议")
    print("=" * 60)
    
    if result.get("api_success") and result.get("connection_success"):
        print("✅ 青果代理完全正常，可以正常使用")
    elif result.get("api_success") and not result.get("connection_success"):
        print("⚠️ API正常但连接失败，可能需要:")
        print("   1. 将当前IP添加到青果代理白名单")
        print("   2. 检查认证信息是否正确")
        print("   3. 联系青果代理客服")
    else:
        print("❌ API调用失败，可能需要:")
        print("   1. 检查网络连接")
        print("   2. 检查API地址是否正确")
        print("   3. 检查API密钥是否有效")
    
    return result

if __name__ == "__main__":
    main() 