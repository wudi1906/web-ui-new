#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境变量配置脚本
帮助用户快速设置智能问卷系统的必要环境变量
"""

import os
import sys

def setup_environment():
    """设置环境变量"""
    print("🔧 智能问卷系统环境配置")
    print("=" * 50)
    
    # 检查.env文件是否存在
    env_file = ".env"
    env_exists = os.path.exists(env_file)
    
    if env_exists:
        print(f"✅ 发现现有 {env_file} 文件")
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print("📋 当前配置:")
            print(content)
    else:
        print(f"📝 创建新的 {env_file} 文件")
    
    print("\n🔑 请输入您的API密钥配置:")
    
    # Gemini API密钥
    gemini_api_key = input("Gemini API密钥 (GOOGLE_API_KEY): ").strip()
    if not gemini_api_key:
        print("⚠️ 未设置Gemini API密钥，系统将无法调用AI模型")
    
    # 询问是否要配置其他服务
    print("\n🌐 是否配置其他可选服务？")
    
    # 青果代理配置
    setup_proxy = input("是否配置青果代理？(y/n): ").lower().startswith('y')
    qingguo_user = ""
    qingguo_pass = ""
    if setup_proxy:
        qingguo_user = input("青果代理用户名: ").strip()
        qingguo_pass = input("青果代理密码: ").strip()
    
    # 生成.env文件内容
    env_content = "# 智能问卷系统环境配置\n"
    env_content += "# 由setup_env.py自动生成\n\n"
    
    # Gemini配置
    env_content += "# Gemini AI配置\n"
    if gemini_api_key:
        env_content += f"GOOGLE_API_KEY={gemini_api_key}\n"
    else:
        env_content += "# GOOGLE_API_KEY=你的Gemini_API密钥\n"
    
    # 青果代理配置
    env_content += "\n# 青果代理配置\n"
    if qingguo_user and qingguo_pass:
        env_content += f"QINGGUO_USERNAME={qingguo_user}\n"
        env_content += f"QINGGUO_PASSWORD={qingguo_pass}\n"
    else:
        env_content += "# QINGGUO_USERNAME=你的青果代理用户名\n"
        env_content += "# QINGGUO_PASSWORD=你的青果代理密码\n"
    
    # 其他配置
    env_content += "\n# 其他配置\n"
    env_content += "BROWSER_USE_DISABLE_MEMORY=true\n"
    env_content += "# ADSPOWER_API_KEY=你的AdsPower_API密钥\n"
    
    # 保存文件
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"\n✅ 配置已保存到 {env_file}")
        
        # 设置当前进程的环境变量
        if gemini_api_key:
            os.environ["GOOGLE_API_KEY"] = gemini_api_key
            print("✅ Gemini API密钥已设置到当前会话")
        
        if qingguo_user and qingguo_pass:
            os.environ["QINGGUO_USERNAME"] = qingguo_user
            os.environ["QINGGUO_PASSWORD"] = qingguo_pass
            print("✅ 青果代理配置已设置到当前会话")
        
        os.environ["BROWSER_USE_DISABLE_MEMORY"] = "true"
        
        print("\n🚀 环境配置完成！")
        print("现在可以启动Web界面或直接运行问卷填写任务")
        
    except Exception as e:
        print(f"❌ 保存配置文件失败: {e}")
        return False
    
    return True

def show_usage_instructions():
    """显示使用说明"""
    print("\n📖 使用说明:")
    print("1. 启动Web界面: python main.py")
    print("2. 直接测试系统: python test_optimized_system.py")
    print("3. 如需修改配置，重新运行: python setup_env.py")
    
    print("\n💡 系统特点:")
    print("- ✅ AdsPower配置文件管理和复用")
    print("- ✅ 自动降级为标准浏览器模式")
    print("- ✅ 小社会系统数字人集成")
    print("- ✅ 分批执行避免资源竞争")
    print("- ✅ 完整的敢死队→分析→大部队流程")

if __name__ == "__main__":
    print("🧪 智能问卷填写系统 - 环境配置")
    
    if setup_environment():
        show_usage_instructions()
    else:
        print("❌ 环境配置失败，请检查错误信息")
        sys.exit(1) 