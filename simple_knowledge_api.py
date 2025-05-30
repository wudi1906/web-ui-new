#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的知识库API
直接从数据库获取数据并返回JSON
"""

import pymysql
import pymysql.cursors
import json
from datetime import datetime

# 数据库配置
DB_CONFIG = {
    "host": "192.168.50.137",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "wenjuan",
    "charset": "utf8mb4"
}

def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def get_knowledge_summary():
    """获取知识库概览"""
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 统计总体数据
            cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT session_id) as total_sessions,
                COUNT(DISTINCT questionnaire_url) as total_questionnaires,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_records,
                COUNT(DISTINCT persona_name) as total_personas
            FROM questionnaire_knowledge
            """)
            summary = cursor.fetchone()
            
            # 获取最近的经验记录
            cursor.execute("""
            SELECT session_id, questionnaire_url, persona_name, persona_role,
                   question_content, answer_choice, success, created_at
            FROM questionnaire_knowledge 
            ORDER BY created_at DESC 
            LIMIT 10
            """)
            recent_records = list(cursor.fetchall())
            
            # 获取指导规则
            cursor.execute("""
            SELECT question_content, answer_choice, experience_description
            FROM questionnaire_knowledge 
            WHERE persona_role = 'guidance'
            ORDER BY created_at DESC 
            LIMIT 5
            """)
            guidance_rules = list(cursor.fetchall())
            
            return {
                "success": True,
                "data": {
                    "summary": summary,
                    "recent_records": recent_records,
                    "guidance_rules": guidance_rules
                }
            }
            
    except Exception as e:
        print(f"获取知识库概览失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "summary": {},
                "recent_records": [],
                "guidance_rules": []
            }
        }
    finally:
        if 'connection' in locals():
            connection.close()

def test_knowledge_data():
    """测试知识库数据获取"""
    print("🧪 测试知识库数据获取")
    print("=" * 50)
    
    result = get_knowledge_summary()
    
    if result["success"]:
        print("✅ 数据获取成功")
        
        summary = result["data"]["summary"]
        print(f"\n📊 知识库统计:")
        print(f"  总记录数: {summary.get('total_records', 0)}")
        print(f"  成功记录: {summary.get('successful_records', 0)}")
        print(f"  数字人数: {summary.get('total_personas', 0)}")
        print(f"  问卷数量: {summary.get('total_questionnaires', 0)}")
        
        recent_records = result["data"]["recent_records"]
        print(f"\n📝 最近记录数: {len(recent_records)}")
        
        if recent_records:
            print("最近的几条记录:")
            for i, record in enumerate(recent_records[:3]):
                status = "✅" if record.get('success') else "❌"
                print(f"  {i+1}. {status} {record.get('persona_name', 'Unknown')} - {record.get('question_content', 'No content')[:50]}...")
        
        guidance_rules = result["data"]["guidance_rules"]
        print(f"\n🎯 指导规则数: {len(guidance_rules)}")
        
        if guidance_rules:
            print("指导规则:")
            for i, rule in enumerate(guidance_rules):
                print(f"  {i+1}. {rule.get('question_content', 'Unknown')[:50]}... -> {rule.get('answer_choice', 'No answer')}")
        
    else:
        print(f"❌ 数据获取失败: {result.get('error', 'Unknown error')}")
    
    print(f"\n📋 完整JSON数据:")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    test_knowledge_data() 