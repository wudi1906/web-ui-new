#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版智能问卷自动填写系统 - Web界面启动脚本
集成testWenjuanFinal.py和增强系统功能
"""

import os
import sys
import logging
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_system_requirements():
    """检查系统要求"""
    print("🔍 检查系统要求...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    
    print(f"✅ Python版本: {sys.version}")
    
    # 检查必需的模块
    required_modules = [
        'flask',
        'pymysql',
        'asyncio',
        'threading'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} 模块可用")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module} 模块缺失")
    
    if missing_modules:
        print(f"❌ 缺失模块: {', '.join(missing_modules)}")
        print("请运行: pip install flask pymysql")
        return False
    
    # 检查browser-use相关模块
    try:
        import browser_use
        print("✅ browser-use 模块可用")
    except ImportError:
        print("⚠️ browser-use 模块不可用，将使用模拟模式")
    
    # 检查langchain_google_genai
    try:
        import langchain_google_genai
        print("✅ langchain_google_genai 模块可用")
    except ImportError:
        print("⚠️ langchain_google_genai 模块不可用")
    
    # 检查testWenjuanFinal.py
    try:
        import testWenjuanFinal
        print("✅ testWenjuanFinal.py 可用")
    except ImportError:
        print("⚠️ testWenjuanFinal.py 不可用")
    
    return True

def check_environment_variables():
    """检查环境变量"""
    print("\n🔧 检查环境变量...")
    
    # 检查GOOGLE_API_KEY
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if google_api_key:
        print("✅ GOOGLE_API_KEY 已设置")
    else:
        print("⚠️ GOOGLE_API_KEY 未设置，将使用默认密钥")
    
    return True

def check_project_files():
    """检查项目文件"""
    print("\n📁 检查项目文件...")
    
    required_files = [
        'web_interface.py',
        'questionnaire_system.py',
        'enhanced_browser_use_integration.py',
        'phase2_scout_automation.py',
        'demo_enhanced_integration.py'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} 存在")
        else:
            missing_files.append(file)
            print(f"❌ {file} 缺失")
    
    if missing_files:
        print(f"❌ 缺失文件: {', '.join(missing_files)}")
        return False
    
    # 检查templates目录
    if not os.path.exists('templates'):
        print("📁 创建templates目录...")
        os.makedirs('templates', exist_ok=True)
    
    return True

def create_simple_index_template():
    """创建简单的首页模板"""
    template_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>增强版智能问卷自动填写系统</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .feature-card { border: 1px solid #ddd; padding: 20px; border-radius: 8px; background: #f9f9f9; }
        .feature-card h3 { color: #333; margin-top: 0; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-online { background-color: #4CAF50; }
        .status-offline { background-color: #f44336; }
        .status-warning { background-color: #ff9800; }
        .btn { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; margin: 5px; }
        .btn:hover { background-color: #0056b3; }
        .btn-success { background-color: #28a745; }
        .btn-warning { background-color: #ffc107; color: #212529; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 增强版智能问卷自动填写系统</h1>
            <p>基于testWenjuanFinal.py的browser-use webui集成系统</p>
        </div>
        
        <div class="feature-grid">
            <div class="feature-card">
                <h3>🎯 单个数字人答题</h3>
                <p>使用testWenjuanFinal.py中的数字人进行单个问卷填写</p>
                <button class="btn btn-success" onclick="startSingleTask()">启动单任务</button>
            </div>
            
            <div class="feature-card">
                <h3>👥 敢死队任务</h3>
                <p>多个数字人并发探索性答题，积累知识库</p>
                <button class="btn btn-warning" onclick="startScoutMission()">启动敢死队</button>
            </div>
            
            <div class="feature-card">
                <h3>🚀 批量自动化</h3>
                <p>基于知识库的大规模自动化问卷填写</p>
                <button class="btn" onclick="startBatchTask()">启动批量任务</button>
            </div>
            
            <div class="feature-card">
                <h3>📊 系统状态</h3>
                <p id="system-status">正在检查系统状态...</p>
                <button class="btn" onclick="checkSystemStatus()">刷新状态</button>
            </div>
        </div>
        
        <div style="margin-top: 30px; text-align: center;">
            <h3>🔗 快速链接</h3>
            <a href="/active_tasks" class="btn">活跃任务</a>
            <a href="/task_history" class="btn">任务历史</a>
            <a href="/knowledge_base" class="btn">知识库</a>
            <a href="/resource_consumption" class="btn">资源消耗</a>
        </div>
    </div>
    
    <script>
        // 检查系统状态
        function checkSystemStatus() {
            fetch('/system_status')
                .then(response => response.json())
                .then(data => {
                    let statusHtml = '';
                    statusHtml += `<span class="status-indicator ${data.enhanced_system_available ? 'status-online' : 'status-offline'}"></span>增强系统: ${data.enhanced_system_available ? '可用' : '不可用'}<br>`;
                    statusHtml += `<span class="status-indicator ${data.testwenjuan_available ? 'status-online' : 'status-offline'}"></span>testWenjuanFinal: ${data.testwenjuan_available ? '可用' : '不可用'}<br>`;
                    statusHtml += `活跃任务: ${data.active_tasks_count} | 历史任务: ${data.task_history_count}`;
                    document.getElementById('system-status').innerHTML = statusHtml;
                })
                .catch(error => {
                    document.getElementById('system-status').innerHTML = '<span class="status-indicator status-offline"></span>系统状态检查失败';
                });
        }
        
        // 启动单任务
        function startSingleTask() {
            const url = prompt('请输入问卷URL:');
            if (url) {
                fetch('/enhanced_single_task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({questionnaire_url: url, digital_human_id: 1})
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.success ? `任务启动成功: ${data.task_id}` : `启动失败: ${data.error}`);
                });
            }
        }
        
        // 启动敢死队任务
        function startScoutMission() {
            const url = prompt('请输入问卷URL:');
            if (url) {
                fetch('/create_task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({questionnaire_url: url, scout_count: 2, target_count: 5})
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.success ? `敢死队任务启动成功: ${data.task_id}` : `启动失败: ${data.error}`);
                });
            }
        }
        
        // 启动批量任务
        function startBatchTask() {
            const url = prompt('请输入问卷URL:');
            if (url) {
                fetch('/enhanced_batch_task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({questionnaire_url: url, digital_human_ids: [1, 2, 3]})
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.success ? `批量任务启动成功: ${data.task_id}` : `启动失败: ${data.error}`);
                });
            }
        }
        
        // 页面加载时检查系统状态
        window.onload = function() {
            checkSystemStatus();
        };
    </script>
</body>
</html>'''
    
    template_path = 'templates/index.html'
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print(f"✅ 创建首页模板: {template_path}")

def main():
    """主函数"""
    print("🚀 启动增强版智能问卷自动填写系统")
    print("="*60)
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 检查系统要求
    if not check_system_requirements():
        print("\n❌ 系统要求检查失败，请解决上述问题后重试")
        return False
    
    # 检查环境变量
    if not check_environment_variables():
        print("\n❌ 环境变量检查失败")
        return False
    
    # 检查项目文件
    if not check_project_files():
        print("\n❌ 项目文件检查失败")
        return False
    
    # 检查模板文件是否存在，如果不存在才创建
    if not os.path.exists('templates/index.html'):
        print("📁 创建默认模板文件...")
        create_simple_index_template()
    else:
        print("✅ 使用现有模板文件: templates/index.html")
    
    print("\n✅ 所有检查通过，启动Web界面...")
    print("="*60)
    print("🌐 访问地址: http://localhost:5002")
    print("📋 功能特性:")
    print("  • 基于testWenjuanFinal.py的真实browser-use答题")
    print("  • 增强的敢死队自动化系统")
    print("  • 单个/批量/敢死队多种模式")
    print("  • 实时任务监控和结果查看")
    print("  • 详细的资源消耗统计")
    print("="*60)
    
    # 启动Web界面
    try:
        from web_interface import app
        app.run(host='0.0.0.0', port=5002, debug=False)
    except Exception as e:
        print(f"❌ Web界面启动失败: {e}")
        return False

if __name__ == '__main__':
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，系统退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 系统启动失败: {e}")
        sys.exit(1) 