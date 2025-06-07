#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷系统启动脚本
包含基础检查和错误修复
"""

import sys
import os
import subprocess
import ast

def check_syntax(file_path):
    """检查文件语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"第{e.lineno}行: {e.msg}"
    except Exception as e:
        return False, str(e)

def main():
    """主函数"""
    print("🚀 智能问卷系统启动检查")
    print("=" * 40)
    
    # 检查关键文件语法
    critical_files = [
        'main.py',
        'adspower_browser_use_integration.py'
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            is_valid, error = check_syntax(file_path)
            if is_valid:
                print(f"✅ {file_path} - 语法正确")
            else:
                print(f"❌ {file_path} - 语法错误: {error}")
                return False
        else:
            print(f"❌ {file_path} - 文件不存在")
            return False
    
    print("\n🎯 所有检查通过，启动系统...")
    print("🌐 系统将在 http://localhost:5002 启动")
    print("💡 按 Ctrl+C 停止服务")
    print("=" * 40)
    
    # 启动主程序
    try:
        subprocess.run([sys.executable, 'main.py'], check=False)
    except KeyboardInterrupt:
        print("\n👋 系统已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 