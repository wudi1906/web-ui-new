#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统重启脚本
停止当前服务并启动正确的智能问卷填写系统
"""

import subprocess
import time
import sys
import os
import signal
import requests
import psutil

def kill_processes_on_port(port):
    """杀死占用指定端口的进程"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                connections = proc.info['connections']
                if connections:
                    for conn in connections:
                        if conn.laddr.port == port:
                            print(f"🔪 杀死进程 {proc.info['pid']} ({proc.info['name']}) 占用端口 {port}")
                            proc.kill()
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        print(f"❌ 杀死端口进程失败: {e}")
    
    return False

def check_service(port, timeout=2):
    """检查服务是否运行"""
    try:
        response = requests.get(f'http://localhost:{port}', timeout=timeout)
        return True
    except:
        return False

def start_knowledge_api():
    """启动知识库API"""
    print("🚀 启动知识库API服务...")
    
    # 检查是否已运行
    if check_service(5003):
        print("✅ 知识库API已运行")
        return True
    
    try:
        process = subprocess.Popen([
            sys.executable, 'knowledge_base_api.py'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待启动
        for i in range(10):
            if check_service(5003):
                print("✅ 知识库API启动成功")
                return True
            time.sleep(1)
            print(f"⏳ 等待知识库API启动... ({i+1}/10)")
        
        print("❌ 知识库API启动失败")
        return False
        
    except Exception as e:
        print(f"❌ 启动知识库API失败: {e}")
        return False

def start_main_web():
    """启动主Web服务"""
    print("🚀 启动主Web服务...")
    
    try:
        process = subprocess.Popen([
            sys.executable, 'app.py'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待启动
        for i in range(15):
            if check_service(5001):
                print("✅ 主Web服务启动成功")
                return True
            time.sleep(1)
            print(f"⏳ 等待主Web服务启动... ({i+1}/15)")
        
        print("❌ 主Web服务启动失败")
        return False
        
    except Exception as e:
        print(f"❌ 启动主Web服务失败: {e}")
        return False

def verify_system():
    """验证系统是否正确启动"""
    print("\n🧪 验证系统...")
    
    # 检查知识库API
    try:
        response = requests.get('http://localhost:5003/api/knowledge/summary', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ 知识库API验证通过")
            else:
                print("⚠️ 知识库API返回失败状态")
        else:
            print(f"❌ 知识库API验证失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 知识库API验证失败: {e}")
    
    # 检查主Web服务
    try:
        response = requests.get('http://localhost:5001/', timeout=5)
        if response.status_code == 200:
            content = response.text
            if "智能问卷自动填写系统" in content:
                print("✅ 主Web服务验证通过 - 正确的系统")
            else:
                print("⚠️ 主Web服务运行但内容不正确")
                print(f"   页面标题: {content[:100]}...")
        else:
            print(f"❌ 主Web服务验证失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 主Web服务验证失败: {e}")
    
    # 检查系统状态API
    try:
        response = requests.get('http://localhost:5001/system_status', timeout=5)
        if response.status_code == 200:
            print("✅ 系统状态API验证通过")
        else:
            print(f"❌ 系统状态API验证失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 系统状态API验证失败: {e}")

def main():
    """主函数"""
    print("🔄 重启智能问卷填写系统")
    print("=" * 60)
    
    # 1. 停止当前服务
    print("⏹️ 停止当前服务...")
    
    # 杀死端口5001上的进程
    if kill_processes_on_port(5001):
        print("✅ 已停止端口5001上的服务")
        time.sleep(2)
    else:
        print("ℹ️ 端口5001没有运行的服务")
    
    # 杀死端口5003上的进程（如果需要）
    if not check_service(5003):
        print("ℹ️ 端口5003没有运行的服务")
    
    # 2. 启动知识库API
    if not start_knowledge_api():
        print("❌ 知识库API启动失败，退出")
        return False
    
    time.sleep(2)
    
    # 3. 启动主Web服务
    if not start_main_web():
        print("❌ 主Web服务启动失败，退出")
        return False
    
    time.sleep(3)
    
    # 4. 验证系统
    verify_system()
    
    print("\n🎉 系统重启完成！")
    print("\n🌐 访问地址:")
    print("   主界面: http://localhost:5001")
    print("   知识库API: http://localhost:5003/api/knowledge/summary")
    print("   系统状态: http://localhost:5001/system_status")
    
    print("\n💡 提示:")
    print("   - 系统已在后台运行")
    print("   - 可以直接访问Web界面")
    print("   - 如需停止，请使用 kill_processes_on_port() 函数")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 操作被用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 重启失败: {e}")
        sys.exit(1) 