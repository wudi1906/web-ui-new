#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试真实工作流
验证：敢死队(真实browser-use答题) → 知识库分析 → 大部队(带经验指导的真实答题)
"""

import asyncio
import json
import time
import requests
from datetime import datetime

def test_system_status():
    """测试系统状态"""
    print("🔍 测试系统状态...")
    try:
        response = requests.get("http://localhost:5002/api/system_status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 系统状态正常:")
            print(f"   - 系统就绪: {status['system_ready']}")
            print(f"   - 数据库连接: {status['database_connected']}")
            print(f"   - 知识库就绪: {status['knowledge_base_ready']}")
            print(f"   - 活跃任务: {status['active_tasks']}")
            return True
        else:
            print(f"❌ 系统状态检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 系统状态检查异常: {e}")
        return False

def create_test_task():
    """创建测试任务"""
    print("\n📝 创建测试任务...")
    
    task_data = {
        "questionnaire_url": "https://www.wjx.cn/vm/ml5AbmN.aspx",
        "scout_count": 1,  # 1个敢死队成员
        "target_count": 2   # 2个大部队成员
    }
    
    try:
        response = requests.post(
            "http://localhost:5002/api/create_task",
            json=task_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result["task_id"]
            print(f"✅ 任务创建成功:")
            print(f"   - 任务ID: {task_id}")
            print(f"   - 问卷URL: {result['questionnaire_url']}")
            print(f"   - 敢死队数量: {result['scout_count']}")
            print(f"   - 大部队数量: {result['target_count']}")
            return task_id
        else:
            print(f"❌ 任务创建失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 任务创建异常: {e}")
        return None

def monitor_task_progress(task_id: str, max_wait_time: int = 300):
    """监控任务进度"""
    print(f"\n👀 监控任务进度: {task_id}")
    print(f"⏰ 最大等待时间: {max_wait_time}秒")
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"http://localhost:5002/api/refresh_task/{task_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                # 检查是否有错误
                if "error" in result:
                    print(f"❌ 任务执行失败: {result['error']}")
                    return result
                
                # 检查是否完成
                if "scout_phase" in result and "target_phase" in result:
                    print(f"🎉 任务执行完成!")
                    return result
                
                # 显示当前状态
                current_status = result.get("status", "unknown")
                if current_status != last_status:
                    print(f"📍 状态更新: {current_status}")
                    if "message" in result:
                        print(f"   消息: {result['message']}")
                    last_status = current_status
                
            else:
                print(f"⚠️ 状态查询失败: {response.status_code}")
            
            # 等待5秒后再次检查
            time.sleep(5)
            
        except Exception as e:
            print(f"⚠️ 监控异常: {e}")
            time.sleep(5)
    
    print(f"⏰ 监控超时 ({max_wait_time}秒)")
    return None

def analyze_results(result: dict):
    """分析执行结果"""
    print("\n📊 执行结果分析:")
    print("=" * 60)
    
    if "error" in result:
        print(f"❌ 执行失败: {result['error']}")
        return
    
    # 会话信息
    print(f"🆔 会话ID: {result['session_id']}")
    print(f"🌐 问卷URL: {result['questionnaire_url']}")
    
    # 敢死队阶段
    scout_phase = result.get("scout_phase", {})
    print(f"\n🔍 敢死队阶段:")
    print(f"   - 参与人数: {scout_phase.get('count', 0)}")
    print(f"   - 成功人数: {scout_phase.get('success_count', 0)}")
    print(f"   - 成功率: {scout_phase.get('success_rate', 0):.1f}%")
    
    scout_results = scout_phase.get("results", [])
    for i, scout in enumerate(scout_results, 1):
        status = "✅" if scout.get("success") else "❌"
        print(f"   {status} {scout.get('scout_name', f'敢死队员{i}')}: {scout.get('persona_name', '未知')}")
        if scout.get("duration"):
            print(f"      用时: {scout['duration']:.1f}秒")
        if scout.get("error"):
            print(f"      错误: {scout['error']}")
    
    # 知识库分析阶段
    guidance_phase = result.get("guidance_phase", {})
    print(f"\n📚 知识库分析阶段:")
    print(f"   - 生成规则数: {guidance_phase.get('rules_generated', 0)}")
    
    rules = guidance_phase.get("rules", [])
    for i, rule in enumerate(rules, 1):
        keywords = "、".join(rule.get("keywords", []))
        print(f"   规则{i}: {keywords} → {rule.get('recommended_answer')} (置信度{rule.get('confidence', 0)}%)")
    
    # 大部队阶段
    target_phase = result.get("target_phase", {})
    print(f"\n🎯 大部队阶段:")
    print(f"   - 参与人数: {target_phase.get('count', 0)}")
    print(f"   - 成功人数: {target_phase.get('success_count', 0)}")
    print(f"   - 成功率: {target_phase.get('success_rate', 0):.1f}%")
    
    target_results = target_phase.get("results", [])
    for i, member in enumerate(target_results, 1):
        status = "✅" if member.get("success") else "❌"
        guidance_used = "🧠" if member.get("used_guidance") else "🤔"
        print(f"   {status} {guidance_used} {member.get('member_name', f'大部队成员{i}')}: {member.get('persona_name', '未知')}")
        if member.get("duration"):
            print(f"      用时: {member['duration']:.1f}秒")
        if member.get("guidance_rules_applied"):
            print(f"      应用规则: {member['guidance_rules_applied']}条")
        if member.get("error"):
            print(f"      错误: {member['error']}")
    
    # 总体统计
    overall = result.get("overall", {})
    print(f"\n📈 总体统计:")
    print(f"   - 总参与人数: {overall.get('total_participants', 0)}")
    print(f"   - 总成功人数: {overall.get('total_success', 0)}")
    print(f"   - 总体成功率: {overall.get('success_rate', 0):.1f}%")
    
    # 效果分析
    scout_success_rate = scout_phase.get('success_rate', 0)
    target_success_rate = target_phase.get('success_rate', 0)
    improvement = target_success_rate - scout_success_rate
    
    print(f"\n🚀 效果分析:")
    print(f"   - 敢死队成功率: {scout_success_rate:.1f}%")
    print(f"   - 大部队成功率: {target_success_rate:.1f}%")
    if improvement > 0:
        print(f"   - 🎉 知识库指导提升: +{improvement:.1f}%")
    elif improvement < 0:
        print(f"   - ⚠️ 成功率下降: {improvement:.1f}%")
    else:
        print(f"   - 📊 成功率持平")

def main():
    """主测试流程"""
    print("🧪 智能问卷填写系统 - 真实工作流测试")
    print("=" * 60)
    print("🎯 测试流程: 敢死队(真实答题) → 知识库分析 → 大部队(经验指导答题)")
    print("=" * 60)
    
    # 步骤1: 检查系统状态
    if not test_system_status():
        print("❌ 系统状态检查失败，请确保main.py正在运行")
        return
    
    # 步骤2: 创建测试任务
    task_id = create_test_task()
    if not task_id:
        print("❌ 任务创建失败")
        return
    
    # 步骤3: 监控任务执行
    print(f"\n⚠️ 注意: 此测试将启动真实的浏览器进行问卷填写")
    print(f"📱 请确保您的环境支持browser-use和相关依赖")
    print(f"⏰ 预计执行时间: 2-5分钟")
    
    input("\n按回车键开始执行测试...")
    
    result = monitor_task_progress(task_id, max_wait_time=600)  # 10分钟超时
    
    # 步骤4: 分析结果
    if result:
        analyze_results(result)
    else:
        print("❌ 任务执行超时或失败")
    
    print("\n" + "=" * 60)
    print("🏁 测试完成")

if __name__ == "__main__":
    main() 