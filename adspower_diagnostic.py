#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AdsPower深度诊断工具
用于诊断15个配置文件限制的隐藏问题
"""

import requests
import time
import json
from typing import Dict, List, Optional

class AdsPowerDeepDiagnostic:
    """AdsPower深度诊断器"""
    
    def __init__(self):
        self.config = {
            "base_url": "http://local.adspower.net:50325",
            "api_key": "cd606f2e6e4558c9c9f2980e7017b8e9",
            "timeout": 30
        }
        self.last_request_time = 0
        self.min_request_interval = 1.5
    
    def _rate_limit_request(self):
        """API请求频率控制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, silent: bool = False) -> Dict:
        """发送AdsPower API请求"""
        self._rate_limit_request()
        
        if endpoint.startswith("/status"):
            url = f"{self.config['base_url']}{endpoint}"
        elif "/v2/" in endpoint:
            url = f"{self.config['base_url']}/api{endpoint}"
        else:
            url = f"{self.config['base_url']}/api/v1{endpoint}"
        
        try:
            if data is None:
                data = {}
            
            request_data = data.copy()
            request_data["serial_number"] = self.config["api_key"]
            
            if not silent:
                print(f"🔍 测试API: {method} {endpoint}")
            
            if method.upper() == "GET":
                response = requests.get(url, params=request_data, timeout=self.config["timeout"])
            else:
                response = requests.post(url, json=request_data, timeout=self.config["timeout"])
            
            response.raise_for_status()
            result = response.json()
            
            if not silent:
                print(f"   结果: code={result.get('code', 'N/A')}, msg='{result.get('msg', 'N/A')}'")
            
            return result
            
        except Exception as e:
            if not silent:
                print(f"   ❌ 异常: {e}")
            return {"code": -1, "msg": str(e), "error": True}
    
    def comprehensive_profile_scan(self):
        """全面扫描配置文件"""
        print("🔍 AdsPower配置文件深度扫描")
        print("=" * 60)
        
        # 1. 基本配置文件列表检查
        print("\n📋 1. 基本配置文件列表检查")
        print("-" * 40)
        
        for page in range(1, 6):  # 检查前5页
            result = self._make_request("GET", "/user/list", {"page": page, "page_size": 100})
            
            if result.get("code") == 0:
                data = result.get("data", {})
                profiles = data.get("list", [])
                total = data.get("total", 0)
                
                print(f"   第{page}页: 发现 {len(profiles)} 个配置文件 (总计: {total})")
                
                if profiles:
                    for i, profile in enumerate(profiles[:3]):  # 显示前3个
                        profile_id = profile.get("user_id", "N/A")
                        name = profile.get("name", "未知")
                        group = profile.get("group_name", "未分组")
                        print(f"      {i+1}. {name} ({profile_id}) - {group}")
                
                if len(profiles) == 0:
                    break
            else:
                print(f"   ❌ 第{page}页失败: {result.get('msg', '未知错误')}")
                break
        
        # 2. 尝试不同的分页参数
        print("\n📋 2. 不同分页参数测试")
        print("-" * 40)
        
        page_sizes = [10, 50, 200, 500]
        for page_size in page_sizes:
            result = self._make_request("GET", "/user/list", {"page": 1, "page_size": page_size}, silent=True)
            
            if result.get("code") == 0:
                data = result.get("data", {})
                profiles = data.get("list", [])
                total = data.get("total", 0)
                print(f"   页大小 {page_size}: 发现 {len(profiles)} 个配置文件 (总计: {total})")
            else:
                print(f"   页大小 {page_size}: ❌ 失败 - {result.get('msg', '未知错误')}")
        
        # 3. 尝试获取分组信息
        print("\n📋 3. 分组信息检查")
        print("-" * 40)
        
        # 尝试获取分组列表
        result = self._make_request("GET", "/user/group/list", {})
        
        if result.get("code") == 0:
            groups = result.get("data", [])
            print(f"   发现 {len(groups)} 个分组:")
            
            for group in groups:
                group_id = group.get("group_id", "N/A")
                group_name = group.get("group_name", "未知")
                print(f"      分组: {group_name} (ID: {group_id})")
                
                # 尝试获取每个分组的配置文件
                group_result = self._make_request("GET", "/user/list", {"group_id": group_id}, silent=True)
                
                if group_result.get("code") == 0:
                    group_data = group_result.get("data", {})
                    group_profiles = group_data.get("list", [])
                    print(f"         包含 {len(group_profiles)} 个配置文件")
                else:
                    print(f"         ❌ 获取失败")
        else:
            print(f"   ❌ 获取分组失败: {result.get('msg', '未知错误')}")
        
        # 4. 尝试创建最小配置文件测试限制
        print("\n📋 4. 配置文件限制测试")
        print("-" * 40)
        
        minimal_config = {
            "name": "diagnostic_test_profile",
            "group_id": "0",
            "remark": "诊断测试配置文件",
            "domain_name": "",
            "open_urls": "",
            "cookie": "",
            "fingerprint_config": {
                "automatic_timezone": 1,
                "language": ["zh-CN"],
                "screen_resolution": "1920_1080",
                "canvas": 1,
                "webgl": 1,
                "audio": 1,
                "location": "ask"
            },
            "user_proxy_config": {
                "proxy_soft": "no_proxy",
                "proxy_type": "noproxy"
            }
        }
        
        print("   尝试创建测试配置文件...")
        create_result = self._make_request("POST", "/user/create", minimal_config)
        
        if create_result.get("code") == 0:
            test_profile_id = create_result.get("data", {}).get("id")
            print(f"   ✅ 创建成功: {test_profile_id}")
            
            # 立即删除测试配置文件
            print("   清理测试配置文件...")
            delete_result = self._make_request("POST", "/user/delete", {"user_ids": [test_profile_id]}, silent=True)
            
            if delete_result.get("code") == 0:
                print("   ✅ 测试配置文件已清理")
            else:
                print("   ⚠️ 测试配置文件清理失败")
        else:
            error_msg = create_result.get("msg", "未知错误")
            print(f"   ❌ 创建失败: {error_msg}")
            
            # 分析错误信息
            if "15" in error_msg.lower() or "limit" in error_msg.lower():
                print("   🔍 检测到15个配置文件限制错误！")
                print("   📊 这说明确实有隐藏的配置文件存在")
        
        # 5. 尝试检查活跃浏览器
        print("\n📋 5. 活跃浏览器检查")
        print("-" * 40)
        
        # 尝试多种活跃浏览器API
        browser_apis = [
            "/browser/active",
            "/browser/list", 
            "/browser/status",
            "/v2/browser/list"
        ]
        
        for api in browser_apis:
            result = self._make_request("GET", api, {}, silent=True)
            
            if result.get("code") == 0:
                browser_data = result.get("data", [])
                if isinstance(browser_data, list):
                    print(f"   {api}: 发现 {len(browser_data)} 个活跃浏览器")
                else:
                    print(f"   {api}: 返回非列表数据")
            else:
                print(f"   {api}: ❌ 失败 - {result.get('msg', '未知错误')}")
        
        # 6. 尝试检查不同的用户参数
        print("\n📋 6. 用户配置检查")
        print("-" * 40)
        
        # 尝试检查用户信息
        user_info_result = self._make_request("GET", "/user/info", {})
        
        if user_info_result.get("code") == 0:
            user_data = user_info_result.get("data", {})
            print(f"   用户信息: {json.dumps(user_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"   ❌ 获取用户信息失败: {user_info_result.get('msg', '未知错误')}")
        
        # 7. 检查回收站或已删除的配置文件
        print("\n📋 7. 回收站/已删除配置文件检查")
        print("-" * 40)
        
        # 尝试一些可能的回收站API
        recycle_apis = [
            "/user/recycle/list",
            "/user/deleted/list",
            "/user/trash/list"
        ]
        
        for api in recycle_apis:
            result = self._make_request("GET", api, {}, silent=True)
            
            if result.get("code") == 0:
                deleted_data = result.get("data", [])
                if isinstance(deleted_data, list):
                    print(f"   {api}: 发现 {len(deleted_data)} 个已删除配置文件")
                else:
                    print(f"   {api}: 返回非列表数据")
            else:
                print(f"   {api}: ❌ 失败 - {result.get('msg', '未知错误')}")
        
        print("\n" + "=" * 60)
        print("🎯 诊断完成！")
        print("\n💡 建议解决方案:")
        print("1. 重启AdsPower客户端应用程序")
        print("2. 检查AdsPower客户端界面是否有隐藏的配置文件")
        print("3. 尝试手动在AdsPower客户端中创建配置文件")
        print("4. 联系AdsPower技术支持")
        print("5. 如果是付费版，确认配置文件限制数量")

def main():
    """主函数"""
    diagnostic = AdsPowerDeepDiagnostic()
    diagnostic.comprehensive_profile_scan()

if __name__ == "__main__":
    main() 