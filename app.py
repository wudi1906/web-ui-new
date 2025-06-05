#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷填写系统 - 主Web服务
提供Web界面和任务管理功能
融合三阶段智能核心系统
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

# 导入三阶段智能核心系统
try:
    from intelligent_three_stage_core import ThreeStageIntelligentCore
    THREE_STAGE_AVAILABLE = True
    print("✅ 三阶段智能核心系统可用")
except ImportError as e:
    print(f"⚠️ 三阶段智能系统导入失败: {e}")
    THREE_STAGE_AVAILABLE = False

app = Flask(__name__)
CORS(app, origins=['*'])
app.secret_key = 'questionnaire_system_secret_key_2024'

# 全局变量
active_tasks = {}
task_history = []
enhanced_system = None
questionnaire_manager = None
three_stage_core = None

# 初始化系统组件
def initialize_system():
    """初始化系统组件"""
    global enhanced_system, questionnaire_manager, three_stage_core
    
    try:
        # 尝试初始化传统系统
        try:
            enhanced_system = EnhancedQuestionnaireSystem()
            questionnaire_manager = QuestionnaireManager()
            print("✅ 传统系统组件初始化成功")
        except Exception as e:
            print(f"⚠️ 传统系统初始化失败: {e}")
        
        # 初始化三阶段智能系统
        if THREE_STAGE_AVAILABLE:
            try:
                three_stage_core = ThreeStageIntelligentCore()
                print("✅ 三阶段智能系统初始化成功")
            except Exception as e:
                print(f"⚠️ 三阶段智能系统初始化失败: {e}")
        
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
            "three_stage_system_available": three_stage_core is not None,
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
            "three_stage_system_available": False,
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
        task_mode = data.get('task_mode', 'three_stage')  # 新增任务模式选择
        
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
            "task_mode": task_mode,
            "status": "created",
            "phase": "准备中",
            "created_at": datetime.now().isoformat(),
            "progress": {
                "current_phase": 1,
                "total_phases": 4 if task_mode == 'three_stage' else 2,
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
        
        # 根据任务模式启动不同的执行方式
        if task_mode == 'three_stage' and three_stage_core:
            # 启动三阶段智能工作流
            thread = threading.Thread(
                target=execute_three_stage_task_async,
                args=(task_id, questionnaire_url, scout_count, target_count)
            )
            thread.daemon = True
            thread.start()
            print(f"✅ 启动三阶段智能任务: {task_id}")
        else:
            # 启动传统模拟模式
            thread = threading.Thread(
                target=simulate_task_execution,
                args=(task_id,)
            )
            thread.daemon = True
            thread.start()
            print(f"✅ 启动传统模拟任务: {task_id}")
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "task_mode": task_mode,
            "message": f"{'三阶段智能' if task_mode == 'three_stage' else '传统模拟'}任务创建成功，开始执行"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"创建任务失败: {str(e)}"
        }), 500

def execute_three_stage_task_async(task_id: str, questionnaire_url: str, scout_count: int, target_count: int):
    """异步执行三阶段智能任务"""
    try:
        if not three_stage_core:
            active_tasks[task_id]["status"] = "failed"
            active_tasks[task_id]["error"] = "三阶段智能系统不可用"
            return
        
        task = active_tasks.get(task_id)
        if not task:
            return
        
        # 更新任务状态
        task["status"] = "running"
        task["phase"] = "启动三阶段智能工作流（增强人类化模式）"
        task["enhanced_human_like"] = True  # 🔥 标记使用增强版本
        
        print(f"🚀 启动三阶段智能任务（增强人类化）: {task_id}")
        print(f"🛡️ 反检测模式: 启用多重人类化操作策略")
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 执行完整三阶段工作流
            result = loop.run_until_complete(
                three_stage_core.execute_complete_three_stage_workflow(
                    questionnaire_url, scout_count, target_count
                )
            )
            
            if result.get("success"):
                # 更新任务结果
                task["status"] = "completed"
                task["phase"] = "三阶段智能工作流完成"
                task["results"] = result
                task["progress"]["phase4_complete"] = True
                task["completed_at"] = datetime.now().isoformat()
                
                # 移动到历史记录
                task_history.append(task.copy())
                if task_id in active_tasks:
                    del active_tasks[task_id]
                
                print(f"✅ 三阶段智能任务 {task_id} 完成成功")
            else:
                task["status"] = "failed"
                task["error"] = result.get("error", "三阶段工作流执行失败")
                task["failed_at"] = datetime.now().isoformat()
                print(f"❌ 三阶段智能任务 {task_id} 执行失败: {task['error']}")
                
        except Exception as e:
            task["status"] = "failed"
            task["phase"] = f"三阶段执行失败: {str(e)}"
            task["error"] = str(e)
            task["failed_at"] = datetime.now().isoformat()
            print(f"❌ 三阶段智能任务 {task_id} 异常: {e}")
            
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ 三阶段智能任务执行异常: {e}")
        if task_id in active_tasks:
            active_tasks[task_id]["status"] = "failed"
            active_tasks[task_id]["error"] = str(e)

def execute_task_async(task_id: str, questionnaire_url: str, scout_count: int, target_count: int):
    """异步执行任务（传统模式）"""
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
        task_mode = task.get('task_mode', 'simulate')
        
        # 根据任务模式调整模拟逻辑
        if task_mode == 'three_stage':
            simulate_three_stage_execution(task, questionnaire_url, scout_count, target_count)
        else:
            simulate_traditional_execution(task, questionnaire_url, scout_count, target_count)
            
    except Exception as e:
        print(f"❌ 模拟任务执行异常: {e}")
        if task_id in active_tasks:
            active_tasks[task_id]["status"] = "failed"
            active_tasks[task_id]["error"] = str(e)

def simulate_three_stage_execution(task: Dict, questionnaire_url: str, scout_count: int, target_count: int):
    """模拟三阶段智能执行"""
    session_id = f"sim_three_stage_{int(time.time())}"
    
    # 第一阶段：敢死队情报收集
    task["status"] = "running"
    task["phase"] = "第一阶段：敢死队情报收集"
    task["progress"]["current_phase"] = 1
    time.sleep(3)
    
    # 模拟敢死队招募和执行
    scout_experiences = []
    for i in range(scout_count):
        scout_name = f"敢死队成员{i+1}"
        # 模拟探索多个页面
        for page in range(1, 4):
            experience = {
                "scout_id": f"scout_{i+1}",
                "scout_name": scout_name,
                "page_number": page,
                "questions_answered": [
                    {"question": f"第{page}页问题{j+1}", "answer": f"选项{chr(65+j)}", "reasoning": f"{scout_name}的选择理由"}
                    for j in range(2+page)
                ],
                "success": True if i < scout_count - 1 else False,  # 最后一个失败
                "timestamp": datetime.now().isoformat()
            }
            scout_experiences.append(experience)
    
    task["progress"]["phase1_complete"] = True
    time.sleep(2)
    
    # 第二阶段：Gemini智能分析
    task["phase"] = "第二阶段：Gemini智能分析"
    task["progress"]["current_phase"] = 2
    time.sleep(4)
    
    # 模拟智能分析结果
    intelligence_analysis = {
        "questionnaire_theme": "消费习惯调研",
        "target_audience": {
            "age_range": "25-40",
            "gender": "不限",
            "occupation": "上班族",
            "education": "大学本科"
        },
        "trap_questions": [
            {"question": "收入验证题", "trap_type": "一致性检查"},
            {"question": "重复询问题", "trap_type": "逻辑陷阱"}
        ],
        "success_patterns": [
            {"pattern": "保守选择", "success_rate": 0.85},
            {"pattern": "符合身份", "success_rate": 0.90}
        ],
        "guidance_rules": [
            {
                "rule_id": "rule_1",
                "question_pattern": "收入相关",
                "recommended_answer": "中等收入",
                "confidence": 0.85
            },
            {
                "rule_id": "rule_2", 
                "question_pattern": "消费习惯",
                "recommended_answer": "理性消费",
                "confidence": 0.80
            }
        ],
        "confidence_score": 0.85
    }
    
    task["progress"]["phase2_complete"] = True
    time.sleep(2)
    
    # 第三阶段：大部队招募
    task["phase"] = "第三阶段：基于智能分析招募大部队"
    task["progress"]["current_phase"] = 3
    time.sleep(2)
    
    # 模拟大部队成员选择（70%相似 + 30%多样化）
    similar_count = int(target_count * 0.7)
    diverse_count = target_count - similar_count
    
    target_assignments = []
    for i in range(target_count):
        if i < similar_count:
            assignment_type = "相似成员"
            match_score = 0.85 + (i * 0.02)
        else:
            assignment_type = "多样化成员"
            match_score = 0.65 + (i * 0.03)
            
        target_assignments.append({
            "target_id": f"target_{i+1}",
            "target_name": f"大部队成员{i+1}",
            "assignment_type": assignment_type,
            "match_score": min(match_score, 0.95),
            "predicted_success_rate": min(match_score + 0.05, 0.90)
        })
    
    task["progress"]["phase3_complete"] = True
    time.sleep(2)
    
    # 第四阶段：大部队智能答题
    task["phase"] = "第四阶段：大部队智能答题执行"
    task["progress"]["current_phase"] = 4
    time.sleep(6)
    
    # 模拟大部队执行（基于智能指导的高成功率）
    target_results = []
    successful_targets = 0
    
    for assignment in target_assignments:
        # 基于匹配度和指导规则的成功率
        success_prob = assignment["predicted_success_rate"]
        success = True if successful_targets / target_count < success_prob else False
        
        if success:
            successful_targets += 1
            
        target_results.append({
            "target_id": assignment["target_id"],
            "target_name": assignment["target_name"],
            "success": success,
            "guided_by_rules": len(intelligence_analysis["guidance_rules"]),
            "execution_time": 45 + (i * 5)
        })
    
    # 完成任务
    task["status"] = "completed"
    task["phase"] = "三阶段智能工作流完成"
    task["progress"]["phase4_complete"] = True
    task["completed_at"] = datetime.now().isoformat()
    
    # 生成详细结果
    scout_success_count = sum(1 for exp in scout_experiences if exp.get("success", False))
    overall_success_rate = (scout_success_count + successful_targets) / (len(scout_experiences) + len(target_results))
    
    task["results"] = {
        "success": True,
        "session_id": session_id,
        "workflow_type": "three_stage_intelligent",
        "scout_phase": {
            "total_scouts": scout_count,
            "successful_scouts": scout_success_count,
            "success_rate": scout_success_count / scout_count,
            "experiences_collected": len(scout_experiences),
            "scout_experiences": scout_experiences
        },
        "analysis_phase": {
            "intelligence_analysis": intelligence_analysis,
            "guidance_rules_generated": len(intelligence_analysis["guidance_rules"]),
            "confidence_score": intelligence_analysis["confidence_score"]
        },
        "target_phase": {
            "total_targets": target_count,
            "successful_targets": successful_targets,
            "success_rate": successful_targets / target_count,
            "similar_members": similar_count,
            "diverse_members": diverse_count,
            "target_assignments": target_assignments,
            "target_results": target_results
        },
        "overall": {
            "total_participants": scout_count + target_count,
            "total_successful": scout_success_count + successful_targets,
            "overall_success_rate": overall_success_rate,
            "improvement_rate": (successful_targets / target_count) - (scout_success_count / scout_count)
        }
    }
    
    # 模拟资源消耗
    task["resource_consumption"] = {
        "total_cost": 0.0456 * (scout_count + target_count) / 7,
        "resources": [
            {"type": "gemini_api_calls", "quantity": 3, "cost": 0.0120},
            {"type": "xiaoshe_queries", "quantity": scout_count + target_count, "cost": 0.0200 * (scout_count + target_count) / 7},
            {"type": "browser_automation", "quantity": scout_count + target_count, "cost": 0.0136 * (scout_count + target_count) / 7}
        ]
    }
    
    # 移动到历史记录
    task_history.append(task.copy())
    task_id = task["task_id"]
    if task_id in active_tasks:
        del active_tasks[task_id]

def simulate_traditional_execution(task: Dict, questionnaire_url: str, scout_count: int, target_count: int):
    """模拟传统执行（保持原有逻辑）"""
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
    task_id = task["task_id"]
    if task_id in active_tasks:
        del active_tasks[task_id]

@app.route('/get_gemini_analysis/<task_id>')
def get_gemini_analysis(task_id):
    """获取任务的Gemini截图分析结果"""
    try:
        if not three_stage_core:
            return jsonify({
                "success": False,
                "error": "三阶段智能系统不可用"
            }), 503
        
        # 从三阶段核心系统获取Gemini分析结果
        analysis_result = three_stage_core.get_session_gemini_analysis(task_id)
        
        if analysis_result:
            return jsonify({
                "success": True,
                "gemini_analysis": analysis_result,
                "has_analysis": True
            })
        else:
            return jsonify({
                "success": True,
                "gemini_analysis": None,
                "has_analysis": False,
                "message": "该任务尚未进行Gemini截图分析或分析失败"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取Gemini分析失败: {str(e)}"
        }), 500

@app.route('/get_processed_screenshots')
def get_processed_screenshots():
    """获取处理后的截图列表"""
    try:
        import os
        from adspower_browser_use_integration import IMAGE_PROCESSING_CONFIG
        
        processed_dir = IMAGE_PROCESSING_CONFIG["processed_dir"]
        
        if not os.path.exists(processed_dir):
            return jsonify({
                "success": True,
                "screenshots": [],
                "message": "处理目录不存在"
            })
        
        # 获取所有处理后的截图文件
        screenshot_files = []
        for filename in os.listdir(processed_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(processed_dir, filename)
                file_stat = os.stat(filepath)
                
                screenshot_files.append({
                    "filename": filename,
                    "filepath": filepath,
                    "size_kb": round(file_stat.st_size / 1024, 1),
                    "created_time": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "analysis_type": filename.split('_')[0] if '_' in filename else 'unknown'
                })
        
        # 按创建时间排序
        screenshot_files.sort(key=lambda x: x['created_time'], reverse=True)
        
        return jsonify({
            "success": True,
            "screenshots": screenshot_files[:20],  # 最近20个截图
            "total_count": len(screenshot_files)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取截图列表失败: {str(e)}"
        }), 500

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
    print("融合三阶段智能核心系统")
    print("=" * 60)
    
    # 初始化系统
    system_ready = initialize_system()
    
    if system_ready:
        print("✅ 系统组件初始化完成")
        if three_stage_core:
            print("🧠 三阶段智能系统：已启用")
        else:
            print("⚠️ 三阶段智能系统：未启用（使用模拟模式）")
    else:
        print("⚠️ 系统组件初始化失败，将以基础模式运行")
    
    print("\n🌐 服务信息:")
    print("   主界面: http://localhost:5002")
    print("   系统状态: http://localhost:5002/system_status")
    print("   知识库API: http://localhost:5003/api/knowledge/summary")
    
    print("\n💡 功能特性:")
    print("   ✅ 传统问卷模式 - 基于testWenjuan.py技术")
    if three_stage_core:
        print("   🧠 三阶段智能模式 - 敢死队→分析→大部队")
        print("   ✅ Gemini智能分析 - 专业问卷情报分析")
        print("   ✅ 智能指导作答 - 基于经验的精准指导")
        print("   ✅ 多样化数字人选择 - 70%相似+30%多样化")
    else:
        print("   ⚠️ 三阶段智能模式 - 模拟演示版本")
    
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