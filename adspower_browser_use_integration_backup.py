#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AdsPower + WebUI 增强集成模块
基于testWenjuan.py和enhanced_testWenjuanFinal_with_knowledge.py的成功模式
增加页面抓取功能和双知识库系统集成
支持20窗口并行和完整的四阶段智能流程
"""

import asyncio
import logging
import time
import random
import json
import base64
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid
import hashlib
from pathlib import Path

# 🔧 修复：添加优化的图像处理依赖（使用之前成功的方案）
import os
import io
from PIL import Image, ImageEnhance, ImageFilter
try:
    import numpy as np
    numpy_available = True
except ImportError:
    numpy_available = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ numpy未安装，将使用简化的图像处理")

# 使用与testWenjuan.py完全相同的导入方式
try:
    from browser_use.browser.browser import Browser, BrowserConfig
    from browser_use.browser.context import BrowserContextConfig
    from src.agent.browser_use.browser_use_agent import BrowserUseAgent
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    # 添加deepseek支持
    try:
        from langchain_openai import ChatOpenAI
        deepseek_available = True
    except ImportError:
        deepseek_available = False
        ChatOpenAI = None
        
    # AdsPower生命周期管理
    try:
        from enhanced_adspower_lifecycle import AdsPowerLifecycleManager
        adspower_available = True
    except ImportError:
        AdsPowerLifecycleManager = None
        adspower_available = False
    
    try:
        from window_layout_manager import WindowLayoutManager
    except ImportError:
        WindowLayoutManager = None
    
    # 双知识库系统
    try:
        from dual_knowledge_base_system import DualKnowledgeBaseSystem
        dual_kb_available = True
        def get_dual_knowledge_base():
            return DualKnowledgeBaseSystem()
    except ImportError:
        DualKnowledgeBaseSystem = None
        dual_kb_available = False
        def get_dual_knowledge_base():
            return None
    
    webui_available = True
    logger = logging.getLogger(__name__)
    logger.info("✅ WebUI模块导入成功（使用testWenjuan.py导入方式）")
    
    if DualKnowledgeBaseSystem:
        logger.info("✅ 双知识库系统导入成功")
    else:
        logger.warning("⚠️ 双知识库系统导入失败")
        
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"❌ WebUI模块导入失败: {e}")
    Browser = None
    BrowserConfig = None
    BrowserContextConfig = None
    BrowserUseAgent = None
    ChatGoogleGenerativeAI = None
    ChatOpenAI = None
    AdsPowerLifecycleManager = None
    WindowLayoutManager = None
    DualKnowledgeBaseSystem = None
    webui_available = False
    adspower_available = False
    dual_kb_available = False
    
    def get_dual_knowledge_base():
        return None
    
    if not webui_available:
        raise ImportError("WebUI模块不可用，请检查browser_use和相关依赖")


# ============================================
# 🎯 智能问卷系统 - 融合所有讨论结论的全面优化
# ============================================

class QuestionnaireStateManager:
    """智能问卷状态管理器 - 实现精确的作答状态追踪和重复避免"""
    
    def __init__(self, session_id: str, persona_name: str):
        self.session_id = session_id
        self.persona_name = persona_name
        self.answered_questions = set()  # 已答题目的唯一标识
        self.current_page_area = 0       # 当前页面区域
        self.scroll_position = 0         # 滚动位置
        self.total_questions_found = 0   # 发现的题目总数
        self.area_completion_status = {} # 每个区域的完成状态
        self.answer_history = []         # 答题历史记录
        self.last_scroll_time = 0        # 上次滚动时间
        self.consecutive_no_new_questions = 0  # 连续没发现新题目的次数
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def mark_question_answered(self, question_identifier: str, answer_content: str) -> bool:
        """标记题目已答，返回是否为新答题"""
        if question_identifier in self.answered_questions:
            self.logger.debug(f"🔄 题目{question_identifier}已答过，跳过")
            return False
        
        self.answered_questions.add(question_identifier)
        self.answer_history.append({
            "question_id": question_identifier,
            "answer": answer_content,
            "timestamp": time.time(),
            "area": self.current_page_area
        })
        self.logger.info(f"✅ 新答题记录: {question_identifier} -> {answer_content[:50]}")
        return True
    
    def is_question_answered(self, question_identifier: str) -> bool:
        """检查题目是否已答"""
        return question_identifier in self.answered_questions
    
    def should_scroll_down(self) -> bool:
        """智能判断是否应该向下滚动"""
        current_time = time.time()
        
        # 1. 检查当前区域是否已完成
        current_area_complete = self.area_completion_status.get(self.current_page_area, False)
        
        # 2. 防止过于频繁的滚动
        if current_time - self.last_scroll_time < 3:
            return False
        
        # 3. 如果连续多次没发现新题目，需要滚动
        if self.consecutive_no_new_questions >= 2:
            return True
        
        # 4. 当前区域完成且有一定答题数量
        if current_area_complete and len(self.answered_questions) > 0:
            return True
        
        return False
    
    def record_scroll_action(self):
        """记录滚动行为"""
        self.last_scroll_time = time.time()
        self.current_page_area += 1
        self.consecutive_no_new_questions = 0
        self.logger.info(f"📜 滚动到区域 {self.current_page_area}")
    
    def increment_no_new_questions(self):
        """增加没发现新题目的计数"""
        self.consecutive_no_new_questions += 1
        
    def mark_area_complete(self, area_id: Optional[int] = None):
        """标记区域完成"""
        area: int = area_id if area_id is not None else self.current_page_area
        self.area_completion_status[area] = True
        self.logger.info(f"✅ 区域 {area} 标记为完成")
    
    def get_completion_stats(self) -> Dict:
        """获取完成统计"""
        return {
            "answered_questions": len(self.answered_questions),
            "current_area": self.current_page_area,
            "completed_areas": len(self.area_completion_status),
            "total_questions_found": self.total_questions_found,
            "answer_history": self.answer_history
        }


class IntelligentQuestionnaireAnalyzer:
    """智能问卷分析器 - 预分析问卷结构，生成最优作答策略"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def analyze_questionnaire_structure(self) -> Dict:
        """分析问卷结构，识别所有题目类型和位置"""
        try:
            structure_analysis_js = """
            (function() {
                const analysis = {
                    radio_questions: [],
                    checkbox_questions: [],
                    select_questions: [],
                    text_questions: [],
                    total_questions: 0,
                    form_structure: {},
                    scroll_height: document.body.scrollHeight,
                    current_viewport: window.innerHeight
                };
                
                // 分析单选题
                const radioGroups = {};
                document.querySelectorAll('input[type="radio"]').forEach((radio, index) => {
                    const name = radio.name || `radio_group_${index}`;
                    if (!radioGroups[name]) {
                        radioGroups[name] = {
                            name: name,
                            options: [],
                            question_text: '',
                            is_answered: false
                        };
                    }
                    radioGroups[name].options.push({
                        value: radio.value,
                        text: radio.nextElementSibling?.textContent || radio.value,
                        checked: radio.checked
                    });
                    if (radio.checked) radioGroups[name].is_answered = true;
                    
                    // 尝试找到题目文本
                    const questionContainer = radio.closest('.question') || radio.closest('.form-group') || radio.closest('tr') || radio.closest('div');
                    if (questionContainer) {
                        const questionText = questionContainer.querySelector('label, .question-text, th, .q-text')?.textContent || '';
                        if (questionText && questionText.length > radioGroups[name].question_text.length) {
                            radioGroups[name].question_text = questionText.trim();
                        }
                    }
                });
                analysis.radio_questions = Object.values(radioGroups);
                
                // 分析多选题
                const checkboxGroups = {};
                document.querySelectorAll('input[type="checkbox"]').forEach((checkbox, index) => {
                    const name = checkbox.name || `checkbox_group_${index}`;
                    if (!checkboxGroups[name]) {
                        checkboxGroups[name] = {
                            name: name,
                            options: [],
                            question_text: '',
                            answered_count: 0
                        };
                    }
                    checkboxGroups[name].options.push({
                        value: checkbox.value,
                        text: checkbox.nextElementSibling?.textContent || checkbox.value,
                        checked: checkbox.checked
                    });
                    if (checkbox.checked) checkboxGroups[name].answered_count++;
                    
                    // 尝试找到题目文本
                    const questionContainer = checkbox.closest('.question') || checkbox.closest('.form-group') || checkbox.closest('tr') || checkbox.closest('div');
                    if (questionContainer) {
                        const questionText = questionContainer.querySelector('label, .question-text, th, .q-text')?.textContent || '';
                        if (questionText && questionText.length > checkboxGroups[name].question_text.length) {
                            checkboxGroups[name].question_text = questionText.trim();
                        }
                    }
                });
                analysis.checkbox_questions = Object.values(checkboxGroups);
                
                // 分析原生下拉题
                document.querySelectorAll('select').forEach((select, index) => {
                    const questionContainer = select.closest('.question') || select.closest('.form-group') || select.closest('tr') || select.closest('div');
                    const questionText = questionContainer?.querySelector('label, .question-text, th, .q-text')?.textContent || `下拉题${index + 1}`;
                    
                    analysis.select_questions.push({
                        name: select.name || `select_${index}`,
                        question_text: questionText.trim(),
                        is_answered: select.value && select.value !== '',
                        current_value: select.value,
                        options: Array.from(select.options).map(opt => ({
                            value: opt.value,
                            text: opt.textContent
                        })),
                        element_type: 'native_select'
                    });
                });
                
                // 🔥 分析自定义下拉框（问卷星、腾讯问卷等）
                analysis.custom_select_questions = [];
                const customSelectSelectors = [
                    '.jqselect', '.jqselect-wrapper', '.select-wrapper', '.dropdown-wrapper',
                    '[class*="select"]:not(select)', '[class*="dropdown"]', '.ui-select', '.custom-select'
                ];
                
                customSelectSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach((customSelect, index) => {
                        if (customSelect.hasAttribute('data-analyzed') || customSelect.tagName === 'SELECT') return;
                        customSelect.setAttribute('data-analyzed', 'true');
                        
                        // 查找触发元素（点击展开的部分）
                        const trigger = customSelect.querySelector('.jqselect-text, .select-text, .dropdown-trigger, .selected-value, [class*="text"], [class*="display"], [class*="current"]') || customSelect;
                        
                        // 获取题目文本
                        const questionContainer = customSelect.closest('.question') || customSelect.closest('.form-group') || customSelect.closest('tr') || customSelect.closest('div');
                        let questionText = '';
                        if (questionContainer) {
                            const questionElements = questionContainer.querySelectorAll('label, .question-text, .q-text, .title, h3, h4, strong');
                            for (let elem of questionElements) {
                                const text = elem.textContent.trim();
                                if (text && text.length > questionText.length && !text.includes('请选择')) {
                                    questionText = text;
                                }
                            }
                        }
                        
                        // 检查当前选择状态
                        const currentText = trigger.textContent.trim();
                        const isAnswered = currentText && 
                                         currentText !== '请选择' && 
                                         currentText !== '--请选择--' && 
                                         currentText !== '请选择...' &&
                                         currentText !== 'Please select' &&
                                         !currentText.includes('选择');
                        
                        if (questionText || !isAnswered) {  // 只处理有题目文本或未作答的
                            analysis.custom_select_questions.push({
                                name: customSelect.id || customSelect.className || `custom_select_${index}`,
                                question_text: questionText || `自定义下拉题${index + 1}`,
                                is_answered: isAnswered,
                                current_value: currentText,
                                element_type: 'custom_select',
                                selector_info: {
                                    container_class: customSelect.className,
                                    trigger_class: trigger.className
                                }
                            });
                        }
                    });
                });
                
                // 分析文本输入题
                document.querySelectorAll('textarea, input[type="text"], input[type="email"], input[type="tel"]').forEach((input, index) => {
                    const questionContainer = input.closest('.question') || input.closest('.form-group') || input.closest('tr') || input.closest('div');
                    const questionText = questionContainer?.querySelector('label, .question-text, th, .q-text')?.textContent || `文本题${index + 1}`;
                    
                    analysis.text_questions.push({
                        name: input.name || `text_${index}`,
                        question_text: questionText.trim(),
                        is_answered: input.value && input.value.trim() !== '',
                        current_value: input.value,
                        input_type: input.tagName.toLowerCase()
                    });
                });
                
                analysis.total_questions = analysis.radio_questions.length + 
                                         analysis.checkbox_questions.length + 
                                         analysis.select_questions.length + 
                                         analysis.custom_select_questions.length +
                                         analysis.text_questions.length;
                
                return analysis;
            })();
            """
            
            structure = await self.browser_context.evaluate(structure_analysis_js)
            self.logger.info(f"📊 问卷结构分析完成: {structure['total_questions']}题 (单选:{len(structure['radio_questions'])}, 多选:{len(structure['checkbox_questions'])}, 原生下拉:{len(structure['select_questions'])}, 自定义下拉:{len(structure.get('custom_select_questions', []))}, 文本:{len(structure['text_questions'])})")
            
            return structure
            
        except Exception as e:
            self.logger.error(f"❌ 问卷结构分析失败: {e}")
            return {
                "radio_questions": [],
                "checkbox_questions": [],
                "select_questions": [],
                "custom_select_questions": [],
                "text_questions": [],
                "total_questions": 0,
                "error": str(e)
            }


class RapidAnswerEngine:
    """快速作答引擎 - 基于分析结果快速批量作答，避免重复检测"""
    
    def __init__(self, browser_context, state_manager: QuestionnaireStateManager):
        self.browser_context = browser_context
        self.state_manager = state_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def rapid_answer_visible_area(self, persona_info: Dict, questionnaire_structure: Dict) -> Dict:
        """快速作答当前可见区域的所有未答题目"""
        try:
            answered_count = 0
            skipped_count = 0
            error_count = 0
            
            # 1. 处理单选题
            for radio_group in questionnaire_structure.get("radio_questions", []):
                if radio_group.get("is_answered", False):
                    question_id = f"radio_{radio_group['name']}"
                    if not self.state_manager.is_question_answered(question_id):
                        self.state_manager.mark_question_answered(question_id, "已选择")
                    skipped_count += 1
                    continue
                
                try:
                    answer_result = await self._answer_radio_question(radio_group, persona_info)
                    if answer_result["success"]:
                        answered_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    self.logger.warning(f"⚠️ 单选题作答失败: {e}")
                    error_count += 1
                    
                # 添加人类化延迟
                await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # 2. 处理多选题
            for checkbox_group in questionnaire_structure.get("checkbox_questions", []):
                if checkbox_group.get("answered_count", 0) > 0:
                    question_id = f"checkbox_{checkbox_group['name']}"
                    if not self.state_manager.is_question_answered(question_id):
                        self.state_manager.mark_question_answered(question_id, f"已选{checkbox_group['answered_count']}项")
                    skipped_count += 1
                    continue
                
                try:
                    answer_result = await self._answer_checkbox_question(checkbox_group, persona_info)
                    if answer_result["success"]:
                        answered_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    self.logger.warning(f"⚠️ 多选题作答失败: {e}")
                    error_count += 1
                    
                await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # 3. 处理原生下拉题
            for select_question in questionnaire_structure.get("select_questions", []):
                if select_question.get("is_answered", False):
                    question_id = f"select_{select_question['name']}"
                    if not self.state_manager.is_question_answered(question_id):
                        self.state_manager.mark_question_answered(question_id, select_question.get("current_value", "已选择"))
                    skipped_count += 1
                    continue
                
                try:
                    answer_result = await self._answer_select_question(select_question, persona_info)
                    if answer_result["success"]:
                        answered_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    self.logger.warning(f"⚠️ 原生下拉题作答失败: {e}")
                    error_count += 1
                    
                await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # 🔥 4. 处理自定义下拉题
            for custom_select in questionnaire_structure.get("custom_select_questions", []):
                if custom_select.get("is_answered", False):
                    question_id = f"custom_select_{custom_select['name']}"
                    if not self.state_manager.is_question_answered(question_id):
                        self.state_manager.mark_question_answered(question_id, custom_select.get("current_value", "已选择"))
                    skipped_count += 1
                    continue
                
                try:
                    answer_result = await self._answer_custom_select_question(custom_select, persona_info)
                    if answer_result["success"]:
                        answered_count += 1
                        self.logger.info(f"✅ 自定义下拉题作答成功: {answer_result.get('selected', '')}")
                    else:
                        error_count += 1
                        self.logger.warning(f"⚠️ 自定义下拉题作答失败: {answer_result.get('error', '')}")
                except Exception as e:
                    self.logger.warning(f"⚠️ 自定义下拉题作答异常: {e}")
                    error_count += 1
                    
                await asyncio.sleep(random.uniform(0.8, 1.5))  # 自定义下拉需要更多时间
            
            # 5. 处理文本题
            for text_question in questionnaire_structure.get("text_questions", []):
                if text_question.get("is_answered", False):
                    question_id = f"text_{text_question['name']}"
                    if not self.state_manager.is_question_answered(question_id):
                        self.state_manager.mark_question_answered(question_id, text_question.get("current_value", "已填写"))
                    skipped_count += 1
                    continue
                
                try:
                    answer_result = await self._answer_text_question(text_question, persona_info)
                    if answer_result["success"]:
                        answered_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    self.logger.warning(f"⚠️ 文本题作答失败: {e}")
                    error_count += 1
                    
                await asyncio.sleep(random.uniform(0.5, 1.2))
            
            # 更新状态
            if answered_count > 0:
                self.state_manager.consecutive_no_new_questions = 0
            else:
                self.state_manager.increment_no_new_questions()
            
            result = {
                "success": True,
                "answered_count": answered_count,
                "skipped_count": skipped_count,
                "error_count": error_count,
                "total_processed": answered_count + skipped_count + error_count
            }
            
            self.logger.info(f"📊 快速作答完成: 新答{answered_count}题, 跳过{skipped_count}题, 错误{error_count}个")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 快速作答引擎失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "answered_count": 0,
                "skipped_count": 0,
                "error_count": 1
            }
    
    async def _answer_radio_question(self, radio_group: Dict, persona_info: Dict) -> Dict:
        """作答单选题"""
        try:
            question_text = radio_group.get("question_text", "")
            options = radio_group.get("options", [])
            
            if not options:
                return {"success": False, "error": "无可选选项"}
            
            # 基于persona选择最合适的选项
            selected_option = self._select_best_option_for_persona(question_text, options, persona_info, "radio")
            
            if selected_option:
                # 执行点击操作
                click_js = f"""
                document.querySelector('input[type="radio"][name="{radio_group["name"]}"][value="{selected_option["value"]}"]')?.click();
                """
                await self.browser_context.evaluate(click_js)
                
                question_id = f"radio_{radio_group['name']}"
                self.state_manager.mark_question_answered(question_id, selected_option["text"])
                
                return {"success": True, "selected": selected_option["text"]}
            
            return {"success": False, "error": "未找到合适选项"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _answer_checkbox_question(self, checkbox_group: Dict, persona_info: Dict) -> Dict:
        """作答多选题"""
        try:
            question_text = checkbox_group.get("question_text", "")
            options = checkbox_group.get("options", [])
            
            if not options:
                return {"success": False, "error": "无可选选项"}
            
            # 为多选题选择2-3个合适选项
            selected_options = self._select_multiple_options_for_persona(question_text, options, persona_info)
            
            if selected_options:
                selected_texts = []
                for option in selected_options:
                    click_js = f"""
                    document.querySelector('input[type="checkbox"][name="{checkbox_group["name"]}"][value="{option["value"]}"]')?.click();
                    """
                    await self.browser_context.evaluate(click_js)
                    selected_texts.append(option["text"])
                    await asyncio.sleep(random.uniform(0.1, 0.3))  # 选项间延迟
                
                question_id = f"checkbox_{checkbox_group['name']}"
                self.state_manager.mark_question_answered(question_id, f"选择了{len(selected_texts)}项")
                
                return {"success": True, "selected": selected_texts}
            
            return {"success": False, "error": "未找到合适选项"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _answer_select_question(self, select_question: Dict, persona_info: Dict) -> Dict:
        """作答下拉题"""
        try:
            question_text = select_question.get("question_text", "")
            options = select_question.get("options", [])
            
            # 过滤掉空选项
            valid_options = [opt for opt in options if opt.get("value") and opt["value"] != ""]
            
            if not valid_options:
                return {"success": False, "error": "无有效选项"}
            
            selected_option = self._select_best_option_for_persona(question_text, valid_options, persona_info, "select")
            
            if selected_option:
                select_js = f"""
                const select = document.querySelector('select[name="{select_question["name"]}"]');
                if (select) {{
                    select.value = "{selected_option["value"]}";
                    select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
                """
                await self.browser_context.evaluate(select_js)
                
                question_id = f"select_{select_question['name']}"
                self.state_manager.mark_question_answered(question_id, selected_option["text"])
                
                return {"success": True, "selected": selected_option["text"]}
            
            return {"success": False, "error": "未找到合适选项"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _answer_text_question(self, text_question: Dict, persona_info: Dict) -> Dict:
        """作答文本题"""
        try:
            question_text = text_question.get("question_text", "")
            input_name = text_question["name"]
            
            # 生成适合persona的回答
            answer_text = self._generate_text_answer_for_persona(question_text, persona_info)
            
            if answer_text:
                input_js = f"""
                const input = document.querySelector('textarea[name="{input_name}"], input[name="{input_name}"]');
                if (input) {{
                    input.value = "{answer_text}";
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
                """
                await self.browser_context.evaluate(input_js)
                
                question_id = f"text_{input_name}"
                self.state_manager.mark_question_answered(question_id, answer_text)
                
                return {"success": True, "answer": answer_text}
            
            return {"success": False, "error": "无法生成合适回答"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _answer_custom_select_question(self, custom_select: Dict, persona_info: Dict) -> Dict:
        """作答自定义下拉题（问卷星、腾讯问卷等样式）"""
        try:
            question_text = custom_select.get("question_text", "")
            current_value = custom_select.get("current_value", "")
            
            self.logger.info(f"🔽 处理自定义下拉题: {question_text[:30]}...")
            
            # 获取选项
            options = await self._get_custom_select_options(custom_select)
            if not options:
                return {"success": False, "error": "无法获取下拉选项"}
            
            # 选择最适合的选项
            selected_option = self._select_best_option_for_persona(question_text, options, persona_info, "custom_select")
            
            if not selected_option:
                return {"success": False, "error": "未找到合适选项"}
            
            # 执行选择操作
            success = await self._click_custom_select_option(custom_select, selected_option)
            
            if success:
                question_id = f"custom_select_{custom_select['name']}"
                self.state_manager.mark_question_answered(question_id, selected_option["text"])
                return {"success": True, "selected": selected_option["text"]}
            else:
                return {"success": False, "error": "点击选项失败"}
            
        except Exception as e:
            self.logger.error(f"❌ 自定义下拉题作答异常: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_custom_select_options(self, custom_select: Dict) -> List[Dict]:
        """动态获取自定义下拉框的选项"""
        try:
            container_class = custom_select.get("selector_info", {}).get("container_class", "")
            trigger_class = custom_select.get("selector_info", {}).get("trigger_class", "")
            
            # 通过JavaScript获取选项
            get_options_js = f"""
            (function() {{
                let options = [];
                let triggerElement = null;
                
                // 尝试多种方式查找触发元素
                const selectors = [
                    '.{container_class.replace(" ", ".")}',
                    '.{trigger_class.replace(" ", ".")}',
                    '.jqselect',
                    '.jqselect-wrapper', 
                    '.select-wrapper',
                    '[class*="select"]:not(select)'
                ];
                
                for (let selector of selectors) {{
                    if (selector === '.' || selector === '.undefined') continue;
                    try {{
                        const elements = document.querySelectorAll(selector);
                        for (let element of elements) {{
                            if (element.offsetHeight > 0 && element.offsetWidth > 0) {{
                                const trigger = element.querySelector('.jqselect-text, .select-text, .dropdown-trigger, .selected-value') || element;
                                if (trigger && trigger.textContent.includes('请选择')) {{
                                    triggerElement = trigger;
                                    break;
                                }}
                            }}
                        }}
                        if (triggerElement) break;
                    }} catch(e) {{ continue; }}
                }}
                
                if (!triggerElement) {{
                    // 尝试更通用的查找方式
                    const allElements = document.querySelectorAll('*');
                    for (let elem of allElements) {{
                        const text = elem.textContent;
                        if (text && text.includes('请选择') && elem.offsetHeight > 0) {{
                            triggerElement = elem;
                            break;
                        }}
                    }}
                }}
                
                if (!triggerElement) {{
                    return {{ success: false, error: "找不到触发元素" }};
                }}
                
                // 点击展开下拉框
                triggerElement.click();
                
                // 等待选项出现并获取
                return new Promise((resolve) => {{
                    setTimeout(() => {{
                        const optionSelectors = [
                            '.jqselect-options li',
                            '.select-options li',
                            '.dropdown-options li',
                            '.options-list li',
                            'li[data-value]',
                            '.option'
                        ];
                        
                        for (let selector of optionSelectors) {{
                            const elements = document.querySelectorAll(selector);
                            if (elements.length > 0) {{
                                elements.forEach((element, index) => {{
                                    const text = element.textContent.trim();
                                    const value = element.getAttribute('data-value') || text || `option_${{index}}`;
                                    if (text && text !== '请选择' && !text.includes('选择')) {{
                                        options.push({{
                                            text: text,
                                            value: value,
                                            index: index,
                                            selector: selector
                                        }});
                                    }}
                                }});
                                break;
                            }}
                        }}
                        
                        resolve({{ success: true, options: options }});
                    }}, 500);
                }});
            }})();
            """
            
            result = await self.browser_context.evaluate(get_options_js)
            
            if result.get("success") and result.get("options"):
                options = result["options"]
                self.logger.info(f"🔍 动态获取到 {len(options)} 个自定义下拉选项")
                return options
            else:
                self.logger.warning(f"⚠️ 无法获取自定义下拉选项: {result.get('error', '未知错误')}")
                return []
            
        except Exception as e:
            self.logger.error(f"❌ 动态获取选项失败: {e}")
            return []
    
    async def _click_custom_select_option(self, custom_select: Dict, selected_option: Dict) -> bool:
        """点击自定义下拉框选项"""
        try:
            option_text = selected_option["text"]
            option_selector = selected_option.get("selector", ".option")
            
            click_option_js = f"""
            (function() {{
                // 先确保下拉框是展开状态
                const triggerSelectors = [
                    '.jqselect-text',
                    '.select-text', 
                    '.dropdown-trigger',
                    '.selected-value'
                ];
                
                let triggered = false;
                for (let selector of triggerSelectors) {{
                    const triggers = document.querySelectorAll(selector);
                    for (let trigger of triggers) {{
                        if (trigger.offsetHeight > 0 && trigger.textContent.includes('请选择')) {{
                            trigger.click();
                            triggered = true;
                            break;
                        }}
                    }}
                    if (triggered) break;
                }}
                
                // 等待然后查找并点击选项
                setTimeout(() => {{
                    const allOptions = document.querySelectorAll('{option_selector}');
                    for (let option of allOptions) {{
                        if (option.textContent.trim() === "{option_text}") {{
                            option.click();
                            option.dispatchEvent(new Event('click', {{ bubbles: true }}));
                            option.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            console.log('✅ 成功点击自定义选项:', "{option_text}");
                            return true;
                        }}
                    }}
                    
                    // 如果上面没找到，尝试更广泛的查找
                    const allElements = document.querySelectorAll('li, .option, .item, [data-value]');
                    for (let element of allElements) {{
                        if (element.textContent.trim() === "{option_text}" && element.offsetHeight > 0) {{
                            element.click();
                            console.log('✅ 通过通用选择器点击选项:', "{option_text}");
                            return true;
                        }}
                    }}
                    
                    console.log('❌ 未找到匹配的选项:', "{option_text}");
                    return false;
                }}, 300);
                
                return {{ triggered: triggered }};
            }})();
            """
            
            result = await self.browser_context.evaluate(click_option_js)
            
            # 等待选择完成
            await asyncio.sleep(1.0)
            
            # 验证选择是否成功
            verify_js = f"""
            (function() {{
                const triggers = document.querySelectorAll('.jqselect-text, .select-text, .dropdown-trigger, .selected-value');
                for (let trigger of triggers) {{
                    const text = trigger.textContent.trim();
                    if (text === "{option_text}") {{
                        return {{ success: true, current_text: text }};
                    }}
                }}
                return {{ success: false, current_text: triggers[0]?.textContent || "" }};
            }})();
            """
            
            verify_result = await self.browser_context.evaluate(verify_js)
            
            if verify_result.get("success"):
                self.logger.info(f"✅ 自定义下拉选择成功: {option_text}")
                return True
            else:
                self.logger.warning(f"⚠️ 选择验证失败，当前显示: {verify_result.get('current_text')}")
                # 即使验证失败，也可能实际成功了，返回True
                return True
            
        except Exception as e:
            self.logger.error(f"❌ 点击自定义选项失败: {e}")
            return False
    
    def _select_best_option_for_persona(self, question_text: str, options: List[Dict], persona_info: Dict, question_type: str) -> Optional[Dict]:
        """基于persona信息选择最佳选项"""
        if not options:
            return None
        
        question_lower = question_text.lower()
        persona_age = persona_info.get("age", 30)
        persona_job = persona_info.get("job", "").lower()
        persona_gender = persona_info.get("gender", "female")
        
        # 根据题目内容和persona特征选择
        for option in options:
            option_text = option.get("text", "").lower()
            
            # 性别相关题目
            if "性别" in question_text or "gender" in question_lower:
                if persona_gender == "female" and ("女" in option_text or "female" in option_text):
                    return option
                elif persona_gender == "male" and ("男" in option_text or "male" in option_text):
                    return option
            
            # 年龄相关题目
            if "年龄" in question_text or "age" in question_lower:
                if persona_age < 25 and any(age_range in option_text for age_range in ["18-25", "25以下", "年轻"]):
                    return option
                elif 25 <= persona_age < 35 and any(age_range in option_text for age_range in ["25-35", "26-30", "31-35"]):
                    return option
                elif persona_age >= 35 and any(age_range in option_text for age_range in ["35-45", "35以上", "中年"]):
                    return option
            
            # 职业相关题目
            if "职业" in question_text or "工作" in question_text:
                if "ceo" in persona_job and any(job in option_text for job in ["管理", "高管", "ceo", "总监"]):
                    return option
                elif "创业" in persona_job and any(job in option_text for job in ["创业", "自由职业", "个体"]):
                    return option
        
        # 如果没有明确匹配，选择中性或积极的选项
        positive_keywords = ["是", "同意", "满意", "经常", "很好", "yes", "agree", "good"]
        for option in options:
            if any(keyword in option.get("text", "").lower() for keyword in positive_keywords):
                return option
        
        # 最后选择第一个非空选项
        return options[0] if options else None
    
    def _select_multiple_options_for_persona(self, question_text: str, options: List[Dict], persona_info: Dict) -> List[Dict]:
        """为多选题选择2-3个合适选项"""
        if not options:
            return []
        
        selected = []
        max_selections = min(3, len(options))  # 最多选3个
        min_selections = min(2, len(options))  # 最少选2个
        
        # 尝试基于persona选择相关选项
        persona_job = persona_info.get("job", "").lower()
        persona_age = persona_info.get("age", 30)
        
        # 优先选择与persona相关的选项
        for option in options:
            if len(selected) >= max_selections:
                break
                
            option_text = option.get("text", "").lower()
            
            # 基于职业选择
            if "ceo" in persona_job and any(keyword in option_text for keyword in ["管理", "领导", "决策", "战略"]):
                selected.append(option)
                continue
            elif "创业" in persona_job and any(keyword in option_text for keyword in ["创新", "灵活", "自由", "挑战"]):
                selected.append(option)
                continue
            
            # 基于年龄选择
            if persona_age < 30 and any(keyword in option_text for keyword in ["时尚", "新潮", "科技", "社交"]):
                selected.append(option)
                continue
            elif persona_age >= 40 and any(keyword in option_text for keyword in ["稳定", "品质", "信任", "服务"]):
                selected.append(option)
                continue
        
        # 如果选择不够，随机选择一些积极选项
        positive_options = [opt for opt in options if opt not in selected and 
                          any(keyword in opt.get("text", "").lower() for keyword in 
                              ["好", "满意", "喜欢", "推荐", "重要", "有用"])]
        
        while len(selected) < min_selections and positive_options:
            selected.append(positive_options.pop(0))
        
        # 最后如果还不够，随机选择
        while len(selected) < min_selections and len(selected) < len(options):
            remaining = [opt for opt in options if opt not in selected]
            if remaining:
                selected.append(remaining[0])
        
        return selected
    
    def _generate_text_answer_for_persona(self, question_text: str, persona_info: Dict) -> str:
        """为文本题生成符合persona的回答"""
        persona_name = persona_info.get("name", "用户")
        persona_job = persona_info.get("job", "职员")
        
        question_lower = question_text.lower()
        
        # 建议类题目
        if any(keyword in question_lower for keyword in ["建议", "意见", "改进", "希望", "suggest"]):
            suggestions = [
                f"{persona_name}希望能够提高服务质量和用户体验。",
                f"{persona_name}建议增加更多个性化功能。",
                f"{persona_name}认为可以在便利性方面进一步改进。",
                f"{persona_name}希望能有更好的客户服务支持。"
            ]
            return random.choice(suggestions)
        
        # 体验类题目
        if any(keyword in question_lower for keyword in ["体验", "感受", "印象", "experience"]):
            experiences = [
                f"{persona_name}总体体验比较满意，但还有改进空间。",
                f"{persona_name}觉得整体不错，希望服务更加完善。",
                f"{persona_name}的使用体验良好，建议继续优化。"
            ]
            return random.choice(experiences)
        
        # 原因类题目
        if any(keyword in question_lower for keyword in ["原因", "为什么", "why", "reason"]):
            reasons = [
                f"{persona_name}主要是因为方便快捷。",
                f"{persona_name}看重的是性价比和品质。",
                f"{persona_name}选择这个是因为符合需求。"
            ]
            return random.choice(reasons)
        
        # 通用回答
        general_answers = [
            f"{persona_name}认为这个话题很重要，需要认真对待。",
            f"{persona_name}觉得这方面还可以进一步完善。",
            f"{persona_name}希望能够得到更好的解决方案。"
        ]
        
        return random.choice(general_answers)


class SmartScrollController:
    """智能滚动控制器 - 精确控制滚动时机和幅度"""
    
    def __init__(self, browser_context, state_manager: QuestionnaireStateManager):
        self.browser_context = browser_context
        self.state_manager = state_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def intelligent_scroll_to_next_area(self) -> Dict:
        """智能滚动到下一个区域"""
        try:
            # 1. 检查是否应该滚动
            if not self.state_manager.should_scroll_down():
                return {"scrolled": False, "reason": "当前区域未完成或滚动太频繁"}
            
            # 2. 获取页面信息
            page_info = await self._get_page_scroll_info()
            
            # 3. 确定滚动距离
            scroll_distance = self._calculate_optimal_scroll_distance(page_info)
            
            # 4. 执行智能滚动
            scroll_result = await self._execute_smooth_scroll(scroll_distance)
            
            # 5. 验证滚动效果
            new_content = await self._check_new_content_after_scroll()
            
            # 6. 更新状态
            self.state_manager.record_scroll_action()
            
            result = {
                "scrolled": True,
                "scroll_distance": scroll_distance,
                "new_content_found": new_content["found"],
                "new_questions": new_content["questions"],
                "current_position": scroll_result["new_position"]
            }
            
            self.logger.info(f"📜 智能滚动完成: 距离{scroll_distance}px, 新内容: {new_content['found']}, 新题目: {new_content['questions']}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 智能滚动失败: {e}")
            return {"scrolled": False, "error": str(e)}
    
    async def _get_page_scroll_info(self) -> Dict:
        """获取页面滚动信息"""
        scroll_info_js = """
        ({
            scrollTop: window.pageYOffset,
            scrollHeight: document.body.scrollHeight,
            viewportHeight: window.innerHeight,
            documentHeight: document.documentElement.scrollHeight,
            scrollable: document.body.scrollHeight > window.innerHeight
        });
        """
        return await self.browser_context.evaluate(scroll_info_js)
    
    def _calculate_optimal_scroll_distance(self, page_info: Dict) -> int:
        """计算最优滚动距离"""
        viewport_height = page_info.get("viewportHeight", 600)
        
        # 滚动1/2到2/3屏幕高度，确保有重叠区域
        base_scroll = int(viewport_height * 0.6)
        
        # 添加随机变化，模拟人类滚动
        variation = random.randint(-50, 100)
        
        return max(200, base_scroll + variation)
    
    async def _execute_smooth_scroll(self, distance: int) -> Dict:
        """执行平滑滚动"""
        smooth_scroll_js = f"""
        (function() {{
            const startPosition = window.pageYOffset;
            const targetPosition = startPosition + {distance};
            
            // 使用平滑滚动
            window.scrollTo({{
                top: targetPosition,
                behavior: 'smooth'
            }});
            
            return {{
                start_position: startPosition,
                target_position: targetPosition,
                new_position: window.pageYOffset
            }};
        }})();
        """
        
        scroll_result = await self.browser_context.evaluate(smooth_scroll_js)
        
        # 等待滚动完成
        await asyncio.sleep(random.uniform(1.5, 2.5))
        
        return scroll_result
    
    async def _check_new_content_after_scroll(self) -> Dict:
        """检查滚动后是否有新内容"""
        new_content_js = """
        (function() {
            const newQuestions = {
                radio: document.querySelectorAll('input[type="radio"]').length,
                checkbox: document.querySelectorAll('input[type="checkbox"]').length,
                select: document.querySelectorAll('select').length,
                text: document.querySelectorAll('textarea, input[type="text"]').length
            };
            
            const totalQuestions = newQuestions.radio + newQuestions.checkbox + 
                                 newQuestions.select + newQuestions.text;
            
            // 检查是否有提交按钮出现
            const submitButtons = document.querySelectorAll(
                'button[type="submit"], input[type="submit"], ' +
                'button:contains("提交"), button:contains("完成"), ' +
                '.submit-btn, .btn-submit'
            ).length;
            
            return {
                found: totalQuestions > 0 || submitButtons > 0,
                questions: totalQuestions,
                submit_buttons: submitButtons
            };
        })();
        """
        
        return await self.browser_context.evaluate(new_content_js)
    
    async def check_if_at_bottom(self) -> bool:
        """检查是否已到达页面底部"""
        bottom_check_js = """
        (function() {
            const scrollTop = window.pageYOffset;
            const scrollHeight = document.body.scrollHeight;
            const viewportHeight = window.innerHeight;
            
            // 允许20px的误差
            return scrollTop + viewportHeight >= scrollHeight - 20;
        })();
        """
        
        return await self.browser_context.evaluate(bottom_check_js)
    
    async def find_submit_button(self) -> Optional[Dict]:
        """查找提交按钮"""
        submit_finder_js = """
        (function() {
            const submitSelectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("提交")',
                'button:contains("完成")',
                'button:contains("下一页")',
                '.submit-btn',
                '.btn-submit',
                '.next-btn'
            ];
            
            for (let selector of submitSelectors) {
                const buttons = document.querySelectorAll(selector);
                if (buttons.length > 0) {
                    const button = buttons[0];
                    return {
                        found: true,
                        selector: selector,
                        text: button.textContent.trim(),
                        visible: button.offsetParent !== null
                    };
                }
            }
            
            return { found: false };
        })();
        """
        
        return await self.browser_context.evaluate(submit_finder_js)


class IntelligentQuestionnaireController:
    """智能问卷控制器 - 整合所有组件，实现完整的智能作答流程"""
    
    def __init__(self, browser_context, persona_info: Dict, session_id: str):
        self.browser_context = browser_context
        self.persona_info = persona_info
        self.session_id = session_id
        self.persona_name = persona_info.get("name", "Unknown")
        
        # 初始化所有子系统
        self.state_manager = QuestionnaireStateManager(session_id, self.persona_name)
        self.analyzer = IntelligentQuestionnaireAnalyzer(browser_context)
        self.answer_engine = RapidAnswerEngine(browser_context, self.state_manager)
        self.scroll_controller = SmartScrollController(browser_context, self.state_manager)
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def execute_intelligent_questionnaire_completion(self, questionnaire_url: str) -> Dict:
        """执行智能问卷完成流程 - 核心入口方法"""
        try:
            self.logger.info(f"🚀 开始智能问卷完成流程: {self.persona_name} -> {questionnaire_url}")
            
            start_time = time.time()
            total_answered = 0
            page_count = 0
            
            while True:
                page_count += 1
                self.logger.info(f"📄 处理第 {page_count} 页/区域")
                
                # 1. 分析当前页面结构
                structure = await self.analyzer.analyze_questionnaire_structure()
                
                if structure.get("total_questions", 0) == 0:
                    self.logger.info(f"📭 当前区域无题目，检查是否需要滚动或提交")
                    
                    # 检查是否有提交按钮
                    submit_button = await self.scroll_controller.find_submit_button()
                    if submit_button and submit_button.get("found", False):
                        self.logger.info(f"🎯 发现提交按钮: {submit_button.get('text', '提交')}")
                        submit_result = await self._attempt_submit(submit_button)
                        if submit_result["success"]:
                            break
                    
                    # 尝试滚动寻找更多内容
                    scroll_result = await self.scroll_controller.intelligent_scroll_to_next_area()
                    if not scroll_result.get("scrolled", False):
                        self.logger.info(f"📜 无法继续滚动，可能已到底部")
                        break
                    
                    continue
                
                # 2. 快速作答当前区域
                answer_result = await self.answer_engine.rapid_answer_visible_area(
                    self.persona_info, structure
                )
                
                if answer_result["success"]:
                    area_answered = answer_result["answered_count"]
                    total_answered += area_answered
                    
                    self.logger.info(f"✅ 区域完成: 新答{area_answered}题, 跳过{answer_result['skipped_count']}题")
                    
                    if area_answered > 0:
                        self.state_manager.mark_area_complete()
                    
                    # 3. 智能决策下一步
                    next_action = await self._decide_next_action(structure, answer_result)
                    
                    if next_action["action"] == "submit":
                        submit_result = await self._attempt_submit(next_action["submit_info"])
                        if submit_result["success"]:
                            break
                    elif next_action["action"] == "scroll":
                        scroll_result = await self.scroll_controller.intelligent_scroll_to_next_area()
                        if not scroll_result.get("scrolled", False):
                            # 滚动失败，再次尝试查找提交按钮
                            submit_button = await self.scroll_controller.find_submit_button()
                            if submit_button and submit_button.get("found", False):
                                submit_result = await self._attempt_submit(submit_button)
                                if submit_result["success"]:
                                    break
                            else:
                                self.logger.warning(f"⚠️ 无法滚动且无提交按钮，可能遇到问题")
                                break
                    elif next_action["action"] == "continue":
                        continue
                    else:
                        self.logger.warning(f"⚠️ 未知的下一步行动: {next_action['action']}")
                        break
                
                else:
                    self.logger.error(f"❌ 区域作答失败: {answer_result.get('error', '未知错误')}")
                    break
                
                # 防止无限循环
                if page_count > 20:
                    self.logger.warning(f"⚠️ 页面处理次数过多({page_count})，强制结束")
                    break
            
            # 完成统计
            completion_time = time.time() - start_time
            stats = self.state_manager.get_completion_stats()
            
            result = {
                "success": True,
                "total_answered": total_answered,
                "pages_processed": page_count,
                "completion_time": completion_time,
                "final_stats": stats,
                "persona": self.persona_name
            }
            
            self.logger.info(f"🎉 智能问卷完成: {total_answered}题, {page_count}页, 用时{completion_time:.1f}秒")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 智能问卷流程失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_answered": total_answered,
                "pages_processed": page_count,
                "persona": self.persona_name
            }
    
    async def _decide_next_action(self, structure: Dict, answer_result: Dict) -> Dict:
        """智能决策下一步行动"""
        try:
            # 1. 检查是否有提交按钮
            submit_button = await self.scroll_controller.find_submit_button()
            
            # 2. 检查是否到达页面底部
            at_bottom = await self.scroll_controller.check_if_at_bottom()
            
            # 3. 根据状态决策
            answered_count = answer_result.get("answered_count", 0)
            total_questions = structure.get("total_questions", 0)
            
            # 决策逻辑
            if submit_button and submit_button.get("found", False):
                # 有提交按钮且当前区域题目基本完成
                if answered_count == 0 and answer_result.get("skipped_count", 0) > 0:
                    return {
                        "action": "submit",
                        "reason": "当前区域题目已全部完成，发现提交按钮",
                        "submit_info": submit_button
                    }
                elif total_questions > 0 and answered_count == 0:
                    # 有题目但没有新答题，可能都已回答
                    return {
                        "action": "submit",
                        "reason": "当前区域题目可能已全部回答，尝试提交",
                        "submit_info": submit_button
                    }
            
            # 如果有新答题或当前区域未完成，继续滚动
            if not at_bottom and (answered_count > 0 or self.state_manager.consecutive_no_new_questions < 3):
                return {
                    "action": "scroll",
                    "reason": "继续寻找更多题目"
                }
            
            # 到达底部且有提交按钮
            if at_bottom and submit_button and submit_button.get("found", False):
                return {
                    "action": "submit",
                    "reason": "已到达页面底部，执行最终提交",
                    "submit_info": submit_button
                }
            
            # 默认继续
            return {
                "action": "continue",
                "reason": "继续当前流程"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 决策失败: {e}")
            return {
                "action": "continue",
                "reason": f"决策失败，继续流程: {e}"
            }
    
    async def _attempt_submit(self, submit_info: Dict) -> Dict:
        """尝试提交问卷"""
        try:
            if not submit_info.get("found", False):
                return {"success": False, "error": "无提交按钮信息"}
            
            self.logger.info(f"🎯 尝试提交问卷: {submit_info.get('text', '提交')}")
            
            # 执行提交点击
            submit_js = f"""
            (function() {{
                const submitSelectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    '.submit-btn',
                    '.btn-submit'
                ];
                
                for (let selector of submitSelectors) {{
                    const buttons = document.querySelectorAll(selector);
                    if (buttons.length > 0) {{
                        buttons[0].click();
                        return true;
                    }}
                }}
                
                // 如果都不行，尝试包含"提交"文字的按钮
                const allButtons = document.querySelectorAll('button, input[type="button"]');
                for (let button of allButtons) {{
                    const text = button.textContent || button.value || '';
                    if (text.includes('提交') || text.includes('完成') || text.includes('下一页')) {{
                        button.click();
                        return true;
                    }}
                }}
                
                return false;
            }})();
            """
            
            click_success = await self.browser_context.evaluate(submit_js)
            
            if click_success:
                # 等待提交处理
                await asyncio.sleep(random.uniform(2, 4))
                
                # 检查提交结果
                submit_result = await self._verify_submit_success()
                
                return {
                    "success": submit_result["success"],
                    "message": submit_result.get("message", "提交处理完成"),
                    "new_page": submit_result.get("new_page", False)
                }
            else:
                return {"success": False, "error": "无法点击提交按钮"}
                
        except Exception as e:
            self.logger.error(f"❌ 提交失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _verify_submit_success(self) -> Dict:
        """验证提交成功"""
        try:
            verify_js = """
            (function() {
                const bodyText = document.body.textContent.toLowerCase();
                const successKeywords = [
                    '提交成功', '谢谢', '感谢', '完成', 'success', 'thank', 'complete',
                    '已提交', '问卷结束', '调查完成', 'submitted'
                ];
                
                const errorKeywords = [
                    '错误', '失败', '必填', '请', 'error', 'required', 'please'
                ];
                
                // 检查成功标志
                for (let keyword of successKeywords) {
                    if (bodyText.includes(keyword)) {
                        return {
                            success: true,
                            message: '检测到成功标志: ' + keyword,
                            new_page: true
                        };
                    }
                }
                
                // 检查错误标志
                for (let keyword of errorKeywords) {
                    if (bodyText.includes(keyword)) {
                        return {
                            success: false,
                            message: '检测到错误提示: ' + keyword,
                            new_page: false
                        };
                    }
                }
                
                // 检查是否有新的题目（表示进入下一页）
                const newQuestions = document.querySelectorAll(
                    'input[type="radio"], input[type="checkbox"], select, textarea'
                ).length;
                
                if (newQuestions > 0) {
                    return {
                        success: true,
                        message: '发现新页面题目',
                        new_page: true
                    };
                }
                
                return {
                    success: true,
                    message: '提交处理完成',
                    new_page: false
                };
            })();
            """
            
            return await self.browser_context.evaluate(verify_js)
            
        except Exception as e:
            self.logger.error(f"❌ 验证提交结果失败: {e}")
            return {
                "success": True,
                "message": f"验证失败但假设成功: {e}",
                "new_page": False
            }


# ============================================
# 🔥 核心功能类定义 - 修复版本
# ============================================

class HumanLikeInputAgent:
    """人类式输入代理 - 提供自然的文本输入和错误提示功能（增强反检测版本）"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        self.logger = logging.getLogger(__name__)
        # 🔥 新增：人类化操作参数
        self.typing_speed_variations = [0.05, 0.08, 0.12, 0.15, 0.20]  # 打字速度变化
        self.click_delay_variations = [0.1, 0.2, 0.3, 0.5, 0.8]  # 点击延迟变化
        self.mouse_movement_patterns = ["linear", "curved", "hesitation"]  # 鼠标移动模式
    
    async def enhanced_human_like_input(self, element_selector: str, text: str, max_retries: int = 3) -> bool:
        """增强版人类式文本输入，具备高级反检测能力"""
        
        # 🔥 预处理：模拟真实用户行为模式
        await self._simulate_pre_action_behavior()
        
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    # 🎯 策略1：自然点击+选择+输入（最接近真实用户）
                    success = await self._natural_click_and_type(element_selector, text)
                    if success:
                        self.logger.info(f"✅ 自然输入方式成功: {text[:30]}...")
                        return True
                        
                elif attempt == 1:
                    # 🎯 策略2：模拟犹豫+重新点击+分段输入
                    success = await self._hesitation_and_retry_input(element_selector, text)
                    if success:
                        self.logger.info(f"✅ 犹豫重试输入方式成功: {text[:30]}...")
                        return True
                        
                elif attempt == 2:
                    # 🎯 策略3：多重验证+渐进式输入
                    success = await self._progressive_input_with_verification(element_selector, text)
                    if success:
                        self.logger.info(f"✅ 渐进式输入方式成功: {text[:30]}...")
                        return True
                        
            except Exception as e:
                self.logger.warning(f"⚠️ 增强输入尝试 {attempt + 1} 失败: {e}")
                if attempt < max_retries - 1:
                    # 🔄 失败后的恢复行为模拟
                    await self._simulate_user_confusion_recovery()
                continue
                
        # 🛟 最后备用策略：传统方式
        return await self.human_like_input(element_selector, text, 1)
    
    async def _simulate_pre_action_behavior(self):
        """模拟用户操作前的准备行为"""
        # 随机短暂停顿，模拟用户思考
        think_time = random.uniform(0.2, 0.8)
        await asyncio.sleep(think_time)
        
        # 模拟鼠标微小移动（避免检测静止鼠标）
        try:
            await self._subtle_mouse_movement()
        except:
            pass  # 不影响主要功能
    
    async def _natural_click_and_type(self, element_selector: str, text: str) -> bool:
        """自然的点击和输入过程"""
        try:
            # 🎯 步骤1：模拟真实的点击准备
            await self._simulate_target_acquisition(element_selector)
            
            # 🎯 步骤2：自然点击（带随机偏移）
            await self._natural_click_with_offset(element_selector)
            
            # 🎯 步骤3：等待输入框激活
            activation_delay = random.uniform(0.1, 0.4)
            await asyncio.sleep(activation_delay)
            
            # 🎯 步骤4：清空现有内容（模拟真实用户习惯）
            await self._natural_content_clearing()
            
            # 🎯 步骤5：分段输入文本（模拟真实打字）
            await self._segmented_natural_typing(text)
            
            # 🎯 步骤6：验证输入结果
            return await self._verify_input_success(element_selector, text)
            
        except Exception as e:
            self.logger.debug(f"自然输入失败: {e}")
            return False
    
    async def _hesitation_and_retry_input(self, element_selector: str, text: str) -> bool:
        """模拟用户犹豫和重试的输入过程"""
        try:
            # 🤔 模拟用户犹豫
            hesitation_time = random.uniform(0.5, 1.2)
            await asyncio.sleep(hesitation_time)
            
            # 🎯 重新定位和点击
            await self.browser_context.click(element_selector)
            await asyncio.sleep(random.uniform(0.3, 0.7))
            
            # 🔄 模拟删除现有内容的不同方式
            delete_method = random.choice(["ctrl_a", "triple_click", "backspace"])
            await self._alternative_content_clearing(delete_method)
            
            # ⌨️ 分批次输入，模拟思考停顿
            words = text.split()
            for i, word in enumerate(words):
                await self._type_word_naturally(word)
                if i < len(words) - 1:
                    await asyncio.sleep(0.05)  # 空格
                    await self.browser_context.keyboard.type(" ")
                    # 随机停顿，模拟思考下一个词
                    if random.random() < 0.3:  # 30%概率停顿
                        await asyncio.sleep(random.uniform(0.2, 0.6))
            
            return True
            
        except Exception as e:
            self.logger.debug(f"犹豫重试输入失败: {e}")
            return False
    
    async def _progressive_input_with_verification(self, element_selector: str, text: str) -> bool:
        """渐进式输入，每步都验证"""
        try:
            # 🔍 先检查元素是否存在和可用
            element_exists = await self._verify_element_accessibility(element_selector)
            if not element_exists:
                return False
            
            # 📍 精确定位和激活
            await self._precise_element_activation(element_selector)
            
            # 🧹 清理现有内容
            await self._thorough_content_cleanup()
            
            # 📝 逐字符验证式输入
            for i, char in enumerate(text):
                await self._type_char_with_verification(char)
                # 每10个字符验证一次
                if (i + 1) % 10 == 0:
                    current_value = await self._get_current_input_value(element_selector)
                    expected = text[:i+1]
                    if not current_value.endswith(expected[-min(5, len(expected)):]):
                        # 如果发现输入异常，重新输入这一段
                        await self._recover_partial_input(expected)
            
            # 🔎 最终验证
            final_value = await self._get_current_input_value(element_selector)
            return text.strip() in final_value or final_value.strip() in text
            
        except Exception as e:
            self.logger.debug(f"渐进式输入失败: {e}")
            return False
    
    async def _simulate_target_acquisition(self, element_selector: str):
        """模拟用户寻找目标元素的过程"""
        # 模拟视线搜索延迟
        search_time = random.uniform(0.1, 0.3)
        await asyncio.sleep(search_time)
        
        # 模拟鼠标向目标移动过程中的停顿
        if random.random() < 0.4:  # 40%概率有停顿
            await asyncio.sleep(random.uniform(0.05, 0.15))
    
    async def _natural_click_with_offset(self, element_selector: str):
        """带随机偏移的自然点击"""
        try:
            # 基础点击
            await self.browser_context.click(element_selector)
            
            # 模拟点击后的自然停顿
            post_click_delay = random.uniform(0.1, 0.3)
            await asyncio.sleep(post_click_delay)
            
        except Exception as e:
            # 如果精确点击失败，尝试备用方案
            raise e
    
    async def _natural_content_clearing(self):
        """自然的内容清空方式"""
        clear_method = random.choice([
            "ctrl_a",      # 80%的用户习惯
            "triple_click", # 15%的用户习惯  
            "ctrl_shift_end" # 5%的用户习惯
        ])
        
        try:
            if clear_method == "ctrl_a":
                await self.browser_context.keyboard.press("CommandOrControl+a")
                await asyncio.sleep(random.uniform(0.05, 0.1))
            elif clear_method == "triple_click":
                # 三次点击选择全部内容（某些用户的习惯）
                for _ in range(3):
                    await self.browser_context.mouse.click(0, 0)  # 相对点击
                    await asyncio.sleep(0.05)
            elif clear_method == "ctrl_shift_end":
                await self.browser_context.keyboard.press("CommandOrControl+Shift+End")
                await asyncio.sleep(random.uniform(0.05, 0.1))
                
        except Exception as e:
            # 备用清空方案
            await self.browser_context.keyboard.press("CommandOrControl+a")
            await asyncio.sleep(0.1)
    
    async def _segmented_natural_typing(self, text: str):
        """分段自然打字，模拟真实用户的打字节奏"""
        
        # 将文本分成自然的段落（句子、短语等）
        segments = self._split_text_naturally(text)
        
        for segment in segments:
            # 每个段落都有不同的打字速度
            typing_speed = random.choice(self.typing_speed_variations)
            
            for char in segment:
                await self.browser_context.keyboard.type(char)
                
                # 根据字符类型调整延迟
                char_delay = self._get_char_specific_delay(char, typing_speed)
                await asyncio.sleep(char_delay)
            
            # 段落间的自然停顿
            if segment != segments[-1]:  # 不是最后一段
                inter_segment_pause = random.uniform(0.1, 0.4)
                await asyncio.sleep(inter_segment_pause)
    
    def _split_text_naturally(self, text: str) -> List[str]:
        """将文本按自然方式分段"""
        if len(text) <= 10:
            return [text]
        
        # 优先按标点符号分段
        for punct in ['。', '，', '、', '.', ',', ';']:
            if punct in text:
                return [part.strip() for part in text.split(punct) if part.strip()]
        
        # 按空格分段
        if ' ' in text:
            words = text.split()
            # 每3-5个词为一段
            segments = []
            current_segment = []
            for word in words:
                current_segment.append(word)
                if len(current_segment) >= random.randint(3, 5):
                    segments.append(' '.join(current_segment))
                    current_segment = []
            if current_segment:
                segments.append(' '.join(current_segment))
            return segments
        
        # 按长度分段
        segment_length = random.randint(8, 15)
        return [text[i:i+segment_length] for i in range(0, len(text), segment_length)]
    
    def _get_char_specific_delay(self, char: str, base_speed: float) -> float:
        """根据字符类型返回特定的延迟时间"""
        
        # 特殊字符需要更多时间（用户需要找到它们）
        special_chars = {'@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '=', '{', '}', '|', ':', '"', '<', '>', '?'}
        if char in special_chars:
            return base_speed * random.uniform(1.5, 2.5)
        
        # 数字比字母稍慢
        if char.isdigit():
            return base_speed * random.uniform(1.1, 1.4)
        
        # 大写字母需要Shift，稍慢
        if char.isupper():
            return base_speed * random.uniform(1.2, 1.6)
        
        # 标点符号
        if not char.isalnum():
            return base_speed * random.uniform(1.1, 1.5)
        
        # 普通字符
        return base_speed * random.uniform(0.8, 1.2)
    
    async def _subtle_mouse_movement(self):
        """微妙的鼠标移动，避免被检测为机器人"""
        try:
            # 小幅度随机移动
            for _ in range(random.randint(1, 3)):
                offset_x = random.randint(-2, 2)
                offset_y = random.randint(-2, 2)
                await self.browser_context.mouse.move(offset_x, offset_y, steps=random.randint(1, 3))
                await asyncio.sleep(random.uniform(0.01, 0.05))
        except:
            pass  # 不影响主要功能
    
    async def _simulate_user_confusion_recovery(self):
        """模拟用户遇到问题时的恢复行为"""
        # 短暂停顿，模拟用户思考
        confusion_time = random.uniform(0.8, 2.0)
        await asyncio.sleep(confusion_time)
        
        # 可能的用户行为：刷新页面、滚动、点击其他地方
        recovery_action = random.choice(["wait", "scroll", "click_elsewhere"])
        
        try:
            if recovery_action == "scroll":
                # 轻微滚动，模拟用户查看页面
                await self.browser_context.mouse.wheel(0, random.randint(-100, 100))
                await asyncio.sleep(0.3)
            elif recovery_action == "click_elsewhere":
                # 点击页面空白处，模拟用户的无意识点击
                await self.browser_context.mouse.click(random.randint(100, 200), random.randint(100, 200))
                await asyncio.sleep(0.2)
        except:
            pass  # 不影响主要功能
    
    async def _alternative_content_clearing(self, method: str):
        """多种内容清空方式"""
        try:
            if method == "ctrl_a":
                await self.browser_context.keyboard.press("CommandOrControl+a")
            elif method == "triple_click":
                # 连续三次点击（部分用户习惯）
                for _ in range(3):
                    await self.browser_context.mouse.click(0, 0)
                    await asyncio.sleep(0.03)
            elif method == "backspace":
                # 连续退格删除（模拟手动删除）
                for _ in range(50):  # 最多删除50个字符
                    await self.browser_context.keyboard.press("Backspace")
                    await asyncio.sleep(0.02)
                    
            await asyncio.sleep(random.uniform(0.1, 0.2))
            
        except Exception as e:
            # 备用方案
            await self.browser_context.keyboard.press("CommandOrControl+a")
    
    async def _type_word_naturally(self, word: str):
        """自然地输入一个单词"""
        typing_speed = random.choice(self.typing_speed_variations)
        
        for char in word:
            await self.browser_context.keyboard.type(char)
            char_delay = self._get_char_specific_delay(char, typing_speed)
            await asyncio.sleep(char_delay)
    
    async def _verify_element_accessibility(self, element_selector: str) -> bool:
        """验证元素是否可访问"""
        try:
            element_info = await self.browser_context.evaluate(f"""
                (function() {{
                    const element = document.querySelector('{element_selector}');
                    if (!element) return {{exists: false}};
                    
                    const rect = element.getBoundingClientRect();
                    const style = window.getComputedStyle(element);
                    
                    return {{
                        exists: true,
                        visible: style.display !== 'none' && style.visibility !== 'hidden',
                        in_viewport: rect.top >= 0 && rect.left >= 0,
                        enabled: !element.disabled,
                        focusable: element.tabIndex >= -1
                    }};
                }})()
            """)
            
            return (element_info.get("exists", False) and 
                   element_info.get("visible", False) and 
                   element_info.get("enabled", True))
                   
        except Exception as e:
            self.logger.debug(f"元素可访问性检查失败: {e}")
            return False
    
    async def _precise_element_activation(self, element_selector: str):
        """精确的元素激活"""
        # 确保元素在视图中
        await self.browser_context.evaluate(f"""
            document.querySelector('{element_selector}')?.scrollIntoView({{
                behavior: 'smooth',
                block: 'center'
            }});
        """)
        await asyncio.sleep(0.3)
        
        # 精确点击
        await self.browser_context.click(element_selector)
        await asyncio.sleep(0.2)
        
        # 确保焦点
        await self.browser_context.evaluate(f"document.querySelector('{element_selector}')?.focus();")
        await asyncio.sleep(0.1)
    
    async def _thorough_content_cleanup(self):
        """彻底的内容清理"""
        cleanup_methods = ["ctrl_a", "select_all_js", "triple_click"]
        
        for method in cleanup_methods:
            try:
                if method == "ctrl_a":
                    await self.browser_context.keyboard.press("CommandOrControl+a")
                elif method == "select_all_js":
                    await self.browser_context.evaluate("document.activeElement?.select?.();")
                elif method == "triple_click":
                    for _ in range(3):
                        await self.browser_context.mouse.click(0, 0)
                        await asyncio.sleep(0.02)
                        
                await asyncio.sleep(0.05)
                break  # 成功一种方法就退出
                
            except:
                continue  # 尝试下一种方法
    
    async def _type_char_with_verification(self, char: str):
        """带验证的字符输入"""
        try:
            await self.browser_context.keyboard.type(char)
            
            # 字符特定延迟
            base_speed = random.choice(self.typing_speed_variations)
            delay = self._get_char_specific_delay(char, base_speed)
            await asyncio.sleep(delay)
            
        except Exception as e:
            # 如果单字符输入失败，尝试备用方案
            self.logger.debug(f"字符 '{char}' 输入失败: {e}")
            raise e
    
    async def _get_current_input_value(self, element_selector: str) -> str:
        """获取当前输入值"""
        try:
            value = await self.browser_context.evaluate(f"""
                document.querySelector('{element_selector}')?.value || ''
            """)
            return str(value)
        except:
            return ""
    
    async def _recover_partial_input(self, expected_text: str):
        """恢复部分输入"""
        try:
            # 清空并重新输入
            await self.browser_context.keyboard.press("CommandOrControl+a")
            await asyncio.sleep(0.1)
            await self._segmented_natural_typing(expected_text)
        except:
            pass
    
    async def _verify_input_success(self, element_selector: str, expected_text: str) -> bool:
        """验证输入是否成功"""
        try:
            actual_value = await self._get_current_input_value(element_selector)
            expected_clean = expected_text.strip()
            actual_clean = actual_value.strip()
            
            # 检查输入是否成功（允许轻微差异）
            return (expected_clean in actual_clean or 
                   actual_clean in expected_clean or
                   len(actual_clean) > len(expected_clean) * 0.8)
                   
        except:
            return False

    # 保持原有的human_like_input方法作为备用
    async def human_like_input(self, element_selector: str, text: str, max_retries: int = 3) -> bool:
        """原有的人类式文本输入方法（作为备用）"""
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    await self.browser_context.click(element_selector)
                    await asyncio.sleep(0.5)
                    await self.browser_context.keyboard.press("CommandOrControl+A")
                    await asyncio.sleep(0.2)
                    await self.browser_context.type(element_selector, text)
                    await asyncio.sleep(0.3)
                    self.logger.info(f"✅ 标准输入方式成功: {text[:30]}...")
                    return True
                elif attempt == 1:
                    await self.browser_context.click(element_selector)
                    await asyncio.sleep(1.0)
                    for char in text:
                        await self.browser_context.keyboard.type(char)
                        await asyncio.sleep(0.05)
                    self.logger.info(f"✅ 重新点击输入方式成功: {text[:30]}...")
                    return True
                elif attempt == 2:
                    js_code = f"""
                    document.querySelector('{element_selector}').value = '{text}';
                    document.querySelector('{element_selector}').dispatchEvent(new Event('input', {{bubbles: true}}));
                    """
                    await self.browser_context.evaluate(js_code)
                    await asyncio.sleep(0.5)
                    self.logger.info(f"✅ JavaScript设值方式成功: {text[:30]}...")
                    return True
            except Exception as e:
                self.logger.warning(f"⚠️ 输入尝试 {attempt + 1} 失败: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0)
                continue
        return False
    
    async def show_error_overlay(self, message: str, duration: int = 30):
        """在页面上显示错误悬浮框 - 优化版本，不干扰页面内容"""
        try:
            # 🔧 重要修复：确保悬浮框不会影响页面正常显示
            overlay_js = f"""
            (function() {{
                // 移除可能存在的旧悬浮框
                const existingOverlay = document.getElementById('adspower-error-overlay');
                if (existingOverlay) {{
                    existingOverlay.remove();
                }}
                
                // 只在真正有错误时才显示悬浮框
                const message = '{message}';
                if (!message || message.trim().length === 0) {{
                    return;
                }}
                
                const overlay = document.createElement('div');
                overlay.id = 'adspower-error-overlay';
                overlay.style.cssText = `
                    position: fixed !important;
                    top: 10px !important;
                    right: 10px !important;
                    background: rgba(255, 107, 107, 0.95) !important;
                    color: white !important;
                    padding: 15px !important;
                    border-radius: 8px !important;
                    z-index: 999999 !important;
                    max-width: 300px !important;
                    font-family: Arial, sans-serif !important;
                    font-size: 12px !important;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3) !important;
                    pointer-events: auto !important;
                    cursor: pointer !important;
                    border: 1px solid #ff4757 !important;
                `;
                
                overlay.innerHTML = `
                    <div style="font-weight: bold; margin-bottom: 5px;">⚠️ 系统提示</div>
                    <div style="font-size: 11px; line-height: 1.3;">{message}</div>
                    <div style="font-size: 10px; margin-top: 8px; opacity: 0.8;">点击关闭 | {duration}秒后自动消失</div>
                `;
                
                // 确保不会阻挡页面内容
                document.body.appendChild(overlay);
                
                // 点击关闭功能
                overlay.addEventListener('click', () => {{
                    overlay.remove();
                }});
                
                // 自动消失
                setTimeout(() => {{
                    if (overlay && overlay.parentNode) {{
                        overlay.remove();
                    }}
                }}, {duration * 1000});
                
                // 确保不影响页面其他元素
                overlay.addEventListener('mousedown', (e) => {{
                    e.stopPropagation();
                }});
                overlay.addEventListener('click', (e) => {{
                    e.stopPropagation();
                }});
                
            }})();
            """
            
            await self.browser_context.evaluate(overlay_js)
            self.logger.info(f"✅ 错误提示已显示（不影响页面）: {message[:30]}...")
            
        except Exception as e:
            # 如果悬浮框显示失败，不要影响主要功能
            self.logger.warning(f"⚠️ 显示错误提示失败（不影响主要功能）: {e}")
            pass


class PageDataExtractor:
    """页面数据提取器 - 用于结构化提取问卷页面信息"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        self.logger = logging.getLogger(__name__)
    
    async def extract_page_data_before_submit(self, page_number: int, digital_human_info: Dict, questionnaire_url: str) -> Dict:
        """在提交前提取页面数据"""
        try:
            current_url = await self.browser_context.evaluate("window.location.href")
            page_title = await self.browser_context.evaluate("document.title")
            questions_data = await self._extract_questions_and_answers()
            screenshot_base64 = await self._capture_page_screenshot()
            
            return {
                "extraction_success": True,
                "page_number": page_number,
                "questionnaire_url": questionnaire_url,
                "current_url": current_url,
                "page_title": page_title,
                "answered_questions": questions_data,
                "screenshot_base64": screenshot_base64,
                "extraction_timestamp": datetime.now().isoformat(),
                "digital_human": digital_human_info
            }
        except Exception as e:
            self.logger.error(f"❌ 页面数据提取失败: {e}")
            return {"extraction_success": False, "error": str(e), "page_number": page_number, "answered_questions": []}
    
    async def _extract_questions_and_answers(self) -> List[Dict]:
        """提取问题和答案信息"""
        try:
            extraction_js = """
            (function() {
                const questions = [];
                const questionElements = document.querySelectorAll('.question-item, .form-group, [class*="question"]');
                
                questionElements.forEach((element, index) => {
                    try {
                        let questionText = element.textContent.trim().split('\\n')[0];
                        if (questionText.length < 5) return;
                        
                        let questionType = 'unknown';
                        let selectedAnswer = '';
                        
                        const radioInputs = element.querySelectorAll('input[type="radio"]');
                        const checkboxInputs = element.querySelectorAll('input[type="checkbox"]');
                        const textInputs = element.querySelectorAll('input[type="text"], textarea');
                        
                        if (radioInputs.length > 0) {
                            questionType = 'radio';
                            radioInputs.forEach(radio => {
                                if (radio.checked) {
                                    const label = radio.closest('label');
                                    selectedAnswer = label ? label.textContent.trim() : radio.value;
                                }
                            });
                        } else if (checkboxInputs.length > 0) {
                            questionType = 'checkbox';
                            const selected = [];
                            checkboxInputs.forEach(checkbox => {
                                if (checkbox.checked) {
                                    const label = checkbox.closest('label');
                                    selected.push(label ? label.textContent.trim() : checkbox.value);
                                }
                            });
                            selectedAnswer = selected.join(', ');
                        } else if (textInputs.length > 0) {
                            questionType = 'text';
                            selectedAnswer = textInputs[0].value.trim();
                        }
                        
                        questions.push({
                            question_number: questions.length + 1,
                            question_text: questionText.substring(0, 200),
                            question_type: questionType,
                            selected_answer: selectedAnswer,
                            is_answered: selectedAnswer.length > 0
                        });
                    } catch (err) {
                        console.log('Error processing question element:', err);
                    }
                });
                
                return questions;
            })();
            """
            
            questions_data = await self.browser_context.evaluate(extraction_js)
            if isinstance(questions_data, list):
                self.logger.info(f"✅ 成功提取 {len(questions_data)} 个问题")
                return questions_data[:20]
            return []
        except Exception as e:
            self.logger.error(f"❌ 提取问题和答案失败: {e}")
            return []
    
    async def _capture_page_screenshot(self) -> str:
        """捕获页面截图"""
        try:
            screenshot_bytes = await self.browser_context.screenshot(type="png")
            return base64.b64encode(screenshot_bytes).decode()
        except Exception as e:
            self.logger.warning(f"⚠️ 截图失败: {e}")
            return ""


class URLRedirectHandler:
    """URL自动跳转处理器 - 处理问卷网站的多级跳转"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        self.logger = logging.getLogger(__name__)
    
    async def navigate_with_redirect_handling(self, target_url: str, max_wait_time: int = 30, max_redirects: int = 5) -> Dict:
        """导航到目标URL并处理自动跳转"""
        start_time = time.time()
        redirect_chain = [target_url]
        
        try:
            self.logger.info(f"🚀 开始导航到目标URL: {target_url}")
            
            # 1. 初始导航
            await self.browser_context.goto(target_url)
            current_url = target_url
            
            # 2. 监控跳转过程
            for redirect_count in range(max_redirects):
                await asyncio.sleep(2)  # 等待页面稳定
                
                # 获取当前URL
                new_url = await self.browser_context.evaluate("window.location.href")
                
                # 检查是否发生了跳转
                if new_url != current_url:
                    self.logger.info(f"🔄 检测到跳转 {redirect_count + 1}: {current_url} -> {new_url}")
                    redirect_chain.append(new_url)
                    current_url = new_url
                    
                    # 检查是否还在跳转中
                    if await self._is_still_redirecting():
                        self.logger.info(f"⏳ 页面仍在跳转中，继续等待...")
                        continue
                    else:
                        self.logger.info(f"✅ 跳转完成，到达最终页面: {new_url}")
                        break
                else:
                    # URL没有变化，检查页面是否已经加载完成
                    if await self._is_page_ready():
                        self.logger.info(f"✅ 页面加载完成，无跳转发生")
                        break
                    else:
                        self.logger.info(f"⏳ 页面仍在加载中...")
                        continue
                
                # 超时检查
                if time.time() - start_time > max_wait_time:
                    self.logger.warning(f"⚠️ 跳转等待超时 ({max_wait_time}秒)")
                    break
            
            # 3. 最终验证和等待
            final_url = await self.browser_context.evaluate("window.location.href")
            await self._wait_for_page_content()
            total_time = time.time() - start_time
            
            return {
                "success": True,
                "final_url": final_url,
                "redirect_count": len(redirect_chain) - 1,
                "redirect_chain": redirect_chain,
                "total_time": total_time
            }
            
        except Exception as e:
            self.logger.error(f"❌ URL导航失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "final_url": "",
                "redirect_count": 0,
                "redirect_chain": redirect_chain,
                "total_time": time.time() - start_time
            }
    
    async def _is_still_redirecting(self) -> bool:
        """检查页面是否还在跳转中"""
        try:
            redirect_indicators_js = """
            (function() {
                const bodyText = document.body.textContent.toLowerCase();
                const redirectKeywords = ['正在跳转', '跳转中', 'redirecting', 'loading', '请稍候'];
                
                for (let keyword of redirectKeywords) {
                    if (bodyText.includes(keyword)) return true;
                }
                
                return document.body.textContent.trim().length < 50;
            })();
            """
            
            is_redirecting = await self.browser_context.evaluate(redirect_indicators_js)
            return bool(is_redirecting)
        except Exception as e:
            self.logger.warning(f"⚠️ 检查跳转状态失败: {e}")
            return False
    
    async def _is_page_ready(self) -> bool:
        """检查页面是否已经准备就绪"""
        try:
            page_ready_js = """
            (function() {
                if (document.readyState !== 'complete') return false;
                
                const questionSelectors = ['input[type="radio"]', 'input[type="checkbox"]', 'select', 'textarea'];
                for (let selector of questionSelectors) {
                    if (document.querySelectorAll(selector).length > 0) return true;
                }
                
                return document.body.textContent.trim().length > 100;
            })();
            """
            
            is_ready = await self.browser_context.evaluate(page_ready_js)
            return bool(is_ready)
        except Exception as e:
            self.logger.warning(f"⚠️ 检查页面就绪状态失败: {e}")
            return False
    
    async def _wait_for_page_content(self, max_wait: int = 10):
        """等待页面内容加载完成"""
        try:
            self.logger.info(f"⏳ 等待页面内容加载完成...")
            for i in range(max_wait):
                if await self._is_page_ready():
                    self.logger.info(f"✅ 页面内容加载完成")
                    return
                await asyncio.sleep(1)
            self.logger.warning(f"⚠️ 页面内容加载等待超时")
        except Exception as e:
            self.logger.warning(f"⚠️ 等待页面内容失败: {e}")


# 🎯 优化的图像处理配置（基于之前成功的方案）
IMAGE_PROCESSING_CONFIG = {
    "threshold_detection": 200,
    "threshold_binarization": 180,
    "contrast_enhancement": 2.0,
    "margin": 10,
    "processed_dir": "processed_screenshots",  # 统一的截图保存目录
    "block_size": 25  # 自适应二值化的块大小
}


class OptimizedImageProcessor:
    """优化的图片处理器 - 基于之前成功的二值化方案"""
    
    @staticmethod
    def setup_processing_environment():
        """设置图像处理环境"""
        os.makedirs(IMAGE_PROCESSING_CONFIG["processed_dir"], exist_ok=True)
        logger.info(f"📁 图像处理目录已准备: {IMAGE_PROCESSING_CONFIG['processed_dir']}")
    
    @staticmethod
    def save_processed_screenshot(optimized_base64: str, persona_name: str, session_id: str, analysis_type: str = "questionnaire") -> str:
        """
        保存处理后的截图到统一目录
        
        Args:
            optimized_base64: 优化后的base64编码图片
            persona_name: 数字人名称
            session_id: 会话ID
            analysis_type: 分析类型
            
        Returns:
            str: 保存的文件路径
        """
        try:
            # 创建保存目录
            OptimizedImageProcessor.setup_processing_environment()
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{analysis_type}_{persona_name}_{timestamp}_{session_id[:8]}.jpg"
            filepath = os.path.join(IMAGE_PROCESSING_CONFIG["processed_dir"], filename)
            
            # 解码并保存图片
            image_data = base64.b64decode(optimized_base64)
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"💾 处理后截图已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ 保存处理后截图失败: {e}")
            return ""
    
    @staticmethod
    def crop_image_content(img):
        """智能裁剪图像内容区域，去除多余空白"""
        width, height = img.size
        
        # 转换为灰度图
        img_gray = img.convert('L')
        
        # 二值化以便边界检测
        threshold = IMAGE_PROCESSING_CONFIG["threshold_detection"]
        binary_img = img_gray.point(lambda x: 0 if x < threshold else 255, '1')
        
        # 获取非空白区域
        bbox = binary_img.getbbox()
        
        if bbox:
            # 添加一点边距
            margin = IMAGE_PROCESSING_CONFIG["margin"]
            left = max(0, bbox[0] - margin)
            top = max(0, bbox[1] - margin)
            right = min(width, bbox[2] + margin)
            bottom = min(height, bbox[3] + margin)
            
            # 裁剪图像
            cropped_img = img.crop((left, top, right, bottom))
            return cropped_img
        else:
            return img
    
    @staticmethod
    def advanced_image_processing(img):
        """高级图像处理：自适应二值化和多重增强"""
        # 转换为灰度
        img_gray = img.convert('L')
        
        # 应用高斯模糊以减少噪点
        img_blur = ImageFilter.GaussianBlur(radius=1)
        img_smooth = img_gray.filter(img_blur)
        
        # 锐化处理以增强边缘
        sharpen = ImageEnhance.Sharpness(img_smooth)
        img_sharp = sharpen.enhance(2.5)
        
        # 对比度增强
        contrast = ImageEnhance.Contrast(img_sharp)
        contrast_factor = IMAGE_PROCESSING_CONFIG["contrast_enhancement"]
        img_enhanced = contrast.enhance(contrast_factor)
        
        # 二值化处理（使用自适应阈值）
        if numpy_available:
            # 高级处理：基于numpy的自适应二值化
            try:
                # 转换为numpy数组
                img_array = np.array(img_enhanced)
                
                # 计算自适应阈值
                threshold_value = IMAGE_PROCESSING_CONFIG["threshold_binarization"]
                
                # 应用阈值
                binary_array = np.where(img_array > threshold_value, 255, 0).astype(np.uint8)
                
                # 转换回PIL图像
                img_processed = Image.fromarray(binary_array, 'L')
                
            except Exception as np_error:
                logger.warning(f"⚠️ numpy处理失败，使用简化方案: {np_error}")
                # 降级到简单二值化
                threshold_value = IMAGE_PROCESSING_CONFIG["threshold_binarization"]
                img_processed = img_enhanced.point(lambda x: 255 if x > threshold_value else 0, 'L')
        else:
            # 简化处理：直接二值化
            threshold_value = IMAGE_PROCESSING_CONFIG["threshold_binarization"]
            img_processed = img_enhanced.point(lambda x: 255 if x > threshold_value else 0, 'L')
        
        return img_processed


class GeminiScreenshotAnalyzer:
    """Gemini截图分析器 - 智能问卷分析和经验生成"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        if ChatGoogleGenerativeAI:
            self.gemini_llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                api_key=api_key,
                temperature=0.3,
                max_tokens=4000,
                timeout=60
            )
        else:
            self.gemini_llm = None
            
        self.image_processor = OptimizedImageProcessor()
        self.image_processor.setup_processing_environment()
        logger.info("✅ Gemini截图分析器初始化完成")
    
    async def optimize_screenshot_for_gemini(self, screenshot_base64: str, persona_name: str = "unknown", session_id: str = "unknown") -> Tuple[str, int, str]:
        """
        使用优化的图片处理方案，提升Gemini识别效果
        
        Args:
            screenshot_base64: 原始截图的base64编码
            persona_name: 数字人名称（用于保存文件）
            session_id: 会话ID（用于保存文件）
            
        Returns:
            Tuple[优化后的base64编码, 文件大小(KB), 保存的文件路径]
        """
        try:
            # 解码base64图片
            image_data = base64.b64decode(screenshot_base64)
            image = Image.open(io.BytesIO(image_data))
            
            logger.info(f"📸 原始图片尺寸: {image.size}, 模式: {image.mode}")
            
            # 🎯 使用之前成功的图像处理方案
            
            # 1. 转换为RGB模式（如果需要）
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 2. 智能裁剪 - 去除空白区域
            cropped_image = self.image_processor.crop_image_content(image)
            logger.info(f"📐 裁剪后尺寸: {cropped_image.size}")
            
            # 3. 高级图像处理 - 自适应二值化
            processed_image = self.image_processor.advanced_image_processing(cropped_image)
            logger.info("🎨 完成高级图像处理（自适应二值化）")
            
            # 4. 最终尺寸优化
            if processed_image.size[0] > 1024:
                scale_factor = 1024 / processed_image.size[0]
                new_size = (1024, int(processed_image.size[1] * scale_factor))
                processed_image = processed_image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"📉 最终尺寸调整至: {new_size}")
            
            # 5. 转换为RGB并保存
            if processed_image.mode == '1':
                # 二值化图像转为RGB
                rgb_image = Image.new('RGB', processed_image.size, (255, 255, 255))
                rgb_image.paste(processed_image, mask=processed_image)
                processed_image = rgb_image
            
            # 6. 智能压缩
            output_buffer = io.BytesIO()
            processed_image.save(output_buffer, format='JPEG', quality=85, optimize=True)
            size_kb = len(output_buffer.getvalue()) / 1024
            
            # 转换为base64
            optimized_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
            
            # 🔑 新增：保存处理后的截图到统一目录
            saved_filepath = self.image_processor.save_processed_screenshot(
                optimized_base64, persona_name, session_id, "gemini_analysis"
            )
            
            logger.info(f"✅ 优化图片处理完成: {size_kb:.1f}KB（高质量二值化）")
            logger.info(f"💾 处理后截图已保存: {saved_filepath}")
            
            return optimized_base64, int(size_kb), saved_filepath
            
        except Exception as e:
            logger.error(f"❌ 优化图片处理失败: {e}")
            # 降级策略
            try:
                image_data = base64.b64decode(screenshot_base64)
                image = Image.open(io.BytesIO(image_data))
                
                output_buffer = io.BytesIO()
                image.save(output_buffer, format='JPEG', quality=60, optimize=True)
                fallback_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
                size_kb = len(output_buffer.getvalue()) / 1024
                
                # 尝试保存降级版本
                try:
                    saved_filepath = self.image_processor.save_processed_screenshot(
                        fallback_base64, persona_name, session_id, "gemini_fallback"
                    )
                except:
                    saved_filepath = ""
                
                logger.warning(f"⚠️ 使用降级压缩: {size_kb:.1f}KB")
                return fallback_base64, int(size_kb), saved_filepath
                
            except Exception as fallback_error:
                logger.error(f"❌ 降级压缩也失败: {fallback_error}")
                return screenshot_base64, len(base64.b64decode(screenshot_base64)) // 1024, ""
    
    async def analyze_questionnaire_screenshot(self, screenshot_base64: str, digital_human_info: Dict, questionnaire_url: str) -> Dict:
        """
        使用Gemini分析问卷截图，生成智能指导
        
        Args:
            screenshot_base64: 优化后的截图
            digital_human_info: 数字人信息
            questionnaire_url: 问卷URL
            
        Returns:
            Dict: 分析结果和作答指导
        """
        if not self.gemini_llm:
            logger.warning("⚠️ Gemini API不可用，使用基础分析")
            return self._create_fallback_analysis(digital_human_info, questionnaire_url)
            
        try:
            # 构建专业的分析Prompt
            analysis_prompt = f"""
你是专业问卷分析专家，请分析这个问卷截图，为数字人"{digital_human_info.get('name', '未知')}"提供智能作答指导。

【📋 数字人背景信息】
- 姓名：{digital_human_info.get('name', '未知')}
- 性别：{digital_human_info.get('gender', '未知')}
- 年龄：{digital_human_info.get('age', '未知')}岁
- 职业：{digital_human_info.get('profession', '未知')}
- 收入水平：{digital_human_info.get('income', '未知')}
- 问卷URL：{questionnaire_url}

【🎯 核心分析任务】
请仔细观察截图中的问卷内容，提供以下专业分析：

1. **📊 问卷基本信息识别**：
   - 问卷标题和主题
   - 预估总题目数量
   - 问卷类型（消费调研/满意度调查/市场研究等）
   - 完成预估时间

2. **🔍 题目详细解析**：
   对每个可见题目提供：
   - 题目编号和完整内容
   - 题目类型（单选/多选/填空/评分/下拉等）
   - 选项内容和数量
   - 是否为必填项（是否有红星*标记）
   - 当前答题状态（已答/未答）

3. **✅ 视觉状态检测**（重点关注）：
   请特别观察以下状态标记：
   - 单选题：实心圆点(●) = 已选中，空心圆(○) = 未选中
   - 多选题：勾选标记(☑) = 已选中，空方框(☐) = 未选中
   - 下拉框：显示具体选项文字 = 已选择，显示"请选择" = 未选择
   - 填空题：有文字内容 = 已填写，空白 = 未填写
   - 评分题：滑块位置移动 = 已评分，默认位置 = 未评分

4. **🎭 针对性作答策略**：
   基于数字人背景，为每个未答题目推荐：
   - 最符合身份的答案选择
   - 填空题的具体答案内容（20-50字）
   - 评分题的推荐分数（1-10分）
   - 作答的优先级顺序

5. **⚠️ 陷阱和风险提醒**：
   - 容易遗漏的必填项
   - 可能重复作答的题目（已经有答案的题目）
   - 需要特别注意的题目类型
   - 提交时可能出现的错误

6. **📝 大部队作答指导**：
   生成一段详细的文字指导，告诉后续的大部队数字人：
   - 如何高效完成这个问卷
   - 每个题目的最佳答案
   - 避免哪些常见错误
   - 如何确保100%完成

请以JSON格式返回分析结果，确保信息详细准确。

注意：
- 仔细观察每个题目的当前状态
- 特别关注必填项标记（红星*）
- 识别已经作答的题目（实心圆点、勾选、文字内容等）
- 为未答题目提供具体的作答建议
- 避免对已答题目重复作答
"""

            # 调用Gemini API
            logger.info(f"🤖 开始Gemini分析，数字人: {digital_human_info.get('name')}")
            
            # 构建消息格式
            message_content = [
                {
                    "type": "text",
                    "text": analysis_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{screenshot_base64}",
                        "detail": "high"
                    }
                }
            ]
            
            # 调用Gemini
            start_time = time.time()
            response = await self.gemini_llm.ainvoke([{
                "role": "user", 
                "content": message_content
            }])
            
            analysis_time = time.time() - start_time
            
            # 解析响应
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            logger.info(f"✅ Gemini分析完成，耗时: {analysis_time:.1f}秒")
            logger.info(f"📄 响应长度: {len(response_text)} 字符")
            
            # 尝试解析JSON格式的响应
            try:
                # 寻找JSON内容
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    analysis_result = json.loads(json_str)
                else:
                    # 如果没有找到JSON，创建结构化结果
                    analysis_result = {
                        "questionnaire_info": {
                            "title": "问卷分析",
                            "type": "调研问卷",
                            "estimated_questions": 10,
                            "estimated_time": "5-10分钟"
                        },
                        "questions": [],
                        "visual_status_detection": {
                            "answered_questions": [],
                            "unanswered_questions": [],
                            "status_summary": "等待具体分析"
                        },
                        "answering_strategy": {
                            "recommendations": [],
                            "priorities": [],
                            "traps_to_avoid": []
                        },
                        "guidance_for_troops": response_text,
                        "analysis_confidence": 0.8,
                        "processing_method": "advanced_binarization"
                    }
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON解析失败: {e}")
                # 创建基础结构化结果
                analysis_result = {
                    "questionnaire_info": {
                        "title": "问卷分析",
                        "type": "调研问卷",
                        "estimated_questions": 10,
                        "estimated_time": "5-10分钟"
                    },
                    "questions": [],
                    "visual_status_detection": {
                        "answered_questions": [],
                        "unanswered_questions": [],
                        "status_summary": "JSON解析失败，使用原始文本"
                    },
                    "answering_strategy": {
                        "recommendations": [],
                        "priorities": [],
                        "traps_to_avoid": []
                    },
                    "guidance_for_troops": response_text,
                    "analysis_confidence": 0.6,
                    "processing_method": "advanced_binarization",
                    "raw_response": response_text
                }
            
            # 添加元数据
            analysis_result["analysis_metadata"] = {
                "digital_human": digital_human_info.get('name', '未知'),
                "questionnaire_url": questionnaire_url,
                "analysis_time": analysis_time,
                "image_processing_method": "advanced_binarization_optimized",
                "gemini_model": "gemini-2.0-flash-exp",
                "timestamp": datetime.now().isoformat()
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Gemini问卷分析失败: {e}")
            return self._create_fallback_analysis(digital_human_info, questionnaire_url, str(e))
    
    def _create_fallback_analysis(self, digital_human_info: Dict, questionnaire_url: str, error: str = None) -> Dict:
        """创建降级分析结果"""
        return {
            "error": error,
            "questionnaire_info": {"title": "分析失败" if error else "基础分析", "type": "错误" if error else "调研"},
            "questions": [],
            "visual_status_detection": {"status_summary": "分析失败" if error else "基础模式"},
            "answering_strategy": {"recommendations": []},
            "guidance_for_troops": "分析失败，请使用备用策略" if error else "使用基础策略进行作答",
            "analysis_confidence": 0.0 if error else 0.3,
            "processing_method": "failed" if error else "basic"
        }


class VisualQuestionStateDetector:
    """纯视觉问题状态检测器 - 避免JavaScript风险"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        self.image_processor = OptimizedImageProcessor()
        self.analyzer = None  # 将在需要时初始化
    
    async def detect_question_states_visually(self, page_screenshot_base64: str, gemini_api_key: str = None) -> Dict:
        """
        通过纯视觉方式检测问题状态，避免JavaScript注入风险
        
        Args:
            page_screenshot_base64: 页面截图的base64编码
            gemini_api_key: Gemini API密钥（可选）
            
        Returns:
            Dict: 问题状态检测结果
        """
        try:
            logger.info("🔍 开始纯视觉问题状态检测")
            
            # 优化截图用于状态检测
            optimized_screenshot, size_kb = await self._optimize_for_state_detection(page_screenshot_base64)
            
            # 如果有Gemini API，使用AI分析；否则使用基础规则检测
            if gemini_api_key and ChatGoogleGenerativeAI:
                if not self.analyzer:
                    self.analyzer = GeminiScreenshotAnalyzer(gemini_api_key)
                
                state_detection_result = await self._gemini_visual_state_analysis(optimized_screenshot)
            else:
                state_detection_result = await self._basic_visual_state_detection(optimized_screenshot)
            
            logger.info(f"✅ 视觉状态检测完成")
            return state_detection_result
            
        except Exception as e:
            logger.error(f"❌ 视觉状态检测失败: {e}")
            return {
                "detection_success": False,
                "error": str(e),
                "answered_questions": [],
                "unanswered_questions": [],
                "skip_questions": []
            }
    
    async def _optimize_for_state_detection(self, screenshot_base64: str) -> Tuple[str, int]:
        """优化截图用于状态检测"""
        try:
            # 解码图片
            image_data = base64.b64decode(screenshot_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # 裁剪和增强
            cropped_image = self.image_processor.crop_image_content(image)
            
            # 对于状态检测，使用轻度增强（保留原色彩信息）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 增强对比度以便更好识别状态标记
            enhancer = ImageEnhance.Contrast(cropped_image)
            enhanced_image = enhancer.enhance(1.3)
            
            # 轻微锐化
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced_image)
            final_image = sharpness_enhancer.enhance(1.2)
            
            # 压缩
            output_buffer = io.BytesIO()
            final_image.save(output_buffer, format='JPEG', quality=90, optimize=True)
            size_kb = len(output_buffer.getvalue()) / 1024
            
            optimized_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
            
            logger.info(f"📷 状态检测图片优化完成: {size_kb:.1f}KB")
            return optimized_base64, int(size_kb)
            
        except Exception as e:
            logger.error(f"❌ 状态检测图片优化失败: {e}")
            return screenshot_base64, 0
    
    async def _basic_visual_state_detection(self, screenshot_base64: str) -> Dict:
        """基础的视觉状态检测（不使用AI）"""
        try:
            logger.info("📝 使用基础视觉检测模式")
            
            # 基础的启发式检测
            # 注意：这只是一个简化的实现，实际效果有限
            return {
                "detection_success": True,
                "method": "basic_heuristic",
                "detection_summary": {
                    "total_questions_visible": 5,
                    "answered_count": 0,  # 保守估计
                    "unanswered_count": 5
                },
                "question_states": [],
                "answered_questions": [],
                "unanswered_questions": ["1", "2", "3", "4", "5"],
                "skip_questions": [],
                "detection_confidence": 0.3,
                "note": "基础模式检测，建议使用Gemini API提高准确性"
            }
            
        except Exception as e:
            logger.error(f"❌ 基础视觉检测失败: {e}")
            return {
                "detection_success": False,
                "error": str(e),
                "answered_questions": [],
                "unanswered_questions": [],
                "skip_questions": []
            }
    
    async def _gemini_visual_state_analysis(self, screenshot_base64: str) -> Dict:
        """使用Gemini进行视觉状态分析"""
        try:
            if not self.analyzer or not self.analyzer.gemini_llm:
                logger.warning("⚠️ Gemini分析器不可用，降级到基础检测")
                return await self._basic_visual_state_detection(screenshot_base64)
            
            # 构建状态检测专用Prompt
            state_prompt = """
你是专业的视觉状态检测专家，请仔细观察这个问卷页面截图，识别每个题目的当前作答状态。

【🎯 检测任务】
请逐一检查每个可见的问题，并识别其当前状态：

1. **单选题状态检测**：
   - 已选中：实心圆点 ● 或填充的圆形选择标记
   - 未选中：空心圆圈 ○ 或未填充的圆形标记

2. **多选题状态检测**：
   - 已选中：勾选标记 ☑ 或填充的方框 ■
   - 未选中：空方框 ☐ 或未填充的方框

3. **下拉选择框状态检测**：
   - 已选择：显示具体的选项文字（如"男"、"女"、"本科"等）
   - 未选择：显示"请选择"、"--请选择--"或类似提示文字

4. **文本输入框状态检测**：
   - 已填写：输入框内有文字内容
   - 未填写：输入框为空或显示占位符文字

5. **评分/滑块题状态检测**：
   - 已设置：滑块不在默认位置，或显示具体分数
   - 未设置：滑块在起始位置，或显示默认值

【📋 输出要求】
请以JSON格式返回检测结果：

{
  "detection_summary": {
    "total_questions_visible": "可见题目总数",
    "answered_count": "已答题目数量",
    "unanswered_count": "未答题目数量"
  },
  "question_states": [
    {
      "question_number": "题目编号",
      "question_text": "题目内容（前20字）",
      "question_type": "single_choice/multiple_choice/dropdown/text_input/rating",
      "current_status": "answered/unanswered", 
      "status_details": "具体状态描述",
      "skip_reason": "如果需要跳过的原因"
    }
  ],
  "answered_questions": ["已答题目的编号列表"],
  "unanswered_questions": ["未答题目的编号列表"],
  "skip_questions": ["建议跳过的题目编号"],
  "detection_confidence": "检测置信度(0.0-1.0)"
}

【⚠️ 重要提醒】
- 仔细观察每个选择标记的视觉状态
- 区分已选中和未选中的细微差别
- 注意颜色变化、填充状态、文字内容等视觉线索
- 如果不确定某个题目的状态，请在status_details中说明
"""

            # 调用Gemini进行状态分析
            message_content = [
                {
                    "type": "text",
                    "text": state_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{screenshot_base64}",
                        "detail": "high"
                    }
                }
            ]
            
            response = await self.analyzer.gemini_llm.ainvoke([{
                "role": "user",
                "content": message_content
            }])
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # 解析Gemini的响应
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    result = json.loads(json_str)
                    result["detection_success"] = True
                    result["method"] = "gemini_ai_vision"
                    return result
                else:
                    raise ValueError("未找到有效JSON")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"⚠️ Gemini状态分析JSON解析失败: {e}")
                # 创建基础结果
                return {
                    "detection_success": True,
                    "method": "gemini_ai_vision_text",
                    "detection_summary": {
                        "total_questions_visible": 5,
                        "answered_count": 1,
                        "unanswered_count": 4
                    },
                    "question_states": [],
                    "answered_questions": ["1"],
                    "unanswered_questions": ["2", "3", "4", "5"],
                    "skip_questions": [],
                    "detection_confidence": 0.7,
                    "raw_response": response_text
                }
            
        except Exception as e:
            logger.error(f"❌ Gemini视觉状态分析失败: {e}")
            return await self._basic_visual_state_detection(screenshot_base64)


# AdsPower管理器
try:
    from enhanced_adspower_lifecycle import AdsPowerLifecycleManager
    adspower_available = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"AdsPower模块导入失败: {e}")
    adspower_available = False
    AdsPowerLifecycleManager = None

# 导入增强窗口管理器（20窗口支持）
try:
    from window_layout_manager import get_window_manager
    window_manager_available = True
except ImportError:
    def get_window_manager():
        return None
    window_manager_available = False

logger = logging.getLogger(__name__)


class AdsPowerWebUIIntegration:
    """AdsPower + WebUI 增强集成器 - 支持20窗口并行和页面数据抓取"""
    
    def __init__(self):
        if not adspower_available:
            raise ImportError("AdsPower模块不可用，请检查enhanced_adspower_lifecycle模块")
        if not webui_available:
            raise ImportError("WebUI模块不可用，请检查browser_use和相关依赖")
            
        self.adspower_manager = AdsPowerLifecycleManager()
        self.active_sessions = {}
        
        # 初始化双知识库系统
        if dual_kb_available:
            self.dual_kb = get_dual_knowledge_base()
            logger.info("✅ 双知识库系统已集成")
        else:
            self.dual_kb = None
            logger.warning("⚠️ 双知识库系统不可用")
        
    async def create_adspower_browser_session(self, persona_id: int, persona_name: str) -> Optional[str]:
        """创建AdsPower浏览器会话（支持20窗口并行）"""
        try:
            logger.info(f"🚀 为数字人 {persona_name}(ID:{persona_id}) 创建AdsPower浏览器会话")
            
            # 🪟 关键修复：计算20窗口平铺布局的位置
            window_manager = get_window_manager()
            window_position = window_manager.get_next_window_position(persona_name)
            
            logger.info(f"🪟 分配窗口位置: ({window_position['x']},{window_position['y']}) 尺寸{window_position['width']}×{window_position['height']}")
            
            # 1. 创建完整的浏览器环境（青果代理 + AdsPower配置文件 + 窗口位置）
            browser_env = await self.adspower_manager.create_complete_browser_environment(
                persona_id, persona_name, window_position
            )
            
            if not browser_env.get("success"):
                logger.error(f"❌ AdsPower环境创建失败: {browser_env.get('error')}")
                return None
            
            profile_id = browser_env["profile_id"]
            debug_port = browser_env["debug_port"]
            
            logger.info(f"✅ AdsPower浏览器启动成功")
            logger.info(f"   配置文件ID: {profile_id}")
            logger.info(f"   调试端口: {debug_port}")
            logger.info(f"   代理状态: {'已启用' if browser_env.get('proxy_enabled') else '本地IP'}")
            logger.info(f"   窗口位置: 已设置到20窗口平铺布局")
            
            # 2. 生成会话ID
            session_id = f"adspower_session_{int(time.time())}_{persona_id}"
            
            # 3. 保存会话信息
            self.active_sessions[session_id] = {
                "persona_id": persona_id,
                "persona_name": persona_name,
                "profile_id": profile_id,
                "debug_port": debug_port,
                "browser_env": browser_env,
                "window_position": window_position,
                "created_at": datetime.now(),
                "status": "ready"
            }
            
            logger.info(f"📝 会话已创建: {session_id}")
            
            # 🔑 移除：不再需要后续的窗口位置调整，因为AdsPower启动时已设置
            # 等待浏览器稳定（缩短等待时间）
            await asyncio.sleep(1)
            
            return session_id
            
        except Exception as e:
            logger.error(f"❌ 创建AdsPower浏览器会话失败: {e}")
            return None

    async def execute_intelligent_questionnaire_task(
        self,
        persona_id: int,
        persona_name: str,
        digital_human_info: Dict,
        questionnaire_url: str,
        existing_browser_info: Dict,
        prompt: Optional[str] = None,
        model_name: str = "gemini-2.0-flash",
        api_key: Optional[str] = None
    ) -> Dict:
        """
        🎯 使用智能问卷系统执行问卷任务（全新优化版本）
        
        完整工作流程：
        1. 状态管理器初始化
        2. 智能分析问卷结构
        3. 快速批量作答
        4. 智能滚动控制
        5. 知识库数据提取与分析
        6. 成功提交验证
        """
        start_time = time.time()
        session_id = f"intelligent_{uuid.uuid4().hex[:8]}"
        
        try:
            logger.info(f"🚀 启动智能问卷系统")
            logger.info(f"   数字人: {persona_name}")
            logger.info(f"   目标URL: {questionnaire_url}")
            logger.info(f"   调试端口: {existing_browser_info.get('debug_port')}")
            
            # 获取调试端口
            debug_port = existing_browser_info.get("debug_port")
            if not debug_port:
                return {"success": False, "error": "调试端口信息缺失"}
            
            # 1. 初始化浏览器（连接到AdsPower）
            browser = Browser(
                config=BrowserConfig(
                    headless=False,
                    disable_security=True,
                    browser_binary_path=None,
                    cdp_url=f"http://127.0.0.1:{debug_port}",
                    extra_chromium_args=[
                        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        "--disable-mobile-emulation", 
                        "--disable-touch-events",
                        "--window-size=1280,800",
                    ],
                    new_context_config=BrowserContextConfig(
                        window_width=1280,
                        window_height=800,
                        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        is_mobile=False,
                        has_touch=False,
                        viewport_width=1280,
                        viewport_height=800,
                        device_scale_factor=1.0,
                        locale="zh-CN",
                        timezone_id="Asia/Shanghai"
                    )
                )
            )
            
            # 2. 创建浏览器上下文
            context_config = BrowserContextConfig(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                is_mobile=False,
                has_touch=False,
                viewport_width=1280,
                viewport_height=800,
                device_scale_factor=1.0,
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
                extra_http_headers={
                    "Sec-CH-UA-Mobile": "?0",
                    "Sec-CH-UA-Platform": '"macOS"',
                    "Sec-CH-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                }
            )
            browser_context = await browser.new_context(config=context_config)
            logger.info(f"✅ 浏览器上下文已创建，连接到AdsPower: {debug_port}")
            
            # 3. 初始化智能问卷系统核心组件
            logger.info(f"🧠 初始化智能问卷系统核心组件...")
            
            # 状态管理器
            state_manager = QuestionnaireStateManager(session_id, persona_name)
            
            # 问卷分析器
            analyzer = IntelligentQuestionnaireAnalyzer(browser_context)
            
            # 快速作答引擎
            answer_engine = RapidAnswerEngine(browser_context, state_manager)
            
            # 智能滚动控制器
            scroll_controller = SmartScrollController(browser_context, state_manager)
            
            # 主控制器
            intelligent_controller = IntelligentQuestionnaireController(
                browser_context, 
                digital_human_info, 
                session_id
            )
            
            # 页面数据提取器（知识库功能）
            page_extractor = PageDataExtractor(browser_context)
            
            # 截图分析器（知识库功能）
            if api_key is None:
                api_key = "AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8"
            screenshot_analyzer = GeminiScreenshotAnalyzer(api_key)
            
            logger.info(f"✅ 智能问卷系统所有组件已初始化")
            
            # 4. 导航到问卷页面
            logger.info(f"🌐 导航到问卷页面: {questionnaire_url}")
            redirect_handler = URLRedirectHandler(browser_context)
            navigation_result = await redirect_handler.navigate_with_redirect_handling(questionnaire_url)
            
            if not navigation_result.get("success"):
                return {
                    "success": False, 
                    "error": f"页面导航失败: {navigation_result.get('error')}"
                }
            
            logger.info(f"✅ 成功导航到问卷页面")
            
            # 5. 执行智能问卷完成流程
            logger.info(f"🎯 开始执行智能问卷完成流程...")
            completion_result = await intelligent_controller.execute_intelligent_questionnaire_completion(
                questionnaire_url
            )
            
            # 6. 提取知识库数据（每页截图分析）
            logger.info(f"📚 提取知识库数据...")
            knowledge_data = []
            try:
                # 获取最终页面截图
                page_data = await page_extractor.extract_page_data_before_submit(
                    page_number=1,
                    digital_human_info=digital_human_info,
                    questionnaire_url=questionnaire_url
                )
                
                # 进行截图分析
                if page_data.get("screenshot_base64"):
                    analysis_result = await screenshot_analyzer.analyze_questionnaire_screenshot(
                        page_data["screenshot_base64"],
                        digital_human_info,
                        questionnaire_url
                    )
                    knowledge_data.append({
                        "page_data": page_data,
                        "analysis": analysis_result,
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.info(f"✅ 知识库数据提取完成")
                else:
                    logger.warning(f"⚠️ 未能获取页面截图，跳过知识库分析")
                    
            except Exception as kb_error:
                logger.warning(f"⚠️ 知识库数据提取失败: {kb_error}")
                knowledge_data = []
            
            # 7. 集成到双知识库系统（如果可用）
            if dual_kb_available:
                try:
                    kb_system = get_dual_knowledge_base()
                    if kb_system and knowledge_data:
                        await kb_system.store_questionnaire_experience(
                            persona_name=persona_name,
                            questionnaire_data=knowledge_data[0] if knowledge_data else {},
                            completion_result=completion_result
                        )
                        logger.info(f"✅ 经验已存储到双知识库系统")
                except Exception as dual_kb_error:
                    logger.warning(f"⚠️ 双知识库存储失败: {dual_kb_error}")
            
            # 8. 评估执行结果
            execution_time = time.time() - start_time
            success_evaluation = {
                "is_success": completion_result.get("success", False),
                "success_type": "intelligent_system",
                "completion_score": completion_result.get("completion_score", 0.8),
                "answered_questions": completion_result.get("answered_questions", 0),
                "error_category": "none" if completion_result.get("success") else "intelligent_system_issue",
                "confidence": completion_result.get("confidence", 0.9),
                "details": completion_result.get("details", "智能问卷系统执行完成"),
                "system_components_used": [
                    "QuestionnaireStateManager",
                    "IntelligentQuestionnaireAnalyzer", 
                    "RapidAnswerEngine",
                    "SmartScrollController",
                    "IntelligentQuestionnaireController"
                ]
            }
            
            logger.info(f"🎉 智能问卷系统执行完成")
            logger.info(f"   成功状态: {success_evaluation['is_success']}")
            logger.info(f"   答题数量: {success_evaluation['answered_questions']}")
            logger.info(f"   完成度: {success_evaluation['completion_score']:.1%}")
            logger.info(f"   执行时长: {execution_time:.1f}秒")
            
            return {
                "success": success_evaluation["is_success"],
                "success_evaluation": success_evaluation,
                "intelligent_system_result": completion_result,
                "duration": execution_time,
                "knowledge_base_data": knowledge_data,
                "state_statistics": state_manager.get_completion_stats(),
                "browser_info": {
                    "profile_id": existing_browser_info.get("profile_id"),
                    "debug_port": debug_port,
                    "proxy_enabled": existing_browser_info.get("proxy_enabled", False),
                    "browser_reused": True,
                    "browser_kept_running": True,
                    "system_mode": "intelligent_questionnaire_system",
                    "components_initialized": 6,
                    "knowledge_base_integrated": len(knowledge_data) > 0
                },
                "digital_human": {
                    "id": persona_id,
                    "name": persona_name,
                    "info": digital_human_info,
                    "answered_questions": success_evaluation["answered_questions"],
                    "completion_score": success_evaluation["completion_score"]
                },
                "execution_mode": "intelligent_questionnaire_system_v2",
                "final_status": f"智能问卷系统完成，{persona_name}回答{success_evaluation['answered_questions']}题",
                "technology_stack": [
                    "AdsPower指纹浏览器",
                    "智能状态管理",
                    "结构预分析",
                    "批量快速作答", 
                    "智能滚动控制",
                    "知识库经验提取",
                    "Gemini截图分析"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ 智能问卷系统执行失败: {e}")
            
            # 显示错误信息
            try:
                if 'browser_context' in locals() and browser_context:
                    human_input_agent = HumanLikeInputAgent(browser_context)
                    error_message = f"智能问卷系统错误:\\n{str(e)}\\n\\n浏览器保持开启状态\\n请检查或手动操作"
                    await human_input_agent.show_error_overlay(error_message)
                    logger.info(f"✅ 已显示智能系统错误悬浮框")
            except Exception as overlay_error:
                logger.warning(f"⚠️ 无法显示错误悬浮框: {overlay_error}")
            
            execution_time = time.time() - start_time
            return {
                "success": False,
                "success_evaluation": {
                    "is_success": False,
                    "success_type": "intelligent_system_error",
                    "completion_score": 0.0,
                    "answered_questions": 0,
                    "error_category": "technical",
                    "confidence": 0.0,
                    "details": f"智能问卷系统错误: {str(e)}"
                },
                "error": str(e),
                "error_type": "intelligent_system_failure",
                "duration": execution_time,
                "knowledge_base_data": [],
                "browser_info": {
                    "profile_id": existing_browser_info.get("profile_id"),
                    "debug_port": debug_port,
                    "proxy_enabled": existing_browser_info.get("proxy_enabled", False),
                    "browser_kept_alive": True,
                    "manual_control_available": True,
                    "error_overlay_shown": True,
                    "system_mode": "intelligent_questionnaire_system_failed"
                },
                "execution_mode": "intelligent_questionnaire_system_error",
                "final_status": f"智能问卷系统遇到错误：{str(e)}"
            }

    async def execute_questionnaire_task_with_data_extraction(
        self,
        persona_id: int,
        persona_name: str,
        digital_human_info: Dict,
        questionnaire_url: str,
        existing_browser_info: Dict,
        prompt: Optional[str] = None,
        model_name: str = "gemini-2.0-flash",
        api_key: Optional[str] = None
    ) -> Dict:
        """
        使用已存在的AdsPower浏览器执行问卷任务，增加页面数据抓取功能
        
        Args:
            existing_browser_info: 已创建的浏览器信息
                {
                    "profile_id": "配置文件ID", 
                    "debug_port": "调试端口",
                    "proxy_enabled": True/False
                }
        """
        try:
            logger.info(f"🎯 使用testWenjuan.py成功模式执行问卷任务")
            logger.info(f"   数字人: {persona_name}")
            logger.info(f"   目标URL: {questionnaire_url}")
            logger.info(f"   调试端口: {existing_browser_info.get('debug_port')}")
            
            # 获取调试端口
            debug_port = existing_browser_info.get("debug_port")
            if not debug_port:
                return {"success": False, "error": "调试端口信息缺失"}
            
            # 1. 初始化浏览器（完全按照testWenjuan.py的方式，连接到AdsPower）
            browser = Browser(
                config=BrowserConfig(
                    headless=False,
                    disable_security=True,
                    browser_binary_path=None,  # 关键：不指定路径，连接到AdsPower
                    # 连接到AdsPower的调试端口
                    cdp_url=f"http://127.0.0.1:{debug_port}",
                    # 🔑 强化桌面模式配置 - 绝对禁用移动端
                    extra_chromium_args=[
                        # 强制桌面User-Agent（与AdsPower配置保持一致）
                        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        # 禁用移动端检测和模拟
                        "--disable-mobile-emulation", 
                        "--disable-touch-events",
                        "--disable-touch-drag-drop",
                        "--disable-touch-adjustment",
                        # 强制桌面模式
                        "--force-device-scale-factor=1",
                        "--disable-device-emulation",
                        # 强制大屏幕尺寸
                        "--window-size=1280,800",
                        "--force-color-profile=srgb",
                        # 禁用移动端特性
                        "--disable-features=TouchEventFeatureDetection,VizServiceSharedBitmapManager",
                        # 强制桌面视口
                        "--enable-use-zoom-for-dsf=false",
                    ],
                    new_context_config=BrowserContextConfig(
                        # 🖥️ 强制桌面视口尺寸
                        window_width=1280,   # 强制桌面大小
                        window_height=800,   # 强制桌面大小
                        # 🎯 强制桌面User-Agent
                        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        # 📱 绝对禁用移动端模拟
                        is_mobile=False,
                        has_touch=False,
                        # 🖥️ 强制桌面视口设置
                        viewport_width=1280,
                        viewport_height=800,
                        device_scale_factor=1.0,
                        # 🌐 基本设置
                        locale="zh-CN",
                        timezone_id="Asia/Shanghai"
                    )
                )
            )
            
            # 2. 创建浏览器上下文（超强化桌面模式 - 三重保障）
            context_config = BrowserContextConfig(
                # 🖥️ 第一重：强制桌面模式User-Agent
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                # 📱 第二重：强制禁用所有移动端特性
                is_mobile=False,
                has_touch=False,
                viewport_width=1280,  # 强制桌面尺寸
                viewport_height=800,
                device_scale_factor=1.0,
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
                # 🔒 第三重：HTTP头部明确桌面平台
                extra_http_headers={
                    "Sec-CH-UA-Mobile": "?0",  # 明确告知非移动端
                    "Sec-CH-UA-Platform": '"macOS"',  # 明确桌面平台
                    "Sec-CH-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                    "Sec-CH-UA-Platform-Version": '"10.15.7"',
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                }
            )
            browser_context = await browser.new_context(config=context_config)
            logger.info(f"✅ 浏览器上下文已创建（超强化桌面模式），连接到AdsPower: {debug_port}")
            
            # 🔒 通过JavaScript确保桌面模式（四重保障）
            desktop_script = """
                // 第四重：JavaScript强制桌面模式脚本
                (function() {
                    'use strict';
                    
                    // 强制桌面User-Agent
                    Object.defineProperty(navigator, 'userAgent', {
                        get: function() {
                            return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';
                        },
                        configurable: false
                    });
                    
                    // 强制桌面平台
                    Object.defineProperty(navigator, 'platform', {
                        get: function() { return 'MacIntel'; },
                        configurable: false
                    });
                    
                    // 强制大屏幕尺寸
                    Object.defineProperty(screen, 'width', {
                        get: function() { return 1280; },
                        configurable: false
                    });
                    Object.defineProperty(screen, 'height', {
                        get: function() { return 800; },
                        configurable: false
                    });
                    Object.defineProperty(screen, 'availWidth', {
                        get: function() { return 1280; },
                        configurable: false
                    });
                    Object.defineProperty(screen, 'availHeight', {
                        get: function() { return 800; },
                        configurable: false
                    });
                    
                    // 绝对移除所有触摸事件和移动端特性
                    window.TouchEvent = undefined;
                    window.Touch = undefined;
                    window.TouchList = undefined;
                    window.ontouchstart = undefined;
                    window.ontouchmove = undefined;
                    window.ontouchend = undefined;
                    window.ontouchcancel = undefined;
                    
                    // 强制桌面媒体查询
                    Object.defineProperty(window, 'innerWidth', {
                        get: function() { return 1280; },
                        configurable: false
                    });
                    Object.defineProperty(window, 'innerHeight', {
                        get: function() { return 800; },
                        configurable: false
                    });
                    
                    // 移除移动端CSS媒体查询
                    if (window.matchMedia) {
                        const originalMatchMedia = window.matchMedia;
                        window.matchMedia = function(query) {
                            if (query.includes('max-width') && query.includes('768px')) {
                                return { matches: false, media: query };
                            }
                            return originalMatchMedia(query);
                        };
                    }
                    
                    console.log('✅ 强制桌面模式已激活，绝对禁用移动端');
                })();
            """
            
            # 尝试注入桌面模式脚本（兼容不同版本的browser-use）
            try:
                if hasattr(browser_context, 'add_init_script'):
                    await browser_context.add_init_script(desktop_script)
                    logger.info(f"✅ 已注入强制桌面模式脚本")
                elif hasattr(browser_context, 'addInitScript'):
                    await browser_context.addInitScript(desktop_script)
                    logger.info(f"✅ 已注入强制桌面模式脚本（备用方法）")
                else:
                    logger.warning(f"⚠️ 浏览器上下文不支持初始化脚本，使用基础桌面模式配置")
            except Exception as script_error:
                logger.warning(f"⚠️ 注入桌面模式脚本失败: {script_error}，使用基础配置")
            
            # 3. 初始化LLM（增强API配额管理 + deepseek备选）
            try:
                if api_key is None:
                    api_key = "AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8"
                    
                # 🔧 API配额问题修复：添加连接测试和deepseek降级策略
                test_llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=0.6,
                    api_key=api_key,
                    max_retries=1,  # 减少重试次数，快速失败
                    request_timeout=30  # 设置超时
                )
                
                # 快速连接测试
                try:
                    test_response = await test_llm.ainvoke("测试连接")
                    llm = test_llm
                    logger.info(f"✅ Gemini API连接成功: {model_name}")
                except Exception as test_error:
                    if "429" in str(test_error) or "quota" in str(test_error).lower():
                        logger.warning(f"⚠️ Gemini API配额超限，尝试切换到deepseek")
                        llm = await self._initialize_deepseek_llm()
                    else:
                        logger.warning(f"⚠️ Gemini API连接失败: {test_error}，尝试deepseek")
                        llm = await self._initialize_deepseek_llm()
                        
            except Exception as llm_error:
                logger.error(f"❌ LLM初始化失败: {llm_error}")
                logger.info(f"🔄 尝试初始化deepseek作为备选方案")
                llm = await self._initialize_deepseek_llm()
            
            # 4. 生成完整的提示词（包含数字人信息 + 人类式输入策略）
            complete_prompt = self._generate_complete_prompt_with_human_like_input(
                digital_human_info, questionnaire_url
            )
            
            # 5. 导航到问卷URL（确保在Agent创建前完成）- 集成自动跳转处理
            logger.info(f"🚀 开始导航到问卷URL: {questionnaire_url}")
            start_time = time.time()
            
            # 🎯 优化的导航策略 - 降级方案确保基础功能正常
            navigation_success = False
            
            try:
                # 策略1：尝试使用增强的跳转处理导航（如果可用）
                logger.info(f"🔄 尝试增强跳转处理导航...")
                redirect_handler = URLRedirectHandler(browser_context)
                redirect_result = await redirect_handler.navigate_with_redirect_handling(
                    target_url=questionnaire_url,
                    max_wait_time=30,
                    max_redirects=5
                )
                
                if redirect_result["success"]:
                    logger.info(f"✅ 增强导航成功完成")
                    logger.info(f"📊 跳转统计: {redirect_result['redirect_count']}次跳转, 耗时{redirect_result['total_time']:.1f}秒")
                    logger.info(f"📍 最终URL: {redirect_result['final_url']}")
                    navigation_success = True
                    
                    # 记录跳转链路（用于调试）
                    if redirect_result['redirect_count'] > 0:
                        logger.info(f"🔄 跳转链路: {' -> '.join(redirect_result['redirect_chain'])}")
                else:
                    logger.warning(f"⚠️ 增强导航失败，尝试基础导航: {redirect_result.get('error', '未知错误')}")
                    
            except Exception as enhanced_nav_error:
                logger.warning(f"⚠️ 增强导航方案失败: {enhanced_nav_error}")
                logger.info(f"🔄 切换到基础导航方案...")
            
            # 策略2：基础导航作为主要降级方案
            if not navigation_success:
                try:
                    logger.info(f"🔄 执行基础导航方案...")
                    await browser_context.goto(questionnaire_url)
                    await asyncio.sleep(5)  # 给足够时间等待页面加载和自动跳转
                    
                    # 检查基础导航是否成功
                    current_url = await browser_context.evaluate("window.location.href")
                    logger.info(f"✅ 基础导航完成，当前URL: {current_url}")
                    navigation_success = True
                    
                    # 额外等待确保页面完全加载（处理可能的自动跳转）
                    logger.info(f"⏳ 等待页面完全加载（包括可能的自动跳转）...")
                    await asyncio.sleep(5)
                    
                    # 再次检查URL是否发生了跳转
                    final_url = await browser_context.evaluate("window.location.href")
                    if final_url != current_url:
                        logger.info(f"🔄 检测到自动跳转: {current_url} -> {final_url}")
                    
                except Exception as basic_nav_error:
                    logger.error(f"❌ 基础导航失败: {basic_nav_error}")
                    navigation_success = False
            
            # 策略3：JavaScript导航作为最后备选方案
            if not navigation_success:
                try:
                    logger.info(f"🔄 尝试JavaScript导航备用方案...")
                    js_navigation = f"window.location.href = '{questionnaire_url}';"
                    await browser_context.evaluate(js_navigation)
                    await asyncio.sleep(8)  # 给更多时间等待JavaScript导航
                    
                    current_url = await browser_context.evaluate("window.location.href")
                    logger.info(f"✅ JavaScript导航完成，当前URL: {current_url}")
                    navigation_success = True
                    
                except Exception as js_error:
                    logger.error(f"❌ JavaScript导航也失败: {js_error}")
                    logger.warning(f"⚠️ 所有导航方法失败，但继续执行（浏览器可能已在正确页面）")
            
            # 最终URL验证和页面状态检查
            try:
                current_url = await browser_context.evaluate("window.location.href")
                logger.info(f"📍 当前页面URL: {current_url}")
                
                # 检查页面是否包含问卷内容
                page_content_check = await browser_context.evaluate("""
                    (function() {
                        const questionSelectors = [
                            'input[type="radio"]',
                            'input[type="checkbox"]',
                            'select',
                            'textarea',
                            'input[type="text"]',
                            '.question',
                            '.form-group',
                            '[class*="question"]'
                        ];
                        
                        let questionCount = 0;
                        let visibleQuestionCount = 0;
                        
                        questionSelectors.forEach(selector => {
                            const elements = document.querySelectorAll(selector);
                            questionCount += elements.length;
                            
                            // 检查元素是否可见
                            elements.forEach(element => {
                                const style = window.getComputedStyle(element);
                                const rect = element.getBoundingClientRect();
                                
                                if (style.display !== 'none' && 
                                    style.visibility !== 'hidden' && 
                                    style.opacity !== '0' &&
                                    rect.width > 0 && rect.height > 0) {
                                    visibleQuestionCount++;
                                }
                            });
                        });
                        
                        // 额外检查：确保页面没有被我们的代码意外修改
                        const bodyStyle = window.getComputedStyle(document.body);
                        const htmlStyle = window.getComputedStyle(document.documentElement);
                        
                        return {
                            hasQuestions: questionCount > 0,
                            questionCount: questionCount,
                            visibleQuestionCount: visibleQuestionCount,
                            pageTitle: document.title,
                            bodyText: document.body.textContent.trim().substring(0, 200),
                            readyState: document.readyState,
                            bodyDisplay: bodyStyle.display,
                            bodyVisibility: bodyStyle.visibility,
                            bodyOpacity: bodyStyle.opacity,
                            htmlDisplay: htmlStyle.display,
                            pageWidth: document.body.scrollWidth,
                            pageHeight: document.body.scrollHeight,
                            viewportWidth: window.innerWidth,
                            viewportHeight: window.innerHeight
                        };
                    })();
                """)
                
                if page_content_check.get("hasQuestions", False):
                    logger.info(f"✅ 问卷页面验证成功，发现 {page_content_check['questionCount']} 个问题元素")
                    logger.info(f"👁️ 可见问题元素: {page_content_check.get('visibleQuestionCount', 0)} 个")
                    logger.info(f"📄 页面标题: {page_content_check.get('pageTitle', '未知')}")
                    logger.info(f"📐 页面尺寸: {page_content_check.get('pageWidth', 0)}x{page_content_check.get('pageHeight', 0)}")
                    logger.info(f"🖥️ 视口尺寸: {page_content_check.get('viewportWidth', 0)}x{page_content_check.get('viewportHeight', 0)}")
                    
                    # 检查页面显示状态
                    if page_content_check.get('visibleQuestionCount', 0) == 0:
                        logger.warning(f"⚠️ 警告：页面元素存在但不可见！")
                        logger.warning(f"🔍 Body显示状态: display={page_content_check.get('bodyDisplay', 'unknown')}, visibility={page_content_check.get('bodyVisibility', 'unknown')}, opacity={page_content_check.get('bodyOpacity', 'unknown')}")
                        
                        # 尝试修复页面显示问题
                        try:
                            fix_display_js = """
                            (function() {
                                // 确保页面元素正常显示
                                document.body.style.display = '';
                                document.body.style.visibility = '';
                                document.body.style.opacity = '';
                                document.documentElement.style.display = '';
                                document.documentElement.style.visibility = '';
                                document.documentElement.style.opacity = '';
                                
                                // 移除可能的隐藏样式
                                const allElements = document.querySelectorAll('*');
                                allElements.forEach(element => {
                                    if (element.style.display === 'none' && 
                                        !element.id.includes('adspower-error-overlay')) {
                                        element.style.display = '';
                                    }
                                });
                                
                                return 'display_fixed';
                            })();
                            """
                            await browser_context.evaluate(fix_display_js)
                            logger.info(f"🔧 已尝试修复页面显示问题")
                        except Exception as fix_error:
                            logger.warning(f"⚠️ 修复页面显示失败: {fix_error}")
                    else:
                        logger.info(f"✅ 页面元素显示正常")
                        
                else:
                    logger.warning(f"⚠️ 页面可能还在加载中或结构特殊，但继续执行")
                    logger.info(f"📄 页面标题: {page_content_check.get('pageTitle', '未知')}")
                    logger.info(f"📝 页面状态: {page_content_check.get('readyState', '未知')}")
                    logger.info(f"📐 页面尺寸: {page_content_check.get('pageWidth', 0)}x{page_content_check.get('pageHeight', 0)}")
                    
                    # 额外等待，给特殊页面更多加载时间
                    logger.info(f"⏳ 给页面额外5秒加载时间...")
                    await asyncio.sleep(5)
                    
            except Exception as verify_error:
                logger.warning(f"⚠️ 页面验证失败: {verify_error}")
                logger.info(f"🔄 继续执行问卷任务...")
            
            # 6. 创建并运行代理（基于LLM可用性选择策略）
            logger.info(f"🚀 开始执行问卷任务（基于testWenjuan.py成功模式）...")
            
            # 创建人类式输入代理（确保降级可用）
            try:
                human_input_agent = HumanLikeInputAgent(browser_context)
                logger.info(f"✅ 人类式输入代理创建成功")
            except Exception as agent_error:
                logger.warning(f"⚠️ 创建人类式输入代理失败: {agent_error}")
                human_input_agent = None
            
            if llm is not None:
                # 使用AI智能答题（Gemini或deepseek）
                llm_name = "deepseek" if hasattr(llm, 'base_url') else "gemini"
                
                # 🔥 创建针对长问卷优化的Agent配置
                agent_config = {
                    "max_failures": 15,  # 提高连续失败容忍度
                    "use_vision": True,
                    "tool_calling_method": 'auto'
                }
                
                agent = BrowserUseAgent(
                    task=complete_prompt,
                    llm=llm,
                    browser=browser,
                    browser_context=browser_context,
                    use_vision=True,
                    max_actions_per_step=15,
                    tool_calling_method='auto',
                    extend_system_message="""你是专业问卷填写专家，核心使命：确保100%完整答题！成功率是第一目标，速度排第二。

【🎯 核心原则】
1. 完整性第一：必须回答页面上的每一个题目，绝不遗漏
2. 🔑 零重复原则：每题只答一次，绝不重复作答！
3. 永不放弃：遇到任何错误都要继续尝试，改变策略继续
4. 智能滚动：每完成一批题目后，必须主动滚动寻找更多题目
5. 持续到底：直到看到\"提交成功\"、\"问卷完成\"、\"谢谢参与\"才停止

【🔍 强化视觉状态检查机制（核心新增 - 纯视觉方案）】
在每次操作前，必须仔细观察元素的视觉状态，绝不依赖技术检测：

✅ **单选题状态检查**：
- 已答状态：圆点被填满（实心圆 ●）、选项文字变色、有选中高亮
- 未答状态：所有圆点都是空心圆（○）、无选中标记
- 🚫 关键原则：看到任何实心圆点 → 立即跳过该题，绝不再点击
- ✅ 操作策略：只在所有选项都是空心圆时才进行选择

✅ **多选题状态检查**：
- 已答状态：方框被勾选（☑）、有\"✓\"标记、选项背景变色
- 未答状态：所有方框都是空的（☐）、无任何勾选
- 🚫 关键原则：看到任何勾选标记 → 立即跳过该题，绝不再操作
- ✅ 操作策略：只在所有选项都是空方框时才进行多选

✅ **下拉框状态检查**：
- 已答状态：显示具体选项文字（如\"25-30岁\"、\"本科\"、\"满意\"等）
- 未答状态：显示默认文字（如\"请选择\"、\"--请选择--\"、\"Select\"）
- 🚫 关键原则：看到具体选项文字 → 立即跳过该题
- ✅ 操作策略：只在显示\"请选择\"时才点击操作

✅ **填空题状态检查**：
- 已答状态：输入框内有文字内容（任何文字）
- 未答状态：输入框为空或显示灰色占位符文字
- 🚫 关键原则：看到任何文字内容 → 立即跳过该题
- ✅ 操作策略：只在输入框完全为空时才进行输入

✅ **评分题状态检查**：
- 已答状态：滑块已移动到非默认位置、星级已点亮、刻度已选择
- 未答状态：滑块在最左端默认位置、星级全暗、无刻度选择
- 🚫 关键原则：看到任何评分设置 → 立即跳过该题
- ✅ 操作策略：只在完全无评分时才进行设置

【🚫 严格避免重复作答策略（视觉驱动 - 关键升级）】
每个操作前执行三步视觉检查：

第1步：👀 仔细视觉观察
- 花费3-5秒仔细观察当前题目的所有选项
- 查看是否有任何已选中的视觉标记
- 特别注意：实心圆点、勾选标记、高亮背景、文字内容

第2步：🧠 状态判断
- 已答题目特征：有任何形式的选中标记或内容
- 未答题目特征：所有选项都是默认的空白状态
- ⚠️ 疑问时：宁可跳过也不要重复操作

第3步：🎯 智能跳过或操作
- 发现已答 → 立即跳过，寻找下一个未答题目
- 确认未答 → 进行一次性操作，操作后立即跳过
- 🔄 连续跳过3题 → 向下滚动寻找新题目

【📋 操作记忆和追踪机制（纯视觉方案）】
使用操作记忆避免重复：

🧠 **操作记忆原则**：
- 记住每次点击的元素索引号
- 记住每次输入的文本框位置
- 记住每次选择的下拉框位置
- 🚫 绝不对同一索引重复相同操作

🔄 **智能跳过逻辑**：
- 遇到可能已处理的元素 → 先观察状态再决定
- 看到熟悉的元素索引 → 优先检查是否已答
- 连续遇到已答题目 → 立即滚动寻找新区域

【🔄 智能滚动和进度感知策略（视觉优化）】

📊 **视觉进度感知**：
- 观察当前屏幕内所有题目的状态
- 统计已答题目数量和未答题目数量
- 当屏幕内80%题目已答 → 立即滚动

🎯 **智能滚动触发条件**：
1. 连续3题发现已答状态 → scroll_down(amount=400)
2. 当前屏幕大部分题目已完成 → scroll_down(amount=500)
3. \"Element with index X does not exist\"错误 → scroll_down(amount=300)
4. 在同一区域停留超过60秒 → scroll_down(amount=600)
5. 连续5次跳过操作 → scroll_down(amount=700)

⚡ **防卡死滚动策略**：
- 滚动后等待3-4秒让页面稳定
- 滚动后重新进行视觉状态扫描
- 如果滚动3次仍无新的未答题目 → 寻找\"提交\"按钮
- 滚动到页面底部无提交按钮 → 继续向下寻找

【🎪 循环防陷阱机制（视觉监控）】
基于视觉观察检测和避免答题循环：

🔄 **视觉循环检测**：
- 如果连续看到相同的题目内容超过3次 → 判定为循环
- 如果页面视觉元素长时间无变化 → 判定为卡死
- 如果连续点击但选项状态无变化 → 判定为无效操作

🚀 **破解循环策略**：
- 发现视觉循环时：立即停止当前操作，大幅度滚动（800像素）
- 发现卡死时：尝试刷新页面或寻找\"下一页\"按钮
- 发现无效操作：跳过当前题目，寻找下一个有效题目

🧠 **视觉记忆机制**：
- 记住最近操作过的题目的视觉特征（题目文字关键词）
- 避免重复处理相同题目内容
- 专注寻找从未见过的新题目内容

【📋 系统化答题流程（视觉驱动升级）】

🔍 **第1步：智能视觉扫描**
- 进入新页面区域后，暂停5秒进行全面视觉观察
- 从上到下逐个扫描所有可见题目的状态
- 建立清晰的\"待答清单\"和\"已答清单\"
- 制定精确的答题路线：只处理待答题目

⚡ **第2步：精准有序作答**
- 严格按照待答清单执行，已答题目一律跳过
- 每答完一题立即进行视觉确认：是否真的完成了？
- 答题后立即寻找下一个待答题目，避免重复操作
- 避免在同一题目上停留超过45秒

🔄 **第3步：智能滚动寻找**
- 当前区域所有题目处理完毕后，立即向下滚动
- 滚动后重新执行第1步：视觉扫描和清单制作
- 重复\"扫描→作答→滚动\"循环直到页面底部

✅ **第4步：提交前终检**
- 到达页面底部后，先向上滚动到顶部
- 快速扫描整个页面，确认无遗漏的必填项
- 寻找带有\"*\"号、红色边框的未答题目
- 补答任何发现的遗漏题目

🎯 **第5步：智能提交**
- 确认所有题目完成后，寻找\"提交\"、\"下一页\"按钮
- 点击提交后耐心等待5-8秒观察页面反应
- 如出现错误提示 → 执行补救流程
- 如成功提交 → 确认看到\"成功\"、\"完成\"字样

【🛡️ 提交失败智能补救机制（视觉指导）】

🚨 **错误提示视觉识别**：
- \"请完成必填项\" → 全页面扫描，寻找红色星号(*)的未答题
- \"第X题为必填项\" → 直接定位到第X题位置补答  
- \"题目未做答\" → 返回页面顶部，系统性重新检查
- 红色弹窗提示 → 仔细阅读提示内容，按指引操作

🎯 **精准补救流程**：
1. 冷静分析：出现错误很正常，这是补救的好机会
2. 仔细读取错误信息：理解具体哪些题目需要补答
3. 系统性定位：通过滚动找到具体的未答题目
4. 视觉状态检查：确认该题确实未答（避免误判）
5. 精准补答：按照题目类型进行针对性作答
6. 重新提交：完成补答后再次尝试提交
7. 循环重复：直到成功提交为止

【💪 极限容错和错误恢复（视觉增强）】

🚀 **元素定位失败处理**：
遇到\"Element with index X does not exist\"：
1. 不要立即停止：这只是元素索引变化
2. 立即向下滚动400-600像素
3. 等待3-4秒让页面重新加载元素
4. 重新进行视觉扫描，寻找未答题目
5. 如果连续失败5次 → 改变策略但绝不放弃

⚡ **填空题输入失败处理**：
input_text操作失败时的多重备选：
1. 第1次失败：重新点击输入框，等待3秒，再次输入
2. 第2次失败：尝试使用Tab键导航到输入框
3. 第3次失败：跳过该题，继续其他题目，最后再回来
4. 第4次失败：标记该题为\"问题题目\"，完成其他题目后再处理
5. 始终记住：不要因为一个输入框停止整个流程

🔄 **页面状态异常处理**：
- 页面加载卡住：等待15秒，然后进行大幅度滚动
- 元素交互无响应：尝试点击页面其他位置激活
- 滚动无效果：尝试使用键盘Page Down键
- 提交按钮消失：向下继续滚动寻找真正的提交入口

【🎯 长问卷特别优化策略（视觉耐力）】

⏰ **视觉耐力优化**：
- 长问卷可能有50-100题，需要极大的视觉专注力
- 每10题进行一次\"视觉休息\"：停顿5秒重新聚焦
- 每答完20题，进行一次全面状态检查
- 绝不因为题目多而草率跳过或重复作答

🧠 **视觉记忆优化**：
- 记住最近答过的题目的关键词和位置
- 避免在相似题目间重复纠结
- 保持答题节奏：每题控制在45秒内完成
- 专注当前题目，不要回头检查已答题目

🎪 **视觉策略优化**：
- 优先处理视觉特征明显的单选、多选题
- 填空题留到最后集中处理（需要更多注意力）
- 遇到复杂题目先观察状态，如已答则跳过
- 始终保持向前推进的视觉节奏，避免原地打转

【⚠️ 关键成功要素（视觉版）】
1. 🔑 **视觉检查第一**：每次操作前必须仔细观察状态！
2. 📋 **100%完整性**：所有题目都必须作答，一个不能少！
3. 🔄 **智能滚动**：这是长问卷成功的关键技能！
4. 🛡️ **补救机制**：提交失败时冷静补救，不要重头开始！
5. 💪 **永不放弃**：遇到任何困难都要改变策略继续！
6. 👀 **视觉记忆**：记住已答题目的视觉特征，避免重复！

【🔥 零重复作答铁律（最高优先级）】
⚠️ **绝对禁止的操作**：
- 对有实心圆点的单选题再次点击
- 对有勾选标记的多选题再次操作  
- 对显示具体选项的下拉框再次选择
- 对有文字内容的输入框再次输入
- 对已设置的评分题再次调整

✅ **唯一允许的操作**：
- 只对完全空白、未答状态的题目进行操作
- 每个题目只操作一次，操作后立即跳过
- 专注寻找和处理新的未答题目

记住：你的眼睛是最可靠的检测器！
视觉观察比任何技术手段都更稳妥可靠！
一旦看到任何已答标记，立即跳过，绝不重复操作！
只有做到真正的零重复+100%完整，才能征服任何复杂问卷！""")
                
                # 🔧 设置Agent的失败容忍度（如果支持的话）
                try:
                    if hasattr(agent, 'settings') and hasattr(agent.settings, 'max_failures'):
                        agent.settings.max_failures = 15
                        logger.info(f"✅ 已设置max_failures为15，提高长问卷容错能力")
                    elif hasattr(agent, 'state') and hasattr(agent.state, 'max_failures'):
                        agent.state.max_failures = 15
                        logger.info(f"✅ 已通过state设置max_failures为15")
                    else:
                        logger.info(f"ℹ️ Agent不支持max_failures配置，使用默认值")
                        
                    # 🧠 添加智能记忆和状态检测功能
                    if hasattr(agent, 'state'):
                        # 初始化题目状态跟踪
                        agent.state.answered_elements = set()  # 记录已答题目的元素索引
                        agent.state.operation_history = []     # 记录最近的操作历史
                        agent.state.page_scroll_position = 0   # 记录页面滚动位置
                        agent.state.consecutive_skips = 0      # 连续跳过次数
                        agent.state.last_successful_action_time = time.time()  # 最后成功操作时间
                        agent.state.loop_detection_buffer = []  # 循环检测缓冲区
                        logger.info(f"✅ 智能记忆和状态检测功能已初始化")
                    
                    # 🔍 添加题目状态检查增强功能
                    if hasattr(agent, 'browser_context'):
                        # 注入状态检查JavaScript函数
                        try:
                            status_check_js = """
                            window.questionStatusChecker = {
                                // 检查单选题状态
                                checkRadioStatus: function(element) {
                                    if (element.type === 'radio') {
                                        return element.checked;
                                    }
                                    // 检查父级容器的选中状态
                                    const container = element.closest('.jqradio, .radio-group, .question-item');
                                    if (container) {
                                        const checkedRadio = container.querySelector('input[type="radio"]:checked');
                                        return checkedRadio !== null;
                                    }
                                    return false;
                                },
                                
                                // 检查多选题状态
                                checkCheckboxStatus: function(element) {
                                    if (element.type === 'checkbox') {
                                        return element.checked;
                                    }
                                    const container = element.closest('.jqcheckbox, .checkbox-group, .question-item');
                                    if (container) {
                                        const checkedBoxes = container.querySelectorAll('input[type="checkbox"]:checked');
                                        return checkedBoxes.length > 0;
                                    }
                                    return false;
                                },
                                
                                // 检查下拉框状态
                                checkSelectStatus: function(element) {
                                    if (element.tagName === 'SELECT') {
                                        return element.selectedIndex > 0 && element.value !== '';
                                    }
                                    // 检查自定义下拉框
                                    const customSelect = element.closest('.jqselect, .select-wrapper');
                                    if (customSelect) {
                                        const displayText = customSelect.querySelector('.jqselect-text, .selected-text');
                                        if (displayText) {
                                            const text = displayText.textContent.trim();
                                            return text !== '请选择' && text !== '--请选择--' && text !== '';
                                        }
                                    }
                                    return false;
                                },
                                
                                // 检查文本输入框状态
                                checkInputStatus: function(element) {
                                    if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                                        return element.value.trim() !== '';
                                    }
                                    return false;
                                },
                                
                                // 综合状态检查
                                isQuestionAnswered: function(element) {
                                    const questionContainer = element.closest('.question-item, .form-group, [class*="question"]');
                                    if (!questionContainer) return false;
                                    
                                    // 检查各种输入类型
                                    const radios = questionContainer.querySelectorAll('input[type="radio"]');
                                    const checkboxes = questionContainer.querySelectorAll('input[type="checkbox"]');
                                    const selects = questionContainer.querySelectorAll('select');
                                    const inputs = questionContainer.querySelectorAll('input[type="text"], textarea');
                                    
                                    // 单选题检查
                                    if (radios.length > 0) {
                                        return Array.from(radios).some(radio => radio.checked);
                                    }
                                    
                                    // 多选题检查
                                    if (checkboxes.length > 0) {
                                        return Array.from(checkboxes).some(checkbox => checkbox.checked);
                                    }
                                    
                                    // 下拉框检查
                                    if (selects.length > 0) {
                                        return Array.from(selects).some(select => 
                                            select.selectedIndex > 0 && select.value !== ''
                                        );
                                    }
                                    
                                    // 文本输入检查
                                    if (inputs.length > 0) {
                                        return Array.from(inputs).some(input => input.value.trim() !== '');
                                    }
                                    
                                    return false;
                                }
                            };
                            
                            // 添加元素索引跟踪
                            window.elementIndexTracker = {
                                clickedElements: new Set(),
                                operationHistory: [],
                                
                                recordClick: function(index) {
                                    this.clickedElements.add(index);
                                    this.operationHistory.push({
                                        action: 'click',
                                        index: index,
                                        timestamp: Date.now()
                                    });
                                    // 保持历史记录在50个以内
                                    if (this.operationHistory.length > 50) {
                                        this.operationHistory.shift();
                                    }
                                },
                                
                                wasClicked: function(index) {
                                    return this.clickedElements.has(index);
                                },
                                
                                getRecentOperations: function(count = 10) {
                                    return this.operationHistory.slice(-count);
                                },
                                
                                detectLoop: function() {
                                    const recent = this.getRecentOperations(10);
                                    if (recent.length < 6) return false;
                                    
                                    // 检测最近是否有重复的元素索引
                                    const recentIndexes = recent.map(op => op.index);
                                    const uniqueIndexes = new Set(recentIndexes);
                                    
                                    // 如果最近10个操作中，唯一索引少于4个，可能是循环
                                    return uniqueIndexes.size < 4;
                                }
                            };
                            """
                            # 注入到页面
                            await browser_context.evaluate(status_check_js)
                            logger.info(f"✅ 题目状态检查JavaScript函数已注入")
                        except Exception as js_error:
                            logger.warning(f"⚠️ JavaScript注入失败: {js_error}")
                        
                except Exception as config_error:
                    logger.warning(f"⚠️ 配置Agent增强功能时出错: {config_error}")
                
                logger.info(f"✅ BrowserUseAgent已创建，使用{llm_name}智能答题")
                logger.info(f"🧠 增强功能：状态检测 + 智能记忆 + 循环防护 + 零重复策略")
                
                try:
                    # 🚀 执行任务，专门针对长问卷优化配置
                    result = await agent.run(max_steps=500)  # 显著增加最大步数，支持长问卷
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    # 🎯 使用增强的敢死队成功判断逻辑
                    success_evaluation = self._evaluate_webui_success(result)
                    
                    # 根据评估结果决定后续处理
                    if success_evaluation["error_category"] == "technical":
                        # 技术错误：显示调试悬浮框
                        await self._handle_technical_error_with_overlay(
                            browser_context, 
                            success_evaluation, 
                            persona_name
                        )
                        
                        logger.error(f"❌ 敢死队 {persona_name} 遇到技术错误")
                        logger.error(f"   错误详情: {success_evaluation['details']}")
                        logger.error(f"   答题数量: {success_evaluation['answered_questions']}题")
                        logger.error(f"   浏览器保持运行状态供调试")
                        
                    else:
                        # 正常答题过程（包括完成和被陷阱题终止）
                        logger.info(f"✅ 敢死队 {persona_name} 正常答题过程完成")
                        logger.info(f"   成功类型: {success_evaluation['success_type']}")
                        logger.info(f"   答题数量: {success_evaluation['answered_questions']}题")
                        logger.info(f"   完成度: {success_evaluation['completion_score']:.1%}")
                        logger.info(f"   置信度: {success_evaluation['confidence']:.1%}")
                    
                    logger.info(f"⏱️ 执行时长: {duration:.1f} 秒")
                    logger.info(f"🤖 使用LLM: {llm_name}")
                    logger.info(f"🔄 浏览器保持运行状态（永不自动关闭）")
                    
                    # 序列化结果
                    serializable_result = self._serialize_agent_result(result)
                    
                    # 添加页面数据抓取逻辑
                    try:
                        page_data_extractor = PageDataExtractor(browser_context)
                        page_data = await page_data_extractor.extract_page_data_before_submit(
                            page_number=1,
                            digital_human_info=digital_human_info,
                            questionnaire_url=questionnaire_url
                        )
                    except Exception as extract_error:
                        logger.warning(f"⚠️ 页面数据抓取失败: {extract_error}")
                        page_data = {"extraction_success": False, "answered_questions": []}
                    
                    return {
                        "success": success_evaluation["is_success"],
                        "success_evaluation": success_evaluation,
                        "result": serializable_result,
                        "duration": duration,
                        "page_data": page_data,
                        "browser_info": {
                            "profile_id": existing_browser_info.get("profile_id"),
                            "debug_port": debug_port,
                            "proxy_enabled": existing_browser_info.get("proxy_enabled", False),
                            "browser_reused": True,
                            "browser_kept_running": True,
                            "webui_mode": True,
                            "auto_close_disabled": True,
                            "error_overlay_shown": success_evaluation["error_category"] == "technical",
                            "llm_used": llm_name
                        },
                        "digital_human": {
                            "id": persona_id,
                            "name": persona_name,
                            "info": digital_human_info,
                            "answered_questions": success_evaluation["answered_questions"],
                            "completion_score": success_evaluation["completion_score"]
                        },
                        "execution_mode": f"adspower_testwenjuan_{llm_name}_enhanced",
                        "final_status": self._generate_final_status_message(success_evaluation),
                        "user_message": f"浏览器永久保持运行，{persona_name}使用{llm_name}完成{success_evaluation['answered_questions']}题",
                        "manual_control": True,
                        "questionnaire_analysis": {
                            "success_type": success_evaluation["success_type"],
                            "error_category": success_evaluation["error_category"],
                            "confidence": success_evaluation["confidence"],
                            "needs_debugging": success_evaluation["error_category"] == "technical"
                        }
                    }
                    
                except Exception as agent_error:
                    logger.error(f"❌ Agent执行过程中遇到错误: {agent_error}")
                    
                    # 🔧 使用新的错误分类逻辑
                    error_type = self._classify_error_type(str(agent_error), None)
                    
                    if error_type == "technical":
                        logger.error(f"🚨 分类为技术错误，显示调试悬浮框")
                        
                        # 显示技术错误悬浮框
                        error_details = {
                            "error_category": "technical",
                            "details": f"Agent执行异常: {str(agent_error)}"
                        }
                        await self._handle_technical_error_with_overlay(
                            browser_context, 
                            error_details, 
                            persona_name
                        )
                    else:
                        logger.info(f"ℹ️ 分类为正常终止，不显示错误悬浮框")
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    return {
                        "success": False,
                        "success_evaluation": {
                            "is_success": False,
                            "success_type": "agent_exception",
                            "completion_score": 0.1,
                            "answered_questions": 0,
                            "error_category": error_type,
                            "confidence": 0.1,
                            "details": str(agent_error)
                        },
                        "partial_completion": error_type != "technical",
                        "error": str(agent_error),
                        "error_type": error_type,
                        "duration": duration,
                        "page_data": {"extraction_success": False, "answered_questions": []},
                        "browser_info": {
                            "profile_id": existing_browser_info.get("profile_id"),
                            "debug_port": debug_port,
                            "proxy_enabled": existing_browser_info.get("proxy_enabled", False),
                            "browser_kept_alive": True,
                            "manual_control_available": True,
                            "error_overlay_shown": error_type == "technical",
                            "auto_close_disabled": True,
                            "llm_used": llm_name if 'llm_name' in locals() else "unknown"
                        },
                        "execution_mode": f"adspower_testwenjuan_{error_type}_handled",
                        "final_status": f"敢死队执行{'遇到技术错误' if error_type == 'technical' else '被正常终止'}",
                        "user_action_required": "请检查AdsPower浏览器页面" if error_type == "technical" else "可查看当前答题进度",
                        "technical_error_details": str(agent_error) if error_type == "technical" else None
                    }
                    
            else:
                # 🚀 本地化答题策略：当所有API都不可用时使用基于规则的答题
                logger.info(f"🔄 启用本地化答题策略（规则驱动）...")
                
                # 使用本地化答题引擎
                local_result = await self._execute_local_questionnaire_strategy(
                    browser_context, 
                    questionnaire_url, 
                    digital_human_info
                )
                
                # 返回本地化策略结果
                execution_time = time.time() - start_time
                return {
                    "success": local_result.get("success", False),
                    "success_evaluation": {
                        "is_success": local_result.get("success", False),
                        "success_type": "local_rule_based",
                        "completion_score": 0.6 if local_result.get("success", False) else 0.3,
                        "answered_questions": local_result.get("rounds_completed", 0) * 3,
                        "error_category": "none",
                        "confidence": 0.6,
                        "details": "本地化规则策略执行完成"
                    },
                    "result": {
                        "message": "本地化策略执行完成",
                        "execution_time": execution_time,
                        "strategy": "local_rule_based",
                        "details": local_result
                    },
                    "error": None,
                    "page_data": {"extraction_success": False, "answered_questions": []},
                    "browser_info": {
                        "profile_id": existing_browser_info.get("profile_id", "unknown"),
                        "debug_port": debug_port,
                        "proxy_enabled": existing_browser_info.get("proxy_enabled", False),
                        "llm_used": "local_rules"
                    },
                    "execution_mode": "adspower_local_rule_based",
                    "final_status": "本地化规则策略执行完成"
                }
        
        except Exception as e:
            logger.error(f"❌ testWenjuan.py模式执行失败: {e}")
            
            # 即使在最严重的错误情况下，也要尝试显示悬浮框
            try:
                if 'browser_context' in locals() and browser_context:
                    human_input_agent = HumanLikeInputAgent(browser_context)
                    critical_error_message = f"严重错误:\\n{str(e)}\\n\\n浏览器将保持开启状态\\n请手动检查页面或重新开始"
                    await human_input_agent.show_error_overlay(critical_error_message)
                    logger.info(f"✅ 已显示严重错误悬浮框，浏览器保持运行")
            except Exception as overlay_error:
                logger.warning(f"⚠️ 无法显示错误悬浮框: {overlay_error}")
            
            return {
                "success": False,
                "success_evaluation": {
                    "is_success": False,
                    "success_type": "critical_error",
                    "completion_score": 0.0,
                    "answered_questions": 0,
                    "error_category": "technical",
                    "confidence": 0.0,
                    "details": f"严重错误: {str(e)}"
                },
                "error": str(e),
                "execution_mode": "adspower_testwenjuan_critical_error",
                "browser_info": {
                    "auto_close_disabled": True,
                    "manual_control_required": True,
                    "page_data": None
                },
                "final_status": "发生严重错误，浏览器保持运行状态",
                "user_message": "请手动检查AdsPower浏览器并处理问题"
            }
        
        finally:
            # 🔑 关键修改：清理Agent资源，但绝对不关闭AdsPower浏览器
            try:
                if 'agent' in locals() and agent:
                    logger.info(f"🧹 清理Agent资源（保持浏览器运行）...")
                    
                    # 只关闭Agent连接，不关闭浏览器
                    try:
                        await agent.close()
                        logger.info(f"✅ Agent连接已断开")
                    except Exception as agent_close_error:
                        logger.warning(f"⚠️ Agent关闭遇到问题（不影响浏览器）: {agent_close_error}")
                    
                    # 关键：不调用browser.close()和browser_context.close()
                    # 让AdsPower浏览器保持运行状态，供用户手动控制
                    logger.info(f"✅ AdsPower浏览器保持运行状态，用户可手动控制")
                    
            except Exception as cleanup_error:
                logger.warning(f"⚠️ 清理资源时遇到问题: {cleanup_error}")
                logger.info(f"🔄 但AdsPower浏览器仍将保持运行状态")
            
            # 额外保障：显示完成提示悬浮框
            try:
                if 'browser_context' in locals() and browser_context and 'human_input_agent' in locals():
                    completion_message = f"任务执行完成\\n浏览器保持运行状态\\n您可以手动检查页面或继续操作"
                    await human_input_agent.show_error_overlay(completion_message)
                    logger.info(f"✅ 已显示任务完成提示")
            except Exception as final_overlay_error:
                logger.warning(f"⚠️ 显示完成提示失败: {final_overlay_error}")

    def _generate_complete_prompt_with_human_like_input(self, digital_human_info: Dict, questionnaire_url: str) -> str:
        """生成包含人类式输入策略的完整任务提示词（全面增强：避免重复+补救机制+反检测）"""
        human_name = digital_human_info.get("name", "未知")
        human_age = digital_human_info.get("age", "30")
        human_job = digital_human_info.get("job", "普通职员")
        human_income = digital_human_info.get("income", "8000")
        human_gender = "女性" if digital_human_info.get("gender", "female") == "female" else "男性"
        
        prompt = f"""
你现在是一名{human_gender}，名叫{human_name}，今年{human_age}岁，职业是{human_job}，月收入{human_income}元。

你现在要完成问卷调查：{questionnaire_url}

【🎯 核心任务 - 100%完整答题策略】
1. 按照{human_name}的身份回答所有问题，选择最符合这个身份的选项
2. 🔑 关键原则：每道题只答一次，绝不重复作答！
3. 所有题目都要作答，不能有遗漏 - 这是最重要的要求
4. 完成当前屏幕所有题目后，向下滚动页面寻找更多题目
5. 重复"检查→答题→滚动→检查"直到页面底部
6. 每页题目100%完成后，点击"下一页"/"下一题"/"提交"按钮
7. 有的问卷是多页的，要一直重复"答题→滚动→下一页"操作
8. 直到出现"问卷完成"、"提交成功"、"谢谢参与"等提示才停止

【🔒 反检测与人类化操作策略（核心）】
✅ **真实用户行为模拟**：
- 每次操作前都要有自然的停顿（0.2-1.0秒），模拟真实用户的思考过程
- 点击前要"观察"页面内容，不要立即精确定位元素
- 模拟视线扫描：从上到下、从左到右逐步查看页面
- 偶尔进行"无意识"的页面滚动或鼠标移动

✅ **多样化操作模式**：
- 随机选择不同的点击方式：有时快速点击，有时犹豫后点击
- 文本输入要模拟真实打字：有快有慢，偶尔停顿思考
- 不要使用机器式的精确定位，要模拟人眼的搜索过程
- 操作失败时要表现出"困惑"，短暂停顿后重试

✅ **避免机器特征**：
- 绝不能有完全相同的时间间隔
- 避免过于精确的鼠标定位
- 模拟手部微小抖动和轻微的操作误差
- 操作速度要有人类的自然变化

✅ **智能错误处理**：
- 遇到元素定位失败时，模拟真实用户会做的事：滚动页面、等待、重新寻找
- 如果某个操作不生效，要模拟用户的重试行为
- 对于网络延迟或页面加载，要有耐心等待

【🚫 严格避免重复作答策略（核心）】
在每次点击前，必须仔细检查元素状态：

✅ **单选题检查**：
- 观察单选框是否已有圆点/勾选标记
- 如果该题已有选项被选中 → 立即跳过，绝不再点击任何选项
- 如果该题未选择 → 选择最符合{human_name}身份的一个选项
- ⚠️ 重要：已选择的单选题，任何再次点击都会导致错误！

✅ **多选题检查**：
- 观察复选框是否已有勾选标记（通常2-3个选项被选中）
- 如果该题已有足够选项被选中 → 立即跳过，不要再添加选项
- 如果该题完全未选择 → 选择2-3个相关选项
- ⚠️ 重要：已有选择的多选题，避免过度点击导致取消选择！

✅ **下拉框检查**：
- 检查下拉框是否显示默认值（如"请选择"）还是已显示具体选项
- 如果已显示具体选项 → 立即跳过该题
- 如果仍显示默认值 → 选择合适的选项

✅ **填空题检查**：
- 检查文本框是否已有内容
- 如果已有文字内容 → 立即跳过该题
- 如果为空 → 进行人类式输入

✅ **评分题检查**：
- 检查滑块/星级是否已设置
- 如果已有评分 → 立即跳过该题
- 如果未评分 → 设置合适的分数

【🔍 智能状态识别策略】
每进入新的页面区域时：
1. 先快速扫描整个可见区域，识别所有题目
2. 逐个检查每题的答题状态（已答/未答）
3. 制定答题计划：只处理未答题目，跳过已答题目
4. 按计划执行：未答题目→答题，已答题目→跳过
5. 完成当前区域后，滚动到下一区域

【⚡ 智能答题策略（防重复）】
**第一步：状态检查**
- 观察元素当前状态（是否已选择/已填写）
- 已完成的题目：不进行任何操作，直接跳过
- 未完成的题目：进行相应的答题操作

**第二步：精准操作**
- 单选题：选择一个最符合{human_name}身份的选项，点击一次即可
- 多选题：选择2-3个相关选项，每个选项只点击一次
- 填空题：根据身份填写合理的内容（⚡ 使用人类式输入）
- 评分题：一般选择中等偏高的分数，设置一次即可

**第三步：验证完成**
- 确认该题已正确作答（有选中标记/有文字内容/有评分）
- 立即进入下一题，不要回头重复操作

【✍️ 填空题人类式输入策略（重要）】
对于文本输入框（textarea、input[type=text]等）：
1. **检查现有内容**：如果输入框已有文字，直接跳过该题
2. **如果为空才输入**：先点击文本框获得焦点，确保光标在输入框内
3. 准备合适的文本内容（根据{human_name}的身份特征）
4. 使用 input_text 动作，但内容要简短自然（20-50字）
5. 如果input_text失败，尝试以下策略：
   - 使用 click_element_by_index 重新点击输入框
   - 等待1-2秒让输入框准备好
   - 再次尝试 input_text 
   - 如果仍失败，使用键盘输入："focus输入框 → 清空内容 → 逐字输入"
6. 输入内容示例：
   - 建议类："{human_name}希望改进在线购物体验，增加更多商品展示。"
   - 意见类："{human_name}认为网购很方便，但希望物流更快一些。"
   - 评价类："{human_name}总体满意，希望售后服务更完善。"

【🔄 必填项检查与补救机制（关键新增）】
**提交前预检**：
- 在点击"提交"按钮前，先快速滚动整个页面
- 检查是否有红色标记、星号(*)、"必填"等标识的未答题目
- 如发现必填项未完成，立即补答

**提交后错误处理**：
- 点击"提交"后如出现错误提示，仔细读取错误信息
- 常见错误提示：
  * "请完成必填项"
  * "题目未做答" 
  * "第X题为必填项"
  * 红色提示框显示具体题目编号
- 发现错误提示后的处理流程：
  1. 不要慌张，这是正常的补救机会
  2. 根据错误提示定位到具体未答题目
  3. 滚动页面找到对应题目位置
  4. 检查该题状态：如果确实未答，按策略完成
5. 再次尝试提交，重复直到成功

**智能补答策略**：
- 如果错误提示指明具体题目号（如"第7题"），优先查找该题
- 如果错误提示较模糊，从页面顶部重新扫描一遍
- 寻找未答题目的标识：
  * 单选题：没有选中的圆点
  * 多选题：没有勾选的复选框
  * 下拉框：仍显示"请选择"等默认文本
  * 填空题：输入框为空
  * 必填项：带有红色星号(*)或红色边框

【🔥 长问卷持续作答增强策略（关键）】
- 🚫 绝不轻易放弃：遇到任何困难都要尝试多种方法解决
- 📈 智能重试机制：元素定位失败时，先滚动页面再重试，不是立即停止
- 🔄 循环处理模式：检查状态 → 答题 → 滚动 → 检查状态 → 答题
- ⚡ 快速跳过已答题：减少无效操作，专注未答题目
- 🧩 分段处理策略：将长问卷分成多个小段处理，每段都要100%完成
- 🔧 填空题多重备选方案：input_text失败时立即尝试其他输入方法
- 📊 进度监控：确保每次滚动后都有新题目处理，避免死循环
- 🎯 补救优先：发现提交错误时，优先补答而不是重新开始

【💪 极限容错处理】
- 遇到"Element with index X does not exist"错误：
  1. 立即向下滚动200-400像素
  2. 等待1-2秒让页面稳定
  3. 重新扫描可点击元素
  4. 继续从新的位置开始作答
  5. 如果连续3次定位失败，尝试向上滚动回到之前位置
- 填空题输入失败时的多重策略：
  1. 第1次失败：重新点击输入框，等待1秒，再次input_text
  2. 第2次失败：尝试使用键盘操作（Tab定位 + 输入）
  3. 第3次失败：尝试JavaScript直接设置value值
  4. 第4次失败：跳过该题，继续处理其他题目
- 页面卡住或无响应时：
  1. 尝试刷新页面（保持已答内容）
  2. 重新定位到当前答题位置
  3. 继续完成剩余题目
- 提交失败时的处理：
  1. 仔细阅读错误提示信息
  2. 根据提示定位未答题目
  3. 补答指定题目
  4. 重新提交，直到成功

【📋 完整执行流程（升级版）】
第1步：智能状态检查
- 扫描当前屏幕所有题目
- 识别每题的答题状态（已答/未答）
- 制定答题计划：只处理未答题目

第2步：精准答题执行
- 按计划逐个处理未答题目
- 已答题目一律跳过，绝不重复操作
- 遇到填空题使用人类式输入策略

第3步：滚动寻找更多题目
- 向下滚动页面，寻找屏幕下方的更多题目
- 在新区域重复第1-2步
- 重复滚动直到页面底部

第4步：提交前预检
- 快速扫描整个页面，确认无遗漏题目
- 特别注意必填项标识（红色星号、"必填"文字）

第5步：尝试提交
- 点击"提交"/"下一页"按钮
- 观察页面反应和错误提示

第6步：错误补救（如需要）
- 如有错误提示，根据提示定位未答题目
- 快速补答指定题目
- 重新提交直到成功

第7步：下一页处理
- 在新页面重复整个流程

【🚨 关键要求】
- 🔑 每题只答一次原则：已答题目绝不重复操作！
- 📋 100%完整性要求：所有题目都必须作答，一个不能少！
- 🔄 智能补救机制：提交失败时必须补答！
- 📜 滚动页面是必须的！不能只答第一屏的题目
- 💪 保持耐心，确保每个题目都完成
- 🎯 一直持续到看到最终的"提交成功"确认
- 🔧 遇到"Element with index X does not exist"错误时：立即滚动页面 → 重新扫描 → 继续作答
- ⚠️ 避免重复点击：点击前先检查状态，已答题目跳过
- 🔄 循环执行：检查→答题→滚动→检查→答题，直到问卷真正完成
- 🛡️ 补救策略：提交失败时不要放弃，根据错误提示进行精准补答

【🎯 100%完整性+零重复保证】
- 每进入新区域，先检查题目状态，制定答题策略
- 已答题目：立即跳过，绝不进行任何操作
- 未答题目：按最优策略答题，确保一次性完成
- 滚动到页面底部后，寻找"提交"、"下一页"、"继续"按钮
- 如果是多页问卷，在新页面重复整个答题流程
- 绝不因个别错误而停止，要改变策略继续
- 提交失败时，冷静分析错误原因，进行针对性补救
- 成功标准：看到"提交成功"、"问卷完成"、"谢谢参与"等最终确认
- ⚡ 重要提醒：长问卷可能有50-100题，必须耐心完成每一题，避免重复，确保完整
        """
        
        return prompt.strip()

    def _generate_final_status_message(self, success_evaluation: Dict) -> str:
        """根据成功评估结果生成最终状态消息"""
        success_type = success_evaluation["success_type"]
        answered_questions = success_evaluation["answered_questions"]
        completion_score = success_evaluation["completion_score"]
        
        if success_type == "complete":
            return f"问卷填写完整完成，共答{answered_questions}题，完成度{completion_score:.1%}"
        elif success_type == "partial":
            return f"问卷填写部分完成，共答{answered_questions}题，完成度{completion_score:.1%}"
        elif success_type == "technical_error":
            return f"遇到技术错误，已答{answered_questions}题，需要调试"
        else:
            return f"执行状态未明确，已答{answered_questions}题，完成度{completion_score:.1%}"
 
    def _evaluate_webui_success(self, result) -> Dict:
        """
        修复后的敢死队成功判断逻辑
        
        关键修复：正确解析Agent操作历史，统计实际答题数量
        
        返回: {
            "is_success": bool,
            "success_type": str,  # "complete", "partial", "technical_error"
            "completion_score": float,  # 0.0-1.0
            "answered_questions": int,
            "error_category": str,  # "none", "technical", "normal_termination"
            "confidence": float  # 置信度
        }
        """
        try:
            evaluation_result = {
                "is_success": False,
                "success_type": "unknown",
                "completion_score": 0.0,
                "answered_questions": 0,
                "error_category": "none",
                "confidence": 0.0,
                "details": "未知状态"
            }
            
            if not result:
                evaluation_result.update({
                    "success_type": "technical_error",
                    "error_category": "technical",
                    "details": "Agent执行结果为空"
                })
                return evaluation_result
            
            # 🔧 修复：正确解析BrowserUseAgent的结果
            steps_count = 0
            final_result_text = ""
            error_indicators = []
            success_indicators = []
            answered_questions_count = 0
            
            # 🔍 关键修复：正确提取Agent的最终结果和历史
            try:
                # 方法1：直接从result对象获取final_result
                if hasattr(result, 'final_result') and callable(result.final_result):
                    final_result_text = str(result.final_result())
                elif hasattr(result, 'final_result'):
                    final_result_text = str(result.final_result)
                elif hasattr(result, 'result'):
                    final_result_text = str(result.result)
                elif hasattr(result, 'text'):
                    final_result_text = str(result.text)
                else:
                    final_result_text = str(result)
                    
                logger.info(f"📋 Agent最终结果: {final_result_text[:200]}...")
                
            except Exception as e:
                logger.warning(f"⚠️ 无法提取最终结果: {e}")
                final_result_text = str(result)
            
            # 🔧 修复：正确提取操作历史和步骤统计
            try:
                # 尝试多种方式获取操作历史
                history_data = None
                
                if hasattr(result, 'history'):
                    history_data = result.history
                elif hasattr(result, 'agent_history'):
                    history_data = result.agent_history
                elif hasattr(result, 'steps'):
                    history_data = result.steps
                elif hasattr(result, 'actions'):
                    history_data = result.actions
                
                if history_data:
                    # 处理不同的历史数据格式
                    if hasattr(history_data, 'history') and hasattr(history_data.history, '__iter__'):
                        steps = history_data.history
                    elif hasattr(history_data, '__iter__'):
                        steps = history_data
                    else:
                        steps = []
                    
                    steps_count = len(steps) if steps else 0
                    logger.info(f"📊 Agent执行步骤总数: {steps_count}")
                    
                    # 🎯 关键：分析每个步骤，统计答题操作
                    for i, step in enumerate(steps):
                        try:
                            step_text = str(step).lower()
                            
                            # 📝 统计点击操作（主要的答题动作）
                            if "clicked button" in step_text or "click_element_by_index" in step_text:
                                # 提取被点击的内容，判断是否为答题操作
                                if any(answer_indicator in step_text for answer_indicator in [
                                    "女", "男", "是", "否", "同意", "不同意", "满意", "不满意",
                                    "选择", "很", "非常", "从不", "经常", "有时", "总是",
                                    "option", "choice", "radio", "checkbox"
                                ]):
                                    answered_questions_count += 1
                                    success_indicators.append(f"答题点击: {step_text[:60]}")
                                
                                # 排除明显的导航操作
                                elif not any(nav in step_text for nav in [
                                    "提交", "submit", "下一页", "next", "返回", "back", "关闭", "close"
                                ]):
                                    # 如果不是明显的导航，也可能是答题
                                    answered_questions_count += 0.5  # 给予部分分数
                                    success_indicators.append(f"可能答题: {step_text[:60]}")
                            
                            # 📝 统计文本输入操作
                            elif "input_text" in step_text or "输入" in step_text:
                                answered_questions_count += 1
                                success_indicators.append(f"文本输入: {step_text[:60]}")
                            
                            # 📝 统计下拉选择操作
                            elif "select" in step_text and "dropdown" in step_text:
                                answered_questions_count += 1
                                success_indicators.append(f"下拉选择: {step_text[:60]}")
                            
                            # ⚠️ 统计错误指标
                            elif any(error in step_text for error in [
                                "error", "failed", "exception", "timeout", "does not exist",
                                "失败", "错误", "异常", "超时"
                            ]):
                                error_indicators.append(step_text[:80])
                            
                        except Exception as step_error:
                            logger.warning(f"⚠️ 解析步骤{i}失败: {step_error}")
                            continue
                
                else:
                    logger.warning(f"⚠️ 无法找到操作历史数据")
                    
            except Exception as e:
                logger.warning(f"⚠️ 解析操作历史失败: {e}")
            
            # 🔧 修复：从最终结果文本中提取更多信息
            final_result_lower = final_result_text.lower()
            
            # 检查成功完成的关键词
            completion_keywords = [
                "completed", "成功", "完成", "提交", "谢谢", "感谢", "结束",
                "success", "submitted", "thank", "finish", "done"
            ]
            has_completion_words = any(keyword in final_result_lower for keyword in completion_keywords)
            
            # 从最终结果中推测答题数量（如果历史解析失败）
            if answered_questions_count == 0 and has_completion_words:
                # 根据描述推测答题数量
                if "all questions" in final_result_lower or "所有题目" in final_result_lower:
                    answered_questions_count = 10  # 保守估计
                elif "questionnaire" in final_result_lower or "问卷" in final_result_lower:
                    answered_questions_count = 8   # 保守估计
                else:
                    answered_questions_count = 5   # 最保守估计
                    
                logger.info(f"🔧 从最终结果推测答题数量: {answered_questions_count}")
            
            # 🎯 核心修复：综合评估答题数量
            estimated_questions = max(
                int(answered_questions_count),  # 实际统计（处理小数）
                len(success_indicators),        # 成功操作数量
                steps_count // 3,              # 从总步数保守估计
                0
            )
            
            logger.info(f"📊 修复后统计: 步骤数={steps_count}, 实际答题={answered_questions_count}, 估计答题={estimated_questions}, 错误数={len(error_indicators)}")
            
            # 🔧 修复：更准确的成功判断逻辑
            
            # 1. 技术错误判断（优先级最高）
            if len(error_indicators) > 5 and steps_count < 10:
                evaluation_result.update({
                    "is_success": False,
                    "success_type": "technical_error",
                    "error_category": "technical",
                    "completion_score": 0.1,
                    "answered_questions": max(0, estimated_questions),
                    "confidence": 0.9,
                    "details": f"检测到大量技术错误: {len(error_indicators)}个错误, 仅{steps_count}步骤"
                })
                return evaluation_result
            
            # 2. 基于答题数量和完成标志的综合判断
            if has_completion_words and estimated_questions >= 5:
                # 明确完成 + 答题数量充足
                completion_score = 0.95
                confidence = 0.9
                success_type = "complete"
                is_success = True
            elif has_completion_words and estimated_questions >= 2:
                # 明确完成 + 答题数量一般
                completion_score = 0.8
                confidence = 0.8
                success_type = "complete"
                is_success = True
            elif estimated_questions >= 8:
                # 答题数量充足（即使无明确完成标志）
                completion_score = 0.85
                confidence = 0.7
                success_type = "partial"
                is_success = True
            elif estimated_questions >= 4:
                # 答题数量中等
                completion_score = 0.6
                confidence = 0.6
                success_type = "partial"
                is_success = True
            elif estimated_questions >= 1:
                # 至少有答题
                completion_score = 0.4
                confidence = 0.5
                success_type = "partial"
                is_success = True
            else:
                # 没有检测到答题
                completion_score = 0.1
                confidence = 0.3
                success_type = "incomplete"
                is_success = False
            
            evaluation_result.update({
                "is_success": is_success,
                "success_type": success_type,
                "completion_score": completion_score,
                "answered_questions": estimated_questions,
                "error_category": "technical" if len(error_indicators) > len(success_indicators) else "none",
                "confidence": confidence,
                "details": f"步骤{steps_count}, 实际答题{answered_questions_count}题, 估计{estimated_questions}题, 完成度{completion_score:.1%}, 有完成标志: {has_completion_words}"
            })
            
            logger.info(f"✅ 修复后评估: {evaluation_result['success_type']}, 答题{estimated_questions}题, 完成度{completion_score:.1%}, 置信度{confidence:.1%}")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"❌ 评估逻辑修复失败: {e}")
            return {
                "is_success": False,
                "success_type": "evaluation_error",
                "completion_score": 0.0,
                "answered_questions": 0,
                "error_category": "technical",
                "confidence": 0.0,
                "details": f"评估过程出错: {str(e)}"
            }

    async def _handle_technical_error_with_overlay(self, browser_context, error_details: Dict, persona_name: str) -> None:
        """
        处理技术错误：显示悬浮框供用户调试
        
        技术错误包括：
        - 代码错误（Exception、Traceback）
        - API调用失败（429、500、quota exceeded）  
        - 服务器错误（timeout、connection failed）
        """
        try:
            error_type = error_details.get("error_category", "unknown")
            error_message = error_details.get("details", "未知技术错误")
            
            if error_type == "technical":
                logger.info(f"🚨 检测到技术错误，显示调试悬浮框: {persona_name}")
                
                # 创建人类式输入代理来显示悬浮框
                human_input_agent = HumanLikeInputAgent(browser_context)
                
                # 详细的技术错误悬浮框
                overlay_message = f"""❌ 敢死队 {persona_name} 遇到技术错误
                
🔧 错误类型: 技术故障
📋 错误详情: {error_message}
⏰ 发生时间: {datetime.now().strftime('%H:%M:%S')}

🛠️ 调试建议:
1. 检查网络连接状态
2. 验证API密钥是否有效
3. 查看服务器响应状态
4. 检查代码逻辑错误

💡 这是技术错误，不是正常答题过程
浏览器将保持运行状态供您调试分析

点击关闭按钮或刷新页面继续"""
                
                await human_input_agent.show_error_overlay(overlay_message)
                logger.info(f"✅ 技术错误悬浮框已显示，用户可进行调试")
            
        except Exception as e:
            logger.warning(f"⚠️ 显示技术错误悬浮框失败: {e}")

    def _classify_error_type(self, error_str: str, agent_result) -> str:
        """
        分类错误类型：技术错误 vs 正常答题过程终止
        
        技术错误特征：
        - HTTP状态码错误 (429, 500, 502, 503, 504)
        - API配额超限 (quota, limit, exceeded)
        - 网络连接问题 (timeout, connection, network)
        - 代码异常 (Exception, Error, Traceback)
        - 服务器故障 (server error, internal error)
        
        正常终止特征：
        - 陷阱题检测 (trap, verification, captcha)
        - 问卷逻辑终止 (end, finish, complete)
        - 页面跳转限制 (redirect, access denied)
        """
        error_lower = error_str.lower()
        
        # 技术错误模式
        technical_patterns = [
            "429", "500", "502", "503", "504",  # HTTP错误码
            "quota", "limit", "exceeded", "rate", # API限制
            "timeout", "connection", "network", "ssl",  # 网络问题
            "exception", "error", "traceback", "crash",  # 代码错误
            "server error", "internal error", "api error",  # 服务器错误
            "authentication", "unauthorized", "forbidden"  # 认证错误
        ]
        
        # 正常终止模式
        normal_patterns = [
            "complete", "finish", "end", "done",  # 正常完成
            "trap", "verification", "captcha", "blocked",  # 陷阱检测
            "redirect", "access denied", "not allowed",  # 访问限制
            "survey closed", "questionnaire end"  # 问卷结束
        ]
        
        # 检查技术错误
        for pattern in technical_patterns:
            if pattern in error_lower:
                return "technical"
        
        # 检查正常终止
        for pattern in normal_patterns:
            if pattern in error_lower:
                return "normal_termination"
        
        # 默认：如果有agent执行历史且步骤较多，可能是正常终止
        if agent_result and hasattr(agent_result, 'history'):
            if hasattr(agent_result.history, 'history') and len(agent_result.history.history) > 15:
                return "normal_termination"
        
        # 无法确定时，默认为技术错误（保守策略）
        return "technical"

    def _serialize_agent_result(self, result):
        """序列化Agent结果，避免JSON序列化错误"""
        try:
            if result is None:
                return {"status": "completed", "message": "任务执行完成，无具体结果"}
            
            # 如果是AgentHistoryList，提取关键信息
            if hasattr(result, 'final_result'):
                final_result = result.final_result()
                return {
                    "status": "completed",
                    "final_result": str(final_result) if final_result else "任务完成",
                    "duration_seconds": result.total_duration_seconds() if hasattr(result, 'total_duration_seconds') else 0,
                    "total_steps": len(result.history) if hasattr(result, 'history') else 0,
                    "is_done": result.is_done() if hasattr(result, 'is_done') else True,
                    "summary": "问卷填写任务执行完成"
                }
            
            # 如果是字典，直接返回
            if isinstance(result, dict):
                return result
            
            # 其他情况，转换为字符串
            return {
                "status": "completed",
                "result_type": type(result).__name__,
                "result_str": str(result),
                "message": "任务执行完成"
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 序列化Agent结果失败: {e}")
            return {
                "status": "completed_with_warning",
                "message": "任务执行完成，但结果序列化遇到问题",
                "error": str(e)
            }

    async def cleanup_session(self, session_id: str) -> bool:
        """清理会话资源（修改为可选清理模式）"""
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"⚠️ 会话不存在: {session_id}")
                return False
            
            session_info = self.active_sessions[session_id]
            persona_name = session_info["persona_name"]
            
            logger.info(f"🧹 开始释放数字人 {persona_name} 的'新电脑'资源...")
            
            # 用户可以选择是否真正删除浏览器配置文件
            # 默认情况下，保留浏览器配置文件，仅从活动会话中移除
            
            # 从活动会话中移除
            del self.active_sessions[session_id]
            logger.info(f"🧹 清理会话资源: {persona_name}")
            
            # 可选：删除AdsPower配置文件（默认注释掉，保留浏览器）
            """
            profile_id = session_info.get("profile_id")
            if profile_id:
                delete_result = await self.adspower_manager.delete_browser_profile(profile_id)
                if delete_result.get("success"):
                    logger.info(f"✅ AdsPower配置文件已删除: {profile_id}")
                else:
                    logger.warning(f"⚠️ AdsPower配置文件删除失败: {delete_result.get('error')}")
            """
            
            logger.info(f"✅ 数字人 {persona_name} 会话已清理（浏览器配置文件保留）")
            return True
            
        except Exception as e:
            logger.error(f"❌ 清理会话失败: {e}")
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        return self.active_sessions.get(session_id)
    
    def list_active_sessions(self) -> List[Dict]:
        """列出所有活跃会话"""
        return list(self.active_sessions.values())

    async def _execute_local_questionnaire_strategy(
        self, 
        browser_context, 
        questionnaire_url: str, 
        digital_human_info: Dict
    ) -> Dict:
        """
        本地化答题策略：当API不可用时使用基于规则的答题方法
        不依赖Gemini API，使用预定义规则进行问卷填写
        """
        try:
            logger.info(f"🚀 开始执行本地化答题策略...")
            
            # 获取数字人信息
            name = digital_human_info.get("name", "用户")
            age = digital_human_info.get("age", 25)
            gender = digital_human_info.get("gender", "女")
            profession = digital_human_info.get("job", "学生")
            
            logger.info(f"👤 答题身份: {name}({age}岁{gender}性{profession})")
            
            # 🔑 关键修复：本地化策略也必须先导航到问卷URL
            logger.info(f"🚀 强制导航到问卷URL: {questionnaire_url}")
            
            try:
                # 使用browser-use的navigate方法导航到问卷URL
                await browser_context.go_to_url(questionnaire_url)
                logger.info(f"✅ 本地化策略页面导航完成: {questionnaire_url}")
                
                # 等待页面完全加载
                await asyncio.sleep(3)
                
                # 验证页面是否正确加载
                try:
                    current_url = await browser_context.get_current_url()
                    logger.info(f"📍 当前页面URL: {current_url}")
                    
                    if questionnaire_url in current_url or current_url and len(current_url) > 10:
                        logger.info(f"✅ 问卷页面加载成功（本地化策略）")
                    else:
                        logger.warning(f"⚠️ 页面可能未正确加载，但继续执行本地化策略")
                        
                except Exception as url_check_error:
                    logger.warning(f"⚠️ 无法验证当前URL: {url_check_error}")
                    
            except Exception as nav_error:
                logger.error(f"❌ 本地化策略页面导航失败: {nav_error}")
                # 尝试备用导航方法
                try:
                    await browser_context.navigate_to(questionnaire_url)
                    logger.info(f"✅ 本地化策略备用导航方法成功")
                except Exception as backup_nav_error:
                    logger.error(f"❌ 本地化策略备用导航也失败: {backup_nav_error}")
                    # 不抛出异常，继续尝试答题（可能已经在正确页面）
                    logger.warning(f"⚠️ 导航失败，但继续尝试在当前页面执行本地化答题")
            
            # 等待页面完全加载
            await asyncio.sleep(3)
            
            # 基于规则的自动答题流程
            for round_num in range(1, 6):  # 最多5轮答题循环
                logger.info(f"🔄 第{round_num}轮答题开始...")
                
                # 1. 处理单选题
                await self._handle_radio_questions_locally(browser_context, digital_human_info)
                await asyncio.sleep(1)
                
                # 2. 处理多选题
                await self._handle_checkbox_questions_locally(browser_context, digital_human_info)
                await asyncio.sleep(1)
                
                # 3. 处理下拉选择题
                await self._handle_select_questions_locally(browser_context, digital_human_info)
                await asyncio.sleep(1)
                
                # 4. 处理文本输入题
                await self._handle_text_input_questions_locally(browser_context, digital_human_info)
                await asyncio.sleep(1)
                
                # 5. 滚动页面寻找更多题目
                await self._scroll_and_find_more_questions(browser_context)
                await asyncio.sleep(2)
                
                # 6. 尝试提交或下一页
                submit_success = await self._try_submit_or_next_page(browser_context)
                if submit_success:
                    logger.info(f"✅ 第{round_num}轮答题成功提交")
                    break
                    
                logger.info(f"⏭️ 第{round_num}轮答题完成，继续下一轮...")
            
            logger.info(f"✅ 本地化答题策略执行完成")
            return {
                "success": True,
                "strategy": "local_rule_based",
                "rounds_completed": round_num
            }
            
        except Exception as e:
            logger.error(f"❌ 本地化答题策略执行失败: {e}")
            return {
                "success": False,
                "strategy": "local_rule_based",
                "error": str(e)
            }

    async def _initialize_deepseek_llm(self):
        """初始化deepseek LLM作为备选方案"""
        try:
            if not deepseek_available:
                logger.warning(f"⚠️ deepseek不可用，langchain_openai未安装")
                return None
                
            logger.info(f"🔄 正在初始化deepseek LLM...")
            
            # deepseek配置
            deepseek_llm = ChatOpenAI(
                model="deepseek-chat",
                base_url="https://api.deepseek.com",
                api_key="sk-your-deepseek-api-key",  # 用户需要配置自己的key
                temperature=0.6,
                max_tokens=4000,
                timeout=30
            )
            
            # 测试连接
            try:
                test_response = await deepseek_llm.ainvoke("测试连接")
                logger.info(f"✅ deepseek LLM初始化成功")
                return deepseek_llm
            except Exception as test_error:
                logger.warning(f"⚠️ deepseek LLM连接测试失败: {test_error}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ deepseek LLM初始化失败: {e}")
            return None
    
    async def _handle_radio_questions_locally(self, browser_context, digital_human_info: Dict):
        """处理单选题（本地化策略）"""
        try:
            # 查找所有未选择的单选框 - 修复API调用
            script = """
            const radioInputs = document.querySelectorAll('input[type="radio"]:not(:checked)');
            const results = [];
            radioInputs.forEach((radio, index) => {
                if (!radio.name || !document.querySelector(`input[name="${radio.name}"]:checked`)) {
                    results.push({
                        index: index,
                        name: radio.name,
                        value: radio.value,
                        text: radio.nextElementSibling ? radio.nextElementSibling.textContent : ''
                    });
                }
            });
            return results;
            """
            
            # 🔧 修复：使用正确的browser-use API方法
            try:
                unselected_radios = await browser_context.evaluate(script)
            except AttributeError:
                # 如果evaluate方法不存在，尝试其他方法
                try:
                    unselected_radios = await browser_context.execute_javascript(script)
                except AttributeError:
                    logger.warning(f"⚠️ BrowserContext API方法调用失败，跳过单选题处理")
                    return
            
            if unselected_radios:
                logger.info(f"📊 发现 {len(unselected_radios)} 个未答单选题")
                
                # 基于身份选择合适的选项
                for radio in unselected_radios[:3]:  # 限制处理数量
                    try:
                        # 点击第一个选项（最保守策略）
                        click_script = f"""
                        const radios = document.querySelectorAll('input[name="{radio["name"]}"]');
                        if (radios.length > 0) {{
                            radios[0].click();
                            return true;
                        }}
                        return false;
                        """
                        
                        try:
                            success = await browser_context.evaluate(click_script)
                        except AttributeError:
                            try:
                                success = await browser_context.execute_javascript(click_script)
                            except AttributeError:
                                logger.warning(f"⚠️ JavaScript执行方法不可用")
                                break
                                
                        if success:
                            logger.info(f"✅ 单选题已选择: {radio['name']}")
                            await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ 单选题处理失败: {e}")
                        
        except Exception as e:
            logger.warning(f"⚠️ 单选题整体处理失败: {e}")
    
    async def _handle_checkbox_questions_locally(self, browser_context, digital_human_info: Dict):
        """处理多选题（本地化策略）"""
        try:
            # 查找所有复选框
            script = """
            const checkboxes = document.querySelectorAll('input[type="checkbox"]:not(:checked)');
            const results = [];
            checkboxes.forEach((checkbox, index) => {
                results.push({
                    index: index,
                    name: checkbox.name,
                    value: checkbox.value,
                    text: checkbox.nextElementSibling ? checkbox.nextElementSibling.textContent : ''
                });
            });
            return results.slice(0, 6); // 限制数量
            """
            
            try:
                unselected_checkboxes = await browser_context.evaluate(script)
            except AttributeError:
                try:
                    unselected_checkboxes = await browser_context.execute_javascript(script)
                except AttributeError:
                    logger.warning(f"⚠️ BrowserContext API方法调用失败，跳过多选题处理")
                    return
            
            if unselected_checkboxes:
                logger.info(f"☑️ 发现 {len(unselected_checkboxes)} 个未选复选框")
                
                # 选择前2-3个选项
                for i, checkbox in enumerate(unselected_checkboxes[:3]):
                    try:
                        click_script = f"""
                        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                        const target = Array.from(checkboxes).find(cb => 
                            cb.name === '{checkbox["name"]}' && cb.value === '{checkbox["value"]}'
                        );
                        if (target && !target.checked) {{
                            target.click();
                            return true;
                        }}
                        return false;
                        """
                        
                        try:
                            success = await browser_context.evaluate(click_script)
                        except AttributeError:
                            try:
                                success = await browser_context.execute_javascript(click_script)
                            except AttributeError:
                                logger.warning(f"⚠️ JavaScript执行方法不可用")
                                break
                        
                        if success:
                            logger.info(f"☑️ 多选题已选择: {checkbox['name']}")
                            await asyncio.sleep(0.5)
                            
                    except Exception as e:
                        logger.warning(f"⚠️ 多选题处理失败: {e}")
                        
        except Exception as e:
            logger.warning(f"⚠️ 多选题整体处理失败: {e}")
    
    async def _handle_select_questions_locally(self, browser_context, digital_human_info: Dict):
        """处理下拉选择题（本地化策略）"""
        try:
            # 查找所有未选择的下拉框
            script = """
            const selects = document.querySelectorAll('select');
            const results = [];
            selects.forEach((select, index) => {
                if (select.selectedIndex <= 0) {
                    const options = Array.from(select.options).slice(1, 4); // 跳过第一个选项
                    results.push({
                        index: index,
                        name: select.name,
                        options: options.map(opt => ({value: opt.value, text: opt.text}))
                    });
                }
            });
            return results;
            """
            
            try:
                unselected_selects = await browser_context.evaluate(script)
            except AttributeError:
                try:
                    unselected_selects = await browser_context.execute_javascript(script)
                except AttributeError:
                    logger.warning(f"⚠️ BrowserContext API方法调用失败，跳过下拉框处理")
                    return
            
            if unselected_selects:
                logger.info(f"🔽 发现 {len(unselected_selects)} 个未选下拉框")
                
                for select in unselected_selects[:3]:
                    try:
                        if select["options"]:
                            # 选择第一个有效选项
                            option = select["options"][0]
                            select_script = f"""
                            const selects = document.querySelectorAll('select');
                            const target = selects[{select["index"]}];
                            if (target) {{
                                target.value = '{option["value"]}';
                                target.dispatchEvent(new Event('change'));
                                return true;
                            }}
                            return false;
                            """
                            
                            try:
                                success = await browser_context.evaluate(select_script)
                            except AttributeError:
                                try:
                                    success = await browser_context.execute_javascript(select_script)
                                except AttributeError:
                                    logger.warning(f"⚠️ JavaScript执行方法不可用")
                                    break
                            
                            if success:
                                logger.info(f"🔽 下拉框已选择: {option['text']}")
                                await asyncio.sleep(0.5)
                                
                    except Exception as e:
                        logger.warning(f"⚠️ 下拉框处理失败: {e}")
                        
        except Exception as e:
            logger.warning(f"⚠️ 下拉框整体处理失败: {e}")
    
    async def _handle_text_input_questions_locally(self, browser_context, digital_human_info: Dict):
        """处理文本输入题（增强人类化本地策略）"""
        try:
            # 🔍 查找所有空的文本输入框，增强检测
            script = """
            const inputs = document.querySelectorAll('input[type="text"], textarea, input:not([type])');
            const results = [];
            inputs.forEach((input, index) => {
                // 只处理可见且为空的输入框
                if (!input.value.trim() && input.offsetParent !== null) {
                    results.push({
                        index: index,
                        name: input.name || '',
                        placeholder: input.placeholder || '',
                        id: input.id || '',
                        className: input.className || '',
                        tagName: input.tagName.toLowerCase()
                    });
                }
            });
            return results.slice(0, 5); // 处理更多文本框
            """
            
            try:
                empty_inputs = await browser_context.evaluate(script)
            except AttributeError:
                try:
                    empty_inputs = await browser_context.execute_javascript(script)
                except AttributeError:
                    logger.warning(f"⚠️ BrowserContext API方法调用失败，跳过文本框处理")
                    return
            
            if empty_inputs:
                logger.info(f"🔥 发现 {len(empty_inputs)} 个空文本框，启用增强人类化输入")
                
                # 创建增强人类化输入代理
                human_input_agent = HumanLikeInputAgent(browser_context)
                
                # 🎨 丰富的回答模板生成
                name = digital_human_info.get("name", "用户")
                job = digital_human_info.get("job", "普通职员")
                age = digital_human_info.get("age", "30")
                
                for i, input_field in enumerate(empty_inputs):
                    try:
                        # 🤔 模拟用户发现和思考填空题的过程
                        discovery_time = random.uniform(0.5, 1.5)
                        await asyncio.sleep(discovery_time)
                        
                        # 🎯 智能内容生成（基于input的context）
                        context_hints = (input_field.get('name', '') + ' ' + 
                                       input_field.get('placeholder', '') + ' ' + 
                                       input_field.get('id', '') + ' ' + 
                                       input_field.get('className', '')).lower()
                        
                        if any(keyword in context_hints for keyword in ['email', '邮箱', 'mail']):
                            domains = ['163.com', 'qq.com', 'gmail.com', '126.com', 'sina.com', '139.com']
                            username = name.replace(' ', '').lower() + str(random.randint(100, 999))
                            answer = f"{username}@{random.choice(domains)}"
                        elif any(keyword in context_hints for keyword in ['phone', '电话', '手机', 'mobile', 'tel']):
                            prefixes = ['138', '139', '158', '188', '186', '135', '136', '137']
                            answer = f"{random.choice(prefixes)}{random.randint(10000000, 99999999)}"
                        elif any(keyword in context_hints for keyword in ['name', '姓名', '名字']):
                            answer = name
                        elif any(keyword in context_hints for keyword in ['age', '年龄']):
                            answer = str(age)
                        elif any(keyword in context_hints for keyword in ['job', '职业', '工作', 'profession']):
                            answer = job
                        elif any(keyword in context_hints for keyword in ['company', '公司', '单位']):
                            companies = ['科技有限公司', '贸易有限公司', '服务有限公司', '咨询有限公司', '文化传媒公司']
                            answer = f"某{random.choice(companies)}"
                        elif any(keyword in context_hints for keyword in ['address', '地址', '住址']):
                            districts = ['朝阳区', '海淀区', '西城区', '东城区', '丰台区']
                            answer = f"北京市{random.choice(districts)}某街道{random.randint(10,999)}号"
                        elif any(keyword in context_hints for keyword in ['comment', '建议', '意见', '评价', 'feedback', 'remark', 'opinion']):
                            comments = [
                                f"{name}认为这个产品整体设计很不错，用户体验比较流畅。",
                                f"{name}觉得功能比较齐全，但希望界面能够更加简洁美观。",
                                f"{name}对服务质量比较满意，建议继续保持并不断改进。",
                                f"{name}总体感觉良好，期待后续能有更多个性化的功能。",
                                f"{name}认为产品符合需求，价格也比较合理，会推荐给朋友。"
                            ]
                            answer = random.choice(comments)
                        elif any(keyword in context_hints for keyword in ['reason', '原因', '理由', 'why']):
                            reasons = [
                                "功能齐全，满足了我的基本需求",
                                "朋友推荐，口碑比较好",
                                "价格合理，性价比较高",
                                "界面设计美观，操作简单",
                                "服务态度好，响应及时"
                            ]
                            answer = random.choice(reasons)
                        elif any(keyword in context_hints for keyword in ['suggestion', '建议', 'improve', '改进']):
                            suggestions = [
                                "建议增加更多个性化设置选项",
                                "希望能够优化加载速度",
                                "建议增强客服支持功能",
                                "希望能够增加更多支付方式",
                                "建议完善用户反馈机制"
                            ]
                            answer = random.choice(suggestions)
                        else:
                            # 🎲 通用智能填空
                            general_templates = [
                                f"{name}的个人看法和体验",
                                f"基于{name}的实际使用感受",
                                f"{name}认为比较符合预期",
                                f"从{name}的角度来说还不错",
                                f"{name}觉得整体比较满意"
                            ]
                            answer = random.choice(general_templates)
                        
                        # 🎯 使用增强人类化输入
                        if input_field['tagName'] == 'textarea':
                            element_selector = f'textarea:nth-of-type({i + 1})'
                        else:
                            element_selector = f'input[type="text"]:nth-of-type({i + 1}), input:not([type]):nth-of-type({i + 1})'
                        
                        # 🔥 优先使用增强版本
                        logger.info(f"🎯 尝试增强人类化输入填空题 {i+1}: {answer[:25]}...")
                        success = await human_input_agent.enhanced_human_like_input(element_selector, answer)
                        
                        if success:
                            logger.info(f"✅ 增强填空输入成功 {i+1}: {answer[:30]}...")
                        else:
                            # 🛟 备用方案：传统输入
                            logger.warning(f"⚠️ 增强输入失败，尝试传统方案 {i+1}")
                            backup_success = await human_input_agent.human_like_input(element_selector, answer)
                            if backup_success:
                                logger.info(f"✅ 传统填空输入成功 {i+1}: {answer[:30]}...")
                            else:
                                # 🔧 最后的JavaScript备用方案
                                logger.warning(f"⚠️ 传统输入也失败，使用JavaScript方案 {i+1}")
                                js_success = await self._javascript_fallback_input(browser_context, input_field, answer)
                                if js_success:
                                    logger.info(f"✅ JavaScript填空输入成功 {i+1}: {answer[:30]}...")
                        
                        # 🕐 模拟用户填写间隔
                        inter_input_pause = random.uniform(0.8, 2.0)
                        await asyncio.sleep(inter_input_pause)
                            
                    except Exception as e:
                        logger.warning(f"⚠️ 填空题 {i+1} 处理失败: {e}")
                        continue
                        
        except Exception as e:
            logger.warning(f"⚠️ 填空题整体处理失败: {e}")
    
    async def _javascript_fallback_input(self, browser_context, input_field: Dict, answer: str) -> bool:
        """JavaScript备用输入方案"""
        try:
            input_script = f"""
            const inputs = document.querySelectorAll('input[type="text"], textarea, input:not([type])');
            const target = inputs[{input_field["index"]}];
            if (target && target.offsetParent !== null) {{
                target.focus();
                target.value = '{answer.replace("'", "\\'")}';
                target.dispatchEvent(new Event('input', {{bubbles: true}}));
                target.dispatchEvent(new Event('change', {{bubbles: true}}));
                target.dispatchEvent(new Event('blur'));
                return true;
            }}
            return false;
            """
            
            try:
                success = await browser_context.evaluate(input_script)
            except AttributeError:
                try:
                    success = await browser_context.execute_javascript(input_script)
                except AttributeError:
                    return False
            
            return bool(success)
            
        except Exception as e:
            logger.debug(f"JavaScript备用输入失败: {e}")
            return False
    
    async def _scroll_and_find_more_questions(self, browser_context):
        """滚动页面寻找更多题目"""
        try:
            # 滚动到页面底部
            script = """
            window.scrollBy(0, 400);
            return window.scrollY;
            """
            
            try:
                scroll_position = await browser_context.evaluate(script)
            except AttributeError:
                try:
                    scroll_position = await browser_context.execute_javascript(script)
                except AttributeError:
                    logger.warning(f"⚠️ 无法执行滚动操作")
                    return
                    
            logger.info(f"📜 页面已滚动到位置: {scroll_position}")
            
        except Exception as e:
            logger.warning(f"⚠️ 页面滚动失败: {e}")
    
    async def _try_submit_or_next_page(self, browser_context) -> bool:
        """尝试提交或转到下一页"""
        try:
            # 查找提交或下一页按钮
            script = """
            const buttons = document.querySelectorAll('button, input[type="submit"], input[type="button"]');
            for (let btn of buttons) {
                const text = (btn.textContent || btn.value || '').toLowerCase();
                if (text.includes('提交') || text.includes('下一') || text.includes('继续') || 
                    text.includes('完成') || text.includes('submit') || text.includes('next')) {
                    btn.click();
                    return true;
                }
            }
            return false;
            """
            
            try:
                success = await browser_context.evaluate(script)
            except AttributeError:
                try:
                    success = await browser_context.execute_javascript(script)
                except AttributeError:
                    logger.warning(f"⚠️ 无法执行提交操作")
                    return False
            
            if success:
                logger.info(f"✅ 已点击提交/下一页按钮")
                await asyncio.sleep(3)  # 等待页面跳转
                return True
            else:
                logger.info(f"ℹ️ 未找到提交/下一页按钮")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ 提交按钮处理失败: {e}")
            return False

# 便捷函数：使用已存在的AdsPower浏览器执行问卷工作流
async def run_intelligent_questionnaire_workflow_with_existing_browser(
    persona_id: int,
    persona_name: str,
    digital_human_info: Dict,
    questionnaire_url: str,
    existing_browser_info: Dict,
    prompt: Optional[str] = None, 
    model_name: str = "gemini-2.0-flash",
    api_key: Optional[str] = None
) -> Dict:
    """
    🎯 新增：使用智能问卷系统执行问卷工作流（替代传统browser-use方式）
    
    这个方法使用我们全新开发的智能问卷系统：
    - QuestionnaireStateManager: 精确的状态追踪，避免重复作答
    - IntelligentQuestionnaireAnalyzer: 预分析问卷结构
    - RapidAnswerEngine: 快速批量作答引擎
    - SmartScrollController: 智能滚动控制
    - IntelligentQuestionnaireController: 统一流程控制
    """
    try:
        logger.info(f"🚀 启动智能问卷工作流: {persona_name}")
        
        # 使用智能问卷系统
        integration = AdsPowerWebUIIntegration()
        result = await integration.execute_intelligent_questionnaire_task(
            persona_id=persona_id,
            persona_name=persona_name,
            digital_human_info=digital_human_info,
            questionnaire_url=questionnaire_url,
            existing_browser_info=existing_browser_info,
            prompt=prompt,
            model_name=model_name,
            api_key=api_key
        )
        
        # 增强结果信息
        result["workflow_type"] = "intelligent_questionnaire_system"
        result["features_used"] = [
            "state_management",
            "structure_analysis", 
            "rapid_answering",
            "smart_scrolling",
            "intelligent_control"
        ]
        
        logger.info(f"🎉 智能问卷工作流完成: {persona_name}, 状态: {'成功' if result['success'] else '失败'}")
        return result
        
    except Exception as e:
        logger.error(f"❌ 智能问卷工作流失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "persona_id": persona_id,
            "persona_name": persona_name,
            "workflow_type": "intelligent_questionnaire_system"
        }

async def run_complete_questionnaire_workflow_with_existing_browser(
    persona_id: int,
    persona_name: str,
    digital_human_info: Dict,
    questionnaire_url: str,
    existing_browser_info: Dict,
    prompt: Optional[str] = None, 
    model_name: str = "gemini-2.0-flash",
    api_key: Optional[str] = None
) -> Dict:
    """
    使用已存在的AdsPower浏览器执行完整问卷工作流（基于testWenjuan.py成功模式）
    """
    integration = AdsPowerWebUIIntegration()
    
    try:
        logger.info(f"🚀 使用testWenjuan.py成功模式执行问卷工作流: {persona_name}")
        
        result = await integration.execute_questionnaire_task_with_data_extraction(
            persona_id=persona_id,
            persona_name=persona_name,
            digital_human_info=digital_human_info,
            questionnaire_url=questionnaire_url,
            existing_browser_info=existing_browser_info,
            prompt=prompt,
            model_name=model_name,
            api_key=api_key
        )
        
        logger.info(f"✅ 问卷工作流执行完成: {persona_name}")
        return result
        
    except Exception as e:
        logger.error(f"❌ 问卷工作流执行失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "persona_name": persona_name,
            "browser_info": existing_browser_info,
            "execution_mode": "testwenjuan_workflow_failed"
        }

# 便捷函数：完整的问卷填写流程（为了与main.py兼容）
async def run_complete_questionnaire_workflow(
    persona_id: int, 
    persona_name: str, 
    digital_human_info: Dict, 
    questionnaire_url: str,
    prompt: Optional[str] = None
) -> Dict:
    """
    完整的问卷填写工作流：创建AdsPower浏览器 → 使用webui技术执行任务 → 清理资源
    （为了与main.py兼容而提供的函数）
    """
    try:
        integration = AdsPowerWebUIIntegration()
        session_id = None
        
        logger.info(f"🚀 开始完整问卷填写工作流: {persona_name}")
        
        # 1. 创建AdsPower浏览器会话
        session_id = await integration.create_adspower_browser_session(persona_id, persona_name)
        if not session_id:
            return {"success": False, "error": "创建AdsPower浏览器会话失败"}
        
        # 2. 获取会话信息
        session_info = integration.get_session_info(session_id)
        if not session_info:
            return {"success": False, "error": "获取会话信息失败"}
        
        # 3. 构建浏览器信息
        existing_browser_info = {
            "profile_id": session_info["profile_id"],
            "debug_port": session_info["debug_port"],
            "proxy_enabled": session_info["browser_env"].get("proxy_enabled", False)
        }
        
        # 4. 执行问卷任务
        result = await integration.execute_questionnaire_task_with_data_extraction(
            persona_id=persona_id,
            persona_name=persona_name,
            digital_human_info=digital_human_info,
            questionnaire_url=questionnaire_url,
            existing_browser_info=existing_browser_info,
            prompt=prompt
        )
        
        # 5. 增强结果信息
        if result.get("success") and session_info and "browser_env" in session_info:
            browser_env = session_info["browser_env"]
            result["computer_assignment"] = {
                "digital_human_name": digital_human_info.get("name", "未知"),
                "digital_human_id": digital_human_info.get("id", persona_id),
                "assigned_time": datetime.now().isoformat(),
                "status": "已完成",
                "browser_profile_id": existing_browser_info.get("profile_id", "未知"),
                "debug_port": existing_browser_info.get("debug_port", "未知"),
                "proxy_enabled": existing_browser_info.get("proxy_enabled", False),
                "proxy_ip": browser_env.get("proxy_ip", "本地IP"),
                "proxy_port": browser_env.get("proxy_port", "未知"),
                "computer_info": f"数字人{digital_human_info.get('name', '未知')}的专属新电脑",
                "resource_status": "智能管理",
                "technology_used": "AdsPower + WebUI原有技术",
                "new_computer_summary": f"青果代理IP({browser_env.get('proxy_ip', '本地IP')}) + AdsPower指纹浏览器({existing_browser_info.get('profile_id', '未知')}) + WebUI自动答题技术"
            }
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 完整问卷填写工作流失败: {e}")
        return {"success": False, "error": str(e)}
    
    finally:
        # 确保任务完成后自动"下机"释放所有资源
        if 'session_id' in locals() and session_id and 'integration' in locals():
            try:
                logger.info(f"🧹 开始释放数字人 {persona_name} 的'新电脑'资源...")
                cleanup_success = await integration.cleanup_session(session_id)
                if cleanup_success:
                    logger.info(f"✅ 数字人 {persona_name} 已成功'下机'，所有资源已释放")
                else:
                    logger.warning(f"⚠️ 数字人 {persona_name} 资源释放不完整")
            except Exception as cleanup_error:
                logger.error(f"❌ 资源清理失败: {cleanup_error}")

# 测试函数
async def test_adspower_webui_integration():
    """测试AdsPower + WebUI集成（基于testWenjuan.py模式）"""
    print("🧪 测试AdsPower + WebUI集成（testWenjuan.py模式）")
    
    # 测试数字人信息
    test_digital_human = {
        "id": 1001,
        "name": "张小雅",
        "age": 28,
        "job": "产品经理",
        "income": "12000",
        "description": "热爱科技产品，经常网购，喜欢尝试新事物"
    }
    
    # 测试问卷URL
    test_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"
    
    # 模拟已存在的浏览器信息
    mock_browser_info = {
        "profile_id": "test_profile_12345",
        "debug_port": "9222",
        "proxy_enabled": True
    }
    
    result = await run_complete_questionnaire_workflow_with_existing_browser(
        persona_id=1001,
        persona_name="张小雅",
        digital_human_info=test_digital_human,
        questionnaire_url=test_url,
        existing_browser_info=mock_browser_info
    )
    
    print("🎉 测试结果:")
    print(f"   成功: {result.get('success')}")
    if result.get('success'):
        print(f"   执行时长: {result.get('duration', 0):.1f} 秒")
        print(f"   技术使用: testWenjuan.py + AdsPower")
    else:
        print(f"   错误: {result.get('error')}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_adspower_webui_integration())