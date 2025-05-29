#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
问卷系统配置文件
集中管理所有系统配置
"""

import os
from typing import Dict, Any

# 数据库配置
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "192.168.50.137"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "wenjuan"),
    "charset": "utf8mb4"
}

# AdsPower API配置
ADSPOWER_CONFIG = {
    "base_url": os.getenv("ADSPOWER_URL", "http://localhost:50325"),
    "api_key": os.getenv("ADSPOWER_API_KEY", "cd606f2e6e4558c9c9f2980e7017b8e9"),
    "timeout": int(os.getenv("ADSPOWER_TIMEOUT", "30")),
    "api_version": "v1"
}

# 小社会系统配置
XIAOSHE_CONFIG = {
    "base_url": os.getenv("XIAOSHE_URL", "http://localhost:5001"),
    "timeout": int(os.getenv("XIAOSHE_TIMEOUT", "30")),
    "smart_query_endpoint": "/api/smart-query/query"
}

# Browser-use配置
BROWSER_USE_CONFIG = {
    "default_model": "gemini-2.0-flash",
    "temperature": 0.5,
    "max_steps": 200,
    "max_actions_per_step": 20,
    "auto_close": False,
    "headless": False
}

# LLM配置
LLM_CONFIG = {
    "provider": "gemini",
    "model": "gemini-2.0-flash",
    "api_key": "AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8",
    "temperature": 0.5,
    "max_tokens": 4096,
    "timeout": 60,
    "retry_attempts": 3
}

# 问卷系统配置
QUESTIONNAIRE_CONFIG = {
    "default_scout_count": 2,      # 默认敢死队数量
    "default_target_count": 10,    # 默认目标团队数量
    "max_concurrent_browsers": 5,  # 最大并发浏览器数量
    "task_timeout_minutes": 60,    # 任务超时时间（分钟）
    "retry_attempts": 3,           # 重试次数
    "screenshot_enabled": True,    # 是否启用截图
    "knowledge_base_ttl_hours": 24 # 知识库生存时间（小时）
}

# 日志配置
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_enabled": True,
    "file_path": "logs/questionnaire_system.log",
    "max_file_size": "10MB",
    "backup_count": 5
}

# 安全配置
SECURITY_CONFIG = {
    "api_key_required": False,     # 是否需要API密钥
    "rate_limit_enabled": True,    # 是否启用速率限制
    "max_requests_per_minute": 60, # 每分钟最大请求数
    "allowed_domains": [           # 允许的问卷域名
        "wjx.cn",
        "jinshuju.net", 
        "tencent.com",
        "example.com"  # 测试用
    ]
}

# 代理配置
PROXY_CONFIG = {
    "enabled": False,              # 是否启用代理
    "rotation_enabled": True,      # 是否启用代理轮换
    "proxy_list": [               # 代理列表
        # {"type": "http", "host": "proxy1.example.com", "port": 8080},
        # {"type": "socks5", "host": "proxy2.example.com", "port": 1080}
    ],
    "timeout": 10,                # 代理超时时间
    "retry_count": 3              # 代理重试次数
}

def get_config(config_name: str) -> Dict[str, Any]:
    """获取指定配置"""
    config_map = {
        "database": DATABASE_CONFIG,
        "adspower": ADSPOWER_CONFIG,
        "xiaoshe": XIAOSHE_CONFIG,
        "browser_use": BROWSER_USE_CONFIG,
        "llm": LLM_CONFIG,
        "questionnaire": QUESTIONNAIRE_CONFIG,
        "logging": LOGGING_CONFIG,
        "security": SECURITY_CONFIG,
        "proxy": PROXY_CONFIG
    }
    
    return config_map.get(config_name, {})

def validate_config() -> bool:
    """验证配置有效性"""
    try:
        # 检查必要的配置项
        required_configs = [
            ("database", ["host", "port", "user", "password", "database"]),
            ("adspower", ["base_url"]),
            ("xiaoshe", ["base_url"]),
            ("questionnaire", ["default_scout_count", "default_target_count"])
        ]
        
        for config_name, required_keys in required_configs:
            config = get_config(config_name)
            for key in required_keys:
                if key not in config or config[key] is None:
                    print(f"❌ 配置错误: {config_name}.{key} 未设置")
                    return False
        
        print("✅ 配置验证通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False

def print_config_summary():
    """打印配置摘要"""
    print("📋 系统配置摘要:")
    print(f"   数据库: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}")
    print(f"   AdsPower: {ADSPOWER_CONFIG['base_url']}")
    print(f"   小社会系统: {XIAOSHE_CONFIG['base_url']}")
    print(f"   默认敢死队数量: {QUESTIONNAIRE_CONFIG['default_scout_count']}")
    print(f"   默认目标团队数量: {QUESTIONNAIRE_CONFIG['default_target_count']}")
    print(f"   最大并发浏览器: {QUESTIONNAIRE_CONFIG['max_concurrent_browsers']}")
    print(f"   代理启用: {'是' if PROXY_CONFIG['enabled'] else '否'}")
    print(f"   日志级别: {LOGGING_CONFIG['level']}")

if __name__ == "__main__":
    print("🔧 问卷系统配置")
    print("=" * 40)
    print_config_summary()
    print("\n" + "=" * 40)
    validate_config() 