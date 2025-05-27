#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AdsPower快速测试脚本
用于快速验证AdsPower基本功能和API连接
"""

import requests
import json
import time
import asyncio

# AdsPower配置
ADSPOWER_BASE_URL = "http://localhost:50325"
ADSPOWER_API_KEY = "cd606f2e6e4558c9c9f2980e7017b8e9"

def test_adspower_api():
    """测试AdsPower API连接"""
    print("🔍 测试AdsPower API连接...")
    
    try:
        # 测试API连接
        url = f"{ADSPOWER_BASE_URL}/api/v1/user/list"
        params = {"page": 1, "page_size": 1, "api_key": ADSPOWER_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("code") == 0:
            print("✅ AdsPower API连接成功")
            print(f"   响应消息: {result.get('msg', 'OK')}")
            return True
        else:
            print(f"❌ API返回错误: {result.get('msg', '未知错误')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：无法连接到AdsPower")
        print("   请确保：")
        print("   1. AdsPower客户端正在运行")
        print("   2. 本地API服务已启用")
        print("   3. 端口50325未被占用")
        return False
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def create_test_profile():
    """创建一个测试浏览器配置文件"""
    print("🚀 创建测试浏览器配置文件...")
    
    try:
        url = f"{ADSPOWER_BASE_URL}/api/v1/user/create"
        
        # 正确的配置文件格式
        profile_config = {
            "name": f"quick_test_{int(time.time())}",
            "group_id": "0",
            "user_proxy_config": {
                "proxy_soft": "no_proxy",
                "proxy_type": "noproxy"
            },
            "api_key": ADSPOWER_API_KEY
        }
        
        response = requests.post(url, json=profile_config, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("code") == 0:
            profile_id = result["data"]["id"]
            print(f"✅ 配置文件创建成功")
            print(f"   配置文件ID: {profile_id}")
            return profile_id
        else:
            print(f"❌ 配置文件创建失败: {result.get('msg', '未知错误')}")
            return None
            
    except Exception as e:
        print(f"❌ 创建配置文件异常: {e}")
        return None

def start_browser(profile_id):
    """启动浏览器"""
    print(f"🌐 启动浏览器 (ID: {profile_id})...")
    
    try:
        url = f"{ADSPOWER_BASE_URL}/api/v1/browser/start"
        params = {"user_id": profile_id, "api_key": ADSPOWER_API_KEY}
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("code") == 0:
            browser_info = result["data"]
            selenium_port = browser_info.get('ws', {}).get('selenium')
            debug_port = browser_info.get('debug_port')
            
            print("✅ 浏览器启动成功")
            print(f"   Selenium端口: {selenium_port}")
            print(f"   调试端口: {debug_port}")
            
            return browser_info
        else:
            print(f"❌ 浏览器启动失败: {result.get('msg', '未知错误')}")
            return None
            
    except Exception as e:
        print(f"❌ 启动浏览器异常: {e}")
        return None

def stop_browser(profile_id):
    """停止浏览器"""
    print(f"⏹️ 停止浏览器 (ID: {profile_id})...")
    
    try:
        url = f"{ADSPOWER_BASE_URL}/api/v1/browser/stop"
        params = {"user_id": profile_id, "api_key": ADSPOWER_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("code") == 0:
            print("✅ 浏览器停止成功")
            return True
        else:
            print(f"⚠️ 浏览器停止失败: {result.get('msg', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 停止浏览器异常: {e}")
        return False

def delete_profile(profile_id):
    """删除配置文件"""
    print(f"🗑️ 删除配置文件 (ID: {profile_id})...")
    
    try:
        url = f"{ADSPOWER_BASE_URL}/api/v1/user/delete"
        data = {"user_ids": [profile_id], "api_key": ADSPOWER_API_KEY}
        
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("code") == 0:
            print("✅ 配置文件删除成功")
            return True
        else:
            print(f"⚠️ 配置文件删除失败: {result.get('msg', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 删除配置文件异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 AdsPower快速功能测试")
    print("=" * 40)
    
    # 1. 测试API连接
    if not test_adspower_api():
        print("\n❌ API连接测试失败，请检查AdsPower设置")
        return
    
    profile_id = None
    
    try:
        # 2. 创建测试配置文件
        profile_id = create_test_profile()
        if not profile_id:
            print("\n❌ 配置文件创建失败")
            return
        
        # 3. 启动浏览器
        browser_info = start_browser(profile_id)
        if not browser_info:
            print("\n❌ 浏览器启动失败")
            return
        
        # 4. 等待用户查看
        print(f"\n🎉 测试成功！")
        print(f"现在你可以：")
        print(f"1. 在AdsPower客户端中看到新创建的配置文件")
        print(f"2. 浏览器应该已经自动启动")
        print(f"3. 可以在浏览器中访问测试网站验证指纹")
        
        print(f"\n⏳ 请查看浏览器，测试完成后按 Enter 键清理资源...")
        input()
        
        # 5. 停止浏览器
        stop_browser(profile_id)
        
        # 6. 删除配置文件
        delete_profile(profile_id)
        
        print(f"\n✅ 快速测试完成！")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 测试被中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
    finally:
        # 清理资源
        if profile_id:
            print(f"\n🧹 清理测试资源...")
            stop_browser(profile_id)
            delete_profile(profile_id)

if __name__ == "__main__":
    main() 