"""
WebUI 下拉框增强补丁
===========================

这个补丁专门用于增强browser-use的下拉框处理能力：
1. 保持原有<select>元素处理逻辑
2. 添加下拉框内滚动功能，解决viewport限制问题
3. 添加自定义下拉框支持
4. 无缝集成到webui原生工作流

目标：修改browser-use源码中的select_dropdown_option函数
位置：/opt/homebrew/Caskroom/miniconda/base/lib/python3.12/site-packages/browser_use/controller/service.py
"""

import asyncio
import json
import logging
import random
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class WebUIDropdownEnhancementPatch:
    """WebUI下拉框增强补丁类"""
    
    def __init__(self):
        self.original_function = None
        self.patch_applied = False
    
    async def enhanced_select_dropdown_option(
        self,
        index: int,
        text: str,
        browser_context,
        original_function
    ):
        """
        增强版下拉框选项选择函数
        
        保持原有逻辑，但添加滚动支持和自定义下拉框处理
        """
        try:
            # 🔥 步骤1：尝试原有逻辑（处理原生<select>元素）
            logger.info(f"🎯 开始增强下拉框选择: index={index}, text='{text}'")
            
            page = await browser_context.get_current_page()
            selector_map = await browser_context.get_selector_map()
            dom_element = selector_map[index]
            
            # 如果是原生select元素，先尝试原有逻辑
            if dom_element.tag_name == 'select':
                logger.info(f"✅ 检测到原生<select>元素，尝试原有逻辑...")
                
                try:
                    # 🎯 增强原生select处理：添加滚动支持
                    result = await self._enhanced_native_select_with_scroll(
                        index, text, browser_context, dom_element, original_function
                    )
                    
                    if result and hasattr(result, 'extracted_content') and result.extracted_content and "selected option" in result.extracted_content:
                        logger.info(f"✅ 原生select处理成功")
                        return result
                    else:
                        logger.info(f"⚠️ 原生select处理未成功，尝试滚动增强...")
                        
                except Exception as native_error:
                    logger.warning(f"⚠️ 原生select处理失败: {native_error}")
            
            # 🔥 步骤2：自定义下拉框处理 + 滚动增强
            logger.info(f"🔄 尝试自定义下拉框处理和滚动增强...")
            custom_result = await self._handle_custom_dropdown_with_scroll(
                index, text, browser_context, dom_element
            )
            
            if custom_result.get("success"):
                from browser_use.agent.views import ActionResult
                return ActionResult(
                    extracted_content=f"selected option {text} using enhanced method",
                    include_in_memory=True
                )
            
            # 🔥 步骤3：如果都失败，回退到原有函数
            logger.info(f"🔄 回退到原有函数...")
            return await original_function(index, text, browser_context)
            
        except Exception as e:
            logger.error(f"❌ 增强下拉框选择失败: {e}")
            # 最终回退
            try:
                return await original_function(index, text, browser_context)
            except:
                from browser_use.agent.views import ActionResult
                return ActionResult(error=f"下拉框选择失败: {e}")
    
    async def _enhanced_native_select_with_scroll(
        self, 
        index: int, 
        text: str, 
        browser_context, 
        dom_element, 
        original_function
    ):
        """增强的原生select处理，支持滚动查看更多选项"""
        try:
            page = await browser_context.get_current_page()
            
            # 先检查选项是否可见
            options_check = await page.evaluate(f"""
            () => {{
                const select = document.evaluate('{dom_element.xpath}', document, null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                
                if (!select) return {{ found: false }};
                
                const options = Array.from(select.options);
                const targetOption = options.find(opt => 
                    opt.text.includes('{text}') || opt.text.trim() === '{text}'
                );
                
                return {{
                    found: !!targetOption,
                    totalOptions: options.length,
                    targetIndex: targetOption ? targetOption.index : -1,
                    allOptionsVisible: true  // 原生select总是显示所有选项
                }};
            }}
            """)
            
            if options_check.get("found"):
                logger.info(f"✅ 在原生select中找到目标选项，位置: {options_check.get('targetIndex')}")
                
                # 🔥 关键增强：如果选项很多，先滚动到目标位置
                if options_check.get("totalOptions", 0) > 10:
                    await self._scroll_select_to_option(page, dom_element, text)
                
                # 执行原有选择逻辑
                return await original_function(index, text, browser_context)
            else:
                logger.warning(f"⚠️ 在原生select中未找到目标选项: '{text}'")
                return None
                
        except Exception as e:
            logger.error(f"❌ 增强原生select处理失败: {e}")
            return None
    
    async def _scroll_select_to_option(self, page, dom_element, text: str):
        """在原生select中滚动到目标选项"""
        try:
            scroll_js = f"""
            () => {{
                const select = document.evaluate('{dom_element.xpath}', document, null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                
                if (!select) return false;
                
                const options = Array.from(select.options);
                const targetOption = options.find(opt => 
                    opt.text.includes('{text}') || opt.text.trim() === '{text}'
                );
                
                if (targetOption) {{
                    // 设置选中状态，这会自动滚动到该选项
                    select.selectedIndex = targetOption.index;
                    select.scrollTop = targetOption.index * 20; // 估算的选项高度
                    return true;
                }}
                
                return false;
            }}
            """
            
            result = await page.evaluate(scroll_js)
            if result:
                # 给滚动一些时间
                await asyncio.sleep(0.3)
                logger.info(f"✅ 成功滚动原生select到目标选项")
            
        except Exception as e:
            logger.warning(f"⚠️ 原生select滚动失败: {e}")
    
    async def _handle_custom_dropdown_with_scroll(
        self, 
        index: int, 
        text: str, 
        browser_context, 
        dom_element
    ) -> Dict:
        """处理自定义下拉框，支持滚动查看更多选项"""
        try:
            page = await browser_context.get_current_page()
            
            # 🔥 步骤1：尝试展开下拉框
            expand_result = await self._expand_custom_dropdown(page, index)
            if not expand_result.get("success"):
                return {"success": False, "error": "无法展开下拉框"}
            
            # 给展开动画时间
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # 🔥 步骤2：查找目标选项（支持滚动）
            search_result = await self._scroll_search_option_in_dropdown(page, text)
            
            if search_result.get("found"):
                # 🔥 步骤3：选择目标选项
                select_result = await self._select_option_in_dropdown(page, text)
                return select_result
            else:
                return {"success": False, "error": f"在自定义下拉框中未找到选项: '{text}'"}
                
        except Exception as e:
            logger.error(f"❌ 自定义下拉框处理失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _expand_custom_dropdown(self, page, index: int) -> Dict:
        """展开自定义下拉框"""
        try:
            expand_js = """
            (index) => {
                // 查找下拉框触发器
                const triggers = document.querySelectorAll(`
                    .select-trigger, .dropdown-trigger, .jqselect, .custom-select,
                    [class*="select"]:not(select), [role="combobox"], 
                    .dropdown-toggle, .select-wrapper
                `);
                
                let targetTrigger = null;
                
                // 通过索引或其他方式找到对应的触发器
                for (let trigger of triggers) {
                    if (trigger.offsetHeight > 0 && trigger.offsetWidth > 0) {
                        const text = trigger.textContent || trigger.value || '';
                        if (text.includes('请选择') || text.includes('选择') || text.includes('Select')) {
                            targetTrigger = trigger;
                            break;
                        }
                    }
                }
                
                if (targetTrigger) {
                    // 模拟点击展开
                    targetTrigger.click();
                    
                    // 也尝试触发焦点和键盘事件
                    targetTrigger.focus();
                    targetTrigger.dispatchEvent(new KeyboardEvent('keydown', {
                        key: 'ArrowDown',
                        bubbles: true
                    }));
                    
                    return { success: true, triggered: true };
                }
                
                return { success: false, error: "未找到可展开的下拉框" };
            }
            """
            
            result = await page.evaluate(expand_js, index)
            return result
            
        except Exception as e:
            return {"success": False, "error": f"展开失败: {e}"}
    
    async def _scroll_search_option_in_dropdown(self, page, target_text: str) -> Dict:
        """在下拉框中滚动搜索目标选项"""
        try:
            max_scroll_attempts = 10
            
            for attempt in range(max_scroll_attempts):
                # 检查当前可见的选项
                visible_check = await page.evaluate(f"""
                () => {{
                    const targetText = '{target_text}';
                    
                    // 查找选项容器
                    const containers = document.querySelectorAll(`
                        .dropdown-menu, .select-dropdown, .options-container,
                        .jqselect-options, [role="listbox"], .dropdown-options,
                        ul.dropdown, .select-options
                    `);
                    
                    for (let container of containers) {{
                        if (container.offsetHeight > 0) {{
                            const options = container.querySelectorAll(`
                                li, .option, .dropdown-item, .select-option,
                                [role="option"], .item, .choice
                            `);
                            
                            for (let option of options) {{
                                if (option.offsetHeight > 0) {{
                                    const optionText = option.textContent.trim();
                                    if (optionText.includes(targetText) || optionText === targetText) {{
                                        return {{
                                            found: true,
                                            text: optionText,
                                            container: container.className
                                        }};
                                    }}
                                }}
                            }}
                            
                            // 如果没找到，尝试滚动
                            if (container.scrollHeight > container.clientHeight) {{
                                const currentScroll = container.scrollTop;
                                const maxScroll = container.scrollHeight - container.clientHeight;
                                
                                if (currentScroll < maxScroll) {{
                                    container.scrollTop += 100; // 向下滚动100px
                                    return {{
                                        found: false,
                                        scrolled: true,
                                        scrollPosition: container.scrollTop,
                                        maxScroll: maxScroll
                                    }};
                                }}
                            }}
                        }}
                    }}
                    
                    return {{ found: false, scrolled: false }};
                }}
                """)
                
                if visible_check.get("found"):
                    logger.info(f"✅ 找到目标选项: {visible_check.get('text')}")
                    return visible_check
                
                if visible_check.get("scrolled"):
                    logger.info(f"🔄 滚动下拉框中... ({attempt+1}/{max_scroll_attempts})")
                    await asyncio.sleep(0.3)  # 等待滚动完成
                else:
                    break
            
            return {"found": False, "error": "滚动完所有选项后仍未找到目标"}
            
        except Exception as e:
            return {"found": False, "error": f"滚动搜索失败: {e}"}
    
    async def _select_option_in_dropdown(self, page, target_text: str) -> Dict:
        """在下拉框中选择目标选项"""
        try:
            select_js = f"""
            () => {{
                const targetText = '{target_text}';
                
                // 查找并点击目标选项
                const containers = document.querySelectorAll(`
                    .dropdown-menu, .select-dropdown, .options-container,
                    .jqselect-options, [role="listbox"], .dropdown-options
                `);
                
                for (let container of containers) {{
                    if (container.offsetHeight > 0) {{
                        const options = container.querySelectorAll(`
                            li, .option, .dropdown-item, .select-option,
                            [role="option"], .item, .choice
                        `);
                        
                        for (let option of options) {{
                            if (option.offsetHeight > 0) {{
                                const optionText = option.textContent.trim();
                                if (optionText.includes(targetText) || optionText === targetText) {{
                                    option.click();
                                    
                                    // 也触发其他可能需要的事件
                                    option.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    option.dispatchEvent(new Event('select', {{ bubbles: true }}));
                                    
                                    return {{
                                        success: true,
                                        selectedText: optionText
                                    }};
                                }}
                            }}
                        }}
                    }}
                }}
                
                return {{ success: false, error: "未找到可点击的目标选项" }};
            }}
            """
            
            result = await page.evaluate(select_js)
            
            if result.get("success"):
                # 选择后的自然停顿
                await asyncio.sleep(random.uniform(0.3, 0.8))
                logger.info(f"✅ 成功选择选项: {result.get('selectedText')}")
            
            return result
            
        except Exception as e:
            return {"success": False, "error": f"选择失败: {e}"}

    def patch_controller_instance(self, controller):
        """
        在controller实例上应用补丁
        """
        try:
            if not hasattr(controller, 'registry'):
                logger.error("❌ Controller没有registry属性")
                return False
            
            registry = controller.registry
            
            # 查找select_dropdown_option动作
            select_action_key = None
            for action_name in registry.registry.actions:
                if 'select_dropdown_option' in action_name:
                    select_action_key = action_name
                    break
            
            if not select_action_key:
                logger.error("❌ 未找到select_dropdown_option动作")
                return False
            
            # 保存原有函数
            original_action = registry.registry.actions[select_action_key]
            original_function = original_action.function
            self.original_function = original_function
            
            # 创建增强版本的包装函数
            async def enhanced_wrapper(index: int, text: str, browser: 'BrowserContext') -> 'ActionResult':
                return await self.enhanced_select_dropdown_option(
                    index, text, browser, original_function
                )
            
            # 替换函数
            original_action.function = enhanced_wrapper
            registry.registry.actions[select_action_key] = original_action
            
            logger.info(f"✅ 成功在controller实例上应用下拉框增强补丁")
            logger.info(f"🎯 增强功能: 原生select滚动 + 自定义下拉框支持")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 在controller实例上应用补丁失败: {e}")
            return False

# 全局补丁实例
webui_dropdown_patch = WebUIDropdownEnhancementPatch()

def patch_existing_controller(controller):
    """为已存在的controller实例应用补丁"""
    return webui_dropdown_patch.patch_controller_instance(controller) 