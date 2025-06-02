#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
窗口布局管理器
支持6窗口平铺布局（2行×3列）流式排列
每个窗口640×540像素，实现高效的多浏览器管理

布局示例（1920×1080屏幕）：
┌─────────┬─────────┬─────────┐
│窗口1    │窗口2    │窗口3    │
│0,0      │640,0    │1280,0   │
│640×540  │640×540  │640×540  │
├─────────┼─────────┼─────────┤
│窗口4    │窗口5    │窗口6    │
│0,540    │640,540  │1280,540 │
│640×540  │640×540  │640×540  │
└─────────┴─────────┴─────────┘

流式定位策略：
- 窗口1-3：第一行（从左到右）
- 窗口4-6：第二行（从左到右）
- 自动计算位置避免重叠
"""

import subprocess
import time
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WindowPosition(Enum):
    """窗口位置枚举（6窗口平铺 - 每个窗口640×540）"""
    TOP_LEFT = (0, 0)           # 位置1：左上
    TOP_CENTER = (640, 0)       # 位置2：中上  
    TOP_RIGHT = (1280, 0)       # 位置3：右上
    BOTTOM_LEFT = (0, 540)      # 位置4：左下
    BOTTOM_CENTER = (640, 540)  # 位置5：中下
    BOTTOM_RIGHT = (1280, 540)  # 位置6：右下

@dataclass
class WindowInfo:
    """窗口信息"""
    profile_id: str
    persona_name: str
    position: WindowPosition
    width: int = 640   # 6窗口平铺：640×540
    height: int = 540  # 6窗口平铺：640×540
    window_title: Optional[str] = None
    pid: Optional[int] = None

class WindowLayoutManager:
    """窗口布局管理器"""
    
    def __init__(self):
        self.window_size = (640, 540)  # 6窗口平铺：每个窗口640×540
        self.screen_size = (1920, 1080)  # 目标屏幕尺寸
        self.active_windows: Dict[str, WindowInfo] = {}  # profile_id -> WindowInfo
        self.position_queue: List[WindowPosition] = [
            WindowPosition.TOP_LEFT,
            WindowPosition.TOP_CENTER, 
            WindowPosition.TOP_RIGHT,
            WindowPosition.BOTTOM_LEFT,
            WindowPosition.BOTTOM_CENTER,
            WindowPosition.BOTTOM_RIGHT
        ]
        self.used_positions: List[WindowPosition] = []
        
    def get_next_position(self) -> Optional[WindowPosition]:
        """获取下一个可用位置（流式排列）"""
        if len(self.used_positions) >= 6:
            logger.warning("已达到6窗口限制，无法分配新位置")
            return None
            
        # 按流式顺序分配位置
        available_positions = [pos for pos in self.position_queue if pos not in self.used_positions]
        if available_positions:
            return available_positions[0]
        return None
    
    def _run_applescript(self, script: str) -> bool:
        """运行AppleScript命令（macOS窗口控制）"""
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.debug(f"AppleScript执行成功")
                return True
            else:
                logger.warning(f"AppleScript执行失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("AppleScript执行超时")
            return False
        except Exception as e:
            logger.error(f"AppleScript执行异常: {e}")
            return False
    
    def set_browser_window_position(self, profile_id: str, persona_name: str, 
                                   window_title: Optional[str] = None) -> bool:
        """设置浏览器窗口到指定位置"""
        
        # 获取下一个可用位置
        position = self.get_next_position()
        if not position:
            logger.error("无法分配窗口位置：已达到6窗口限制")
            return False
        
        x, y = position.value
        width, height = self.window_size
        
        logger.info(f"🪟 设置窗口位置: {persona_name} → 位置{len(self.used_positions)+1} ({x},{y})")
        
        try:
            # macOS AppleScript方案：通过窗口标题定位
            if window_title:
                script = f'''
                tell application "System Events"
                    set windowFound to false
                    repeat with proc in (every process whose background only is false)
                        try
                            repeat with win in (every window of proc)
                                if (name of win) contains "{window_title}" or (name of win) contains "AdsPower" then
                                    set position of win to {{{x}, {y}}}
                                    set size of win to {{{width}, {height}}}
                                    set windowFound to true
                                    exit repeat
                                end if
                            end repeat
                            if windowFound then exit repeat
                        end try
                    end repeat
                end tell
                '''
            else:
                # 通用方案：查找最前面的浏览器窗口
                script = f'''
                tell application "System Events"
                    set windowFound to false
                    repeat with appName in {{"Google Chrome", "Chromium", "AdsPower Local Browser"}}
                        try
                            tell application appName
                                if (count of windows) > 0 then
                                    set frontWindow to front window
                                    tell application "System Events"
                                        tell process appName
                                            set position of front window to {{{x}, {y}}}
                                            set size of front window to {{{width}, {height}}}
                                        end tell
                                    end tell
                                    set windowFound to true
                                    exit repeat
                                end if
                            end tell
                        end try
                    end repeat
                end tell
                '''
            
            success = self._run_applescript(script)
            
            if success:
                # 创建窗口信息记录
                window_info = WindowInfo(
                    profile_id=profile_id,
                    persona_name=persona_name,
                    position=position,
                    window_title=window_title
                )
                
                # 更新管理状态
                self.active_windows[profile_id] = window_info
                self.used_positions.append(position)
                
                logger.info(f"✅ 窗口位置设置成功: {persona_name} @ ({x},{y})")
                return True
            else:
                logger.error(f"❌ 窗口位置设置失败: {persona_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 设置窗口位置异常: {e}")
            return False
    
    def remove_window(self, profile_id: str) -> bool:
        """移除窗口记录，释放位置"""
        if profile_id in self.active_windows:
            window_info = self.active_windows[profile_id]
            
            # 释放位置
            if window_info.position in self.used_positions:
                self.used_positions.remove(window_info.position)
            
            # 移除记录
            del self.active_windows[profile_id]
            
            logger.info(f"🗑️ 释放窗口位置: {window_info.persona_name}")
            return True
        return False
    
    def arrange_all_windows(self) -> bool:
        """重新排列所有活跃窗口（紧凑布局）"""
        logger.info("🔄 重新排列所有窗口...")
        
        # 清空位置状态
        self.used_positions.clear()
        
        # 重新分配位置
        success_count = 0
        for profile_id, window_info in self.active_windows.items():
            new_position = self.get_next_position()
            if new_position:
                x, y = new_position.value
                width, height = self.window_size
                
                # 更新窗口位置
                script = f'''
                tell application "System Events"
                    repeat with proc in (every process whose background only is false)
                        try
                            repeat with win in (every window of proc)
                                if (name of win) contains "{window_info.persona_name}" or (name of win) contains "AdsPower" then
                                    set position of win to {{{x}, {y}}}
                                    set size of win to {{{width}, {height}}}
                                    exit repeat
                                end if
                            end repeat
                        end try
                    end repeat
                end tell
                '''
                
                if self._run_applescript(script):
                    window_info.position = new_position
                    self.used_positions.append(new_position)
                    success_count += 1
        
        logger.info(f"✅ 窗口重排完成: {success_count}/{len(self.active_windows)} 个窗口")
        return success_count == len(self.active_windows)
    
    def get_layout_info(self) -> Dict:
        """获取当前布局信息"""
        return {
            "total_windows": len(self.active_windows),
            "max_windows": 6,
            "available_positions": 6 - len(self.used_positions),
            "active_windows": [
                {
                    "profile_id": profile_id,
                    "persona_name": info.persona_name,
                    "position": info.position.name,
                    "coordinates": info.position.value
                }
                for profile_id, info in self.active_windows.items()
            ]
        }
    
    def cleanup_all_windows(self):
        """清理所有窗口记录"""
        logger.info("🧹 清理所有窗口布局记录...")
        self.active_windows.clear()
        self.used_positions.clear()
        logger.info("✅ 窗口布局记录已清理")

# 全局窗口管理器实例
window_manager = WindowLayoutManager()

def get_window_manager() -> WindowLayoutManager:
    """获取全局窗口管理器实例"""
    return window_manager

if __name__ == "__main__":
    # 测试代码
    async def test_window_layout():
        """测试窗口布局功能"""
        logger.info("🧪 测试6窗口平铺布局...")
        
        manager = get_window_manager()
        
        # 模拟6个窗口的设置
        test_profiles = [
            ("profile1", "张三"),
            ("profile2", "李四"),
            ("profile3", "王五"),
            ("profile4", "赵六"),
            ("profile5", "钱七"),
            ("profile6", "孙八")
        ]
        
        for profile_id, name in test_profiles:
            success = manager.set_browser_window_position(profile_id, name)
            logger.info(f"设置窗口 {name}: {'成功' if success else '失败'}")
            time.sleep(0.5)  # 避免操作过快
        
        # 打印布局信息
        layout_info = manager.get_layout_info()
        logger.info(f"当前布局: {layout_info}")
        
        # 测试重排
        logger.info("测试窗口重排...")
        manager.arrange_all_windows()
        
    import asyncio
    asyncio.run(test_window_layout()) 