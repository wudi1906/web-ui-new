#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
青果代理管理器
集成青果代理API，为每个浏览器分配独立的代理IP
"""

import requests
import time
import random
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class QinguoProxyManager:
    """青果代理管理器"""
    
    def __init__(self):
        # 青果代理配置
        self.business_id = "k3reh5az"  # 业务标识
        self.auth_key = "A942CE1E"     # Authkey
        self.auth_pwd = "B9FCD013057A" # Authpwd
        self.base_url = "https://proxy.qg.net"
        
        # 代理池管理
        self.allocated_proxies = []  # 已分配的代理
        self.proxy_pool = []         # 代理池
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """发送API请求"""
        try:
            url = f"{self.base_url}/{endpoint}"
            if params is None:
                params = {}
            
            # 添加认证参数
            params.update({
                "Key": self.auth_key,
                "Pwd": self.auth_pwd
            })
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # 青果代理返回的是文本格式，需要解析
            result_text = response.text.strip()
            
            if result_text.startswith("ERROR"):
                raise Exception(f"青果代理API错误: {result_text}")
            
            return {"success": True, "data": result_text}
            
        except Exception as e:
            logger.error(f"青果代理API请求失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_proxy_list(self, count: int = 10, region: str = "all") -> List[Dict]:
        """获取代理IP列表"""
        try:
            logger.info(f"获取 {count} 个代理IP...")
            
            # 使用短效代理（弹性提取）
            params = {
                "num": count,
                "format": "json",
                "sep": 1,  # 分隔符类型
                "regions": region  # 地区
            }
            
            result = self._make_request("allocate", params)
            
            if not result["success"]:
                logger.error(f"获取代理失败: {result['error']}")
                return []
            
            # 解析代理数据
            proxy_data = result["data"]
            proxies = []
            
            # 如果返回的是JSON格式
            try:
                import json
                if proxy_data.startswith('[') or proxy_data.startswith('{'):
                    proxy_list = json.loads(proxy_data)
                    for proxy in proxy_list:
                        proxies.append({
                            "ip": proxy.get("ip"),
                            "port": proxy.get("port"),
                            "username": proxy.get("username", ""),
                            "password": proxy.get("password", ""),
                            "type": "http",
                            "full_address": f"{proxy.get('ip')}:{proxy.get('port')}"
                        })
                else:
                    # 文本格式解析 (ip:port:username:password)
                    lines = proxy_data.split('\n')
                    for line in lines:
                        if line.strip():
                            parts = line.strip().split(':')
                            if len(parts) >= 2:
                                proxies.append({
                                    "ip": parts[0],
                                    "port": parts[1],
                                    "username": parts[2] if len(parts) > 2 else "",
                                    "password": parts[3] if len(parts) > 3 else "",
                                    "type": "http",
                                    "full_address": f"{parts[0]}:{parts[1]}"
                                })
            except:
                # 简单文本格式解析 (ip:port)
                lines = proxy_data.split('\n')
                for line in lines:
                    if line.strip() and ':' in line:
                        ip, port = line.strip().split(':', 1)
                        proxies.append({
                            "ip": ip,
                            "port": port,
                            "username": "",
                            "password": "",
                            "type": "http",
                            "full_address": f"{ip}:{port}"
                        })
            
            logger.info(f"成功获取 {len(proxies)} 个代理IP")
            self.proxy_pool.extend(proxies)
            return proxies
            
        except Exception as e:
            logger.error(f"获取代理列表失败: {e}")
            return []
    
    def allocate_proxy_for_browser(self, browser_name: str) -> Optional[Dict]:
        """为浏览器分配专用代理"""
        try:
            # 如果代理池不足，获取更多代理
            if len(self.proxy_pool) < 2:
                new_proxies = self.get_proxy_list(10)
                if not new_proxies:
                    logger.error("无法获取新的代理IP")
                    return None
            
            # 随机选择一个代理
            if self.proxy_pool:
                proxy = random.choice(self.proxy_pool)
                self.proxy_pool.remove(proxy)
                
                # 添加浏览器信息
                proxy["browser_name"] = browser_name
                proxy["allocated_at"] = time.time()
                
                self.allocated_proxies.append(proxy)
                
                logger.info(f"为浏览器 {browser_name} 分配代理: {proxy['full_address']}")
                return proxy
            
            return None
            
        except Exception as e:
            logger.error(f"分配代理失败: {e}")
            return None
    
    def generate_adspower_proxy_config(self, proxy: Dict) -> Dict:
        """生成AdsPower代理配置"""
        if not proxy:
            return {
                "proxy_soft": "no_proxy",
                "proxy_type": "noproxy"
            }
        
        config = {
            "proxy_soft": "other",
            "proxy_type": "http",
            "proxy_host": proxy["ip"],
            "proxy_port": proxy["port"]
        }
        
        # 如果有用户名密码
        if proxy.get("username") and proxy.get("password"):
            config.update({
                "proxy_user": proxy["username"],
                "proxy_password": proxy["password"]
            })
        
        return config
    
    def test_proxy(self, proxy: Dict) -> bool:
        """测试代理是否可用"""
        try:
            proxy_url = f"http://{proxy['ip']}:{proxy['port']}"
            
            if proxy.get("username") and proxy.get("password"):
                proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
            
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            
            # 测试请求
            response = requests.get(
                "http://httpbin.org/ip", 
                proxies=proxies, 
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"代理测试成功: {proxy['full_address']} -> IP: {result.get('origin')}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"代理测试失败 {proxy['full_address']}: {e}")
            return False
    
    def release_proxy(self, browser_name: str) -> bool:
        """释放浏览器的代理"""
        try:
            for i, proxy in enumerate(self.allocated_proxies):
                if proxy.get("browser_name") == browser_name:
                    released_proxy = self.allocated_proxies.pop(i)
                    logger.info(f"释放浏览器 {browser_name} 的代理: {released_proxy['full_address']}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"释放代理失败: {e}")
            return False
    
    def get_proxy_status(self) -> Dict:
        """获取代理状态"""
        return {
            "pool_size": len(self.proxy_pool),
            "allocated_count": len(self.allocated_proxies),
            "allocated_proxies": [
                {
                    "browser": p["browser_name"],
                    "proxy": p["full_address"],
                    "allocated_time": time.strftime("%H:%M:%S", time.localtime(p["allocated_at"]))
                }
                for p in self.allocated_proxies
            ]
        }
    
    def cleanup_all_proxies(self):
        """清理所有代理"""
        logger.info("清理所有代理资源...")
        self.allocated_proxies.clear()
        self.proxy_pool.clear()

# 测试函数
async def test_qinguo_proxy():
    """测试青果代理功能"""
    print("🧪 测试青果代理功能...")
    
    manager = QinguoProxyManager()
    
    try:
        # 1. 获取代理列表
        proxies = manager.get_proxy_list(5)
        print(f"✅ 获取到 {len(proxies)} 个代理IP")
        
        if proxies:
            # 2. 测试第一个代理
            test_proxy = proxies[0]
            print(f"🔍 测试代理: {test_proxy['full_address']}")
            
            if manager.test_proxy(test_proxy):
                print("✅ 代理测试成功")
            else:
                print("❌ 代理测试失败")
            
            # 3. 生成AdsPower配置
            adspower_config = manager.generate_adspower_proxy_config(test_proxy)
            print(f"📋 AdsPower配置: {adspower_config}")
        
        # 4. 显示状态
        status = manager.get_proxy_status()
        print(f"📊 代理状态: {status}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_qinguo_proxy()) 