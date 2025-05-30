#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AdsPower应急配置文件清理工具
用于强制清理隐藏的配置文件，解决"超过15个限制"但API显示0个配置文件的问题
"""

import requests
import time
import json
from typing import Dict, List, Optional

class EmergencyAdsPowerCleanup:
    """AdsPower应急清理工具"""
    
    def __init__(self):
        self.config = {
            "base_url": "http://local.adspower.net:50325",
            "api_key": "cd606f2e6e4558c9c9f2980e7017b8e9",
            "timeout": 30
        }
        self.last_request_time = 0
        self.min_request_interval = 2.0
    
    def _rate_limit_request(self):
        """API请求频率控制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
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
            
            if method.upper() == "GET":
                response = requests.get(url, params=request_data, timeout=self.config["timeout"])
            else:
                response = requests.post(url, json=request_data, timeout=self.config["timeout"])
            
            response.raise_for_status()
            result = response.json()
            return result
            
        except Exception as e:
            return {"code": -1, "msg": str(e), "error": True}
    
    def attempt_force_cleanup_by_id_range(self):
        """尝试通过ID范围强制清理配置文件"""
        print("🔥 尝试通过ID范围强制清理隐藏配置文件...")
        print("-" * 50)
        
        # 尝试删除可能的配置文件ID
        # AdsPower的配置文件ID通常是字母数字组合
        possible_id_patterns = [
            # 常见的ID格式
            ["j7qczg4", "k8rdah5", "l9seb16", "m0tfc27", "n1ugd38"],  # 随机字母数字
            ["profile_1", "profile_2", "profile_3", "profile_4", "profile_5"],  # 可能的命名格式
            ["test_1", "test_2", "test_3", "test_4", "test_5"],  # 测试配置文件
        ]
        
        for pattern_index, id_pattern in enumerate(possible_id_patterns):
            print(f"\n🔍 尝试ID模式 {pattern_index + 1}: {id_pattern}")
            
            for profile_id in id_pattern:
                try:
                    print(f"   尝试删除: {profile_id}")
                    
                    result = self._make_request("POST", "/user/delete", {"user_ids": [profile_id]})
                    
                    if result.get("code") == 0:
                        print(f"   ✅ 删除成功: {profile_id}")
                    elif result.get("code") == -1 and "Profile does not exist" in result.get("msg", ""):
                        print(f"   ➖ 配置文件不存在: {profile_id}")
                    else:
                        print(f"   ❌ 删除失败: {result.get('msg', '未知错误')}")
                        
                except Exception as e:
                    print(f"   ❌ 删除异常: {e}")
    
    def attempt_bulk_cleanup(self):
        """尝试批量清理操作"""
        print("\n🔥 尝试批量清理操作...")
        print("-" * 50)
        
        # 尝试一些可能的批量删除操作
        bulk_operations = [
            {"operation": "delete_all", "user_ids": []},  # 删除所有
            {"operation": "clear_cache"},  # 清理缓存
            {"operation": "reset_profiles"},  # 重置配置文件
        ]
        
        for operation in bulk_operations:
            try:
                print(f"🔍 尝试操作: {operation}")
                
                result = self._make_request("POST", "/user/delete", operation)
                
                if result.get("code") == 0:
                    print(f"   ✅ 操作成功")
                else:
                    print(f"   ❌ 操作失败: {result.get('msg', '未知错误')}")
                    
            except Exception as e:
                print(f"   ❌ 操作异常: {e}")
    
    def attempt_service_restart_simulation(self):
        """尝试模拟服务重启"""
        print("\n🔄 尝试模拟服务重启...")
        print("-" * 50)
        
        # 尝试一些可能的重启或刷新操作
        restart_apis = [
            "/user/refresh",
            "/user/reload", 
            "/user/reset",
            "/service/restart",
            "/cache/clear"
        ]
        
        for api in restart_apis:
            try:
                print(f"🔍 尝试API: {api}")
                
                result = self._make_request("POST", api, {})
                
                if result.get("code") == 0:
                    print(f"   ✅ 成功")
                else:
                    print(f"   ❌ 失败: {result.get('msg', '未知错误')}")
                    
            except Exception as e:
                print(f"   ❌ 异常: {e}")
    
    def test_create_after_cleanup(self):
        """清理后测试创建配置文件"""
        print("\n🧪 测试清理效果...")
        print("-" * 50)
        
        test_config = {
            "name": f"emergency_test_{int(time.time())}",
            "group_id": "0",
            "remark": "应急清理测试配置文件",
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
        
        print("🔍 尝试创建测试配置文件...")
        
        result = self._make_request("POST", "/user/create", test_config)
        
        if result.get("code") == 0:
            test_profile_id = result.get("data", {}).get("id")
            print(f"✅ 创建成功！配置文件ID: {test_profile_id}")
            print("🎉 15个配置文件限制问题已解决！")
            
            # 清理测试配置文件
            print("🧹 清理测试配置文件...")
            delete_result = self._make_request("POST", "/user/delete", {"user_ids": [test_profile_id]})
            
            if delete_result.get("code") == 0:
                print("✅ 测试配置文件已清理")
            
            return True
        else:
            error_msg = result.get("msg", "未知错误")
            print(f"❌ 创建仍然失败: {error_msg}")
            
            if "15" in error_msg.lower() or "limit" in error_msg.lower():
                print("⚠️ 15个配置文件限制仍然存在")
            
            return False
    
    def emergency_cleanup_procedure(self):
        """应急清理程序"""
        print("🚨 AdsPower应急配置文件清理程序")
        print("=" * 60)
        print("⚠️ 警告：这个工具会尝试强制清理隐藏的配置文件")
        print("⚠️ 请确保你已经保存了重要的配置文件信息")
        print("=" * 60)
        
        # 用户确认
        confirm = input("\n是否继续应急清理？(输入 'YES' 确认): ").strip()
        
        if confirm != "YES":
            print("❌ 应急清理已取消")
            return
        
        print("\n🚀 开始应急清理程序...")
        
        # 第一步：检查当前状态
        print("\n📋 第1步：检查当前状态")
        current_profiles = self._make_request("GET", "/user/list", {"page": 1, "page_size": 100})
        
        if current_profiles.get("code") == 0:
            profile_count = len(current_profiles.get("data", {}).get("list", []))
            total = current_profiles.get("data", {}).get("total", 0)
            print(f"   API显示: {profile_count} 个配置文件 (总计: {total})")
        else:
            print(f"   ❌ 获取配置文件失败: {current_profiles.get('msg', '未知错误')}")
        
        # 第二步：尝试ID范围清理
        print("\n📋 第2步：尝试ID范围强制清理")
        self.attempt_force_cleanup_by_id_range()
        
        # 第三步：尝试批量清理
        print("\n📋 第3步：尝试批量清理操作")
        self.attempt_bulk_cleanup()
        
        # 第四步：尝试服务重启模拟
        print("\n📋 第4步：尝试服务重启模拟")
        self.attempt_service_restart_simulation()
        
        # 第五步：等待并测试
        print("\n📋 第5步：等待并测试创建")
        print("⏳ 等待5秒让操作生效...")
        time.sleep(5)
        
        success = self.test_create_after_cleanup()
        
        # 第六步：生成报告
        print("\n📋 第6步：应急清理报告")
        print("=" * 60)
        
        if success:
            print("🎉 应急清理成功！")
            print("✅ 现在可以正常创建AdsPower配置文件了")
            print("\n💡 建议：")
            print("   1. 重新启动你的问卷填写任务")
            print("   2. 监控配置文件数量，避免再次超过限制")
        else:
            print("❌ 应急清理失败，问题仍然存在")
            print("\n💡 建议：")
            print("   1. 重启AdsPower客户端应用程序")
            print("   2. 在AdsPower客户端界面手动检查和删除配置文件")
            print("   3. 联系AdsPower技术支持")
            print("   4. 如果是付费版，确认配置文件限制数量")
        
        print("=" * 60)

def main():
    """主函数"""
    cleanup_tool = EmergencyAdsPowerCleanup()
    cleanup_tool.emergency_cleanup_procedure()

if __name__ == "__main__":
    main() 