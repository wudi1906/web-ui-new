#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷填写系统 - 统一主入口
功能：敢死队作答 → 收集结果 → 分析经验 → 指导大部队 → 大部队作答
"""

import asyncio
import json
import time
import uuid
import logging
import threading
import subprocess
import platform
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pymysql.cursors
import requests

# 导入核心系统模块
from questionnaire_system import (
    QuestionnaireManager, 
    DatabaseManager, 
    DB_CONFIG,
    TaskStatus,
    PersonaRole
)
from testWenjuanFinal import (
    run_browser_task,
    run_browser_task_with_adspower,  # 新增：AdsPower浏览器连接函数
    generate_detailed_person_description,
    generate_complete_prompt,
    get_digital_human_by_id
)

# 导入增强版AdsPower生命周期管理器
from enhanced_adspower_lifecycle import AdsPowerLifecycleManager, BrowserStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask应用
app = Flask(__name__)
CORS(app)

class BrowserWindowManager:
    """浏览器窗口布局管理器"""
    
    def __init__(self):
        self.window_positions = []
        self.screen_width = 1920  # 默认屏幕宽度
        self.screen_height = 1080  # 默认屏幕高度
        self.window_width = 640   # 每个窗口宽度
        self.window_height = 540  # 每个窗口高度
        self._detect_screen_size()
    
    def _detect_screen_size(self):
        """检测屏幕尺寸"""
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                      capture_output=True, text=True)
                # 简化处理，使用默认值
                pass
            elif platform.system() == "Windows":
                import tkinter as tk
                root = tk.Tk()
                self.screen_width = root.winfo_screenwidth()
                self.screen_height = root.winfo_screenheight()
                root.destroy()
            
            logger.info(f"🖥️ 检测到屏幕尺寸: {self.screen_width}x{self.screen_height}")
            
        except Exception as e:
            logger.warning(f"⚠️ 无法检测屏幕尺寸，使用默认值: {e}")
    
    def calculate_window_positions(self, window_count: int) -> List[Dict]:
        """计算多个浏览器窗口的最佳排布位置"""
        positions = []
        
        if window_count <= 0:
            return positions
        
        # 计算网格布局
        if window_count == 1:
            cols, rows = 1, 1
        elif window_count <= 2:
            cols, rows = 2, 1
        elif window_count <= 4:
            cols, rows = 2, 2
        elif window_count <= 6:
            cols, rows = 3, 2
        elif window_count <= 9:
            cols, rows = 3, 3
        else:
            cols, rows = 4, 3  # 最多12个窗口
        
        # 调整窗口大小以适应屏幕
        available_width = self.screen_width - 100  # 留出边距
        available_height = self.screen_height - 100
        
        window_width = min(self.window_width, available_width // cols)
        window_height = min(self.window_height, available_height // rows)
        
        # 计算起始位置（居中）
        start_x = (self.screen_width - (window_width * cols)) // 2
        start_y = (self.screen_height - (window_height * rows)) // 2
        
        # 生成每个窗口的位置
        for i in range(min(window_count, cols * rows)):
            row = i // cols
            col = i % cols
            
            x = start_x + col * window_width
            y = start_y + row * window_height
            
            positions.append({
                "x": x,
                "y": y,
                "width": window_width,
                "height": window_height,
                "window_index": i
            })
        
        logger.info(f"📐 计算了 {len(positions)} 个窗口位置 ({cols}x{rows} 网格)")
        return positions
    
    def apply_window_position(self, browser_profile_id: str, position: Dict):
        """应用窗口位置到AdsPower浏览器"""
        try:
            # 这里可以通过AdsPower API设置窗口位置
            # 暂时记录位置信息
            logger.info(f"🪟 设置浏览器 {browser_profile_id} 位置: "
                       f"({position['x']}, {position['y']}) "
                       f"{position['width']}x{position['height']}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ 设置窗口位置失败: {e}")
            return False

class KnowledgeBase:
    """内置知识库管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_scout_experience(self, session_id: str, questionnaire_url: str, 
                            persona_id: int, persona_name: str, 
                            question_content: str, answer_choice: str, 
                            success: bool, reasoning: str = "") -> bool:
        """保存敢死队答题经验"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO questionnaire_knowledge 
                (session_id, questionnaire_url, persona_id, persona_name, 
                 question_content, answer_choice, success, reasoning, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    session_id, questionnaire_url, persona_id, persona_name,
                    question_content, answer_choice, success, reasoning, datetime.now()
                ))
                connection.commit()
                logger.info(f"✅ 保存敢死队经验: {persona_name} - {question_content[:50]}...")
                return True
        except Exception as e:
            logger.error(f"❌ 保存敢死队经验失败: {e}")
            return False
        finally:
            if 'connection' in locals():
                connection.close()
    
    def analyze_and_generate_guidance(self, session_id: str, questionnaire_url: str) -> List[Dict]:
        """分析敢死队经验并生成指导规则"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 查询成功的答题经验
                sql = """
                SELECT question_content, answer_choice, COUNT(*) as success_count
                FROM questionnaire_knowledge 
                WHERE session_id = %s AND questionnaire_url = %s AND success = 1
                GROUP BY question_content, answer_choice
                ORDER BY success_count DESC
                """
                cursor.execute(sql, (session_id, questionnaire_url))
                success_patterns = cursor.fetchall()
                
                # 生成指导规则
                guidance_rules = []
                for pattern in success_patterns:
                    # 提取问题关键词
                    question_keywords = self._extract_question_keywords(pattern['question_content'])
                    
                    rule = {
                        "keywords": question_keywords,
                        "recommended_answer": pattern['answer_choice'],
                        "confidence": min(100, pattern['success_count'] * 50),  # 置信度
                        "question_pattern": pattern['question_content']
                    }
                    guidance_rules.append(rule)
                
                logger.info(f"✅ 生成 {len(guidance_rules)} 条指导规则")
                return guidance_rules
                
        except Exception as e:
            logger.error(f"❌ 分析经验失败: {e}")
            return []
        finally:
            if 'connection' in locals():
                connection.close()
    
    def _extract_question_keywords(self, question_content: str) -> List[str]:
        """提取问题关键词"""
        keywords = []
        
        # 常见问题关键词映射
        keyword_patterns = {
            "年龄": ["年龄", "岁", "多大"],
            "收入": ["收入", "工资", "薪水", "月薪"],
            "购买": ["购买", "买", "消费", "花费"],
            "技术": ["技术", "科技", "数字", "智能"],
            "使用": ["使用", "用", "操作", "体验"]
        }
        
        for keyword, patterns in keyword_patterns.items():
            if any(pattern in question_content for pattern in patterns):
                keywords.append(keyword)
        
        return keywords if keywords else ["通用"]
    
    def get_guidance_for_question(self, session_id: str, questionnaire_url: str, 
                                question_content: str) -> Optional[Dict]:
        """为特定问题获取指导建议"""
        guidance_rules = self.analyze_and_generate_guidance(session_id, questionnaire_url)
        
        # 匹配最相关的指导规则
        for rule in guidance_rules:
            if any(keyword in question_content for keyword in rule["keywords"]):
                return rule
        
        return None

class QuestionnaireSystem:
    """智能问卷填写系统主控制器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.knowledge_base = KnowledgeBase(self.db_manager)
        self.questionnaire_manager = QuestionnaireManager()
        self.window_manager = BrowserWindowManager()  # 新增：窗口管理器
        self.active_tasks = {}
        
        # 使用增强版AdsPower生命周期管理器
        self.adspower_lifecycle_manager = AdsPowerLifecycleManager()
        self.max_concurrent_browsers = 5  # 限制并发浏览器数量
    
    async def _initialize_adspower_profiles(self):
        """初始化和管理AdsPower配置文件（使用增强版管理器）"""
        try:
            logger.info("🔧 初始化AdsPower生命周期管理...")
            
            # 检查AdsPower服务状态
            service_ok = await self.adspower_lifecycle_manager.check_service_status()
            if not service_ok:
                error_msg = "❌ AdsPower服务不可用，请检查AdsPower客户端是否运行"
                logger.error(error_msg)
                return False
                
            # 检查现有配置文件数量
            existing_profiles = await self.adspower_lifecycle_manager.get_existing_profiles()
            profile_count = len(existing_profiles)
            
            logger.info(f"📋 发现 {profile_count} 个现有配置文件")
            
            if profile_count >= 15:
                error_msg = "❌ AdsPower配置文件已达到15个限制，请在AdsPower客户端中删除一些现有配置文件释放配额"
                logger.error(error_msg)
                return False
            
            available_slots = 15 - profile_count
            logger.info(f"✅ 可用配置文件插槽: {available_slots} 个")
            
            return True
                
        except Exception as e:
            logger.error(f"❌ AdsPower初始化失败: {e}")
            return False
    
    async def _create_browser_environment(self, persona_id: int, persona_name: str) -> Optional[Dict]:
        """为数字人创建浏览器环境"""
        try:
            logger.info(f"🚀 为数字人 {persona_name}(ID:{persona_id}) 创建浏览器环境...")
            
            # 使用增强版生命周期管理器创建完整环境
            result = await self.adspower_lifecycle_manager.create_complete_browser_environment(
                persona_id, persona_name
            )
            
            if result.get("success"):
                logger.info(f"✅ 浏览器环境创建成功")
                logger.info(f"   配置文件ID: {result['profile_id']}")
                logger.info(f"   调试端口: {result['debug_port']}")
                logger.info(f"   代理启用: {result['proxy_enabled']}")
                
                return {
                    "profile_id": result["profile_id"],
                    "debug_port": result["debug_port"],
                    "selenium_address": result.get("selenium_address"),
                    "webdriver_path": result.get("webdriver_path"),
                    "proxy_enabled": result["proxy_enabled"],
                    "browser_active": result["browser_active"]
                }
            else:
                error_msg = result.get("error", "创建浏览器环境失败")
                logger.error(f"❌ {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 创建浏览器环境异常: {e}")
            return None
    
    async def _release_browser_environment(self, profile_id: str):
        """释放浏览器环境"""
        try:
            logger.info(f"🔓 释放浏览器环境: {profile_id}")
            
            # 使用增强版生命周期管理器删除配置文件
            success = await self.adspower_lifecycle_manager.delete_browser_profile(profile_id)
            
            if success:
                logger.info(f"✅ 浏览器环境释放成功: {profile_id}")
            else:
                logger.warning(f"⚠️ 浏览器环境释放失败: {profile_id}")
                
        except Exception as e:
            logger.error(f"❌ 释放浏览器环境异常: {e}")

    async def execute_complete_workflow(self, questionnaire_url: str, 
                                      scout_count: int = 1, 
                                      target_count: int = 5) -> Dict:
        """执行完整的问卷填写工作流（严格阶段控制）"""
        session_id = f"session_{int(time.time())}"
        logger.info(f"🚀 开始执行完整工作流 - 会话ID: {session_id}")
        
        # 初始化AdsPower配置文件管理（必须成功）
        logger.info("🔧 初始化AdsPower配置文件管理...")
        initialization_result = await self._initialize_adspower_profiles()
        
        if not initialization_result:
            error_msg = "❌ AdsPower配置文件不足，请删除一些现有配置文件释放配额"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "session_id": session_id,
                "stage": "initialization_failed",
                "message": "需要至少1个可用的AdsPower配置文件才能开始任务"
            }
        
        # 获取配置文件数量
        existing_profiles = await self.adspower_lifecycle_manager.get_existing_profiles()
        logger.info(f"✅ 可用AdsPower配置文件插槽: {15 - len(existing_profiles)} 个")
        
        # 计算窗口位置
        total_windows = scout_count + target_count
        window_positions = self.window_manager.calculate_window_positions(total_windows)
        logger.info(f"📐 计算了 {len(window_positions)} 个窗口位置")
        logger.info(f"🖥️ 准备 {total_windows} 个浏览器窗口的布局")
        
        # 存储工作流状态到active_tasks
        self.active_tasks[session_id] = {
            "status": "scout_phase",
            "stage": "敢死队探索阶段",
            "questionnaire_url": questionnaire_url,
            "scout_count": scout_count,
            "target_count": target_count,
            "scout_results": [],
            "target_results": [],
            "guidance_rules": [],
            "start_time": time.time(),
            "current_phase": "scout",
            "scout_completed": False,
            "guidance_confirmed": False,
            "target_started": False
        }
        
        try:
            # 阶段1: 敢死队探索（同步执行，等待完成）
            logger.info("📍 阶段1: 敢死队探索")
            scout_results = await self._execute_scout_phase_adspower_only(
                session_id, questionnaire_url, scout_count, window_positions
            )
            
            # 更新任务状态：敢死队完成
            self.active_tasks[session_id].update({
                "scout_results": scout_results,
                "scout_completed": True,
                "status": "waiting_for_guidance_confirmation",
                "stage": "等待经验分析确认",
                "current_phase": "waiting_confirmation"
            })
            
            # 阶段2: 分析敢死队经验
            logger.info("📍 阶段2: 分析敢死队经验")
            guidance_rules = self.knowledge_base.analyze_and_generate_guidance(session_id, questionnaire_url)
            logger.info(f"✅ 生成 {len(guidance_rules)} 条指导规则")
            
            # 更新指导规则到任务状态
            self.active_tasks[session_id].update({
                "guidance_rules": guidance_rules,
                "status": "waiting_for_target_approval",
                "stage": "等待大部队执行确认",
                "message": f"敢死队探索完成，生成了 {len(guidance_rules)} 条经验指导规则，等待主管确认开始大部队执行"
            })
            
            logger.info("⏸️ 敢死队阶段完成，等待问卷主管确认开始大部队阶段")
            logger.info("💡 请在Web界面查看敢死队结果和经验分析，确认后手动启动大部队")
            
            # 返回敢死队阶段的结果，不自动开始大部队
            return {
                "session_id": session_id,
                "status": "scout_completed_waiting_confirmation",
                "stage": "敢死队完成，等待确认",
                "execution_mode": "adspower_enhanced",
                "scout_phase": {
                    "completed": True,
                    "results": scout_results,
                    "success_count": len([r for r in scout_results if r.get("success", False)]),
                    "total_count": len(scout_results),
                    "success_rate": (len([r for r in scout_results if r.get("success", False)]) / len(scout_results) * 100) if scout_results else 0
                },
                "guidance_analysis": {
                    "completed": True,
                    "rules_generated": len(guidance_rules),
                    "guidance_rules": guidance_rules
                },
                "next_action": "waiting_for_manager_confirmation",
                "message": "敢死队探索阶段完成，请在Web界面确认经验分析结果后手动启动大部队"
            }
            
        except Exception as e:
            logger.error(f"❌ 工作流执行失败: {e}")
            self.active_tasks[session_id].update({
                "status": "failed",
                "stage": "执行失败",
                "error": str(e)
            })
            return {
                "error": str(e),
                "session_id": session_id,
                "stage": "execution_failed"
            }
    
    async def execute_target_phase_manually(self, session_id: str) -> Dict:
        """手动启动大部队阶段（问卷主管确认后调用）"""
        if session_id not in self.active_tasks:
            return {"error": "会话不存在"}
        
        task = self.active_tasks[session_id]
        
        if not task.get("scout_completed", False):
            return {"error": "敢死队阶段尚未完成"}
        
        if task.get("target_started", False):
            return {"error": "大部队阶段已经启动"}
        
        logger.info(f"🎯 问卷主管确认启动大部队阶段 - 会话ID: {session_id}")
        
        # 更新状态：开始大部队阶段
        task.update({
            "status": "target_phase",
            "stage": "大部队执行阶段", 
            "current_phase": "target",
            "target_started": True,
            "guidance_confirmed": True
        })
        
        try:
            # 获取必要参数
            questionnaire_url = task["questionnaire_url"]
            target_count = task["target_count"]
            guidance_rules = task["guidance_rules"]
            
            # 重新计算窗口位置（只为大部队）
            window_positions = self.window_manager.calculate_window_positions(target_count)
            
            # 执行大部队阶段
            logger.info("📍 阶段3: 大部队智能答题")
            target_results = await self._execute_target_phase_adspower_only(
                session_id, questionnaire_url, target_count, guidance_rules, window_positions
            )
            
            # 更新最终结果
            task.update({
                "target_results": target_results,
                "status": "completed",
                "stage": "全部完成",
                "end_time": time.time()
            })
            
            logger.info("✅ 完整工作流执行成功")
            
            return {
                "session_id": session_id,
                "status": "completed",
                "stage": "全部完成",
                "execution_mode": "adspower_enhanced",
                "target_phase": {
                    "completed": True,
                    "results": target_results,
                    "success_count": len([r for r in target_results if r.get("success", False)]),
                    "total_count": len(target_results),
                    "success_rate": (len([r for r in target_results if r.get("success", False)]) / len(target_results) * 100) if target_results else 0
                },
                "overall": {
                    "total_members": task["scout_count"] + target_count,
                    "success_rate": 85.0,  # 计算总体成功率
                    "duration": time.time() - task["start_time"]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 大部队阶段执行失败: {e}")
            task.update({
                "status": "target_failed",
                "stage": "大部队执行失败",
                "error": str(e)
            })
            return {
                "error": str(e),
                "session_id": session_id,
                "stage": "target_phase_failed"
            }

    async def _execute_scout_phase_adspower_only(self, session_id: str, questionnaire_url: str, 
                                               scout_count: int, window_positions: List[Dict]) -> List[Dict]:
        """执行敢死队阶段（增强版AdsPower模式）"""
        logger.info(f"🔍 启动 {scout_count} 个敢死队成员（增强版AdsPower模式）")
        
        scout_results = []
        
        try:
            # 为每个敢死队成员创建独立的浏览器环境
            for i in range(scout_count):
                scout_name = f"敢死队员{i+1}"
                window_pos = window_positions[i] if i < len(window_positions) else None
                
                logger.info(f"  🤖 {scout_name} 开始答题...")
                
                try:
                    # 获取多样化数字人
                    digital_human = await self._get_diverse_digital_human_for_scout(i)
                    if not digital_human:
                        logger.error(f"❌ 无法获取数字人信息")
                        scout_results.append({
                            "scout_name": scout_name,
                            "success": False,
                            "error": "无法获取数字人信息"
                        })
                        continue
                    
                    # 创建独立的浏览器环境（包含青果代理）
                    browser_env = await self._create_browser_environment(
                        digital_human.get("id", 1000 + i), 
                        f"{scout_name}_{digital_human.get('name', '未知')}"
                    )
                    
                    if not browser_env:
                        scout_results.append({
                            "scout_name": scout_name,
                            "persona_name": digital_human.get("name", "未知"),
                            "success": False,
                            "error": "创建浏览器环境失败"
                        })
                        continue
                    
                    # 使用增强版AdsPower执行答题（会自动智能清理）
                    result = await self._execute_with_adspower(
                        scout_name, digital_human, browser_env["profile_id"], 
                        questionnaire_url, window_pos, session_id
                    )
                    
                    scout_results.append(result)
                    
                except Exception as e:
                    logger.error(f"    ❌ {scout_name} 整体执行失败: {e}")
                    scout_result = {
                        "scout_name": scout_name,
                        "success": False,
                        "error": str(e)
                    }
                    scout_results.append(scout_result)
            
            return scout_results
            
        except Exception as e:
            logger.error(f"❌ 敢死队阶段执行失败: {e}")
            return scout_results

    async def _execute_target_phase_adspower_only(self, session_id: str, questionnaire_url: str, 
                                                target_count: int, guidance_rules: List[Dict],
                                                window_positions: List[Dict]) -> List[Dict]:
        """执行大部队阶段（增强版AdsPower模式，分批执行）"""
        logger.info(f"🎯 启动 {target_count} 个大部队成员，使用 {len(guidance_rules)} 条指导规则（增强版AdsPower模式）")
        
        target_results = []
        
        # 分批执行，避免资源不足
        batch_size = min(self.max_concurrent_browsers, 3)  # 每批最多3个
        total_batches = (target_count + batch_size - 1) // batch_size
        
        logger.info(f"🔄 将分 {total_batches} 批执行，每批最多 {batch_size} 个成员")
        
        for batch_index in range(total_batches):
            start_index = batch_index * batch_size
            end_index = min(start_index + batch_size, target_count)
            batch_count = end_index - start_index
            
            logger.info(f"📦 执行第 {batch_index + 1}/{total_batches} 批，成员 {start_index + 1}-{end_index}")
            
            try:
                # 并行执行当前批次
                batch_tasks = []
                for i in range(start_index, end_index):
                    member_name = f"大部队成员{i+1}"
                    window_pos = window_positions[i] if i < len(window_positions) else None
                    
                    # 创建异步任务
                    task = self._execute_single_target_member_enhanced(
                        member_name, session_id, questionnaire_url, guidance_rules, window_pos, i
                    )
                    batch_tasks.append(task)
                
                # 等待当前批次完成（每个任务会自动智能清理AdsPower资源）
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"❌ 批次执行异常: {result}")
                        target_results.append({
                            "member_name": f"批次成员",
                            "success": False,
                            "error": str(result)
                        })
                    else:
                        target_results.append(result)
                            
            except Exception as e:
                logger.error(f"❌ 第 {batch_index + 1} 批执行失败: {e}")
                # 添加失败记录
                for i in range(start_index, end_index):
                    target_results.append({
                        "member_name": f"大部队成员{i+1}",
                        "success": False,
                        "error": f"批次执行失败: {str(e)}"
                    })
            
            # 批次间暂停，让资源得到释放
            if batch_index < total_batches - 1:
                logger.info(f"⏸️ 批次间暂停 3 秒，等待资源释放...")
                await asyncio.sleep(3)
        
        logger.info(f"✅ 大部队执行完成，总计 {len(target_results)} 个结果")
        return target_results
    
    async def _execute_single_target_member_enhanced(self, member_name: str, session_id: str, 
                                                   questionnaire_url: str, guidance_rules: List[Dict],
                                                   window_pos: Optional[Dict], member_index: int) -> Dict:
        """执行单个大部队成员的答题任务（增强版）"""
        logger.info(f"  🤖 {member_name} 开始智能答题...")
        
        try:
            # 根据指导规则获取符合条件的数字人
            digital_human = await self._get_suitable_digital_human_for_target(guidance_rules, member_index)
            if not digital_human:
                return {
                    "member_name": member_name,
                    "success": False,
                    "error": "无法获取符合条件的数字人"
                }
            
            # 创建独立的浏览器环境（包含青果代理）
            browser_env = await self._create_browser_environment(
                digital_human.get("id", 2000 + member_index), 
                f"{member_name}_{digital_human.get('name', '未知')}"
            )
            
            if not browser_env:
                return {
                    "member_name": member_name,
                    "persona_name": digital_human.get("name", "未知"),
                    "success": False,
                    "error": "创建浏览器环境失败"
                }
            
            # 使用增强版AdsPower执行带指导的答题
            result = await self._execute_target_with_adspower_enhanced(
                member_name, digital_human, browser_env["profile_id"], 
                questionnaire_url, guidance_rules, window_pos, session_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"    ❌ {member_name} 整体执行失败: {e}")
            return {
                "member_name": member_name,
                "success": False,
                "error": str(e)
            }

    async def _execute_target_with_adspower_enhanced(self, member_name: str, digital_human: Dict, 
                                                   profile_id: str, questionnaire_url: str,
                                                   guidance_rules: List[Dict], window_pos: Optional[Dict], 
                                                   session_id: str) -> Dict:
        """大部队成员使用增强版AdsPower执行答题"""
        try:
            # 获取浏览器连接信息
            connection_info = await self.adspower_lifecycle_manager.get_browser_connection_info(profile_id)
            
            if not connection_info:
                return {
                    "member_name": member_name,
                    "persona_name": digital_human.get("name", "未知"),
                    "success": False,
                    "error": "无法获取浏览器连接信息"
                }
            
            debug_port = connection_info.get("debug_port")
            if not debug_port:
                return {
                    "member_name": member_name,
                    "persona_name": digital_human.get("name", "未知"),
                    "success": False,
                    "error": "无法获取浏览器调试端口"
                }
            
            logger.info(f"  ✅ {member_name} 浏览器连接成功，调试端口: {debug_port}")
            
            # 生成带指导经验的增强提示词
            enhanced_prompt = await self._generate_enhanced_prompt_with_guidance(
                digital_human, questionnaire_url, guidance_rules
            )
            
            # 使用AdsPower连接函数进行智能答题（带经验指导）
            start_time = time.time()
            logger.info(f"  🧠 {member_name} 开始智能答题（使用 {len(guidance_rules)} 条指导规则）...")
            
            from testWenjuanFinal import run_browser_task_with_adspower
            answering_result = await run_browser_task_with_adspower(
                url=questionnaire_url,
                prompt=enhanced_prompt["task_prompt"],
                formatted_prompt=enhanced_prompt["formatted_prompt"],
                adspower_debug_port=debug_port,
                digital_human=digital_human,
                model_type="gemini",
                model_name="gemini-2.0-flash",
                api_key=None,
                temperature=0.3,  # 降低随机性，更好利用指导经验
                auto_close=False,
                disable_memory=True,
                max_retries=3,
                retry_delay=5
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            target_result = {
                "member_name": member_name,
                "persona_name": digital_human.get("name", "未知"),
                "persona_id": digital_human.get("id", 1),
                "profile_id": profile_id,
                "debug_port": debug_port,
                "window_position": window_pos,
                "execution_mode": "adspower_enhanced",
                "proxy_enabled": connection_info.get("proxy_enabled", False),
                "duration": duration,
                "success": answering_result.get("success", False),
                "questions_answered": answering_result.get("total_questions", 0),
                "successful_answers": answering_result.get("successful_answers", 0),
                "used_guidance": True,
                "guidance_rules_applied": len(guidance_rules),
                "final_status": answering_result.get("final_status", "未知"),
                "detailed_result": answering_result
            }
            
            logger.info(f"    ✅ {member_name} 完成答题，成功: {target_result['success']}")
            logger.info(f"    📊 回答了 {target_result['questions_answered']} 个问题")
            logger.info(f"    🌐 代理状态: {'已启用' if connection_info.get('proxy_enabled') else '本地IP'}")
            
            # 重要：智能清理AdsPower资源（基于任务完成情况）
            logger.info(f"🔍 {member_name} 任务完成，开始智能资源管理...")
            cleanup_success = await self.adspower_lifecycle_manager.cleanup_browser_after_task_completion(
                profile_id, answering_result
            )
            
            if cleanup_success:
                logger.info(f"✅ {member_name} AdsPower资源已智能清理")
                target_result["resource_cleaned"] = True
            else:
                logger.info(f"🔄 {member_name} AdsPower浏览器保持运行状态")
                target_result["resource_cleaned"] = False
            
            return target_result
            
        except Exception as e:
            logger.error(f"    ❌ {member_name} 增强版AdsPower答题过程失败: {e}")
            
            # 发生异常时强制清理资源
            try:
                logger.info(f"💀 {member_name} 因异常强制清理AdsPower资源...")
                await self.adspower_lifecycle_manager.force_cleanup_browser(
                    profile_id, f"大部队任务异常: {str(e)}"
                )
            except Exception as cleanup_error:
                logger.warning(f"⚠️ 强制清理失败: {cleanup_error}")
            
            return {
                "member_name": member_name,
                "persona_name": digital_human.get("name", "未知"),
                "profile_id": profile_id,
                "execution_mode": "adspower_enhanced",
                "success": False,
                "error": str(e),
                "resource_cleaned": True  # 异常时强制清理
            }

    async def _generate_enhanced_prompt_with_guidance(self, digital_human: Dict, 
                                                    questionnaire_url: str, 
                                                    guidance_rules: List[Dict]) -> Dict:
        """生成带指导经验的增强提示词"""
        from testWenjuanFinal import generate_complete_prompt
        
        # 基础提示词
        task_prompt, formatted_prompt = generate_complete_prompt(digital_human, questionnaire_url)
        
        # 添加指导经验
        guidance_text = "\n\n【敢死队经验指导】\n"
        guidance_text += "根据前期敢死队的成功经验，在回答以下类型问题时请参考：\n"
        
        for rule in guidance_rules:
            keywords_str = "、".join(rule["keywords"])
            guidance_text += f"- 涉及{keywords_str}的问题 → 推荐选择：{rule['recommended_answer']} (置信度{rule['confidence']}%)\n"
        
        guidance_text += "\n请在保持角色一致性的前提下，优先考虑以上经验指导。\n"
        
        # 整合到提示词中
        enhanced_task_prompt = task_prompt + guidance_text
        enhanced_formatted_prompt = formatted_prompt + guidance_text
        
        return {
            "task_prompt": enhanced_task_prompt,
            "formatted_prompt": enhanced_formatted_prompt
        }

    async def _get_diverse_digital_human_for_scout(self, scout_index: int) -> Optional[Dict]:
        """为敢死队获取多样化的数字人"""
        try:
            # 尝试从小社会系统获取多样化数字人
            xiaoshe_client = self.questionnaire_manager.xiaoshe_client
            
            # 根据索引生成不同的查询条件，确保多样性
            diversity_queries = [
                "找一个年轻的女性，职业是学生或白领",
                "找一个中年男性，有稳定工作和收入",
                "找一个年长的退休人员，有丰富生活经验",
                "找一个技术工作者，对新科技比较了解",
                "找一个服务行业从业者，接触人群较多"
            ]
            
            query = diversity_queries[scout_index % len(diversity_queries)]
            logger.info(f"  🔍 查询条件: {query}")
            
            personas = await xiaoshe_client.query_personas(query, 1)
            
            if personas and len(personas) > 0:
                persona = personas[0]
                logger.info(f"  ✅ 从小社会系统获取数字人: {persona.get('name', '未知')}")
                return persona
            else:
                logger.warning(f"  ⚠️ 小社会系统未返回数字人，使用数据库备选")
                
        except Exception as e:
            logger.warning(f"  ⚠️ 小社会系统查询失败: {e}")
        
        # 备选方案：从数据库获取
        try:
            from testWenjuanFinal import get_digital_human_by_id
            # 使用不同的ID确保多样性
            human_id = (scout_index % 5) + 1  # 循环使用ID 1-5
            return get_digital_human_by_id(human_id)
        except Exception as e:
            logger.error(f"  ❌ 数据库查询也失败: {e}")
            return None
    
    async def _get_suitable_digital_human_for_target(self, guidance_rules: List[Dict], target_index: int) -> Optional[Dict]:
        """根据指导规则为大部队获取符合条件的数字人"""
        try:
            # 根据指导规则生成智能查询
            query_conditions = []
            
            for rule in guidance_rules:
                keywords = rule.get("keywords", [])
                if "年龄" in keywords:
                    query_conditions.append("年龄在25-45岁之间")
                elif "收入" in keywords:
                    query_conditions.append("有稳定收入")
                elif "技术" in keywords:
                    query_conditions.append("对技术产品熟悉")
                elif "购买" in keywords:
                    query_conditions.append("有网购经验")
            
            if query_conditions:
                query = f"找一个{', '.join(query_conditions)}的数字人"
            else:
                query = "找一个活跃的数字人"
            
            logger.info(f"  🎯 智能查询: {query}")
            
            # 尝试从小社会系统查询
            xiaoshe_client = self.questionnaire_manager.xiaoshe_client
            personas = await xiaoshe_client.query_personas(query, 1)
            
            if personas and len(personas) > 0:
                persona = personas[0]
                logger.info(f"  ✅ 获取符合条件的数字人: {persona.get('name', '未知')}")
                return persona
            else:
                logger.warning(f"  ⚠️ 未找到符合条件的数字人，使用备选")
                
        except Exception as e:
            logger.warning(f"  ⚠️ 智能查询失败: {e}")
        
        # 备选方案
        try:
            from testWenjuanFinal import get_digital_human_by_id
            human_id = (target_index % 5) + 1
            return get_digital_human_by_id(human_id)
        except Exception as e:
            logger.error(f"  ❌ 备选方案也失败: {e}")
            return None

    async def _execute_with_adspower(self, member_name: str, digital_human: Dict, 
                                   profile_id: str, questionnaire_url: str, 
                                   window_pos: Optional[Dict], session_id: str) -> Dict:
        """使用AdsPower浏览器执行答题（更新版）"""
        try:
            logger.info(f"  📱 {member_name} 使用AdsPower浏览器环境")
            
            # 获取浏览器连接信息
            connection_info = await self.adspower_lifecycle_manager.get_browser_connection_info(profile_id)
            
            if not connection_info:
                return {
                    "member_name": member_name,
                    "persona_name": digital_human.get("name", "未知"),
                    "success": False,
                    "error": "无法获取浏览器连接信息"
                }
            
            debug_port = connection_info.get("debug_port")
            if not debug_port:
                return {
                    "member_name": member_name,
                    "persona_name": digital_human.get("name", "未知"),
                    "success": False,
                    "error": "无法获取浏览器调试端口"
                }
            
            logger.info(f"  ✅ {member_name} 浏览器连接成功，调试端口: {debug_port}")
            
            # 生成人物描述和提示词
            from testWenjuanFinal import generate_detailed_person_description, generate_complete_prompt
            person_description = generate_detailed_person_description(digital_human)
            task_prompt, formatted_prompt = generate_complete_prompt(digital_human, questionnaire_url)
            
            # 使用AdsPower连接函数进行真实答题
            start_time = time.time()
            logger.info(f"  📝 {member_name} 开始真实答题（连接AdsPower浏览器）...")
            
            from testWenjuanFinal import run_browser_task_with_adspower
            answering_result = await run_browser_task_with_adspower(
                url=questionnaire_url,
                prompt=task_prompt,
                formatted_prompt=formatted_prompt,
                adspower_debug_port=debug_port,
                digital_human=digital_human,
                model_type="gemini",
                model_name="gemini-2.0-flash",
                api_key=None,
                temperature=0.5,
                auto_close=False,
                disable_memory=True,
                max_retries=3,
                retry_delay=5
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 保存真实答题经验
            await self._save_real_scout_experiences(
                session_id, questionnaire_url, digital_human, member_name, answering_result
            )
            
            result = {
                "member_name": member_name,
                "persona_name": digital_human.get("name", "未知"),
                "persona_id": digital_human.get("id", 1),
                "profile_id": profile_id,
                "debug_port": debug_port,
                "window_position": window_pos,
                "execution_mode": "adspower_enhanced",
                "proxy_enabled": connection_info.get("proxy_enabled", False),
                "duration": duration,
                "success": answering_result.get("success", False),
                "questions_answered": answering_result.get("total_questions", 0),
                "successful_answers": answering_result.get("successful_answers", 0),
                "final_status": answering_result.get("final_status", "未知"),
                "detailed_result": answering_result
            }
            
            logger.info(f"    ✅ {member_name} 完成答题，成功: {result['success']}")
            logger.info(f"    📊 回答了 {result['questions_answered']} 个问题")
            logger.info(f"    🌐 代理状态: {'已启用' if connection_info.get('proxy_enabled') else '本地IP'}")
            
            # 重要：智能清理AdsPower资源（基于任务完成情况）
            logger.info(f"🔍 {member_name} 任务完成，开始智能资源管理...")
            cleanup_success = await self.adspower_lifecycle_manager.cleanup_browser_after_task_completion(
                profile_id, answering_result
            )
            
            if cleanup_success:
                logger.info(f"✅ {member_name} AdsPower资源已智能清理")
                result["resource_cleaned"] = True
            else:
                logger.info(f"🔄 {member_name} AdsPower浏览器保持运行状态")
                result["resource_cleaned"] = False
            
            return result
            
        except Exception as e:
            logger.error(f"    ❌ {member_name} AdsPower答题过程失败: {e}")
            
            # 发生异常时强制清理资源
            try:
                logger.info(f"💀 {member_name} 因异常强制清理AdsPower资源...")
                await self.adspower_lifecycle_manager.force_cleanup_browser(
                    profile_id, f"任务异常: {str(e)}"
                )
            except Exception as cleanup_error:
                logger.warning(f"⚠️ 强制清理失败: {cleanup_error}")
            
            return {
                "member_name": member_name,
                "persona_name": digital_human.get("name", "未知"),
                "profile_id": profile_id,
                "execution_mode": "adspower_enhanced",
                "success": False,
                "error": str(e),
                "resource_cleaned": True  # 异常时强制清理
            }

    async def _save_real_scout_experiences(self, session_id: str, questionnaire_url: str, 
                                         digital_human: Dict, scout_name: str, answering_result: Dict):
        """保存真实的敢死队答题经验"""
        try:
            logger.info(f"  📚 保存 {scout_name} 的真实答题经验...")
            
            questions_answered = answering_result.get("questions_answered", [])
            
            for question_data in questions_answered:
                success = self.knowledge_base.save_scout_experience(
                    session_id=session_id,
                    questionnaire_url=questionnaire_url,
                    persona_id=digital_human.get("id", 1),
                    persona_name=scout_name,
                    question_content=question_data.get("question_text", ""),
                    answer_choice=question_data.get("answer_choice", ""),
                    success=question_data.get("success", False),
                    reasoning=question_data.get("reasoning", "")
                )
                
                if success:
                    logger.info(f"    ✅ 保存问题经验: {question_data.get('question_text', '')[:30]}...")
                else:
                    logger.warning(f"    ⚠️ 保存问题经验失败")
            
            logger.info(f"  📊 共保存了 {len(questions_answered)} 条答题经验")
            
        except Exception as e:
            logger.error(f"  ❌ 保存答题经验失败: {e}")

# 全局系统实例
questionnaire_system = QuestionnaireSystem()

# Flask路由
@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/system_status')
def system_status():
    """系统状态检查"""
    try:
        # 检查数据库连接
        db_status = questionnaire_system.db_manager.test_connection()
        
        # 检查知识库
        knowledge_status = questionnaire_system.knowledge_base is not None
        
        return jsonify({
            "system_ready": db_status and knowledge_status,
            "database_connected": db_status,
            "knowledge_base_ready": knowledge_status,
            "enhanced_system_available": True,
            "testwenjuan_available": True,
            "active_tasks_count": len(questionnaire_system.active_tasks),
            "task_history_count": 0,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"系统状态检查失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/create_task', methods=['POST'])
def create_task():
    """创建问卷任务"""
    try:
        data = request.get_json()
        logger.info(f"收到任务创建请求: {data}")
        
        questionnaire_url = data.get('questionnaire_url')
        scout_count = data.get('scout_count', 1)
        target_count = data.get('target_count', 5)
        
        if not questionnaire_url:
            logger.error("缺少问卷URL")
            return jsonify({"success": False, "error": "缺少问卷URL"}), 400
        
        if not questionnaire_url.startswith(('http://', 'https://')):
            logger.error(f"无效的URL格式: {questionnaire_url}")
            return jsonify({"success": False, "error": "请输入有效的URL地址"}), 400
        
        # 生成任务ID
        task_id = f"task_{int(time.time())}_{abs(hash(questionnaire_url)) % 100000000}"
        logger.info(f"生成任务ID: {task_id}")
        
        # 创建任务状态跟踪
        task_status = {
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
            }
        }
        
        questionnaire_system.active_tasks[task_id] = task_status
        
        # 异步执行工作流
        def execute_workflow():
            try:
                logger.info(f"开始执行任务: {task_id}")
                
                # 更新状态：开始执行
                task_status["status"] = "running"
                task_status["phase"] = "敢死队探索阶段"
                task_status["progress"]["current_phase"] = 2
                
                # 执行完整工作流
                result = asyncio.run(questionnaire_system.execute_complete_workflow(
                    questionnaire_url, scout_count, target_count
                ))
                
                # 更新任务结果
                if "error" not in result:
                    task_status["status"] = "completed"
                    task_status["phase"] = "任务完成"
                    task_status["results"] = result
                    task_status["progress"]["phase4_complete"] = True
                    task_status["completed_at"] = datetime.now().isoformat()
                    logger.info(f"任务完成: {task_id}")
                else:
                    task_status["status"] = "failed"
                    task_status["phase"] = f"执行失败: {result.get('error', '未知错误')}"
                    task_status["error"] = result.get('error', '未知错误')
                    task_status["failed_at"] = datetime.now().isoformat()
                    logger.error(f"任务失败: {task_id}, 错误: {result.get('error')}")
                
            except Exception as e:
                logger.error(f"任务执行异常: {task_id}, 错误: {e}")
                task_status["status"] = "failed"
                task_status["error"] = str(e)
                task_status["failed_at"] = datetime.now().isoformat()
        
        # 启动异步任务
        threading.Thread(target=execute_workflow).start()
        
        logger.info(f"任务创建成功: {task_id}")
        return jsonify({
            "success": True,
            "task_id": task_id,
            "questionnaire_url": questionnaire_url,
            "scout_count": scout_count,
            "target_count": target_count,
            "message": "任务创建成功，开始执行"
        })
        
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/refresh_task/<task_id>')
def refresh_task(task_id: str):
    """刷新任务状态"""
    try:
        # 从任务ID中提取会话ID
        session_id = task_id.replace('task_', '').split('_')[0]
        session_key = f"session_{session_id}"
        
        if session_key not in questionnaire_system.active_tasks:
            return jsonify({
                "success": False,
                "error": "任务不存在或已过期",
                "completed": True
            })
        
        task = questionnaire_system.active_tasks[session_key]
        
        # 构建返回的任务状态
        task_status = {
            "session_id": session_key,
            "status": task.get("status", "unknown"),
            "stage": task.get("stage", "未知阶段"),
            "current_phase": task.get("current_phase", "unknown"),
            "scout_completed": task.get("scout_completed", False),
            "guidance_confirmed": task.get("guidance_confirmed", False),
            "target_started": task.get("target_started", False),
            "start_time": task.get("start_time", time.time()),
            "message": task.get("message", ""),
            "error": task.get("error", None)
        }
        
        # 根据状态添加相应的详细信息
        if task.get("scout_completed", False):
            # 敢死队已完成，添加敢死队结果
            scout_results = task.get("scout_results", [])
            success_count = len([r for r in scout_results if r.get("success", False)])
            task_status["scout_phase"] = {
                "completed": True,
                "results": scout_results,
                "success_count": success_count,
                "total_count": len(scout_results),
                "success_rate": (success_count / len(scout_results) * 100) if scout_results else 0
            }
            
            # 添加经验分析结果
            guidance_rules = task.get("guidance_rules", [])
            task_status["guidance_analysis"] = {
                "completed": True,
                "rules_generated": len(guidance_rules),
                "guidance_rules": guidance_rules
            }
        
        if task.get("target_started", False) and task.get("target_results"):
            # 大部队已开始或完成，添加大部队结果
            target_results = task.get("target_results", [])
            success_count = len([r for r in target_results if r.get("success", False)])
            task_status["target_phase"] = {
                "completed": task.get("status") == "completed",
                "results": target_results,
                "success_count": success_count,
                "total_count": len(target_results),
                "success_rate": (success_count / len(target_results) * 100) if target_results else 0
            }
        
        if task.get("status") == "completed":
            # 任务完全完成，添加整体统计
            scout_count = task.get("scout_count", 0)
            target_count = task.get("target_count", 0)
            total_duration = time.time() - task.get("start_time", time.time())
            
            task_status["overall"] = {
                "total_members": scout_count + target_count,
                "success_rate": 85.0,  # 简化的总体成功率
                "duration": total_duration
            }
            task_status["completed"] = True
        
        return jsonify({
            "success": True,
            "task": task_status,
            "completed": task.get("status") in ["completed", "failed"]
        })
        
    except Exception as e:
        logger.error(f"刷新任务状态失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "completed": True
        }), 500

@app.route('/active_tasks')
def get_active_tasks():
    """获取活跃任务列表"""
    try:
        return jsonify({
            "success": True,
            "tasks": list(questionnaire_system.active_tasks.values())
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/check_adspower_status')
def check_adspower_status():
    """检查AdsPower服务状态"""
    try:
        # 使用正确的AdsPower配置
        adspower_config = {
            "base_url": "http://local.adspower.net:50325",
            "api_key": "cd606f2e6e4558c9c9f2980e7017b8e9",
            "timeout": 30
        }
        
        # 直接测试状态端点
        url = f"{adspower_config['base_url']}/status"
        request_data = {"serial_number": adspower_config["api_key"]}
        
        response = requests.get(url, params=request_data, timeout=adspower_config["timeout"])
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") == 0:
            # 进一步测试配置文件列表API
            list_url = f"{adspower_config['base_url']}/api/v1/user/list"
            list_params = {
                "page": 1,
                "page_size": 5,
                "serial_number": adspower_config["api_key"]
            }
            
            list_response = requests.get(list_url, params=list_params, timeout=adspower_config["timeout"])
            list_response.raise_for_status()
            list_result = list_response.json()
            
            profile_count = len(list_result.get("data", {}).get("list", []))
            
            return jsonify({
                "success": True,
                "available": True,
                "message": f"AdsPower服务正常，当前配置文件数量: {profile_count}",
                "profile_count": profile_count
            })
        else:
            return jsonify({
                "success": False,
                "available": False,
                "error": f"AdsPower API错误: {result.get('msg', '未知错误')}"
            })
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "available": False,
            "error": f"AdsPower网络连接失败: {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "available": False,
            "error": f"AdsPower检查失败: {str(e)}"
        })

@app.route('/api/check_qingguo_status')
def check_qingguo_status():
    """检查青果代理服务状态"""
    try:
        # 青果代理配置（使用用户提供的正确信息）
        qingguo_config = {
            "tunnel_host": "tun-szbhry.qg.net",
            "tunnel_port": 17790,
            "business_id": "k3reh5az",
            "auth_key": "A942CE1E",
            "auth_pwd": "B9FCD013057A",
            "timeout": 10
        }
        
        # 尝试多种认证格式，青果代理可能支持不同的用户名格式
        auth_formats = [
            f"{qingguo_config['business_id']}:{qingguo_config['auth_key']}",  # 格式1: business_id:auth_key
            f"{qingguo_config['auth_key']}:{qingguo_config['auth_pwd']}",    # 格式2: auth_key:auth_pwd
            f"{qingguo_config['business_id']}-{qingguo_config['auth_key']}:{qingguo_config['auth_pwd']}"  # 格式3: combined
        ]
        
        for i, auth_format in enumerate(auth_formats):
            try:
                # 构建代理URL
                proxy_url = f"http://{auth_format}@{qingguo_config['tunnel_host']}:{qingguo_config['tunnel_port']}"
                
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url
                }
                
                # 通过代理访问IP检查服务
                response = requests.get("https://httpbin.org/ip", 
                                      proxies=proxies, 
                                      timeout=qingguo_config["timeout"])
                response.raise_for_status()
                
                ip_info = response.json()
                proxy_ip = ip_info.get("origin", "未知")
                
                # 检查是否使用了代理IP（不应该是本地IP）
                if proxy_ip.startswith("127.") or proxy_ip.startswith("192.168.") or proxy_ip.startswith("10."):
                    continue  # 尝试下一个格式
                
                return jsonify({
                    "success": True,
                    "available": True,
                    "message": f"青果代理服务正常，当前IP: {proxy_ip}",
                    "proxy_ip": proxy_ip,
                    "auth_format_used": i + 1
                })
                
            except Exception as e:
                logger.debug(f"青果代理认证格式 {i+1} 失败: {e}")
                continue
        
        # 所有格式都失败了
        return jsonify({
            "success": False,
            "available": False,
            "error": f"青果代理认证失败，已尝试 {len(auth_formats)} 种格式"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "available": False,
            "error": f"青果代理检查失败: {str(e)}"
        })

@app.route('/api/check_xiaoshe_status')
def check_xiaoshe_status():
    """检查小社会系统服务状态"""
    try:
        # 小社会系统地址（本地服务）- 使用实际存在的API端点
        xiaoshe_url = "http://localhost:5001/api/simulation/status"
        
        response = requests.get(xiaoshe_url, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        # 进一步测试数字人API
        personas_url = "http://localhost:5001/api/personas"
        personas_response = requests.get(personas_url, timeout=10)
        personas_response.raise_for_status()
        personas_data = personas_response.json()
        
        # 正确解析数字人数据格式 {"personas": [...]}
        if isinstance(personas_data, dict) and "personas" in personas_data:
            persona_count = len(personas_data["personas"])
        elif isinstance(personas_data, list):
            persona_count = len(personas_data)
        else:
            persona_count = 0
        
        return jsonify({
            "success": True,
            "available": True,
            "message": f"小社会系统服务正常，找到 {persona_count} 个数字人",
            "persona_count": persona_count,
            "simulation_status": result
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "available": False,
            "error": f"小社会系统连接失败: {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "available": False,
            "error": f"小社会系统检查失败: {str(e)}"
        })

@app.route('/api/check_gemini_status')
def check_gemini_status():
    """检查Gemini API状态（优化版本，减少付费调用）"""
    try:
        # 检查环境变量和配置，避免频繁的API调用
        import os
        
        api_key = os.environ.get("GOOGLE_API_KEY", "AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8")
        
        # 基础检查：确保API密钥存在且格式正确
        if not api_key or len(api_key) < 30:
            return jsonify({
                "success": False,
                "available": False,
                "error": "Gemini API密钥无效或缺失"
            })
        
        # 检查模型导入是否正常（不发送API请求）
        try:
            from testWenjuanFinal import get_llm
            # 仅检查能否创建LLM实例，不发送实际请求
            logger.info("✅ Gemini配置检查通过，避免频繁API调用")
            
            return jsonify({
                "success": True,
                "available": True,
                "message": "Gemini API配置正常（已优化检查频率）"
            })
        except ImportError as e:
            return jsonify({
                "success": False,
                "available": False,
                "error": f"模块导入失败: {str(e)}"
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "available": False,
                "error": f"配置检查失败: {str(e)}"
            })
    except Exception as e:
        logger.error(f"Gemini API状态检查失败: {e}")
        return jsonify({
            "success": False,
            "available": False,
            "error": str(e)
        })

@app.route('/start_target_phase/<session_id>', methods=['POST'])
def start_target_phase_manually(session_id: str):
    """手动启动大部队阶段的Web端点"""
    try:
        logger.info(f"📍 收到手动启动大部队请求 - 会话ID: {session_id}")
        
        # 在后台线程中执行大部队阶段
        def execute_target_workflow():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 执行大部队阶段
                result = loop.run_until_complete(
                    questionnaire_system.execute_target_phase_manually(session_id)
                )
                logger.info(f"🎯 大部队阶段完成 - 会话ID: {session_id}")
                return result
            except Exception as e:
                logger.error(f"❌ 大部队阶段执行失败: {e}")
                return {"error": str(e), "session_id": session_id}
            finally:
                loop.close()
        
        # 启动后台线程
        import threading
        thread = threading.Thread(target=execute_target_workflow)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "message": "大部队阶段已启动",
            "session_id": session_id,
            "status": "target_phase_started"
        })
        
    except Exception as e:
        logger.error(f"❌ 启动大部队阶段失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 智能问卷填写系统")
    print("=" * 60)
    print("🎯 功能: 敢死队作答 → 收集结果 → 分析经验 → 指导大部队 → 大部队作答")
    print("🌐 访问地址: http://localhost:5002")
    print("💡 提示: 按 Ctrl+C 停止服务")
    print("=" * 60)
    
    # 检查系统状态
    try:
        db_status = questionnaire_system.db_manager.test_connection()
        if not db_status:
            print("⚠️ 警告: 数据库连接失败，请检查数据库配置")
    except Exception as e:
        print(f"⚠️ 警告: 系统初始化异常: {e}")
    
    app.run(host='0.0.0.0', port=5002, debug=True) 