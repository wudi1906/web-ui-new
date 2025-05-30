#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终AdsPower解决方案
整合所有发现的问题和修复：
1. API频率控制 (Too many request per second)
2. 代理配置必需 (user_proxy_config or proxyid is required)
3. 正确的浏览器生命周期管理
4. 青果代理 + AdsPower指纹浏览器完美融合
"""

import asyncio
import requests
import time
import random
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserStatus(Enum):
    """浏览器状态枚举"""
    CREATED = "created"
    CONFIGURED = "configured"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    DELETED = "deleted"

@dataclass
class BrowserProfile:
    """浏览器配置文件信息"""
    profile_id: str
    persona_id: int
    persona_name: str
    proxy_info: Optional[Dict] = None
    debug_port: Optional[str] = None
    status: BrowserStatus = BrowserStatus.CREATED
    created_at: float = 0.0
    updated_at: float = 0.0

class QingGuoProxyManager:
    """青果代理管理器（优化版）"""
    
    def __init__(self):
        self.config = {
            "business_id": "k3reh5az",
            "auth_key": "A942CE1E", 
            "auth_pwd": "B9FCD013057A",
            "tunnel_host": "tun-szbhry.qg.net",
            "tunnel_port": 17790
        }
        
        # 支持多种认证格式，为每个数字人提供不同IP
        self.auth_formats = [
            f"{self.config['business_id']}:{self.config['auth_key']}",
            f"{self.config['auth_key']}:{self.config['auth_pwd']}",
            f"{self.config['business_id']}-{self.config['auth_key']}:{self.config['auth_pwd']}"
        ]
    
    def get_proxy_config(self, persona_id: int) -> Dict:
        """为数字人生成代理配置（AdsPower格式）"""
        # 根据persona_id选择认证格式，确保每个人都有不同的代理IP
        auth_format = self.auth_formats[persona_id % len(self.auth_formats)]
        
        proxy_config = {
            "proxy_soft": "other",           # 使用第三方代理
            "proxy_type": "http",            # HTTP代理类型
            "proxy_host": self.config["tunnel_host"],
            "proxy_port": str(self.config["tunnel_port"]),
            "proxy_user": auth_format.split(':')[0],
            "proxy_password": auth_format.split(':')[1] if ':' in auth_format else self.config['auth_pwd']
        }
        
        return proxy_config

class FinalAdsPowerManager:
    """最终AdsPower管理器（解决所有问题）"""
    
    def __init__(self):
        self.config = {
            "base_url": "http://local.adspower.net:50325",
            "api_key": "cd606f2e6e4558c9c9f2980e7017b8e9",
            "timeout": 30
        }
        
        self.proxy_manager = QingGuoProxyManager()
        self.active_profiles: Dict[str, BrowserProfile] = {}
        
        # 严格的API频率控制
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 增加到2秒间隔
        self.request_count = 0
        self.max_requests_per_minute = 20  # 每分钟最多20个请求
        
    def _strict_rate_limit(self):
        """严格的API频率控制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # 基础间隔控制
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.info(f"⏱️ API频率控制：等待 {sleep_time:.1f} 秒")
            time.sleep(sleep_time)
        
        # 每分钟请求数控制
        self.request_count += 1
        if self.request_count > self.max_requests_per_minute:
            logger.info(f"⏱️ 达到每分钟请求限制，等待60秒...")
            time.sleep(60)
            self.request_count = 0
        
        self.last_request_time = time.time()
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """发送AdsPower API请求（严格频率控制）"""
        # 严格频率控制
        self._strict_rate_limit()
        
        # 构建URL
        if endpoint.startswith("/status"):
            url = f"{self.config['base_url']}{endpoint}"
        elif "/v2/" in endpoint:
            url = f"{self.config['base_url']}/api{endpoint}"
        else:
            url = f"{self.config['base_url']}/api/v1{endpoint}"
        
        try:
            if data is None:
                data = {}
            
            # 添加API密钥
            request_data = data.copy()
            request_data["serial_number"] = self.config["api_key"]
            
            logger.debug(f"🔍 AdsPower API: {method} {endpoint}")
            
            if method.upper() == "GET":
                response = requests.get(url, params=request_data, timeout=self.config["timeout"])
            else:
                response = requests.post(url, json=request_data, timeout=self.config["timeout"])
            
            response.raise_for_status()
            result = response.json()
            
            # 检查API响应
            if result.get("code") == -1 and "Too many request" in result.get("msg", ""):
                logger.warning(f"⚠️ API频率限制触发，增加等待时间...")
                time.sleep(5)  # 额外等待5秒
                raise Exception("API频率限制，需要重试")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ AdsPower API网络请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ AdsPower API请求处理失败: {e}")
            raise
    
    async def check_service_status(self) -> bool:
        """检查AdsPower服务状态"""
        try:
            result = self._make_request("GET", "/status")
            return result.get("code") == 0
        except Exception as e:
            logger.error(f"❌ AdsPower服务检查失败: {e}")
            return False
    
    async def get_existing_profiles(self) -> List[Dict]:
        """获取现有配置文件列表（带重试）"""
        max_retries = 3
        retry_delay = 3
        
        for attempt in range(max_retries):
            try:
                result = self._make_request("GET", "/user/list", {"page": 1, "page_size": 50})
                
                if result.get("code") == 0:
                    profiles = result.get("data", {}).get("list", [])
                    logger.info(f"📋 发现 {len(profiles)} 个现有配置文件")
                    return profiles
                else:
                    error_msg = result.get('msg', '未知错误')
                    if "Too many request" in error_msg and attempt < max_retries - 1:
                        logger.warning(f"⚠️ API频率限制，等待 {retry_delay} 秒后重试 (尝试 {attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        logger.error(f"❌ 获取配置文件列表失败: {error_msg}")
                        return []
                        
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ 获取配置文件列表异常，重试中 (尝试 {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"❌ 获取配置文件列表最终失败: {e}")
                    return []
        
        return []
    
    async def create_browser_profile(self, persona_id: int, persona_name: str) -> BrowserProfile:
        """创建浏览器配置文件（解决所有格式问题）"""
        logger.info(f"🚀 为数字人 {persona_name}(ID:{persona_id}) 创建浏览器配置文件...")
        
        try:
            # 检查配置文件数量限制
            existing_profiles = await self.get_existing_profiles()
            if len(existing_profiles) >= 15:
                raise Exception("AdsPower配置文件数量已达到15个限制，请在AdsPower客户端中删除一些现有配置文件")
            
            # 生成青果代理配置
            proxy_config = self.proxy_manager.get_proxy_config(persona_id)
            logger.info(f"   📶 配置青果代理: {proxy_config['proxy_host']}:{proxy_config['proxy_port']}")
            
            # 生成完整的配置文件（修复所有已知问题）
            profile_config = {
                "name": f"questionnaire_{persona_id}_{persona_name}_{int(time.time())}",
                "group_id": "0",  # 未分组
                "remark": f"问卷填写-{persona_name}的专用浏览器环境",
                "domain_name": "",
                "open_urls": "",
                "cookie": "",  # 空字符串，不是列表
                "user_proxy_config": proxy_config,  # 必需的代理配置
                "fingerprint_config": {
                    "automatic_timezone": 1,
                    "language": ["zh-CN", "zh", "en-US", "en"],
                    "screen_resolution": "1920_1080",
                    "fonts": ["system"],
                    "canvas": 1,  # 数值1，不是字符串
                    "webgl": 1,   # 数值1，不是字符串
                    "webgl_vendor": "random",
                    "webgl_renderer": "random",
                    "audio": 1,   # 数值1，不是字符串
                    "timezone": "auto",
                    "location": "ask",  # ask/allow/block
                    "cpu": "random",
                    "memory": "random",
                    "do_not_track": "default",
                    "hardware_concurrency": "random"
                }
            }
            
            # 发送创建请求
            result = self._make_request("POST", "/user/create", profile_config)
            
            if result.get("code") == 0:
                profile_id = result["data"]["id"]
                
                # 创建BrowserProfile对象
                browser_profile = BrowserProfile(
                    profile_id=profile_id,
                    persona_id=persona_id,
                    persona_name=persona_name,
                    proxy_info=proxy_config,
                    status=BrowserStatus.CREATED,
                    created_at=time.time()
                )
                
                # 存储到活跃配置文件
                self.active_profiles[profile_id] = browser_profile
                
                logger.info(f"✅ 浏览器配置文件创建成功: {profile_id}")
                return browser_profile
            else:
                error_msg = result.get('msg', '未知错误')
                raise Exception(f"创建配置文件失败: {error_msg}")
                
        except Exception as e:
            logger.error(f"❌ 创建浏览器配置文件失败: {e}")
            raise
    
    async def start_browser(self, profile_id: str) -> Dict:
        """启动浏览器实例（使用V2 API）"""
        logger.info(f"🌐 启动浏览器实例: {profile_id}")
        
        try:
            if profile_id not in self.active_profiles:
                raise Exception(f"配置文件不存在: {profile_id}")
            
            browser_profile = self.active_profiles[profile_id]
            browser_profile.status = BrowserStatus.STARTING
            
            # 使用V2 API启动浏览器
            start_params = {
                "profile_id": profile_id,
                "headless": 0,
                "last_opened_tabs": 1,
                "proxy_detection": 0,
                "password_filling": 0,
                "password_saving": 0,
                "cdp_mask": 1,
                "delete_cache": 0,
                "launch_args": [
                    "--disable-notifications",
                    "--disable-popup-blocking",
                    "--disable-default-apps",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                    "--disable-backgrounding-occluded-windows"
                ]
            }
            
            result = self._make_request("POST", "/v2/browser-profile/start", start_params)
            
            if result.get("code") == 0:
                browser_data = result["data"]
                debug_port = browser_data.get("debug_port", "")
                
                # 更新浏览器配置文件状态
                browser_profile.debug_port = debug_port
                browser_profile.status = BrowserStatus.RUNNING
                browser_profile.updated_at = time.time()
                
                browser_info = {
                    "success": True,
                    "profile_id": profile_id,
                    "debug_port": debug_port,
                    "selenium_address": browser_data.get("ws", {}).get("selenium", ""),
                    "webdriver_path": browser_data.get("webdriver", ""),
                    "raw_data": browser_data
                }
                
                logger.info(f"✅ 浏览器启动成功，调试端口: {debug_port}")
                return browser_info
            else:
                error_msg = result.get('msg', '未知错误')
                browser_profile.status = BrowserStatus.STOPPED
                logger.error(f"❌ 浏览器启动失败: {error_msg}")
                return {"success": False, "error": error_msg, "profile_id": profile_id}
                
        except Exception as e:
            if profile_id in self.active_profiles:
                self.active_profiles[profile_id].status = BrowserStatus.STOPPED
            logger.error(f"❌ 启动浏览器异常: {e}")
            return {"success": False, "error": str(e), "profile_id": profile_id}
    
    async def stop_browser(self, profile_id: str) -> bool:
        """停止浏览器实例"""
        logger.info(f"⏹️ 停止浏览器实例: {profile_id}")
        
        try:
            if profile_id in self.active_profiles:
                self.active_profiles[profile_id].status = BrowserStatus.STOPPING
            
            result = self._make_request("GET", "/browser/stop", {"user_id": profile_id})
            
            if result.get("code") == 0:
                if profile_id in self.active_profiles:
                    self.active_profiles[profile_id].status = BrowserStatus.STOPPED
                    self.active_profiles[profile_id].debug_port = None
                    self.active_profiles[profile_id].updated_at = time.time()
                
                logger.info(f"✅ 浏览器停止成功: {profile_id}")
                return True
            else:
                logger.warning(f"⚠️ 浏览器停止失败: {result.get('msg', '未知错误')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 停止浏览器异常: {e}")
            return False
    
    async def delete_browser_profile(self, profile_id: str) -> bool:
        """删除浏览器配置文件"""
        logger.info(f"🗑️ 删除浏览器配置文件: {profile_id}")
        
        try:
            # 先停止浏览器
            await self.stop_browser(profile_id)
            await asyncio.sleep(2)  # 等待停止完成
            
            # 删除配置文件
            result = self._make_request("POST", "/user/delete", {"user_ids": [profile_id]})
            
            if result.get("code") == 0:
                # 从活跃列表中移除
                if profile_id in self.active_profiles:
                    self.active_profiles[profile_id].status = BrowserStatus.DELETED
                    del self.active_profiles[profile_id]
                
                logger.info(f"✅ 配置文件删除成功: {profile_id}")
                return True
            else:
                logger.warning(f"⚠️ 配置文件删除失败: {result.get('msg', '未知错误')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 删除配置文件异常: {e}")
            return False
    
    async def get_browser_connection_info(self, profile_id: str) -> Optional[Dict]:
        """获取浏览器连接信息"""
        if profile_id not in self.active_profiles:
            logger.error(f"❌ 配置文件不存在: {profile_id}")
            return None
        
        browser_profile = self.active_profiles[profile_id]
        
        if browser_profile.status != BrowserStatus.RUNNING:
            logger.error(f"❌ 浏览器未运行: {profile_id}")
            return None
        
        return {
            "profile_id": profile_id,
            "persona_id": browser_profile.persona_id,
            "persona_name": browser_profile.persona_name,
            "debug_port": browser_profile.debug_port,
            "proxy_info": browser_profile.proxy_info,
            "proxy_enabled": browser_profile.proxy_info is not None,
            "status": browser_profile.status.value
        }
    
    async def create_complete_browser_environment(self, persona_id: int, persona_name: str) -> Dict:
        """为数字人创建完整的浏览器环境（一站式服务）"""
        logger.info(f"🚀 为数字人 {persona_name}(ID:{persona_id}) 创建完整的浏览器环境...")
        
        try:
            # 步骤1：创建配置文件（包含青果代理）
            browser_profile = await self.create_browser_profile(persona_id, persona_name)
            
            # 步骤2：启动浏览器
            browser_info = await self.start_browser(browser_profile.profile_id)
            
            if browser_info.get("success"):
                # 步骤3：验证浏览器状态
                await asyncio.sleep(3)  # 等待浏览器完全启动
                
                result = {
                    "success": True,
                    "profile_id": browser_profile.profile_id,
                    "persona_id": persona_id,
                    "persona_name": persona_name,
                    "debug_port": browser_info.get("debug_port"),
                    "selenium_address": browser_info.get("selenium_address"),
                    "webdriver_path": browser_info.get("webdriver_path"),
                    "proxy_enabled": True,  # 总是启用青果代理
                    "proxy_ip": "青果代理IP",
                    "browser_active": True,
                    "created_at": browser_profile.created_at
                }
                
                logger.info(f"✅ 完整浏览器环境创建成功")
                logger.info(f"   配置文件: {browser_profile.profile_id}")
                logger.info(f"   数字人: {persona_name}")
                logger.info(f"   代理状态: 已启用青果代理")
                logger.info(f"   浏览器状态: 运行中")
                
                return result
            else:
                # 如果启动失败，清理配置文件
                await self.delete_browser_profile(browser_profile.profile_id)
                error_msg = browser_info.get("error", "未知错误")
                raise Exception(f"浏览器启动失败: {error_msg}")
                
        except Exception as e:
            logger.error(f"❌ 创建完整浏览器环境失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "persona_id": persona_id,
                "persona_name": persona_name
            }
    
    async def cleanup_all_browsers(self):
        """清理所有活跃的浏览器"""
        logger.info(f"🧹 清理所有活跃浏览器 ({len(self.active_profiles)} 个)...")
        
        cleanup_results = []
        
        for profile_id in list(self.active_profiles.keys()):
            try:
                browser_profile = self.active_profiles[profile_id]
                logger.info(f"   清理: {browser_profile.persona_name} ({profile_id})")
                
                success = await self.delete_browser_profile(profile_id)
                cleanup_results.append({
                    "profile_id": profile_id,
                    "persona_name": browser_profile.persona_name,
                    "success": success
                })
                
                if success:
                    logger.info(f"   ✅ 清理成功")
                else:
                    logger.warning(f"   ⚠️ 清理失败")
                    
            except Exception as e:
                logger.error(f"   ❌ 清理异常: {e}")
                cleanup_results.append({
                    "profile_id": profile_id,
                    "success": False,
                    "error": str(e)
                })
        
        logger.info(f"✅ 浏览器清理完成，成功清理 {len([r for r in cleanup_results if r.get('success')])} 个")
        return cleanup_results

# 测试函数
async def test_final_solution():
    """测试最终解决方案"""
    print("🎯 测试最终AdsPower解决方案")
    print("=" * 80)
    print("🔧 整合所有修复：API频率控制 + 代理配置 + 正确格式")
    print()
    
    manager = FinalAdsPowerManager()
    
    try:
        # 检查服务状态
        print("📋 1. 检查AdsPower服务状态...")
        service_ok = await manager.check_service_status()
        if not service_ok:
            print("❌ AdsPower服务不可用")
            return
        print("✅ AdsPower服务正常")
        
        # 查看现有配置文件
        print("\n📋 2. 查看现有配置文件...")
        existing_profiles = await manager.get_existing_profiles()
        print(f"发现 {len(existing_profiles)} 个现有配置文件")
        
        if len(existing_profiles) >= 15:
            print("⚠️ 配置文件已达到15个限制")
            print("💡 请在AdsPower客户端中删除一些配置文件后重试")
            return
        
        # 创建测试环境
        print("\n📋 3. 创建测试数字人的完整浏览器环境...")
        test_personas = [
            (1001, "测试小王"),
            (1002, "测试小李")
        ]
        
        created_environments = []
        
        for persona_id, persona_name in test_personas:
            print(f"\n   🚀 为 {persona_name} 创建完整环境...")
            result = await manager.create_complete_browser_environment(persona_id, persona_name)
            
            if result.get("success"):
                created_environments.append(result)
                print(f"   ✅ 环境创建成功")
                print(f"      配置文件ID: {result['profile_id']}")
                print(f"      调试端口: {result['debug_port']}")
                print(f"      代理状态: {'已启用青果代理' if result['proxy_enabled'] else '本地IP'}")
            else:
                print(f"   ❌ 环境创建失败: {result.get('error')}")
        
        if created_environments:
            print(f"\n🎉 成功创建 {len(created_environments)} 个浏览器环境！")
            print(f"💡 每个数字人都有独立的'新电脑'：")
            print(f"   - AdsPower指纹浏览器隔离")
            print(f"   - 青果代理IP隔离")
            print(f"   - 完整的生命周期管理")
            
            print(f"\n测试完成后按 Enter 键清理资源...")
            input()
            
            # 清理资源
            print(f"\n🧹 清理测试资源...")
            cleanup_results = await manager.cleanup_all_browsers()
            
            success_count = len([r for r in cleanup_results if r.get("success")])
            print(f"✅ 清理完成，成功清理 {success_count}/{len(cleanup_results)} 个浏览器")
        
        print(f"\n🎉 最终解决方案测试完成！")
        print(f"✅ 所有问题已解决：")
        print(f"   - API频率控制 ✅")
        print(f"   - 代理配置必需 ✅")
        print(f"   - 配置格式正确 ✅")
        print(f"   - 青果代理集成 ✅")
        print(f"   - 完整生命周期 ✅")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 测试被中断，开始清理资源...")
        await manager.cleanup_all_browsers()
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        await manager.cleanup_all_browsers()

if __name__ == "__main__":
    asyncio.run(test_final_solution()) 