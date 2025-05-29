#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复后的浏览器集成系统
验证所有核心功能是否正常工作
"""

import asyncio
import json
import time
import logging
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from questionnaire_system import DatabaseManager, DB_CONFIG
from enhanced_browser_use_integration import EnhancedBrowserUseIntegration

logger = logging.getLogger(__name__)

class BrowserIntegrationTester:
    """浏览器集成测试器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.browser_integration = EnhancedBrowserUseIntegration(self.db_manager)
        self.test_results = []
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🧪 开始测试修复后的浏览器集成...")
        
        # 测试1: 数据库连接
        await self.test_database_connection()
        
        # 测试2: 浏览器会话创建
        await self.test_browser_session_creation()
        
        # 测试3: 页面导航
        await self.test_page_navigation()
        
        # 测试4: 问卷答题模拟
        await self.test_questionnaire_answering()
        
        # 测试5: 知识库操作
        await self.test_knowledge_base_operations()
        
        # 输出测试结果
        self.print_test_results()
    
    async def test_database_connection(self):
        """测试数据库连接"""
        try:
            logger.info("📊 测试1: 数据库连接...")
            
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            connection.close()
            
            if result and result[0] == 1:
                self.test_results.append(("数据库连接", True, "连接成功"))
                logger.info("   ✅ 数据库连接正常")
            else:
                self.test_results.append(("数据库连接", False, "连接失败"))
                logger.error("   ❌ 数据库连接失败")
                
        except Exception as e:
            self.test_results.append(("数据库连接", False, str(e)))
            logger.error(f"   ❌ 数据库连接异常: {e}")
    
    async def test_browser_session_creation(self):
        """测试浏览器会话创建"""
        try:
            logger.info("🌐 测试2: 浏览器会话创建...")
            
            # 准备测试数据
            persona_info = {
                "persona_id": 999,
                "persona_name": "测试数字人",
                "name": "测试数字人",
                "age": 25,
                "gender": "男"
            }
            
            browser_config = {
                "headless": False,
                "args": ["--no-sandbox", "--disable-dev-shm-usage"],
                "user_data_dir": "/tmp/test_browser_profile"
            }
            
            # 创建会话
            session_id = await self.browser_integration.create_browser_session(persona_info, browser_config)
            
            if session_id and session_id in self.browser_integration.active_sessions:
                session = self.browser_integration.active_sessions[session_id]
                status = session.get("status", "unknown")
                
                self.test_results.append(("浏览器会话创建", True, f"会话ID: {session_id}, 状态: {status}"))
                logger.info(f"   ✅ 浏览器会话创建成功: {session_id} (状态: {status})")
                
                # 保存session_id供后续测试使用
                self.test_session_id = session_id
                
            else:
                self.test_results.append(("浏览器会话创建", False, "会话创建失败"))
                logger.error("   ❌ 浏览器会话创建失败")
                
        except Exception as e:
            self.test_results.append(("浏览器会话创建", False, str(e)))
            logger.error(f"   ❌ 浏览器会话创建异常: {e}")
    
    async def test_page_navigation(self):
        """测试页面导航"""
        try:
            logger.info("🧭 测试3: 页面导航...")
            
            if not hasattr(self, 'test_session_id'):
                self.test_results.append(("页面导航", False, "没有可用的会话"))
                logger.error("   ❌ 没有可用的会话进行导航测试")
                return
            
            # 测试导航到问卷页面
            test_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"
            task_id = f"test_task_{int(time.time())}"
            
            result = await self.browser_integration.navigate_and_analyze_questionnaire(
                self.test_session_id, test_url, task_id
            )
            
            if result.get("success"):
                page_data = result.get("page_data", {})
                page_title = page_data.get("page_title", "未知")
                
                self.test_results.append(("页面导航", True, f"成功导航到: {page_title}"))
                logger.info(f"   ✅ 页面导航成功: {page_title}")
                
                # 保存task_id供后续测试使用
                self.test_task_id = task_id
                
            else:
                error = result.get("error", "未知错误")
                self.test_results.append(("页面导航", False, error))
                logger.error(f"   ❌ 页面导航失败: {error}")
                
        except Exception as e:
            self.test_results.append(("页面导航", False, str(e)))
            logger.error(f"   ❌ 页面导航异常: {e}")
    
    async def test_questionnaire_answering(self):
        """测试问卷答题模拟"""
        try:
            logger.info("📝 测试4: 问卷答题模拟...")
            
            if not hasattr(self, 'test_session_id') or not hasattr(self, 'test_task_id'):
                self.test_results.append(("问卷答题", False, "没有可用的会话或任务"))
                logger.error("   ❌ 没有可用的会话或任务进行答题测试")
                return
            
            # 执行问卷答题
            result = await self.browser_integration.execute_complete_questionnaire(
                self.test_session_id, self.test_task_id, "conservative"
            )
            
            if result.get("success"):
                answered_count = result.get("successful_answers", 0)
                total_count = result.get("total_questions", 0)
                duration = result.get("duration", 0)
                
                self.test_results.append(("问卷答题", True, f"回答 {answered_count}/{total_count} 个问题，用时 {duration:.1f}s"))
                logger.info(f"   ✅ 问卷答题成功: {answered_count}/{total_count} 个问题，用时 {duration:.1f}s")
                
            else:
                error = result.get("error", "未知错误")
                self.test_results.append(("问卷答题", False, error))
                logger.error(f"   ❌ 问卷答题失败: {error}")
                
        except Exception as e:
            self.test_results.append(("问卷答题", False, str(e)))
            logger.error(f"   ❌ 问卷答题异常: {e}")
    
    async def test_knowledge_base_operations(self):
        """测试知识库操作"""
        try:
            logger.info("📚 测试5: 知识库操作...")
            
            # 测试查询知识库
            test_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"
            knowledge_items = self.browser_integration.get_questionnaire_knowledge("", test_url)
            
            if isinstance(knowledge_items, list):
                count = len(knowledge_items)
                self.test_results.append(("知识库查询", True, f"查询到 {count} 条记录"))
                logger.info(f"   ✅ 知识库查询成功: {count} 条记录")
            else:
                self.test_results.append(("知识库查询", False, "查询结果格式错误"))
                logger.error("   ❌ 知识库查询失败: 结果格式错误")
                
        except Exception as e:
            self.test_results.append(("知识库操作", False, str(e)))
            logger.error(f"   ❌ 知识库操作异常: {e}")
    
    def print_test_results(self):
        """打印测试结果"""
        print("\n" + "="*60)
        print("🧪 浏览器集成测试结果")
        print("="*60)
        
        passed_tests = 0
        total_tests = len(self.test_results)
        
        for test_name, success, message in self.test_results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{status} {test_name}: {message}")
            if success:
                passed_tests += 1
        
        print("-"*60)
        print(f"测试总结: {passed_tests}/{total_tests} 个测试通过")
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！浏览器集成系统工作正常。")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️ 大部分测试通过，系统基本可用，但有一些问题需要修复。")
        else:
            print("❌ 多个测试失败，系统需要进一步修复。")
        
        print("="*60)

async def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)
    
    tester = BrowserIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 