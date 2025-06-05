#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版三阶段智能问卷系统启动器
🔥 包含人类化操作、反检测机制、完整三阶段工作流

功能特性：
1. 敢死队情报收集（增强人类化操作）
2. Gemini AI智能分析
3. 大部队精确执行（反检测策略）
4. Web界面监控
5. 实时进度跟踪
"""

import sys
import os
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'enhanced_system_{int(time.time())}.log')
    ]
)
logger = logging.getLogger(__name__)

def print_banner():
    """打印系统启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     🚀 增强版三阶段智能问卷系统                              ║
║                      Enhanced Three-Stage Intelligent System                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🛡️  反检测人类化操作     ║  🧠  Gemini AI智能分析                          ║
║  🎯  三阶段精确执行       ║  📊  实时监控界面                                ║
║  🔄  自动错误恢复         ║  💾  经验知识积累                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"🕐 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

def check_system_dependencies():
    """检查系统依赖"""
    print("🔍 检查系统依赖...")
    
    dependencies = {
        "main.py": "主控制器",
        "app.py": "Web界面", 
        "adspower_browser_use_integration.py": "增强人类化操作",
        "intelligent_three_stage_core.py": "三阶段智能核心",
        "enhanced_adspower_lifecycle.py": "AdsPower生命周期管理"
    }
    
    missing_files = []
    for file_name, description in dependencies.items():
        if os.path.exists(file_name):
            print(f"  ✅ {description}: {file_name}")
        else:
            print(f"  ❌ {description}: {file_name} (缺失)")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n⚠️ 发现缺失文件: {missing_files}")
        print("请确保所有核心文件都存在")
        return False
    
    print("✅ 所有依赖检查通过\n")
    return True

def check_external_services():
    """检查外部服务状态"""
    print("🌐 检查外部服务状态...")
    
    services = {
        "AdsPower": "localhost:50325",
        "青果代理": "API服务",
        "小社会系统": "localhost:5001", 
        "知识库API": "localhost:5003",
        "Gemini API": "在线服务"
    }
    
    service_status = {}
    for service_name, endpoint in services.items():
        try:
            if service_name == "知识库API":
                import requests
                response = requests.get(f"http://{endpoint}/api/knowledge/summary", timeout=2)
                status = "✅ 在线" if response.status_code == 200 else "⚠️ 异常"
            elif service_name == "AdsPower":
                # 可以添加AdsPower检查逻辑
                status = "⚠️ 需要手动启动"
            else:
                status = "⚠️ 需要检查"
                
            service_status[service_name] = status
            print(f"  {status} {service_name}: {endpoint}")
            
        except Exception as e:
            service_status[service_name] = f"❌ 离线"
            print(f"  ❌ 离线 {service_name}: {endpoint}")
    
    print()
    return service_status

def display_system_features():
    """展示系统特性"""
    print("🔥 增强版系统特性:")
    print("┌─────────────────────────────────────────────────────────────────────────┐")
    print("│ 1. 🛡️ 反检测人类化操作                                                  │")
    print("│    • 多重输入策略 (自然点击、犹豫重试、渐进验证)                          │")
    print("│    • 随机延迟模拟 (思考时间、打字速度、操作间隔)                          │")
    print("│    • 鼠标轨迹伪装 (微动、曲线移动、停顿模拟)                             │")
    print("│    • 智能错误恢复 (困惑行为、重试机制、备用策略)                          │")
    print("│                                                                         │")
    print("│ 2. 🧠 三阶段智能工作流                                                  │")
    print("│    • 敢死队侦察 → Gemini分析 → 大部队执行                               │")
    print("│    • 实时经验收集和策略优化                                              │")
    print("│    • 自适应人群匹配和任务分配                                            │")
    print("│                                                                         │")
    print("│ 3. 📊 完整监控体系                                                      │")
    print("│    • Web界面实时监控                                                     │")
    print("│    • 任务进度可视化                                                      │")
    print("│    • 错误日志和恢复跟踪                                                  │")
    print("└─────────────────────────────────────────────────────────────────────────┘")
    print()

def show_usage_examples():
    """展示使用示例"""
    print("📋 使用示例:")
    print("┌─────────────────────────────────────────────────────────────────────────┐")
    print("│ 1. 启动Web界面:                                                          │")
    print("│    python main.py                                                      │")
    print("│    访问: http://localhost:5001                                         │")
    print("│                                                                         │")
    print("│ 2. 直接执行任务:                                                         │")
    print("│    from intelligent_three_stage_core import ThreeStageIntelligentCore  │")
    print("│    core = ThreeStageIntelligentCore()                                  │")
    print("│    result = await core.execute_complete_three_stage_workflow(          │")
    print("│        questionnaire_url='https://example.com/survey',                 │")
    print("│        scout_count=2, target_count=10                                  │")
    print("│    )                                                                    │")
    print("│                                                                         │")
    print("│ 3. 测试人类化输入:                                                       │")
    print("│    from adspower_browser_use_integration import HumanLikeInputAgent    │")
    print("│    agent = HumanLikeInputAgent(browser_context)                        │")
    print("│    await agent.enhanced_human_like_input(selector, text)               │")
    print("└─────────────────────────────────────────────────────────────────────────┘")
    print()

def start_web_interface():
    """启动Web界面"""
    print("🌐 启动Web界面...")
    try:
        import subprocess
        import sys
        
        # 启动main.py
        process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Web界面已启动")
        print("🔗 访问地址: http://localhost:5001")
        print("📊 系统状态: http://localhost:5001/system_status")
        print("📈 任务监控: http://localhost:5001/active_tasks")
        print()
        
        return process
        
    except Exception as e:
        print(f"❌ Web界面启动失败: {e}")
        return None

async def test_core_functionality():
    """测试核心功能"""
    print("🧪 测试核心功能...")
    
    try:
        # 测试三阶段核心系统
        from intelligent_three_stage_core import ThreeStageIntelligentCore
        core = ThreeStageIntelligentCore()
        print("  ✅ 三阶段智能核心初始化成功")
        
        # 测试AdsPower集成
        from adspower_browser_use_integration import AdsPowerWebUIIntegration, HumanLikeInputAgent
        integration = AdsPowerWebUIIntegration()
        print("  ✅ AdsPower WebUI集成可用")
        print("  ✅ 增强人类化输入代理可用")
        
        # 测试增强生命周期管理
        from enhanced_adspower_lifecycle import AdsPowerLifecycleManager
        lifecycle = AdsPowerLifecycleManager()
        print("  ✅ AdsPower生命周期管理器可用")
        
        print("✅ 核心功能测试通过\n")
        return True
        
    except ImportError as e:
        print(f"  ❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print_banner()
    
    # 1. 检查系统依赖
    if not check_system_dependencies():
        print("❌ 系统依赖检查失败，请修复后重试")
        return
    
    # 2. 检查外部服务
    service_status = check_external_services()
    
    # 3. 展示系统特性
    display_system_features()
    
    # 4. 测试核心功能
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        core_test_passed = loop.run_until_complete(test_core_functionality())
        if not core_test_passed:
            print("⚠️ 核心功能测试失败，但系统仍可启动")
    finally:
        loop.close()
    
    # 5. 展示使用示例
    show_usage_examples()
    
    # 6. 询问是否启动Web界面
    while True:
        choice = input("是否启动Web界面? (y/n/q): ").lower().strip()
        
        if choice in ['y', 'yes', '是']:
            web_process = start_web_interface()
            if web_process:
                try:
                    print("🎯 系统运行中... 按 Ctrl+C 停止")
                    web_process.wait()
                except KeyboardInterrupt:
                    print("\n🛑 正在停止系统...")
                    web_process.terminate()
                    web_process.wait()
                    print("✅ 系统已停止")
            break
            
        elif choice in ['n', 'no', '否']:
            print("📋 您可以稍后手动启动: python main.py")
            break
            
        elif choice in ['q', 'quit', '退出']:
            print("👋 再见!")
            break
            
        else:
            print("请输入 y(启动) / n(不启动) / q(退出)")

if __name__ == "__main__":
    main() 