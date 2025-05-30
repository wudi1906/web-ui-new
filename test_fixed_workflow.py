#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复后的完整工作流
验证：AdsPower+青果代理+敢死队答题 → 知识库分析 → 大部队答题
"""

import requests
import time
import json

def test_complete_workflow():
    """测试完整工作流"""
    print("🧪 测试修复后的完整工作流")
    print("=" * 60)
    
    # 步骤1: 检查系统状态
    print("🔍 检查系统状态...")
    try:
        response = requests.get("http://localhost:5002/system_status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 系统状态: {status}")
            if not status.get("system_ready"):
                print("❌ 系统未就绪，请检查")
                return False
        else:
            print(f"❌ 系统状态检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到系统: {e}")
        return False
    
    # 步骤2: 创建测试任务
    print("\n📝 创建测试任务...")
    task_data = {
        "questionnaire_url": "https://www.wjx.cn/vm/ml5AbmN.aspx",
        "scout_count": 1,  # 1个敢死队成员
        "target_count": 1   # 1个大部队成员
    }
    
    try:
        response = requests.post(
            "http://localhost:5002/create_task",
            json=task_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                task_id = result["task_id"]
                print(f"✅ 任务创建成功: {task_id}")
                print(f"   问卷URL: {result['questionnaire_url']}")
                print(f"   敢死队: {result['scout_count']} 人")
                print(f"   大部队: {result['target_count']} 人")
            else:
                print(f"❌ 任务创建失败: {result.get('error')}")
                return False
        else:
            print(f"❌ 任务创建请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 任务创建异常: {e}")
        return False
    
    # 步骤3: 监控任务执行
    print(f"\n👀 监控任务执行: {task_id}")
    print("⚠️ 注意: 此测试将启动真实的AdsPower浏览器和browser-use答题")
    print("📱 请确保AdsPower已启动且配置正确")
    
    max_wait_time = 300  # 5分钟超时
    start_time = time.time()
    last_phase = None
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"http://localhost:5002/refresh_task/{task_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    task = result["task"]
                    current_phase = task.get("phase", "未知")
                    status = task.get("status", "未知")
                    
                    # 显示阶段变化
                    if current_phase != last_phase:
                        print(f"📍 阶段更新: {current_phase}")
                        last_phase = current_phase
                    
                    # 检查是否完成
                    if result.get("completed") or status in ["completed", "failed"]:
                        print(f"🎉 任务执行完成!")
                        
                        # 显示详细结果
                        if "results" in task:
                            print("\n📊 执行结果:")
                            results = task["results"]
                            
                            # 敢死队结果
                            if "scout_phase" in results:
                                scout = results["scout_phase"]
                                print(f"🔍 敢死队阶段:")
                                print(f"   成功率: {scout.get('success_rate', 0):.1f}%")
                                print(f"   参与人数: {scout.get('count', 0)}")
                            
                            # 知识库分析
                            if "guidance_phase" in results:
                                guidance = results["guidance_phase"]
                                print(f"📚 知识库分析:")
                                print(f"   生成规则: {guidance.get('rules_generated', 0)} 条")
                            
                            # 大部队结果
                            if "target_phase" in results:
                                target = results["target_phase"]
                                print(f"🎯 大部队阶段:")
                                print(f"   成功率: {target.get('success_rate', 0):.1f}%")
                                print(f"   参与人数: {target.get('count', 0)}")
                            
                            # 总体统计
                            if "overall" in results:
                                overall = results["overall"]
                                print(f"📈 总体统计:")
                                print(f"   总成功率: {overall.get('success_rate', 0):.1f}%")
                                print(f"   总参与人数: {overall.get('total_participants', 0)}")
                        
                        return status == "completed"
                    
                    # 显示进度
                    progress = task.get("progress", {})
                    current_phase_num = progress.get("current_phase", 1)
                    total_phases = progress.get("total_phases", 4)
                    print(f"   进度: {current_phase_num}/{total_phases} ({status})")
                    
                else:
                    print(f"❌ 任务状态查询失败: {result.get('error')}")
                    return False
            else:
                print(f"⚠️ 状态查询请求失败: {response.status_code}")
            
            # 等待5秒后再次检查
            time.sleep(5)
            
        except Exception as e:
            print(f"⚠️ 监控异常: {e}")
            time.sleep(5)
    
    print(f"⏰ 监控超时 ({max_wait_time}秒)")
    return False

def main():
    """主函数"""
    print("🚀 智能问卷填写系统 - 修复验证测试")
    print("=" * 60)
    print("🎯 验证内容:")
    print("  ✅ Web界面 → Flask路由")
    print("  ✅ AdsPower浏览器管理")
    print("  ✅ 青果代理集成")
    print("  ✅ testWenjuanFinal.py真实答题")
    print("  ✅ 知识库经验收集和分析")
    print("  ✅ 敢死队 → 大部队完整流程")
    print("=" * 60)
    
    success = test_complete_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试成功! 所有功能正常工作")
        print("✅ 系统已准备好进行生产使用")
    else:
        print("❌ 测试失败! 需要进一步调试")
        print("⚠️ 请检查日志和错误信息")
    print("=" * 60)

if __name__ == "__main__":
    main() 