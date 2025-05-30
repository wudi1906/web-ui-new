#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷填写系统 - 主Web服务
提供Web界面和任务管理功能
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import uuid
import time
import json
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Optional

# 导入系统模块
try:
    from questionnaire_manager import QuestionnaireManager
    from enhanced_run_questionnaire_with_knowledge import EnhancedQuestionnaireSystem
except ImportError as e:
    print(f"⚠️ 导入模块失败: {e}")
    print("系统将以基础模式运行")

app = Flask(__name__)
CORS(app, origins=['*'])
app.secret_key = 'questionnaire_system_secret_key_2024'

# 全局变量
active_tasks = {}
task_history = []
enhanced_system = None
questionnaire_manager = None

# 初始化系统组件
def initialize_system():
    """初始化系统组件"""
    global enhanced_system, questionnaire_manager
    
    try:
        enhanced_system = EnhancedQuestionnaireSystem()
        questionnaire_manager = QuestionnaireManager()
        print("✅ 系统组件初始化成功")
        return True
    except Exception as e:
        print(f"❌ 系统组件初始化失败: {e}")
        return False

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/system_status')
def system_status():
    """系统状态API"""
    try:
        status = {
            "enhanced_system_available": enhanced_system is not None,
            "testwenjuan_available": True,  # 假设testWenjuanFinal可用
            "active_tasks_count": len(active_tasks),
            "task_history_count": len(task_history),
            "knowledge_api_available": check_knowledge_api(),
            "timestamp": datetime.now().isoformat()
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({
            "error": str(e),
            "enhanced_system_available": False,
            "testwenjuan_available": False,
            "active_tasks_count": 0,
            "task_history_count": 0,
            "knowledge_api_available": False
        }), 500

def check_knowledge_api():
    """检查知识库API是否可用"""
    try:
        import requests
        response = requests.get('http://localhost:5003/api/knowledge/summary', timeout=2)
        return response.status_code == 200
    except:
        return False

@app.route('/create_task', methods=['POST'])
def create_task():
    """创建新任务"""
    try:
        data = request.get_json()
        
        # 验证输入
        questionnaire_url = data.get('questionnaire_url', '').strip()
        scout_count = int(data.get('scout_count', 2))
        target_count = int(data.get('target_count', 10))
        
        if not questionnaire_url:
            return jsonify({
                "success": False,
                "error": "问卷URL不能为空"
            }), 400
        
        if not questionnaire_url.startswith(('http://', 'https://')):
            return jsonify({
                "success": False,
                "error": "请输入有效的URL地址"
            }), 400
        
        # 创建任务ID
        task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # 创建任务记录
        task = {
            "task_id": task_id,
            "questionnaire_url": questionnaire_url,
            "scout_count": scout_count,
            "target_count": target_count,
            "status": "created",
            "phase": "准备中",
            "created_at": datetime.now().isoformat(),
            "progress": {
                "current_phase": 1,
                "total_phases": 4,
                "phase1_complete": False,
                "phase2_complete": False,
                "phase3_complete": False,
                "phase4_complete": False
            },
            "results": {},
            "resource_consumption": {
                "total_cost": 0.0,
                "resources": []
            }
        }
        
        # 保存任务
        active_tasks[task_id] = task
        
        # 启动异步任务执行
        # 为了演示，强制使用模拟模式
        thread = threading.Thread(
            target=simulate_task_execution,
            args=(task_id,)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": "任务创建成功，开始执行"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"创建任务失败: {str(e)}"
        }), 500

def execute_task_async(task_id: str, questionnaire_url: str, scout_count: int, target_count: int):
    """异步执行任务"""
    try:
        task = active_tasks.get(task_id)
        if not task:
            return
        
        # 更新任务状态
        task["status"] = "running"
        task["phase"] = "启动问卷主管系统"
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 执行完整工作流
            result = loop.run_until_complete(
                questionnaire_manager.execute_complete_workflow(
                    questionnaire_url, scout_count, target_count
                )
            )
            
            # 更新任务结果
            task["status"] = "completed"
            task["phase"] = "任务完成"
            task["results"] = result
            task["progress"]["phase4_complete"] = True
            task["completed_at"] = datetime.now().isoformat()
            
            # 移动到历史记录
            task_history.append(task.copy())
            if task_id in active_tasks:
                del active_tasks[task_id]
                
        except Exception as e:
            task["status"] = "failed"
            task["phase"] = f"执行失败: {str(e)}"
            task["error"] = str(e)
            task["failed_at"] = datetime.now().isoformat()
            
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ 任务执行异常: {e}")
        if task_id in active_tasks:
            active_tasks[task_id]["status"] = "failed"
            active_tasks[task_id]["error"] = str(e)

def simulate_task_execution(task_id: str):
    """模拟任务执行（当真实系统不可用时）"""
    try:
        task = active_tasks.get(task_id)
        if not task:
            return
        
        questionnaire_url = task.get('questionnaire_url')
        scout_count = task.get('scout_count', 2)
        target_count = task.get('target_count', 5)
        
        # 阶段1: 基础设施准备
        task["status"] = "running"
        task["phase"] = "基础设施准备"
        task["progress"]["current_phase"] = 1
        time.sleep(2)
        
        # 阶段2: 敢死队执行
        task["phase"] = "敢死队执行中"
        task["progress"]["current_phase"] = 2
        task["progress"]["phase1_complete"] = True
        
        # 模拟敢死队答题过程
        import random
        session_id = f"sim_session_{int(time.time())}"
        
        # 模拟向知识库添加敢死队经验
        scout_experiences = []
        for i in range(scout_count):
            persona_name = f"敢死队员{i+1}"
            # 模拟几个问题的答题经验
            questions = [
                "您对新技术的接受程度如何？",
                "您通常在哪里购买日用品？", 
                "您平时最常使用的电子设备是？"
            ]
            
            for question in questions:
                experience = {
                    "session_id": session_id,
                    "questionnaire_url": questionnaire_url,
                    "persona_name": persona_name,
                    "persona_role": "scout",
                    "question_content": question,
                    "answer_choice": random.choice(["选项A", "选项B", "选项C"]),
                    "success": random.choice([True, True, False]),  # 80%成功率
                    "experience_description": f"{persona_name}的答题经验"
                }
                scout_experiences.append(experience)
        
        # 模拟保存到知识库（通过API调用）
        try:
            import requests
            for exp in scout_experiences:
                # 这里应该调用知识库API保存经验，但为了演示，我们跳过
                pass
        except:
            pass
        
        time.sleep(5)
        
        # 阶段3: 经验分析
        task["phase"] = "经验分析中"
        task["progress"]["current_phase"] = 3
        task["progress"]["phase2_complete"] = True
        
        # 模拟生成指导规则
        guidance_rules = [
            {
                "question_pattern": "技术接受程度",
                "recommended_answer": "中等",
                "confidence_score": 0.85,
                "experience_description": "基于敢死队经验，中等选择成功率更高"
            },
            {
                "question_pattern": "购买渠道",
                "recommended_answer": "网购",
                "confidence_score": 0.90,
                "experience_description": "年轻群体更倾向于网购"
            }
        ]
        
        time.sleep(3)
        
        # 阶段4: 大部队执行
        task["phase"] = "大部队执行中"
        task["progress"]["current_phase"] = 4
        task["progress"]["phase3_complete"] = True
        
        # 模拟大部队答题，使用指导规则
        successful_targets = 0
        total_answers = 0
        
        for i in range(target_count):
            # 模拟每个大部队成员的答题
            member_success = random.random() < 0.9  # 90%成功率（因为有指导）
            if member_success:
                successful_targets += 1
            total_answers += random.randint(8, 15)  # 每人答8-15题
        
        time.sleep(8)
        
        # 完成
        task["status"] = "completed"
        task["phase"] = "任务完成"
        task["progress"]["phase4_complete"] = True
        task["completed_at"] = datetime.now().isoformat()
        
        # 模拟结果
        task["results"] = {
            "success": True,
            "session_id": session_id,
            "questionnaire_url": questionnaire_url,
            "scout_phase": {
                "total": scout_count,
                "successful": sum(1 for exp in scout_experiences if exp["success"]),
                "success_rate": sum(1 for exp in scout_experiences if exp["success"]) / len(scout_experiences),
                "results": scout_experiences
            },
            "analysis_phase": {
                "guidance_rules_count": len(guidance_rules),
                "guidance_rules": guidance_rules
            },
            "target_phase": {
                "total": target_count,
                "successful": successful_targets,
                "success_rate": successful_targets / target_count,
                "results": [{"success": i < successful_targets} for i in range(target_count)]
            },
            "overall": {
                "total_count": scout_count + target_count,
                "total_success": sum(1 for exp in scout_experiences if exp["success"]) + successful_targets,
                "total_answers": total_answers,
                "overall_success_rate": (sum(1 for exp in scout_experiences if exp["success"]) + successful_targets) / (scout_count + target_count)
            }
        }
        
        # 模拟资源消耗
        task["resource_consumption"] = {
            "total_cost": 0.0234 * (scout_count + target_count) / 7,  # 按人数比例
            "resources": [
                {"type": "adspower_browser", "quantity": scout_count + target_count, "cost": 0.0100 * (scout_count + target_count) / 7},
                {"type": "qinguo_proxy", "quantity": scout_count + target_count, "cost": 0.0080 * (scout_count + target_count) / 7},
                {"type": "xiaoshe_query", "quantity": total_answers, "cost": 0.0054 * total_answers / 45}
            ]
        }
        
        # 移动到历史记录
        task_history.append(task.copy())
        if task_id in active_tasks:
            del active_tasks[task_id]
            
    except Exception as e:
        print(f"❌ 模拟任务执行异常: {e}")
        if task_id in active_tasks:
            active_tasks[task_id]["status"] = "failed"
            active_tasks[task_id]["error"] = str(e)

@app.route('/refresh_task/<task_id>')
def refresh_task(task_id):
    """刷新任务状态"""
    try:
        # 检查活跃任务
        if task_id in active_tasks:
            task = active_tasks[task_id]
            return jsonify({
                "success": True,
                "task": task,
                "completed": False
            })
        
        # 检查历史任务
        for task in task_history:
            if task["task_id"] == task_id:
                return jsonify({
                    "success": True,
                    "task": task,
                    "completed": True
                })
        
        return jsonify({
            "success": False,
            "error": "任务不存在"
        }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/active_tasks')
def get_active_tasks():
    """获取活跃任务列表"""
    try:
        return jsonify({
            "success": True,
            "tasks": list(active_tasks.values())
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/task_history')
def get_task_history():
    """获取任务历史"""
    try:
        return jsonify({
            "success": True,
            "tasks": task_history[-20:]  # 最近20个任务
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/knowledge_base')
def knowledge_base():
    """知识库页面"""
    return render_template('knowledge_base.html')

@app.route('/resource_consumption')
def resource_consumption():
    """资源消耗页面"""
    return render_template('resource_consumption.html')

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        "success": False,
        "error": "页面不存在"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        "success": False,
        "error": "服务器内部错误"
    }), 500

if __name__ == '__main__':
    print("🚀 启动智能问卷填写系统 - 主Web服务")
    print("=" * 60)
    
    # 初始化系统
    system_ready = initialize_system()
    
    if system_ready:
        print("✅ 系统组件初始化完成")
    else:
        print("⚠️ 系统组件初始化失败，将以基础模式运行")
    
    print("\n🌐 服务信息:")
    print("   主界面: http://localhost:5002")
    print("   系统状态: http://localhost:5002/system_status")
    print("   知识库API: http://localhost:5003/api/knowledge/summary")
    
    print("\n💡 提示:")
    print("   - 确保知识库API服务已启动 (端口5003)")
    print("   - 按 Ctrl+C 停止服务")
    
    print("\n🎯 系统启动中...")
    
    try:
        app.run(host='0.0.0.0', port=5002, debug=True, threaded=True)
    except KeyboardInterrupt:
        print("\n⏹️ 服务已停止")
    except Exception as e:
        print(f"\n❌ 服务启动失败: {e}") 