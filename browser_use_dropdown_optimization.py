"""
Browser-use 下拉框处理优化方案
=====================================

基于对browser-use原生代码的深入分析，提供针对性的优化方案
解决自定义下拉框滚动和选择问题
"""

import asyncio
import json
import logging
import random
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class EnhancedDropdownHandler:
    """增强版下拉框处理器，补充browser-use的不足"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        
    async def smart_dropdown_selection(self, index: int, target_text: str) -> Dict:
        """
        智能下拉框选择 - 兼容原生select和自定义下拉框
        
        处理流程：
        1. 检测下拉框类型（原生 vs 自定义）
        2. 根据类型选择最优策略
        3. 处理滚动和选项查找
        4. 执行选择操作
        """
        try:
            # 第一步：检测下拉框类型
            dropdown_type = await self._detect_dropdown_type(index)
            
            if dropdown_type["is_native_select"]:
                # 原生select：使用增强的原生处理
                return await self._handle_native_select_with_scroll(index, target_text)
            else:
                # 自定义下拉框：使用WebUI风格的处理
                return await self._handle_custom_dropdown_webui_style(index, target_text)
                
        except Exception as e:
            return {"success": False, "error": f"下拉框处理失败: {e}"}
    
    async def _detect_dropdown_type(self, index: int) -> Dict:
        """检测下拉框类型和特征"""
        try:
            selector_map = await self.browser_context.get_selector_map()
            dom_element = selector_map[index]
            
            detection_result = await self.browser_context.execute_javascript(f"""
            (() => {{
                const element = document.evaluate('{dom_element.xpath}', document, null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                
                if (!element) return {{ found: false }};
                
                const tagName = element.tagName.toLowerCase();
                const isNativeSelect = tagName === 'select';
                
                return {{
                    found: true,
                    is_native_select: isNativeSelect,
                    tag_name: tagName,
                    class_list: Array.from(element.classList)
                }};
            }})();
            """)
            
            return detection_result if detection_result else {"found": False}
            
        except Exception as e:
            return {"found": False, "error": f"检测失败: {e}"}
    
    async def _handle_native_select_with_scroll(self, index: int, target_text: str) -> Dict:
        """
        处理原生select（增强browser-use的原生逻辑）
        
        WebUI原生逻辑的问题：
        - 不处理大量选项的滚动
        - 假设所有选项都可见
        
        我们的增强：
        - 添加滚动支持
        - 智能定位目标选项
        """
        try:
            logger.info(f"🎯 处理原生select，目标: '{target_text}'")
            
            # 第一步：获取所有选项（类似browser-use的get_dropdown_options）
            options_info = await self._get_native_select_options(index)
            
            if not options_info["success"]:
                return options_info
            
            # 第二步：查找目标选项
            target_option = None
            for opt in options_info["options"]:
                if target_text.lower() in opt["text"].lower():
                    target_option = opt
                    break
            
            if not target_option:
                return {
                    "success": False, 
                    "error": f"在{len(options_info['options'])}个选项中未找到: '{target_text}'"
                }
            
            # 第三步：如果选项很多，先滚动到目标位置
            if len(options_info["options"]) > 10:
                await self._scroll_native_select_to_option(index, target_option["index"])
            
            # 第四步：使用browser-use的原生选择方法
            return await self._execute_native_select(index, target_text)
            
        except Exception as e:
            return {"success": False, "error": f"原生select处理失败: {e}"}
    
    async def _handle_custom_dropdown_webui_style(self, index: int, target_text: str) -> Dict:
        """
        处理自定义下拉框（WebUI风格的处理方式）
        
        模拟WebUI的处理逻辑：
        1. 简洁直接
        2. 最少的复杂性
        3. 专注于结果
        """
        try:
            logger.info(f"🎯 处理自定义下拉框，目标: '{target_text}'")
            
            # 第一步：确保下拉框展开
            expand_result = await self._webui_style_expand_dropdown(index)
            if not expand_result["success"]:
                return expand_result
            
            # 第二步：查找并滚动到目标选项
            scroll_result = await self._webui_style_scroll_to_option(target_text)
            
            # 第三步：选择目标选项
            selection_result = await self._webui_style_select_option(target_text)
            
            return selection_result
            
        except Exception as e:
            return {"success": False, "error": f"自定义下拉框处理失败: {e}"}
    
    async def _webui_style_expand_dropdown(self, index: int) -> Dict:
        """WebUI风格的下拉框展开"""
        try:
            selector_map = await self.browser_context.get_selector_map()
            dom_element = selector_map[index]
            
            expand_result = await self.browser_context.execute_javascript(f"""
            (() => {{
                const element = document.evaluate('{dom_element.xpath}', document, null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                
                if (!element) return {{ success: false, error: "元素未找到" }};
                
                try {{
                    element.click();
                    
                    // 等待展开完成
                    return new Promise(resolve => {{
                        setTimeout(() => {{
                            const optionContainers = document.querySelectorAll(
                                '.dropdown-menu, .select-dropdown, .options-container, ' +
                                '.jqselect-options, [role="listbox"], .dropdown-options'
                            );
                            
                            let expanded = false;
                            for (let container of optionContainers) {{
                                if (container.offsetHeight > 0) {{
                                    expanded = true;
                                    break;
                                }}
                            }}
                            
                            resolve({{ 
                                success: expanded, 
                                message: expanded ? "下拉框已展开" : "下拉框展开失败"
                            }});
                        }}, 300);
                    }});
                }} catch(e) {{
                    return {{ success: false, error: "点击失败: " + e.message }};
                }}
            }})();
            """)
            
            return expand_result if expand_result else {"success": False, "error": "展开脚本返回空"}
            
        except Exception as e:
            return {"success": False, "error": f"展开失败: {e}"}
    
    async def _webui_style_scroll_to_option(self, target_text: str) -> Dict:
        """WebUI风格的选项滚动 - 解决核心滚动问题"""
        try:
            scroll_result = await self.browser_context.execute_javascript(f"""
            (() => {{
                const targetText = "{target_text.replace('"', '\\"')}";
                
                const containers = document.querySelectorAll(
                    '.dropdown-menu, .select-dropdown, .options-container, ' +
                    '.jqselect-options, [role="listbox"], .dropdown-options'
                );
                
                for (let container of containers) {{
                    if (container.offsetHeight > 0 && container.scrollHeight > container.clientHeight) {{
                        let scrollAttempts = 0;
                        const maxScrollAttempts = 10;
                        const scrollStep = container.clientHeight / 3;
                        
                        while (scrollAttempts < maxScrollAttempts) {{
                            container.scrollTop += scrollStep;
                            
                            const options = container.querySelectorAll(
                                'li, .option, .dropdown-item, [role="option"], .item'
                            );
                            
                            for (let option of options) {{
                                if (option.offsetHeight > 0) {{
                                    const optionText = option.textContent.trim();
                                    if (optionText.includes(targetText) || optionText === targetText) {{
                                        option.scrollIntoView({{ 
                                            behavior: 'smooth', 
                                            block: 'center' 
                                        }});
                                        
                                        return {{
                                            success: true,
                                            found: true,
                                            scrolled: true,
                                            scroll_attempts: scrollAttempts + 1
                                        }};
                                    }}
                                }}
                            }}
                            
                            scrollAttempts++;
                            if (container.scrollTop + container.clientHeight >= container.scrollHeight - 10) {{
                                break;
                            }}
                        }}
                        
                        return {{
                            success: false,
                            found: false,
                            scrolled: true,
                            scroll_attempts: scrollAttempts
                        }};
                    }}
                }}
                
                return {{ success: true, found: true, scrolled: false }};
            }})();
            """)
            
            if scroll_result and scroll_result.get("scrolled"):
                await asyncio.sleep(0.5)
            
            return scroll_result if scroll_result else {"success": False, "error": "滚动脚本返回空"}
            
        except Exception as e:
            return {"success": False, "error": f"滚动失败: {e}"}
    
    async def _webui_style_select_option(self, target_text: str) -> Dict:
        """WebUI风格的选项选择"""
        try:
            selection_result = await self.browser_context.execute_javascript(f"""
            (() => {{
                const targetText = "{target_text.replace('"', '\\"')}";
                
                const containers = document.querySelectorAll(
                    '.dropdown-menu, .select-dropdown, .options-container, ' +
                    '.jqselect-options, [role="listbox"], .dropdown-options'
                );
                
                for (let container of containers) {{
                    if (container.offsetHeight > 0) {{
                        const options = container.querySelectorAll(
                            'li, .option, .dropdown-item, [role="option"], .item'
                        );
                        
                        for (let option of options) {{
                            if (option.offsetHeight > 0) {{
                                const optionText = option.textContent.trim();
                                if (optionText.includes(targetText) || optionText === targetText) {{
                                    option.click();
                                    option.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    
                                    return {{
                                        success: true,
                                        selected_text: optionText
                                    }};
                                }}
                            }}
                        }}
                    }}
                }}
                
                return {{ success: false, error: "未找到可点击的目标选项" }};
            }})();
            """)
            
            await asyncio.sleep(0.3)
            
            return selection_result if selection_result else {"success": False, "error": "选择脚本返回空"}
            
        except Exception as e:
            return {"success": False, "error": f"选择失败: {e}"}
    
    async def _get_native_select_options(self, index: int) -> Dict:
        """获取原生select的所有选项（仿照browser-use逻辑）"""
        try:
            selector_map = await self.browser_context.get_selector_map()
            dom_element = selector_map[index]
            
            options_result = await self.browser_context.execute_javascript(f"""
            (() => {{
                const select = document.evaluate('{dom_element.xpath}', document, null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                
                if (!select || select.tagName.toLowerCase() !== 'select') {{
                    return {{ success: false, error: "不是有效的select元素" }};
                }}
                
                const options = Array.from(select.options).map((opt, idx) => ({{
                    text: opt.text,
                    value: opt.value,
                    index: idx
                }}));
                
                return {{
                    success: true,
                    options: options,
                    total_count: options.length
                }};
            }})();
            """)
            
            return options_result if options_result else {"success": False, "error": "获取选项脚本返回空"}
            
        except Exception as e:
            return {"success": False, "error": f"获取选项失败: {e}"}
    
    async def _scroll_native_select_to_option(self, index: int, option_index: int):
        """在原生select中滚动到指定选项"""
        try:
            selector_map = await self.browser_context.get_selector_map()
            dom_element = selector_map[index]
            
            await self.browser_context.execute_javascript(f"""
            (() => {{
                const select = document.evaluate('{dom_element.xpath}', document, null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                
                if (select && select.options[{option_index}]) {{
                    // 预选目标选项，这会自动滚动
                    select.selectedIndex = {option_index};
                    
                    // 确保滚动到正确位置
                    const optionHeight = 20; // 估算的选项高度
                    select.scrollTop = {option_index} * optionHeight;
                }}
            }})();
            """)
            
            await asyncio.sleep(0.2)  # 给滚动一些时间
            
        except Exception as e:
            logger.warning(f"原生select滚动失败: {e}")
    
    async def _execute_native_select(self, index: int, target_text: str) -> Dict:
        """执行原生select选择（类似browser-use的select_dropdown_option）"""
        try:
            selector_map = await self.browser_context.get_selector_map()
            dom_element = selector_map[index]
            
            # 使用类似browser-use的选择逻辑
            page = await self.browser_context.get_current_page()
            
            selected_option_values = await page.locator(f'//{dom_element.xpath}').select_option(
                label=target_text, 
                timeout=1000
            )
            
            return {
                "success": True,
                "selected_values": selected_option_values,
                "message": f"成功选择原生select选项: {target_text}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"原生select选择失败: {e}"}


# 使用示例
async def example_usage(browser_context, index: int, target_text: str):
    """使用示例"""
    handler = EnhancedDropdownHandler(browser_context)
    result = await handler.smart_dropdown_selection(index, target_text)
    
    if result["success"]:
        print(f"✅ 下拉框选择成功: {result.get('message', '完成')}")
    else:
        print(f"❌ 下拉框选择失败: {result.get('error', '未知错误')}")
    
    return result 