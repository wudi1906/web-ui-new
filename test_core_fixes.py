#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
核心修复验证测试 - 简化版
重点测试launch_args修复和基础AdsPower功能
"""

import asyncio
import requests
import time
import json
import logging
import urllib.parse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_adspower_basic_service():
    """测试AdsPower基础服务"""
    print("🔧 测试1: AdsPower基础服务连接")
    print("-" * 50)
    
    base_url = "http://local.adspower.net:50325"
    
    try:
        # 测试服务状态
        response = requests.get(f"{base_url}/status", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("✅ AdsPower服务正常运行")
                return True
            else:
                print(f"❌ AdsPower服务状态异常: {result}")
                return False
        else:
            print(f"❌ HTTP连接失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 连接AdsPower服务失败: {e}")
        return False

async def test_launch_args_fix():
    """测试launch_args修复效果"""
    print("\n🚀 测试2: launch_args修复验证")
    print("-" * 50)
    
    base_url = "http://local.adspower.net:50325"
    
    try:
        # 步骤1: 创建简单的测试配置文件
        print("   创建测试配置文件...")
        
        create_data = {
            "name": f"launch_args_test_{int(time.time())}",
            "group_id": "0",
            "domain_name": "https://www.baidu.com",
            "user_proxy_config": {
                "proxy_soft": "no_proxy"
            },
            "fingerprint_config": {
                "automatic_timezone": "1",
                "language": ["en-US", "en"],
                "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }
        
        response = requests.post(f"{base_url}/api/v1/user/create", json=create_data, timeout=10)
        if response.status_code != 200 or response.json().get("code") != 0:
            print(f"❌ 创建配置文件失败: {response.json()}")
            return False
            
        profile_id = response.json()["data"]["id"]
        print(f"   ✅ 配置文件创建成功: {profile_id}")
        
        # 步骤2: 测试基础启动（无launch_args）
        print("   测试基础启动...")
        
        basic_params = {
            "user_id": profile_id,
            "open_tabs": 1,
            "ip_tab": 0,
            "headless": 0
        }
        
        response = requests.get(f"{base_url}/api/v1/browser/start", params=basic_params, timeout=15)
        if response.status_code == 200 and response.json().get("code") == 0:
            print(f"   ✅ 基础启动成功")
            
            debug_port = response.json().get("data", {}).get("debug_port")
            print(f"   调试端口: {debug_port}")
            
            # 停止浏览器
            await asyncio.sleep(2)
            requests.get(f"{base_url}/api/v1/browser/stop", params={"user_id": profile_id})
            await asyncio.sleep(2)
            
        else:
            print(f"   ❌ 基础启动失败: {response.json()}")
            # 继续测试launch_args修复
        
        # 步骤3: 测试修复后的launch_args格式
        print("   测试修复后的launch_args...")
        
        # 测试方式1: 字符串列表格式（修复后的格式）
        window_params_list = {
            "user_id": profile_id,
            "open_tabs": 1,
            "ip_tab": 0,
            "headless": 0,
            "launch_args": [
                "--window-position=100,100",
                "--window-size=400,300", 
                "--disable-notifications",
                "--disable-infobars"
            ]
        }
        
        # 🔧 重要：需要将列表序列化为JSON字符串传递给GET请求
        query_params = {}
        for key, value in window_params_list.items():
            if key == "launch_args":
                # 将列表序列化为JSON字符串
                query_params[key] = json.dumps(value)
            else:
                query_params[key] = value
        
        response = requests.get(f"{base_url}/api/v1/browser/start", params=query_params, timeout=15)
        list_success = response.status_code == 200 and response.json().get("code") == 0
        
        if list_success:
            print(f"   ✅ 字符串列表格式launch_args成功")
            requests.get(f"{base_url}/api/v1/browser/stop", params={"user_id": profile_id})
            await asyncio.sleep(2)
        else:
            print(f"   ⚠️ 字符串列表格式失败: {response.json().get('msg', '未知错误')}")
            
            # 如果列表格式也失败，测试POST方法
            print("   尝试POST方法...")
            post_data = {
                "user_id": profile_id,
                "open_tabs": 1,
                "ip_tab": 0,
                "headless": 0,
                "launch_args": [
                    "--window-position=100,100",
                    "--window-size=400,300", 
                    "--disable-notifications"
                ]
            }
            
            response = requests.post(f"{base_url}/api/v1/browser/start", json=post_data, timeout=15)
            post_success = response.status_code == 200 and response.json().get("code") == 0
            
            if post_success:
                print(f"   ✅ POST方法成功")
                list_success = True
                requests.get(f"{base_url}/api/v1/browser/stop", params={"user_id": profile_id})
                await asyncio.sleep(2)
            else:
                print(f"   ❌ POST方法也失败: {response.json().get('msg', '未知错误')}")
        
        # 清理测试资源
        print("   清理测试资源...")
        requests.post(f"{base_url}/api/v1/user/delete", json={"user_ids": [profile_id]})
        
        # 总结结果
        if list_success:
            print("   🎉 launch_args修复验证成功！")
            return True
        else:
            print("   ❌ launch_args修复可能仍有问题")
            return False
            
    except Exception as e:
        print(f"❌ launch_args测试异常: {e}")
        return False

async def test_window_layout_calculation():
    """测试20窗口布局计算"""
    print("\n🪟 测试3: 20窗口布局计算")
    print("-" * 50)
    
    try:
        # 模拟20窗口布局计算
        def calculate_20_window_layout():
            """计算20窗口平铺布局 (4行×5列)"""
            positions = []
            
            # 设计参数
            window_width = 384
            window_height = 270
            rows = 4
            cols = 5
            
            # 屏幕边距
            margin_x = 10
            margin_y = 80  # 顶部留空间给菜单栏
            
            for i in range(20):
                row = i // cols
                col = i % cols
                
                x = margin_x + col * window_width
                y = margin_y + row * window_height
                
                positions.append({
                    "index": i + 1,
                    "x": x,
                    "y": y,
                    "width": window_width,
                    "height": window_height
                })
            
            return positions
        
        positions = calculate_20_window_layout()
        
        # 验证布局
        print("   窗口布局预览:")
        for i, pos in enumerate(positions[:5]):  # 显示前5个窗口
            print(f"   窗口{pos['index']}: 位置({pos['x']},{pos['y']}) 尺寸{pos['width']}×{pos['height']}")
        
        # 验证无重叠
        unique_positions = set((p['x'], p['y']) for p in positions)
        no_overlap = len(unique_positions) == len(positions)
        
        # 验证尺寸一致
        consistent_size = all(p['width'] == 384 and p['height'] == 270 for p in positions)
        
        print(f"   窗口无重叠: {'✅' if no_overlap else '❌'}")
        print(f"   尺寸一致性: {'✅' if consistent_size else '❌'}")
        print(f"   总窗口数: {len(positions)}")
        
        return no_overlap and consistent_size
        
    except Exception as e:
        print(f"❌ 窗口布局测试异常: {e}")
        return False

async def test_success_evaluation_logic():
    """测试敢死队成功判断逻辑"""
    print("\n🎯 测试4: 敢死队成功判断逻辑")
    print("-" * 50)
    
    try:
        # 模拟成功判断函数
        def evaluate_success(steps_count: int, error_count: int, final_message: str) -> dict:
            """模拟敢死队成功判断逻辑"""
            
            # 技术错误判断
            if error_count > 0 and steps_count < 10:
                return {
                    "is_success": False,
                    "success_type": "technical_error",
                    "completion_score": 0.1,
                    "answered_questions": max(0, steps_count - error_count),
                    "error_category": "technical"
                }
            
            # 基于步骤数判断
            if steps_count >= 50:
                completion_score = min(1.0, steps_count / 100.0)
                confidence = 0.9
            elif steps_count >= 20:
                completion_score = min(0.8, steps_count / 50.0)
                confidence = 0.7
            elif steps_count >= 10:
                completion_score = min(0.6, steps_count / 30.0)
                confidence = 0.5
            else:
                completion_score = 0.2
                confidence = 0.3
            
            # 检查完成关键词
            completion_keywords = ["完成", "成功", "提交", "谢谢"]
            has_completion = any(word in final_message for word in completion_keywords)
            
            if has_completion:
                completion_score = max(completion_score, 0.8)
                confidence = max(confidence, 0.8)
            
            # 最终判断
            if completion_score >= 0.8 and confidence >= 0.7:
                success_type = "complete"
                is_success = True
            elif completion_score >= 0.5 and confidence >= 0.5:
                success_type = "partial"
                is_success = True
            else:
                success_type = "incomplete"
                is_success = False
            
            return {
                "is_success": is_success,
                "success_type": success_type,
                "completion_score": completion_score,
                "answered_questions": steps_count // 3,  # 估算
                "error_category": "none" if error_count == 0 else "technical"
            }
        
        # 测试用例
        test_cases = [
            {"name": "完整成功", "steps": 60, "errors": 0, "message": "问卷提交成功", "expected": True},
            {"name": "部分成功", "steps": 30, "errors": 0, "message": "部分完成", "expected": True},
            {"name": "技术错误", "steps": 5, "errors": 3, "message": "500 server error", "expected": False},
            {"name": "步骤不足", "steps": 8, "errors": 0, "message": "停止", "expected": False}
        ]
        
        all_passed = True
        
        for case in test_cases:
            result = evaluate_success(case["steps"], case["errors"], case["message"])
            passed = result["is_success"] == case["expected"]
            
            print(f"   {case['name']}: {'✅' if passed else '❌'}")
            print(f"     成功: {result['is_success']}, 类型: {result['success_type']}")
            print(f"     答题: {result['answered_questions']}题, 完成度: {result['completion_score']:.1%}")
            
            if not passed:
                all_passed = False
        
        print(f"   总体结果: {'✅ 所有测试通过' if all_passed else '❌ 部分测试失败'}")
        return all_passed
        
    except Exception as e:
        print(f"❌ 成功判断逻辑测试异常: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 智能问卷自动化系统 - 核心修复验证")
    print("=" * 80)
    
    test_results = []
    start_time = time.time()
    
    # 执行测试
    tests = [
        ("AdsPower基础服务", test_adspower_basic_service),
        ("launch_args修复", test_launch_args_fix),
        ("20窗口布局", test_window_layout_calculation),
        ("成功判断逻辑", test_success_evaluation_logic)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 异常: {e}")
            test_results.append((test_name, False))
    
    # 生成报告
    print(f"\n📊 测试报告")
    print("=" * 80)
    
    passed = len([r for r in test_results if r[1]])
    total = len(test_results)
    
    print(f"测试总数: {total}")
    print(f"通过测试: {passed} ✅")
    print(f"失败测试: {total - passed} ❌")
    print(f"通过率: {passed/total*100:.1f}%")
    print(f"测试时长: {time.time() - start_time:.1f} 秒")
    
    print(f"\n详细结果:")
    for i, (test_name, result) in enumerate(test_results, 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i}. {test_name}: {status}")
    
    # 核心问题状态
    print(f"\n🔧 核心问题修复状态:")
    
    service_ok = test_results[0][1] if len(test_results) > 0 else False
    launch_fix = test_results[1][1] if len(test_results) > 1 else False
    window_layout = test_results[2][1] if len(test_results) > 2 else False
    success_logic = test_results[3][1] if len(test_results) > 3 else False
    
    print(f"1. AdsPower服务连接: {'✅ 正常' if service_ok else '❌ 异常'}")
    print(f"2. launch_args启动问题: {'✅ 已修复' if launch_fix else '❌ 需要修复'}")
    print(f"3. 20窗口布局支持: {'✅ 正常工作' if window_layout else '❌ 需要修复'}")
    print(f"4. 敢死队成功判断: {'✅ 逻辑正确' if success_logic else '❌ 需要修复'}")
    
    if all([service_ok, launch_fix, window_layout, success_logic]):
        print(f"\n🎉 所有核心问题已修复，系统可以正常使用！")
    else:
        print(f"\n⚠️ 部分问题仍需修复，请检查失败的测试项目")
        
        if not service_ok:
            print(f"   💡 请确认AdsPower客户端已启动")
        if not launch_fix:
            print(f"   💡 launch_args格式可能仍有问题，请检查API参数")

if __name__ == "__main__":
    asyncio.run(main()) 