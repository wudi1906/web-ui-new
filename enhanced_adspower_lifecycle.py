#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版AdsPower浏览器生命周期管理系统
基于官方文档实现完整的浏览器配置文件生命周期管理
整合青果代理，为每个数字人提供独立的"新电脑"环境

浏览器生命周期：
1. 创建阶段：create_profile() → 创建浏览器配置文件
2. 配置阶段：configure_proxy() → 配置青果代理
3. 启动阶段：start_browser() → 启动浏览器实例  
4. 使用阶段：get_browser_connection() → 获取连接信息
5. 停止阶段：stop_browser() → 停止浏览器实例
6. 清理阶段：delete_profile() → 删除配置文件

核心API端点（基于官方文档）：
- POST /api/v1/user/create - 创建浏览器配置文件
- POST /api/v1/user/update - 更新配置文件（添加代理）
- GET /api/v1/user/list - 查询配置文件列表
- POST /api/v2/browser-profile/start - 启动浏览器V2
- GET /api/v1/browser/stop - 停止浏览器
- POST /api/v1/user/delete - 删除配置文件
- GET /api/v1/browser/active - 检查启动状态
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
    CREATED = "created"           # 已创建配置文件
    CONFIGURED = "configured"     # 已配置代理
    STARTING = "starting"         # 启动中
    RUNNING = "running"          # 运行中
    STOPPING = "stopping"        # 停止中
    STOPPED = "stopped"          # 已停止
    DELETED = "deleted"          # 已删除

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
    """青果代理管理器"""
    
    def __init__(self):
        self.config = {
            "business_id": "k3reh5az",
            "auth_key": "A942CE1E", 
            "auth_pwd": "B9FCD013057A",
            "tunnel_host": "tun-szbhry.qg.net",
            "tunnel_port": 17790
        }
        
        # 支持多种认证格式，AdsPower可能需要不同格式
        self.auth_formats = [
            f"{self.config['business_id']}:{self.config['auth_key']}",
            f"{self.config['auth_key']}:{self.config['auth_pwd']}",
            f"{self.config['business_id']}-{self.config['auth_key']}:{self.config['auth_pwd']}"
        ]
    
    def get_proxy_config(self, persona_id: int) -> Dict:
        """为数字人生成代理配置"""
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
    
    def test_proxy_connection(self, proxy_config: Dict) -> Tuple[bool, Optional[str]]:
        """测试代理连接并返回IP"""
        try:
            proxy_url = f"http://{proxy_config['proxy_user']}:{proxy_config['proxy_password']}@{proxy_config['proxy_host']}:{proxy_config['proxy_port']}"
            
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            
            response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
            response.raise_for_status()
            
            ip_info = response.json()
            proxy_ip = ip_info.get("origin", "未知")
            
            logger.info(f"✅ 代理连接测试成功，IP: {proxy_ip}")
            return True, proxy_ip
            
        except Exception as e:
            logger.warning(f"⚠️ 代理连接测试失败: {e}")
            return False, None

class AdsPowerLifecycleManager:
    """AdsPower浏览器生命周期管理器"""
    
    def __init__(self):
        self.config = {
            "base_url": "http://local.adspower.net:50325",
            "api_key": "cd606f2e6e4558c9c9f2980e7017b8e9",
            "timeout": 30
        }
        
        self.proxy_manager = QingGuoProxyManager()
        self.active_profiles: Dict[str, BrowserProfile] = {}
        self.profile_pool: List[str] = []  # 可复用的配置文件池
        self.max_profiles = 10  # 最大配置文件数量（小于15的限制）
        self.last_request_time = 0  # 添加请求频率控制
        self.min_request_interval = 1.0  # 最小请求间隔（秒）
        
    def _rate_limit_request(self):
        """API请求频率控制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"API频率控制：等待 {sleep_time:.1f} 秒")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """发送AdsPower API请求（带频率控制）"""
        # 频率控制
        self._rate_limit_request()
        
        # 根据端点确定是否需要api版本前缀
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
            
            if method.upper() == "GET":
                response = requests.get(url, params=request_data, timeout=self.config["timeout"])
            else:
                response = requests.post(url, json=request_data, timeout=self.config["timeout"])
            
            response.raise_for_status()
            result = response.json()
            
            logger.debug(f"AdsPower API: {method} {endpoint} → {result.get('code', 'unknown')}")
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
        """获取现有配置文件列表（带重试机制）"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                result = self._make_request("GET", "/user/list", {"page": 1, "page_size": 50})
                
                if result.get("code") == 0:
                    profiles = result.get("data", {}).get("list", [])
                    logger.info(f"📋 发现 {len(profiles)} 个现有配置文件")
                    return profiles
                else:
                    error_msg = result.get('msg', '未知错误')
                    if "Too many request per second" in error_msg and attempt < max_retries - 1:
                        logger.warning(f"⚠️ API频率限制，等待 {retry_delay} 秒后重试 (尝试 {attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
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
    
    async def create_browser_profile(self, persona_id: int, persona_name: str, 
                                   use_proxy: bool = True) -> BrowserProfile:
        """创建浏览器配置文件"""
        logger.info(f"🚀 为数字人 {persona_name}(ID:{persona_id}) 创建浏览器配置文件...")
        
        try:
            # 检查是否已达到配置文件数量限制
            existing_profiles = await self.get_existing_profiles()
            if len(existing_profiles) >= 15:
                raise Exception("AdsPower配置文件数量已达到15个限制，请删除一些现有配置文件")
            
            # 生成配置文件基本信息（专注于核心桌面浏览器配置）
            profile_config = {
                "name": f"questionnaire_{persona_id}_{persona_name}_{int(time.time())}",
                "group_id": "0",  # 未分组
                "remark": f"问卷填写-{persona_name}的专用桌面浏览器环境",
                "domain_name": "",
                "open_urls": "",
                "cookie": "",  # 使用空字符串而不是空列表
                "fingerprint_config": {
                    # 🔑 核心桌面浏览器配置（只使用AdsPower支持的参数）
                    "automatic_timezone": 1,  # 自动时区
                    "language": ["zh-CN", "zh", "en-US", "en"],  # 支持中英文
                    "screen_resolution": "1920_1080",  # 强制桌面高分辨率
                    "fonts": ["system"],  # 系统字体
                    "canvas": 1,  # 启用Canvas噪音
                    "webgl": 1,   # 启用WebGL噪音
                    "webgl_vendor": "random",  # 随机WebGL厂商
                    "webgl_renderer": "random",  # 随机WebGL渲染器
                    "audio": 1,   # 启用音频指纹噪音
                    "timezone": "auto", # 自动时区
                    "location": "ask",  # 位置权限：询问
                    "cpu": "random",    # 随机CPU核心数
                    "memory": "random", # 随机内存
                    "do_not_track": "default",  # 不跟踪设置
                    "hardware_concurrency": "random",  # 随机硬件并发
                    "accept_language": "zh-CN,zh;q=0.9,en;q=0.8",
                    
                    # 🔑 关键：强制桌面User-Agent，防止移动端显示
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                }
            }
            
            # 如果使用代理，先配置代理信息
            if use_proxy:
                proxy_config = self.proxy_manager.get_proxy_config(persona_id)
                profile_config["user_proxy_config"] = proxy_config
                logger.info(f"   📶 配置青果代理: {proxy_config['proxy_host']}:{proxy_config['proxy_port']}")
            else:
                profile_config["user_proxy_config"] = {
                    "proxy_soft": "no_proxy",
                    "proxy_type": "noproxy"
                }
                logger.info(f"   🚫 不使用代理")
            
            # 发送创建请求
            result = self._make_request("POST", "/user/create", profile_config)
            
            if result.get("code") == 0:
                profile_id = result["data"]["id"]
                
                # 创建BrowserProfile对象
                browser_profile = BrowserProfile(
                    profile_id=profile_id,
                    persona_id=persona_id,
                    persona_name=persona_name,
                    proxy_info=proxy_config if use_proxy else None,
                    status=BrowserStatus.CREATED,
                    created_at=time.time()
                )
                
                # 如果配置了代理，测试代理连接
                if use_proxy:
                    proxy_success, proxy_ip = self.proxy_manager.test_proxy_connection(proxy_config)
                    if proxy_success:
                        browser_profile.status = BrowserStatus.CONFIGURED
                        logger.info(f"   ✅ 代理配置成功，IP: {proxy_ip}")
                    else:
                        logger.warning(f"   ⚠️ 代理测试失败，但配置文件已创建")
                
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
        """启动浏览器实例（使用V1 API）"""
        logger.info(f"🌐 启动浏览器实例: {profile_id}")
        
        try:
            # 检查配置文件是否存在
            if profile_id not in self.active_profiles:
                raise Exception(f"配置文件不存在: {profile_id}")
            
            browser_profile = self.active_profiles[profile_id]
            browser_profile.status = BrowserStatus.STARTING
            
            # 使用V1 API启动浏览器（基于官方文档，简化参数）
            start_params = {
                "user_id": profile_id,        # V1 API使用user_id
                "open_tabs": 1,               # 不打开平台和历史页面 (1:不打开, 0:打开)
                "ip_tab": 0,                  # 不打开IP检测页面 (0:不打开, 1:打开)
                "headless": 0,                # 非无头模式
            }
            
            result = self._make_request("GET", "/browser/start", start_params)
            
            if result.get("code") == 0:
                browser_data = result["data"]
                
                # 提取调试端口信息
                debug_port = browser_data.get("debug_port", "")
                ws_info = browser_data.get("ws", {})
                selenium_address = ws_info.get("selenium", "")
                puppeteer_address = ws_info.get("puppeteer", "")
                webdriver_path = browser_data.get("webdriver", "")
                
                # 更新浏览器配置文件状态
                browser_profile.debug_port = debug_port
                browser_profile.status = BrowserStatus.RUNNING
                browser_profile.updated_at = time.time()
                
                browser_info = {
                    "success": True,
                    "profile_id": profile_id,
                    "debug_port": debug_port,
                    "selenium_address": selenium_address,
                    "puppeteer_address": puppeteer_address,
                    "webdriver_path": webdriver_path,
                    "ws_info": ws_info,
                    "raw_data": browser_data
                }
                
                logger.info(f"✅ 浏览器启动成功")
                logger.info(f"   配置文件ID: {profile_id}")
                logger.info(f"   调试端口: {debug_port}")
                logger.info(f"   Selenium地址: {selenium_address}")
                logger.info(f"   WebDriver路径: {webdriver_path}")
                logger.info(f"   已禁用IP检测页面和平台页面")
                
                return browser_info
            else:
                error_msg = result.get('msg', '未知错误')
                browser_profile.status = BrowserStatus.STOPPED
                logger.error(f"❌ 浏览器启动失败: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "profile_id": profile_id
                }
                
        except Exception as e:
            if profile_id in self.active_profiles:
                self.active_profiles[profile_id].status = BrowserStatus.STOPPED
            logger.error(f"❌ 启动浏览器异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "profile_id": profile_id
            }
    
    async def check_browser_status(self, profile_id: str) -> Dict:
        """检查浏览器启动状态"""
        try:
            result = self._make_request("GET", "/browser/active", {"user_id": profile_id})
            
            if result.get("code") == 0:
                status_data = result.get("data", {})
                is_active = status_data.get("status") == "Active"
                
                return {
                    "success": True,
                    "profile_id": profile_id,
                    "is_active": is_active,
                    "status_data": status_data
                }
            else:
                return {
                    "success": False,
                    "profile_id": profile_id,
                    "error": result.get('msg', '未知错误')
                }
                
        except Exception as e:
            logger.error(f"❌ 检查浏览器状态失败: {e}")
            return {
                "success": False,
                "profile_id": profile_id,
                "error": str(e)
            }
    
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
            await asyncio.sleep(1)  # 等待停止完成
            
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
            "status": browser_profile.status.value
        }
    
    async def create_complete_browser_environment(self, persona_id: int, persona_name: str) -> Dict:
        """为数字人创建完整的浏览器环境（一站式服务）"""
        logger.info(f"🚀 为数字人 {persona_name}(ID:{persona_id}) 创建完整的浏览器环境...")
        
        try:
            # 步骤1：创建配置文件（包含代理配置）
            browser_profile = await self.create_browser_profile(persona_id, persona_name, use_proxy=True)
            
            # 步骤2：启动浏览器
            browser_info = await self.start_browser(browser_profile.profile_id)
            
            if browser_info.get("success"):
                # 步骤3：验证浏览器状态
                await asyncio.sleep(3)  # 等待浏览器完全启动
                status_info = await self.check_browser_status(browser_profile.profile_id)
                
                result = {
                    "success": True,
                    "profile_id": browser_profile.profile_id,
                    "persona_id": persona_id,
                    "persona_name": persona_name,
                    "debug_port": browser_info.get("debug_port"),
                    "selenium_address": browser_info.get("selenium_address"),
                    "webdriver_path": browser_info.get("webdriver_path"),
                    "proxy_enabled": browser_profile.proxy_info is not None,
                    "proxy_ip": "代理IP待检测" if browser_profile.proxy_info else "本地IP",
                    "browser_active": status_info.get("is_active", False),
                    "created_at": browser_profile.created_at
                }
                
                logger.info(f"✅ 完整浏览器环境创建成功")
                logger.info(f"   配置文件: {browser_profile.profile_id}")
                logger.info(f"   数字人: {persona_name}")
                logger.info(f"   代理状态: {'已启用' if browser_profile.proxy_info else '未启用'}")
                logger.info(f"   浏览器状态: {'运行中' if status_info.get('is_active') else '未运行'}")
                
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
    
    async def cleanup_browser_after_task_completion(self, profile_id: str, task_result: Dict) -> bool:
        """
        在数字人任务完成后智能清理浏览器资源
        
        清理条件：
        1. 任务成功完成且置信度高
        2. 问卷确实已经提交
        3. 没有待处理的重要操作
        
        参数:
            profile_id: 浏览器配置文件ID
            task_result: 任务执行结果，包含完成状态和置信度
        
        返回:
            bool: 是否成功清理
        """
        logger.info(f"🔍 智能评估是否清理浏览器资源: {profile_id}")
        
        try:
            if profile_id not in self.active_profiles:
                logger.warning(f"⚠️ 配置文件不存在: {profile_id}")
                return False
            
            browser_profile = self.active_profiles[profile_id]
            
            # 获取任务完成信息
            task_success = task_result.get("success", False)
            completion_confidence = task_result.get("completion_confidence", 0.0)
            completion_check = task_result.get("completion_check", {})
            
            logger.info(f"📊 任务完成分析:")
            logger.info(f"   任务成功: {task_success}")
            logger.info(f"   完成置信度: {completion_confidence:.1%}")
            logger.info(f"   智能检查结果: {completion_check.get('is_completed', False)}")
            
            # 决策逻辑：是否清理浏览器
            should_cleanup = False
            cleanup_reason = ""
            
            if task_success and completion_confidence >= 0.8:
                should_cleanup = True
                cleanup_reason = f"任务成功完成，置信度{completion_confidence:.1%}>=80%"
            elif task_success and completion_confidence >= 0.7 and completion_check.get("is_completed", False):
                should_cleanup = True  
                cleanup_reason = f"任务成功且智能检查确认完成，置信度{completion_confidence:.1%}"
            elif completion_check.get("is_completed", False) and completion_confidence >= 0.9:
                should_cleanup = True
                cleanup_reason = f"智能检查高度确认完成，置信度{completion_confidence:.1%}"
            else:
                cleanup_reason = f"不满足清理条件：成功={task_success}, 置信度={completion_confidence:.1%}"
            
            logger.info(f"🎯 清理决策: {'✅ 清理' if should_cleanup else '❌ 保留'}")
            logger.info(f"   决策依据: {cleanup_reason}")
            
            if should_cleanup:
                # 执行智能清理
                logger.info(f"🧹 开始智能清理浏览器资源...")
                
                # 给用户一个短暂的查看时间（可选）
                logger.info(f"⏳ 等待3秒供查看结果，然后清理资源...")
                await asyncio.sleep(3)
                
                # 停止浏览器
                stop_success = await self.stop_browser(profile_id)
                if stop_success:
                    logger.info(f"✅ 浏览器停止成功")
                else:
                    logger.warning(f"⚠️ 浏览器停止失败，继续清理配置文件")
                
                # 删除配置文件
                delete_success = await self.delete_browser_profile(profile_id)
                if delete_success:
                    logger.info(f"✅ 配置文件删除成功，AdsPower资源已释放")
                    return True
                else:
                    logger.error(f"❌ 配置文件删除失败")
                    return False
                    
            else:
                logger.info(f"🔄 浏览器保持运行状态，等待进一步确认")
                # 更新配置文件状态为等待确认
                browser_profile.status = BrowserStatus.RUNNING
                browser_profile.updated_at = time.time()
                return False
                
        except Exception as e:
            logger.error(f"❌ 智能清理评估失败: {e}")
            return False
    
    async def force_cleanup_browser(self, profile_id: str, reason: str = "手动强制清理") -> bool:
        """
        强制清理浏览器资源（用于异常情况或手动清理）
        
        参数:
            profile_id: 浏览器配置文件ID  
            reason: 强制清理的原因
        
        返回:
            bool: 是否成功清理
        """
        logger.info(f"💀 强制清理浏览器资源: {profile_id}")
        logger.info(f"   清理原因: {reason}")
        
        try:
            if profile_id in self.active_profiles:
                browser_profile = self.active_profiles[profile_id]
                logger.info(f"   数字人: {browser_profile.persona_name}")
                logger.info(f"   状态: {browser_profile.status.value}")
            
            # 强制停止浏览器
            try:
                await self.stop_browser(profile_id)
            except Exception as e:
                logger.warning(f"⚠️ 强制停止浏览器时出错: {e}")
            
            # 强制删除配置文件
            try:
                success = await self.delete_browser_profile(profile_id)
                if success:
                    logger.info(f"✅ 强制清理成功")
                    return True
                else:
                    logger.error(f"❌ 强制清理失败")
                    return False
            except Exception as e:
                logger.error(f"❌ 强制删除配置文件时出错: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 强制清理异常: {e}")
            return False

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
        
        success_count = len([r for r in cleanup_results if r.get("success")])
        print(f"✅ 清理完成，成功清理 {success_count}/{len(cleanup_results)} 个浏览器")
        return cleanup_results
    
    def get_active_browsers_info(self) -> List[Dict]:
        """获取所有活跃浏览器信息"""
        browsers_info = []
        
        for profile_id, browser_profile in self.active_profiles.items():
            info = {
                "profile_id": profile_id,
                "persona_id": browser_profile.persona_id,
                "persona_name": browser_profile.persona_name,
                "status": browser_profile.status.value,
                "debug_port": browser_profile.debug_port,
                "proxy_enabled": browser_profile.proxy_info is not None,
                "created_at": browser_profile.created_at,
                "updated_at": browser_profile.updated_at
            }
            browsers_info.append(info)
        
        return browsers_info

# 测试函数
async def test_complete_lifecycle():
    """测试完整的浏览器生命周期"""
    print("🧪 AdsPower浏览器生命周期完整测试")
    print("=" * 80)
    
    manager = AdsPowerLifecycleManager()
    
    try:
        # 检查服务状态
        print("📋 1. 检查AdsPower服务状态...")
        service_ok = await manager.check_service_status()
        if not service_ok:
            print("❌ AdsPower服务不可用，请检查AdsPower客户端是否运行")
            return
        print("✅ AdsPower服务正常")
        
        # 查看现有配置文件
        print("\n📋 2. 查看现有配置文件...")
        existing_profiles = await manager.get_existing_profiles()
        print(f"发现 {len(existing_profiles)} 个现有配置文件")
        
        # 创建测试数字人的完整环境
        print("\n🚀 3. 为测试数字人创建完整浏览器环境...")
        test_personas = [
            (1001, "测试小王"),
            (1002, "测试小李")
        ]
        
        browser_environments = []
        
        for persona_id, persona_name in test_personas:
            print(f"\n   创建环境: {persona_name}")
            result = await manager.create_complete_browser_environment(persona_id, persona_name)
            
            if result.get("success"):
                browser_environments.append(result)
                print(f"   ✅ 环境创建成功")
                print(f"      配置文件ID: {result['profile_id']}")
                print(f"      调试端口: {result['debug_port']}")
                print(f"      代理状态: {result['proxy_enabled']}")
            else:
                print(f"   ❌ 环境创建失败: {result.get('error')}")
        
        # 显示活跃浏览器信息
        print(f"\n📊 4. 活跃浏览器信息:")
        active_browsers = manager.get_active_browsers_info()
        for browser in active_browsers:
            print(f"   - {browser['persona_name']}: {browser['status']} (端口: {browser['debug_port']})")
        
        # 等待用户测试
        if browser_environments:
            print(f"\n⏳ 浏览器环境已准备就绪！")
            print(f"现在你可以：")
            print(f"1. 在AdsPower客户端中查看新创建的配置文件")
            print(f"2. 每个浏览器都有独立的青果代理IP")
            print(f"3. 可以通过debug端口连接浏览器进行自动化操作")
            print(f"4. 测试完成后按 Enter 键清理资源...")
            input()
        
        # 清理资源
        print(f"\n🧹 5. 清理测试资源...")
        cleanup_results = await manager.cleanup_all_browsers()
        
        success_count = len([r for r in cleanup_results if r.get("success")])
        print(f"✅ 清理完成，成功清理 {success_count}/{len(cleanup_results)} 个浏览器")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 测试被中断，开始清理资源...")
        await manager.cleanup_all_browsers()
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        await manager.cleanup_all_browsers()

if __name__ == "__main__":
    asyncio.run(test_complete_lifecycle()) 