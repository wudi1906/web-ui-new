#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AdsPower配置文件管理工具
用于处理AdsPower配置文件的查看、清理和管理
特别针对15个配置文件限制问题进行优化
"""

import asyncio
import requests
import time
import json
from typing import Dict, List, Optional

class AdsPowerProfileManager:
    """AdsPower配置文件管理器"""
    
    def __init__(self):
        self.config = {
            "base_url": "http://local.adspower.net:50325",
            "api_key": "cd606f2e6e4558c9c9f2980e7017b8e9",
            "timeout": 30
        }
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 更保守的请求间隔
    
    def _rate_limit_request(self):
        """API请求频率控制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(f"⏳ API频率控制：等待 {sleep_time:.1f} 秒")
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
            print(f"❌ API请求失败: {e}")
            return {"code": -1, "msg": str(e)}
    
    def check_service_status(self) -> bool:
        """检查AdsPower服务状态"""
        try:
            result = self._make_request("GET", "/status")
            return result.get("code") == 0
        except Exception as e:
            print(f"❌ AdsPower服务检查失败: {e}")
            return False
    
    def get_all_profiles(self) -> List[Dict]:
        """获取所有配置文件（包括分组和未分组）"""
        all_profiles = []
        
        try:
            # 获取第一页以确定总数
            result = self._make_request("GET", "/user/list", {"page": 1, "page_size": 100})
            
            if result.get("code") == 0:
                data = result.get("data", {})
                profiles = data.get("list", [])
                total = data.get("total", 0)
                
                all_profiles.extend(profiles)
                
                print(f"📋 第1页: 发现 {len(profiles)} 个配置文件")
                print(f"📊 总计: {total} 个配置文件")
                
                # 如果有更多页面，继续获取
                if total > 100:
                    pages = (total + 99) // 100  # 向上取整
                    for page in range(2, pages + 1):
                        print(f"📋 获取第{page}页...")
                        result = self._make_request("GET", "/user/list", {"page": page, "page_size": 100})
                        
                        if result.get("code") == 0:
                            more_profiles = result.get("data", {}).get("list", [])
                            all_profiles.extend(more_profiles)
                            print(f"   发现 {len(more_profiles)} 个配置文件")
                        else:
                            print(f"   ⚠️ 获取第{page}页失败: {result.get('msg', '未知错误')}")
            else:
                print(f"❌ 获取配置文件列表失败: {result.get('msg', '未知错误')}")
                
        except Exception as e:
            print(f"❌ 获取配置文件异常: {e}")
        
        return all_profiles
    
    def get_active_browsers(self) -> List[Dict]:
        """获取当前活跃的浏览器"""
        try:
            # 这个API可能不存在，尝试其他方法
            result = self._make_request("GET", "/browser/list")
            
            if result.get("code") == 0:
                return result.get("data", [])
            else:
                print(f"⚠️ 获取活跃浏览器失败: {result.get('msg', '未知错误')}")
                return []
                
        except Exception as e:
            print(f"❌ 获取活跃浏览器异常: {e}")
            return []
    
    def stop_browser(self, profile_id: str) -> bool:
        """停止指定配置文件的浏览器"""
        try:
            result = self._make_request("GET", "/browser/stop", {"user_id": profile_id})
            
            if result.get("code") == 0:
                print(f"✅ 浏览器停止成功: {profile_id}")
                return True
            else:
                print(f"⚠️ 浏览器停止失败: {result.get('msg', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"❌ 停止浏览器异常: {e}")
            return False
    
    def delete_profiles(self, profile_ids: List[str]) -> Dict:
        """批量删除配置文件"""
        if not profile_ids:
            return {"success": 0, "failed": 0, "errors": []}
        
        print(f"🗑️ 准备删除 {len(profile_ids)} 个配置文件...")
        
        success_count = 0
        failed_count = 0
        errors = []
        
        try:
            # 尝试批量删除
            result = self._make_request("POST", "/user/delete", {"user_ids": profile_ids})
            
            if result.get("code") == 0:
                success_count = len(profile_ids)
                print(f"✅ 批量删除成功: {len(profile_ids)} 个配置文件")
            else:
                # 批量删除失败，尝试逐个删除
                error_msg = result.get('msg', '未知错误')
                print(f"⚠️ 批量删除失败: {error_msg}")
                print(f"🔄 尝试逐个删除...")
                
                for profile_id in profile_ids:
                    try:
                        individual_result = self._make_request("POST", "/user/delete", {"user_ids": [profile_id]})
                        
                        if individual_result.get("code") == 0:
                            success_count += 1
                            print(f"   ✅ 删除成功: {profile_id}")
                        else:
                            failed_count += 1
                            error = f"{profile_id}: {individual_result.get('msg', '未知错误')}"
                            errors.append(error)
                            print(f"   ❌ 删除失败: {error}")
                            
                    except Exception as e:
                        failed_count += 1
                        error = f"{profile_id}: {str(e)}"
                        errors.append(error)
                        print(f"   ❌ 删除异常: {error}")
                        
        except Exception as e:
            print(f"❌ 删除操作异常: {e}")
            failed_count = len(profile_ids)
            errors = [f"批量操作异常: {str(e)}"]
        
        return {
            "success": success_count,
            "failed": failed_count,
            "errors": errors
        }
    
    def display_profiles_info(self, profiles: List[Dict]):
        """显示配置文件信息"""
        if not profiles:
            print("📋 没有发现配置文件")
            return
        
        print(f"\n📋 配置文件列表 (共 {len(profiles)} 个):")
        print("=" * 80)
        print(f"{'ID':<20} {'名称':<25} {'分组':<10} {'备注':<20}")
        print("-" * 80)
        
        for profile in profiles:
            profile_id = profile.get("user_id", "未知")
            name = profile.get("name", "未知")[:24]
            group_name = profile.get("group_name", "未分组")[:9]
            remark = profile.get("remark", "")[:19]
            
            print(f"{profile_id:<20} {name:<25} {group_name:<10} {remark:<20}")
        
        print("=" * 80)
    
    def interactive_cleanup(self):
        """交互式清理配置文件"""
        print("\n🧹 AdsPower配置文件清理工具")
        print("=" * 50)
        
        # 检查服务状态
        print("📋 1. 检查AdsPower服务状态...")
        if not self.check_service_status():
            print("❌ AdsPower服务不可用，请检查AdsPower客户端是否运行")
            return
        
        print("✅ AdsPower服务正常")
        
        # 获取所有配置文件
        print("\n📋 2. 获取所有配置文件...")
        profiles = self.get_all_profiles()
        
        if not profiles:
            print("✅ 没有发现配置文件，可以正常创建新的配置文件")
            return
        
        # 显示配置文件信息
        self.display_profiles_info(profiles)
        
        # 提供清理选项
        print(f"\n🔧 清理选项:")
        print(f"1. 删除所有配置文件 ({len(profiles)} 个)")
        print(f"2. 删除前10个配置文件")
        print(f"3. 删除前5个配置文件")
        print(f"4. 手动选择要删除的配置文件")
        print(f"5. 仅停止所有浏览器（不删除配置文件）")
        print(f"6. 退出")
        
        while True:
            try:
                choice = input(f"\n请选择操作 (1-6): ").strip()
                
                if choice == "1":
                    # 删除所有
                    print(f"\n⚠️ 即将删除所有 {len(profiles)} 个配置文件")
                    confirm = input("确认删除？(输入 'YES' 确认): ").strip()
                    
                    if confirm == "YES":
                        profile_ids = [p.get("user_id") for p in profiles if p.get("user_id")]
                        result = self.delete_profiles(profile_ids)
                        print(f"\n📊 清理结果:")
                        print(f"   ✅ 成功删除: {result['success']} 个")
                        print(f"   ❌ 删除失败: {result['failed']} 个")
                        if result['errors']:
                            print(f"   错误详情: {result['errors'][:3]}")  # 只显示前3个错误
                    else:
                        print("❌ 操作已取消")
                    break
                    
                elif choice == "2":
                    # 删除前10个
                    to_delete = profiles[:10]
                    print(f"\n⚠️ 即将删除前 {len(to_delete)} 个配置文件")
                    confirm = input("确认删除？(输入 'yes' 确认): ").strip()
                    
                    if confirm.lower() == "yes":
                        profile_ids = [p.get("user_id") for p in to_delete if p.get("user_id")]
                        result = self.delete_profiles(profile_ids)
                        print(f"\n📊 清理结果:")
                        print(f"   ✅ 成功删除: {result['success']} 个")
                        print(f"   ❌ 删除失败: {result['failed']} 个")
                    else:
                        print("❌ 操作已取消")
                    break
                    
                elif choice == "3":
                    # 删除前5个
                    to_delete = profiles[:5]
                    print(f"\n⚠️ 即将删除前 {len(to_delete)} 个配置文件")
                    confirm = input("确认删除？(输入 'yes' 确认): ").strip()
                    
                    if confirm.lower() == "yes":
                        profile_ids = [p.get("user_id") for p in to_delete if p.get("user_id")]
                        result = self.delete_profiles(profile_ids)
                        print(f"\n📊 清理结果:")
                        print(f"   ✅ 成功删除: {result['success']} 个")
                        print(f"   ❌ 删除失败: {result['failed']} 个")
                    else:
                        print("❌ 操作已取消")
                    break
                    
                elif choice == "4":
                    # 手动选择
                    print(f"\n📋 请输入要删除的配置文件ID (用逗号分隔):")
                    ids_input = input("配置文件ID: ").strip()
                    
                    if ids_input:
                        profile_ids = [id.strip() for id in ids_input.split(",") if id.strip()]
                        if profile_ids:
                            print(f"\n⚠️ 即将删除 {len(profile_ids)} 个指定的配置文件")
                            confirm = input("确认删除？(输入 'yes' 确认): ").strip()
                            
                            if confirm.lower() == "yes":
                                result = self.delete_profiles(profile_ids)
                                print(f"\n📊 清理结果:")
                                print(f"   ✅ 成功删除: {result['success']} 个")
                                print(f"   ❌ 删除失败: {result['failed']} 个")
                            else:
                                print("❌ 操作已取消")
                        else:
                            print("❌ 没有有效的配置文件ID")
                    else:
                        print("❌ 没有输入配置文件ID")
                    break
                    
                elif choice == "5":
                    # 仅停止浏览器
                    print(f"\n⏹️ 停止所有浏览器...")
                    stopped_count = 0
                    for profile in profiles:
                        profile_id = profile.get("user_id")
                        if profile_id:
                            if self.stop_browser(profile_id):
                                stopped_count += 1
                    print(f"✅ 成功停止 {stopped_count}/{len(profiles)} 个浏览器")
                    break
                    
                elif choice == "6":
                    print("👋 退出清理工具")
                    break
                    
                else:
                    print("❌ 无效选择，请输入 1-6")
                    
            except KeyboardInterrupt:
                print(f"\n👋 用户中断，退出清理工具")
                break
            except Exception as e:
                print(f"❌ 操作异常: {e}")
                break

def main():
    """主函数"""
    print("🧹 AdsPower配置文件管理工具")
    print("用于解决15个配置文件限制问题")
    print("=" * 50)
    
    manager = AdsPowerProfileManager()
    manager.interactive_cleanup()

if __name__ == "__main__":
    main() 