#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版青果代理测试工具
"""

import requests
import socket
from datetime import datetime

def test_network_connectivity():
    """测试基本网络连接"""
    print("🌐 基本网络连接测试")
    print("-" * 40)
    
    test_sites = [
        "google.com",
        "baidu.com", 
        "httpbin.org",
        "share.proxy-seller.com"
    ]
    
    for site in test_sites:
        try:
            # DNS解析测试
            ip = socket.gethostbyname(site)
            print(f"✅ {site} -> {ip}")
        except socket.gaierror as e:
            print(f"❌ {site} -> DNS解析失败: {e}")
    
    print()

def test_qingguo_api_simple():
    """简单测试青果代理API"""
    print("🧪 青果代理API简单测试")
    print("-" * 40)
    
    # 可能的API地址
    api_urls = [
        "https://share.proxy-seller.com/api/proxy/get_proxy/51966ae4c2b78e0c30b1f40afeabf5fb/",
        "http://share.proxy-seller.com/api/proxy/get_proxy/51966ae4c2b78e0c30b1f40afeabf5fb/",
        "https://api.proxy-seller.com/api/proxy/get_proxy/51966ae4c2b78e0c30b1f40afeabf5fb/",
    ]
    
    for i, url in enumerate(api_urls, 1):
        print(f"\n📡 测试API地址 {i}: {url}")
        try:
            response = requests.get(url, timeout=10)
            print(f"   HTTP状态: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}...")
            
            if response.status_code == 200:
                print("   ✅ API调用成功!")
                return {"success": True, "url": url, "response": response.text}
            else:
                print(f"   ⚠️ HTTP错误: {response.status_code}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ 连接失败: {e}")
        except requests.exceptions.Timeout:
            print(f"   ❌ 请求超时")
        except Exception as e:
            print(f"   ❌ 其他错误: {e}")
    
    return {"success": False, "error": "所有API地址都失败"}

def test_direct_proxy_connection():
    """直接测试代理连接"""
    print("\n🔌 直接代理连接测试")
    print("-" * 40)
    
    proxy_config = {
        "host": "tun-szbhry.qg.net",
        "port": "17790",
        "user": "k3reh5az:A942CE1E",  # business_id:auth_key
        "password": "B9FCD013057A"
    }
    
    print(f"代理服务器: {proxy_config['host']}:{proxy_config['port']}")
    print(f"认证信息: {proxy_config['user']}:{proxy_config['password']}")
    
    try:
        proxy_url = f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['host']}:{proxy_config['port']}"
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        print("🔄 正在测试代理连接...")
        response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=15)
        
        if response.status_code == 200:
            ip_data = response.json()
            actual_ip = ip_data.get("origin", "未知")
            print(f"✅ 代理连接成功! 当前IP: {actual_ip}")
            return {"success": True, "ip": actual_ip}
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            
    except requests.exceptions.ProxyError as e:
        print(f"❌ 代理错误: {e}")
        if "407" in str(e):
            print("   💡 这通常表示需要将IP添加到代理白名单")
    except Exception as e:
        print(f"❌ 其他错误: {e}")
    
    return {"success": False}

def main():
    """主函数"""
    print("🚀 青果代理诊断工具")
    print("=" * 50)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 网络连接测试
    test_network_connectivity()
    
    # 2. API测试
    api_result = test_qingguo_api_simple()
    
    # 3. 直接代理测试
    proxy_result = test_direct_proxy_connection()
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 诊断结果总结")
    print("=" * 50)
    
    if api_result.get("success"):
        print(f"✅ API调用成功")
        print(f"📄 API返回: {api_result.get('response', '')[:100]}...")
    else:
        print(f"❌ API调用失败: {api_result.get('error', '未知')}")
    
    if proxy_result.get("success"):
        print(f"✅ 代理连接成功，IP: {proxy_result.get('ip')}")
    else:
        print(f"❌ 代理连接失败")
        print(f"💡 建议: 请将您的当前IP添加到青果代理白名单")
    
    # 获取当前公网IP
    try:
        current_ip_response = requests.get("https://httpbin.org/ip", timeout=10)
        if current_ip_response.status_code == 200:
            current_ip = current_ip_response.json().get("origin", "未知")
            print(f"🌐 您的当前公网IP: {current_ip}")
            print(f"💡 请将此IP添加到青果代理白名单: {current_ip}")
    except:
        print("⚠️ 无法获取当前公网IP")

if __name__ == "__main__":
    main() 