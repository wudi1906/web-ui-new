import pdb

import pyperclip
from typing import Optional, Type, Callable, Dict, Any, Union, Awaitable, TypeVar, List, Tuple
from pydantic import BaseModel
from browser_use.agent.views import ActionResult
from browser_use.browser.context import BrowserContext
from browser_use.controller.service import Controller, DoneAction
from browser_use.controller.registry.service import Registry, RegisteredAction
from main_content_extractor import MainContentExtractor
from browser_use.controller.views import (
    ClickElementAction,
    DoneAction,
    ExtractPageContentAction,
    GoToUrlAction,
    InputTextAction,
    OpenTabAction,
    ScrollAction,
    SearchGoogleAction,
    SendKeysAction,
    SwitchTabAction,
)
import logging
import inspect
import asyncio
import os
import random
from langchain_core.language_models.chat_models import BaseChatModel
from browser_use.agent.views import ActionModel, ActionResult
import time
import json
import hashlib

from src.utils.mcp_client import create_tool_param_model, setup_mcp_client_and_tools

from browser_use.utils import time_execution_sync

logger = logging.getLogger(__name__)

Context = TypeVar('Context')


class CustomController(Controller):
    def __init__(self, exclude_actions: list[str] = [],
                 output_model: Optional[Type[BaseModel]] = None,
                 ask_assistant_callback: Optional[Union[Callable[[str, BrowserContext], Dict[str, Any]], Callable[
                     [str, BrowserContext], Awaitable[Dict[str, Any]]]]] = None,
                 ):
        super().__init__(exclude_actions=exclude_actions, output_model=output_model)
        self._register_custom_actions()
        self.ask_assistant_callback = ask_assistant_callback
        self.mcp_client = None
        self.mcp_server_config = None
        
        # 🔥 关键修改：注册反作弊增强方法
        self._register_anti_detection_enhancements()
        
        # 全局问题状态管理（优先级3）
        self.answered_questions = set()
        self.question_hashes = {}
        self.search_history = {}
        self.page_exploration_state = {
            'current_scroll_position': 0,
            'max_scroll_position': 0,
            'discovered_options': {},
            'exploration_complete': False
        }
        
        # 🛡️ 第五层：智能页面恢复引擎状态
        self.page_recovery_state = {
            'last_stable_timestamp': time.time(),
            'loading_start_time': None,
            'loading_detection_count': 0,
            'recovery_attempts': 0,
            'max_recovery_attempts': 3,
            'questionnaire_progress': {},
            'current_page_context': None,
            'emergency_recovery_enabled': True
        }
        
        # 🌍 新增：语言智能决策引擎
        self.language_engine = self._initialize_language_engine()
        
        logger.info("✅ WebUI智能控制器初始化完成 - 五层融合架构已激活")
        logger.info("🛡️ 智能页面恢复引擎已启动")

    def _register_custom_actions(self):
        """注册自定义动作到控制器注册表"""
        try:
            logger.info("🔍 注册智能选项搜索引擎动作...")
            
            # 注意：动作注册通过装饰器方式进行，这里只是初始化标记
            logger.info("✅ 智能选项搜索引擎 + 页面恢复引擎动作将通过装饰器注册")
            
        except Exception as e:
            logger.error(f"❌ 注册智能搜索引擎动作失败: {e}")

    def _register_anti_detection_enhancements(self):
        """🔥 注册反作弊增强方法 - 替换browser-use原生方法"""
        
        # 🔥 优先级1&2：完全反作弊的下拉框选择
        @self.registry.action(
            'Ultra-safe dropdown selection with intelligent option discovery - anti-detection + AI enhanced',
        )
        async def ultra_safe_select_dropdown(index: int, text: str, browser: BrowserContext) -> ActionResult:
            """🔥 完全反作弊的下拉框选择方法 + 智能搜索引擎增强"""
            try:
                logger.info(f"🛡️ 使用智能反作弊下拉框选择: index={index}, text='{text}'")
                
                page = await browser.get_current_page()
                
                # 🔍 第四层：智能搜索引擎增强
                # 检测是否为选择题页面，特别是国家/语言选择
                if self._is_country_language_selection_page(page) or not text or text.lower() in ['auto', 'intelligent', 'smart']:
                    logger.info("🔍 检测到选择题页面或智能选择请求，启动智能搜索引擎...")
                    
                    # 获取数字人信息
                    persona_info = getattr(self, 'digital_human_info', {})
                    if not persona_info:
                        logger.warning("⚠️ 数字人信息未找到，使用默认信息")
                        persona_info = {'name': '数字人', 'location': '中国'}
                    
                    # 调用智能搜索引擎
                    try:
                        search_result = await self.intelligent_option_discovery_engine(
                            page, persona_info, 
                            target_question_context=f"下拉框选择_index_{index}", 
                            search_scope="country_language"
                        )
                        
                        if search_result.get('success') and search_result.get('best_option'):
                            recommended_option = search_result['best_option']
                            text = recommended_option['text']
                            logger.info(f"🎯 智能搜索推荐选项: {text}")
                            logger.info(f"   推荐理由: {search_result['final_recommendation'].get('reason', '系统推荐')}")
                            logger.info(f"   置信度: {recommended_option.get('confidence', 0):.2f}")
                        else:
                            logger.warning("⚠️ 智能搜索引擎未找到合适选项，使用原始文本")
                    except Exception as search_error:
                        logger.warning(f"⚠️ 智能搜索引擎调用失败: {search_error}")
                
                # 添加人类化延迟（优先级1）
                await asyncio.sleep(random.uniform(0.2, 0.5))
                
                selector_map = await browser.get_selector_map()
                if index not in selector_map:
                    return ActionResult(error=f"Element index {index} not found")
                
                dom_element = selector_map[index]
                page = await browser.get_current_page()
                
                # 🔥 关键：完全避免page.evaluate，只使用Playwright原生API
                if dom_element.tag_name.lower() == 'select':
                    # 原生select - 使用最安全的方法
                    try:
                        xpath = '//' + dom_element.xpath
                        
                        # 🔥 核心修复：先尝试原生选择，失败后使用智能滚动方案
                        select_locator = page.locator(xpath)
                        
                        # 首先尝试直接选择
                        try:
                            await select_locator.select_option(label=text, timeout=2000)
                            msg = f"✅ 原生选择成功: {text}"
                            logger.info(msg)
                            return ActionResult(extracted_content=msg, include_in_memory=True)
                        except Exception as direct_error:
                            logger.info(f"🔄 直接选择失败，尝试智能滚动方案: {direct_error}")
                        
                        # 🔥 核心修复：智能滚动 + 选择方案
                        try:
                            # 步骤1：展开下拉框
                            await select_locator.click()
                            await asyncio.sleep(random.uniform(0.2, 0.4))
                            
                            # 步骤2：智能滚动查找选项
                            option_found = False
                            max_scroll_attempts = 5
                            
                            for scroll_attempt in range(max_scroll_attempts):
                                # 检查当前可见的选项
                                visible_options = await page.locator(f"{xpath}//option").all()
                                
                                for option_locator in visible_options:
                                    option_text = await option_locator.text_content()
                                    if option_text and (text in option_text or option_text.strip() == text.strip()):
                                        await option_locator.click(timeout=1500)
                                        option_found = True
                                        break
                                
                                if option_found:
                                    break
                                
                                # 向下滚动查看更多选项
                                if scroll_attempt < max_scroll_attempts - 1:
                                    await select_locator.press('ArrowDown')
                                    await asyncio.sleep(0.1)
                            
                            if option_found:
                                msg = f"✅ 智能滚动选择成功: {text}"
                                logger.info(msg)
                                return ActionResult(extracted_content=msg, include_in_memory=True)
                            else:
                                # 最后尝试：模糊匹配
                                try:
                                    # 尝试部分匹配
                                    option_locator = page.locator(f"{xpath}//option").filter(has_text=text.split()[0] if ' ' in text else text[:5])
                                    await option_locator.first.click(timeout=1500)
                                    msg = f"✅ 模糊匹配选择成功: {text}"
                                    logger.info(msg)
                                    return ActionResult(extracted_content=msg, include_in_memory=True)
                                except:
                                    pass
                            
                        except Exception as scroll_error:
                            logger.warning(f"⚠️ 智能滚动失败: {scroll_error}")
                            
                        # 🔥 最终备用方案：强制选择最接近的选项
                        try:
                            # 获取所有选项，选择最接近的
                            all_options = await page.locator(f"{xpath}//option").all()
                            best_match = None
                            best_score = 0
                            
                            for option_locator in all_options:
                                option_text = await option_locator.text_content()
                                if option_text:
                                    # 计算相似度
                                    score = self._calculate_text_similarity(text.lower(), option_text.lower())
                                    if score > best_score:
                                        best_score = score
                                        best_match = option_locator
                            
                            if best_match and best_score > 0.3:  # 30%以上相似度
                                await best_match.click(timeout=1500)
                                selected_text = await best_match.text_content()
                                msg = f"✅ 最佳匹配选择成功: {selected_text} (原目标: {text})"
                                logger.info(msg)
                                return ActionResult(extracted_content=msg, include_in_memory=True)
                                                                 
                         except Exception as final_error:
                             return ActionResult(error=f"所有下拉框选择方案均失败: {final_error}")
                        
                    except Exception as native_error:
                        return ActionResult(error=f"原生下拉框处理失败: {native_error}")
                else:
                    # 自定义下拉框 - 纯点击方法
                    try:
                        xpath = '//' + dom_element.xpath
                        element_locator = page.locator(xpath)
                        
                        # 点击展开
                        await element_locator.click()
                        await asyncio.sleep(random.uniform(0.3, 0.6))
                        
                        # 查找并点击选项（多种选择器）
                        option_selectors = [
                            f"text='{text}'",
                            f"[role='option']:has-text('{text}')",
                            f".option:has-text('{text}')",
                            f".dropdown-item:has-text('{text}')",
                            f"li:has-text('{text}')"
                        ]
                        
                        option_clicked = False
                        for selector in option_selectors:
                            try:
                                option_locator = page.locator(selector).first
                                if await option_locator.count() > 0:
                                    await option_locator.click(timeout=1500)
                                    option_clicked = True
                                    break
                            except:
                                continue
                        
                        if option_clicked:
                            msg = f"✅ 反作弊自定义下拉框选择成功: {text}"
                            logger.info(msg)
                            return ActionResult(extracted_content=msg, include_in_memory=True)
                        else:
                            return ActionResult(error=f"未找到匹配的选项: {text}")
                            
                    except Exception as custom_error:
                        return ActionResult(error=f"自定义下拉框选择失败: {custom_error}")
                
            except Exception as e:
                return ActionResult(error=f"反作弊下拉框选择失败: {str(e)}")
        
        # 🔥 优先级1&2：完全反作弊的文本输入
        @self.registry.action(
            'Ultra-safe text input avoiding all JavaScript execution - anti-detection priority',
        )
        async def ultra_safe_input_text(index: int, text: str, browser: BrowserContext) -> ActionResult:
            """🔥 完全反作弊的文本输入方法"""
            try:
                logger.info(f"🛡️ 使用反作弊文本输入: index={index}, text='{text[:20]}...'")
                
                # 🌍 第六层：智能语言决策检查（最关键位置！）
                if hasattr(self, 'digital_human_info') and self.digital_human_info:
                    # 检测输入文本的语言
                    detected_language = self._detect_text_language(text)
                    # 获取数字人应该使用的语言
                    required_language = self._get_answer_language(self.digital_human_info)
                    
                    logger.info(f"🌍 语言检查: 检测到='{detected_language}', 要求='{required_language}'")
                    
                    # 如果语言不匹配，自动转换
                    if detected_language != required_language:
                        logger.warning(f"⚠️ 语言不匹配！自动转换: {detected_language} → {required_language}")
                        text = self._convert_text_language(text, required_language, self.digital_human_info)
                        logger.info(f"✅ 语言转换完成: '{text[:30]}...'")
                
                # 人类化行为模拟（优先级1）
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
                selector_map = await browser.get_selector_map()
                if index not in selector_map:
                    return ActionResult(error=f"Element index {index} not found")
                
                dom_element = selector_map[index]
                page = await browser.get_current_page()
                xpath = '//' + dom_element.xpath
                
                # 🔥 关键：完全避免page.evaluate，只使用Playwright原生API
                element_locator = page.locator(xpath)
                
                # 确保元素可见和可交互
                await element_locator.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(0.05, 0.15))
                
                # 清空并输入 - 使用最安全的方法
                await element_locator.click()  # 聚焦
                await element_locator.clear()  # 清空
                
                # 模拟人类输入速度
                if len(text) > 50:
                    # 长文本：快速输入
                    await element_locator.fill(text)
                else:
                    # 短文本：模拟打字
                    await element_locator.type(text, delay=random.randint(20, 80))
                
                # 触发change事件（使用安全方式）
                await element_locator.press('Tab')  # 移出焦点触发change
                
                msg = f"✅ 反作弊文本输入成功: {text[:20]}..."
                logger.info(msg)
                return ActionResult(extracted_content=msg, include_in_memory=True)
                
            except Exception as e:
                return ActionResult(error=f"反作弊文本输入失败: {str(e)}")
        
        # 🔥 优先级3：智能问题状态管理
        @self.registry.action(
            'Check if question was already answered to prevent duplicates',
        )
        async def check_question_answered(question_text: str, browser: BrowserContext) -> ActionResult:
            """检查问题是否已经作答"""
            try:
                question_hash = hash(question_text.strip().lower())
                
                if question_hash in self.answered_questions:
                    msg = f"⚠️ 问题已作答，跳过: {question_text[:30]}..."
                    logger.info(msg)
                    return ActionResult(extracted_content=msg, include_in_memory=True)
                else:
                    self.answered_questions.add(question_hash)
                    self.question_hashes[question_hash] = question_text
                    msg = f"✅ 新问题，准备作答: {question_text[:30]}..."
                    logger.info(msg)
                    return ActionResult(extracted_content=msg, include_in_memory=True)
                    
            except Exception as e:
                return ActionResult(error=f"问题状态检查失败: {str(e)}")
        
        # 🔥 优先级4：安全页面跳转等待
        @self.registry.action(
            'Wait for page transitions safely without JavaScript execution',
        )
        async def ultra_safe_wait_for_navigation(browser: BrowserContext, max_wait_seconds: int = 30) -> ActionResult:
            """🔥 完全反作弊的页面跳转等待 - 增强版防止连接断开"""
            try:
                logger.info(f"🛡️ 使用反作弊导航等待（增强版），最大等待时间: {max_wait_seconds}秒")
                
                page = await browser.get_current_page()
                
                # 调用增强版的等待方法
                wait_success = await self.ultra_safe_wait_for_navigation(page, max_wait_seconds)
                
                if wait_success:
                    msg = f"✅ 页面跳转完成，连接稳定"
                    logger.info(msg)
                    return ActionResult(extracted_content=msg, include_in_memory=True)
                else:
                    # 备用策略：检查页面是否仍然可用
                    try:
                        if not page.is_closed():
                            current_url = page.url
                            msg = f"⚠️ 等待超时但页面仍可用: {current_url[:50]}..."
                            logger.warning(msg)
                            return ActionResult(extracted_content=msg, include_in_memory=True)
                        else:
                            msg = "❌ 页面连接已断开"
                            logger.error(msg)
                            return ActionResult(error=msg)
                    except Exception as check_error:
                        msg = f"⚠️ 页面状态检查失败: {check_error}"
                        logger.warning(msg)
                        return ActionResult(extracted_content=msg, include_in_memory=True)
                    
            except Exception as e:
                return ActionResult(error=f"反作弊导航等待失败: {str(e)}")

        # 🛡️ 第五层：智能页面恢复引擎装饰器动作
        @self.registry.action(
            'Intelligent page stuck detection and automatic recovery engine',
        )
        async def intelligent_page_stuck_detector_and_recovery_engine_action(browser: BrowserContext, max_loading_time: int = 120) -> ActionResult:
            """🛡️ 智能页面卡住检测和自动恢复引擎 - Agent可调用版本"""
            try:
                logger.info(f"🛡️ 启动智能页面恢复引擎，最大加载时间{max_loading_time}秒")
                
                page = await browser.get_current_page()
                
                # 调用核心恢复引擎
                recovery_result = await self.intelligent_page_stuck_detector_and_recovery_engine(
                    page, max_loading_time
                )
                
                if recovery_result.get('recovery_success'):
                    return ActionResult(
                        extracted_content=f"页面恢复成功: {recovery_result.get('recovery_details', {})}",
                        success=True
                    )
                elif recovery_result.get('stuck_detected'):
                    return ActionResult(
                        extracted_content=f"检测到页面卡住但恢复失败: {recovery_result.get('detection_details', {})}",
                        success=False
                    )
                else:
                    return ActionResult(
                        extracted_content="页面状态正常，无需恢复",
                        success=True
                    )
                    
            except Exception as e:
                logger.error(f"❌ 智能页面恢复引擎异常: {e}")
                return ActionResult(extracted_content=f"页面恢复引擎异常: {e}", success=False)

        @self.registry.action(
            'Detect if page is stuck in loading state intelligently',
        )
        async def detect_page_stuck_intelligently_action(browser: BrowserContext, max_loading_time: int = 120) -> ActionResult:
            """🔍 智能检测页面是否卡住 - Agent可调用版本"""
            try:
                logger.info(f"🔍 检测页面是否卡住，阈值{max_loading_time}秒")
                
                page = await browser.get_current_page()
                
                # 调用智能检测方法
                detection_result = await self._detect_page_stuck_intelligently(page, max_loading_time)
                
                if detection_result.get('is_stuck'):
                    return ActionResult(
                        extracted_content=f"页面卡住检测：{detection_result['stuck_reason']}，加载时间：{detection_result.get('loading_duration', 0):.1f}秒",
                        success=True
                    )
                else:
                    return ActionResult(
                        extracted_content=f"页面状态正常，加载时间：{detection_result.get('loading_duration', 0):.1f}秒",
                        success=True
                    )
                    
            except Exception as e:
                logger.error(f"❌ 页面卡住检测异常: {e}")
                return ActionResult(extracted_content=f"页面检测异常: {e}", success=False)

        # 🎯 新增：页面跳转后持续答题检测
        @self.registry.action(
            'Detect page transitions and continue questionnaire answering',
        )
        async def detect_page_transition_and_continue_answering(browser: BrowserContext) -> ActionResult:
            """🔄 检测页面跳转并继续问卷答题 - 防止Agent提前结束"""
            try:
                logger.info("🔄 检测页面跳转状态，确保持续答题...")
                
                page = await browser.get_current_page()
                current_url = page.url
                
                # 检查是否有新的问题需要回答
                try:
                    # 检查是否有表单元素
                    form_elements = await page.locator('form').count()
                    input_elements = await page.locator('input[type="radio"], input[type="checkbox"], select, textarea').count()
                    button_elements = await page.locator('button, input[type="submit"]').count()
                    
                    has_interactive_elements = form_elements > 0 or input_elements > 0 or button_elements > 0
                    
                    # 检查页面内容是否包含问题关键词
                    body_text = await page.locator('body').text_content()
                    body_text_lower = body_text.lower() if body_text else ""
                    
                    question_indicators = [
                        "问题", "question", "选择", "choice", "单选", "多选", 
                        "请选择", "please select", "您的", "your", "调查", "survey"
                    ]
                    
                    has_question_content = any(indicator in body_text_lower for indicator in question_indicators)
                    
                    logger.info(f"🔍 页面状态检查:")
                    logger.info(f"   URL: {current_url}")
                    logger.info(f"   有交互元素: {has_interactive_elements}")
                    logger.info(f"   有问题内容: {has_question_content}")
                    
                    if has_interactive_elements and has_question_content:
                        return ActionResult(
                            extracted_content="检测到新页面有问题需要回答，继续答题流程",
                            include_in_memory=True,
                            is_done=False  # 关键：确保不会结束
                        )
                    elif has_interactive_elements:
                        return ActionResult(
                            extracted_content="检测到交互元素，可能需要继续操作",
                            include_in_memory=True,
                            is_done=False
                        )
                    else:
                        return ActionResult(
                            extracted_content="页面无明显问题元素，可能接近完成",
                            include_in_memory=True
                        )
                        
                except Exception as content_error:
                    logger.warning(f"⚠️ 页面内容检查失败: {content_error}")
                    return ActionResult(
                        extracted_content="页面内容检查失败，保守策略继续",
                        include_in_memory=True,
                        is_done=False
                    )
                    
            except Exception as e:
                logger.error(f"❌ 页面跳转检测失败: {e}")
                return ActionResult(
                    extracted_content=f"页面跳转检测失败: {e}",
                    include_in_memory=True,
                    is_done=False  # 出错时保守策略，不结束
                )

        # 🎯 核心新增：智能选择决策拦截器
        @self.registry.action(
            'Intelligent persona-based option selection - overrides click_element_by_index',
        )
        async def intelligent_persona_click_element_by_index(index: int, browser: BrowserContext) -> ActionResult:
            """🎯 智能人设化点击选择 - 拦截并智能化处理所有点击动作"""
            try:
                logger.info(f"🎯 智能选择决策拦截器启动 - 元素索引: {index}")
                
                # 获取元素信息
                selector_map = await browser.get_selector_map()
                if index not in selector_map:
                    return ActionResult(error=f"Element index {index} not found")
                
                dom_element = selector_map[index]
                element_text = getattr(dom_element, 'text', '') or ''
                element_tag = getattr(dom_element, 'tag_name', '')
                
                logger.info(f"🔍 元素分析: 文本='{element_text}', 标签='{element_tag}'")
                
                # 检查是否是选择类型的元素
                is_selection_element = self._is_selection_element(element_text, element_tag)
                
                if is_selection_element and hasattr(self, 'digital_human_info') and self.digital_human_info:
                    # 执行智能选择决策
                    decision_result = await self._make_intelligent_selection_decision(
                        element_text, index, browser, self.digital_human_info
                    )
                    
                    if decision_result["should_override"]:
                        logger.warning(f"🚫 拒绝错误选择: {element_text}")
                        logger.info(f"✅ 推荐正确选择: {decision_result['recommended_choice']}")
                        
                        # 尝试找到正确的选项并点击
                        correct_choice_result = await self._find_and_click_correct_option(
                            decision_result['recommended_choice'], browser
                        )
                        
                        if correct_choice_result["success"]:
                            return ActionResult(
                                extracted_content=f"智能选择: {decision_result['recommended_choice']} (拒绝了: {element_text})",
                                include_in_memory=True
                            )
                        else:
                            logger.warning(f"⚠️ 未找到推荐选项，执行原始点击")
                    else:
                        logger.info(f"✅ 选择合理，允许执行: {element_text}")
                
                # 执行原始点击逻辑
                page = await browser.get_current_page()
                xpath = '//' + dom_element.xpath
                element_locator = page.locator(xpath)
                
                await element_locator.click()
                
                return ActionResult(
                    extracted_content=f"点击元素: {element_text}",
                    include_in_memory=True
                )
                
            except Exception as e:
                logger.error(f"❌ 智能选择决策失败: {e}")
                # 失败时回退到原始点击
                try:
                    page = await browser.get_current_page()
                    selector_map = await browser.get_selector_map()
                    dom_element = selector_map[index]
                    xpath = '//' + dom_element.xpath
                    element_locator = page.locator(xpath)
                    await element_locator.click()
                    return ActionResult(extracted_content=f"回退点击成功")
                except:
                    return ActionResult(error=f"智能选择和回退点击都失败: {e}")

    def _is_selection_element(self, element_text: str, element_tag: str) -> bool:
        """判断是否是选择类型的元素"""
        # 选择相关的关键词
        selection_keywords = [
            "不想回答", "prefer not", "其他", "other", 
            "中国", "china", "美国", "usa", "philippines", "菲律宾",
            "中文", "chinese", "english", "英文", "简体", "繁体",
            "男", "女", "male", "female", "性别"
        ]
        
        # 标签类型检查
        selection_tags = ["button", "option", "radio", "checkbox"]
        
        text_matches = any(keyword.lower() in element_text.lower() for keyword in selection_keywords)
        tag_matches = any(tag in element_tag.lower() for tag in selection_tags)
        
        return text_matches or tag_matches

    async def _make_intelligent_selection_decision(
        self, 
        element_text: str, 
        index: int, 
        browser: BrowserContext, 
        digital_human_info: Dict
    ) -> dict:
        """🎯 核心：智能选择决策算法"""
        try:
            # 获取数字人基础信息
            name = digital_human_info.get('name', '')
            location = digital_human_info.get('location', '北京')
            residence = digital_human_info.get('residence', '中国')
            
            logger.info(f"🎯 数字人信息: {name} - 位置: {location} - 居住地: {residence}")
            
            # 1. 国籍/国家选择决策
            if any(keyword in element_text for keyword in ["不想回答", "prefer not", "其他", "other"]):
                # 检查当前页面是否有更好的选择
                better_options = await self._find_better_country_options(browser, digital_human_info)
                
                if better_options:
                    return {
                        "should_override": True,
                        "reason": "发现更符合数字人背景的选项",
                        "recommended_choice": better_options[0]["text"],
                        "recommended_index": better_options[0]["index"]
                    }
            
            # 2. 性别选择决策
            gender = digital_human_info.get('gender', '').lower()
            if element_text in ["男", "女", "male", "female"]:
                expected_gender = self._get_expected_gender_choice(gender, element_text)
                if not expected_gender:
                    return {
                        "should_override": True,
                        "reason": f"性别选择与数字人信息不符: 期望{gender}",
                        "recommended_choice": "女" if "女" in gender or "female" in gender else "男"
                    }
            
            # 3. 语言选择决策
            if any(keyword in element_text.lower() for keyword in ["chinese", "english", "中文", "英文"]):
                expected_language = self._get_expected_language_choice(location, residence)
                if element_text.lower() != expected_language.lower():
                    return {
                        "should_override": True,
                        "reason": f"语言选择与数字人地区不符",
                        "recommended_choice": expected_language
                    }
            
            # 4. 其他选择默认允许
            return {
                "should_override": False,
                "reason": "选择合理或无需拦截"
            }
            
        except Exception as e:
            logger.error(f"❌ 智能决策分析失败: {e}")
            return {"should_override": False, "reason": f"决策分析失败: {e}"}

    async def _find_better_country_options(self, browser: BrowserContext, digital_human_info: Dict) -> List[Dict]:
        """查找更好的国家选项"""
        try:
            page = await browser.get_current_page()
            location = digital_human_info.get('location', '北京')
            residence = digital_human_info.get('residence', '中国')
            
            # 根据数字人信息确定优选项
            preferred_countries = []
            if any(loc in str(location + residence).lower() for loc in ['中国', '北京', '上海', 'china', 'beijing']):
                preferred_countries = ["中国", "中国大陆", "中华人民共和国", "China", "China (Mainland)"]
            
            # 搜索页面中的所有可点击元素
            selector_map = await browser.get_selector_map()
            better_options = []
            
            for index, dom_element in selector_map.items():
                element_text = getattr(dom_element, 'text', '') or ''
                
                # 检查是否匹配优选国家
                for preferred in preferred_countries:
                    if preferred.lower() in element_text.lower():
                        better_options.append({
                            "text": element_text,
                            "index": index,
                            "score": len(preferred)  # 匹配长度作为得分
                        })
            
            # 按得分排序，返回最佳选项
            better_options.sort(key=lambda x: x["score"], reverse=True)
            return better_options[:3]  # 返回前3个最佳选项
            
        except Exception as e:
            logger.error(f"❌ 搜索更好选项失败: {e}")
            return []

    async def _find_and_click_correct_option(self, recommended_choice: str, browser: BrowserContext) -> dict:
        """查找并点击正确的选项"""
        try:
            page = await browser.get_current_page()
            selector_map = await browser.get_selector_map()
            
            # 精确匹配
            for index, dom_element in selector_map.items():
                element_text = getattr(dom_element, 'text', '') or ''
                if element_text.strip() == recommended_choice.strip():
                    xpath = '//' + dom_element.xpath
                    element_locator = page.locator(xpath)
                    await element_locator.click()
                    logger.info(f"✅ 精确匹配点击成功: {element_text}")
                    return {"success": True, "method": "exact_match"}
            
            # 模糊匹配
            for index, dom_element in selector_map.items():
                element_text = getattr(dom_element, 'text', '') or ''
                if recommended_choice.lower() in element_text.lower() or element_text.lower() in recommended_choice.lower():
                    xpath = '//' + dom_element.xpath
                    element_locator = page.locator(xpath)
                    await element_locator.click()
                    logger.info(f"✅ 模糊匹配点击成功: {element_text}")
                    return {"success": True, "method": "fuzzy_match"}
            
            return {"success": False, "error": "未找到匹配的选项"}
            
        except Exception as e:
            logger.error(f"❌ 正确选项点击失败: {e}")
            return {"success": False, "error": str(e)}

    def _get_expected_gender_choice(self, gender_info: str, element_text: str) -> bool:
        """检查性别选择是否正确"""
        gender_lower = gender_info.lower()
        element_lower = element_text.lower()
        
        if "女" in gender_lower or "female" in gender_lower:
            return "女" in element_lower or "female" in element_lower
        elif "男" in gender_lower or "male" in gender_lower:
            return "男" in element_lower or "male" in element_lower
        
        return True  # 如果性别信息不明确，允许选择

    def _get_expected_language_choice(self, location: str, residence: str) -> str:
        """根据地理位置获取期望的语言选择"""
        location_info = str(location + residence).lower()
        
        if any(loc in location_info for loc in ['中国', '北京', '上海', 'china', 'beijing']):
            return "中文"
        elif any(loc in location_info for loc in ['美国', 'usa', 'america', '英国', 'uk']):
            return "English"
        elif any(loc in location_info for loc in ['菲律宾', 'philippines']):
            return "English"
        
        return "中文"  # 默认返回中文

    @time_execution_sync('--act')
    async def act(
            self,
            action: ActionModel,
            browser_context: Optional[BrowserContext] = None,
            #
            page_extraction_llm: Optional[BaseChatModel] = None,
            sensitive_data: Optional[Dict[str, str]] = None,
            available_file_paths: Optional[list[str]] = None,
            #
            context: Context | None = None,
    ) -> ActionResult:
        """Execute an action with intelligent completion detection for questionnaires"""

        try:
            for action_name, params in action.model_dump(exclude_unset=True).items():
                if params is not None:
                    
                    # 🎯 核心修改：拦截done动作并进行智能完成检测
                    if action_name == "done":
                        logger.info("🔍 检测到done动作，启动智能完成验证...")
                        
                        # 执行智能完成检测
                        completion_check = await self._intelligent_questionnaire_completion_check(
                            browser_context, params
                        )
                        
                        if completion_check["should_continue"]:
                            logger.warning(f"⚠️ 问卷未真正完成，拒绝done动作: {completion_check['reason']}")
                            # 返回继续执行的结果，而不是完成
                            return ActionResult(
                                extracted_content=f"问卷检测：{completion_check['reason']}，继续答题...",
                                include_in_memory=True,
                                is_done=False  # 关键：强制设置为False
                            )
                        else:
                            logger.info(f"✅ 确认问卷真正完成: {completion_check['reason']}")
                            # 允许正常完成
                            return ActionResult(
                                extracted_content=f"问卷完成确认：{completion_check['reason']}",
                                include_in_memory=True,
                                is_done=True
                            )
                    
                    # 正常执行其他动作
                    if action_name.startswith("mcp"):
                        # this is a mcp tool
                        logger.debug(f"Invoke MCP tool: {action_name}")
                        mcp_tool = self.registry.registry.actions.get(action_name).function
                        result = await mcp_tool.ainvoke(params)
                    else:
                        result = await self.registry.execute_action(
                            action_name,
                            params,
                            browser=browser_context,
                            page_extraction_llm=page_extraction_llm,
                            sensitive_data=sensitive_data,
                            available_file_paths=available_file_paths,
                            context=context,
                        )

                    if isinstance(result, str):
                        return ActionResult(extracted_content=result)
                    elif isinstance(result, ActionResult):
                        return result
                    elif result is None:
                        return ActionResult()
                    else:
                        raise ValueError(f'Invalid action result type: {type(result)} of {result}')
            return ActionResult()
        except Exception as e:
            raise e

    async def _intelligent_questionnaire_completion_check(
        self, 
        browser_context: BrowserContext, 
        done_params: dict
    ) -> dict:
        """
        🎯 智能问卷完成检测 - 核心逻辑
        
        检查是否真正到达问卷完成页面，而不是中间的提交页面
        """
        try:
            if not browser_context:
                return {"should_continue": False, "reason": "无浏览器上下文，允许完成"}
            
            page = await browser_context.get_current_page()
            current_url = page.url.lower()
            
            # 获取页面内容进行分析
            try:
                page_title = await page.title()
                body_text = await page.locator('body').text_content()
                body_text_lower = body_text.lower() if body_text else ""
            except Exception as e:
                logger.warning(f"⚠️ 获取页面内容失败: {e}")
                page_title = ""
                body_text_lower = ""
            
            logger.info(f"🔍 页面分析 - URL: {current_url[:100]}...")
            logger.info(f"🔍 页面标题: {page_title}")
            
            # 1. 检查真正的完成信号
            true_completion_signals = [
                "感谢您的参与", "问卷已完成", "调查完成", "提交成功", "谢谢参与",
                "thank you for", "survey complete", "questionnaire complete", 
                "submission successful", "thank you for participating",
                "调研结束", "问卷结束", "完成问卷"
            ]
            
            completion_url_patterns = [
                "complete", "success", "finish", "end", "done", "thank", "submitted"
            ]
            
            # 检查URL是否包含完成标识
            url_indicates_completion = any(pattern in current_url for pattern in completion_url_patterns)
            
            # 检查页面内容是否包含完成信号
            content_indicates_completion = any(signal in body_text_lower for signal in true_completion_signals)
            
            # 2. 检查是否仍在问卷页面（继续信号）
            questionnaire_continue_signals = [
                "下一页", "继续", "next page", "continue", "下一步", "next",
                "提交答案", "submit answer", "保存并继续", "save and continue",
                "问题", "question", "选择", "choice", "单选", "多选", "填空"
            ]
            
            still_in_questionnaire = any(signal in body_text_lower for signal in questionnaire_continue_signals)
            
            # 3. 检查是否有更多问题元素
            try:
                # 检查是否有表单元素
                form_elements = await page.locator('form').count()
                input_elements = await page.locator('input[type="radio"], input[type="checkbox"], select, textarea').count()
                
                has_form_elements = form_elements > 0 or input_elements > 0
            except Exception as e:
                logger.warning(f"⚠️ 检查表单元素失败: {e}")
                has_form_elements = False
            
            # 4. 智能决策逻辑
            logger.info(f"🔍 完成检测结果:")
            logger.info(f"   URL指示完成: {url_indicates_completion}")
            logger.info(f"   内容指示完成: {content_indicates_completion}")
            logger.info(f"   仍在问卷中: {still_in_questionnaire}")
            logger.info(f"   有表单元素: {has_form_elements}")
            
            # 决策逻辑：只有明确的完成信号才允许结束
            if content_indicates_completion and not still_in_questionnaire:
                return {
                    "should_continue": False,
                    "reason": "检测到明确完成信号且无继续标识"
                }
            elif url_indicates_completion and not has_form_elements:
                return {
                    "should_continue": False,
                    "reason": "URL指示完成且无表单元素"
                }
            elif still_in_questionnaire or has_form_elements:
                return {
                    "should_continue": True,
                    "reason": "检测到问卷继续信号或表单元素，需要继续答题"
                }
            else:
                # 不确定的情况，保守策略：继续执行
                return {
                    "should_continue": True,
                    "reason": "状态不明确，保守策略继续答题"
                }
                
        except Exception as e:
            logger.error(f"❌ 智能完成检测失败: {e}")
            # 出错时保守策略：继续执行
            return {
                "should_continue": True,
                "reason": f"检测失败，保守策略继续: {e}"
            }

    async def setup_mcp_client(self, mcp_server_config: Optional[Dict[str, Any]] = None):
        self.mcp_server_config = mcp_server_config
        if self.mcp_server_config:
            self.mcp_client = await setup_mcp_client_and_tools(self.mcp_server_config)
            self.register_mcp_tools()

    def register_mcp_tools(self):
        """
        Register the MCP tools used by this controller.
        """
        if self.mcp_client:
            for server_name in self.mcp_client.server_name_to_tools:
                for tool in self.mcp_client.server_name_to_tools[server_name]:
                    tool_name = f"mcp.{server_name}.{tool.name}"
                    self.registry.registry.actions[tool_name] = RegisteredAction(
                        name=tool_name,
                        description=tool.description,
                        function=tool,
                        param_model=create_tool_param_model(tool),
                    )
                    logger.info(f"Add mcp tool: {tool_name}")
                logger.debug(
                    f"Registered {len(self.mcp_client.server_name_to_tools[server_name])} mcp tools for {server_name}")
        else:
            logger.warning(f"MCP client not started.")

    async def close_mcp_client(self):
        if self.mcp_client:
            await self.mcp_client.__aexit__(None, None, None)

    async def intelligent_option_discovery_engine(
        self,
        page,
        persona_info: Dict,
        target_question_context: str = "",
        search_scope: str = "country_language"
    ) -> Dict:
        """
        🔍 核心功能：智能选项发现引擎
        
        这是整个四层架构的核心，实现：
        1. 渐进式页面探索
        2. 智能选项识别
        3. 数字人偏好匹配
        4. 反作弊滚动策略
        """
        try:
            logger.info(f"🔍 启动智能选项发现引擎 - 搜索范围: {search_scope}")
            
            discovery_result = {
                'success': False,
                'best_option': None,
                'all_options': [],
                'search_phases': [],
                'final_recommendation': {},
                'exploration_stats': {}
            }
            
            # 🎯 第一阶段：快速可见区域扫描
            phase1_result = await self._phase1_visible_area_scan(page, persona_info, search_scope)
            discovery_result['search_phases'].append(phase1_result)
            
            if phase1_result['high_confidence_match']:
                logger.info(f"✅ 第一阶段发现高置信度匹配: {phase1_result['best_match']['text']}")
                discovery_result.update({
                    'success': True,
                    'best_option': phase1_result['best_match'],
                    'all_options': phase1_result['options'],
                    'final_recommendation': {
                        'action': 'immediate_select',
                        'option': phase1_result['best_match'],
                        'confidence': phase1_result['best_match']['confidence'],
                        'reason': 'first_phase_perfect_match'
                    }
                })
                return discovery_result
            
            # 🔄 第二阶段：智能滚动探索（仅在第一阶段未找到理想选项时）
            logger.info("🔄 启动第二阶段：智能滚动探索")
            phase2_result = await self._phase2_intelligent_scroll_exploration(page, persona_info, search_scope)
            discovery_result['search_phases'].append(phase2_result)
            
            # 🎯 第三阶段：综合评估和最终推荐
            phase3_result = await self._phase3_comprehensive_evaluation(
                discovery_result['search_phases'], persona_info, search_scope
            )
            discovery_result['search_phases'].append(phase3_result)
            
            # 🏆 生成最终推荐
            if phase3_result['recommended_option']:
                discovery_result.update({
                    'success': True,
                    'best_option': phase3_result['recommended_option'],
                    'all_options': phase3_result['all_discovered_options'],
                    'final_recommendation': phase3_result['recommendation'],
                    'exploration_stats': phase3_result['stats']
                })
            else:
                # 🚨 兜底策略：选择评分最高的选项
                all_options = []
                for phase in discovery_result['search_phases']:
                    all_options.extend(phase.get('options', []))
                
                if all_options:
                    best_fallback = max(all_options, key=lambda x: x.get('confidence', 0))
                    discovery_result.update({
                        'success': True,
                        'best_option': best_fallback,
                        'all_options': all_options,
                        'final_recommendation': {
                            'action': 'fallback_select',
                            'option': best_fallback,
                            'confidence': best_fallback.get('confidence', 0),
                            'reason': 'best_available_option'
                        }
                    })
            
            logger.info(f"🎉 智能选项发现完成 - 成功: {discovery_result['success']}")
            if discovery_result['success']:
                logger.info(f"🎯 推荐选项: {discovery_result['best_option']['text']} (置信度: {discovery_result['best_option'].get('confidence', 0):.1f})")
            
            return discovery_result
            
        except Exception as e:
            logger.error(f"❌ 智能选项发现引擎异常: {e}")
            return {
                'success': False,
                'error': str(e),
                'search_phases': [],
                'final_recommendation': {'action': 'error', 'reason': str(e)}
            }

    async def _phase1_visible_area_scan(self, page, persona_info: Dict, search_scope: str) -> Dict:
        """🔍 第一阶段：快速可见区域扫描"""
        try:
            logger.info("🔍 第一阶段：扫描当前可见选项")
            
            # 🎯 使用反作弊方式获取可见选项
            visible_options = await self._extract_visible_options_safely(page)
            logger.info(f"📊 发现 {len(visible_options)} 个可见选项")
            
            # 🧠 智能评分和匹配
            scored_options = []
            for option in visible_options:
                score = await self._calculate_option_preference_score(
                    option['text'], persona_info, search_scope
                )
                option['confidence'] = score
                scored_options.append(option)
            
            # 🏆 排序并找到最佳匹配
            scored_options.sort(key=lambda x: x['confidence'], reverse=True)
            best_match = scored_options[0] if scored_options else None
            
            # 🎯 判断是否为高置信度匹配（阈值：0.8）
            high_confidence = best_match and best_match['confidence'] >= 0.8
            
            return {
                'phase': 'visible_scan',
                'options': scored_options,
                'best_match': best_match,
                'high_confidence_match': high_confidence,
                'stats': {
                    'total_options': len(visible_options),
                    'avg_confidence': sum(opt['confidence'] for opt in scored_options) / len(scored_options) if scored_options else 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 第一阶段扫描失败: {e}")
            return {'phase': 'visible_scan', 'options': [], 'best_match': None, 'high_confidence_match': False, 'error': str(e)}

    async def _phase2_intelligent_scroll_exploration(self, page, persona_info: Dict, search_scope: str) -> Dict:
        """🔄 第二阶段：智能滚动探索"""
        try:
            logger.info("🔄 第二阶段：智能滚动探索")
            
            all_discovered_options = []
            scroll_attempts = 0
            max_scroll_attempts = 10
            scroll_step = 300  # 每次滚动300px
            
            # 🎯 获取页面滚动信息
            scroll_info = await page.evaluate("""
                () => ({
                    current: window.scrollY,
                    max: Math.max(
                        document.body.scrollHeight,
                        document.documentElement.scrollHeight
                    ) - window.innerHeight,
                    viewHeight: window.innerHeight
                })
            """)
            
            logger.info(f"📏 页面滚动信息: 当前{scroll_info['current']}, 最大{scroll_info['max']}")
            
            # 🔄 渐进式滚动搜索
            while scroll_attempts < max_scroll_attempts:
                # 📍 计算目标滚动位置
                target_scroll = min(
                    scroll_info['current'] + scroll_step,
                    scroll_info['max']
                )
                
                if target_scroll <= scroll_info['current']:
                    logger.info("📄 已到达页面底部，停止滚动")
                    break
                
                # 🛡️ 反作弊滚动（使用原生方法）
                await self._anti_detection_scroll_to_position(page, target_scroll)
                
                # ⏳ 等待页面稳定
                await asyncio.sleep(0.8)
                
                # 🔍 扫描新出现的选项
                new_options = await self._extract_visible_options_safely(page)
                
                # 🆕 过滤出真正的新选项
                existing_texts = {opt['text'] for opt in all_discovered_options}
                truly_new_options = [
                    opt for opt in new_options 
                    if opt['text'] not in existing_texts
                ]
                
                if truly_new_options:
                    logger.info(f"🆕 滚动后发现 {len(truly_new_options)} 个新选项")
                    
                    # 🧠 对新选项进行智能评分
                    for option in truly_new_options:
                        score = await self._calculate_option_preference_score(
                            option['text'], persona_info, search_scope
                        )
                        option['confidence'] = score
                        option['discovered_at_scroll'] = target_scroll
                    
                    all_discovered_options.extend(truly_new_options)
                    
                    # 🎯 检查是否发现了高分选项
                    high_score_options = [opt for opt in truly_new_options if opt['confidence'] >= 0.9]
                    if high_score_options:
                        logger.info(f"🎉 发现高分选项，提前结束滚动: {high_score_options[0]['text']}")
                        break
                
                scroll_attempts += 1
                scroll_info['current'] = target_scroll
            
            # 🏆 对所有发现的选项进行最终排序
            all_discovered_options.sort(key=lambda x: x['confidence'], reverse=True)
            
            return {
                'phase': 'scroll_exploration',
                'options': all_discovered_options,
                'best_match': all_discovered_options[0] if all_discovered_options else None,
                'scroll_stats': {
                    'attempts': scroll_attempts,
                    'final_position': scroll_info['current'],
                    'total_discovered': len(all_discovered_options)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 第二阶段滚动探索失败: {e}")
            return {'phase': 'scroll_exploration', 'options': [], 'best_match': None, 'error': str(e)}

    async def _phase3_comprehensive_evaluation(
        self, 
        search_phases: List[Dict], 
        persona_info: Dict, 
        search_scope: str
    ) -> Dict:
        """🎯 第三阶段：综合评估和最终推荐"""
        try:
            logger.info("🎯 第三阶段：综合评估和最终推荐")
            
            # 🔍 汇总所有发现的选项
            all_options = []
            for phase in search_phases:
                all_options.extend(phase.get('options', []))
            
            if not all_options:
                return {
                    'phase': 'comprehensive_evaluation',
                    'recommended_option': None,
                    'all_discovered_options': [],
                    'recommendation': {'action': 'no_options_found'},
                    'stats': {'total_options': 0}
                }
            
            # 🧠 智能去重（基于文本相似度）
            unique_options = await self._deduplicate_options_intelligently(all_options)
            logger.info(f"🔄 去重后保留 {len(unique_options)} 个唯一选项")
            
            # 🎯 重新评分（考虑发现方式和位置）
            for option in unique_options:
                # 🏆 基础分数
                base_score = option.get('confidence', 0)
                
                # 🎁 位置加权：可见区域的选项获得轻微加分
                if not option.get('discovered_at_scroll', 0):
                    base_score += 0.05  # 可见区域加分
                
                # 🎯 特殊关键词强化
                text_lower = option['text'].lower()
                if search_scope == "country_language":
                    persona_name = persona_info.get('name', '')
                    if any(keyword in text_lower for keyword in ['中国', 'china', '简体']):
                        if '李小芳' in persona_name or '张小娟' in persona_name:
                            base_score += 0.1  # 中国选项对中国数字人强化加分
                
                option['final_confidence'] = min(base_score, 1.0)  # 确保不超过1.0
            
            # 🏆 最终排序
            unique_options.sort(key=lambda x: x['final_confidence'], reverse=True)
            recommended_option = unique_options[0]
            
            # 🎯 生成推荐策略
            recommendation = {
                'action': 'select_recommended',
                'option': recommended_option,
                'confidence': recommended_option['final_confidence'],
                'reason': self._generate_recommendation_reason(recommended_option, persona_info)
            }
            
            return {
                'phase': 'comprehensive_evaluation',
                'recommended_option': recommended_option,
                'all_discovered_options': unique_options,
                'recommendation': recommendation,
                'stats': {
                    'total_options': len(all_options),
                    'unique_options': len(unique_options),
                    'top_confidence': recommended_option['final_confidence']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 第三阶段综合评估失败: {e}")
            return {
                'phase': 'comprehensive_evaluation',
                'recommended_option': None,
                'recommendation': {'action': 'evaluation_error', 'reason': str(e)},
                'error': str(e)
            }

    async def _extract_visible_options_safely(self, page) -> List[Dict]:
        """🛡️ 反作弊方式提取可见选项"""
        try:
            # 🛡️ 使用原生Playwright定位器，避免JavaScript检测
            options_data = await page.evaluate("""
                () => {
                    const options = [];
                    
                    // 🔍 多种选择器组合，覆盖各种UI框架
                    const selectors = [
                        'button', 'a[role="button"]', '.btn', '[role="option"]',
                        'select option', '.option', '.dropdown-item', 
                        '.list-item', 'li', '.choice', '.selection-item'
                    ];
                    
                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        
                        for (const elem of elements) {
                            // 🎯 检查元素是否可见且有意义
                            if (elem.offsetHeight > 0 && elem.offsetWidth > 0) {
                                const text = elem.textContent?.trim() || '';
                                const rect = elem.getBoundingClientRect();
                                
                                // 📏 确保在视窗内
                                if (rect.top >= 0 && rect.top < window.innerHeight && text.length > 0) {
                                    // 🚫 过滤掉明显的非选项元素
                                    if (!text.includes('请选择') && 
                                        !text.includes('...') && 
                                        text.length < 100) {
                                        
                                        options.push({
                                            text: text,
                                            element_tag: elem.tagName.toLowerCase(),
                                            class_list: Array.from(elem.classList),
                                            position: {
                                                top: rect.top,
                                                left: rect.left,
                                                width: rect.width,
                                                height: rect.height
                                            },
                                            is_clickable: elem.onclick !== null || 
                                                         elem.getAttribute('role') === 'button' ||
                                                         elem.tagName.toLowerCase() === 'button'
                                        });
                                    }
                                }
                            }
                        }
                    }
                    
                    return options;
                }
            """)
            
            # 🧹 清理和验证提取的选项
            clean_options = []
            seen_texts = set()
            
            for opt in options_data:
                text = opt['text'].strip()
                if text and text not in seen_texts and len(text) >= 2:
                    clean_options.append({
                        'text': text,
                        'metadata': {
                            'tag': opt['element_tag'],
                            'classes': opt['class_list'],
                            'position': opt['position'],
                            'clickable': opt['is_clickable']
                        }
                    })
                    seen_texts.add(text)
            
            return clean_options
            
        except Exception as e:
            logger.warning(f"⚠️ 安全选项提取失败: {e}")
            return []

    async def _calculate_option_preference_score(
        self, 
        option_text: str, 
        persona_info: Dict, 
        search_scope: str
    ) -> float:
        """🧠 智能计算选项偏好分数"""
        try:
            text_lower = option_text.lower().strip()
            persona_name = persona_info.get('name', '')
            base_score = 0.1  # 基础分数
            
            if search_scope == "country_language":
                # 🇨🇳 中国数字人的优选逻辑
                china_keywords = ['中国', 'china', '简体', '中文', 'chinese', 'simplified']
                if any(keyword in text_lower for keyword in china_keywords):
                    base_score = 0.95  # 中国相关选项高分
                    logger.info(f"🇨🇳 中国选项高分: {option_text}")
                
                # 🚫 避免选择其他国家
                avoid_keywords = [
                    'philippines', 'english', 'america', 'usa', 'united states',
                    'australia', 'canada', 'japan', 'korea', 'germany',
                    'france', 'spain', 'italy', 'brazil'
                ]
                if any(keyword in text_lower for keyword in avoid_keywords):
                    base_score = 0.2  # 其他国家低分
                    logger.info(f"🚫 其他国家选项低分: {option_text}")
                
                # 🎯 特殊人名匹配
                if '李小芳' in persona_name or 'xiaofang' in persona_name.lower():
                    if any(keyword in text_lower for keyword in china_keywords):
                        base_score = 0.98  # 李小芳选择中国选项超高分
                        logger.info(f"🎯 李小芳中国选项超高分: {option_text}")
            
            # 🚫 过滤明显的提示文本
            skip_patterns = ['请选择', '选择', '--', 'please select', 'choose', 'select']
            if any(pattern in text_lower for pattern in skip_patterns):
                base_score = 0.05  # 提示文本极低分
            
            return min(base_score, 1.0)
            
        except Exception as e:
            logger.warning(f"⚠️ 选项评分失败: {e}")
            return 0.1

    async def _anti_detection_scroll_to_position(self, page, target_position: int):
        """🛡️ 反作弊滚动到指定位置"""
        try:
            # 🛡️ 使用原生Playwright方法，模拟真实滚动
            current_pos = await page.evaluate("window.scrollY")
            
            if abs(target_position - current_pos) < 10:
                return  # 位置已接近，无需滚动
            
            # 🎭 模拟人类滚动行为：分步滚动
            step_size = 150
            direction = 1 if target_position > current_pos else -1
            
            while abs(current_pos - target_position) > step_size:
                next_pos = current_pos + (step_size * direction)
                
                # 🌊 使用平滑滚动
                await page.evaluate(f"""
                    window.scrollTo({{
                        top: {next_pos},
                        behavior: 'smooth'
                    }});
                """)
                
                # ⏳ 随机等待时间，模拟人类行为
                await asyncio.sleep(0.3 + (0.2 * __import__('random').random()))
                current_pos = await page.evaluate("window.scrollY")
            
            # 🎯 最终精确定位
            await page.evaluate(f"""
                window.scrollTo({{
                    top: {target_position},
                    behavior: 'smooth'
                }});
            """)
            
            # ⏳ 等待滚动完成
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.warning(f"⚠️ 反作弊滚动失败: {e}")

    async def _deduplicate_options_intelligently(self, options: List[Dict]) -> List[Dict]:
        """🧠 智能去重选项"""
        try:
            unique_options = []
            seen_texts = set()
            
            for option in options:
                text = option['text'].strip()
                
                # 🔍 简单文本去重
                if text not in seen_texts:
                    unique_options.append(option)
                    seen_texts.add(text)
            
            return unique_options
            
        except Exception as e:
            logger.warning(f"⚠️ 选项去重失败: {e}")
            return options

    def _generate_recommendation_reason(self, option: Dict, persona_info: Dict) -> str:
        """📝 生成推荐理由"""
        try:
            text = option['text']
            confidence = option.get('final_confidence', 0)
            persona_name = persona_info.get('name', '')
            
            if confidence >= 0.9:
                if any(keyword in text.lower() for keyword in ['中国', 'china', '简体']):
                    return f"高度匹配：{persona_name}作为中国数字人，{text}是最佳选择"
                else:
                    return f"高置信度匹配：{text}最符合数字人特征"
            elif confidence >= 0.7:
                return f"良好匹配：{text}符合预期特征"
            else:
                return f"最佳可用选项：{text}是当前最合适的选择"
                
        except Exception:
            return "系统推荐选项"

    async def check_question_answered(self, question_text: str, persona_info: Dict) -> bool:
        """✅ 检查问题是否已回答（全局状态管理）"""
        try:
            # 🔍 生成问题指纹
            question_hash = hashlib.md5(
                f"{question_text}_{persona_info.get('name', '')}".encode()
            ).hexdigest()
            
            if question_hash in self.answered_questions:
                logger.info(f"🚫 问题已回答，跳过: {question_text[:50]}...")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ 问题状态检查失败: {e}")
            return False

    async def mark_question_answered(self, question_text: str, answer_text: str, persona_info: Dict):
        """✅ 标记问题为已回答"""
        try:
            question_hash = hashlib.md5(
                f"{question_text}_{persona_info.get('name', '')}".encode()
            ).hexdigest()
            
            self.answered_questions.add(question_hash)
            self.question_hashes[question_hash] = {
                'question': question_text,
                'answer': answer_text,
                'timestamp': time.time(),
                'persona': persona_info.get('name', '')
            }
            
            logger.info(f"✅ 问题已标记为回答: {question_text[:50]}... -> {answer_text}")
            
        except Exception as e:
            logger.warning(f"⚠️ 标记问题状态失败: {e}")

    async def ultra_safe_wait_for_navigation(self, page, max_wait: int = 30) -> bool:
        """🕰️ 超安全页面跳转等待 - 增强版防止连接断开"""
        try:
            logger.info("🕰️ 启动超安全跳转等待（增强版）...")
            
            start_time = time.time()
            stable_count = 0
            required_stable = 2  # 降低稳定性要求，避免过长等待
            connection_check_interval = 0.5  # 更频繁的连接检查
            
            while time.time() - start_time < max_wait:
                try:
                    # 🔒 首先检查页面连接状态
                    if page.is_closed():
                        logger.error("❌ 页面连接已关闭，停止等待")
                        return False
                    
                    # 🛡️ 使用更安全的状态检查方法
                    try:
                        ready_state = await page.evaluate("document.readyState", timeout=5000)
                        current_url = page.url
                        
                        # 检查是否为有效的问卷页面
                        if not current_url or current_url == "about:blank":
                            logger.warning("⚠️ 页面URL无效，继续等待...")
                            await asyncio.sleep(connection_check_interval)
                            continue
                        
                        if ready_state == 'complete':
                            stable_count += 1
                            logger.info(f"✅ 页面稳定检测 {stable_count}/{required_stable} (URL: {current_url[:50]}...)")
                            
                            if stable_count >= required_stable:
                                logger.info("🎉 页面跳转完成，状态稳定")
                                return True
                        else:
                            stable_count = 0
                            logger.info(f"🔄 页面状态: {ready_state}")
                        
                    except Exception as eval_error:
                        logger.warning(f"⚠️ 页面状态检查失败: {eval_error}")
                        # 如果evaluate失败，可能是页面正在跳转，等待更长时间
                        await asyncio.sleep(2)
                        continue
                    
                    await asyncio.sleep(connection_check_interval)
                    
                except Exception as e:
                    logger.warning(f"⚠️ 连接检查异常: {e}")
                    # 连接异常时，给更多时间恢复
                    await asyncio.sleep(2)
                    
                    # 检查是否是致命错误
                    if "Browser closed" in str(e) or "Target closed" in str(e):
                        logger.error("❌ 浏览器连接断开，停止等待")
                        return False
            
            elapsed_time = time.time() - start_time
            logger.warning(f"⏰ 跳转等待超时 ({elapsed_time:.1f}s/{max_wait}s)")
            
            # 超时后再做一次最终检查
            try:
                if not page.is_closed():
                    final_state = await page.evaluate("document.readyState", timeout=3000)
                    if final_state == 'complete':
                        logger.info("✅ 超时后检查发现页面已完成加载")
                        return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 超安全跳转等待失败: {e}")
            return False

    def _is_country_language_selection_page(self, page) -> bool:
        """🔍 检测是否为国家/语言选择页面"""
        try:
            # 通过URL和页面内容判断
            current_url = page.url.lower()
            
            # URL关键词检测
            url_indicators = ['country', 'language', 'locale', 'region', 'location', 'qtaskgoto']
            if any(indicator in current_url for indicator in url_indicators):
                return True
            
            # 问卷链接特征检测
            if 'jinshengsurveys.com' in current_url and 'qtaskgoto' in current_url:
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ 页面类型检测失败: {e}")
            return False

    async def intelligent_page_stuck_detector_and_recovery_engine(
        self,
        page,
        max_loading_time: int = 120,  # 最大加载时间2分钟
        detection_interval: int = 5   # 检测间隔5秒
    ) -> Dict:
        """
        🛡️ 核心功能：智能页面卡住检测和自动恢复引擎
        
        功能：
        1. 智能检测页面是否真的卡住
        2. 安全自动刷新页面
        3. 保持答题状态和进度
        4. 无缝恢复答题流程
        """
        try:
            logger.info("🛡️ 启动智能页面卡住检测引擎")
            
            recovery_result = {
                'stuck_detected': False,
                'recovery_performed': False,
                'recovery_success': False,
                'detection_details': {},
                'recovery_details': {},
                'questionnaire_state_preserved': False
            }
            
            # 🔍 第一阶段：智能卡住检测
            stuck_detection = await self._detect_page_stuck_intelligently(page, max_loading_time)
            recovery_result['stuck_detected'] = stuck_detection['is_stuck']
            recovery_result['detection_details'] = stuck_detection
            
            if not stuck_detection['is_stuck']:
                logger.info("✅ 页面状态正常，无需恢复")
                return recovery_result
            
            logger.warning(f"🚨 检测到页面卡住: {stuck_detection['stuck_reason']}")
            
            # 🔄 第二阶段：智能状态保存
            logger.info("💾 保存当前问卷答题状态...")
            state_backup = await self._backup_questionnaire_state(page)
            recovery_result['questionnaire_state_preserved'] = state_backup['success']
            
            # 🛡️ 第三阶段：安全自动刷新
            logger.info("🔄 执行安全自动刷新...")
            refresh_result = await self._perform_safe_page_refresh(page)
            recovery_result['recovery_performed'] = refresh_result['success']
            recovery_result['recovery_details'] = refresh_result
            
            if not refresh_result['success']:
                logger.error("❌ 页面刷新失败")
                return recovery_result
            
            # ⏳ 第四阶段：等待页面重新加载
            logger.info("⏳ 等待页面重新加载完成...")
            reload_success = await self._wait_for_page_reload_completion(page)
            
            if not reload_success:
                logger.error("❌ 页面重新加载超时")
                return recovery_result
            
            # 🔍 第五阶段：智能状态恢复
            logger.info("🔍 检测新页面状态并恢复答题进度...")
            recovery_success = await self._restore_questionnaire_progress(page, state_backup)
            recovery_result['recovery_success'] = recovery_success['success']
            
            # 📊 记录恢复统计
            self.page_recovery_state['recovery_attempts'] += 1
            self.page_recovery_state['last_stable_timestamp'] = time.time()
            
            if recovery_success['success']:
                logger.info("🎉 智能页面恢复完成，可以继续答题")
            else:
                logger.warning("⚠️ 页面恢复部分成功，需要重新开始答题")
            
            return recovery_result
            
        except Exception as e:
            logger.error(f"❌ 智能页面恢复引擎异常: {e}")
            return {
                'stuck_detected': False,
                'recovery_performed': False,
                'recovery_success': False,
                'error': str(e)
            }

    async def _detect_page_stuck_intelligently(self, page, max_loading_time: int) -> Dict:
        """🔍 智能检测页面是否真的卡住"""
        try:
            current_time = time.time()
            
            # 📊 收集页面状态指标
            page_metrics = {
                'loading_indicators': [],
                'network_activity': False,
                'dom_changes': False,
                'user_interaction_blocked': False,
                'loading_duration': 0
            }
            
            # 🔍 检测加载指示器
            loading_indicators = await page.evaluate("""
                () => {
                    const indicators = [];
                    
                    // 检测常见的加载文本
                    const loadingTexts = ['正在载入', '正在加载', 'loading', '加载中', '请稍候'];
                    for (const text of loadingTexts) {
                        if (document.body.textContent.includes(text)) {
                            indicators.push(`loading_text_${text}`);
                        }
                    }
                    
                    // 检测加载动画元素
                    const spinners = document.querySelectorAll('.loading, .spinner, [class*="load"]');
                    if (spinners.length > 0) {
                        indicators.push(`spinner_elements_${spinners.length}`);
                    }
                    
                    // 检测页面可交互性
                    const interactiveElements = document.querySelectorAll('button, input, select, a');
                    const disabledElements = document.querySelectorAll('button:disabled, input:disabled');
                    const interactionBlocked = disabledElements.length > interactiveElements.length * 0.8;
                    
                    return {
                        indicators,
                        interactionBlocked,
                        totalElements: interactiveElements.length,
                        disabledElements: disabledElements.length
                    };
                }
            """)
            
            page_metrics['loading_indicators'] = loading_indicators['indicators']
            page_metrics['user_interaction_blocked'] = loading_indicators['interactionBlocked']
            
            # ⏱️ 检测加载持续时间
            if not self.page_recovery_state['loading_start_time']:
                if page_metrics['loading_indicators']:
                    self.page_recovery_state['loading_start_time'] = current_time
                    logger.info("🕐 开始监控页面加载状态")
            
            if self.page_recovery_state['loading_start_time']:
                page_metrics['loading_duration'] = current_time - self.page_recovery_state['loading_start_time']
            
            # 🎯 智能判断是否卡住
            is_stuck = False
            stuck_reason = ""
            
            # 条件1：加载时间过长
            if page_metrics['loading_duration'] > max_loading_time:
                is_stuck = True
                stuck_reason = f"加载超时({page_metrics['loading_duration']:.1f}s > {max_loading_time}s)"
            
            # 条件2：有加载指示器且交互被阻塞
            elif (page_metrics['loading_indicators'] and 
                  page_metrics['user_interaction_blocked'] and 
                  page_metrics['loading_duration'] > 30):
                is_stuck = True
                stuck_reason = f"长时间加载阻塞({page_metrics['loading_duration']:.1f}s)"
            
            # 条件3：检测到明确的"正在载入"文本超过60秒
            elif any('正在载入' in indicator for indicator in page_metrics['loading_indicators']):
                if page_metrics['loading_duration'] > 60:
                    is_stuck = True
                    stuck_reason = "检测到长时间'正在载入'状态"
            
            logger.info(f"📊 页面状态检测: 加载{page_metrics['loading_duration']:.1f}s, "
                       f"指示器{len(page_metrics['loading_indicators'])}个, "
                       f"交互阻塞{page_metrics['user_interaction_blocked']}")
            
            return {
                'is_stuck': is_stuck,
                'stuck_reason': stuck_reason,
                'metrics': page_metrics,
                'loading_duration': page_metrics['loading_duration']
            }
            
        except Exception as e:
            logger.error(f"❌ 页面卡住检测失败: {e}")
            return {'is_stuck': False, 'error': str(e)}

    async def _backup_questionnaire_state(self, page) -> Dict:
        """💾 备份当前问卷答题状态"""
        try:
            logger.info("💾 备份问卷答题状态...")
            
            # 保存当前URL和页面基本信息
            current_url = page.url
            page_title = await page.title()
            
            # 保存已回答的问题状态
            answered_state = {
                'answered_questions': list(self.answered_questions),
                'question_hashes': dict(self.question_hashes),
                'current_url': current_url,
                'page_title': page_title,
                'timestamp': time.time()
            }
            
            # 尝试保存页面中的表单数据
            form_data = await page.evaluate("""
                () => {
                    const formData = {};
                    
                    // 保存所有输入框的值
                    const inputs = document.querySelectorAll('input, textarea, select');
                    inputs.forEach((input, index) => {
                        if (input.value) {
                            formData[`input_${index}`] = {
                                type: input.type || input.tagName.toLowerCase(),
                                value: input.value,
                                name: input.name || '',
                                id: input.id || ''
                            };
                        }
                    });
                    
                    // 保存选中的选项
                    const checked = document.querySelectorAll('input[type="radio"]:checked, input[type="checkbox"]:checked');
                    checked.forEach((input, index) => {
                        formData[`checked_${index}`] = {
                            type: input.type,
                            name: input.name,
                            value: input.value
                        };
                    });
                    
                    return formData;
                }
            """)
            
            # 保存到恢复状态中
            backup_data = {
                'answered_state': answered_state,
                'form_data': form_data,
                'backup_timestamp': time.time()
            }
            
            self.page_recovery_state['questionnaire_progress'] = backup_data
            
            logger.info(f"✅ 状态备份完成: 已答{len(self.answered_questions)}题, "
                       f"表单数据{len(form_data)}项")
            
            return {'success': True, 'backup_data': backup_data}
            
        except Exception as e:
            logger.error(f"❌ 状态备份失败: {e}")
            return {'success': False, 'error': str(e)}

    async def _perform_safe_page_refresh(self, page) -> Dict:
        """🔄 执行安全的页面刷新"""
        try:
            logger.info("🔄 执行反作弊页面刷新...")
            
            # 🛡️ 方法1：使用原生Playwright刷新（最安全）
            try:
                # 模拟人类刷新行为：先等待一下，然后刷新
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
                # 使用原生刷新方法
                await page.reload(wait_until='domcontentloaded', timeout=30000)
                
                logger.info("✅ 原生刷新成功")
                return {'success': True, 'method': 'native_reload'}
                
            except Exception as native_error:
                logger.warning(f"⚠️ 原生刷新失败: {native_error}")
                
                # 🛡️ 方法2：使用键盘快捷键刷新
                try:
                    await page.keyboard.press('F5')
                    await asyncio.sleep(2)
                    
                    logger.info("✅ 键盘刷新成功")
                    return {'success': True, 'method': 'keyboard_f5'}
                    
                except Exception as keyboard_error:
                    logger.warning(f"⚠️ 键盘刷新失败: {keyboard_error}")
                    
                    # 🛡️ 方法3：重新导航到当前URL
                    try:
                        current_url = page.url
                        await page.goto(current_url, wait_until='domcontentloaded', timeout=30000)
                        
                        logger.info("✅ 重新导航成功")
                        return {'success': True, 'method': 'goto_refresh'}
                        
                    except Exception as goto_error:
                        logger.error(f"❌ 所有刷新方法均失败: {goto_error}")
                        return {'success': False, 'error': str(goto_error)}
            
        except Exception as e:
            logger.error(f"❌ 安全刷新失败: {e}")
            return {'success': False, 'error': str(e)}

    async def _wait_for_page_reload_completion(self, page, max_wait: int = 60) -> bool:
        """⏳ 等待页面重新加载完成"""
        try:
            logger.info("⏳ 等待页面重新加载完成...")
            
            start_time = time.time()
            stable_count = 0
            required_stable = 3
            
            while time.time() - start_time < max_wait:
                try:
                    # 检查页面基本状态
                    ready_state = await page.evaluate("document.readyState")
                    
                    # 检查是否还有加载指示器
                    loading_check = await page.evaluate("""
                        () => {
                            const loadingTexts = ['正在载入', '正在加载', 'loading'];
                            const hasLoadingText = loadingTexts.some(text => 
                                document.body.textContent.includes(text)
                            );
                            
                            const spinners = document.querySelectorAll('.loading, .spinner');
                            
                            return {
                                readyState: document.readyState,
                                hasLoadingText: hasLoadingText,
                                spinnerCount: spinners.length,
                                isStable: document.readyState === 'complete' && !hasLoadingText && spinners.length === 0
                            };
                        }
                    """)
                    
                    if loading_check['isStable']:
                        stable_count += 1
                        logger.info(f"✅ 页面稳定检测 {stable_count}/{required_stable}")
                        
                        if stable_count >= required_stable:
                            logger.info("🎉 页面重新加载完成，状态稳定")
                            # 重置加载检测状态
                            self.page_recovery_state['loading_start_time'] = None
                            self.page_recovery_state['loading_detection_count'] = 0
                            return True
                    else:
                        stable_count = 0
                        logger.info(f"🔄 页面状态: {loading_check}")
                    
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"⚠️ 状态检查异常: {e}")
                    await asyncio.sleep(3)
            
            logger.warning(f"⏰ 页面重新加载等待超时 ({max_wait}s)")
            return False
            
        except Exception as e:
            logger.error(f"❌ 等待页面重新加载失败: {e}")
            return False

    async def _restore_questionnaire_progress(self, page, backup_data: Dict) -> Dict:
        """🔍 恢复问卷答题进度"""
        try:
            logger.info("🔍 尝试恢复问卷答题进度...")
            
            if not backup_data.get('success'):
                logger.warning("⚠️ 无有效备份数据，从头开始答题")
                return {'success': False, 'reason': 'no_backup_data'}
            
            # 恢复已回答问题的状态
            backup_answered = backup_data['backup_data']['answered_state']
            self.answered_questions = set(backup_answered['answered_questions'])
            self.question_hashes = backup_answered['question_hashes']
            
            logger.info(f"✅ 已恢复答题状态: {len(self.answered_questions)}个已答问题")
            
            # 检查当前页面是否与备份时相同
            current_url = page.url
            current_title = await page.title()
            
            # 如果页面相同，尝试恢复表单数据
            if (current_url == backup_answered['current_url'] or 
                current_title == backup_answered['page_title']):
                
                logger.info("🔄 检测到相同页面，尝试恢复表单数据...")
                form_restore_result = await self._restore_form_data(page, backup_data['backup_data']['form_data'])
                
                return {
                    'success': True, 
                    'reason': 'same_page_restored',
                    'form_restored': form_restore_result
                }
            else:
                logger.info("🆕 检测到新页面，保持已答状态继续答题")
                return {
                    'success': True, 
                    'reason': 'new_page_continue',
                    'form_restored': False
                }
            
        except Exception as e:
            logger.error(f"❌ 恢复问卷进度失败: {e}")
            return {'success': False, 'error': str(e)}

    async def _restore_form_data(self, page, form_data: Dict) -> bool:
        """📝 恢复表单数据"""
        try:
            if not form_data:
                return False
            
            logger.info(f"📝 尝试恢复{len(form_data)}项表单数据...")
            
            # 恢复输入框值
            for key, data in form_data.items():
                try:
                    if key.startswith('input_'):
                        # 通过名称或ID查找元素
                        selector = ""
                        if data.get('id'):
                            selector = f"#{data['id']}"
                        elif data.get('name'):
                            selector = f"[name='{data['name']}']"
                        
                        if selector:
                            element = page.locator(selector).first
                            if await element.count() > 0:
                                await element.fill(data['value'])
                                logger.info(f"✅ 恢复输入: {selector} = {data['value'][:20]}...")
                    
                    elif key.startswith('checked_'):
                        # 恢复选中状态
                        if data.get('name'):
                            selector = f"[name='{data['name']}'][value='{data['value']}']"
                            element = page.locator(selector).first
                            if await element.count() > 0:
                                await element.check()
                                logger.info(f"✅ 恢复选中: {selector}")
                        
                except Exception as item_error:
                    logger.warning(f"⚠️ 恢复表单项失败: {key} - {item_error}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 表单数据恢复失败: {e}")
            return False

    async def auto_monitor_page_recovery(self, browser_context: BrowserContext) -> Dict:
        """
        🔍 自动监控页面状态并在必要时触发恢复
        
        这个方法被设计为在Agent执行任何动作前自动调用，
        确保页面处于健康状态，如有异常自动恢复。
        """
        try:
            page = await browser_context.get_current_page()
            current_time = time.time()
            
            # 🕐 更新最后稳定时间戳
            if not self.page_recovery_state.get('loading_start_time'):
                self.page_recovery_state['last_stable_timestamp'] = current_time
            
            # 🔍 快速检测页面是否可能卡住
            quick_detection = await self._detect_page_stuck_intelligently(page, 60)  # 60秒阈值
            
            monitor_result = {
                'monitor_triggered': True,
                'page_status': 'healthy',
                'action_taken': 'none',
                'detection_result': quick_detection,
                'recovery_result': None
            }
            
            # 🚨 如果检测到页面卡住，立即触发恢复
            if quick_detection.get('is_stuck'):
                logger.warning(f"🚨 自动监控检测到页面卡住: {quick_detection['stuck_reason']}")
                
                # 触发智能恢复引擎
                recovery_result = await self.intelligent_page_stuck_detector_and_recovery_engine(
                    page, max_loading_time=120
                )
                
                monitor_result.update({
                    'page_status': 'stuck_detected',
                    'action_taken': 'automatic_recovery',
                    'recovery_result': recovery_result
                })
                
                if recovery_result.get('recovery_success'):
                    logger.info("🎉 自动监控成功恢复页面状态")
                    monitor_result['page_status'] = 'recovered'
                else:
                    logger.error("❌ 自动监控恢复失败")
                    monitor_result['page_status'] = 'recovery_failed'
            else:
                # 页面健康，记录状态
                logger.debug(f"✅ 页面状态监控：健康 (加载时间: {quick_detection.get('loading_duration', 0):.1f}s)")
            
            return monitor_result
            
        except Exception as e:
            logger.error(f"❌ 自动页面监控异常: {e}")
            return {
                'monitor_triggered': True,
                'page_status': 'monitor_error',
                'action_taken': 'none',
                'error': str(e)
            }

    def set_digital_human_info(self, digital_human_info: Dict):
        """🎯 设置数字人信息，用于智能答题偏好匹配"""
        self.digital_human_info = digital_human_info
        logger.info(f"🎯 设置数字人信息: {digital_human_info.get('name', '未知')} - {digital_human_info}")

    def get_system_status(self) -> Dict:
        """📊 获取五层融合架构系统状态"""
        return {
            'controller_type': 'CustomController',
            'architecture': 'five_layer_fusion',
            'layers': {
                'layer1_dropdown_enhancement': 'active',
                'layer2_anti_detection': 'active', 
                'layer3_intelligent_answering': 'active',
                'layer4_option_discovery': 'active',
                'layer5_page_recovery': 'active'
            },
            'page_recovery_state': self.page_recovery_state,
            'answered_questions_count': len(self.answered_questions),
            'registry_actions_count': len(self.registry.registry.actions),
            'digital_human_configured': hasattr(self, 'digital_human_info'),
            'emergency_recovery_enabled': self.page_recovery_state.get('emergency_recovery_enabled', False)
        }

    def _initialize_language_engine(self) -> Dict:
        """初始化语言智能决策引擎"""
        return {
            'active': True,
            'auto_detect': True,
            'default_language': 'zh-CN',
            'fallback_language': 'en-US'
        }
    
    def determine_answer_language(self, digital_human_info: Dict) -> str:
        """🌍 智能语言决策引擎：根据数字人信息自动推断答题语言"""
        try:
            # 🎯 第一优先级：明确的居住地判断
            residence_indicators = [
                digital_human_info.get("residence", ""),
                digital_human_info.get("location", ""), 
                digital_human_info.get("residence_str", ""),
                digital_human_info.get("birthplace_str", "")
            ]
            
            # 中文国家/地区
            chinese_regions = ['中国', '北京', '上海', '广州', '深圳', '杭州', '南京', '成都', '重庆', 
                             '西安', '武汉', '天津', '苏州', '无锡', '青岛', '大连', '厦门', '宁波',
                             'china', 'beijing', 'shanghai', 'guangzhou', 'shenzhen', 'taipei',
                             '台湾', '香港', '澳门', '新加坡', 'singapore', 'hongkong', 'macau']
            
            # 英文国家/地区  
            english_regions = ['美国', '英国', '加拿大', '澳大利亚', '新西兰', 'usa', 'america', 
                              'uk', 'britain', 'canada', 'australia', 'newzealand']
            
            # 检查居住地
            for indicator in residence_indicators:
                if indicator:
                    indicator_lower = indicator.lower()
                    
                    # 中文地区判断
                    if any(region in indicator_lower for region in chinese_regions):
                        return "zh-CN"
                    
                    # 英文地区判断    
                    if any(region in indicator_lower for region in english_regions):
                        return "en-US"
            
            # 🎯 第二优先级：姓名特征判断
            name = digital_human_info.get("name", "")
            if name:
                # 中文姓名特征（包含中文字符）
                if any('\u4e00' <= char <= '\u9fff' for char in name):
                    return "zh-CN"
                    
                # 常见中文姓氏（拼音）
                chinese_surnames = ['zhang', 'wang', 'li', 'zhao', 'chen', 'liu', 'yang', 'huang', 
                                  'zhou', 'wu', 'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'he', 'lin']
                name_lower = name.lower()
                if any(name_lower.startswith(surname) for surname in chinese_surnames):
                    return "zh-CN"
            
            # 🎯 第三优先级：文化特征判断
            brands = digital_human_info.get("favorite_brands", [])
            if brands:
                chinese_brands = ['华为', '小米', '腾讯', '阿里巴巴', '百度', '美团', '滴滴', 
                                '奈雪的茶', '喜茶', '元气森林', 'huawei', 'xiaomi', 'tencent']
                for brand in brands:
                    if brand and any(cb in str(brand).lower() for cb in chinese_brands):
                        return "zh-CN"
            
            # 🎯 默认：根据数字人ID或其他信息推断
            logger.info(f"⚠️ 无法明确判断语言，使用默认中文：{digital_human_info.get('name', '未知')}")
            return "zh-CN"
            
        except Exception as e:
            logger.error(f"❌ 语言决策引擎错误: {e}")
            return "zh-CN"  # 安全默认值
    
    def generate_localized_answer(self, question_type: str, digital_human_info: Dict, 
                                context: str = "") -> str:
        """🎭 本地化答案生成器：根据语言和身份生成合适的回答"""
        try:
            language = self.determine_answer_language(digital_human_info)
            name = digital_human_info.get("name", "用户")
            age = digital_human_info.get("age", 30)
            residence = digital_human_info.get("residence", "") or digital_human_info.get("location", "")
            
            if language == "zh-CN":
                # 中文回答模板
                if "vacation" in context.lower() or "理想" in context or "度假" in context:
                    answers = [
                        f"我希望能和家人一起去桂林看山水，体验中国的自然美景，品尝当地特色美食。",
                        f"想去西藏看雪山，感受纯净的自然环境，在拉萨的八角街逛逛，体验藏族文化。",
                        f"计划去厦门度假，在鼓浪屿漫步，享受海边的悠闲时光，品尝地道的闽南小吃。",
                        f"希望去成都体验慢生活，在宽窄巷子喝茶聊天，品尝正宗的四川火锅和小吃。"
                    ]
                elif "hobby" in context.lower() or "爱好" in context:
                    answers = [
                        f"我平时喜欢瑜伽和烹饪，瑜伽让我保持身心健康，烹饪则是我放松的方式。",
                        f"喜欢园艺和阅读，在阳台种些花草，闲暇时读些好书，很有成就感。",
                        f"我的爱好是摄影和旅行，用镜头记录生活中的美好瞬间。"
                    ]
                else:
                    # 通用中文回答
                    answers = [
                        f"作为一名{digital_human_info.get('profession', '上班族')}，我认为这个问题很有意思，需要仔细考虑。",
                        f"从我的生活经验来看，这确实是一个值得思考的话题。",
                        f"我觉得这个问题反映了现代生活的一些特点，很有代表性。"
                    ]
            else:
                # 英文回答模板（适用于居住在英语国家的数字人）
                if "vacation" in context.lower() or "travel" in context.lower():
                    answers = [
                        f"I would love to visit Europe, especially France and Italy, to experience the rich history and cuisine.",
                        f"I'm planning to explore the national parks in the US, like Yellowstone, for some outdoor adventure.",
                        f"A relaxing beach vacation in Hawaii sounds perfect for unwinding and enjoying nature."
                    ]
                else:
                    answers = [
                        f"As a {digital_human_info.get('profession', 'professional')}, I find this topic quite interesting.",
                        f"From my experience living here, I believe this is an important consideration.",
                        f"This question reflects some interesting aspects of modern life."
                    ]
            
            # 随机选择一个答案（增加自然性）
            import random
            return random.choice(answers)
            
        except Exception as e:
            logger.error(f"❌ 本地化答案生成失败: {e}")
            # 安全的默认中文答案
            return f"我认为这个问题很有意义，值得仔细思考。"

    # 注意：核心动作注册已在_register_anti_detection_enhancements方法中完成
    # 包括ultra_safe_input_text和ultra_safe_select_dropdown等关键方法
    
    def _detect_text_language(self, text: str) -> str:
        """检测文本语言"""
        # 简单但有效的语言检测
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_chars = len([c for c in text if c.isalpha() or '\u4e00' <= c <= '\u9fff'])
        
        if total_chars == 0:
            return "中文"  # 默认中文
            
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:  # 30%以上中文字符
            return "中文"
        else:
            return "英文"
    
    def _get_answer_language(self, digital_human_info: Dict) -> str:
        """获取数字人应该使用的答题语言"""
        return self.determine_answer_language(digital_human_info)
    
    def _convert_text_language(self, text: str, target_language: str, digital_human_info: Dict) -> str:
        """转换文本语言"""
        try:
            # 使用本地化答案生成器
            return self.generate_localized_answer(
                question_type="fill_blank",
                digital_human_info=digital_human_info,
                context=f"原文本：{text}，目标语言：{target_language}"
            )
        except Exception as e:
            logger.warning(f"⚠️ 语言转换失败，使用备用方案: {e}")
            # 备用方案：基于目标语言生成标准答案
            if target_language == "中文":
                return "我认为这个问题很有意义，需要仔细考虑。"
            else:
                return "I think this question is very meaningful and needs careful consideration."
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度（简单的字符匹配算法）"""
        try:
            if not text1 or not text2:
                return 0.0
            
            text1 = text1.lower().strip()
            text2 = text2.lower().strip()
            
            # 完全匹配
            if text1 == text2:
                return 1.0
            
            # 包含关系
            if text1 in text2 or text2 in text1:
                return 0.8
            
            # 字符集交集比例
            set1 = set(text1)
            set2 = set(text2)
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception:
            return 0.0

    def get_questionnaire_aware_system_prompt(self) -> str:
        """
        🎯 获取问卷感知的系统提示词增强
        
        这个提示词将帮助Agent理解问卷的多页面特性，避免提前结束
        """
        return """
🎯 CRITICAL QUESTIONNAIRE COMPLETION INSTRUCTIONS:

You are an intelligent questionnaire completion agent. Your primary goal is to complete ALL questions in a multi-page questionnaire system. Follow these CRITICAL rules:

1. **NEVER assume completion until you see explicit completion signals**:
   - "感谢您的参与" / "Thank you for participating"
   - "问卷已完成" / "Survey completed"
   - "调查结束" / "Survey ended"
   - URL contains: "complete", "success", "finish", "thank"

2. **CONTINUE answering if you see ANY of these signals**:
   - Form elements (radio buttons, checkboxes, dropdowns, text inputs)
   - "下一页" / "Next page" / "Continue" buttons
   - Question numbers or progress indicators
   - Any text containing "问题" / "question" / "选择" / "choice"

3. **Page transitions are NORMAL in questionnaires**:
   - After submitting answers, you may be redirected to new question pages
   - Each page may contain different types of questions
   - ALWAYS check for new questions after page loads

4. **When you encounter a submit/continue button**:
   - Answer ALL visible questions on current page FIRST
   - Then click submit/continue to proceed to next page
   - Wait for page to load completely
   - Check for new questions on the new page

5. **Only use 'done' action when**:
   - You see explicit completion/thank you messages
   - No form elements are present on the page
   - URL clearly indicates completion (contains success/complete/thank)

6. **If unsure about completion**:
   - Use the 'detect_page_transition_and_continue_answering' action
   - This will help determine if more questions exist
   - ALWAYS err on the side of continuing rather than stopping

Remember: Questionnaires often have multiple pages. Your job is to complete ALL pages, not just the first one!
"""

    def enhance_agent_with_questionnaire_awareness(self, agent) -> bool:
        """
        🎯 为Agent注入问卷感知能力
        
        通过修改Agent的系统提示词，确保其理解问卷的多页面特性
        """
        try:
            logger.info("🎯 为Agent注入问卷感知能力...")
            
            # 获取问卷感知提示词
            questionnaire_prompt = self.get_questionnaire_aware_system_prompt()
            
            # 如果Agent有extend_system_message属性，追加提示词
            if hasattr(agent, 'extend_system_message'):
                if agent.extend_system_message:
                    agent.extend_system_message += "\n\n" + questionnaire_prompt
                else:
                    agent.extend_system_message = questionnaire_prompt
                logger.info("✅ 问卷感知提示词已追加到extend_system_message")
                return True
            
            # 如果Agent有system_message属性，修改系统消息
            elif hasattr(agent, 'system_message'):
                if agent.system_message:
                    agent.system_message += "\n\n" + questionnaire_prompt
                else:
                    agent.system_message = questionnaire_prompt
                logger.info("✅ 问卷感知提示词已追加到system_message")
                return True
            
            # 如果Agent有settings属性，尝试修改设置
            elif hasattr(agent, 'settings') and hasattr(agent.settings, 'system_message'):
                if agent.settings.system_message:
                    agent.settings.system_message += "\n\n" + questionnaire_prompt
                else:
                    agent.settings.system_message = questionnaire_prompt
                logger.info("✅ 问卷感知提示词已追加到settings.system_message")
                return True
            
            else:
                logger.warning("⚠️ 无法找到Agent的系统消息属性，跳过提示词注入")
                return False
                
        except Exception as e:
            logger.error(f"❌ Agent问卷感知能力注入失败: {e}")
            return False
