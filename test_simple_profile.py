#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的AdsPower Profile测试脚本
用于验证最基本的profile创建和启动功能
"""

import requests
import json
import time

def test_basic_adspower_operations():
    """测试基本的AdsPower操作"""
    base_url = "http://local.adspower.net:50325"
    
    print("=== AdsPower 基本功能测试 ===")
    
    # 1. 测试状态
    print("\n1. 测试AdsPower状态...")
    response = requests.get(f"{base_url}/status")
    print(f"状态响应: {response.json()}")
    
    # 2. 创建一个最简单的profile
    print("\n2. 创建最简单的profile...")
    
    create_data = {
        "name": f"test_profile_{int(time.time())}",
        "group_id": "0",
        "domain_name": "https://www.baidu.com",
        "user_proxy_config": {
            "proxy_soft": "no_proxy"
        },
        "fingerprint_config": {
            "automatic_timezone": "1",
            "language": ["en-US", "en"],
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
    }
    
    print(f"创建数据: {json.dumps(create_data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(f"{base_url}/api/v1/user/create", json=create_data)
    print(f"创建响应 ({response.status_code}): {response.json()}")
    
    if response.status_code == 200 and response.json().get("code") == 0:
        profile_id = response.json()["data"]["id"]
        print(f"✅ Profile创建成功: {profile_id}")
        
        # 3. 验证profile存在
        print("\n3. 验证profile列表...")
        response = requests.get(f"{base_url}/api/v1/user/list")
        print(f"列表响应: {response.json()}")
        
        # 4. 尝试启动浏览器（最基本的参数）
        print(f"\n4. 尝试启动浏览器: {profile_id}")
        
        start_params = {
            "user_id": profile_id,
            "open_tabs": 1,
            "ip_tab": 0
        }
        
        print(f"启动参数: {start_params}")
        
        response = requests.get(f"{base_url}/api/v1/browser/start", params=start_params)
        print(f"启动响应 ({response.status_code}): {response.json()}")
        
        if response.status_code == 200 and response.json().get("code") == 0:
            print("✅ 浏览器启动成功！")
            
            # 5. 等待一下，然后停止浏览器
            print("\n5. 停止浏览器...")
            time.sleep(2)
            
            response = requests.get(f"{base_url}/api/v1/browser/stop", params={"user_id": profile_id})
            print(f"停止响应: {response.json()}")
        else:
            print("❌ 浏览器启动失败")
        
        # 6. 删除profile
        print(f"\n6. 删除profile: {profile_id}")
        response = requests.post(f"{base_url}/api/v1/user/delete", json={"user_ids": [profile_id]})
        print(f"删除响应: {response.json()}")
        
    else:
        print("❌ Profile创建失败")

if __name__ == "__main__":
    test_basic_adspower_operations() 