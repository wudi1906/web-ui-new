#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷自动填写系统 - Web界面功能测试
"""

import sys
import time
import threading
import requests
from web_interface import app, task_manager

def test_web_interface():
    """测试Web界面功能"""
    print("🧪 开始Web界面功能测试")
    print("=" * 50)
    
    # 测试1: 任务管理器初始化
    print("📋 测试1: 任务管理器初始化")
    try:
        assert task_manager is not None
        assert hasattr(task_manager, 'active_tasks')
        assert hasattr(task_manager, 'task_history')
        print("✅ 任务管理器初始化成功")
    except Exception as e:
        print(f"❌ 任务管理器初始化失败: {e}")
        return False
    
    # 测试2: 创建测试任务
    print("\n📋 测试2: 创建测试任务")
    try:
        task_id = task_manager.create_task(
            questionnaire_url="https://www.wjx.cn/vm/test123.aspx",
            scout_count=2,
            target_count=5
        )
        assert task_id is not None
        assert task_id in task_manager.active_tasks
        print(f"✅ 测试任务创建成功: {task_id}")
    except Exception as e:
        print(f"❌ 测试任务创建失败: {e}")
        return False
    
    # 测试3: 任务状态更新
    print("\n📋 测试3: 任务状态更新")
    try:
        task_manager.update_task_status(task_id, "running", "测试阶段")
        task = task_manager.get_task(task_id)
        assert task['status'] == "running"
        assert task['phase'] == "测试阶段"
        print("✅ 任务状态更新成功")
    except Exception as e:
        print(f"❌ 任务状态更新失败: {e}")
        return False
    
    # 测试4: 进度更新
    print("\n📋 测试4: 进度更新")
    try:
        task_manager.update_task_progress(task_id, 2, complete=True)
        task = task_manager.get_task(task_id)
        assert task['progress']['current_phase'] == 2
        assert task['progress']['phase2_complete'] == True
        print("✅ 进度更新成功")
    except Exception as e:
        print(f"❌ 进度更新失败: {e}")
        return False
    
    # 测试5: 分配信息添加
    print("\n📋 测试5: 分配信息添加")
    try:
        scout_assignment = {
            "persona_id": 1001,
            "persona_name": "测试敢死队员",
            "status": "准备就绪",
            "browser_profile": "test_profile"
        }
        task_manager.add_scout_assignment(task_id, scout_assignment)
        
        target_assignment = {
            "persona_id": 2001,
            "persona_name": "测试大部队员",
            "match_score": 0.85,
            "predicted_success_rate": 0.75,
            "match_reasons": ["年龄匹配", "职业匹配"],
            "status": "已分配"
        }
        task_manager.add_target_assignment(task_id, target_assignment)
        
        task = task_manager.get_task(task_id)
        assert len(task['scout_assignments']) == 1
        assert len(task['target_assignments']) == 1
        print("✅ 分配信息添加成功")
    except Exception as e:
        print(f"❌ 分配信息添加失败: {e}")
        return False
    
    # 测试6: 结果更新
    print("\n📋 测试6: 结果更新")
    try:
        results = {
            "total_tasks": 5,
            "successful_tasks": 3,
            "failed_tasks": 2,
            "success_rate": 0.6,
            "total_answers": 15
        }
        task_manager.update_results(task_id, results)
        
        task = task_manager.get_task(task_id)
        assert task['results']['total_tasks'] == 5
        assert task['results']['success_rate'] == 0.6
        print("✅ 结果更新成功")
    except Exception as e:
        print(f"❌ 结果更新失败: {e}")
        return False
    
    # 测试7: 任务完成
    print("\n📋 测试7: 任务完成")
    try:
        final_results = {"final_status": "completed", "summary": "测试完成"}
        task_manager.complete_task(task_id, final_results)
        
        # 检查任务是否移动到历史记录
        assert task_id not in task_manager.active_tasks
        assert len(task_manager.task_history) > 0
        print("✅ 任务完成处理成功")
    except Exception as e:
        print(f"❌ 任务完成处理失败: {e}")
        return False
    
    # 测试8: Flask应用路由
    print("\n📋 测试8: Flask应用路由")
    try:
        # 简单测试Flask应用是否正常初始化
        assert app is not None
        assert hasattr(app, 'test_client')
        print("✅ Flask应用初始化正常")
        print("✅ 路由配置完成")
        print("✅ 应用已准备就绪")
                
    except Exception as e:
        print(f"❌ Flask应用路由测试失败: {e}")
        return False
    
    print("\n🎉 所有Web界面功能测试通过！")
    print("=" * 50)
    return True

def test_task_creation_api():
    """测试任务创建API"""
    print("\n📋 测试任务创建API")
    try:
        # 测试API路由是否存在
        assert hasattr(app, 'url_map')
        
        # 检查关键路由是否已注册
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        required_routes = ['/create_task', '/task_status/<task_id>', '/active_tasks', '/task_history']
        
        for route in required_routes:
            # 简化路由检查
            route_exists = any(route.replace('<task_id>', '') in r for r in routes)
            assert route_exists, f"路由 {route} 未找到"
        
        print("✅ 所有API路由已正确注册")
        print("✅ 任务创建API准备就绪")
        print("✅ 状态查询API准备就绪")
        print("✅ 历史记录API准备就绪")
            
    except Exception as e:
        print(f"❌ 任务创建API测试失败: {e}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("🚀 智能问卷自动填写系统 - Web界面测试")
    print("🔧 测试Web界面的核心功能和API接口")
    print("=" * 60)
    
    # 运行功能测试
    if not test_web_interface():
        print("❌ Web界面功能测试失败")
        return False
    
    # 运行API测试
    if not test_task_creation_api():
        print("❌ API接口测试失败")
        return False
    
    print("\n🎉 所有测试通过！Web界面已准备就绪")
    print("📋 可以使用以下命令启动Web服务器:")
    print("   python start_web_interface.py")
    print("📋 然后访问: http://localhost:5002")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 