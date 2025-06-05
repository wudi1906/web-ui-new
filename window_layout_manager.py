#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强窗口布局管理器
支持20窗口高密度平铺布局（4行×5列）流式排列
每个窗口384×270像素，实现高效的多浏览器并行管理

布局示例（1920×1080屏幕）：
┌──────┬──────┬──────┬──────┬──────┐
│窗口1 │窗口2 │窗口3 │窗口4 │窗口5 │
│0,0   │384,0 │768,0 │1152,0│1536,0│
│384×270│384×270│384×270│384×270│384×270│
├──────┼──────┼──────┼──────┼──────┤
│窗口6 │窗口7 │窗口8 │窗口9 │窗口10│
│0,270 │384,270│768,270│1152,270│1536,270│
│384×270│384×270│384×270│384×270│384×270│
├──────┼──────┼──────┼──────┼──────┤
│窗口11│窗口12│窗口13│窗口14│窗口15│
│0,540 │384,540│768,540│1152,540│1536,540│
│384×270│384×270│384×270│384×270│384×270│
├──────┼──────┼──────┼──────┼──────┤
│窗口16│窗口17│窗口18│窗口19│窗口20│
│0,810 │384,810│768,810│1152,810│1536,810│
│384×270│384×270│384×270│384×270│384×270│
└──────┴──────┴──────┴──────┴──────┘

流式定位策略：
- 窗口1-5：第一行（从左到右）
- 窗口6-10：第二行（从左到右）
- 窗口11-15：第三行（从左到右）
- 窗口16-20：第四行（从左到右）
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
    """窗口位置枚举（20窗口高密度平铺 - 每个窗口384×270）"""
    # 第一行（1-5）
    ROW1_COL1 = (0, 0)        # 位置1
    ROW1_COL2 = (384, 0)      # 位置2
    ROW1_COL3 = (768, 0)      # 位置3
    ROW1_COL4 = (1152, 0)     # 位置4
    ROW1_COL5 = (1536, 0)     # 位置5
    # 第二行（6-10）
    ROW2_COL1 = (0, 270)      # 位置6
    ROW2_COL2 = (384, 270)    # 位置7
    ROW2_COL3 = (768, 270)    # 位置8
    ROW2_COL4 = (1152, 270)   # 位置9
    ROW2_COL5 = (1536, 270)   # 位置10
    # 第三行（11-15）
    ROW3_COL1 = (0, 540)      # 位置11
    ROW3_COL2 = (384, 540)    # 位置12
    ROW3_COL3 = (768, 540)    # 位置13
    ROW3_COL4 = (1152, 540)   # 位置14
    ROW3_COL5 = (1536, 540)   # 位置15
    # 第四行（16-20）
    ROW4_COL1 = (0, 810)      # 位置16
    ROW4_COL2 = (384, 810)    # 位置17
    ROW4_COL3 = (768, 810)    # 位置18
    ROW4_COL4 = (1152, 810)   # 位置19
    ROW4_COL5 = (1536, 810)   # 位置20

@dataclass
class WindowInfo:
    """窗口信息"""
    profile_id: str
    persona_name: str
    position: WindowPosition
    width: int = 384   # 20窗口高密度平铺：384×270
    height: int = 270  # 20窗口高密度平铺：384×270
    window_title: Optional[str] = None
    pid: Optional[int] = None

class WindowLayoutManager:
    """增强窗口布局管理器 - 支持20窗口并行"""
    
    def __init__(self):
        self.window_size = (384, 270)  # 20窗口高密度平铺：每个窗口384×270
        self.screen_size = (1920, 1080)  # 目标屏幕尺寸
        self.max_windows = 20  # 最大并行窗口数量
        self.active_windows: Dict[str, WindowInfo] = {}  # profile_id -> WindowInfo
        
        # 20窗口流式排列顺序（4行×5列）
        self.position_queue: List[WindowPosition] = [
            # 第一行
            WindowPosition.ROW1_COL1, WindowPosition.ROW1_COL2, WindowPosition.ROW1_COL3, 
            WindowPosition.ROW1_COL4, WindowPosition.ROW1_COL5,
            # 第二行
            WindowPosition.ROW2_COL1, WindowPosition.ROW2_COL2, WindowPosition.ROW2_COL3,
            WindowPosition.ROW2_COL4, WindowPosition.ROW2_COL5,
            # 第三行
            WindowPosition.ROW3_COL1, WindowPosition.ROW3_COL2, WindowPosition.ROW3_COL3,
            WindowPosition.ROW3_COL4, WindowPosition.ROW3_COL5,
            # 第四行
            WindowPosition.ROW4_COL1, WindowPosition.ROW4_COL2, WindowPosition.ROW4_COL3,
            WindowPosition.ROW4_COL4, WindowPosition.ROW4_COL5
        ]
        self.used_positions: List[WindowPosition] = []
        
        logger.info(f"✅ 增强窗口布局管理器初始化完成")
        logger.info(f"   支持并行窗口数量: {self.max_windows}")
        logger.info(f"   单窗口尺寸: {self.window_size[0]}×{self.window_size[1]}")
        logger.info(f"   布局策略: 4行×5列高密度平铺")
        
    def get_next_position(self) -> Optional[WindowPosition]:
        """获取下一个可用位置（20窗口流式排列）"""
        if len(self.used_positions) >= self.max_windows:
            logger.warning(f"已达到{self.max_windows}窗口限制，无法分配新位置")
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
        """设置浏览器窗口到指定位置（20窗口高密度布局）"""
        
        # 获取下一个可用位置
        position = self.get_next_position()
        if not position:
            logger.error(f"无法分配窗口位置：已达到{self.max_windows}窗口限制")
            return False
        
        x, y = position.value
        width, height = self.window_size
        current_window_number = len(self.used_positions) + 1
        
        logger.info(f"🪟 设置窗口位置: {persona_name} → 位置{current_window_number}/20 ({x},{y})")
        
        try:
            # macOS AppleScript方案：通过窗口标题定位（增强版，支持更多浏览器类型）
            if window_title:
                script = f'''
                tell application "System Events"
                    set windowFound to false
                    repeat with proc in (every process whose background only is false)
                        try
                            repeat with win in (every window of proc)
                                set winTitle to (name of win)
                                if winTitle contains "{window_title}" or winTitle contains "AdsPower" or winTitle contains "Chrome" or winTitle contains "Chromium" then
                                    set position of win to {{{x}, {y}}}
                                    set size of win to {{{width}, {height}}}
                                    set windowFound to true
                                    log "窗口已定位: " & winTitle & " 位置: " & {x} & "," & {y}
                                    exit repeat
                                end if
                            end repeat
                            if windowFound then exit repeat
                        end try
                    end repeat
                end tell
                '''
            else:
                # 通用方案：查找最前面的浏览器窗口（增强版）
                script = f'''
                tell application "System Events"
                    set windowFound to false
                    set browserApps to {{"Google Chrome", "Chromium", "AdsPower Local Browser", "Chrome"}}
                    repeat with appName in browserApps
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
                                    log "通用方案定位成功: " & appName & " 位置: " & {x} & "," & {y}
                                    exit repeat
                                end if
                            end tell
                        end try
                    end repeat
                    
                    -- 如果上述方案失败，尝试更通用的方法
                    if not windowFound then
                        repeat with proc in (every process whose background only is false)
                            try
                                repeat with win in (every window of proc)
                                    set winTitle to (name of win)
                                    if winTitle contains "问卷" or winTitle contains "survey" or winTitle contains "questionnaire" or winTitle contains ".aspx" or winTitle contains "wjx.cn" then
                                        set position of win to {{{x}, {y}}}
                                        set size of win to {{{width}, {height}}}
                                        set windowFound to true
                                        log "问卷窗口定位成功: " & winTitle & " 位置: " & {x} & "," & {y}
                                        exit repeat
                                    end if
                                end repeat
                                if windowFound then exit repeat
                            end try
                        end repeat
                    end if
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
                
                logger.info(f"✅ 窗口位置设置成功: {persona_name} @ 位置{current_window_number}/20 ({x},{y}) 尺寸{width}×{height}")
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
            
            # 移除窗口记录
            del self.active_windows[profile_id]
            
            logger.info(f"✅ 窗口记录已移除: {window_info.persona_name} (位置已释放)")
            return True
        else:
            logger.warning(f"⚠️ 未找到窗口记录: {profile_id}")
            return False
    
    def arrange_all_windows(self) -> bool:
        """重新排列所有活跃窗口（20窗口布局优化）"""
        if not self.active_windows:
            logger.info("没有活跃窗口需要排列")
            return True
        
        logger.info(f"🔄 重新排列 {len(self.active_windows)} 个活跃窗口")
        
        success_count = 0
        for profile_id, window_info in self.active_windows.items():
            x, y = window_info.position.value
            width, height = self.window_size
            
            script = f'''
            tell application "System Events"
                repeat with proc in (every process whose background only is false)
                    try
                        repeat with win in (every window of proc)
                            if (name of win) contains "{window_info.window_title or 'Chrome'}" then
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
                success_count += 1
        
        logger.info(f"✅ 窗口重排完成: {success_count}/{len(self.active_windows)} 个窗口")
        return success_count == len(self.active_windows)
    
    def get_layout_info(self) -> Dict:
        """获取当前布局信息"""
        return {
            "total_positions": self.max_windows,
            "used_positions": len(self.used_positions),
            "available_positions": self.max_windows - len(self.used_positions),
            "window_size": self.window_size,
            "screen_size": self.screen_size,
            "layout_type": "20窗口高密度平铺 (4行×5列)",
            "active_windows": [
                {
                    "profile_id": window_info.profile_id,
                    "persona_name": window_info.persona_name,
                    "position": window_info.position.value,
                    "window_title": window_info.window_title
                }
                for window_info in self.active_windows.values()
            ]
        }
    
    def cleanup_all_windows(self):
        """清理所有窗口记录"""
        self.active_windows.clear()
        self.used_positions.clear()
        logger.info("✅ 所有窗口记录已清理")

    def get_next_window_position(self, persona_name: str) -> Dict[str, int]:
        """获取下一个可用窗口位置（返回坐标字典格式）"""
        position = self.get_next_position()
        if not position:
            logger.warning(f"无法分配窗口位置：已达到{self.max_windows}窗口限制，使用默认位置")
            return {
                "x": 0,
                "y": 0, 
                "width": self.window_size[0],
                "height": self.window_size[1]
            }
        
        x, y = position.value
        width, height = self.window_size
        current_window_number = len(self.used_positions) + 1
        
        logger.info(f"🪟 为 {persona_name} 分配窗口位置{current_window_number}/20: ({x},{y}) {width}×{height}")
        
        return {
            "x": x,
            "y": y,
            "width": width,
            "height": height
        }

# 单例模式
_window_manager = None

def get_window_manager() -> WindowLayoutManager:
    """获取窗口管理器单例"""
    global _window_manager
    if _window_manager is None:
        _window_manager = WindowLayoutManager()
    return _window_manager

# 测试代码
if __name__ == "__main__":
    import asyncio
    
    async def test_window_layout():
        """测试20窗口布局"""
        manager = get_window_manager()
        
        print("🧪 测试20窗口高密度平铺布局")
        
        # 模拟分配20个窗口位置
        for i in range(20):
            profile_id = f"test_profile_{i+1}"
            persona_name = f"测试数字人{i+1}"
            
            success = manager.set_browser_window_position(profile_id, persona_name, "Chrome")
            print(f"窗口{i+1}: {'成功' if success else '失败'}")
            
            # 测试窗口限制
            if i == 19:  # 第20个窗口
                # 尝试分配第21个窗口，应该失败
                extra_success = manager.set_browser_window_position("extra_profile", "额外数字人", "Chrome")
                print(f"第21个窗口（应该失败）: {'成功' if extra_success else '失败'}")
        
        # 显示布局信息
        layout_info = manager.get_layout_info()
        print("\n📊 布局信息:")
        print(f"   总位置数: {layout_info['total_positions']}")
        print(f"   已用位置: {layout_info['used_positions']}")
        print(f"   可用位置: {layout_info['available_positions']}")
        print(f"   布局类型: {layout_info['layout_type']}")
        
        # 清理
        manager.cleanup_all_windows()
        print("\n✅ 测试完成")
    
    asyncio.run(test_window_layout()) 