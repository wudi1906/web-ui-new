#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷自动填写系统 - Web管理界面
提供可视化的任务管理、进度监控和结果查看功能
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dataclasses import asdict

# 导入核心系统模块
from questionnaire_system import QuestionnaireManager, DatabaseManager, DB_CONFIG
from phase2_scout_automation import ScoutAutomationSystem
from phase3_knowledge_analysis import Phase3KnowledgeAnalysisSystem
from phase4_mass_automation import Phase4MassAutomationSystem

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'questionnaire_system_secret_key_2024'

# 全局任务管理器
class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.active_tasks: Dict[str, Dict] = {}
        self.task_history: List[Dict] = []
        self.questionnaire_manager = QuestionnaireManager()
        self.scout_system = ScoutAutomationSystem()
        self.phase3_system = Phase3KnowledgeAnalysisSystem()
        self.phase4_system = Phase4MassAutomationSystem()
        self.db_manager = DatabaseManager(DB_CONFIG)
    
    def create_task(self, questionnaire_url: str, scout_count: int, target_count: int) -> str:
        """创建新任务"""
        task_id = f"web_task_{int(time.time())}"
        
        task_info = {
            "task_id": task_id,
            "questionnaire_url": questionnaire_url,
            "scout_count": scout_count,
            "target_count": target_count,
            "status": "created",
            "phase": "准备中",
            "created_at": datetime.now().isoformat(),
            "scout_assignments": [],
            "target_assignments": [],
            "progress": {
                "phase1_complete": False,
                "phase2_complete": False,
                "phase3_complete": False,
                "phase4_complete": False,
                "current_phase": 1,
                "total_phases": 4
            },
            "results": {
                "scout_results": [],
                "target_results": [],
                "success_count": 0,
                "failure_count": 0,
                "total_answers": 0
            },
            "error_message": None
        }
        
        self.active_tasks[task_id] = task_info
        logger.info(f"✅ 创建任务: {task_id}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        return self.active_tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: str, phase: str = None, error: str = None):
        """更新任务状态"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = status
            if phase:
                self.active_tasks[task_id]["phase"] = phase
            if error:
                self.active_tasks[task_id]["error_message"] = error
            self.active_tasks[task_id]["updated_at"] = datetime.now().isoformat()
    
    def update_task_progress(self, task_id: str, phase: int, complete: bool = False):
        """更新任务进度"""
        if task_id in self.active_tasks:
            progress = self.active_tasks[task_id]["progress"]
            progress["current_phase"] = phase
            if complete:
                if phase == 1:
                    progress["phase1_complete"] = True
                elif phase == 2:
                    progress["phase2_complete"] = True
                elif phase == 3:
                    progress["phase3_complete"] = True
                elif phase == 4:
                    progress["phase4_complete"] = True
    
    def add_scout_assignment(self, task_id: str, assignment: Dict):
        """添加敢死队分配"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["scout_assignments"].append(assignment)
    
    def add_target_assignment(self, task_id: str, assignment: Dict):
        """添加目标团队分配"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["target_assignments"].append(assignment)
    
    def update_results(self, task_id: str, results: Dict):
        """更新任务结果"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["results"].update(results)
    
    def complete_task(self, task_id: str, final_results: Dict):
        """完成任务"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task["status"] = "completed"
            task["phase"] = "已完成"
            task["completed_at"] = datetime.now().isoformat()
            task["final_results"] = final_results
            
            # 移动到历史记录
            self.task_history.append(task.copy())
            
            # 从活跃任务中删除
            del self.active_tasks[task_id]
            
            logger.info(f"✅ 任务完成: {task_id}")

# 全局任务管理器实例
task_manager = TaskManager()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/create_task', methods=['POST'])
def create_task():
    """创建新任务"""
    try:
        data = request.get_json()
        questionnaire_url = data.get('questionnaire_url', '').strip()
        scout_count = int(data.get('scout_count', 2))
        target_count = int(data.get('target_count', 10))
        
        # 验证输入
        if not questionnaire_url:
            return jsonify({"success": False, "error": "问卷URL不能为空"})
        
        if not questionnaire_url.startswith(('http://', 'https://')):
            return jsonify({"success": False, "error": "请输入有效的URL地址"})
        
        if scout_count < 1 or scout_count > 10:
            return jsonify({"success": False, "error": "敢死队人数应在1-10之间"})
        
        if target_count < 1 or target_count > 50:
            return jsonify({"success": False, "error": "大部队人数应在1-50之间"})
        
        # 创建任务
        task_id = task_manager.create_task(questionnaire_url, scout_count, target_count)
        
        # 启动后台任务执行
        thread = threading.Thread(target=execute_task_async, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": "任务创建成功，正在后台执行"
        })
        
    except Exception as e:
        logger.error(f"❌ 创建任务失败: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/task_status/<task_id>')
def task_status(task_id: str):
    """获取任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({"success": False, "error": "任务不存在"})
    
    return jsonify({"success": True, "task": task})

@app.route('/task_monitor/<task_id>')
def task_monitor(task_id: str):
    """任务监控页面"""
    task = task_manager.get_task(task_id)
    if not task:
        return redirect(url_for('index'))
    
    return render_template('task_monitor.html', task=task)

@app.route('/refresh_task/<task_id>')
def refresh_task(task_id: str):
    """刷新任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({"success": False, "error": "任务不存在"})
    
    # 这里可以添加额外的状态刷新逻辑
    # 比如从数据库重新加载最新状态
    
    return jsonify({"success": True, "task": task})

@app.route('/active_tasks')
def active_tasks():
    """获取所有活跃任务"""
    return jsonify({
        "success": True,
        "tasks": list(task_manager.active_tasks.values())
    })

@app.route('/task_history')
def task_history():
    """获取任务历史"""
    return jsonify({
        "success": True,
        "tasks": task_manager.task_history
    })

def execute_task_async(task_id: str):
    """异步执行任务"""
    try:
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 执行任务
        loop.run_until_complete(execute_full_task(task_id))
        
    except Exception as e:
        logger.error(f"❌ 任务执行异常: {e}")
        task_manager.update_task_status(task_id, "failed", "执行失败", str(e))
    finally:
        loop.close()

async def execute_full_task(task_id: str):
    """执行完整任务流程"""
    try:
        task = task_manager.get_task(task_id)
        if not task:
            return
        
        questionnaire_url = task["questionnaire_url"]
        scout_count = task["scout_count"]
        target_count = task["target_count"]
        
        logger.info(f"🚀 开始执行任务: {task_id}")
        
        # 第一阶段：基础设施准备
        task_manager.update_task_status(task_id, "running", "第一阶段：基础设施准备")
        task_manager.update_task_progress(task_id, 1)
        
        # 创建问卷任务
        questionnaire_task = await task_manager.questionnaire_manager.create_questionnaire_task(
            url=questionnaire_url,
            scout_count=scout_count,
            target_count=target_count
        )
        
        session_id = questionnaire_task.session_id
        task_manager.update_task_progress(task_id, 1, complete=True)
        
        # 第二阶段：敢死队试探
        task_manager.update_task_status(task_id, "running", "第二阶段：敢死队试探")
        task_manager.update_task_progress(task_id, 2)
        
        # 启动敢死队任务
        scout_task_id = await task_manager.scout_system.start_scout_mission(
            questionnaire_url=questionnaire_url,
            scout_count=scout_count
        )
        
        if scout_task_id:
            # 更新敢死队分配信息
            for persona_id, session_info in task_manager.scout_system.scout_sessions.items():
                assignment = session_info["assignment"]
                task_manager.add_scout_assignment(task_id, {
                    "persona_id": assignment.persona_id,
                    "persona_name": assignment.persona_name,
                    "status": "准备就绪",
                    "browser_profile": session_info.get("browser", {}).get("name", "未知")
                })
            
            # 执行敢死队答题
            scout_results = await task_manager.scout_system.execute_scout_answering(scout_task_id)
            
            # 更新敢死队结果
            if scout_results:
                for scout_result in scout_results.get("scout_results", []):
                    # 更新分配状态
                    for assignment in task["scout_assignments"]:
                        if assignment["persona_id"] == scout_result.get("persona_id"):
                            assignment["status"] = "成功" if scout_result.get("success") else "失败"
                            assignment["answers_count"] = len(scout_result.get("answers", []))
                            assignment["error_message"] = scout_result.get("error_message", "")
                
                task_manager.update_results(task_id, {
                    "scout_success_count": scout_results.get("success_count", 0),
                    "scout_failure_count": scout_results.get("failure_count", 0),
                    "scout_experiences": len(scout_results.get("experiences", []))
                })
        
        task_manager.update_task_progress(task_id, 2, complete=True)
        
        # 第三阶段：知识库分析
        task_manager.update_task_status(task_id, "running", "第三阶段：知识库分析")
        task_manager.update_task_progress(task_id, 3)
        
        analysis_result = await task_manager.phase3_system.analyze_and_select_target_team(
            session_id=session_id,
            questionnaire_url=questionnaire_url,
            target_count=target_count
        )
        
        if analysis_result.get("success"):
            target_matches = analysis_result.get("target_matches", [])
            
            # 更新目标团队分配信息
            for match in target_matches:
                task_manager.add_target_assignment(task_id, {
                    "persona_id": match.persona_id,
                    "persona_name": match.persona_name,
                    "match_score": round(match.match_score, 2),
                    "match_reasons": match.match_reasons,
                    "predicted_success_rate": round(match.predicted_success_rate, 2),
                    "status": "已分配"
                })
        
        task_manager.update_task_progress(task_id, 3, complete=True)
        
        # 第四阶段：大规模自动化
        task_manager.update_task_status(task_id, "running", "第四阶段：大规模自动化")
        task_manager.update_task_progress(task_id, 4)
        
        final_result = await task_manager.phase4_system.execute_full_automation_pipeline(
            questionnaire_url=questionnaire_url,
            session_id=session_id,
            target_count=target_count,
            max_workers=min(5, target_count)
        )
        
        if final_result.get("success"):
            automation_result = final_result.get("automation_result", {})
            
            # 更新最终结果
            task_manager.update_results(task_id, {
                "total_tasks": automation_result.get("total_tasks", 0),
                "successful_tasks": automation_result.get("successful_tasks", 0),
                "failed_tasks": automation_result.get("failed_tasks", 0),
                "success_rate": automation_result.get("success_rate", 0),
                "total_answers": automation_result.get("total_answers", 0)
            })
            
            # 更新目标团队状态
            results = automation_result.get("results", [])
            for result in results:
                for assignment in task["target_assignments"]:
                    if assignment["persona_id"] == result.persona_id:
                        assignment["status"] = "成功" if result.success else "失败"
                        assignment["answers_count"] = result.answers_count
                        assignment["error_message"] = result.error_message
        
        task_manager.update_task_progress(task_id, 4, complete=True)
        
        # 完成任务
        task_manager.complete_task(task_id, final_result)
        
        logger.info(f"✅ 任务执行完成: {task_id}")
        
    except Exception as e:
        logger.error(f"❌ 任务执行失败: {e}")
        task_manager.update_task_status(task_id, "failed", "执行失败", str(e))

if __name__ == '__main__':
    # 创建模板目录
    import os
    os.makedirs('templates', exist_ok=True)
    
    print("🌐 启动智能问卷自动填写系统Web界面")
    print("📋 访问地址: http://localhost:5000")
    print("🔧 功能: 任务创建、进度监控、结果查看")
    
    app.run(host='0.0.0.0', port=5000, debug=True) 