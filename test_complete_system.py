#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整系统测试脚本
验证智能问卷填写系统的所有功能
"""

import requests
import json
import time
from datetime import datetime

class SystemTester:
    """系统测试器"""
    
    def __init__(self):
        self.base_url_web = "http://localhost:5002"
        self.base_url_api = "http://localhost:5003"
        self.test_results = []
    
    def log_test(self, test_name, success, message="", data=None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        
        if data and not success:
            print(f"   详细信息: {data}")
    
    def test_knowledge_api(self):
        """测试知识库API"""
        print("\n🧪 测试知识库API...")
        
        try:
            # 测试概览API
            response = requests.get(f"{self.base_url_api}/api/knowledge/summary", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    summary = data.get('data', {}).get('summary', {})
                    records_count = summary.get('total_records', 0)
                    success_count = summary.get('successful_records', 0)
                    
                    self.log_test(
                        "知识库API概览",
                        True,
                        f"获取到 {records_count} 条记录，{success_count} 条成功",
                        summary
                    )
                    
                    # 测试指导规则
                    guidance_rules = data.get('data', {}).get('guidance_rules', [])
                    self.log_test(
                        "指导规则获取",
                        len(guidance_rules) > 0,
                        f"获取到 {len(guidance_rules)} 条指导规则",
                        guidance_rules[:2] if guidance_rules else None
                    )
                    
                    # 测试最近记录
                    recent_records = data.get('data', {}).get('recent_records', [])
                    self.log_test(
                        "最近记录获取",
                        len(recent_records) > 0,
                        f"获取到 {len(recent_records)} 条最近记录",
                        recent_records[:2] if recent_records else None
                    )
                    
                else:
                    self.log_test("知识库API概览", False, "API返回失败状态", data)
            else:
                self.log_test("知识库API概览", False, f"HTTP状态码: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("知识库API概览", False, f"请求失败: {e}")
    
    def test_web_interface(self):
        """测试Web界面"""
        print("\n🌐 测试Web界面...")
        
        try:
            # 测试主页
            response = requests.get(f"{self.base_url_web}/", timeout=5)
            
            if response.status_code == 200:
                content = response.text
                
                # 检查关键元素
                key_elements = [
                    "智能问卷自动填写系统",
                    "questionnaire-url",
                    "scout-count",
                    "target-count",
                    "开始执行完整任务流程"
                ]
                
                missing_elements = []
                for element in key_elements:
                    if element not in content:
                        missing_elements.append(element)
                
                if not missing_elements:
                    self.log_test("Web界面主页", True, "所有关键元素都存在")
                else:
                    self.log_test("Web界面主页", False, f"缺少元素: {missing_elements}")
                
                # 检查知识库集成
                if "knowledge-area" in content and "localhost:5003" in content:
                    self.log_test("知识库集成", True, "Web界面包含知识库集成代码")
                else:
                    self.log_test("知识库集成", False, "Web界面缺少知识库集成")
                    
            else:
                self.log_test("Web界面主页", False, f"HTTP状态码: {response.status_code}")
                
        except Exception as e:
            self.log_test("Web界面主页", False, f"请求失败: {e}")
    
    def test_system_status(self):
        """测试系统状态"""
        print("\n📊 测试系统状态...")
        
        try:
            response = requests.get(f"{self.base_url_web}/system_status", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查系统组件状态
                components = [
                    "enhanced_system_available",
                    "testwenjuan_available",
                    "active_tasks_count",
                    "task_history_count"
                ]
                
                available_components = []
                for component in components:
                    if component in data:
                        available_components.append(component)
                
                self.log_test(
                    "系统状态API",
                    len(available_components) == len(components),
                    f"可用组件: {len(available_components)}/{len(components)}",
                    data
                )
                
            else:
                self.log_test("系统状态API", False, f"HTTP状态码: {response.status_code}")
                
        except Exception as e:
            self.log_test("系统状态API", False, f"请求失败: {e}")
    
    def test_cross_origin_requests(self):
        """测试跨域请求"""
        print("\n🔗 测试跨域请求...")
        
        try:
            # 模拟从Web界面发起的跨域请求
            headers = {
                'Origin': 'http://localhost:5002',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url_api}/api/knowledge/summary",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                # 检查CORS头
                cors_headers = response.headers.get('Access-Control-Allow-Origin')
                if cors_headers:
                    self.log_test("CORS支持", True, f"CORS头: {cors_headers}")
                else:
                    self.log_test("CORS支持", False, "缺少CORS头")
                    
                # 检查数据
                data = response.json()
                if data.get('success'):
                    self.log_test("跨域数据获取", True, "成功获取知识库数据")
                else:
                    self.log_test("跨域数据获取", False, "数据获取失败")
                    
            else:
                self.log_test("跨域请求", False, f"HTTP状态码: {response.status_code}")
                
        except Exception as e:
            self.log_test("跨域请求", False, f"请求失败: {e}")
    
    def test_data_quality(self):
        """测试数据质量"""
        print("\n📈 测试数据质量...")
        
        try:
            response = requests.get(f"{self.base_url_api}/api/knowledge/summary", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    summary = data.get('data', {}).get('summary', {})
                    recent_records = data.get('data', {}).get('recent_records', [])
                    guidance_rules = data.get('data', {}).get('guidance_rules', [])
                    
                    # 检查数据完整性
                    total_records = summary.get('total_records', 0)
                    successful_records = int(summary.get('successful_records', 0))
                    
                    if total_records > 0:
                        success_rate = successful_records / total_records
                        self.log_test(
                            "数据质量-成功率",
                            success_rate > 0.8,
                            f"成功率: {success_rate:.2%} ({successful_records}/{total_records})"
                        )
                    else:
                        self.log_test("数据质量-成功率", False, "没有数据记录")
                    
                    # 检查指导规则质量
                    if guidance_rules:
                        valid_rules = 0
                        for rule in guidance_rules:
                            if (rule.get('question_content') and 
                                rule.get('answer_choice') and 
                                rule.get('experience_description')):
                                valid_rules += 1
                        
                        rule_quality = valid_rules / len(guidance_rules)
                        self.log_test(
                            "数据质量-指导规则",
                            rule_quality > 0.8,
                            f"规则完整性: {rule_quality:.2%} ({valid_rules}/{len(guidance_rules)})"
                        )
                    else:
                        self.log_test("数据质量-指导规则", False, "没有指导规则")
                    
                    # 检查最近记录的时效性
                    if recent_records:
                        latest_record = recent_records[0]
                        created_at = latest_record.get('created_at')
                        if created_at:
                            self.log_test(
                                "数据质量-时效性",
                                True,
                                f"最新记录时间: {created_at}"
                            )
                        else:
                            self.log_test("数据质量-时效性", False, "记录缺少时间戳")
                    else:
                        self.log_test("数据质量-时效性", False, "没有最近记录")
                        
                else:
                    self.log_test("数据质量", False, "无法获取数据")
                    
            else:
                self.log_test("数据质量", False, f"HTTP状态码: {response.status_code}")
                
        except Exception as e:
            self.log_test("数据质量", False, f"请求失败: {e}")
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📋 系统测试报告")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"通过率: {passed_tests/total_tests:.1%}")
        
        if failed_tests > 0:
            print(f"\n❌ 失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        print(f"\n🎯 系统状态总结:")
        if passed_tests / total_tests >= 0.8:
            print("✅ 系统运行良好，所有核心功能正常")
        elif passed_tests / total_tests >= 0.6:
            print("⚠️ 系统基本可用，但有部分功能需要优化")
        else:
            print("❌ 系统存在严重问题，需要修复")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": passed_tests / total_tests,
            "results": self.test_results
        }
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🎯 开始完整系统测试")
        print("="*60)
        
        # 等待服务启动
        print("⏳ 等待服务启动...")
        time.sleep(3)
        
        # 运行各项测试
        self.test_knowledge_api()
        self.test_web_interface()
        self.test_system_status()
        self.test_cross_origin_requests()
        self.test_data_quality()
        
        # 生成报告
        return self.generate_report()

def main():
    """主函数"""
    tester = SystemTester()
    report = tester.run_all_tests()
    
    # 保存报告
    with open('system_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 详细报告已保存到: system_test_report.json")

if __name__ == "__main__":
    main() 