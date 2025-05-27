#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷填写系统 - 主架构文件
包含问卷主管、AdsPower浏览器管理、知识库管理等核心模块
"""

import asyncio
import json
import requests
import pymysql
import pymysql.cursors
import time
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    "host": "192.168.50.137",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "wenjuan",
    "charset": "utf8mb4"
}

# AdsPower API配置
ADSPOWER_CONFIG = {
    "base_url": "http://localhost:50325",  # AdsPower本地API地址
    "timeout": 30
}

# 小社会系统配置
XIAOSHE_CONFIG = {
    "base_url": "http://localhost:5001",  # 小社会系统API地址
    "timeout": 30
}

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ANALYZING = "analyzing"

class PersonaRole(Enum):
    """数字人角色枚举"""
    SCOUT = "scout"  # 敢死队
    TARGET = "target"  # 目标答题者

@dataclass
class QuestionnaireTask:
    """问卷任务数据类"""
    task_id: str
    url: str
    session_id: str
    status: TaskStatus
    scout_count: int = 2
    target_count: int = 10
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class PersonaAssignment:
    """数字人分配数据类"""
    persona_id: int
    persona_name: str
    role: PersonaRole
    browser_profile_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    assigned_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.assigned_at is None:
            self.assigned_at = datetime.now()

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def get_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**self.config)
    
    def init_knowledge_base_tables(self):
        """初始化知识库相关表"""
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                # 问卷知识库表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS questionnaire_knowledge (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    session_id VARCHAR(100) NOT NULL,
                    questionnaire_url VARCHAR(500) NOT NULL,
                    question_content TEXT,
                    question_type VARCHAR(50),
                    question_number INT,
                    answer_choice TEXT,
                    persona_id INT,
                    persona_role ENUM('scout', 'target'),
                    success BOOLEAN,
                    experience_type ENUM('success', 'failure'),
                    experience_description TEXT,
                    page_screenshot LONGBLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_session_id (session_id),
                    INDEX idx_questionnaire_url (questionnaire_url),
                    INDEX idx_persona_id (persona_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                
                # 答题记录表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS answer_records (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    session_id VARCHAR(100) NOT NULL,
                    task_id VARCHAR(100) NOT NULL,
                    questionnaire_url VARCHAR(500) NOT NULL,
                    persona_id INT NOT NULL,
                    persona_name VARCHAR(100),
                    persona_role ENUM('scout', 'target'),
                    question_number INT,
                    question_content TEXT,
                    question_options JSON,
                    answer_choice TEXT,
                    page_screenshot LONGBLOB,
                    success BOOLEAN,
                    error_message TEXT,
                    browser_profile_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_session_id (session_id),
                    INDEX idx_task_id (task_id),
                    INDEX idx_persona_id (persona_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                
                # 任务管理表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS questionnaire_tasks (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    task_id VARCHAR(100) UNIQUE NOT NULL,
                    session_id VARCHAR(100) NOT NULL,
                    questionnaire_url VARCHAR(500) NOT NULL,
                    status ENUM('pending', 'running', 'success', 'failed', 'analyzing'),
                    scout_count INT DEFAULT 2,
                    target_count INT DEFAULT 10,
                    scout_completed INT DEFAULT 0,
                    target_completed INT DEFAULT 0,
                    success_rate DECIMAL(5,2),
                    analysis_result JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_task_id (task_id),
                    INDEX idx_session_id (session_id),
                    INDEX idx_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                
                # 数字人分配表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS persona_assignments (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    task_id VARCHAR(100) NOT NULL,
                    session_id VARCHAR(100) NOT NULL,
                    persona_id INT NOT NULL,
                    persona_name VARCHAR(100),
                    persona_role ENUM('scout', 'target'),
                    browser_profile_id VARCHAR(100),
                    status ENUM('pending', 'running', 'success', 'failed'),
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    INDEX idx_task_id (task_id),
                    INDEX idx_persona_id (persona_id),
                    INDEX idx_browser_profile_id (browser_profile_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                
                connection.commit()
                logger.info("✅ 知识库表初始化完成")
                
        except Exception as e:
            logger.error(f"❌ 初始化知识库表失败: {e}")
            raise
        finally:
            if 'connection' in locals():
                connection.close()

class AdsPowerManager:
    """AdsPower浏览器管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config["base_url"]
        self.timeout = config.get("timeout", 30)
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """发送API请求"""
        url = f"{self.base_url}/api/v1{endpoint}"
        
        # 添加API Key到请求头
        headers = {}
        if "api_key" in self.config:
            headers["Authorization"] = f"Bearer {self.config['api_key']}"
        
        try:
            if method.upper() == "GET":
                # 将API Key添加到查询参数中（AdsPower的要求）
                if data is None:
                    data = {}
                if "api_key" in self.config:
                    data["api_key"] = self.config["api_key"]
                response = requests.get(url, params=data, headers=headers, timeout=self.timeout)
            else:
                # 将API Key添加到请求体中
                if data is None:
                    data = {}
                if "api_key" in self.config:
                    data["api_key"] = self.config["api_key"]
                response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"AdsPower API请求失败: {e}")
            raise
    
    async def create_browser_profile(self, persona_id: int, persona_name: str) -> str:
        """为数字人创建独立的浏览器配置文件"""
        try:
            profile_config = {
                "name": f"persona_{persona_id}_{persona_name}",
                "group_id": "0",  # 默认分组
                "remark": f"数字人{persona_name}的专用浏览器环境",
                "user_proxy_config": {
                    "proxy_soft": "no_proxy",
                    "proxy_type": "noproxy"
                }
            }
            
            result = self._make_request("POST", "/user/create", profile_config)
            
            if result.get("code") == 0:
                profile_id = result["data"]["id"]
                logger.info(f"✅ 为数字人 {persona_name}(ID:{persona_id}) 创建浏览器配置文件: {profile_id}")
                return profile_id
            else:
                raise Exception(f"创建配置文件失败: {result.get('msg', '未知错误')}")
                
        except Exception as e:
            logger.error(f"❌ 创建浏览器配置文件失败: {e}")
            raise
    
    async def start_browser(self, profile_id: str) -> Dict:
        """启动浏览器实例"""
        try:
            result = self._make_request("GET", "/browser/start", {"user_id": profile_id})
            
            if result.get("code") == 0:
                browser_info = result["data"]
                logger.info(f"✅ 启动浏览器成功: {profile_id}, 调试端口: {browser_info.get('ws', {}).get('selenium')}")
                return browser_info
            else:
                raise Exception(f"启动浏览器失败: {result.get('msg', '未知错误')}")
                
        except Exception as e:
            logger.error(f"❌ 启动浏览器失败: {e}")
            raise
    
    async def stop_browser(self, profile_id: str) -> bool:
        """停止浏览器实例"""
        try:
            result = self._make_request("GET", "/browser/stop", {"user_id": profile_id})
            
            if result.get("code") == 0:
                logger.info(f"✅ 停止浏览器成功: {profile_id}")
                return True
            else:
                logger.warning(f"停止浏览器失败: {result.get('msg', '未知错误')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 停止浏览器失败: {e}")
            return False
    
    async def delete_browser_profile(self, profile_id: str) -> bool:
        """删除浏览器配置文件"""
        try:
            result = self._make_request("POST", "/user/delete", {"user_ids": [profile_id]})
            
            if result.get("code") == 0:
                logger.info(f"✅ 删除浏览器配置文件成功: {profile_id}")
                return True
            else:
                logger.warning(f"删除配置文件失败: {result.get('msg', '未知错误')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 删除浏览器配置文件失败: {e}")
            return False

class XiaosheSystemClient:
    """小社会系统客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config["base_url"]
        self.timeout = config.get("timeout", 30)
    
    async def query_personas(self, query: str, limit: int = 10) -> List[Dict]:
        """查询数字人"""
        try:
            url = f"{self.base_url}/api/smart-query/query"
            data = {
                "query": query,
                "limit": limit
            }
            
            response = requests.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                personas = result.get("personas", [])
                logger.info(f"✅ 查询到 {len(personas)} 个符合条件的数字人")
                return personas
            else:
                logger.warning(f"查询数字人失败: {result.get('error', '未知错误')}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 查询小社会系统失败: {e}")
            return []

class QuestionnaireKnowledgeBase:
    """问卷知识库管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_question_content(self, session_id: str, questionnaire_url: str, 
                            question_content: str, question_type: str, 
                            question_number: int, persona_id: int, 
                            persona_role: PersonaRole) -> bool:
        """保存题目内容"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO questionnaire_knowledge 
                (session_id, questionnaire_url, question_content, question_type, 
                 question_number, persona_id, persona_role)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (session_id, questionnaire_url, question_content, 
                                   question_type, question_number, persona_id, persona_role.value))
                connection.commit()
                logger.info(f"✅ 保存题目内容: 第{question_number}题")
                return True
                
        except Exception as e:
            logger.error(f"❌ 保存题目内容失败: {e}")
            return False
        finally:
            if 'connection' in locals():
                connection.close()
    
    def save_answer_experience(self, session_id: str, questionnaire_url: str,
                             persona_id: int, answer_choice: str, success: bool,
                             experience_description: str) -> bool:
        """保存答题经验"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                experience_type = "success" if success else "failure"
                sql = """
                UPDATE questionnaire_knowledge 
                SET answer_choice = %s, success = %s, experience_type = %s, 
                    experience_description = %s
                WHERE session_id = %s AND questionnaire_url = %s AND persona_id = %s
                ORDER BY created_at DESC LIMIT 1
                """
                cursor.execute(sql, (answer_choice, success, experience_type, 
                                   experience_description, session_id, questionnaire_url, persona_id))
                connection.commit()
                logger.info(f"✅ 保存答题经验: {'成功' if success else '失败'}")
                return True
                
        except Exception as e:
            logger.error(f"❌ 保存答题经验失败: {e}")
            return False
        finally:
            if 'connection' in locals():
                connection.close()
    
    def get_success_experiences(self, session_id: str, questionnaire_url: str) -> List[Dict]:
        """获取成功经验"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT * FROM questionnaire_knowledge 
                WHERE session_id = %s AND questionnaire_url = %s 
                AND experience_type = 'success'
                ORDER BY question_number
                """
                cursor.execute(sql, (session_id, questionnaire_url))
                results = cursor.fetchall()
                logger.info(f"✅ 获取到 {len(results)} 条成功经验")
                return list(results)
                
        except Exception as e:
            logger.error(f"❌ 获取成功经验失败: {e}")
            return []
        finally:
            if 'connection' in locals():
                connection.close()
    
    def analyze_questionnaire_requirements(self, session_id: str, questionnaire_url: str) -> Dict:
        """分析问卷要求，提取目标人群特征"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 获取所有答题记录
                sql = """
                SELECT qk.*, dh.age, dh.gender, dh.profession, dh.birthplace_str, dh.residence_str
                FROM questionnaire_knowledge qk
                LEFT JOIN digital_humans dh ON qk.persona_id = dh.id
                WHERE qk.session_id = %s AND qk.questionnaire_url = %s
                """
                cursor.execute(sql, (session_id, questionnaire_url))
                records = cursor.fetchall()
                
                if not records:
                    return {}
                
                # 分析成功和失败的模式
                success_records = [r for r in records if r.get('success')]
                failure_records = [r for r in records if not r.get('success')]
                
                analysis = {
                    "total_questions": len(set(r['question_number'] for r in records if r['question_number'])),
                    "success_count": len(success_records),
                    "failure_count": len(failure_records),
                    "success_rate": len(success_records) / len(records) if records else 0,
                    "target_demographics": self._extract_target_demographics(success_records),
                    "common_failure_reasons": self._extract_failure_patterns(failure_records),
                    "recommended_query": self._generate_persona_query(success_records)
                }
                
                logger.info(f"✅ 问卷分析完成: 成功率 {analysis['success_rate']:.2%}")
                return analysis
                
        except Exception as e:
            logger.error(f"❌ 分析问卷要求失败: {e}")
            return {}
        finally:
            if 'connection' in locals():
                connection.close()
    
    def _extract_target_demographics(self, success_records: List[Dict]) -> Dict:
        """提取目标人群特征"""
        if not success_records:
            return {}
        
        ages = [r['age'] for r in success_records if r.get('age')]
        genders = [r['gender'] for r in success_records if r.get('gender')]
        professions = [r['profession'] for r in success_records if r.get('profession')]
        
        return {
            "age_range": {
                "min": min(ages) if ages else None,
                "max": max(ages) if ages else None,
                "avg": sum(ages) / len(ages) if ages else None
            },
            "preferred_genders": list(set(genders)),
            "preferred_professions": list(set(professions)),
            "sample_size": len(success_records)
        }
    
    def _extract_failure_patterns(self, failure_records: List[Dict]) -> List[str]:
        """提取失败模式"""
        patterns = []
        for record in failure_records:
            if record.get('experience_description'):
                patterns.append(record['experience_description'])
        return patterns
    
    def _generate_persona_query(self, success_records: List[Dict]) -> str:
        """生成数字人查询语句"""
        if not success_records:
            return "找一些活跃的数字人来参与问卷调查"
        
        demographics = self._extract_target_demographics(success_records)
        
        query_parts = []
        
        if demographics.get("age_range", {}).get("min"):
            age_min = demographics["age_range"]["min"]
            age_max = demographics["age_range"]["max"]
            query_parts.append(f"年龄在{age_min}-{age_max}岁之间")
        
        if demographics.get("preferred_genders"):
            genders = "、".join(demographics["preferred_genders"])
            query_parts.append(f"性别为{genders}")
        
        if demographics.get("preferred_professions"):
            professions = "、".join(demographics["preferred_professions"][:3])  # 取前3个职业
            query_parts.append(f"职业包括{professions}")
        
        if query_parts:
            return f"找一些{', '.join(query_parts)}的数字人"
        else:
            return "找一些背景多样化的数字人来参与问卷调查"
    
    def cleanup_session(self, session_id: str) -> bool:
        """清理会话知识库"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                # 删除知识库记录
                cursor.execute("DELETE FROM questionnaire_knowledge WHERE session_id = %s", (session_id,))
                knowledge_deleted = cursor.rowcount
                
                # 删除答题记录
                cursor.execute("DELETE FROM answer_records WHERE session_id = %s", (session_id,))
                records_deleted = cursor.rowcount
                
                # 删除任务记录
                cursor.execute("DELETE FROM questionnaire_tasks WHERE session_id = %s", (session_id,))
                tasks_deleted = cursor.rowcount
                
                # 删除分配记录
                cursor.execute("DELETE FROM persona_assignments WHERE session_id = %s", (session_id,))
                assignments_deleted = cursor.rowcount
                
                connection.commit()
                logger.info(f"✅ 清理会话 {session_id}: 知识库{knowledge_deleted}条, 答题记录{records_deleted}条, 任务{tasks_deleted}个, 分配{assignments_deleted}个")
                return True
                
        except Exception as e:
            logger.error(f"❌ 清理会话知识库失败: {e}")
            return False
        finally:
            if 'connection' in locals():
                connection.close()

class QuestionnaireManager:
    """问卷主管 - 系统核心协调器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.adspower_manager = AdsPowerManager(ADSPOWER_CONFIG)
        self.xiaoshe_client = XiaosheSystemClient(XIAOSHE_CONFIG)
        self.knowledge_base = QuestionnaireKnowledgeBase(self.db_manager)
        
        # 初始化数据库表
        self.db_manager.init_knowledge_base_tables()
    
    async def create_questionnaire_task(self, url: str, scout_count: int = 2, target_count: int = 10) -> QuestionnaireTask:
        """创建问卷任务"""
        task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        task = QuestionnaireTask(
            task_id=task_id,
            url=url,
            session_id=session_id,
            status=TaskStatus.PENDING,
            scout_count=scout_count,
            target_count=target_count
        )
        
        # 保存任务到数据库
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO questionnaire_tasks 
                (task_id, session_id, questionnaire_url, status, scout_count, target_count)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (task.task_id, task.session_id, task.url, 
                                   task.status.value, task.scout_count, task.target_count))
                connection.commit()
                
            logger.info(f"✅ 创建问卷任务: {task.task_id}")
            return task
            
        except Exception as e:
            logger.error(f"❌ 创建问卷任务失败: {e}")
            raise
        finally:
            if 'connection' in locals():
                connection.close()
    
    async def select_scout_team(self, task: QuestionnaireTask) -> List[PersonaAssignment]:
        """选择敢死队成员"""
        logger.info(f"🔍 为任务 {task.task_id} 选择 {task.scout_count} 名敢死队成员...")
        
        # 查询多样化的数字人作为敢死队
        query = f"找{task.scout_count}个不同背景的数字人，包括不同年龄、性别、职业的人"
        personas = await self.xiaoshe_client.query_personas(query, task.scout_count * 2)
        
        if len(personas) < task.scout_count:
            raise Exception(f"找到的数字人数量不足，需要{task.scout_count}个，实际找到{len(personas)}个")
        
        # 选择前N个作为敢死队
        selected_personas = personas[:task.scout_count]
        assignments = []
        
        for persona in selected_personas:
            assignment = PersonaAssignment(
                persona_id=persona['id'],
                persona_name=persona['name'],
                role=PersonaRole.SCOUT
            )
            assignments.append(assignment)
            
            # 保存分配记录
            await self._save_persona_assignment(task, assignment)
        
        logger.info(f"✅ 选择敢死队完成: {[a.persona_name for a in assignments]}")
        return assignments
    
    async def select_target_team(self, task: QuestionnaireTask) -> List[PersonaAssignment]:
        """根据敢死队经验选择目标答题团队"""
        logger.info(f"🎯 为任务 {task.task_id} 选择目标答题团队...")
        
        # 分析问卷要求
        analysis = self.knowledge_base.analyze_questionnaire_requirements(task.session_id, task.url)
        
        if not analysis or analysis.get("success_rate", 0) == 0:
            logger.warning("敢死队未获得成功经验，使用默认策略选择目标团队")
            query = f"找{task.target_count}个活跃的数字人，背景多样化"
        else:
            query = analysis.get("recommended_query", f"找{task.target_count}个合适的数字人")
        
        personas = await self.xiaoshe_client.query_personas(query, task.target_count * 2)
        
        if len(personas) < task.target_count:
            logger.warning(f"目标数字人数量不足，需要{task.target_count}个，实际找到{len(personas)}个")
        
        # 选择数字人作为目标团队
        selected_personas = personas[:task.target_count]
        assignments = []
        
        for persona in selected_personas:
            assignment = PersonaAssignment(
                persona_id=persona['id'],
                persona_name=persona['name'],
                role=PersonaRole.TARGET
            )
            assignments.append(assignment)
            
            # 保存分配记录
            await self._save_persona_assignment(task, assignment)
        
        logger.info(f"✅ 选择目标团队完成: {len(assignments)}名数字人")
        return assignments
    
    async def _save_persona_assignment(self, task: QuestionnaireTask, assignment: PersonaAssignment):
        """保存数字人分配记录"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO persona_assignments 
                (task_id, session_id, persona_id, persona_name, persona_role, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (task.task_id, task.session_id, assignment.persona_id,
                                   assignment.persona_name, assignment.role.value, assignment.status.value))
                connection.commit()
                
        except Exception as e:
            logger.error(f"❌ 保存数字人分配记录失败: {e}")
            raise
        finally:
            if 'connection' in locals():
                connection.close()
    
    async def prepare_browser_environments(self, assignments: List[PersonaAssignment]) -> Dict[int, str]:
        """为数字人准备浏览器环境"""
        logger.info(f"🌐 为 {len(assignments)} 个数字人准备浏览器环境...")
        
        browser_profiles = {}
        
        for assignment in assignments:
            try:
                # 创建浏览器配置文件
                profile_id = await self.adspower_manager.create_browser_profile(
                    assignment.persona_id, assignment.persona_name
                )
                
                assignment.browser_profile_id = profile_id
                browser_profiles[assignment.persona_id] = profile_id
                
                # 更新分配记录
                await self._update_assignment_browser_profile(assignment)
                
            except Exception as e:
                logger.error(f"❌ 为数字人 {assignment.persona_name} 创建浏览器环境失败: {e}")
                continue
        
        logger.info(f"✅ 浏览器环境准备完成: {len(browser_profiles)} 个")
        return browser_profiles
    
    async def _update_assignment_browser_profile(self, assignment: PersonaAssignment):
        """更新分配记录的浏览器配置文件ID"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                sql = """
                UPDATE persona_assignments 
                SET browser_profile_id = %s 
                WHERE persona_id = %s AND persona_role = %s
                """
                cursor.execute(sql, (assignment.browser_profile_id, assignment.persona_id, assignment.role.value))
                connection.commit()
                
        except Exception as e:
            logger.error(f"❌ 更新浏览器配置文件ID失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()
    
    async def cleanup_task_resources(self, task: QuestionnaireTask):
        """清理任务资源"""
        logger.info(f"🧹 清理任务 {task.task_id} 的资源...")
        
        try:
            # 获取所有浏览器配置文件
            connection = self.db_manager.get_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = "SELECT browser_profile_id FROM persona_assignments WHERE task_id = %s"
                cursor.execute(sql, (task.task_id,))
                profiles = cursor.fetchall()
                
                # 停止并删除浏览器配置文件
                for profile in profiles:
                    if profile['browser_profile_id']:
                        await self.adspower_manager.stop_browser(profile['browser_profile_id'])
                        await self.adspower_manager.delete_browser_profile(profile['browser_profile_id'])
                
                # 清理知识库
                self.knowledge_base.cleanup_session(task.session_id)
                
                logger.info(f"✅ 任务资源清理完成")
                
        except Exception as e:
            logger.error(f"❌ 清理任务资源失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()

# 测试函数
async def test_system():
    """测试系统基础功能"""
    logger.info("🧪 开始测试问卷系统...")
    
    try:
        # 创建问卷主管
        manager = QuestionnaireManager()
        
        # 创建测试任务
        test_url = "https://example.com/questionnaire"
        task = await manager.create_questionnaire_task(test_url, scout_count=2, target_count=5)
        
        logger.info(f"✅ 测试任务创建成功: {task.task_id}")
        
        # 测试选择敢死队（注意：需要小社会系统运行）
        try:
            scout_team = await manager.select_scout_team(task)
            logger.info(f"✅ 敢死队选择测试成功: {len(scout_team)} 名成员")
        except Exception as e:
            logger.warning(f"⚠️ 敢死队选择测试失败（可能是小社会系统未运行）: {e}")
        
        # 测试浏览器环境准备（注意：需要AdsPower运行）
        try:
            if 'scout_team' in locals():
                browser_profiles = await manager.prepare_browser_environments(scout_team[:1])  # 只测试1个
                logger.info(f"✅ 浏览器环境测试成功: {len(browser_profiles)} 个配置文件")
        except Exception as e:
            logger.warning(f"⚠️ 浏览器环境测试失败（可能是AdsPower未运行）: {e}")
        
        # 清理测试资源
        await manager.cleanup_task_resources(task)
        logger.info("✅ 测试完成，资源已清理")
        
    except Exception as e:
        logger.error(f"❌ 系统测试失败: {e}")
        raise

if __name__ == "__main__":
    print("🚀 智能问卷填写系统 - 基础架构")
    print("=" * 50)
    
    # 运行测试
    asyncio.run(test_system()) 