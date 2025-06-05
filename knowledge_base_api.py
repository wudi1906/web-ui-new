#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识库API接口
为index页面提供知识库内容显示功能
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
import pymysql.cursors
import json
from datetime import datetime
from typing import Dict, List, Optional

# 数据库配置
DB_CONFIG = {
    "host": "192.168.50.137",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "wenjuan",
    "charset": "utf8mb4"
}

app = Flask(__name__)
CORS(app, origins=['*'])  # 允许所有来源的跨域请求

class KnowledgeBaseAPI:
    """知识库API类"""
    
    def __init__(self):
        self.db_config = DB_CONFIG
    
    def get_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**self.db_config)
    
    def get_knowledge_summary(self) -> Dict:
        """获取知识库概览"""
        try:
            connection = self.get_connection()
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
                
                # 获取指导规则 - 修改查询逻辑
                cursor.execute("""
                SELECT question_content, answer_choice, experience_description, created_at
                FROM questionnaire_knowledge 
                WHERE persona_role = 'guidance' OR experience_description IS NOT NULL
                ORDER BY created_at DESC 
                LIMIT 5
                """)
                guidance_rules = list(cursor.fetchall())
                
                # 如果没有指导规则，生成基于成功经验的规则
                if not guidance_rules:
                    cursor.execute("""
                    SELECT question_content, answer_choice, 
                           COUNT(*) as frequency,
                           '基于成功经验生成的指导规则' as experience_description
                    FROM questionnaire_knowledge 
                    WHERE success = 1 AND persona_role = 'scout'
                    GROUP BY question_content, answer_choice
                    HAVING frequency >= 2
                    ORDER BY frequency DESC
                    LIMIT 5
                    """)
                    guidance_rules = list(cursor.fetchall())
                
                return {
                    "summary": summary,
                    "recent_records": recent_records,
                    "guidance_rules": guidance_rules
                }
                
        except Exception as e:
            print(f"获取知识库概览失败: {e}")
            return {
                "summary": {
                    "total_records": 0,
                    "total_sessions": 0,
                    "total_questionnaires": 0,
                    "successful_records": 0,
                    "total_personas": 0
                },
                "recent_records": [],
                "guidance_rules": []
            }
        finally:
            if 'connection' in locals():
                connection.close()
    
    def get_session_knowledge(self, session_id: str) -> Dict:
        """获取特定会话的知识库内容"""
        try:
            connection = self.get_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 获取会话基本信息
                cursor.execute("""
                SELECT session_id, questionnaire_url, 
                       COUNT(*) as total_records,
                       COUNT(DISTINCT persona_name) as persona_count,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_records
                FROM questionnaire_knowledge 
                WHERE session_id = %s
                GROUP BY session_id, questionnaire_url
                """, (session_id,))
                session_info = cursor.fetchone()
                
                # 获取敢死队经验
                cursor.execute("""
                SELECT persona_name, question_content, answer_choice, success, 
                       experience_description, created_at
                FROM questionnaire_knowledge 
                WHERE session_id = %s AND persona_role = 'scout'
                ORDER BY created_at
                """, (session_id,))
                scout_experiences = list(cursor.fetchall())
                
                # 获取指导规则
                cursor.execute("""
                SELECT question_content, answer_choice, experience_description, created_at
                FROM questionnaire_knowledge 
                WHERE session_id = %s AND persona_role = 'guidance'
                ORDER BY created_at
                """, (session_id,))
                guidance_rules = list(cursor.fetchall())
                
                return {
                    "session_info": session_info,
                    "scout_experiences": scout_experiences,
                    "guidance_rules": guidance_rules
                }
                
        except Exception as e:
            print(f"获取会话知识库失败: {e}")
            return {
                "session_info": {},
                "scout_experiences": [],
                "guidance_rules": []
            }
        finally:
            if 'connection' in locals():
                connection.close()
    
    def get_questionnaire_knowledge(self, questionnaire_url: str) -> Dict:
        """获取特定问卷的知识库内容"""
        try:
            connection = self.get_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 获取问卷统计信息
                cursor.execute("""
                SELECT questionnaire_url,
                       COUNT(DISTINCT session_id) as session_count,
                       COUNT(*) as total_records,
                       COUNT(DISTINCT persona_name) as persona_count,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_records,
                       AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
                FROM questionnaire_knowledge 
                WHERE questionnaire_url = %s
                GROUP BY questionnaire_url
                """, (questionnaire_url,))
                questionnaire_info = cursor.fetchone()
                
                # 获取成功经验模式
                cursor.execute("""
                SELECT question_content, answer_choice, 
                       COUNT(*) as frequency,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
                FROM questionnaire_knowledge 
                WHERE questionnaire_url = %s AND persona_role = 'scout'
                GROUP BY question_content, answer_choice
                HAVING success_count > 0
                ORDER BY frequency DESC, success_count DESC
                LIMIT 10
                """, (questionnaire_url,))
                success_patterns = list(cursor.fetchall())
                
                # 获取最新指导规则
                cursor.execute("""
                SELECT question_content, answer_choice, experience_description, created_at
                FROM questionnaire_knowledge 
                WHERE questionnaire_url = %s AND persona_role = 'guidance'
                ORDER BY created_at DESC
                LIMIT 5
                """, (questionnaire_url,))
                latest_guidance = list(cursor.fetchall())
                
                return {
                    "questionnaire_info": questionnaire_info,
                    "success_patterns": success_patterns,
                    "latest_guidance": latest_guidance
                }
                
        except Exception as e:
            print(f"获取问卷知识库失败: {e}")
            return {
                "questionnaire_info": {},
                "success_patterns": [],
                "latest_guidance": []
            }
        finally:
            if 'connection' in locals():
                connection.close()
    
    def get_persona_performance(self) -> List[Dict]:
        """获取数字人表现统计"""
        try:
            connection = self.get_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                SELECT persona_name,
                       COUNT(*) as total_attempts,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_attempts,
                       AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                       COUNT(DISTINCT questionnaire_url) as questionnaire_count,
                       MAX(created_at) as last_activity
                FROM questionnaire_knowledge 
                WHERE persona_role = 'scout'
                GROUP BY persona_name
                ORDER BY success_rate DESC, total_attempts DESC
                """)
                return list(cursor.fetchall())
                
        except Exception as e:
            print(f"获取数字人表现统计失败: {e}")
            return []
        finally:
            if 'connection' in locals():
                connection.close()

# 创建API实例
kb_api = KnowledgeBaseAPI()

@app.route('/api/knowledge/summary', methods=['GET'])
def get_knowledge_summary():
    """获取知识库概览"""
    try:
        data = kb_api.get_knowledge_summary()
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/knowledge/session/<session_id>', methods=['GET'])
def get_session_knowledge(session_id):
    """获取特定会话的知识库内容"""
    try:
        data = kb_api.get_session_knowledge(session_id)
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/knowledge/questionnaire', methods=['GET'])
def get_questionnaire_knowledge():
    """获取特定问卷的知识库内容"""
    questionnaire_url = request.args.get('url')
    if not questionnaire_url:
        return jsonify({
            "success": False,
            "error": "缺少问卷URL参数"
        }), 400
    
    try:
        data = kb_api.get_questionnaire_knowledge(questionnaire_url)
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/knowledge/personas', methods=['GET'])
def get_persona_performance():
    """获取数字人表现统计"""
    try:
        data = kb_api.get_persona_performance()
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/knowledge/recent', methods=['GET'])
def get_recent_activities():
    """获取最近的知识库活动"""
    try:
        connection = kb_api.get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
            SELECT session_id, questionnaire_url, persona_name, persona_role,
                   question_content, answer_choice, success, experience_description,
                   created_at
            FROM questionnaire_knowledge 
            ORDER BY created_at DESC 
            LIMIT 20
            """)
            recent_activities = list(cursor.fetchall())
            
            return jsonify({
                "success": True,
                "data": recent_activities
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        if 'connection' in locals():
            connection.close()

@app.route('/api/save_experience', methods=['POST'])
def save_experience():
    """保存经验到知识库"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['session_id', 'questionnaire_url', 'persona_name', 'persona_role', 
                          'question_content', 'answer_choice', 'success']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"缺少必要字段: {field}"
                }), 400
        
        # 连接数据库保存经验
        kb_api = KnowledgeBaseAPI()
        connection = kb_api.get_connection()
        
        with connection.cursor() as cursor:
            # 插入经验记录
            cursor.execute("""
            INSERT INTO questionnaire_knowledge 
            (session_id, questionnaire_url, persona_name, persona_role, 
             question_content, answer_choice, success, experience_description, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['session_id'],
                data['questionnaire_url'],
                data['persona_name'],
                data['persona_role'],
                data['question_content'],
                data['answer_choice'],
                data['success'],
                data.get('experience_description', ''),
                datetime.now()
            ))
            
            connection.commit()
            
        return jsonify({
            "success": True,
            "message": "经验保存成功"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    print("🚀 启动知识库API服务")
    print("📋 可用接口:")
    print("  GET /api/knowledge/summary - 知识库概览")
    print("  GET /api/knowledge/session/<session_id> - 会话知识库")
    print("  GET /api/knowledge/questionnaire?url=<url> - 问卷知识库")
    print("  GET /api/knowledge/personas - 数字人表现统计")
    print("  GET /api/knowledge/recent - 最近活动")
    
    app.run(host='0.0.0.0', port=5003, debug=True) 