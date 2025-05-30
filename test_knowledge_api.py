#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试知识库API
"""

import requests
import json

def test_knowledge_api():
    """测试知识库API"""
    print("🧪 测试知识库API")
    print("=" * 40)
    
    try:
        # 测试知识库概览API
        print("📊 测试知识库概览API...")
        response = requests.get('http://localhost:5003/api/knowledge/summary', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API响应成功")
            print(f"📋 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get('success'):
                summary = data.get('data', {}).get('summary', {})
                print(f"\n📈 知识库统计:")
                print(f"  总记录数: {summary.get('total_records', 0)}")
                print(f"  成功记录: {summary.get('successful_records', 0)}")
                print(f"  数字人数: {summary.get('total_personas', 0)}")
                print(f"  问卷数量: {summary.get('total_questionnaires', 0)}")
                
                recent_records = data.get('data', {}).get('recent_records', [])
                print(f"\n📝 最近记录数: {len(recent_records)}")
                
                guidance_rules = data.get('data', {}).get('guidance_rules', [])
                print(f"🎯 指导规则数: {len(guidance_rules)}")
                
            else:
                print("⚠️ API返回失败状态")
        else:
            print(f"❌ API响应失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到知识库API服务")
        print("请确保knowledge_base_api.py正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_knowledge_api() 