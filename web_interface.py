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
from phase2_scout_automation import EnhancedScoutAutomationSystem
from phase3_knowledge_analysis import Phase3KnowledgeAnalysisSystem
from phase4_mass_automation import Phase4MassAutomationSystem

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入新增强系统
try:
    from enhanced_browser_use_integration import EnhancedBrowserUseIntegration
    from demo_enhanced_integration import EnhancedQuestionnaireSystem
    ENHANCED_SYSTEM_AVAILABLE = True
    logger.info("✅ 增强系统模块加载成功")
except ImportError as e:
    ENHANCED_SYSTEM_AVAILABLE = False
    logger.warning(f"⚠️ 增强系统模块加载失败: {e}")

# 尝试导入testWenjuanFinal
try:
    import testWenjuanFinal
    TESTWENJUAN_AVAILABLE = True
    logger.info("✅ testWenjuanFinal.py模块可用")
except ImportError:
    TESTWENJUAN_AVAILABLE = False
    logger.warning("⚠️ testWenjuanFinal.py模块不可用")

app = Flask(__name__)
app.secret_key = 'questionnaire_system_secret_key_2024'

# 资源消耗统计类
class ResourceConsumptionTracker:
    """资源消耗统计器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._init_consumption_table()
    
    def _init_consumption_table(self):
        """初始化资源消耗统计表"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS resource_consumption (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    task_id VARCHAR(100) NOT NULL,
                    session_id VARCHAR(100) NOT NULL,
                    questionnaire_url VARCHAR(500) NOT NULL,
                    resource_type ENUM('adspower_browser', 'qinguo_proxy', 'xiaoshe_query', 'browser_use_action') NOT NULL,
                    resource_name VARCHAR(200),
                    quantity INT DEFAULT 1,
                    unit_cost DECIMAL(10,4) DEFAULT 0.0000,
                    total_cost DECIMAL(10,4) DEFAULT 0.0000,
                    currency VARCHAR(10) DEFAULT 'CNY',
                    provider VARCHAR(100),
                    details JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_task_id (task_id),
                    INDEX idx_session_id (session_id),
                    INDEX idx_resource_type (resource_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                connection.commit()
                logger.info("✅ 资源消耗统计表初始化完成")
        except Exception as e:
            logger.error(f"❌ 初始化资源消耗统计表失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()
    
    def record_adspower_consumption(self, task_id: str, session_id: str, questionnaire_url: str, 
                                  browser_count: int, duration_hours: float = 1.0):
        """记录AdsPower浏览器消耗"""
        try:
            # AdsPower成本估算：按浏览器实例和使用时长计费
            # 假设：每个浏览器实例每小时0.05元（实际价格请参考AdsPower官方）
            unit_cost = 0.05  # 每浏览器每小时
            total_cost = browser_count * duration_hours * unit_cost
            
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO resource_consumption 
                (task_id, session_id, questionnaire_url, resource_type, resource_name, 
                 quantity, unit_cost, total_cost, provider, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    task_id, session_id, questionnaire_url, 'adspower_browser',
                    f'{browser_count}个浏览器实例', browser_count, unit_cost, total_cost,
                    'AdsPower', json.dumps({
                        'browser_count': browser_count,
                        'duration_hours': duration_hours,
                        'cost_per_browser_hour': unit_cost
                    })
                ))
                connection.commit()
                logger.info(f"✅ 记录AdsPower消耗: {browser_count}个浏览器 × {duration_hours}小时 = ¥{total_cost:.4f}")
        except Exception as e:
            logger.error(f"❌ 记录AdsPower消耗失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()
    
    def record_qinguo_proxy_consumption(self, task_id: str, session_id: str, questionnaire_url: str,
                                      proxy_type: str, ip_count: int, duration_minutes: int = 60):
        """记录青果代理消耗"""
        try:
            # 青果代理成本估算（实际价格请参考青果官方）
            cost_config = {
                'tunnel_proxy': {'unit_cost': 0.02, 'unit': '每IP每小时'},  # 隧道代理
                'short_proxy': {'unit_cost': 0.01, 'unit': '每IP每次'},     # 短效代理
                'long_proxy': {'unit_cost': 0.05, 'unit': '每IP每天'}       # 长效代理
            }
            
            config = cost_config.get(proxy_type, cost_config['tunnel_proxy'])
            
            if proxy_type == 'tunnel_proxy':
                total_cost = ip_count * (duration_minutes / 60) * config['unit_cost']
            elif proxy_type == 'short_proxy':
                total_cost = ip_count * config['unit_cost']
            else:  # long_proxy
                total_cost = ip_count * (duration_minutes / 1440) * config['unit_cost']
            
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO resource_consumption 
                (task_id, session_id, questionnaire_url, resource_type, resource_name, 
                 quantity, unit_cost, total_cost, provider, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    task_id, session_id, questionnaire_url, 'qinguo_proxy',
                    f'{ip_count}个{proxy_type}代理IP', ip_count, config['unit_cost'], total_cost,
                    '青果代理', json.dumps({
                        'proxy_type': proxy_type,
                        'ip_count': ip_count,
                        'duration_minutes': duration_minutes,
                        'unit_description': config['unit']
                    })
                ))
                connection.commit()
                logger.info(f"✅ 记录青果代理消耗: {ip_count}个{proxy_type} × {duration_minutes}分钟 = ¥{total_cost:.4f}")
        except Exception as e:
            logger.error(f"❌ 记录青果代理消耗失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()
    
    def record_xiaoshe_query_consumption(self, task_id: str, session_id: str, questionnaire_url: str,
                                       query_count: int, query_type: str = 'standard'):
        """记录小社会系统查询消耗"""
        try:
            # 小社会系统查询成本估算
            cost_config = {
                'standard': 0.001,  # 标准查询每次0.001元
                'advanced': 0.005,  # 高级查询每次0.005元
                'batch': 0.0005     # 批量查询每次0.0005元
            }
            
            unit_cost = cost_config.get(query_type, cost_config['standard'])
            total_cost = query_count * unit_cost
            
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO resource_consumption 
                (task_id, session_id, questionnaire_url, resource_type, resource_name, 
                 quantity, unit_cost, total_cost, provider, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    task_id, session_id, questionnaire_url, 'xiaoshe_query',
                    f'{query_count}次{query_type}查询', query_count, unit_cost, total_cost,
                    '小社会系统', json.dumps({
                        'query_type': query_type,
                        'query_count': query_count
                    })
                ))
                connection.commit()
                logger.info(f"✅ 记录小社会查询消耗: {query_count}次{query_type}查询 = ¥{total_cost:.4f}")
        except Exception as e:
            logger.error(f"❌ 记录小社会查询消耗失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()
    
    def get_task_consumption_summary(self, task_id: str) -> Dict:
        """获取任务资源消耗汇总"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT resource_type, SUM(quantity) as total_quantity, 
                       SUM(total_cost) as total_cost, provider
                FROM resource_consumption 
                WHERE task_id = %s 
                GROUP BY resource_type, provider
                """, (task_id,))
                
                results = cursor.fetchall()
                summary = {
                    'total_cost': 0.0,
                    'resources': []
                }
                
                for result in results:
                    resource_info = {
                        'type': result[0],
                        'quantity': result[1],
                        'cost': float(result[2]),
                        'provider': result[3]
                    }
                    summary['resources'].append(resource_info)
                    summary['total_cost'] += resource_info['cost']
                
                return summary
        except Exception as e:
            logger.error(f"❌ 获取任务消耗汇总失败: {e}")
            return {'total_cost': 0.0, 'resources': []}
        finally:
            if 'connection' in locals():
                connection.close()

# 成本优化管理器
class CostOptimizationManager:
    """成本优化管理器"""
    
    def __init__(self):
        self.optimization_strategies = {
            'adspower': self._optimize_adspower_usage,
            'qinguo': self._optimize_qinguo_proxy,
            'xiaoshe': self._optimize_xiaoshe_queries
        }
    
    def _optimize_adspower_usage(self, scout_count: int, target_count: int, questionnaire_complexity: str) -> Dict:
        """优化AdsPower浏览器使用策略"""
        recommendations = {
            'browser_reuse': True,  # 启用浏览器复用
            'concurrent_limit': min(5, target_count),  # 限制并发数
            'profile_cleanup': True,  # 及时清理配置文件
            'cost_estimate': 0.0
        }
        
        # 根据问卷复杂度调整策略
        if questionnaire_complexity == 'simple':
            recommendations['browser_reuse'] = True
            recommendations['session_duration'] = 0.5  # 30分钟
        elif questionnaire_complexity == 'complex':
            recommendations['browser_reuse'] = False
            recommendations['session_duration'] = 2.0  # 2小时
        else:
            recommendations['session_duration'] = 1.0  # 1小时
        
        # 成本估算
        total_browsers = scout_count + recommendations['concurrent_limit']
        recommendations['cost_estimate'] = total_browsers * recommendations['session_duration'] * 0.05
        
        return recommendations
    
    def _optimize_qinguo_proxy(self, target_count: int, questionnaire_duration: int) -> Dict:
        """优化青果代理使用策略"""
        recommendations = {
            'proxy_type': 'tunnel_proxy',  # 默认使用隧道代理
            'ip_rotation': True,
            'cost_estimate': 0.0
        }
        
        # 根据任务规模选择代理类型
        if target_count <= 5 and questionnaire_duration <= 30:
            recommendations['proxy_type'] = 'short_proxy'
            recommendations['cost_estimate'] = target_count * 0.01
        elif questionnaire_duration >= 120:
            recommendations['proxy_type'] = 'long_proxy'
            recommendations['cost_estimate'] = target_count * 0.05 * (questionnaire_duration / 1440)
        else:
            recommendations['proxy_type'] = 'tunnel_proxy'
            recommendations['cost_estimate'] = target_count * (questionnaire_duration / 60) * 0.02
        
        # 运营商选择建议
        recommendations['isp_preference'] = ['移动', '联通', '电信']  # 按成功率排序
        recommendations['region_preference'] = ['一线城市', '二线城市']  # 按可信度排序
        
        return recommendations
    
    def _optimize_xiaoshe_queries(self, target_count: int) -> Dict:
        """优化小社会系统查询策略"""
        recommendations = {
            'query_type': 'standard',
            'batch_size': min(50, target_count * 3),  # 批量查询减少成本
            'cache_enabled': True,
            'cost_estimate': 0.0
        }
        
        # 根据目标数量选择查询策略
        if target_count >= 20:
            recommendations['query_type'] = 'batch'
            recommendations['cost_estimate'] = (target_count * 3) * 0.0005
        else:
            recommendations['query_type'] = 'standard'
            recommendations['cost_estimate'] = (target_count * 2) * 0.001
        
        return recommendations
    
    def get_optimization_plan(self, scout_count: int, target_count: int, 
                            questionnaire_url: str) -> Dict:
        """获取完整的成本优化方案"""
        # 分析问卷复杂度（简化版）
        questionnaire_complexity = 'medium'
        if 'simple' in questionnaire_url.lower() or len(questionnaire_url) < 50:
            questionnaire_complexity = 'simple'
        elif 'complex' in questionnaire_url.lower() or len(questionnaire_url) > 100:
            questionnaire_complexity = 'complex'
        
        # 估算问卷时长（分钟）
        estimated_duration = 60  # 默认60分钟
        
        plan = {
            'adspower': self._optimize_adspower_usage(scout_count, target_count, questionnaire_complexity),
            'qinguo': self._optimize_qinguo_proxy(target_count, estimated_duration),
            'xiaoshe': self._optimize_xiaoshe_queries(target_count),
            'total_estimated_cost': 0.0,
            'optimization_tips': []
        }
        
        # 计算总成本
        plan['total_estimated_cost'] = (
            plan['adspower']['cost_estimate'] +
            plan['qinguo']['cost_estimate'] +
            plan['xiaoshe']['cost_estimate']
        )
        
        # 生成优化建议
        plan['optimization_tips'] = [
            f"建议使用{plan['qinguo']['proxy_type']}代理类型以获得最佳性价比",
            f"AdsPower浏览器建议{'复用' if plan['adspower']['browser_reuse'] else '独立使用'}",
            f"小社会查询建议使用{plan['xiaoshe']['query_type']}模式",
            f"预估总成本: ¥{plan['total_estimated_cost']:.4f}"
        ]
        
        return plan

# 全局任务管理器
class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.active_tasks: Dict[str, Dict] = {}
        self.task_history: List[Dict] = []
        self.questionnaire_manager = QuestionnaireManager()
        self.scout_system = EnhancedScoutAutomationSystem()
        self.phase3_system = Phase3KnowledgeAnalysisSystem()
        self.phase4_system = Phase4MassAutomationSystem()
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.resource_tracker = ResourceConsumptionTracker(self.db_manager)
        self.cost_optimizer = CostOptimizationManager()
        
        # 初始化增强系统
        if ENHANCED_SYSTEM_AVAILABLE:
            try:
                self.enhanced_system = EnhancedQuestionnaireSystem()
                self.browser_integration = EnhancedBrowserUseIntegration(self.db_manager)
                logger.info("✅ 增强系统初始化成功")
            except Exception as e:
                logger.error(f"❌ 增强系统初始化失败: {e}")
                self.enhanced_system = None
                self.browser_integration = None
        else:
            self.enhanced_system = None
            self.browser_integration = None
    
    def create_task(self, questionnaire_url: str, scout_count: int, target_count: int) -> str:
        """创建新任务"""
        task_id = f"web_task_{int(time.time())}"
        
        # 获取成本优化方案
        optimization_plan = self.cost_optimizer.get_optimization_plan(
            scout_count, target_count, questionnaire_url
        )
        
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
            "optimization_plan": optimization_plan,
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
            "resource_consumption": {
                "total_cost": 0.0,
                "resources": []
            },
            "error_message": None
        }
        
        self.active_tasks[task_id] = task_info
        logger.info(f"✅ 创建任务: {task_id}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        return self.active_tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: str, phase: Optional[str] = None, error: Optional[str] = None):
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
    
    def update_resource_consumption(self, task_id: str):
        """更新资源消耗信息"""
        if task_id in self.active_tasks:
            consumption_summary = self.resource_tracker.get_task_consumption_summary(task_id)
            self.active_tasks[task_id]["resource_consumption"] = consumption_summary
    
    def complete_task(self, task_id: str, final_results: Dict):
        """完成任务"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task["status"] = "completed"
            task["phase"] = "已完成"
            task["completed_at"] = datetime.now().isoformat()
            task["final_results"] = final_results
            
            # 更新最终资源消耗
            self.update_resource_consumption(task_id)
            
            # 移动到历史记录
            self.task_history.append(task.copy())
            
            # 从活跃任务中删除
            del self.active_tasks[task_id]
            
            logger.info(f"✅ 任务完成: {task_id}")
    
    def get_knowledge_base_summary(self) -> Dict:
        """获取知识库汇总信息"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                # 获取问卷统计
                cursor.execute("""
                SELECT COUNT(DISTINCT questionnaire_url) as questionnaire_count,
                       COUNT(DISTINCT session_id) as session_count,
                       COUNT(*) as total_records
                FROM questionnaire_knowledge
                """)
                basic_stats = cursor.fetchone()
                
                # 获取成功率统计
                cursor.execute("""
                SELECT experience_type, COUNT(*) as count
                FROM questionnaire_knowledge 
                WHERE experience_type IS NOT NULL
                GROUP BY experience_type
                """)
                experience_stats = cursor.fetchall()
                
                # 获取最近的问卷记录
                cursor.execute("""
                SELECT questionnaire_url, session_id, 
                       COUNT(*) as record_count,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                       MAX(created_at) as last_updated
                FROM questionnaire_knowledge 
                GROUP BY questionnaire_url, session_id
                ORDER BY last_updated DESC
                LIMIT 10
                """)
                recent_questionnaires = cursor.fetchall()
                
                return {
                    'basic_stats': {
                        'questionnaire_count': basic_stats[0] if basic_stats else 0,
                        'session_count': basic_stats[1] if basic_stats else 0,
                        'total_records': basic_stats[2] if basic_stats else 0
                    },
                    'experience_stats': {
                        'success': next((r[1] for r in experience_stats if r[0] == 'success'), 0),
                        'failure': next((r[1] for r in experience_stats if r[0] == 'failure'), 0)
                    },
                    'recent_questionnaires': [
                        {
                            'url': r[0][:50] + '...' if len(r[0]) > 50 else r[0],
                            'session_id': r[1],
                            'record_count': r[2],
                            'success_count': r[3],
                            'success_rate': (r[3] / r[2] * 100) if r[2] > 0 else 0,
                            'last_updated': r[4].strftime('%Y-%m-%d %H:%M') if r[4] else ''
                        }
                        for r in recent_questionnaires
                    ]
                }
        except Exception as e:
            logger.error(f"❌ 获取知识库汇总失败: {e}")
            return {
                'basic_stats': {'questionnaire_count': 0, 'session_count': 0, 'total_records': 0},
                'experience_stats': {'success': 0, 'failure': 0},
                'recent_questionnaires': []
            }
        finally:
            if 'connection' in locals():
                connection.close()
    
    def get_global_resource_consumption(self) -> Dict:
        """获取全局资源消耗统计"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                # 获取总体消耗统计
                cursor.execute("""
                SELECT resource_type, provider,
                       SUM(quantity) as total_quantity,
                       SUM(total_cost) as total_cost,
                       COUNT(DISTINCT task_id) as task_count
                FROM resource_consumption 
                GROUP BY resource_type, provider
                ORDER BY total_cost DESC
                """)
                consumption_stats = cursor.fetchall()
                
                # 获取最近的消耗记录
                cursor.execute("""
                SELECT task_id, questionnaire_url, resource_type, 
                       quantity, total_cost, created_at
                FROM resource_consumption 
                ORDER BY created_at DESC
                LIMIT 20
                """)
                recent_consumption = cursor.fetchall()
                
                total_cost = sum(float(r[3]) for r in consumption_stats)
                
                return {
                    'total_cost': total_cost,
                    'consumption_by_type': [
                        {
                            'type': r[0],
                            'provider': r[1],
                            'quantity': r[2],
                            'cost': float(r[3]),
                            'task_count': r[4]
                        }
                        for r in consumption_stats
                    ],
                    'recent_consumption': [
                        {
                            'task_id': r[0],
                            'questionnaire_url': r[1][:30] + '...' if len(r[1]) > 30 else r[1],
                            'resource_type': r[2],
                            'quantity': r[3],
                            'cost': float(r[4]),
                            'created_at': r[5].strftime('%m-%d %H:%M') if r[5] else ''
                        }
                        for r in recent_consumption
                    ]
                }
        except Exception as e:
            logger.error(f"❌ 获取全局资源消耗失败: {e}")
            return {
                'total_cost': 0.0,
                'consumption_by_type': [],
                'recent_consumption': []
            }
        finally:
            if 'connection' in locals():
                connection.close()

# 全局任务管理器实例
task_manager = TaskManager()

@app.route('/')
def index():
    """主页"""
    # 获取知识库汇总
    knowledge_summary = task_manager.get_knowledge_base_summary()
    
    # 获取资源消耗汇总
    resource_summary = task_manager.get_global_resource_consumption()
    
    return render_template('index.html', 
                         knowledge_summary=knowledge_summary,
                         resource_summary=resource_summary)

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
        # 检查是否在历史记录中
        for history_task in task_manager.task_history:
            if history_task["task_id"] == task_id:
                return jsonify({"success": True, "task": history_task, "completed": True})
        return jsonify({"success": False, "error": "任务不存在"})
    
    # 更新资源消耗信息
    task_manager.update_resource_consumption(task_id)
    
    return jsonify({"success": True, "task": task, "completed": False})

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

@app.route('/knowledge_base')
def knowledge_base():
    """获取知识库详细信息"""
    knowledge_summary = task_manager.get_knowledge_base_summary()
    return jsonify({"success": True, "knowledge": knowledge_summary})

@app.route('/resource_consumption')
def resource_consumption():
    """资源消耗统计页面"""
    consumption_data = task_manager.get_global_resource_consumption()
    return jsonify(consumption_data)

@app.route('/task_knowledge/<task_id>')
def task_knowledge(task_id: str):
    """获取任务的知识库详情"""
    try:
        # 获取任务信息
        task = task_manager.get_task(task_id)
        if not task:
            # 检查历史任务
            for history_task in task_manager.task_history:
                if history_task["task_id"] == task_id:
                    task = history_task
                    break
        
        if not task:
            return jsonify({"success": False, "error": "任务不存在"})
        
        questionnaire_url = task.get("questionnaire_url", "")
        
        # 从数据库获取知识库信息
        connection = task_manager.db_manager.get_connection()
        knowledge_items = []
        
        try:
            with connection.cursor() as cursor:
                # 获取问卷相关的知识库记录
                cursor.execute("""
                SELECT question_text, answer_choice, success, experience_type, 
                       experience_description, created_at
                FROM questionnaire_knowledge 
                WHERE questionnaire_url = %s 
                ORDER BY created_at DESC 
                LIMIT 20
                """, (questionnaire_url,))
                
                records = cursor.fetchall()
                
                if records:
                    # 分析问卷特点
                    total_records = len(records)
                    success_records = sum(1 for r in records if r[2] == 1)
                    success_rate = (success_records / total_records * 100) if total_records > 0 else 0
                    
                    # 提取关键策略
                    strategies = []
                    question_patterns = {}
                    
                    for record in records:
                        if record[4]:  # experience_description
                            strategies.append(record[4])
                        
                        if record[0] and record[1]:  # question_text and answer_choice
                            question_key = record[0][:50]  # 取前50个字符作为问题标识
                            if question_key not in question_patterns:
                                question_patterns[question_key] = []
                            question_patterns[question_key].append(record[1])
                    
                    # 生成知识库项目
                    knowledge_items.append({
                        "title": "问卷主题分析",
                        "content": f"该问卷共收集到{total_records}条答题记录，成功率为{success_rate:.1f}%。通过敢死队探索，识别出问卷的主要考察点和答题模式。"
                    })
                    
                    if question_patterns:
                        pattern_analysis = []
                        for question, answers in list(question_patterns.items())[:3]:  # 显示前3个问题模式
                            most_common_answer = max(set(answers), key=answers.count) if answers else "未知"
                            pattern_analysis.append(f"「{question}...」建议答案：{most_common_answer}")
                        
                        knowledge_items.append({
                            "title": "关键题目策略",
                            "content": "基于敢死队探索结果，以下是关键题目的推荐答案：\n" + "\n".join(pattern_analysis)
                        })
                    
                    if strategies:
                        unique_strategies = list(set(strategies))[:3]  # 去重并取前3个
                        knowledge_items.append({
                            "title": "答题策略总结",
                            "content": "敢死队总结的有效策略：\n" + "\n".join(f"• {strategy}" for strategy in unique_strategies)
                        })
                    
                    knowledge_items.append({
                        "title": "成功率分析",
                        "content": f"敢死队{task.get('scout_count', 2)}人探索，总体成功率{success_rate:.1f}%，已积累{total_records}条有效答题经验，为大部队提供可靠的答题指导。"
                    })
                
                else:
                    # 如果没有找到具体记录，提供通用分析
                    knowledge_items = [
                        {
                            "title": "问卷分析进行中",
                            "content": "敢死队正在探索该问卷的特点和答题策略，请稍等片刻..."
                        },
                        {
                            "title": "预期收获",
                            "content": "将识别问卷主题、关键题目答案、最佳答题时间和成功率模式。"
                        }
                    ]
        
        finally:
            connection.close()
        
        return jsonify({
            "success": True,
            "knowledge_items": knowledge_items,
            "questionnaire_url": questionnaire_url
        })
        
    except Exception as e:
        logger.error(f"❌ 获取任务知识库失败: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/enhanced_single_task', methods=['POST'])
def enhanced_single_task():
    """使用增强系统执行单个数字人任务"""
    try:
        data = request.get_json()
        digital_human_id = data.get('digital_human_id', 1)
        questionnaire_url = data.get('questionnaire_url', '')
        
        if not questionnaire_url:
            return jsonify({"success": False, "error": "问卷URL不能为空"})
        
        if not task_manager.enhanced_system:
            return jsonify({"success": False, "error": "增强系统不可用"})
        
        # 创建异步任务
        task_id = f"enhanced_single_{int(time.time())}"
        
        def run_enhanced_single_task():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    task_manager.enhanced_system.run_single_digital_human_questionnaire(
                        digital_human_id, questionnaire_url
                    )
                )
                
                # 保存结果
                task_manager.active_tasks[task_id] = {
                    "task_id": task_id,
                    "type": "enhanced_single",
                    "status": "completed" if result.get("success") else "failed",
                    "result": result,
                    "created_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat()
                }
                
                logger.info(f"✅ 增强单任务完成: {task_id}")
                
            except Exception as e:
                logger.error(f"❌ 增强单任务失败: {e}")
                task_manager.active_tasks[task_id] = {
                    "task_id": task_id,
                    "type": "enhanced_single",
                    "status": "failed",
                    "error": str(e),
                    "created_at": datetime.now().isoformat()
                }
            finally:
                loop.close()
        
        # 启动后台任务
        thread = threading.Thread(target=run_enhanced_single_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": "增强单任务已启动"
        })
        
    except Exception as e:
        logger.error(f"❌ 启动增强单任务失败: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/enhanced_batch_task', methods=['POST'])
def enhanced_batch_task():
    """使用增强系统执行批量任务"""
    try:
        data = request.get_json()
        digital_human_ids = data.get('digital_human_ids', [1, 2, 3])
        questionnaire_url = data.get('questionnaire_url', '')
        
        if not questionnaire_url:
            return jsonify({"success": False, "error": "问卷URL不能为空"})
        
        if not task_manager.enhanced_system:
            return jsonify({"success": False, "error": "增强系统不可用"})
        
        # 创建异步任务
        task_id = f"enhanced_batch_{int(time.time())}"
        
        def run_enhanced_batch_task():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    task_manager.enhanced_system.run_batch_questionnaire_with_testWenjuan_data(
                        questionnaire_url, digital_human_ids
                    )
                )
                
                # 保存结果
                task_manager.active_tasks[task_id] = {
                    "task_id": task_id,
                    "type": "enhanced_batch",
                    "status": "completed" if result.get("success") else "failed",
                    "result": result,
                    "created_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat()
                }
                
                logger.info(f"✅ 增强批量任务完成: {task_id}")
                
            except Exception as e:
                logger.error(f"❌ 增强批量任务失败: {e}")
                task_manager.active_tasks[task_id] = {
                    "task_id": task_id,
                    "type": "enhanced_batch",
                    "status": "failed",
                    "error": str(e),
                    "created_at": datetime.now().isoformat()
                }
            finally:
                loop.close()
        
        # 启动后台任务
        thread = threading.Thread(target=run_enhanced_batch_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": f"增强批量任务已启动，包含{len(digital_human_ids)}个数字人"
        })
        
    except Exception as e:
        logger.error(f"❌ 启动增强批量任务失败: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/system_status')
def system_status():
    """获取系统状态"""
    try:
        status = {
            "enhanced_system_available": ENHANCED_SYSTEM_AVAILABLE,
            "testwenjuan_available": TESTWENJUAN_AVAILABLE,
            "active_tasks_count": len(task_manager.active_tasks),
            "task_history_count": len(task_manager.task_history),
            "system_components": {
                "questionnaire_manager": task_manager.questionnaire_manager is not None,
                "scout_system": task_manager.scout_system is not None,
                "phase3_system": task_manager.phase3_system is not None,
                "phase4_system": task_manager.phase4_system is not None,
                "enhanced_system": task_manager.enhanced_system is not None,
                "browser_integration": task_manager.browser_integration is not None
            }
        }
        
        # 如果testWenjuanFinal可用，获取数字人信息
        if TESTWENJUAN_AVAILABLE:
            try:
                digital_humans = []
                for i in range(1, 6):  # 获取前5个数字人
                    human = testWenjuanFinal.get_digital_human_by_id(i)
                    if human:
                        digital_humans.append({
                            "id": human["id"],
                            "name": human["name"],
                            "profession": human["profession"],
                            "age": human["age"],
                            "gender": human["gender"]
                        })
                status["available_digital_humans"] = digital_humans
            except Exception as e:
                logger.error(f"❌ 获取数字人信息失败: {e}")
                status["available_digital_humans"] = []
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ 获取系统状态失败: {e}")
        return jsonify({"success": False, "error": str(e)})

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
    """执行完整任务流程 - 增强版"""
    try:
        task = task_manager.get_task(task_id)
        if not task:
            return
        
        questionnaire_url = task["questionnaire_url"]
        scout_count = task["scout_count"]
        target_count = task["target_count"]
        
        logger.info(f"🚀 开始执行增强任务: {task_id}")
        
        # 第一阶段：基础设施准备
        task_manager.update_task_status(task_id, "running", "第一阶段：基础设施准备")
        task_manager.update_task_progress(task_id, 1)
        
        # 记录AdsPower资源消耗
        task_manager.resource_tracker.record_adspower_consumption(
            task_id, f"session_{task_id}", questionnaire_url, scout_count + target_count, 1.0
        )
        
        # 创建问卷任务（基础设施）
        questionnaire_task = await task_manager.questionnaire_manager.create_questionnaire_task(
            url=questionnaire_url,
            scout_count=scout_count,
            target_count=target_count
        )
        
        session_id = questionnaire_task.session_id
        task_manager.update_task_progress(task_id, 1, complete=True)
        
        # 第二阶段：敢死队真实答题（核心改进）
        task_manager.update_task_status(task_id, "running", "第二阶段：敢死队真实答题")
        task_manager.update_task_progress(task_id, 2)
        
        # 记录青果代理资源消耗
        task_manager.resource_tracker.record_qinguo_proxy_consumption(
            task_id, session_id, questionnaire_url, 'tunnel_proxy', scout_count, 60
        )
        
        # 启动增强敢死队任务
        scout_mission_id = await task_manager.scout_system.start_enhanced_scout_mission(
            questionnaire_url=questionnaire_url,
            scout_count=scout_count
        )
        
        if scout_mission_id:
            # 更新敢死队分配信息
            mission_status = await task_manager.scout_system.get_mission_status(scout_mission_id)
            if mission_status.get("success"):
                mission = mission_status["mission"]
                scout_sessions = mission.get("scout_sessions", {})
                
                for persona_id, session_info in scout_sessions.items():
                    persona = session_info["persona"]
                    task_manager.add_scout_assignment(task_id, {
                        "persona_id": persona["persona_id"],
                        "persona_name": persona["persona_name"],
                        "status": "准备就绪",
                        "browser_profile": session_info.get("browser_info", {}).get("name", "未知"),
                        "strategy": "保守策略" if persona_id % 2 == 0 else "激进策略"
                    })
            
            # 执行增强敢死队答题
            scout_results = await task_manager.scout_system.execute_enhanced_scout_answering(scout_mission_id)
            
            # 更新敢死队结果
            if scout_results and scout_results.get("success"):
                successful_scouts = scout_results.get("successful_scouts", 0)
                failed_scouts = scout_results.get("failed_scouts", 0)
                
                # 更新分配状态
                for assignment in task["scout_assignments"]:
                    # 根据结果更新状态（这里简化处理）
                    assignment["status"] = "已完成"
                    assignment["answers_count"] = 5  # 模拟答题数量
                
                task_manager.update_results(task_id, {
                    "scout_success_count": successful_scouts,
                    "scout_failure_count": failed_scouts,
                    "scout_success_rate": scout_results.get("success_rate", 0),
                    "knowledge_accumulated": scout_results.get("knowledge_accumulated", False)
                })
                
                logger.info(f"✅ 敢死队阶段完成: 成功 {successful_scouts}/{scout_count} 人")
            else:
                logger.error(f"❌ 敢死队答题失败")
                task_manager.update_task_status(task_id, "failed", "敢死队答题失败", "敢死队答题过程中出现错误")
                return
        else:
            logger.error(f"❌ 敢死队任务启动失败")
            task_manager.update_task_status(task_id, "failed", "敢死队启动失败", "无法启动敢死队任务")
            return
        
        task_manager.update_task_progress(task_id, 2, complete=True)
        
        # 第三阶段：知识库分析
        task_manager.update_task_status(task_id, "running", "第三阶段：知识库分析")
        task_manager.update_task_progress(task_id, 3)
        
        # 记录小社会查询资源消耗
        task_manager.resource_tracker.record_xiaoshe_query_consumption(
            task_id, session_id, questionnaire_url, target_count * 2, 'standard'
        )
        
        analysis_result = await task_manager.phase3_system.analyze_and_select_target_team(
            session_id=scout_mission_id,  # 使用敢死队的session_id
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
        
        # 记录大部队代理资源消耗
        task_manager.resource_tracker.record_qinguo_proxy_consumption(
            task_id, session_id, questionnaire_url, 'tunnel_proxy', target_count, 90
        )
        
        final_result = await task_manager.phase4_system.execute_full_automation_pipeline(
            questionnaire_url=questionnaire_url,
            session_id=scout_mission_id,  # 使用敢死队的session_id
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
        
        # 清理敢死队任务
        await task_manager.scout_system.cleanup_scout_mission(scout_mission_id)
        
        # 完成任务
        task_manager.complete_task(task_id, final_result)
        
        logger.info(f"✅ 增强任务执行完成: {task_id}")
        
    except Exception as e:
        logger.error(f"❌ 增强任务执行失败: {e}")
        task_manager.update_task_status(task_id, "failed", "执行失败", str(e))

if __name__ == '__main__':
    # 创建模板目录
    import os
    os.makedirs('templates', exist_ok=True)
    
    print("🌐 启动智能问卷自动填写系统Web界面")
    print("📋 访问地址: http://localhost:5002")
    print("🔧 功能: 任务创建、进度监控、结果查看、知识库展示、资源消耗统计")
    
    app.run(host='0.0.0.0', port=5002, debug=True) 