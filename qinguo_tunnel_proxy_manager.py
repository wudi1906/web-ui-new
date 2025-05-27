#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
青果隧道代理管理器
使用青果隧道代理服务，为每个浏览器分配独立的代理通道
"""

import requests
import time
import random
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class QinguoTunnelProxyManager:
    """青果隧道代理管理器"""
    
    def __init__(self):
        # 青果隧道代理配置
        self.business_id = "k3reh5az"  # 业务标识
        self.auth_key = "A942CE1E"     # Authkey
        self.auth_pwd = "B9FCD013057A" # Authpwd
        self.tunnel_host = "tun-szbhry.qg.net"  # 隧道服务器
        self.tunnel_port = "17790"     # 隧道端口
        
        # 代理管理
        self.allocated_proxies = []  # 已分配的代理通道
        self.session_counter = 0     # 会话计数器
        
    def generate_session_id(self) -> str:
        """生成唯一的会话ID"""
        self.session_counter += 1
        timestamp = int(time.time())
        return f"session_{timestamp}_{self.session_counter}_{random.randint(1000, 9999)}"
    
    def create_tunnel_proxy_config(self, session_id: str) -> Dict:
        """创建隧道代理配置"""
        return {
            "proxy_type": "http",
            "proxy_host": self.tunnel_host,
            "proxy_port": self.tunnel_port,
            "proxy_user": f"{self.auth_key}-session-{session_id}",
            "proxy_password": self.auth_pwd,
            "session_id": session_id,
            "full_address": f"{self.tunnel_host}:{self.tunnel_port}"
        }
    
    def allocate_tunnel_proxy_for_browser(self, browser_name: str) -> Dict:
        """为浏览器分配隧道代理"""
        try:
            # 生成唯一会话ID
            session_id = self.generate_session_id()
            
            # 创建隧道代理配置
            proxy_config = self.create_tunnel_proxy_config(session_id)
            proxy_config.update({
                "browser_name": browser_name,
                "allocated_at": time.time(),
                "type": "tunnel"
            })
            
            self.allocated_proxies.append(proxy_config)
            
            logger.info(f"为浏览器 {browser_name} 分配隧道代理: {session_id}")
            return proxy_config
            
        except Exception as e:
            logger.error(f"分配隧道代理失败: {e}")
            return {}
    
    def generate_adspower_proxy_config(self, proxy: Dict) -> Dict:
        """生成AdsPower代理配置"""
        if not proxy or proxy.get("type") != "tunnel":
            return {
                "proxy_soft": "no_proxy",
                "proxy_type": "noproxy"
            }
        
        return {
            "proxy_soft": "other",
            "proxy_type": "http",
            "proxy_host": proxy["proxy_host"],
            "proxy_port": proxy["proxy_port"],
            "proxy_user": proxy["proxy_user"],
            "proxy_password": proxy["proxy_password"]
        }
    
    def test_tunnel_proxy(self, proxy: Dict) -> bool:
        """测试隧道代理是否可用"""
        try:
            if not proxy or proxy.get("type") != "tunnel":
                return False
            
            proxy_url = f"http://{proxy['proxy_user']}:{proxy['proxy_password']}@{proxy['proxy_host']}:{proxy['proxy_port']}"
            
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            
            # 测试请求
            response = requests.get(
                "http://httpbin.org/ip", 
                proxies=proxies, 
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                current_ip = result.get('origin', 'unknown')
                logger.info(f"隧道代理测试成功: {proxy['session_id']} -> IP: {current_ip}")
                proxy["current_ip"] = current_ip
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"隧道代理测试失败 {proxy.get('session_id', 'unknown')}: {e}")
            return False
    
    def release_proxy(self, browser_name: str) -> bool:
        """释放浏览器的代理"""
        try:
            for i, proxy in enumerate(self.allocated_proxies):
                if proxy.get("browser_name") == browser_name:
                    released_proxy = self.allocated_proxies.pop(i)
                    logger.info(f"释放浏览器 {browser_name} 的隧道代理: {released_proxy['session_id']}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"释放代理失败: {e}")
            return False
    
    def get_proxy_status(self) -> Dict:
        """获取代理状态"""
        return {
            "tunnel_server": f"{self.tunnel_host}:{self.tunnel_port}",
            "allocated_count": len(self.allocated_proxies),
            "allocated_proxies": [
                {
                    "browser": p["browser_name"],
                    "session_id": p["session_id"],
                    "current_ip": p.get("current_ip", "未检测"),
                    "allocated_time": time.strftime("%H:%M:%S", time.localtime(p["allocated_at"]))
                }
                for p in self.allocated_proxies
            ]
        }
    
    def cleanup_all_proxies(self):
        """清理所有代理"""
        logger.info("清理所有隧道代理资源...")
        self.allocated_proxies.clear()

# 测试函数
async def test_qinguo_tunnel_proxy():
    """测试青果隧道代理功能"""
    print("🧪 测试青果隧道代理功能...")
    
    manager = QinguoTunnelProxyManager()
    
    try:
        # 1. 为测试浏览器分配隧道代理
        proxy1 = manager.allocate_tunnel_proxy_for_browser("测试浏览器1")
        proxy2 = manager.allocate_tunnel_proxy_for_browser("测试浏览器2")
        
        print(f"✅ 分配隧道代理:")
        print(f"   浏览器1: {proxy1['session_id']}")
        print(f"   浏览器2: {proxy2['session_id']}")
        
        # 2. 测试代理连接
        print(f"\n🔍 测试隧道代理连接...")
        
        if manager.test_tunnel_proxy(proxy1):
            print(f"✅ 浏览器1代理测试成功: IP = {proxy1.get('current_ip')}")
        else:
            print(f"❌ 浏览器1代理测试失败")
        
        if manager.test_tunnel_proxy(proxy2):
            print(f"✅ 浏览器2代理测试成功: IP = {proxy2.get('current_ip')}")
        else:
            print(f"❌ 浏览器2代理测试失败")
        
        # 3. 生成AdsPower配置
        adspower_config1 = manager.generate_adspower_proxy_config(proxy1)
        adspower_config2 = manager.generate_adspower_proxy_config(proxy2)
        
        print(f"\n📋 AdsPower配置:")
        print(f"   浏览器1: {adspower_config1}")
        print(f"   浏览器2: {adspower_config2}")
        
        # 4. 显示状态
        status = manager.get_proxy_status()
        print(f"\n📊 隧道代理状态:")
        print(f"   隧道服务器: {status['tunnel_server']}")
        print(f"   已分配数量: {status['allocated_count']}")
        for proxy_info in status['allocated_proxies']:
            print(f"   - {proxy_info['browser']}: {proxy_info['session_id']} (IP: {proxy_info['current_ip']})")
        
        # 5. 清理资源
        manager.cleanup_all_proxies()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_qinguo_tunnel_proxy()) 