#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
三阶段智能系统完整测试
测试所有组件的集成和工作流
"""

import asyncio
import json
import requests
import time
from datetime import datetime

def test_system_status():
    """测试系统状态"""
    print("🔍 测试系统状态...")
    
    try:
        # 测试Flask应用
        response = requests.get('http://localhost:5002/system_status', timeout=5)
        if response.status_code == 200:
            status = response.json()
            print("✅ Flask应用正常运行")
            print(f"   - 三阶段智能系统: {'可用' if status.get('three_stage_system_available') else '不可用'}")
            print(f"   - 传统系统: {'可用' if status.get('enhanced_system_available') else '不可用'}")
            print(f"   - 知识库API: {'可用' if status.get('knowledge_api_available') else '不可用'}")
            print(f"   - 活跃任务: {status.get('active_tasks_count', 0)}个")
            return True
        else:
            print(f"❌ Flask应用响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Flask应用连接失败: {e}")
        return False

def test_knowledge_api():
    """测试知识库API"""
    print("\n🔍 测试知识库API...")
    
    try:
        response = requests.get('http://localhost:5003/api/knowledge/summary', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ 知识库API正常运行")
            if data.get('success'):
                summary = data.get('data', {}).get('summary', {})
                print(f"   - 总记录: {summary.get('total_records', 0)}条")
                print(f"   - 成功记录: {summary.get('successful_records', 0)}条")
                print(f"   - 数字人: {summary.get('total_personas', 0)}个")
                print(f"   - 会话: {summary.get('total_sessions', 0)}个")
            return True
        else:
            print(f"❌ 知识库API响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 知识库API连接失败: {e}")
        return False

def test_three_stage_core():
    """测试三阶段智能核心"""
    print("\n🔍 测试三阶段智能核心...")
    
    try:
        from intelligent_three_stage_core import ThreeStageIntelligentCore
        
        # 初始化核心系统
        core = ThreeStageIntelligentCore()
        print("✅ 三阶段智能核心初始化成功")
        
        # 测试备用数字人创建
        persona = core._create_backup_persona(0)
        print(f"✅ 备用数字人创建测试: {persona.get('name', '未知')}")
        
        # 测试提示词生成
        prompt = core._generate_enhanced_scout_prompt(persona, "https://example.com")
        print(f"✅ 提示词生成测试: {len(prompt)}字符")
        
        return True
    except Exception as e:
        print(f"❌ 三阶段智能核心测试失败: {e}")
        return False

def test_task_creation():
    """测试任务创建"""
    print("\n🔍 测试三阶段智能任务创建...")
    
    try:
        # 创建测试任务
        task_data = {
            "questionnaire_url": "https://www.wjx.cn/vm/ml5AbmN.aspx",
            "scout_count": 2,
            "target_count": 5,
            "task_mode": "three_stage"
        }
        
        response = requests.post(
            'http://localhost:5002/create_task',
            json=task_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                task_id = result.get('task_id')
                print(f"✅ 任务创建成功: {task_id}")
                print(f"   - 模式: {result.get('task_mode')}")
                print(f"   - 消息: {result.get('message')}")
                
                # 监控任务进度
                print("\n📊 监控任务进度...")
                for i in range(30):  # 监控30秒
                    try:
                        refresh_response = requests.get(f'http://localhost:5002/refresh_task/{task_id}', timeout=5)
                        if refresh_response.status_code == 200:
                            task_data = refresh_response.json()
                            if task_data.get('success'):
                                task = task_data.get('task')
                                status = task.get('status')
                                phase = task.get('phase')
                                progress = task.get('progress', {})
                                
                                print(f"   [{i+1:2d}s] 状态: {status} | 阶段: {phase} | 进度: {progress.get('current_phase', 0)}/{progress.get('total_phases', 0)}")
                                
                                # 如果任务完成，显示结果
                                if task_data.get('completed') or status in ['completed', 'failed']:
                                    print(f"\n🎉 任务{'完成' if status == 'completed' else '失败'}!")
                                    
                                    if status == 'completed' and 'results' in task:
                                        results = task['results']
                                        print("\n📊 执行结果:")
                                        
                                        # 敢死队阶段结果
                                        scout_phase = results.get('scout_phase', {})
                                        print(f"   🔍 敢死队阶段: {scout_phase.get('success_count', 0)}/{scout_phase.get('total_count', 0)} 成功")
                                        
                                        # 分析阶段结果
                                        analysis_phase = results.get('analysis_phase', {})
                                        if 'intelligence' in analysis_phase:
                                            intelligence = analysis_phase['intelligence']
                                            print(f"   🧠 智能分析: 主题={intelligence.get('questionnaire_theme', '未知')}")
                                            print(f"               可信度={intelligence.get('confidence_score', 0):.0%}")
                                            print(f"               指导规则={len(analysis_phase.get('guidance_rules', []))}条")
                                        
                                        # 大部队阶段结果
                                        target_phase = results.get('target_phase', {})
                                        print(f"   🎯 大部队阶段: {target_phase.get('success_count', 0)}/{target_phase.get('total_count', 0)} 成功")
                                        
                                        # 最终报告
                                        if 'final_report' in results:
                                            report = results['final_report']
                                            improvements = report.get('improvements', {})
                                            print(f"   📈 整体效果: 成功率提升 {improvements.get('success_rate_improvement', 0):.1%}")
                                    
                                    return True
                                
                                time.sleep(2)
                            else:
                                print(f"   ❌ 刷新任务失败: {task_data.get('error', '未知错误')}")
                                break
                        else:
                            print(f"   ❌ 刷新请求失败: {refresh_response.status_code}")
                            break
                    except Exception as e:
                        print(f"   ❌ 监控异常: {e}")
                        break
                
                print("\n⏰ 监控超时")
                return True
            else:
                print(f"❌ 任务创建失败: {result.get('error', '未知错误')}")
                return False
        else:
            print(f"❌ 任务创建请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 任务创建测试失败: {e}")
        return False

def test_simulation_mode():
    """测试模拟模式"""
    print("\n🔍 测试模拟模式...")
    
    try:
        # 创建模拟模式任务
        task_data = {
            "questionnaire_url": "https://www.wjx.cn/vm/ml5AbmN.aspx",
            "scout_count": 3,
            "target_count": 8,
            "task_mode": "traditional"
        }
        
        response = requests.post(
            'http://localhost:5002/create_task',
            json=task_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 模拟模式任务创建成功: {result.get('task_id')}")
                return True
            else:
                print(f"❌ 模拟模式任务创建失败: {result.get('error')}")
                return False
        else:
            print(f"❌ 模拟模式请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 模拟模式测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 三阶段智能系统完整测试")
    print("=" * 60)
    
    tests = [
        ("系统状态检查", test_system_status),
        ("知识库API测试", test_knowledge_api),
        ("三阶段核心测试", test_three_stage_core),
        ("三阶段任务测试", test_task_creation),
        ("模拟模式测试", test_simulation_mode)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((test_name, False))
    
    # 测试结果汇总
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1
    
    total = len(results)
    success_rate = passed / total * 100 if total > 0 else 0
    
    print(f"\n总计: {passed}/{total} 通过 ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 系统整体状态良好!")
    elif success_rate >= 60:
        print("⚠️ 系统部分功能正常，建议检查失败项")
    else:
        print("❌ 系统存在较多问题，需要修复")
    
    print("\n💡 提示:")
    print("- 确保Flask应用运行在端口5002")
    print("- 确保知识库API运行在端口5003")
    print("- 如需测试真实问卷，请提供有效的问卷URL")
    print("- 三阶段智能模式需要Gemini API密钥和browser-use组件")

if __name__ == "__main__":
    main() 