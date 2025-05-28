#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷自动填写系统 - Web界面启动脚本
"""

import sys
import subprocess
import os

def check_and_install_flask():
    """检查并安装Flask依赖"""
    try:
        import flask
        print("✅ Flask已安装")
        return True
    except ImportError:
        print("⚠️ Flask未安装，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
            print("✅ Flask安装成功")
            return True
        except subprocess.CalledProcessError:
            print("❌ Flask安装失败，请手动安装: pip install flask")
            return False

def main():
    """主函数"""
    print("🚀 启动智能问卷自动填写系统Web界面")
    print("=" * 50)
    
    # 检查Flask依赖
    if not check_and_install_flask():
        return
    
    # 检查必要的系统组件
    print("🔧 检查系统组件...")
    
    # 检查数据库连接
    try:
        from questionnaire_system import DatabaseManager, DB_CONFIG
        db_manager = DatabaseManager(DB_CONFIG)
        connection = db_manager.get_connection()
        connection.close()
        print("✅ 数据库连接正常")
    except Exception as e:
        print(f"⚠️ 数据库连接异常: {e}")
        print("   请确保MySQL服务正在运行")
    
    # 检查小社会系统
    try:
        import requests
        response = requests.get("http://localhost:5001/api/smart-query/query", timeout=5)
        if response.status_code == 405:  # POST方法，GET返回405是正常的
            print("✅ 小社会系统连接正常")
        else:
            print("⚠️ 小社会系统可能未启动")
    except Exception as e:
        print(f"⚠️ 小社会系统连接异常: {e}")
        print("   请确保小社会系统在localhost:5001运行")
    
    # 启动Web界面
    print("\n🌐 启动Web服务器...")
    print("📋 访问地址: http://localhost:5002")
    print("🔧 功能: 任务创建、进度监控、结果查看")
    print("💡 提示: 按Ctrl+C停止服务器")
    print("=" * 50)
    
    try:
        from web_interface import app
        app.run(host='0.0.0.0', port=5002, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Web服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main() 