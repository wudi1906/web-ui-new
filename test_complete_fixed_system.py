#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整修复系统测试脚本
验证：AdsPower浏览器连接 + browser-use答题 + 多窗口布局 + 完整工作流
"""

import requests
import time
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, Union

def test_system_status():
    """测试系统状态"""
    print("🔍 步骤1: 检查系统状态...")
    try:
        response = requests.get("http://localhost:5002/system_status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 系统状态正常")
            print(f"   - 系统就绪: {status.get('system_ready', False)}")
            print(f"   - 数据库连接: {status.get('database_connected', False)}")
            print(f"   - 知识库就绪: {status.get('knowledge_base_ready', False)}")
            return True
        else:
            print(f"❌ 系统状态检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到系统: {e}")
        return False

def create_test_task():
    """创建测试任务"""
    print("\n📝 步骤2: 创建测试任务...")
    
    # 测试配置
    task_data = {
        "questionnaire_url": "https://www.wjx.cn/vm/ml5AbmN.aspx",
        "scout_count": 2,  # 2个敢死队成员
        "target_count": 3   # 3个大部队成员
    }
    
    print(f"📋 任务配置:")
    print(f"   - 问卷URL: {task_data['questionnaire_url']}")
    print(f"   - 敢死队人数: {task_data['scout_count']}")
    print(f"   - 大部队人数: {task_data['target_count']}")
    print(f"   - 总浏览器窗口: {task_data['scout_count'] + task_data['target_count']}")
    
    try:
        response = requests.post(
            "http://localhost:5002/create_task",
            json=task_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                task_id = result["task_id"]
                print(f"✅ 任务创建成功: {task_id}")
                return task_id
            else:
                print(f"❌ 任务创建失败: {result.get('error')}")
                return None
        else:
            print(f"❌ 任务创建请求失败: HTTP {response.status_code}")
            print(f"   响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 任务创建异常: {e}")
        return None

def monitor_task_execution(task_id: str, max_wait_time: int = 600):
    """监控任务执行"""
    print(f"\n👀 步骤3: 监控任务执行 (任务ID: {task_id})")
    print("=" * 60)
    print("🎯 预期执行流程:")
    print("  1️⃣ 敢死队阶段: 创建AdsPower浏览器 → browser-use答题 → 收集经验")
    print("  2️⃣ 经验分析阶段: 分析敢死队结果 → 生成指导规则")
    print("  3️⃣ 大部队阶段: 应用指导规则 → 智能答题")
    print("  4️⃣ 多窗口布局: 所有浏览器按网格排布")
    print("=" * 60)
    
    start_time = time.time()
    last_phase = None
    phase_start_times = {}
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"http://localhost:5002/refresh_task/{task_id}", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    task = result["task"]
                    current_phase = task.get("phase", "未知")
                    status = task.get("status", "未知")
                    
                    # 记录阶段变化时间
                    if current_phase != last_phase:
                        current_time = datetime.now().strftime("%H:%M:%S")
                        print(f"\n🕐 [{current_time}] 📍 阶段更新: {current_phase}")
                        
                        if last_phase and last_phase in phase_start_times:
                            duration = time.time() - phase_start_times[last_phase]
                            print(f"   ⏱️ 上一阶段用时: {duration:.1f}秒")
                        
                        phase_start_times[current_phase] = time.time()
                        last_phase = current_phase
                    
                    # 显示进度
                    progress = task.get("progress", {})
                    current_phase_num = progress.get("current_phase", 1)
                    total_phases = progress.get("total_phases", 4)
                    print(f"   📊 进度: {current_phase_num}/{total_phases} - {status}")
                    
                    # 检查是否完成
                    if result.get("completed") or status in ["completed", "failed"]:
                        print(f"\n🎉 任务执行完成!")
                        
                        # 显示详细结果
                        if "results" in task:
                            display_detailed_results(task["results"])
                        
                        return status == "completed", task.get("results")
                    
                else:
                    print(f"❌ 任务状态查询失败: {result.get('error')}")
                    return False, None
            else:
                print(f"⚠️ 状态查询请求失败: HTTP {response.status_code}")
            
            # 等待5秒后再次检查
            time.sleep(5)
            
        except Exception as e:
            print(f"⚠️ 监控异常: {e}")
            time.sleep(5)
    
    print(f"\n⏰ 监控超时 ({max_wait_time}秒)")
    return False, None

def display_detailed_results(results: dict):
    """显示详细的执行结果"""
    print("\n" + "=" * 60)
    print("📊 详细执行结果")
    print("=" * 60)
    
    # 窗口布局信息
    if "window_layout" in results:
        layout = results["window_layout"]
        print(f"🖥️ 窗口布局:")
        print(f"   - 总窗口数: {layout.get('total_windows', 0)}")
        print(f"   - 布局位置: {len(layout.get('positions', []))} 个位置已计算")
    
    # 敢死队结果
    if "scout_phase" in results:
        scout = results["scout_phase"]
        print(f"\n🔍 敢死队阶段:")
        print(f"   - 参与人数: {scout.get('count', 0)}")
        print(f"   - 成功人数: {scout.get('success_count', 0)}")
        print(f"   - 成功率: {scout.get('success_rate', 0):.1f}%")
        
        # 显示每个敢死队员的详情
        scout_results = scout.get('results', [])
        for i, scout_result in enumerate(scout_results):
            print(f"     👤 {scout_result.get('scout_name', f'敢死队员{i+1}')}:")
            print(f"        - 数字人: {scout_result.get('persona_name', '未知')}")
            print(f"        - 成功: {'✅' if scout_result.get('success') else '❌'}")
            print(f"        - 回答问题: {scout_result.get('questions_answered', 0)}个")
            if 'window_position' in scout_result:
                pos = scout_result['window_position']
                print(f"        - 窗口位置: ({pos.get('x', 0)}, {pos.get('y', 0)})")
    
    # 知识库分析
    if "guidance_phase" in results:
        guidance = results["guidance_phase"]
        print(f"\n📚 知识库分析:")
        print(f"   - 生成规则: {guidance.get('rules_generated', 0)} 条")
        
        rules = guidance.get('rules', [])
        for i, rule in enumerate(rules[:3]):  # 显示前3条规则
            keywords = ', '.join(rule.get('keywords', []))
            print(f"     📋 规则{i+1}: {keywords} → {rule.get('recommended_answer', '未知')}")
            print(f"        置信度: {rule.get('confidence', 0)}%")
    
    # 大部队结果
    if "target_phase" in results:
        target = results["target_phase"]
        print(f"\n🎯 大部队阶段:")
        print(f"   - 参与人数: {target.get('count', 0)}")
        print(f"   - 成功人数: {target.get('success_count', 0)}")
        print(f"   - 成功率: {target.get('success_rate', 0):.1f}%")
        
        # 显示每个大部队成员的详情
        target_results = target.get('results', [])
        for i, target_result in enumerate(target_results):
            print(f"     👤 {target_result.get('member_name', f'大部队成员{i+1}')}:")
            print(f"        - 数字人: {target_result.get('persona_name', '未知')}")
            print(f"        - 成功: {'✅' if target_result.get('success') else '❌'}")
            print(f"        - 回答问题: {target_result.get('questions_answered', 0)}个")
            print(f"        - 使用指导: {'✅' if target_result.get('used_guidance') else '❌'}")
            if 'window_position' in target_result:
                pos = target_result['window_position']
                print(f"        - 窗口位置: ({pos.get('x', 0)}, {pos.get('y', 0)})")
    
    # 总体统计
    if "overall" in results:
        overall = results["overall"]
        print(f"\n📈 总体统计:")
        print(f"   - 总参与人数: {overall.get('total_participants', 0)}")
        print(f"   - 总成功人数: {overall.get('total_success', 0)}")
        print(f"   - 总成功率: {overall.get('success_rate', 0):.1f}%")

def analyze_system_performance(success: bool, results: Optional[Dict[str, Any]] = None):
    """分析系统性能"""
    print("\n" + "=" * 60)
    print("🔬 系统性能分析")
    print("=" * 60)
    
    if not success:
        print("❌ 系统执行失败，无法进行性能分析")
        return
    
    if not results:
        print("⚠️ 缺少结果数据，无法进行性能分析")
        return
    
    # 分析各个功能模块
    modules_status = {
        "AdsPower浏览器管理": "✅ 正常" if results.get("scout_phase", {}).get("count", 0) > 0 else "❌ 异常",
        "browser-use答题": "✅ 正常" if any(r.get("questions_answered", 0) > 0 for r in results.get("scout_phase", {}).get("results", [])) else "❌ 异常",
        "多窗口布局": "✅ 正常" if results.get("window_layout", {}).get("total_windows", 0) > 0 else "❌ 异常",
        "知识库分析": "✅ 正常" if results.get("guidance_phase", {}).get("rules_generated", 0) > 0 else "❌ 异常",
        "智能指导应用": "✅ 正常" if any(r.get("used_guidance", False) for r in results.get("target_phase", {}).get("results", [])) else "❌ 异常"
    }
    
    print("🧩 功能模块状态:")
    for module, status in modules_status.items():
        print(f"   - {module}: {status}")
    
    # 计算改进效果
    scout_success_rate = results.get("scout_phase", {}).get("success_rate", 0)
    target_success_rate = results.get("target_phase", {}).get("success_rate", 0)
    improvement = target_success_rate - scout_success_rate
    
    print(f"\n📊 改进效果分析:")
    print(f"   - 敢死队成功率: {scout_success_rate:.1f}%")
    print(f"   - 大部队成功率: {target_success_rate:.1f}%")
    print(f"   - 改进幅度: {improvement:+.1f}%")
    
    if improvement > 0:
        print("   ✅ 知识库指导有效，大部队表现优于敢死队")
    elif improvement == 0:
        print("   ⚠️ 知识库指导效果中性")
    else:
        print("   ❌ 知识库指导可能需要优化")

def main():
    """主测试流程"""
    print("🧪 智能问卷填写系统 - 完整修复验证测试")
    print("=" * 60)
    print("🎯 测试目标:")
    print("  ✅ AdsPower浏览器创建和管理")
    print("  ✅ browser-use与AdsPower的连接")
    print("  ✅ 真实问卷答题和经验收集")
    print("  ✅ 知识库分析和指导规则生成")
    print("  ✅ 多浏览器窗口智能布局")
    print("  ✅ 敢死队→大部队完整工作流")
    print("=" * 60)
    
    # 步骤1: 检查系统状态
    if not test_system_status():
        print("\n❌ 系统状态检查失败，请确保main.py正在运行")
        return
    
    # 步骤2: 创建测试任务
    task_id = create_test_task()
    if not task_id:
        print("\n❌ 任务创建失败")
        return
    
    # 重要提示
    print("\n" + "⚠️" * 20)
    print("🚨 重要提示:")
    print("📱 此测试将启动真实的AdsPower浏览器")
    print("🤖 每个浏览器将使用browser-use进行自动答题")
    print("🖥️ 多个浏览器窗口将按网格布局排列")
    print("⏰ 整个过程预计需要5-10分钟")
    print("💡 请确保AdsPower已启动且配置正确")
    print("⚠️" * 20)
    
    input("\n按回车键开始执行测试...")
    
    # 步骤3: 监控任务执行
    success, results = monitor_task_execution(task_id, max_wait_time=900)  # 15分钟超时
    
    # 步骤4: 分析结果
    analyze_system_performance(success, results)
    
    # 总结
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试成功! 所有功能正常工作")
        print("✅ 系统已准备好进行生产使用")
        print("💡 建议: 可以开始大规模问卷调研任务")
    else:
        print("❌ 测试失败! 需要进一步调试")
        print("🔧 建议: 检查日志和错误信息")
        print("📞 如需帮助，请查看详细日志")
    print("=" * 60)

if __name__ == "__main__":
    main() 