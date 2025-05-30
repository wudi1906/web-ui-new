#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整系统启动脚本
按顺序启动所有必要的服务
"""

import subprocess
import time
import sys
import os
import signal
import requests
from threading import Thread

class SystemLauncher:
    """系统启动器"""
    
    def __init__(self):
        self.processes = []
        self.services = {
            'knowledge_api': {'port': 5003, 'process': None, 'status': 'stopped'},
            'main_web': {'port': 5001, 'process': None, 'status': 'stopped'}
        }
    
    def check_port(self, port):
        """检查端口是否可用"""
        try:
            response = requests.get(f'http://localhost:{port}', timeout=2)
            return True
        except:
            return False
    
    def start_knowledge_api(self):
        """启动知识库API服务"""
        print("🚀 启动知识库API服务 (端口5003)...")
        try:
            process = subprocess.Popen([
                sys.executable, 'knowledge_base_api.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.services['knowledge_api']['process'] = process
            self.processes.append(process)
            
            # 等待服务启动
            for i in range(10):
                if self.check_port(5003):
                    print("✅ 知识库API服务启动成功")
                    self.services['knowledge_api']['status'] = 'running'
                    return True
                time.sleep(1)
                print(f"⏳ 等待知识库API启动... ({i+1}/10)")
            
            print("❌ 知识库API服务启动失败")
            return False
            
        except Exception as e:
            print(f"❌ 启动知识库API失败: {e}")
            return False
    
    def start_main_web(self):
        """启动主Web服务"""
        print("🚀 启动主Web服务 (端口5001)...")
        try:
            process = subprocess.Popen([
                sys.executable, 'app.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.services['main_web']['process'] = process
            self.processes.append(process)
            
            # 等待服务启动
            for i in range(10):
                if self.check_port(5001):
                    print("✅ 主Web服务启动成功")
                    self.services['main_web']['status'] = 'running'
                    return True
                time.sleep(1)
                print(f"⏳ 等待主Web服务启动... ({i+1}/10)")
            
            print("❌ 主Web服务启动失败")
            return False
            
        except Exception as e:
            print(f"❌ 启动主Web服务失败: {e}")
            return False
    
    def test_system_integration(self):
        """测试系统集成"""
        print("\n🧪 测试系统集成...")
        
        # 测试知识库API
        try:
            response = requests.get('http://localhost:5003/api/knowledge/summary', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ 知识库API测试通过")
                    summary = data.get('data', {}).get('summary', {})
                    print(f"   📊 知识库记录: {summary.get('total_records', 0)} 条")
                else:
                    print("⚠️ 知识库API返回失败状态")
            else:
                print(f"❌ 知识库API测试失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ 知识库API测试失败: {e}")
        
        # 测试主Web服务
        try:
            response = requests.get('http://localhost:5001/', timeout=5)
            if response.status_code == 200:
                print("✅ 主Web服务测试通过")
            else:
                print(f"❌ 主Web服务测试失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ 主Web服务测试失败: {e}")
    
    def show_status(self):
        """显示系统状态"""
        print("\n📊 系统状态:")
        print("=" * 50)
        for service, info in self.services.items():
            status_icon = "✅" if info['status'] == 'running' else "❌"
            print(f"{status_icon} {service}: {info['status']} (端口 {info['port']})")
        
        print(f"\n🌐 访问地址:")
        print(f"   主界面: http://localhost:5001")
        print(f"   知识库API: http://localhost:5003/api/knowledge/summary")
    
    def cleanup(self):
        """清理所有进程"""
        print("\n🧹 清理系统进程...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print("✅ 进程已正常终止")
            except subprocess.TimeoutExpired:
                process.kill()
                print("⚠️ 进程被强制终止")
            except Exception as e:
                print(f"❌ 清理进程失败: {e}")
    
    def start_complete_system(self):
        """启动完整系统"""
        print("🎯 启动智能问卷填写系统")
        print("=" * 60)
        
        try:
            # 1. 启动知识库API
            if not self.start_knowledge_api():
                print("❌ 知识库API启动失败，系统无法完整运行")
                return False
            
            time.sleep(2)
            
            # 2. 启动主Web服务
            if not self.start_main_web():
                print("❌ 主Web服务启动失败")
                return False
            
            time.sleep(2)
            
            # 3. 测试系统集成
            self.test_system_integration()
            
            # 4. 显示状态
            self.show_status()
            
            print("\n🎉 系统启动完成！")
            print("💡 提示: 按 Ctrl+C 停止所有服务")
            
            # 保持运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n⏹️ 收到停止信号...")
                self.cleanup()
                print("👋 系统已停止")
                return True
                
        except Exception as e:
            print(f"❌ 系统启动失败: {e}")
            self.cleanup()
            return False

def main():
    """主函数"""
    launcher = SystemLauncher()
    
    # 注册信号处理器
    def signal_handler(signum, frame):
        print("\n⏹️ 收到停止信号...")
        launcher.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动系统
    success = launcher.start_complete_system()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 