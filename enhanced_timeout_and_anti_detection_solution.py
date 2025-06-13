#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强超时和反作弊解决方案
======================

解决以下问题：
1. 页面加载超时（特别是国家选择等复杂页面）
2. 下拉框处理错误
3. 反作弊机制完善
4. 页面跳转后的稳定性

核心战略目标：
1. 最大限度绕开反作弊机制
2. 最大程度利用WebUI智能答题特性
3. 准确根据提示词和数字人信息作答所有可见试题
4. 正常等待页面跳转并保证多次跳转后依然可以正常作答
"""

import asyncio
import time
import random
from typing import Dict, Any, Optional


class EnhancedTimeoutAndAntiDetectionSolution:
    """增强的超时和反检测解决方案"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def apply_enhanced_timeouts(self, agent):
        """应用增强的超时设置"""
        try:
            self.logger.info("🔧 应用增强超时设置...")
            
            # 1. 浏览器基础超时 - 从30秒提升到90秒
            if hasattr(agent, 'browser_context'):
                agent.browser_context.set_default_timeout(90000)  # 90秒
                self.logger.info("✅ 浏览器默认超时: 90秒")
                
                # 2. 页面导航超时 - 3分钟
                if hasattr(agent.browser_context, 'set_default_navigation_timeout'):
                    agent.browser_context.set_default_navigation_timeout(180000)  # 3分钟
                    self.logger.info("✅ 页面导航超时: 180秒")
            
            # 3. Agent失败容忍度提升
            if hasattr(agent, 'max_failures'):
                agent.max_failures = 30  # 提升到30次
                self.logger.info(f"✅ 失败容忍度: {agent.max_failures}次")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 超时设置失败: {e}")
            return False
    
    async def enhanced_page_wait_strategy(self, page, max_wait_time=300):
        """增强的页面等待策略 - 最长5分钟"""
        start_time = time.time()
        
        self.logger.info(f"⏳ 开始增强页面等待，最长{max_wait_time}秒...")
        
        while time.time() - start_time < max_wait_time:
            try:
                # 1. 检查基本页面状态
                ready_state = await page.evaluate("document.readyState")
                
                if ready_state == "complete":
                    # 2. 额外等待动态内容
                    await asyncio.sleep(3)
                    
                    # 3. 检查加载指示器
                    loading_indicators = await page.evaluate("""
                        () => {
                            const indicators = document.querySelectorAll(
                                '.loading, .spinner, .loader, .loading-mask, ' +
                                '[class*="load"], [id*="load"], [class*="spin"]'
                            );
                            return Array.from(indicators).some(el => 
                                el.offsetHeight > 0 && 
                                getComputedStyle(el).display !== 'none' &&
                                getComputedStyle(el).visibility !== 'hidden'
                            );
                        }
                    """)
                    
                    # 4. 检查网络活动
                    try:
                        await page.wait_for_load_state('networkidle', timeout=5000)
                        network_idle = True
                    except:
                        network_idle = False
                    
                    if not loading_indicators and network_idle:
                        self.logger.info("✅ 页面完全加载完成")
                        return True
                
                # 等待1秒后重试
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.debug(f"页面状态检查异常: {e}")
                await asyncio.sleep(2)
        
        self.logger.warning(f"⚠️ 页面等待超时 ({max_wait_time}秒)")
        return False
    
    async def setup_advanced_anti_detection(self, page):
        """设置高级反检测机制"""
        try:
            self.logger.info("🛡️ 注入高级反检测脚本...")
            
            await page.add_init_script("""
                // === 核心反检测机制 ===
                
                // 1. 隐藏webdriver标识
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // 2. 伪装Chrome运行时
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {},
                    webstore: {}
                };
                
                // 3. 伪装插件列表
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                        {name: 'Native Client', filename: 'internal-nacl-plugin'}
                    ],
                });
                
                // 4. 伪装语言列表
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                });
                
                // 5. 增强鼠标事件真实性
                const originalAddEventListener = EventTarget.prototype.addEventListener;
                EventTarget.prototype.addEventListener = function(type, listener, options) {
                    if (['click', 'mousedown', 'mouseup', 'mousemove'].includes(type)) {
                        const wrappedListener = function(event) {
                            // 添加微小随机延迟，模拟人类反应时间
                            setTimeout(() => {
                                listener.call(this, event);
                            }, Math.random() * 15 + 5);
                        };
                        return originalAddEventListener.call(this, type, wrappedListener, options);
                    }
                    return originalAddEventListener.call(this, type, listener, options);
                };
                
                // 6. 伪装屏幕信息
                Object.defineProperty(screen, 'availHeight', {
                    get: () => 1040 + Math.floor(Math.random() * 40),
                });
                Object.defineProperty(screen, 'availWidth', {
                    get: () => 1920 + Math.floor(Math.random() * 40),
                });
                
                // 7. 伪装时区
                Date.prototype.getTimezoneOffset = function() {
                    return -480; // 中国时区
                };
                
                // 8. 隐藏自动化痕迹
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            """)
            
            self.logger.info("✅ 高级反检测脚本注入成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 反检测脚本注入失败: {e}")
            return False
    
    async def enhanced_dropdown_handler(self, index, text, browser):
        """增强的下拉框处理器 - 具备强反检测能力"""
        try:
            self.logger.info(f"🎯 增强下拉框处理: index={index}, text='{text}'")
            
            page = await browser.get_current_page()
            
            # 应用反检测
            await self.setup_advanced_anti_detection(page)
            
            # 人类化操作序列
            result = await page.evaluate(f"""
                new Promise(async (resolve) => {{
                    const targetText = "{text.replace('"', '\\"')}";
                    const maxAttempts = 15;  // 增加尝试次数
                    
                    // 人类化延迟函数
                    const humanDelay = (min = 200, max = 500) => 
                        new Promise(r => setTimeout(r, min + Math.random() * (max - min)));
                    
                    // 查找下拉框元素
                    const selectors = [
                        'select', '[role="combobox"]', '.select', '.dropdown',
                        '.jqselect', '.ui-selectmenu', '.el-select', '.ant-select',
                        '[class*="select"]', '[class*="dropdown"]'
                    ];
                    
                    let dropdown = null;
                    for (let selector of selectors) {{
                        const elements = document.querySelectorAll(selector);
                        for (let el of elements) {{
                            if (el.offsetHeight > 0 && getComputedStyle(el).display !== 'none') {{
                                dropdown = el;
                                break;
                            }}
                        }}
                        if (dropdown) break;
                    }}
                    
                    if (!dropdown) {{
                        resolve({{ success: false, error: "未找到下拉框" }});
                        return;
                    }}
                    
                    // 滚动到元素可见
                    dropdown.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    await humanDelay(300, 600);
                    
                    // 人类化点击展开
                    const rect = dropdown.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2 + (Math.random() - 0.5) * 20;
                    const centerY = rect.top + rect.height / 2 + (Math.random() - 0.5) * 10;
                    
                    // 模拟真实的鼠标事件序列
                    const events = ['mouseenter', 'mouseover', 'mousedown', 'focus', 'click', 'mouseup'];
                    for (let i = 0; i < events.length; i++) {{
                        await humanDelay(50, 150);
                        const event = new MouseEvent(events[i], {{
                            bubbles: true,
                            clientX: centerX + Math.random() * 4 - 2,
                            clientY: centerY + Math.random() * 4 - 2
                        }});
                        dropdown.dispatchEvent(event);
                    }}
                    
                    // 等待选项出现
                    await humanDelay(800, 1200);
                    
                    // 查找并选择选项
                    const optionSelectors = [
                        'option', '.option', '.dropdown-item', '[role="option"]',
                        '.el-select-dropdown__item', '.ant-select-item',
                        '.ui-menu-item', '.select-option'
                    ];
                    
                    let optionFound = false;
                    for (let attempt = 0; attempt < maxAttempts && !optionFound; attempt++) {{
                        // 搜索可见选项
                        for (let selector of optionSelectors) {{
                            const options = document.querySelectorAll(selector);
                            for (let option of options) {{
                                if (option.offsetHeight > 0 && 
                                    getComputedStyle(option).display !== 'none' &&
                                    (option.textContent.trim().includes(targetText) ||
                                     option.textContent.trim() === targetText)) {{
                                    
                                    // 人类化选择
                                    await humanDelay(200, 400);
                                    
                                    // 滚动到选项可见
                                    option.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
                                    await humanDelay(100, 200);
                                    
                                    // 点击选项
                                    option.click();
                                    option.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    option.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    
                                    optionFound = true;
                                    resolve({{ success: true, selected: targetText }});
                                    return;
                                }}
                            }}
                        }}
                        
                        // 如果没找到，尝试滚动
                        if (!optionFound) {{
                            const containers = document.querySelectorAll(
                                '.dropdown-menu, .select-dropdown, [role="listbox"], ' +
                                '.options-container, .dropdown-options'
                            );
                            for (let container of containers) {{
                                if (container.scrollHeight > container.clientHeight) {{
                                    const scrollAmount = Math.min(100, container.scrollHeight - container.scrollTop - container.clientHeight);
                                    if (scrollAmount > 0) {{
                                        container.scrollTop += scrollAmount;
                                        await humanDelay(400, 600);
                                        break;
                                    }}
                                }}
                            }}
                        }}
                    }}
                    
                    resolve({{ success: false, error: "选项未找到或无法选择" }});
                }});
            """)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 增强下拉框处理失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_timeout_configuration(self):
        """获取超时配置建议"""
        return {
            "browser_default_timeout": 90000,   # 90秒
            "navigation_timeout": 180000,       # 3分钟
            "page_load_wait": 300,              # 5分钟
            "network_idle_timeout": 120000,     # 2分钟
            "element_wait_timeout": 60000,      # 1分钟
            "dropdown_operation_timeout": 30000, # 30秒
            "max_failures": 30,                 # 30次失败容忍
            "page_stability_checks": 3,         # 3次稳定性检查
            "human_delay_range": (200, 800)     # 人类化延迟范围
        }
    
    def apply_to_adspower_integration(self, integration_instance):
        """应用到AdsPower集成实例"""
        try:
            self.logger.info("🔧 应用增强配置到AdsPower集成...")
            
            # 修改超时设置
            config = self.get_timeout_configuration()
            
            # 如果有相关属性，进行设置
            for attr, value in config.items():
                if hasattr(integration_instance, attr):
                    setattr(integration_instance, attr, value)
                    self.logger.info(f"✅ 设置 {attr} = {value}")
            
            # 绑定增强方法
            integration_instance.enhanced_page_wait_strategy = self.enhanced_page_wait_strategy
            integration_instance.enhanced_dropdown_handler = self.enhanced_dropdown_handler
            integration_instance.setup_advanced_anti_detection = self.setup_advanced_anti_detection
            
            self.logger.info("✅ 增强配置应用完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置应用失败: {e}")
            return False


# 集成指南
INTEGRATION_GUIDE = """
集成指南：
========

1. 修改 adspower_browser_use_integration.py 中的超时设置：

第6395行：await page.wait_for_load_state('networkidle', timeout=120000)
第8331行：await page.wait_for_load_state('networkidle', timeout=120000)  
第12233行：await page.wait_for_load_state('networkidle', timeout=120000)

2. 在 enhance_browser_connection_stability 方法中添加：

```python
# 设置更长的超时时间，特别针对国家选择等复杂页面
agent.browser_context.set_default_timeout(90000)   # 90秒超时
agent.browser_context.set_default_navigation_timeout(180000)  # 3分钟导航超时
```

3. 在下拉框处理函数中添加反检测脚本注入

4. 将所有 timeout=30000 改为 timeout=180000

5. 将 max_failures 从 20 改为 30
"""

if __name__ == "__main__":
    print("增强超时和反作弊解决方案")
    print("=" * 50)
    print(INTEGRATION_GUIDE) 