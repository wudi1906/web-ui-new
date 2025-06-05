#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小规模三阶段智能系统测试
测试修复后的系统：1个敢死队，2个大部队
"""

import requests
import time
import json

def test_small_scale_three_stage():
    """测试小规模三阶段智能系统"""
    print("🚀 小规模三阶段智能系统测试")
    print("=" * 60)
    
    base_url = "http://localhost:5002"
    
    # 1. 检查系统状态
    print("\n📍 1. 检查系统状态...")
    try:
        response = requests.get(f"{base_url}/system_status", timeout=10)
        if response.status_code == 200:
            print("✅ Flask应用正常运行")
        else:
            print("❌ Flask应用状态异常")
            return False
    except Exception as e:
        print(f"❌ Flask应用连接失败: {e}")
        return False
    
    # 2. 创建小规模三阶段任务
    print("\n📍 2. 创建小规模三阶段任务（1敢死队，2大部队）...")
    task_data = {
        "questionnaire_url": "https://www.wjx.cn/vm/ml5AbmN.aspx",
        "scout_count": 1,      # 修复后：1个敢死队
        "target_count": 2,     # 修复后：2个大部队
        "task_mode": "three_stage"
    }
    
    try:
        response = requests.post(
            f"{base_url}/create_task",
            json=task_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            print(f"✅ 任务创建成功: {task_id}")
            print(f"   敢死队: {task_data['scout_count']}人")
            print(f"   大部队: {task_data['target_count']}人")
            print(f"   模式: {task_data['task_mode']}")
            
            # 3. 监控任务执行过程
            print("\n📍 3. 监控任务执行...")
            monitor_task_execution(base_url, task_id)
            
            return True
        else:
            print(f"❌ 任务创建失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 任务创建异常: {e}")
        return False

def monitor_task_execution(base_url: str, task_id: str, max_duration: int = 300):
    """监控任务执行过程"""
    start_time = time.time()
    last_status = None
    
    print(f"🔍 开始监控任务: {task_id}")
    print("   按 Ctrl+C 停止监控")
    
    try:
        while time.time() - start_time < max_duration:
            try:
                # 获取任务状态
                response = requests.get(f"{base_url}/refresh_task/{task_id}", timeout=10)
                
                if response.status_code == 200:
                    task_info = response.json()
                    current_status = task_info.get("status", "unknown")
                    
                    # 只有状态变化时才输出
                    if current_status != last_status:
                        print(f"📊 [{int(time.time() - start_time)}s] 状态: {current_status}")
                        
                        # 如果有执行日志，显示关键信息
                        if "logs" in task_info:
                            logs = task_info["logs"]
                            if logs and len(logs) > 0:
                                latest_log = logs[-1]
                                print(f"   最新: {latest_log}")
                        
                        last_status = current_status
                    
                    # 检查是否完成
                    if current_status in ["completed", "failed"]:
                        print(f"\n🎯 任务完成，最终状态: {current_status}")
                        
                        # 显示结果摘要
                        if "result" in task_info:
                            result = task_info["result"]
                            print("\n📋 结果摘要:")
                            
                            if "scout_phase" in result:
                                scout_phase = result["scout_phase"]
                                print(f"   敢死队阶段: {scout_phase.get('success_count', 0)}/{scout_phase.get('total_count', 0)} 成功")
                            
                            if "analysis_phase" in result:
                                analysis_phase = result["analysis_phase"]
                                intelligence = analysis_phase.get("intelligence", {})
                                print(f"   分析阶段: 置信度 {intelligence.get('confidence_score', 0):.0%}")
                                print(f"   指导规则: {len(analysis_phase.get('guidance_rules', []))}条")
                            
                            if "target_phase" in result:
                                target_phase = result["target_phase"]
                                print(f"   大部队阶段: {target_phase.get('success_count', 0)}/{target_phase.get('total_count', 0)} 成功")
                        
                        break
                else:
                    print(f"⚠️ 获取任务状态失败: {response.status_code}")
                
                # 等待间隔
                time.sleep(5)
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ 监控请求失败: {e}")
                time.sleep(10)
            except KeyboardInterrupt:
                print(f"\n⚠️ 用户停止监控")
                break
    
    except Exception as e:
        print(f"❌ 监控异常: {e}")

def test_api_connectivity():
    """测试API连通性"""
    print("\n🔧 API连通性测试")
    print("-" * 30)
    
    # 测试主Flask应用
    try:
        response = requests.get("http://localhost:5002/system_status", timeout=5)
        print(f"✅ 主应用(5002): {response.status_code}")
    except Exception as e:
        print(f"❌ 主应用(5002): {e}")
    
    # 测试知识库API
    try:
        response = requests.get("http://localhost:5003/api/knowledge/summary", timeout=5)
        print(f"✅ 知识库(5003): {response.status_code}")
    except Exception as e:
        print(f"❌ 知识库(5003): {e}")

if __name__ == "__main__":
    try:
        # 先测试连通性
        test_api_connectivity()
        
        # 执行小规模测试
        success = test_small_scale_three_stage()
        
        if success:
            print("\n🎉 小规模测试完成！")
        else:
            print("\n❌ 小规模测试失败！")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}") 