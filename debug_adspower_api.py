#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AdsPower API调试脚本
用于查看API响应和现有配置
"""

import requests
import json

ADSPOWER_BASE_URL = "http://localhost:50325"
ADSPOWER_API_KEY = "cd606f2e6e4558c9c9f2980e7017b8e9"

def debug_user_list():
    """查看现有用户列表"""
    print("🔍 查看现有用户列表...")
    
    try:
        url = f"{ADSPOWER_BASE_URL}/api/v1/user/list"
        params = {"page": 1, "page_size": 10, "api_key": ADSPOWER_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"响应状态: {result.get('code')}")
        print(f"响应消息: {result.get('msg')}")
        
        if result.get("code") == 0:
            data = result.get("data", {})
            users = data.get("list", [])
            print(f"用户总数: {data.get('total', 0)}")
            
            if users:
                print("\n现有用户配置示例:")
                for i, user in enumerate(users[:2]):  # 只显示前2个
                    print(f"\n用户 {i+1}:")
                    print(f"  ID: {user.get('user_id')}")
                    print(f"  名称: {user.get('name')}")
                    print(f"  平台: {user.get('platform')}")
                    print(f"  分组ID: {user.get('group_id')}")
                    print(f"  状态: {user.get('status')}")
            else:
                print("没有现有用户")
        
        return result
        
    except Exception as e:
        print(f"❌ 查看用户列表失败: {e}")
        return None

def debug_group_list():
    """查看分组列表"""
    print("\n🔍 查看分组列表...")
    
    try:
        url = f"{ADSPOWER_BASE_URL}/api/v1/group/list"
        params = {"api_key": ADSPOWER_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"响应状态: {result.get('code')}")
        print(f"响应消息: {result.get('msg')}")
        
        if result.get("code") == 0:
            groups = result.get("data", [])
            print(f"分组总数: {len(groups)}")
            
            if groups:
                print("\n可用分组:")
                for group in groups:
                    if isinstance(group, dict):
                        print(f"  ID: {group.get('group_id')}, 名称: {group.get('group_name')}")
                    else:
                        print(f"  分组数据: {group}")
            else:
                print("没有可用分组")
        
        return result
        
    except Exception as e:
        print(f"❌ 查看分组列表失败: {e}")
        return None

def test_minimal_create():
    """测试最小化配置创建"""
    print("\n🚀 测试最小化配置创建...")
    
    try:
        url = f"{ADSPOWER_BASE_URL}/api/v1/user/create"
        
        # 最小化配置
        minimal_config = {
            "name": f"minimal_test_{int(__import__('time').time())}",
            "api_key": ADSPOWER_API_KEY
        }
        
        print(f"发送配置: {json.dumps(minimal_config, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, json=minimal_config, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"响应状态: {result.get('code')}")
        print(f"响应消息: {result.get('msg')}")
        
        if result.get("code") == 0:
            profile_id = result["data"]["id"]
            print(f"✅ 创建成功，配置文件ID: {profile_id}")
            return profile_id
        else:
            print(f"❌ 创建失败: {result.get('msg')}")
            return None
            
    except Exception as e:
        print(f"❌ 测试创建失败: {e}")
        return None

def test_create_with_proxy():
    """使用代理配置测试创建"""
    print("\n🚀 测试使用代理配置创建...")
    
    try:
        url = f"{ADSPOWER_BASE_URL}/api/v1/user/create"
        
        # 包含代理配置
        config_with_proxy = {
            "name": f"proxy_test_{int(__import__('time').time())}",
            "group_id": "0",
            "user_proxy_config": {
                "proxy_soft": "no_proxy",
                "proxy_type": "noproxy"
            },
            "api_key": ADSPOWER_API_KEY
        }
        
        print(f"发送配置: {json.dumps(config_with_proxy, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, json=config_with_proxy, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"响应状态: {result.get('code')}")
        print(f"响应消息: {result.get('msg')}")
        
        if result.get("code") == 0:
            profile_id = result["data"]["id"]
            print(f"✅ 创建成功，配置文件ID: {profile_id}")
            return profile_id
        else:
            print(f"❌ 创建失败: {result.get('msg')}")
            return None
            
    except Exception as e:
        print(f"❌ 测试创建失败: {e}")
        return None

def cleanup_test_profile(profile_id):
    """清理测试配置文件"""
    if not profile_id:
        return
        
    print(f"\n🧹 清理测试配置文件: {profile_id}")
    
    try:
        url = f"{ADSPOWER_BASE_URL}/api/v1/user/delete"
        data = {"user_ids": [profile_id], "api_key": ADSPOWER_API_KEY}
        
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get("code") == 0:
            print("✅ 清理成功")
        else:
            print(f"⚠️ 清理失败: {result.get('msg')}")
            
    except Exception as e:
        print(f"❌ 清理异常: {e}")

def main():
    """主函数"""
    print("🔧 AdsPower API调试")
    print("=" * 40)
    
    # 1. 查看现有用户
    debug_user_list()
    
    # 2. 查看分组
    debug_group_list()
    
    # 3. 测试最小化创建
    profile_id1 = test_minimal_create()
    
    # 4. 测试使用代理配置创建
    profile_id2 = test_create_with_proxy()
    
    # 5. 清理测试配置文件
    cleanup_test_profile(profile_id1)
    cleanup_test_profile(profile_id2)
    
    print("\n✅ 调试完成")

if __name__ == "__main__":
    main() 