#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷填写系统 - 快速启动脚本
"""

import subprocess
import sys
import time
import requests
import os

def check_dependencies():
    """检查依赖项"""
    print("🔍 检查系统依赖...")
    
    required_packages = [
        "flask",
        "flask_cors", 
        "pymysql",
        "requests",
        "browser_use",
        "langchain_google_genai"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (缺失)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依赖项检查通过")
    return True

def check_database_connection():
    """检查数据库连接"""
    print("\n🔍 检查数据库连接...")
    
    try:
        import pymysql
        
        # 数据库配置
        DB_CONFIG = {
            "host": "192.168.50.137",
            "port": 3306,
            "user": "root",
            "password": "123456",
            "database": "wenjuan",
            "charset": "utf8mb4"
        }
        
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        connection.close()
        print("✅ 数据库连接正常")
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("请检查数据库配置和网络连接")
        return False

def start_main_service():
    """启动主服务"""
    print("\n🚀 启动智能问卷填写系统...")
    
    try:
        # 启动main.py
        process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("⏳ 等待服务启动...")
        time.sleep(5)
        
        # 检查服务是否启动成功
        try:
            response = requests.get("http://localhost:5002/system_status", timeout=10)
            if response.status_code == 200:
                print("✅ 服务启动成功!")
                print("🌐 访问地址: http://localhost:5002")
                return process
            else:
                print(f"❌ 服务启动失败: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 服务连接失败: {e}")
            return None
            
    except Exception as e:
        print(f"❌ 启动服务失败: {e}")
        return None

def show_usage_guide():
    """显示使用指南"""
    print("\n" + "=" * 60)
    print("📖 使用指南")
    print("=" * 60)
    print("🎯 系统功能:")
    print("  1️⃣ 敢死队探索: 少数数字人先行探索问卷")
    print("  2️⃣ 经验分析: 自动分析敢死队的成功经验")
    print("  3️⃣ 智能指导: 生成指导规则提升成功率")
    print("  4️⃣ 大部队执行: 大规模自动化问卷填写")
    print("  5️⃣ 多窗口布局: 智能排布浏览器窗口")
    print()
    print("🔧 使用步骤:")
    print("  1. 在Web界面输入问卷URL")
    print("  2. 设置敢死队和大部队人数")
    print("  3. 点击'开始执行完整任务流程'")
    print("  4. 监控任务执行状态")
    print("  5. 查看结果和知识库更新")
    print()
    print("⚠️ 注意事项:")
    print("  • 确保AdsPower已启动并配置正确")
    print("  • 青果代理账户余额充足")
    print("  • Gemini API密钥有效")
    print("  • 数据库连接正常")
    print("=" * 60)

def main():
    """主函数"""
    print("🤖 智能问卷填写系统 - 快速启动")
    print("=" * 60)
    
    # 步骤1: 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请安装缺失的包后重试")
        return
    
    # 步骤2: 检查数据库
    if not check_database_connection():
        print("\n❌ 数据库连接失败，请检查配置后重试")
        return
    
    # 步骤3: 启动服务
    process = start_main_service()
    if not process:
        print("\n❌ 服务启动失败")
        return
    
    # 步骤4: 显示使用指南
    show_usage_guide()
    
    print("\n🎉 系统已成功启动!")
    print("💡 按 Ctrl+C 停止服务")
    
    try:
        # 保持服务运行
        process.wait()
    except KeyboardInterrupt:
        print("\n⏹️ 正在停止服务...")
        process.terminate()
        process.wait()
        print("✅ 服务已停止")

if __name__ == "__main__":
    main() 