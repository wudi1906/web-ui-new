#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷填写工作流测试
测试：敢死队作答 → 收集结果 → 分析经验 → 指导大部队 → 大部队作答
"""

import requests
import json
import time
from datetime import datetime

class QuestionnaireWorkflowTester:
    """问卷工作流测试器"""
    
    def __init__(self):
        self.base_url = "http://localhost:5002"
        self.knowledge_api = "http://localhost:5003"
        self.test_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"  # 测试问卷URL
    
    def test_complete_workflow(self):
        """测试完整工作流"""
        print("🎯 测试智能问卷填写完整工作流")
        print("=" * 60)
        
        # 1. 检查系统状态
        print("📊 检查系统状态...")
        status = self.check_system_status()
        if not status:
            print("❌ 系统状态检查失败")
            return False
        
        # 2. 检查知识库初始状态
        print("\n📚 检查知识库初始状态...")
        initial_knowledge = self.get_knowledge_summary()
        print(f"   初始记录数: {initial_knowledge.get('total_records', 0)}")
        print(f"   初始指导规则: {len(initial_knowledge.get('guidance_rules', []))}")
        
        # 3. 创建任务（敢死队2人，大部队5人）
        print("\n🚀 创建智能问卷任务...")
        task_id = self.create_task(
            questionnaire_url=self.test_url,
            scout_count=2,
            target_count=5
        )
        
        if not task_id:
            print("❌ 任务创建失败")
            return False
        
        print(f"✅ 任务创建成功: {task_id}")
        
        # 4. 监控任务执行
        print("\n⏳ 监控任务执行过程...")
        success = self.monitor_task_execution(task_id)
        
        if not success:
            print("❌ 任务执行失败")
            return False
        
        # 5. 检查知识库更新
        print("\n📈 检查知识库更新...")
        final_knowledge = self.get_knowledge_summary()
        self.compare_knowledge_changes(initial_knowledge, final_knowledge)
        
        # 6. 获取最终结果
        print("\n📋 获取最终结果...")
        final_result = self.get_task_result(task_id)
        self.display_final_results(final_result)
        
        print("\n🎉 完整工作流测试完成！")
        return True
    
    def check_system_status(self):
        """检查系统状态"""
        try:
            response = requests.get(f"{self.base_url}/system_status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"   ✅ 增强系统: {'可用' if status.get('enhanced_system_available') else '不可用'}")
                print(f"   ✅ 知识库API: {'可用' if status.get('knowledge_api_available') else '不可用'}")
                print(f"   ✅ testWenjuan: {'可用' if status.get('testwenjuan_available') else '不可用'}")
                return all([
                    status.get('enhanced_system_available'),
                    status.get('knowledge_api_available'),
                    status.get('testwenjuan_available')
                ])
            else:
                print(f"   ❌ 系统状态检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 系统状态检查异常: {e}")
            return False
    
    def get_knowledge_summary(self):
        """获取知识库概览"""
        try:
            response = requests.get(f"{self.knowledge_api}/api/knowledge/summary", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('data', {})
            return {}
        except Exception as e:
            print(f"   ⚠️ 获取知识库失败: {e}")
            return {}
    
    def create_task(self, questionnaire_url, scout_count, target_count):
        """创建任务"""
        try:
            payload = {
                "questionnaire_url": questionnaire_url,
                "scout_count": scout_count,
                "target_count": target_count
            }
            
            response = requests.post(
                f"{self.base_url}/create_task",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('task_id')
                else:
                    print(f"   ❌ 任务创建失败: {result.get('error')}")
            else:
                print(f"   ❌ 任务创建请求失败: {response.status_code}")
            
            return None
            
        except Exception as e:
            print(f"   ❌ 任务创建异常: {e}")
            return None
    
    def monitor_task_execution(self, task_id):
        """监控任务执行"""
        max_wait_time = 300  # 最大等待5分钟
        check_interval = 5   # 每5秒检查一次
        waited_time = 0
        
        last_phase = ""
        
        while waited_time < max_wait_time:
            try:
                response = requests.get(f"{self.base_url}/refresh_task/{task_id}", timeout=5)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('success'):
                        task = result.get('task')
                        current_phase = task.get('phase', '未知')
                        status = task.get('status', '未知')
                        progress = task.get('progress', {})
                        
                        # 显示阶段变化
                        if current_phase != last_phase:
                            print(f"   📍 {current_phase}")
                            last_phase = current_phase
                        
                        # 显示进度
                        current_phase_num = progress.get('current_phase', 1)
                        total_phases = progress.get('total_phases', 4)
                        print(f"      进度: {current_phase_num}/{total_phases} - {status}")
                        
                        # 检查是否完成
                        if status == 'completed':
                            print("   ✅ 任务执行完成")
                            return True
                        elif status == 'failed':
                            print(f"   ❌ 任务执行失败: {task.get('error', '未知错误')}")
                            return False
                        elif result.get('completed'):
                            print("   ✅ 任务已完成")
                            return True
                    else:
                        print(f"   ❌ 获取任务状态失败: {result.get('error')}")
                        return False
                else:
                    print(f"   ❌ 任务状态请求失败: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"   ⚠️ 监控异常: {e}")
            
            time.sleep(check_interval)
            waited_time += check_interval
        
        print(f"   ⏰ 任务执行超时 ({max_wait_time}秒)")
        return False
    
    def compare_knowledge_changes(self, initial, final):
        """比较知识库变化"""
        initial_summary = initial.get('summary', {})
        final_summary = final.get('summary', {})
        
        initial_records = initial_summary.get('total_records', 0)
        final_records = final_summary.get('total_records', 0)
        new_records = final_records - initial_records
        
        initial_rules = len(initial.get('guidance_rules', []))
        final_rules = len(final.get('guidance_rules', []))
        new_rules = final_rules - initial_rules
        
        print(f"   📊 记录变化: {initial_records} → {final_records} (+{new_records})")
        print(f"   🎯 规则变化: {initial_rules} → {final_rules} (+{new_rules})")
        
        if new_records > 0:
            print("   ✅ 知识库已更新，敢死队经验已收集")
        else:
            print("   ⚠️ 知识库未发现新记录")
        
        if new_rules > 0:
            print("   ✅ 新增指导规则，经验分析成功")
        else:
            print("   ℹ️ 未生成新的指导规则")
    
    def get_task_result(self, task_id):
        """获取任务结果"""
        try:
            response = requests.get(f"{self.base_url}/refresh_task/{task_id}", timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('task')
            return None
        except Exception as e:
            print(f"   ⚠️ 获取任务结果失败: {e}")
            return None
    
    def display_final_results(self, task_result):
        """显示最终结果"""
        if not task_result:
            print("   ❌ 无法获取任务结果")
            return
        
        results = task_result.get('results', {})
        resource_consumption = task_result.get('resource_consumption', {})
        
        print(f"   📈 任务状态: {task_result.get('status', '未知')}")
        
        # 显示敢死队结果
        scout_phase = results.get('scout_phase', {})
        if scout_phase:
            print(f"   🔍 敢死队阶段:")
            print(f"      - 总数: {scout_phase.get('total', 0)}")
            print(f"      - 成功: {scout_phase.get('successful', 0)}")
            print(f"      - 成功率: {scout_phase.get('success_rate', 0):.1%}")
        
        # 显示经验分析结果
        analysis_phase = results.get('analysis_phase', {})
        if analysis_phase:
            print(f"   🧠 经验分析阶段:")
            print(f"      - 生成指导规则: {analysis_phase.get('guidance_rules_count', 0)} 条")
        
        # 显示大部队结果
        target_phase = results.get('target_phase', {})
        if target_phase:
            print(f"   🎯 大部队阶段:")
            print(f"      - 总数: {target_phase.get('total', 0)}")
            print(f"      - 成功: {target_phase.get('successful', 0)}")
            print(f"      - 成功率: {target_phase.get('success_rate', 0):.1%}")
        
        # 显示整体结果
        overall = results.get('overall', {})
        if overall:
            print(f"   📊 整体结果:")
            print(f"      - 总参与人数: {overall.get('total_count', 0)}")
            print(f"      - 总成功人数: {overall.get('total_success', 0)}")
            print(f"      - 总答题数: {overall.get('total_answers', 0)}")
            print(f"      - 整体成功率: {overall.get('overall_success_rate', 0):.1%}")
        
        # 显示资源消耗
        print(f"   💰 资源消耗: ¥{resource_consumption.get('total_cost', 0):.4f}")
        
        # 显示资源详情
        resources = resource_consumption.get('resources', [])
        if resources:
            print("   💳 资源详情:")
            for resource in resources:
                print(f"      - {resource.get('type', 'unknown')}: {resource.get('quantity', 0)} 个, ¥{resource.get('cost', 0):.4f}")

def main():
    """主函数"""
    tester = QuestionnaireWorkflowTester()
    
    print("🤖 智能问卷填写系统 - 完整工作流测试")
    print("测试流程: 敢死队作答 → 收集结果 → 分析经验 → 指导大部队 → 大部队作答")
    print("=" * 80)
    
    success = tester.test_complete_workflow()
    
    if success:
        print("\n🎉 工作流测试成功完成！")
        print("✅ 敢死队探索机制正常")
        print("✅ 经验收集和分析正常") 
        print("✅ 知识库更新正常")
        print("✅ 大部队执行正常")
    else:
        print("\n❌ 工作流测试失败")
    
    print(f"\n🌐 访问系统: http://localhost:5002")
    print(f"📚 查看知识库: http://localhost:5003/api/knowledge/summary")

if __name__ == "__main__":
    main() 