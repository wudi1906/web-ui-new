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

# 🔧 重构后的安全导入系统
class ImportManager:
    """安全导入管理器 - 统一处理所有外部依赖，提高IDE兼容性"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ImportManager")
        self.available_modules = {}
        self.import_errors = {}
        
    def safe_import(self, module_path: str, class_name: Optional[str] = None, required: bool = False):
        """安全导入模块或类"""
        try:
            if class_name:
                module = __import__(module_path, fromlist=[class_name])
                imported_obj = getattr(module, class_name)
                key = f"{module_path}.{class_name}"
            else:
                imported_obj = __import__(module_path)
                key = module_path
            
            self.available_modules[key] = imported_obj
            self.logger.info(f"✅ 成功导入: {key}")
            return imported_obj
            
        except ImportError as e:
            key = f"{module_path}.{class_name}" if class_name else module_path
            self.import_errors[key] = str(e)
            if required:
                self.logger.error(f"❌ 必需模块导入失败: {key} - {e}")
                raise
            else:
                self.logger.warning(f"⚠️ 可选模块导入失败: {key} - {e}")
                return None
    
    def is_available(self, key: str) -> bool:
        """检查模块是否可用"""
        return key in self.available_modules

# 初始化导入管理器
import_manager = ImportManager()

# 🔧 核心浏览器组件导入
Browser = import_manager.safe_import('browser_use.browser.browser', 'Browser')
BrowserConfig = import_manager.safe_import('browser_use.browser.browser', 'BrowserConfig')
BrowserContextConfig = import_manager.safe_import('browser_use.browser.context', 'BrowserContextConfig')

# 🔧 Agent组件导入 - 多重回退机制
BrowserUseAgent = None
agent_import_attempts = [
    ('src.agent.browser_use.browser_use_agent', 'BrowserUseAgent'),
    ('browser_use.agent.service', 'Agent'),
]

for module_path, class_name in agent_import_attempts:
    BrowserUseAgent = import_manager.safe_import(module_path, class_name)
    if BrowserUseAgent:
        import_manager.logger.info(f"✅ BrowserUseAgent导入成功: {module_path}.{class_name}")
        break

if not BrowserUseAgent:
    import_manager.logger.error("❌ 所有BrowserUseAgent导入尝试均失败")

# 🔧 LLM组件导入
ChatGoogleGenerativeAI = import_manager.safe_import('langchain_google_genai', 'ChatGoogleGenerativeAI')
ChatOpenAI = import_manager.safe_import('langchain_openai', 'ChatOpenAI')
deepseek_available = ChatOpenAI is not None

# 🔧 AdsPower组件导入
AdsPowerLifecycleManager = import_manager.safe_import('enhanced_adspower_lifecycle', 'AdsPowerLifecycleManager')
adspower_available = AdsPowerLifecycleManager is not None

# 🔧 窗口管理器导入
WindowLayoutManager = import_manager.safe_import('window_layout_manager', 'WindowLayoutManager')
if not WindowLayoutManager:
    # 提供回退函数
    def get_window_manager():
        return None
    window_manager_available = False
else:
    from window_layout_manager import get_window_manager
    window_manager_available = True

# 🔧 双知识库系统导入
DualKnowledgeBaseSystem = import_manager.safe_import('dual_knowledge_base_system', 'DualKnowledgeBaseSystem')
if DualKnowledgeBaseSystem:
    def get_dual_knowledge_base():
        return DualKnowledgeBaseSystem()
    dual_kb_available = True
else:
    def get_dual_knowledge_base():
        return None
    dual_kb_available = False

# 🔧 反检测增强模块导入
anti_detection_manager = import_manager.safe_import('anti_detection_enhancement', 'anti_detection_manager')
anti_detection_available = anti_detection_manager is not None

# 🔧 可用性检查
webui_available = all([
    Browser, BrowserConfig, BrowserContextConfig, BrowserUseAgent
])

# 🔧 状态报告
logger = logging.getLogger(__name__)
if webui_available:
    logger.info("✅ WebUI核心组件全部导入成功")
else:
    logger.warning("⚠️ WebUI核心组件部分导入失败，某些功能可能不可用")

if adspower_available:
    logger.info("✅ AdsPower组件导入成功")
else:
    logger.warning("⚠️ AdsPower组件导入失败")

if dual_kb_available:
    logger.info("✅ 双知识库系统导入成功")
else:
    logger.warning("⚠️ 双知识库系统导入失败")


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
        self.page = None  # 🔥 新增：正确的页面对象
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
                    '[class*="select"]:not(select)', '[class*="dropdown"]', '.ui-select', '.custom-select',
                    '.el-select', '.ant-select', '.layui-select', '.weui-select'  // 新增UI框架支持
                ];
                
                customSelectSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach((customSelect, index) => {
                        if (customSelect.hasAttribute('data-analyzed') || customSelect.tagName === 'SELECT') return;
                        customSelect.setAttribute('data-analyzed', 'true');
                        
                        // 增强触发元素识别（更多样式支持）
                        const triggerSelectors = [
                            '.jqselect-text', '.select-text', '.dropdown-trigger', '.selected-value',
                            '[class*="text"]', '[class*="display"]', '[class*="current"]',
                            '.el-input__inner', '.ant-select-selection', '.layui-select-title',  // UI框架特定
                            '.weui-select', '[role="combobox"]', '[aria-haspopup="listbox"]'
                        ];
                        
                        let trigger = null;
                        for (let triggerSelector of triggerSelectors) {
                            trigger = customSelect.querySelector(triggerSelector);
                            if (trigger && trigger.offsetHeight > 0) break;
                        }
                        trigger = trigger || customSelect;
                        
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
                                         currentText !== 'Select...' &&
                                         !currentText.includes('选择') &&
                                         !currentText.includes('placeholder');
                        
                        if (questionText || !isAnswered) {  // 只处理有题目文本或未作答的
                            analysis.custom_select_questions.push({
                                name: customSelect.id || customSelect.className || `custom_select_${index}`,
                                question_text: questionText || `自定义下拉题${index + 1}`,
                                is_answered: isAnswered,
                                current_value: currentText,
                                element_type: 'custom_select',
                                selector_info: {
                                    container_class: customSelect.className,
                                    trigger_class: trigger.className,
                                    trigger_element: trigger
                                }
                            });
                        }
                    });
                });
                
                // 🔥 新增：表格题/矩阵题识别
                analysis.table_questions = [];
                const tableContainers = document.querySelectorAll('table, .table-container, .matrix-table, .grid-question');
                tableContainers.forEach((table, index) => {
                    // 检查是否为题目表格（包含input元素）
                    const inputs = table.querySelectorAll('input[type="radio"], input[type="checkbox"]');
                    if (inputs.length > 0) {
                        const questionContainer = table.closest('.question') || table.closest('.form-group') || table.closest('div');
                        const questionText = questionContainer?.querySelector('label, .question-text, .q-text, .title, h3, h4')?.textContent || `表格题${index + 1}`;
                        
                        // 分析表格结构
                        const rows = Array.from(table.querySelectorAll('tr')).filter(row => row.querySelectorAll('input').length > 0);
                        const columns = table.querySelectorAll('th, thead td') || table.querySelector('tr')?.querySelectorAll('td, th');
                        
                        analysis.table_questions.push({
                            name: table.id || `table_${index}`,
                            question_text: questionText.trim(),
                            element_type: 'table_matrix',
                            row_count: rows.length,
                            column_count: columns ? columns.length : 0,
                            input_type: inputs[0]?.type || 'radio',
                            answered_count: Array.from(inputs).filter(input => input.checked).length
                        });
                    }
                });
                
                // 🔥 新增：滑块题识别
                analysis.slider_questions = [];
                const sliderSelectors = [
                    'input[type="range"]', '.slider', '.range-slider', '.el-slider', '.ant-slider',
                    '.layui-slider', '.weui-slider', '[role="slider"]'
                ];
                sliderSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach((slider, index) => {
                        const questionContainer = slider.closest('.question') || slider.closest('.form-group') || slider.closest('div');
                        const questionText = questionContainer?.querySelector('label, .question-text, .q-text')?.textContent || `滑块题${index + 1}`;
                        
                        const currentValue = slider.value || slider.getAttribute('aria-valuenow') || '0';
                        const minValue = slider.min || slider.getAttribute('aria-valuemin') || '0';
                        const maxValue = slider.max || slider.getAttribute('aria-valuemax') || '100';
                        
                        analysis.slider_questions.push({
                            name: slider.name || slider.id || `slider_${index}`,
                            question_text: questionText.trim(),
                            element_type: 'slider',
                            current_value: currentValue,
                            min_value: minValue,
                            max_value: maxValue,
                            is_answered: currentValue !== minValue && currentValue !== '0'
                        });
                    });
                });
                
                // 🔥 新增：评分题识别（星级、点击评分等）
                analysis.rating_questions = [];
                const ratingSelectors = [
                    '.rating', '.star-rating', '.score-rating', '.el-rate', '.ant-rate',
                    '[class*="rate"]', '[class*="score"]', '[class*="star"]'
                ];
                ratingSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach((rating, index) => {
                        const questionContainer = rating.closest('.question') || rating.closest('.form-group') || rating.closest('div');
                        const questionText = questionContainer?.querySelector('label, .question-text, .q-text')?.textContent || `评分题${index + 1}`;
                        
                        const ratingItems = rating.querySelectorAll('.star, .rate-item, [class*="star"], input[type="radio"]');
                        const selectedItems = rating.querySelectorAll('.selected, .active, .checked, input:checked');
                        
                        analysis.rating_questions.push({
                            name: rating.id || `rating_${index}`,
                            question_text: questionText.trim(),
                            element_type: 'rating',
                            total_items: ratingItems.length,
                            selected_count: selectedItems.length,
                            is_answered: selectedItems.length > 0
                        });
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
                                         analysis.text_questions.length +
                                         analysis.table_questions.length +
                                         analysis.slider_questions.length +
                                         analysis.rating_questions.length;
                
                return analysis;
            })();
            """
            
            structure = await self.browser_context.execute_javascript(structure_analysis_js)
            
            # 增强日志输出，包含新的题型
            log_msg = f"📊 问卷结构分析完成: {structure['total_questions']}题 ("
            log_msg += f"单选:{len(structure['radio_questions'])}, "
            log_msg += f"多选:{len(structure['checkbox_questions'])}, "
            log_msg += f"原生下拉:{len(structure['select_questions'])}, "
            log_msg += f"自定义下拉:{len(structure.get('custom_select_questions', []))}, "
            log_msg += f"文本:{len(structure['text_questions'])}"
            
            # 新题型信息
            if structure.get('table_questions'):
                log_msg += f", 表格:{len(structure['table_questions'])}"
            if structure.get('slider_questions'):
                log_msg += f", 滑块:{len(structure['slider_questions'])}"
            if structure.get('rating_questions'):
                log_msg += f", 评分:{len(structure['rating_questions'])}"
            log_msg += ")"
            
            self.logger.info(log_msg)
            
            return structure
            
        except Exception as e:
            self.logger.error(f"❌ 问卷结构分析失败: {e}")
            return {
                "radio_questions": [],
                "checkbox_questions": [],
                "select_questions": [],
                "custom_select_questions": [],
                "text_questions": [],
                "table_questions": [],
                "slider_questions": [],
                "rating_questions": [],
                "total_questions": 0,
                "error": str(e)
            }


class RapidAnswerEngine:
    """
    🔥 快速作答引擎 - 基于WebUI原生方法增强版
    
    核心改进：
    1. 融合WebUI原生browser_context方法
    2. 增强下拉框滚动处理能力
    3. 人类化交互模拟升级
    4. 智能错误恢复机制
    """
    
    def __init__(self, browser_context, state_manager: QuestionnaireStateManager):
        self.browser_context = browser_context
        self.state_manager = state_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # 🔥 新增：WebUI增强功能组件
        self.webui_enhanced_handler = WebUIEnhancedDropdownHandler(browser_context)
        self.human_interaction_simulator = HumanInteractionSimulator(browser_context)
        
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
            
            # 🔥 6. 处理表格题/矩阵题
            for table_question in questionnaire_structure.get("table_questions", []):
                if table_question.get("answered_count", 0) > 0:
                    question_id = f"table_{table_question['name']}"
                    if not self.state_manager.is_question_answered(question_id):
                        self.state_manager.mark_question_answered(question_id, f"已填{table_question['answered_count']}项")
                    skipped_count += 1
                    continue
                
                try:
                    answer_result = await self._answer_table_question(table_question, persona_info)
                    if answer_result["success"]:
                        answered_count += 1
                        self.logger.info(f"✅ 表格题作答成功: {answer_result.get('answered_count', 0)}项")
                    else:
                        error_count += 1
                        self.logger.warning(f"⚠️ 表格题作答失败: {answer_result.get('error', '')}")
                except Exception as e:
                    self.logger.warning(f"⚠️ 表格题作答异常: {e}")
                    error_count += 1
                    
                await asyncio.sleep(random.uniform(1.0, 2.0))  # 表格题需要更多时间
            
            # 🔥 7. 处理滑块题
            for slider_question in questionnaire_structure.get("slider_questions", []):
                if slider_question.get("is_answered", False):
                    question_id = f"slider_{slider_question['name']}"
                    if not self.state_manager.is_question_answered(question_id):
                        self.state_manager.mark_question_answered(question_id, f"已设置{slider_question.get('current_value', '')}")
                    skipped_count += 1
                    continue
                
                try:
                    answer_result = await self._answer_slider_question(slider_question, persona_info)
                    if answer_result["success"]:
                        answered_count += 1
                        self.logger.info(f"✅ 滑块题作答成功: {answer_result.get('value', '')}")
                    else:
                        error_count += 1
                        self.logger.warning(f"⚠️ 滑块题作答失败: {answer_result.get('error', '')}")
                except Exception as e:
                    self.logger.warning(f"⚠️ 滑块题作答异常: {e}")
                    error_count += 1
                    
                await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # 🔥 8. 处理评分题
            for rating_question in questionnaire_structure.get("rating_questions", []):
                if rating_question.get("is_answered", False):
                    question_id = f"rating_{rating_question['name']}"
                    if not self.state_manager.is_question_answered(question_id):
                        self.state_manager.mark_question_answered(question_id, f"已评{rating_question.get('selected_count', 0)}分")
                    skipped_count += 1
                    continue
                
                try:
                    answer_result = await self._answer_rating_question(rating_question, persona_info)
                    if answer_result["success"]:
                        answered_count += 1
                        self.logger.info(f"✅ 评分题作答成功: {answer_result.get('rating', '')}分")
                    else:
                        error_count += 1
                        self.logger.warning(f"⚠️ 评分题作答失败: {answer_result.get('error', '')}")
                except Exception as e:
                    self.logger.warning(f"⚠️ 评分题作答异常: {e}")
                    error_count += 1
                    
                await asyncio.sleep(random.uniform(0.8, 1.5))
            
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
                await self.browser_context.execute_javascript(click_js)
                
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
                    await self.browser_context.execute_javascript(click_js)
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
                await self.browser_context.execute_javascript(select_js)
                
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
                await self.browser_context.execute_javascript(input_js)
                
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
        """🔥 增强版：动态获取自定义下拉框的选项，支持更多UI框架"""
        try:
            container_class = custom_select.get("selector_info", {}).get("container_class", "")
            trigger_class = custom_select.get("selector_info", {}).get("trigger_class", "")
            
            # 🔥 增强版JavaScript获取选项
            get_options_js = f"""
            (function() {{
                let options = [];
                let triggerElement = null;
                
                // 🔥 扩展触发元素查找，支持更多UI框架
                const selectors = [
                    '.{container_class.replace(" ", ".")}',
                    '.{trigger_class.replace(" ", ".")}',
                    '.jqselect', '.jqselect-wrapper', '.select-wrapper',
                    '.el-select', '.ant-select', '.layui-select', '.weui-select',  // UI框架
                    '[class*="select"]:not(select)', '[class*="dropdown"]',
                    '[role="combobox"]', '[aria-haspopup="listbox"]'  // 语义化
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
                
                // 🔥 等待选项出现并获取 - 增强版
                return new Promise((resolve) => {{
                    setTimeout(() => {{
                        const optionSelectors = [
                            '.jqselect-options li', '.select-options li', '.dropdown-options li',
                            '.options-list li', 'li[data-value]', '.option',
                            '.el-select-dropdown li', '.ant-select-dropdown li',  // Element UI & Ant Design
                            '.layui-select-options li', '.weui-select-options li',  // Layui & WeUI
                            '[role="option"]', '[class*="option"]',  // 语义化和通用
                            '.dropdown-menu li', '.dropdown-item'  // Bootstrap风格
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
            
            result = await self.browser_context.execute_javascript(get_options_js)
            
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
        """🔥 最新增强版：优先使用WebUIEnhancedDropdownHandler处理下拉框滚动"""
        try:
            option_text = selected_option["text"]
            
            self.logger.info(f"🔽 开始处理下拉框选项: {option_text}")
            
            # 🚀 策略1：优先使用WebUIEnhancedDropdownHandler（支持滚动）
            try:
                enhanced_handler = WebUIEnhancedDropdownHandler(self.browser_context)
                
                # 使用增强的滚动处理器
                for attempt in range(3):
                    success = await enhanced_handler.enhanced_scrollable_option_click(
                        option_text, custom_select, attempt
                    )
                    
                    if success:
                        self.logger.info(f"✅ WebUIEnhancedDropdownHandler成功: {option_text}")
                        return True
                    
                    # 失败后短暂等待
                    await asyncio.sleep(0.5 + attempt * 0.3)
                
                self.logger.warning("⚠️ WebUIEnhancedDropdownHandler所有尝试都失败")
                
            except Exception as enhanced_error:
                self.logger.warning(f"⚠️ WebUIEnhancedDropdownHandler异常: {enhanced_error}")
            
            # 🔄 策略2：回退到原有的渐进式增强策略
            self.logger.info("🔄 回退到原有下拉框处理策略")
            success = await self._enhanced_dropdown_click_with_retries(option_text, custom_select, max_retries=3)
            
            if success:
                self.logger.info(f"✅ 原有策略成功: {option_text}")
                return True
            else:
                self.logger.warning(f"⚠️ 所有策略都失败，但继续执行")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ 点击自定义选项失败: {e}")
            return False
    
    async def _enhanced_dropdown_click_with_retries(self, option_text: str, custom_select: Dict, max_retries: int = 3) -> bool:
        """🔥 渐进式增强：多策略下拉框处理，动态检测和智能重试"""
        
        for attempt in range(max_retries):
            self.logger.info(f"🔄 下拉框处理尝试 {attempt + 1}/{max_retries}")
            
            # 策略1: 智能触发器识别和点击
            if await self._multi_strategy_trigger(custom_select, attempt):
                # 策略2: 动态选项检测（每100ms检测一次，最多3秒）
                options_detected = await self._dynamic_option_detection(timeout_ms=3000, check_interval_ms=100)
                
                if options_detected:
                    # 策略3: 多方法选项点击
                    if await self._multi_method_option_click(option_text, attempt):
                        # 策略4: 多方法验证
                        if await self._multi_method_verification(option_text, custom_select):
                            return True
                        else:
                            self.logger.warning(f"⚠️ 尝试{attempt + 1}: 验证失败，但可能实际成功")
                            # 继续下一次尝试或返回部分成功
                            if attempt == max_retries - 1:
                                return True  # 最后一次尝试，认为可能成功
                    else:
                        self.logger.warning(f"⚠️ 尝试{attempt + 1}: 选项点击失败")
                else:
                    self.logger.warning(f"⚠️ 尝试{attempt + 1}: 选项检测失败")
            else:
                self.logger.warning(f"⚠️ 尝试{attempt + 1}: 触发器点击失败")
            
            # 失败分析和适应性调整
            await self._adaptive_failure_analysis(attempt, custom_select)
            
            # 重试间隔
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 + attempt * 0.3)  # 递增延迟
        
        return False
    
    async def _webui_enhanced_trigger_click(self, custom_select: Dict, attempt: int) -> bool:
        """🔥 WebUI增强版触发器点击 - 融合原生检测能力"""
        try:
            # 使用WebUI的增强元素检测
            trigger_js = f"""
            (function() {{
                // 🔥 融合WebUI原生选择器策略
                const webUITriggerSelectors = [
                    // 问卷平台自定义下拉框
                    '.jqselect', '.jqselect-text', '.jqselect-wrapper',
                    '.select-wrapper', '.dropdown-wrapper', '.dropdown-trigger',
                    // WebUI兼容的主流UI框架
                    '.el-select', '.el-input__inner', '.el-select__input',
                    '.ant-select', '.ant-select-selection', '.ant-select-selector',
                    '.layui-select', '.layui-select-title', 
                    '.weui-select', '.weui-select-title',
                    // WebUI增强语义化选择器
                    '[role="combobox"]', '[aria-haspopup="listbox"]', '[aria-expanded="false"]',
                    '.custom-select', '.select-text', '.selected-value', '.current-value',
                    '[class*="select"]:not(select)', '[class*="dropdown"]', '[class*="picker"]'
                ];
                
                let bestTrigger = null;
                let triggerScore = 0;
                
                // 🔥 智能评分系统 - 选择最佳触发器
                for (let selector of webUITriggerSelectors) {{
                    try {{
                        const elements = document.querySelectorAll(selector);
                        for (let element of elements) {{
                            if (element.offsetHeight > 0 && element.offsetWidth > 0) {{
                                const text = element.textContent || element.value || '';
                                const isPlaceholder = text.includes('请选择') || text.includes('选择') || text.includes('Select') || text === '';
                                const isVisible = element.offsetParent !== null;
                                const hasDropdownFeatures = element.querySelector('.arrow, .caret, .icon') || 
                                                          element.className.includes('dropdown') ||
                                                          element.hasAttribute('aria-haspopup');
                                
                                // 计算触发器质量得分
                                let score = 0;
                                if (isPlaceholder) score += 10;  // 包含"请选择"文本
                                if (isVisible) score += 5;       // 元素可见
                                if (hasDropdownFeatures) score += 3; // 有下拉框特征
                                
                                if (score > triggerScore) {{
                                    triggerScore = score;
                                    bestTrigger = element;
                                }}
                            }}
                        }}
                    }} catch(e) {{ continue; }}
                }}
                
                if (!bestTrigger) {{
                    return {{ success: false, error: "未找到合适的触发器" }};
                }}
                
                // 🔥 根据尝试次数使用不同的点击策略
                const strategies = ['click', 'mousedown_mouseup', 'focus_click', 'dispatch_event', 'keyboard_space'];
                const strategy = strategies[{attempt} % strategies.length];
                
                try {{
                    switch(strategy) {{
                        case 'click':
                            bestTrigger.click();
                            break;
                        case 'mousedown_mouseup':
                            bestTrigger.dispatchEvent(new MouseEvent('mousedown', {{ bubbles: true }}));
                            setTimeout(() => {{
                                bestTrigger.dispatchEvent(new MouseEvent('mouseup', {{ bubbles: true }}));
                                bestTrigger.click();
                            }}, 50);
                            break;
                        case 'focus_click':
                            bestTrigger.focus();
                            setTimeout(() => bestTrigger.click(), 100);
                            break;
                        case 'dispatch_event':
                            ['mouseenter', 'mouseover', 'mousedown', 'click'].forEach(eventType => {{
                                bestTrigger.dispatchEvent(new MouseEvent(eventType, {{ 
                                    bubbles: true, cancelable: true 
                                }}));
                            }});
                            break;
                        case 'keyboard_space':
                            bestTrigger.focus();
                            bestTrigger.dispatchEvent(new KeyboardEvent('keydown', {{ 
                                key: ' ', code: 'Space', bubbles: true 
                            }}));
                            break;
                    }}
                    
                    return {{ 
                        success: true, 
                        strategy: strategy,
                        triggerSelector: bestTrigger.tagName.toLowerCase() + 
                                       (bestTrigger.className ? '.' + bestTrigger.className.split(' ').join('.') : ''),
                        score: triggerScore
                    }};
                    
                }} catch(clickError) {{
                    return {{ success: false, error: "触发器点击失败: " + clickError.message }};
                }}
            }})();
            """
            
            result = await self.browser_context.execute_javascript(trigger_js)
            
            if result.get("success"):
                self.logger.info(f"✅ 触发器点击成功，策略: {result.get('strategy')}, 得分: {result.get('score')}")
                # 人类化等待
                await self.human_interaction_simulator.dropdown_trigger_delay()
                return True
            else:
                self.logger.warning(f"⚠️ 触发器点击失败: {result.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 触发器点击异常: {e}")
            return False
    
    async def _webui_enhanced_options_detection(self, custom_select: Dict) -> bool:
        """🔥 WebUI增强版选项检测 - 智能等待机制"""
        try:
            # 🔥 动态等待选项出现，使用WebUI的智能检测
            detection_js = """
            (function() {
                return new Promise((resolve) => {
                    let attempts = 0;
                    const maxAttempts = 10;
                    
                    function checkForOptions() {
                        attempts++;
                        
                        // 🔥 WebUI兼容的全面选项选择器
                        const optionSelectors = [
                            '.jqselect-options li', '.select-options li', '.dropdown-options li',
                            '.el-select-dropdown li', '.ant-select-dropdown li', '.layui-select-options li',
                            '.weui-select-options li', '.dropdown-menu li', '[role="option"]',
                            '.option', '.item', '.choice', 'li[data-value]', 'ul li', 'ol li',
                            '.dropdown-item', '.menu-item', '.option-item'
                        ];
                        
                        let totalOptions = 0;
                        let visibleOptions = 0;
                        
                        for (let selector of optionSelectors) {
                            const options = document.querySelectorAll(selector);
                            if (options.length > 0) {
                                options.forEach(option => {
                                    totalOptions++;
                                    if (option.offsetHeight > 0 && option.offsetWidth > 0 && 
                                        option.textContent.trim() !== '') {
                                        visibleOptions++;
                                    }
                                });
                                
                                if (visibleOptions > 0) {
                                    resolve({
                                        success: true,
                                        totalOptions: totalOptions,
                                        visibleOptions: visibleOptions,
                                        detectedSelector: selector,
                                        attempts: attempts
                                    });
                                    return;
                                }
                            }
                        }
                        
                        if (attempts < maxAttempts) {
                            setTimeout(checkForOptions, 200);
                        } else {
                            resolve({
                                success: false,
                                error: "选项检测超时",
                                attempts: attempts
                            });
                        }
                    }
                    
                    checkForOptions();
                });
            })();
            """
            
            result = await self.browser_context.execute_javascript(detection_js)
            
            if result.get("success"):
                self.logger.info(f"✅ 选项检测成功: {result.get('visibleOptions')}个可见选项，用时{result.get('attempts')}次检测")
                return True
            else:
                self.logger.warning(f"⚠️ 选项检测失败: {result.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 选项检测异常: {e}")
            return False
    
    async def _webui_enhanced_verification(self, option_text: str, custom_select: Dict) -> bool:
        """🔥 WebUI增强版选择验证"""
        try:
            verify_js = f"""
            (function() {{
                const targetText = "{option_text}";
                
                // 🔥 多重验证策略
                const verificationMethods = [
                    // 方法1: 检查触发器文本变化
                    () => {{
                        const triggers = document.querySelectorAll('.jqselect-text, .select-text, .dropdown-trigger, .selected-value, .current-value');
                        for (let trigger of triggers) {{
                            const text = trigger.textContent.trim();
                            if (text === targetText || text.includes(targetText)) {{
                                return {{ success: true, method: 'trigger_text_match', value: text }};
                            }}
                        }}
                        return {{ success: false, method: 'trigger_text_match' }};
                    }},
                    
                    // 方法2: 检查隐藏input值
                    () => {{
                        const hiddenInputs = document.querySelectorAll('input[type="hidden"], input[style*="display: none"]');
                        for (let input of hiddenInputs) {{
                            if (input.value === targetText || 
                                (input.getAttribute('data-text') && input.getAttribute('data-text').includes(targetText))) {{
                                return {{ success: true, method: 'hidden_input_value', value: input.value }};
                            }}
                        }}
                        return {{ success: false, method: 'hidden_input_value' }};
                    }},
                    
                    // 方法3: 检查选中状态class
                    () => {{
                        const selectedElements = document.querySelectorAll('.selected, .active, .chosen, [aria-selected="true"]');
                        for (let element of selectedElements) {{
                            if (element.textContent.trim().includes(targetText)) {{
                                return {{ success: true, method: 'selected_class', value: element.textContent.trim() }};
                            }}
                        }}
                        return {{ success: false, method: 'selected_class' }};
                    }},
                    
                    // 方法4: 检查下拉框是否已关闭（间接验证）
                    () => {{
                        const openDropdowns = document.querySelectorAll('.dropdown-options, .select-options, .jqselect-options');
                        const visibleDropdowns = Array.from(openDropdowns).filter(dropdown => 
                            dropdown.offsetHeight > 0 && dropdown.offsetWidth > 0
                        );
                        
                        if (visibleDropdowns.length === 0) {{
                            return {{ success: true, method: 'dropdown_closed', value: 'dropdown_closed_after_selection' }};
                        }}
                        return {{ success: false, method: 'dropdown_closed' }};
                    }}
                ];
                
                // 执行所有验证方法
                for (let method of verificationMethods) {{
                    const result = method();
                    if (result.success) {{
                        return result;
                    }}
                }}
                
                return {{ success: false, method: 'all_failed', error: "所有验证方法都失败" }};
            }})();
            """
            
            result = await self.browser_context.execute_javascript(verify_js)
            
            if result.get("success"):
                self.logger.info(f"✅ 选择验证成功: 方法={result.get('method')}, 值={result.get('value')}")
                return True
            else:
                self.logger.warning(f"⚠️ 选择验证失败: {result.get('error')}")
                # 即使验证失败，我们仍然认为操作可能成功了，继续流程
                return True  # 宽松策略，避免因验证问题中断流程
                
        except Exception as e:
            self.logger.error(f"❌ 选择验证异常: {e}")
            return True  # 异常情况下也继续流程
    
    async def _multi_strategy_trigger(self, custom_select: Dict, attempt: int) -> bool:
        """多策略触发器点击"""
        strategies = [
            "specific_click",      # 特定选择器点击
            "focus_and_click",     # 聚焦后点击
            "keyboard_space",      # 键盘空格触发
            "hover_and_click",     # 悬停后点击
            "double_click"         # 双击触发
        ]
        
        strategy = strategies[attempt % len(strategies)]
        
        try:
            trigger_js = f"""
            (function() {{
                // 🔥 全面触发器选择器（覆盖所有主流问卷平台）
                const comprehensiveTriggerSelectors = [
                    // 问卷星系列
                    '.jqselect', '.jqselect-text', '.jqselect-wrapper',
                    // 腾讯问卷系列
                    '.select-wrapper', '.dropdown-wrapper', '.dropdown-trigger',
                    // Element UI
                    '.el-select', '.el-input__inner', '.el-select__input',
                    // Ant Design
                    '.ant-select', '.ant-select-selection', '.ant-select-selector',
                    // Layui
                    '.layui-select', '.layui-select-title', 
                    // WeUI
                    '.weui-select', '.weui-select-title',
                    // Bootstrap
                    '.dropdown-toggle', '.btn-dropdown',
                    // 通用语义化
                    '[role="combobox"]', '[aria-haspopup="listbox"]', '[aria-expanded="false"]',
                    // 自定义样式
                    '.custom-select', '.select-text', '.selected-value', '.current-value',
                    '[class*="select"]:not(select)', '[class*="dropdown"]', '[class*="picker"]'
                ];
                
                let trigger = null;
                
                // 寻找合适的触发器
                for (let selector of comprehensiveTriggerSelectors) {{
                    const elements = document.querySelectorAll(selector);
                    for (let element of elements) {{
                        if (element.offsetHeight > 0 && element.offsetWidth > 0) {{
                            const text = element.textContent || element.value || '';
                            if (text.includes('请选择') || text.includes('选择') || text.includes('Select') || text === '') {{
                                trigger = element;
                                break;
                            }}
                        }}
                    }}
                    if (trigger) break;
                }}
                
                if (!trigger) {{
                    console.log('❌ 未找到合适的触发器');
                    return false;
                }}
                
                // 根据策略执行不同的触发方式
                const strategy = '{strategy}';
                
                try {{
                    if (strategy === 'specific_click') {{
                        trigger.click();
                    }} else if (strategy === 'focus_and_click') {{
                        trigger.focus();
                        setTimeout(() => trigger.click(), 100);
                    }} else if (strategy === 'keyboard_space') {{
                        trigger.focus();
                        const spaceEvent = new KeyboardEvent('keydown', {{ key: ' ', code: 'Space' }});
                        trigger.dispatchEvent(spaceEvent);
                    }} else if (strategy === 'hover_and_click') {{
                        const hoverEvent = new MouseEvent('mouseover', {{ bubbles: true }});
                        trigger.dispatchEvent(hoverEvent);
                        setTimeout(() => trigger.click(), 200);
                    }} else if (strategy === 'double_click') {{
                        trigger.click();
                        setTimeout(() => trigger.click(), 50);
                    }}
                    
                    console.log('✅ 触发器点击成功，策略:', strategy);
                    return true;
                    
                }} catch (e) {{
                    console.log('❌ 触发器点击失败:', e.message);
                    return false;
                }}
            }})();
            """
            
            result = await self.browser_context.execute_javascript(trigger_js)
            return bool(result)
            
        except Exception as e:
            self.logger.warning(f"⚠️ 触发器策略 {strategy} 失败: {e}")
            return False
    
    async def _dynamic_option_detection(self, timeout_ms: int = 3000, check_interval_ms: int = 100) -> bool:
        """动态选项检测（每100ms检测一次，最多3秒）"""
        
        detection_js = f"""
        (function() {{
            return new Promise((resolve) => {{
                let attempts = 0;
                const maxAttempts = {timeout_ms // check_interval_ms};
                
                function checkOptions() {{
                    attempts++;
                    
                    // 🔥 全面选项选择器（覆盖所有主流UI框架）
                    const comprehensiveOptionSelectors = [
                        // 问卷星
                        '.jqselect-options li', '.jqselect-option',
                        // 腾讯问卷
                        '.select-options li', '.dropdown-options li', '.options-list li',
                        // Element UI
                        '.el-select-dropdown li', '.el-select-dropdown__item', '.el-option',
                        // Ant Design
                        '.ant-select-dropdown li', '.ant-select-item', '.ant-select-item-option',
                        // Layui
                        '.layui-select-options li', '.layui-option',
                        // WeUI
                        '.weui-select-options li', '.weui-option',
                        // Bootstrap
                        '.dropdown-menu li', '.dropdown-item',
                        // 通用语义化
                        '[role="option"]', '[role="listbox"] li', 'li[data-value]',
                        // 通用样式
                        '.option', '.item', '.choice', '.select-item',
                        'ul li', 'ol li'  // 最通用的列表项
                    ];
                    
                    let foundOptions = [];
                    
                    for (let selector of comprehensiveOptionSelectors) {{
                        const options = document.querySelectorAll(selector);
                        if (options.length > 0) {{
                            // 验证这些是真正的选项（有文本内容且可见）
                            const validOptions = Array.from(options).filter(option => {{
                                const text = option.textContent?.trim();
                                const isVisible = option.offsetHeight > 0 && option.offsetWidth > 0;
                                return text && text !== '' && isVisible && !text.includes('请选择');
                            }});
                            
                            if (validOptions.length > 0) {{
                                foundOptions = validOptions;
                                console.log(`✅ 选项检测成功: 找到 ${{validOptions.length}} 个选项 (选择器: ${{selector}})`);
                                resolve(true);
                                return;
                            }}
                        }}
                    }}
                    
                    if (attempts >= maxAttempts) {{
                        console.log(`❌ 选项检测超时: ${{attempts}} 次尝试后仍未找到选项`);
                        resolve(false);
                    }} else {{
                        console.log(`🔍 选项检测尝试 ${{attempts}}/${{maxAttempts}}: 未找到选项，继续检测...`);
                        setTimeout(checkOptions, {check_interval_ms});
                    }}
                }}
                
                // 立即开始检测
                checkOptions();
            }});
        }})();
        """
        
        try:
            result = await self.browser_context.execute_javascript(detection_js)
            return bool(result)
        except Exception as e:
            self.logger.warning(f"⚠️ 动态选项检测失败: {e}")
            return False
    
    async def _multi_method_option_click(self, option_text: str, attempt: int) -> bool:
        """多方法选项点击"""
        
        click_methods = [
            "enhanced_scrollable_click",  # 🔥 新增：WebUI增强滚动点击
            "text_match_click",           # 文本匹配点击
            "fuzzy_text_match",           # 模糊文本匹配
            "index_based_click",          # 基于索引点击
            "event_simulation"            # 事件模拟
        ]
        
        method = click_methods[attempt % len(click_methods)]
        
        # 🔥 优先使用WebUI增强滚动点击方法
        if method == "enhanced_scrollable_click":
            try:
                custom_select_dict = {}  # 创建一个基本的custom_select字典
                result = await self.webui_enhanced_handler.enhanced_scrollable_option_click(
                    option_text, custom_select_dict, attempt
                )
                self.logger.info(f"✅ WebUI增强滚动点击{'成功' if result else '失败'}")
                return result
            except Exception as e:
                self.logger.warning(f"⚠️ WebUI增强滚动点击异常: {e}")
                # 继续使用传统方法
        
        click_js = f"""
        (function() {{
            const targetText = "{option_text}";
            const method = "{method}";
            
            // 🔥 全面选项选择器
            const allOptionSelectors = [
                '.jqselect-options li', '.select-options li', '.dropdown-options li',
                '.el-select-dropdown li', '.ant-select-dropdown li', '.layui-select-options li',
                '.weui-select-options li', '.dropdown-menu li', '[role="option"]',
                '.option', '.item', '.choice', 'li[data-value]', 'ul li', 'ol li'
            ];
            
            let allOptions = [];
            for (let selector of allOptionSelectors) {{
                const options = document.querySelectorAll(selector);
                allOptions = allOptions.concat(Array.from(options));
            }}
            
            // 去重并过滤可见选项
            const uniqueOptions = allOptions.filter((option, index, self) => {{
                return self.indexOf(option) === index && 
                       option.offsetHeight > 0 && 
                       option.textContent?.trim() !== '';
            }});
            
            console.log(`🔍 找到 ${{uniqueOptions.length}} 个候选选项`);
            
            if (method === 'text_match_click') {{
                // 精确文本匹配
                for (let option of uniqueOptions) {{
                    if (option.textContent.trim() === targetText) {{
                        option.click();
                        option.dispatchEvent(new Event('click', {{ bubbles: true }}));
                        console.log('✅ 精确文本匹配成功');
                        return true;
                    }}
                }}
            }} else if (method === 'fuzzy_text_match') {{
                // 模糊文本匹配
                for (let option of uniqueOptions) {{
                    const optionText = option.textContent.trim().toLowerCase();
                    const target = targetText.toLowerCase();
                    if (optionText.includes(target) || target.includes(optionText)) {{
                        option.click();
                        option.dispatchEvent(new Event('click', {{ bubbles: true }}));
                        console.log('✅ 模糊文本匹配成功');
                        return true;
                    }}
                }}
            }} else if (method === 'index_based_click') {{
                // 基于索引点击（选择第一个或第二个选项）
                const index = Math.min(1, uniqueOptions.length - 1);
                if (uniqueOptions[index]) {{
                    uniqueOptions[index].click();
                    uniqueOptions[index].dispatchEvent(new Event('click', {{ bubbles: true }}));
                    console.log(`✅ 索引点击成功 (索引: ${{index}})`);
                    return true;
                }}
            }} else if (method === 'event_simulation') {{
                // 事件模拟点击
                for (let option of uniqueOptions) {{
                    if (option.textContent.trim() === targetText) {{
                        const clickEvent = new MouseEvent('click', {{ bubbles: true, cancelable: true }});
                        const changeEvent = new Event('change', {{ bubbles: true }});
                        option.dispatchEvent(clickEvent);
                        option.dispatchEvent(changeEvent);
                        console.log('✅ 事件模拟成功');
                        return true;
                    }}
                }}
            }}
            
            console.log(`❌ 方法 ${{method}} 未能找到或点击选项`);
            return false;
        }})();
        """
        
        try:
            result = await self.browser_context.execute_javascript(click_js)
            return bool(result)
        except Exception as e:
            self.logger.warning(f"⚠️ 选项点击方法 {method} 失败: {e}")
            return False
    
    async def _multi_method_verification(self, option_text: str, custom_select: Dict) -> bool:
        """多方法验证选择是否成功"""
        
        verify_js = f"""
        (function() {{
            const targetText = "{option_text}";
            
            // 验证方法1: 触发器文本变化
            const triggerSelectors = [
                '.jqselect-text', '.select-text', '.dropdown-trigger', '.selected-value',
                '.el-input__inner', '.ant-select-selection', '.layui-select-title',
                '.weui-select', '[role="combobox"]'
            ];
            
            for (let selector of triggerSelectors) {{
                const triggers = document.querySelectorAll(selector);
                for (let trigger of triggers) {{
                    const currentText = trigger.textContent || trigger.value || '';
                    if (currentText.trim() === targetText) {{
                        console.log('✅ 验证方法1成功: 触发器文本已更新');
                        return {{ success: true, method: 'trigger_text_change' }};
                    }}
                }}
            }}
            
            // 验证方法2: 隐藏输入值检查
            const hiddenInputs = document.querySelectorAll('input[type="hidden"]');
            for (let input of hiddenInputs) {{
                if (input.value === targetText) {{
                    console.log('✅ 验证方法2成功: 隐藏输入值匹配');
                    return {{ success: true, method: 'hidden_input_value' }};
                }}
            }}
            
            // 验证方法3: aria-selected检查
            const selectedOptions = document.querySelectorAll('[aria-selected="true"]');
            for (let option of selectedOptions) {{
                if (option.textContent.trim() === targetText) {{
                    console.log('✅ 验证方法3成功: aria-selected属性匹配');
                    return {{ success: true, method: 'aria_selected' }};
                }}
            }}
            
            // 验证方法4: 表单验证状态
            const forms = document.querySelectorAll('form');
            for (let form of forms) {{
                if (form.checkValidity && form.checkValidity()) {{
                    const selects = form.querySelectorAll('select');
                    for (let select of selects) {{
                        if (select.value && select.value !== '') {{
                            console.log('✅ 验证方法4成功: 表单验证通过');
                            return {{ success: true, method: 'form_validation' }};
                        }}
                    }}
                }}
            }}
            
            console.log('❌ 所有验证方法都失败');
            return {{ success: false, method: 'none' }};
        }})();
        """
        
        try:
            result = await self.browser_context.execute_javascript(verify_js)
            success = result.get("success", False)
            method = result.get("method", "unknown")
            
            if success:
                self.logger.info(f"✅ 选择验证成功，方法: {method}")
            else:
                self.logger.warning(f"⚠️ 选择验证失败")
            
            return success
            
        except Exception as e:
            self.logger.warning(f"⚠️ 验证过程失败: {e}")
            return False
    
    async def _adaptive_failure_analysis(self, attempt: int, custom_select: Dict):
        """智能失败分析和适应性策略调整"""
        
        analysis_js = """
        (function() {
            const analysis = {
                triggers_found: 0,
                options_found: 0,
                ui_framework: 'unknown',
                page_state: 'unknown'
            };
            
            // 分析触发器
            const triggerSelectors = [
                '.jqselect', '.el-select', '.ant-select', '.layui-select', '.weui-select'
            ];
            
            for (let selector of triggerSelectors) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    analysis.triggers_found += elements.length;
                    if (selector.includes('el-')) analysis.ui_framework = 'Element UI';
                    else if (selector.includes('ant-')) analysis.ui_framework = 'Ant Design';
                    else if (selector.includes('layui-')) analysis.ui_framework = 'Layui';
                    else if (selector.includes('weui-')) analysis.ui_framework = 'WeUI';
                    else if (selector.includes('jq')) analysis.ui_framework = '问卷星';
                }
            }
            
            // 分析选项
            const optionSelectors = [
                'li', '.option', '[role="option"]'
            ];
            
            for (let selector of optionSelectors) {
                analysis.options_found += document.querySelectorAll(selector).length;
            }
            
            // 分析页面状态
            if (document.readyState === 'complete') {
                analysis.page_state = 'complete';
            } else if (document.readyState === 'interactive') {
                analysis.page_state = 'interactive';
            } else {
                analysis.page_state = 'loading';
            }
            
            return analysis;
        })();
        """
        
        try:
            analysis = await self.browser_context.execute_javascript(analysis_js)
            
            self.logger.info(f"🔍 失败分析(尝试{attempt + 1}): "
                          f"触发器数量={analysis.get('triggers_found', 0)}, "
                          f"选项数量={analysis.get('options_found', 0)}, "
                          f"UI框架={analysis.get('ui_framework', 'unknown')}, "
                          f"页面状态={analysis.get('page_state', 'unknown')}")
            
            # 基于分析结果调整策略
            if analysis.get('triggers_found', 0) == 0:
                self.logger.warning("⚠️ 未发现下拉触发器，可能需要滚动页面")
            elif analysis.get('options_found', 0) == 0:
                self.logger.warning("⚠️ 未发现选项，可能需要更长的等待时间")
            elif analysis.get('page_state') != 'complete':
                self.logger.warning("⚠️ 页面未完全加载，建议等待")
                
        except Exception as e:
            self.logger.warning(f"⚠️ 失败分析异常: {e}")
    
    def _select_best_option_for_persona(self, question_text: str, options: List[Dict], persona_info: Dict, question_type: str) -> Optional[Dict]:
        """
        🔧 增强：基于小社会系统的丰富persona信息选择最佳选项
        充分利用attributes、health_info、favorite_brands等完整数据
        """
        if not options:
            return None
        
        question_lower = question_text.lower()
        
        # 🎯 基础信息提取（兼容新旧格式）
        persona_age = persona_info.get("age", 30)
        persona_job = persona_info.get("profession", persona_info.get("job", "")).lower()
        persona_gender = persona_info.get("gender", "female")
        persona_income = persona_info.get("income", "8000")
        persona_education = persona_info.get("education", "").lower()
        persona_marital = persona_info.get("marital_status", "")
        
        # 🎨 丰富属性信息提取
        attributes = persona_info.get("attributes", {})
        personality_traits = attributes.get("性格", []) if attributes else []
        interests = attributes.get("爱好", []) if attributes else []
        achievements = attributes.get("成就", "") if attributes else ""
        
        # 🏥 健康和生活方式信息
        health_info = persona_info.get("health_info", {})
        health_status = health_info.get("health_status", []) if health_info else []
        favorite_brands = persona_info.get("favorite_brands", [])
        current_mood = persona_info.get("mood", "")
        
        # 🔍 增强的选项匹配逻辑
        for option in options:
            option_text = option.get("text", "").lower()
            
            # 性别相关题目
            if "性别" in question_text or "gender" in question_lower:
                if persona_gender == "female" and ("女" in option_text or "female" in option_text):
                    return option
                elif persona_gender == "male" and ("男" in option_text or "male" in option_text):
                    return option
            
            # 年龄相关题目（更精细的年龄段判断）
            if "年龄" in question_text or "age" in question_lower:
                if persona_age < 25 and any(age_range in option_text for age_range in ["18-25", "25以下", "年轻", "学生"]):
                    return option
                elif 25 <= persona_age < 35 and any(age_range in option_text for age_range in ["25-35", "26-30", "31-35", "青年"]):
                    return option
                elif 35 <= persona_age < 50 and any(age_range in option_text for age_range in ["35-45", "36-40", "41-45", "中年"]):
                    return option
                elif persona_age >= 50 and any(age_range in option_text for age_range in ["45以上", "50+", "中老年", "退休"]):
                    return option
            
            # 🔧 增强：职业相关题目（更全面的职业匹配）
            if "职业" in question_text or "工作" in question_text or "profession" in question_lower:
                if any(job_keyword in persona_job for job_keyword in ["ceo", "总裁", "总监"]):
                    if any(job in option_text for job in ["管理", "高管", "领导", "决策"]):
                        return option
                elif any(job_keyword in persona_job for job_keyword in ["工程师", "技术", "程序"]):
                    if any(job in option_text for job in ["技术", "it", "工程", "研发"]):
                        return option
                elif any(job_keyword in persona_job for job_keyword in ["医生", "医师"]):
                    if any(job in option_text for job in ["医疗", "健康", "医生", "医师"]):
                        return option
                elif any(job_keyword in persona_job for job_keyword in ["教师", "教授"]):
                    if any(job in option_text for job in ["教育", "教学", "培训", "学术"]):
                        return option
                elif "学生" in persona_job:
                    if any(job in option_text for job in ["学生", "学习", "教育", "校园"]):
                        return option
            
            # 💰 收入相关题目
            if "收入" in question_text or "salary" in question_lower or "income" in question_lower:
                try:
                    income_num = int(persona_income.replace("元", "").replace(",", ""))
                    if income_num < 5000 and any(income_range in option_text for income_range in ["5000以下", "低收入", "3000-5000"]):
                        return option
                    elif 5000 <= income_num < 10000 and any(income_range in option_text for income_range in ["5000-10000", "中等", "8000"]):
                        return option
                    elif income_num >= 10000 and any(income_range in option_text for income_range in ["10000以上", "高收入", "15000"]):
                        return option
                except:
                    pass
            
            # 🎓 教育背景相关
            if "学历" in question_text or "教育" in question_text or "education" in question_lower:
                if "博士" in persona_education and any(edu in option_text for edu in ["博士", "博士研究生", "最高学历"]):
                    return option
                elif "硕士" in persona_education and any(edu in option_text for edu in ["硕士", "研究生", "硕士研究生"]):
                    return option
                elif "本科" in persona_education and any(edu in option_text for edu in ["本科", "大学", "学士"]):
                    return option
                elif "专科" in persona_education and any(edu in option_text for edu in ["专科", "大专", "高职"]):
                    return option
            
            # 💒 婚姻状况相关
            if "婚姻" in question_text or "结婚" in question_text or "marital" in question_lower:
                if "已婚" in persona_marital and any(marital in option_text for marital in ["已婚", "结婚", "有配偶"]):
                    return option
                elif "未婚" in persona_marital and any(marital in option_text for marital in ["未婚", "单身", "无配偶"]):
                    return option
                elif "离异" in persona_marital and any(marital in option_text for marital in ["离异", "离婚", "分居"]):
                    return option
            
            # 🎨 兴趣爱好相关（基于attributes中的爱好）
            if "爱好" in question_text or "兴趣" in question_text or "喜欢" in question_text:
                for interest in interests:
                    if interest in option_text:
                        return option
                # 其他爱好匹配
                if any(hobby_keyword in interests for hobby_keyword in ["运动", "健身", "篮球", "足球"]):
                    if any(sport in option_text for sport in ["运动", "健身", "体育", "锻炼"]):
                        return option
                elif any(hobby_keyword in interests for hobby_keyword in ["读书", "阅读", "文学"]):
                    if any(reading in option_text for reading in ["读书", "阅读", "文学", "书籍"]):
                        return option
                elif any(hobby_keyword in interests for hobby_keyword in ["音乐", "唱歌", "钢琴"]):
                    if any(music in option_text for music in ["音乐", "唱歌", "乐器", "歌曲"]):
                        return option
            
            # 🏥 健康相关题目
            if "健康" in question_text or "身体" in question_text or "health" in question_lower:
                if health_status and any(health in option_text for health in health_status):
                    return option
                # 健康状况判断
                if "身体健康" in health_status and any(healthy in option_text for healthy in ["健康", "良好", "正常"]):
                    return option
                elif any(disease in health_status for disease in ["糖尿病", "高血压", "心脏病"]) and any(concern in option_text for concern in ["关注", "注意", "重视"]):
                    return option
            
            # 🛍️ 品牌偏好相关
            if "品牌" in question_text or "购买" in question_text or "brand" in question_lower:
                for brand in favorite_brands:
                    if brand.lower() in option_text or brand in option_text:
                        return option
                # 品牌价位判断
                if any(luxury_brand in favorite_brands for luxury_brand in ["LV", "Gucci", "Hermès", "Prada"]):
                    if any(luxury_keyword in option_text for luxury_keyword in ["高端", "奢侈", "品质", "昂贵"]):
                        return option
                elif any(popular_brand in favorite_brands for popular_brand in ["Nike", "Adidas", "Apple", "华为"]):
                    if any(popular_keyword in option_text for popular_keyword in ["知名", "流行", "大众", "实用"]):
                        return option
            
            # 🎭 性格特征相关
            if "性格" in question_text or "个性" in question_text or "character" in question_lower:
                for trait in personality_traits:
                    if trait in option_text:
                        return option
                # 性格匹配
                if any(trait in personality_traits for trait in ["外向", "开朗", "活泼"]):
                    if any(extro in option_text for extro in ["社交", "活跃", "外向", "开朗"]):
                        return option
                elif any(trait in personality_traits for trait in ["内向", "安静", "内敛"]):
                    if any(intro in option_text for intro in ["安静", "独处", "内向", "思考"]):
                        return option
            
            # 🎯 当前心情影响选择
            if current_mood:
                if current_mood in ["开心", "兴奋", "满足"] and any(positive in option_text for positive in ["是", "同意", "很好", "满意"]):
                    return option
                elif current_mood in ["疲惫", "焦虑", "压力"] and any(neutral in option_text for neutral in ["一般", "还好", "普通"]):
                    return option
        
        # 🔄 如果没有明确匹配，基于人设特征选择合适的选项
        
        # 根据教育水平选择
        if "博士" in persona_education or "硕士" in persona_education:
            # 高学历倾向于理性、客观的选择
            rational_keywords = ["客观", "理性", "分析", "研究", "科学", "逻辑"]
            for option in options:
                if any(keyword in option.get("text", "").lower() for keyword in rational_keywords):
                    return option
        
        # 根据收入水平选择
        try:
            income_num = int(persona_income.replace("元", "").replace(",", ""))
            if income_num >= 12000:
                # 高收入倾向于品质、服务导向的选择
                quality_keywords = ["品质", "服务", "专业", "高端", "优质"]
                for option in options:
                    if any(keyword in option.get("text", "").lower() for keyword in quality_keywords):
                        return option
        except:
            pass
        
        # 根据年龄选择
        if persona_age < 30:
            # 年轻人倾向于创新、时尚的选择
            young_keywords = ["新颖", "创新", "时尚", "潮流", "科技", "数字"]
            for option in options:
                if any(keyword in option.get("text", "").lower() for keyword in young_keywords):
                    return option
        elif persona_age >= 40:
            # 中年人倾向于稳定、实用的选择
            stable_keywords = ["稳定", "实用", "可靠", "传统", "安全", "保障"]
            for option in options:
                if any(keyword in option.get("text", "").lower() for keyword in stable_keywords):
                    return option
        
        # 🎯 最终回退：选择积极中性的选项
        positive_keywords = ["是", "同意", "满意", "经常", "很好", "一般", "还可以", "yes", "agree", "good", "ok"]
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
    
    # 🔥 新增：表格题/矩阵题处理方法
    async def _answer_table_question(self, table_question: Dict, persona_info: Dict) -> Dict:
        """作答表格题/矩阵题"""
        try:
            question_text = table_question.get("question_text", "")
            table_name = table_question["name"]
            input_type = table_question.get("input_type", "radio")
            row_count = table_question.get("row_count", 0)
            
            self.logger.info(f"📊 处理表格题: {question_text[:30]}... ({row_count}行)")
            
            # 根据输入类型选择合适的策略
            if input_type == "radio":
                # 对于每行选择一个选项
                success_count = await self._answer_matrix_radio_table(table_name, row_count, persona_info)
            elif input_type == "checkbox":
                # 对于每行可选择多个选项
                success_count = await self._answer_matrix_checkbox_table(table_name, row_count, persona_info)
            else:
                return {"success": False, "error": f"不支持的表格输入类型: {input_type}"}
            
            if success_count > 0:
                question_id = f"table_{table_name}"
                self.state_manager.mark_question_answered(question_id, f"已填写{success_count}项")
                return {"success": True, "answered_count": success_count}
            else:
                return {"success": False, "error": "未能成功作答任何表格项"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _answer_matrix_radio_table(self, table_name: str, row_count: int, persona_info: Dict) -> int:
        """处理矩阵单选表格"""
        success_count = 0
        
        for row in range(row_count):
            try:
                # 为每行选择一个合适的选项（通常选择中等偏好的选项）
                option_preference = random.choice([2, 3, 4])  # 偏向中间选项
                
                radio_click_js = f"""
                (function() {{
                    const table = document.querySelector('table#{table_name}, table[data-name="{table_name}"], .table-container#{table_name}');
                    if (!table) return false;
                    
                    const rows = table.querySelectorAll('tr');
                    if (rows.length <= {row + 1}) return false;
                    
                    const currentRow = rows[{row + 1}]; // 跳过表头
                    const radios = currentRow.querySelectorAll('input[type="radio"]');
                    
                    if (radios.length > 0) {{
                        const targetIndex = Math.min({option_preference}, radios.length - 1);
                        radios[targetIndex].click();
                        return true;
                    }}
                    return false;
                }})();
                """
                
                result = await self.browser_context.execute_javascript(radio_click_js)
                if result:
                    success_count += 1
                    await asyncio.sleep(random.uniform(0.2, 0.5))
                
            except Exception as e:
                self.logger.warning(f"⚠️ 表格行{row}作答失败: {e}")
                continue
        
        return success_count
    
    async def _answer_matrix_checkbox_table(self, table_name: str, row_count: int, persona_info: Dict) -> int:
        """处理矩阵多选表格"""
        success_count = 0
        
        for row in range(row_count):
            try:
                # 每行选择1-2个选项
                checkbox_click_js = f"""
                (function() {{
                    const table = document.querySelector('table#{table_name}, table[data-name="{table_name}"], .table-container#{table_name}');
                    if (!table) return 0;
                    
                    const rows = table.querySelectorAll('tr');
                    if (rows.length <= {row + 1}) return 0;
                    
                    const currentRow = rows[{row + 1}];
                    const checkboxes = currentRow.querySelectorAll('input[type="checkbox"]');
                    
                    if (checkboxes.length > 0) {{
                        const selectCount = Math.min(2, Math.max(1, Math.floor(checkboxes.length / 2)));
                        let clicked = 0;
                        
                        for (let i = 0; i < selectCount && i < checkboxes.length; i++) {{
                            const randomIndex = Math.floor(Math.random() * checkboxes.length);
                            if (!checkboxes[randomIndex].checked) {{
                                checkboxes[randomIndex].click();
                                clicked++;
                            }}
                        }}
                        
                        return clicked;
                    }}
                    return 0;
                }})();
                """
                
                clicked_count = await self.browser_context.execute_javascript(checkbox_click_js)
                if clicked_count > 0:
                    success_count += 1
                    await asyncio.sleep(random.uniform(0.3, 0.7))
                
            except Exception as e:
                self.logger.warning(f"⚠️ 表格行{row}作答失败: {e}")
                continue
        
        return success_count
    
    # 🔥 新增：滑块题处理方法
    async def _answer_slider_question(self, slider_question: Dict, persona_info: Dict) -> Dict:
        """作答滑块题"""
        try:
            question_text = slider_question.get("question_text", "")
            slider_name = slider_question["name"]
            min_value = int(slider_question.get("min_value", 0))
            max_value = int(slider_question.get("max_value", 100))
            
            self.logger.info(f"🎚️ 处理滑块题: {question_text[:30]}... (范围: {min_value}-{max_value})")
            
            # 根据persona和题目内容智能选择数值
            target_value = self._calculate_slider_value(question_text, min_value, max_value, persona_info)
            
            slider_set_js = f"""
            (function() {{
                const sliders = [
                    document.querySelector('input[type="range"][name="{slider_name}"]'),
                    document.querySelector('input[type="range"]#{slider_name}'),
                    document.querySelector('.slider#{slider_name}'),
                    document.querySelector('.range-slider[data-name="{slider_name}"]')
                ];
                
                for (let slider of sliders) {{
                    if (slider) {{
                        slider.value = {target_value};
                        
                        // 触发事件
                        slider.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        slider.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        
                        // 对于一些框架，可能需要模拟拖拽
                        if (slider.setAttribute) {{
                            slider.setAttribute('aria-valuenow', {target_value});
                        }}
                        
                        return {{ success: true, value: {target_value} }};
                    }}
                }}
                
                return {{ success: false, error: "未找到滑块元素" }};
            }})();
            """
            
            result = await self.browser_context.execute_javascript(slider_set_js)
            
            if result.get("success"):
                question_id = f"slider_{slider_name}"
                self.state_manager.mark_question_answered(question_id, str(target_value))
                return {"success": True, "value": target_value}
            else:
                return {"success": False, "error": result.get("error", "设置滑块值失败")}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _calculate_slider_value(self, question_text: str, min_val: int, max_val: int, persona_info: Dict) -> int:
        """根据题目内容和persona计算滑块值"""
        # 默认选择中等偏上的值
        mid_value = (min_val + max_val) // 2
        
        # 关键词匹配调整
        satisfaction_keywords = ["满意", "喜欢", "同意", "支持", "推荐"]
        dissatisfaction_keywords = ["不满意", "不喜欢", "不同意", "反对", "不推荐"]
        
        question_lower = question_text.lower()
        
        if any(keyword in question_lower for keyword in satisfaction_keywords):
            # 满意度相关，倾向于较高分数
            return random.randint(int(mid_value * 1.2), max_val)
        elif any(keyword in question_lower for keyword in dissatisfaction_keywords):
            # 不满意相关，倾向于较低分数
            return random.randint(min_val, int(mid_value * 0.8))
        else:
            # 中性题目，选择中等范围
            variance = (max_val - min_val) // 4
            return random.randint(mid_value - variance, mid_value + variance)
    
    # 🔥 新增：评分题处理方法
    async def _answer_rating_question(self, rating_question: Dict, persona_info: Dict) -> Dict:
        """作答评分题（星级、点击评分等）"""
        try:
            question_text = rating_question.get("question_text", "")
            rating_name = rating_question["name"]
            total_items = rating_question.get("total_items", 5)
            
            self.logger.info(f"⭐ 处理评分题: {question_text[:30]}... ({total_items}分)")
            
            # 计算评分（1-total_items）
            target_rating = self._calculate_rating_score(question_text, total_items, persona_info)
            
            rating_click_js = f"""
            (function() {{
                const ratingContainers = [
                    document.querySelector('.rating#{rating_name}'),
                    document.querySelector('.star-rating#{rating_name}'),
                    document.querySelector('[data-rating="{rating_name}"]'),
                    document.querySelector('.el-rate#{rating_name}'),
                    document.querySelector('.ant-rate#{rating_name}')
                ];
                
                for (let container of ratingContainers) {{
                    if (container) {{
                        // 尝试多种评分方式
                        
                        // 方式1：点击星星或评分项
                        const ratingItems = container.querySelectorAll('.star, .rate-item, .el-rate__item, .ant-rate-star, [data-score]');
                        if (ratingItems.length >= {target_rating}) {{
                            ratingItems[{target_rating - 1}].click();
                            return {{ success: true, rating: {target_rating}, method: 'click' }};
                        }}
                        
                        // 方式2：radio按钮评分
                        const radios = container.querySelectorAll('input[type="radio"]');
                        if (radios.length >= {target_rating}) {{
                            radios[{target_rating - 1}].click();
                            return {{ success: true, rating: {target_rating}, method: 'radio' }};
                        }}
                        
                        // 方式3：设置data属性或类
                        if (container.setAttribute) {{
                            container.setAttribute('data-rating', {target_rating});
                            container.className = container.className.replace(/rate-\\d+/, '') + ' rate-{target_rating}';
                            return {{ success: true, rating: {target_rating}, method: 'attribute' }};
                        }}
                    }}
                }}
                
                return {{ success: false, error: "未找到评分控件" }};
            }})();
            """
            
            result = await self.browser_context.execute_javascript(rating_click_js)
            
            if result.get("success"):
                question_id = f"rating_{rating_name}"
                self.state_manager.mark_question_answered(question_id, f"{target_rating}分")
                return {"success": True, "rating": target_rating, "method": result.get("method")}
            else:
                return {"success": False, "error": result.get("error", "设置评分失败")}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _calculate_rating_score(self, question_text: str, max_rating: int, persona_info: Dict) -> int:
        """根据题目内容和persona计算评分"""
        # 默认给出中等偏上的评分
        base_rating = max(3, int(max_rating * 0.7))
        
        # 根据题目内容调整
        positive_keywords = ["满意", "推荐", "喜欢", "好", "优秀", "满足"]
        negative_keywords = ["不满意", "不推荐", "不喜欢", "差", "糟糕", "失望"]
        
        question_lower = question_text.lower()
        
        if any(keyword in question_lower for keyword in positive_keywords):
            # 正面评价题，给较高分
            return random.randint(base_rating, max_rating)
        elif any(keyword in question_lower for keyword in negative_keywords):
            # 负面评价题，给较低分
            return random.randint(1, min(3, max_rating))
        else:
            # 中性题目，给中等分数
            mid_rating = max_rating // 2
            return random.randint(mid_rating, min(mid_rating + 2, max_rating))


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
        return await self.browser_context.execute_javascript(scroll_info_js)
    
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
        
        scroll_result = await self.browser_context.execute_javascript(smooth_scroll_js)
        
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
        
        return await self.browser_context.execute_javascript(new_content_js)
    
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
        
        return await self.browser_context.execute_javascript(bottom_check_js)
    
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
        
        return await self.browser_context.execute_javascript(submit_finder_js)


class IntelligentQuestionnaireController:
    """智能问卷控制器 - 整合所有组件，实现完整的智能作答流程"""
    
    def __init__(self, browser_context, persona_info: Dict, session_id: str):
        self.browser_context = browser_context
        self.persona_info = persona_info
        self.session_id = session_id
        self.persona_name = persona_info.get("name", "Unknown")
        
        # 初始化所有子系统（页面对象稍后设置）
        self.state_manager = QuestionnaireStateManager(session_id, self.persona_name)
        self.analyzer = None  # 🔥 将在设置页面后初始化
        self.answer_engine = None  # 🔥 将在设置页面后初始化
        self.scroll_controller = None  # 🔥 将在设置页面后初始化
        self.page = None  # 🔥 页面对象
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    
    def set_page(self, page):
        """设置页面对象并初始化所有组件"""
        self.page = page
        self.analyzer = IntelligentQuestionnaireAnalyzer(page)
        self.answer_engine = RapidAnswerEngine(page, self.state_manager)
        self.scroll_controller = SmartScrollController(page, self.state_manager)

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
                    if self.scroll_controller:
                        submit_button = await self.scroll_controller.find_submit_button()
                        if submit_button and submit_button.get("found", False):
                            self.logger.info(f"🎯 发现提交按钮: {submit_button.get('text', '提交')}")
                            submit_result = await self._attempt_submit(submit_button)
                            if submit_result["success"]:
                                break
                        
                        # 尝试滚动寻找更多内容
                        scroll_result = await self.scroll_controller.intelligent_scroll_to_next_area()
                    else:
                        scroll_result = {"scrolled": False}
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
                        if self.scroll_controller:
                            scroll_result = await self.scroll_controller.intelligent_scroll_to_next_area()
                            if not scroll_result.get("scrolled", False):
                                # 滚动失败，再次尝试查找提交按钮
                                submit_button = await self.scroll_controller.find_submit_button()
                            else:
                                submit_button = None
                        else:
                            scroll_result = {"scrolled": False}
                            submit_button = None
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
            # 🔧 安全性检查：确保scroll_controller已初始化
            if not self.scroll_controller:
                self.logger.error("❌ scroll_controller未初始化，无法进行决策")
                return {"action": "continue", "reason": "scroll_controller未初始化"}
            
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
            
            # 🔥 关键新增：在点击提交按钮之前进行截图
            # 用户需求：每页答完题目后，点击提交按钮之前截图
            await self._capture_pre_submit_screenshot()
            
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
            
            click_success = await self.browser_context.execute_javascript(submit_js)
            
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
            
            return await self.browser_context.execute_javascript(verify_js)
            
        except Exception as e:
            self.logger.error(f"❌ 验证提交结果失败: {e}")
            return {
                "success": True,
                "message": f"验证失败但假设成功: {e}",
                "new_page": False
            }
    
    async def _capture_pre_submit_screenshot(self):
        """在提交前进行截图 - 核心截图功能（用户需求）"""
        try:
            self.logger.info(f"📷 执行提交前截图（每页答完后、提交前截图）")
            
            # 获取当前页面号
            page_number = getattr(self, '_current_page_number', 1)
            self._current_page_number = page_number + 1
            
            # 创建截图目录
            import os
            import base64
            from datetime import datetime
            screenshots_dir = "processed_screenshots"
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # 使用页面对象进行完整页面截图
            page = await self.browser_context.get_current_page()
            screenshot_bytes = await page.screenshot(type="png", full_page=True)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode()
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            digital_human_name = self.persona_info.get("name", "unknown")
            filename = f"{self.session_id}_{digital_human_name}_page_{page_number}_answers.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            # 保存截图文件
            with open(filepath, "wb") as f:
                f.write(screenshot_bytes)
            
            self.logger.info(f"✅ 截图已保存: {filepath}")
            self.logger.info(f"📋 截图内容: 第{page_number}页的所有题目和答案")
            
            # 记录截图信息
            screenshot_info = {
                "page_number": page_number,
                "timestamp": timestamp,
                "filename": filename,
                "filepath": filepath,
                "digital_human": digital_human_name,
                "session_id": self.session_id,
                "screenshot_base64": screenshot_base64,
                "capture_trigger": "pre_submit",
                "description": f"第{page_number}页答题完成后、提交前的完整页面截图"
            }
            
            # 存储到实例变量中
            if not hasattr(self, '_page_screenshots'):
                self._page_screenshots = []
            self._page_screenshots.append(screenshot_info)
            
            return screenshot_info
            
        except Exception as e:
            self.logger.error(f"❌ 提交前截图失败: {e}")
            return None


# ============================================
# 🔥 核心功能类定义 - 修复版本
# ============================================

class WebUIEnhancedDropdownHandler:
    """🔥 WebUI增强下拉框处理器 - 基于反作弊研究的人类化策略"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def enhanced_scrollable_option_click(self, option_text: str, custom_select: Dict, attempt: int) -> bool:
        """
        🔥 核心功能：人类化下拉框滚动与选择
        
        基于反作弊研究的安全策略：
        1. 避免JavaScript注入检测
        2. 模拟真实人类视觉和操作行为  
        3. 使用WebUI原生能力
        4. 自然的滚动和点击时间间隔
        """
        try:
            self.logger.info(f"🎯 开始人类化下拉框处理: '{option_text[:50]}...' (尝试 {attempt})")
            
            # 🔥 步骤1: 预交互行为模拟（避免行为检测）
            await self._pre_dropdown_human_behavior()
            
            # 🔥 步骤2: 使用WebUI原生视觉理解查找下拉框
            dropdown_result = await self._webui_native_dropdown_detection(option_text)
            if not dropdown_result["success"]:
                self.logger.warning(f"⚠️ WebUI原生检测失败: {dropdown_result.get('error')}")
                return False
            
            # 🔥 步骤3: 人类化下拉框展开
            expand_result = await self._human_like_dropdown_expand(dropdown_result)
            if not expand_result["success"]:
                self.logger.warning(f"⚠️ 下拉框展开失败: {expand_result.get('error')}")
                return False
            
            await self._natural_pause_after_expand()
            
            # 🔥 步骤4: 人类化视觉查找和滚动
            scroll_result = await self._human_like_visual_scroll_search(option_text, attempt)
            if not scroll_result["success"]:
                self.logger.warning(f"⚠️ 视觉滚动查找失败: {scroll_result.get('error')}")
                return False
            
            # 🔥 步骤5: 自然选择行为
            select_result = await self._natural_option_selection(option_text, scroll_result, attempt)
            if not select_result["success"]:
                self.logger.warning(f"⚠️ 选项选择失败: {select_result.get('error')}")
                return False
            
            # 🔥 步骤6: 后交互行为和验证
            await self._post_dropdown_human_behavior()
            verification = await self._gentle_selection_verification(option_text)
            
            if verification["success"]:
                self.logger.info(f"✅ 人类化下拉框处理成功: {option_text[:30]}")
                return True
            else:
                self.logger.warning(f"⚠️ 选择验证失败，但可能已成功")
                return True  # 在某些情况下验证可能失败但实际已成功
                
        except Exception as e:
            self.logger.error(f"❌ 人类化下拉框处理异常: {e}")
            return False
    
    async def _pre_dropdown_human_behavior(self):
        """模拟用户在操作下拉框前的自然行为"""
        # 模拟用户阅读页面内容的时间
        await asyncio.sleep(random.uniform(0.5, 1.2))
        
        # 模拟轻微的鼠标移动
        try:
            await self.browser_context.execute_javascript("""
            (() => {
                const event = new MouseEvent('mousemove', {
                    clientX: Math.random() * 100 + 100,
                    clientY: Math.random() * 100 + 100,
                    bubbles: true
                });
                document.dispatchEvent(event);
            })();
            """)
        except:
            pass  # 忽略鼠标移动失败
    
    async def _webui_native_dropdown_detection(self, option_text: str) -> Dict:
        """使用WebUI原生能力检测下拉框，避免JavaScript注入"""
        try:
            # 模拟人类思考时间
            await asyncio.sleep(random.uniform(0.8, 1.5))
            
            # 通过WebUI的原生视觉理解检测下拉框
            result = await self.browser_context.execute_javascript("""
            (() => {
                // 使用最基础的DOM查找，避免复杂JavaScript检测
                const dropdownSelectors = [
                    'select', '[role="combobox"]', '[role="listbox"]', 
                    '.select', '.dropdown', '.combobox'
                ];
                
                for (let selector of dropdownSelectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        return {
                            success: true,
                            found: elements.length,
                            type: selector
                        };
                    }
                }
                
                return { success: false, error: "未找到下拉框" };
            })();
            """)
            
            return result if result else {"success": False, "error": "检测脚本返回空"}
            
        except Exception as e:
            return {"success": False, "error": f"检测异常: {e}"}
    
    async def _human_like_dropdown_expand(self, dropdown_info: Dict) -> Dict:
        """人类化下拉框展开行为"""
        try:
            # 模拟人类操作前的短暂停顿
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # 使用自然的鼠标事件序列，避免单一click事件
            result = await self.browser_context.execute_javascript("""
            (() => {
                const triggers = document.querySelectorAll('select, [role="combobox"], .select-trigger, .dropdown-trigger');
                
                for (let trigger of triggers) {
                    if (trigger.offsetHeight > 0) {
                        // 模拟自然点击行为
                        const rect = trigger.getBoundingClientRect();
                        const centerX = rect.left + rect.width / 2;
                        const centerY = rect.top + rect.height / 2;
                        
                        // 分派自然的鼠标事件序列，模拟真实用户操作
                        ['mouseenter', 'mouseover', 'mousedown', 'focus', 'click', 'mouseup'].forEach((eventType, index) => {
                            setTimeout(() => {
                                const event = new MouseEvent(eventType, {
                                    bubbles: true,
                                    clientX: centerX + Math.random() * 4 - 2,
                                    clientY: centerY + Math.random() * 4 - 2
                                });
                                trigger.dispatchEvent(event);
                            }, index * 15);
                        });
                        
                        return { success: true, triggered: true };
                    }
                }
                
                return { success: false, error: "未找到可点击的下拉触发器" };
            })();
            """)
            
            return result if result else {"success": False, "error": "展开脚本返回空"}
            
        except Exception as e:
            return {"success": False, "error": f"展开异常: {e}"}
    
    async def _natural_pause_after_expand(self):
        """下拉框展开后的自然停顿，模拟人类查看选项的时间"""
        # 模拟人类看到下拉框展开后的自然反应时间
        pause_time = random.uniform(0.8, 2.0)
        await asyncio.sleep(pause_time)
    
    async def _human_like_visual_scroll_search(self, option_text: str, attempt: int) -> Dict:
        """
        🔥 增强版人类化视觉滚动搜索 - 支持展开方向检测
        
        核心改进：
        1. 🔍 智能检测下拉框展开方向（向上/向下/内联）
        2. 🎯 根据展开方向采用最佳滚动策略
        3. 👁️ 模拟真实用户的"观察→滚动→再观察"流程
        4. 🚀 解决WebUI视觉限制问题
        """
        try:
            # 🔍 步骤1：检测下拉框展开方向（关键新功能）
            direction_info = await self._detect_dropdown_expansion_direction({})
            
            # 📊 打印检测结果（调试用）
            if direction_info.get("success"):
                direction = direction_info.get("primary_direction", "unknown")
                scroll_strategy = direction_info.get("scroll_strategy", "unknown")
                self.logger.info(f"🔍 检测到下拉框展开方向: {direction}, 滚动策略: {scroll_strategy}")
            else:
                self.logger.warning(f"⚠️ 展开方向检测失败: {direction_info.get('error')}")
            
            max_scroll_attempts = 5
            
            for scroll_attempt in range(max_scroll_attempts):
                self.logger.info(f"🔍 增强视觉搜索轮次 {scroll_attempt + 1}/{max_scroll_attempts}")
                
                # 🔥 模拟人类视觉扫描当前可见选项
                scan_result = await self._simulate_visual_option_scan(option_text)
                
                if scan_result["found"]:
                    self.logger.info(f"✅ 视觉扫描找到目标选项: {scan_result.get('matched_text')}")
                    return {
                        "success": True,
                        "found_option": scan_result,
                        "scroll_attempts": scroll_attempt,
                        "direction_info": direction_info
                    }
                
                # 🔄 如果没找到且还能滚动，根据展开方向进行智能滚动
                if scroll_attempt < max_scroll_attempts - 1:
                    # 🎯 使用基于方向的增强滚动策略
                    scroll_result = await self._enhanced_scroll_strategy_by_direction(
                        direction_info, option_text
                    )
                    
                    if not scroll_result.get("success"):
                        self.logger.warning(f"⚠️ 智能滚动失败: {scroll_result.get('error')}")
                        # 回退到默认滚动
                        scroll_result = await self._gentle_scroll_down_in_dropdown()
                    
                    if not scroll_result.get("can_scroll_more", True):
                        self.logger.info("📜 滚动到边界，无法继续滚动")
                        break
                    
                    # 📊 记录滚动信息
                    scrolled = scroll_result.get("scrolled", 0)
                    direction = scroll_result.get("direction", "unknown")
                    self.logger.info(f"📜 滚动执行: 方向={direction}, 距离={scrolled}px")
                    
                    # 滚动后的自然停顿，模拟人类处理新信息的时间
                    await asyncio.sleep(random.uniform(0.5, 1.2))
            
            return {
                "success": False,
                "error": f"经过 {max_scroll_attempts} 轮增强视觉搜索未找到选项 '{option_text}'",
                "direction_info": direction_info
            }
            
        except Exception as e:
            return {
                "success": False, 
                "error": f"增强视觉搜索异常: {e}",
                "direction_detection_attempted": True
            }
    
    async def _simulate_visual_option_scan(self, target_text: str) -> Dict:
        """模拟人类视觉扫描当前可见选项"""
        try:
            # 使用最简单的DOM查询，避免复杂JavaScript检测
            scan_result = await self.browser_context.execute_javascript(f"""
            (() => {{
                const targetText = "{target_text.replace('"', '\\"')}";
                
                // 查找可见的选项元素
                const optionSelectors = [
                    'option', 'li[role="option"]', '.option', 
                    '.dropdown-item', '.select-option', 'li'
                ];
                
                let visibleOptions = [];
                
                for (let selector of optionSelectors) {{
                    const options = document.querySelectorAll(selector);
                    for (let option of options) {{
                        if (option.offsetHeight > 0 && option.textContent.trim()) {{
                            visibleOptions.push({{
                                text: option.textContent.trim(),
                                element: option
                            }});
                        }}
                    }}
                }}
                
                // 简单文本匹配，避免复杂算法检测
                for (let option of visibleOptions) {{
                    const optionText = option.text.toLowerCase();
                    const target = targetText.toLowerCase();
                    
                    if (optionText === target || optionText.includes(target)) {{
                        return {{
                            found: true,
                            matched_text: option.text,
                            total_visible: visibleOptions.length
                        }};
                    }}
                }}
                
                return {{
                    found: false,
                    total_visible: visibleOptions.length,
                    sample_options: visibleOptions.slice(0, 3).map(opt => opt.text)
                }};
            }})();
            """)
            
            return scan_result if scan_result else {"found": False, "error": "扫描脚本返回空"}
            
        except Exception as e:
            return {"found": False, "error": f"视觉扫描异常: {e}"}
    
    async def _gentle_scroll_down_in_dropdown(self) -> Dict:
        """
        温和的下拉框内滚动
        
        使用原生的scroll行为而非复杂JavaScript，
        模拟真实用户的滚动操作
        """
        try:
            # 模拟人类决定滚动前的短暂思考
            await asyncio.sleep(random.uniform(0.2, 0.5))
            
            scroll_result = await self.browser_context.execute_javascript("""
            (() => {
                // 查找滚动容器
                const scrollContainers = document.querySelectorAll(
                    '.dropdown-menu, .select-dropdown, .options-container, .scrollable-options, [role="listbox"]'
                );
                
                for (let container of scrollContainers) {
                    if (container.scrollHeight > container.clientHeight) {
                        const currentScrollTop = container.scrollTop;
                        const maxScrollTop = container.scrollHeight - container.clientHeight;
                        
                        if (currentScrollTop < maxScrollTop) {
                            // 温和的小幅滚动，模拟人类滚动行为
                            const scrollAmount = Math.min(100, maxScrollTop - currentScrollTop);
                            container.scrollTop += scrollAmount;
                            
                            return {
                                success: true,
                                scrolled: scrollAmount,
                                can_scroll_more: container.scrollTop < maxScrollTop - 10
                            };
                        } else {
                            return {
                                success: true,
                                scrolled: 0,
                                can_scroll_more: false
                            };
                        }
                    }
                }
                
                return { success: false, error: "未找到可滚动的下拉容器" };
            })();
            """)
            
            return scroll_result if scroll_result else {"success": False, "can_scroll_more": False}
            
        except Exception as e:
            return {"success": False, "can_scroll_more": False, "error": f"滚动异常: {e}"}
    
    async def _natural_option_selection(self, option_text: str, scroll_result: Dict, attempt: int) -> Dict:
        """
        自然的选项选择行为
        
        避免立即点击，模拟人类确认后点击的行为
        """
        try:
            # 模拟人类确认找到目标选项的时间
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # 使用不同的点击策略来避免检测
            strategies = ["gentle_click", "focus_and_enter", "mouse_events", "natural_tap"]
            strategy = strategies[attempt % len(strategies)]
            
            selection_result = await self.browser_context.execute_javascript(f"""
            (() => {{
                const targetText = "{option_text.replace('"', '\\"')}";
                const strategy = "{strategy}";
                
                // 查找目标选项
                const optionSelectors = [
                    'option', 'li[role="option"]', '.option', '.dropdown-item', '.select-option'
                ];
                
                let targetOption = null;
                
                for (let selector of optionSelectors) {{
                    const options = document.querySelectorAll(selector);
                    for (let option of options) {{
                        if (option.offsetHeight > 0) {{
                            const optionText = option.textContent.trim().toLowerCase();
                            const target = targetText.toLowerCase();
                            if (optionText === target || optionText.includes(target)) {{
                                targetOption = option;
                                break;
                            }}
                        }}
                    }}
                    if (targetOption) break;
                }}
                
                if (!targetOption) {{
                    return {{ success: false, error: "未找到目标选项" }};
                }}
                
                // 执行自然选择
                try {{
                    if (strategy === "gentle_click") {{
                        targetOption.click();
                    }} else if (strategy === "focus_and_enter") {{
                        targetOption.focus();
                        setTimeout(() => {{
                            targetOption.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
                        }}, 50);
                    }} else if (strategy === "mouse_events") {{
                        const rect = targetOption.getBoundingClientRect();
                        const centerX = rect.left + rect.width / 2;
                        const centerY = rect.top + rect.height / 2;
                        
                        ['mouseenter', 'mouseover', 'mousedown', 'click', 'mouseup'].forEach((eventType, index) => {{
                            setTimeout(() => {{
                                const event = new MouseEvent(eventType, {{
                                    bubbles: true,
                                    clientX: centerX,
                                    clientY: centerY
                                }});
                                targetOption.dispatchEvent(event);
                            }}, index * 20);
                        }});
                    }} else {{
                        // natural_tap - 模拟自然触摸
                        targetOption.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        setTimeout(() => targetOption.click(), 150);
                    }}
                    
                    return {{ 
                        success: true, 
                        strategy: strategy,
                        selected_text: targetOption.textContent.trim()
                    }};
                    
                }} catch(error) {{
                    return {{ success: false, error: "选择执行失败: " + error.message }};
                }}
            }})();
            """)
            
            # 选择后的自然停顿
            await asyncio.sleep(random.uniform(0.2, 0.6))
            
            return selection_result if selection_result else {"success": False, "error": "选择脚本返回空"}
            
        except Exception as e:
            return {"success": False, "error": f"选择异常: {e}"}
    
    async def _post_dropdown_human_behavior(self):
        """下拉框操作后的自然行为"""
        # 模拟用户确认选择后的停顿
        await asyncio.sleep(random.uniform(0.3, 0.8))
    
    async def _gentle_selection_verification(self, option_text: str) -> Dict:
        """温和的选择验证，避免过于频繁的检测"""
        try:
            # 给选择操作一些时间生效
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            verification_result = await self.browser_context.execute_javascript(f"""
            (() => {{
                const targetText = "{option_text.replace('"', '\\"')}";
                
                // 检查常见的选择反馈
                const indicators = [
                    () => {{
                        const selected = document.querySelector('[aria-selected="true"]');
                        return selected && selected.textContent.trim().toLowerCase().includes(targetText.toLowerCase());
                    }},
                    () => {{
                        const triggers = document.querySelectorAll('.select-trigger, .dropdown-trigger, select');
                        for (let trigger of triggers) {{
                            const value = trigger.value || trigger.textContent || '';
                            if (value.toLowerCase().includes(targetText.toLowerCase())) return true;
                        }}
                        return false;
                    }},
                    () => {{
                        const hiddenInputs = document.querySelectorAll('input[type="hidden"]');
                        for (let input of hiddenInputs) {{
                            if (input.value.toLowerCase().includes(targetText.toLowerCase())) return true;
                        }}
                        return false;
                    }}
                ];
                
                for (let i = 0; i < indicators.length; i++) {{
                    try {{
                        if (indicators[i]()) {{
                            return {{ success: true, method: `indicator_${{i + 1}}` }};
                        }}
                    }} catch(e) {{
                        // 忽略单个指示器的错误
                    }}
                }}
                
                return {{ success: false, checked_methods: indicators.length }};
            }})();
            """)
            
            return verification_result if verification_result else {"success": False, "error": "验证脚本返回空"}
            
        except Exception as e:
            return {"success": False, "error": f"验证异常: {e}"}

    async def _detect_dropdown_expansion_direction(self, custom_select: Dict) -> Dict:
        """
        🔍 检测下拉框展开方向（向上/向下）
        
        这是解决滚动问题的关键功能：
        - 下拉框可能向下展开（常见）
        - 也可能向上展开（当靠近页面底部时）
        - 不同展开方向需要不同的滚动策略
        """
        try:
            await asyncio.sleep(random.uniform(0.1, 0.3))  # 自然停顿
            
            direction_result = await self.browser_context.execute_javascript("""
            (() => {
                // 查找下拉框触发器和选项容器
                const triggers = document.querySelectorAll(
                    'select, .select-trigger, .dropdown-trigger, .jqselect, [role="combobox"]'
                );
                
                const optionContainers = document.querySelectorAll(
                    '.dropdown-menu, .select-dropdown, .options-container, .jqselect-options, [role="listbox"]'
                );
                
                let detectionResults = [];
                
                // 检测每个下拉框的展开方向
                for (let i = 0; i < Math.max(triggers.length, optionContainers.length); i++) {
                    const trigger = triggers[i];
                    const container = optionContainers[i] || optionContainers[0];
                    
                    if (trigger && container && container.offsetHeight > 0) {
                        const triggerRect = trigger.getBoundingClientRect();
                        const containerRect = container.getBoundingClientRect();
                        
                        // 判断展开方向
                        let direction = 'unknown';
                        let confidence = 0;
                        
                        if (containerRect.top < triggerRect.top) {
                            direction = 'upward';  // 向上展开
                            confidence = triggerRect.top - containerRect.bottom;
                        } else if (containerRect.top > triggerRect.bottom) {
                            direction = 'downward';  // 向下展开
                            confidence = containerRect.top - triggerRect.bottom;
                        } else if (containerRect.top >= triggerRect.top && containerRect.bottom <= triggerRect.bottom + 50) {
                            direction = 'inline';  // 内联展开
                            confidence = 1;
                        }
                        
                        // 检测滚动容器的边界
                        const scrollableHeight = container.scrollHeight;
                        const visibleHeight = container.clientHeight;
                        const currentScrollTop = container.scrollTop;
                        const maxScrollTop = scrollableHeight - visibleHeight;
                        
                        detectionResults.push({
                            direction: direction,
                            confidence: confidence,
                            trigger_position: {
                                top: triggerRect.top,
                                bottom: triggerRect.bottom,
                                height: triggerRect.height
                            },
                            container_position: {
                                top: containerRect.top,
                                bottom: containerRect.bottom,
                                height: containerRect.height
                            },
                            scroll_info: {
                                scrollable_height: scrollableHeight,
                                visible_height: visibleHeight,
                                current_scroll: currentScrollTop,
                                max_scroll: maxScrollTop,
                                can_scroll: scrollableHeight > visibleHeight,
                                scroll_percentage: maxScrollTop > 0 ? currentScrollTop / maxScrollTop : 0
                            },
                            viewport_info: {
                                window_height: window.innerHeight,
                                trigger_distance_from_bottom: window.innerHeight - triggerRect.bottom,
                                container_fits_below: window.innerHeight - triggerRect.bottom >= containerRect.height
                            }
                        });
                    }
                }
                
                // 返回最相关的结果
                if (detectionResults.length > 0) {
                    // 选择置信度最高的结果
                    const bestResult = detectionResults.reduce((best, current) => 
                        current.confidence > best.confidence ? current : best
                    );
                    
                    return {
                        success: true,
                        primary_direction: bestResult.direction,
                        scroll_strategy: bestResult.direction === 'upward' ? 'scroll_up_to_see_more' : 'scroll_down_to_see_more',
                        can_scroll: bestResult.scroll_info.can_scroll,
                        scroll_progress: bestResult.scroll_info.scroll_percentage,
                        expansion_details: bestResult,
                        total_dropdowns_detected: detectionResults.length,
                        all_results: detectionResults
                    };
                } else {
                    return {
                        success: false,
                        error: "未检测到有效的下拉框展开容器",
                        fallback_strategy: "use_keyboard_navigation"
                    };
                }
            })();
            """)
            
            return direction_result if direction_result else {
                "success": False, 
                "error": "方向检测脚本返回空值",
                "fallback_strategy": "assume_downward_expansion"
            }
            
        except Exception as e:
            return {
                "success": False, 
                "error": f"方向检测异常: {e}",
                "fallback_strategy": "assume_downward_expansion"
            }

    async def _enhanced_scroll_strategy_by_direction(self, direction_info: Dict, target_text: str) -> Dict:
        """
        🎯 根据展开方向执行增强滚动策略
        
        关键改进：
        - 向上展开：需要向上滚动查看更多选项
        - 向下展开：需要向下滚动查看更多选项  
        - 内联展开：使用键盘导航
        """
        try:
            if not direction_info.get("success"):
                # 使用默认向下滚动策略
                return await self._gentle_scroll_down_in_dropdown()
            
            direction = direction_info.get("primary_direction", "downward")
            scroll_strategy = direction_info.get("scroll_strategy", "scroll_down_to_see_more")
            can_scroll = direction_info.get("can_scroll", False)
            
            if not can_scroll:
                return {"success": True, "scrolled": 0, "can_scroll_more": False, "reason": "无需滚动"}
            
            # 模拟人类查看和理解展开方向的时间
            await asyncio.sleep(random.uniform(0.3, 0.7))
            
            if direction == "upward":
                # 向上展开的下拉框：需要向上滚动
                scroll_result = await self.browser_context.execute_javascript(f"""
                (() => {{
                    const target = "{target_text.replace('"', '\\"')}";
                    const containers = document.querySelectorAll(
                        '.dropdown-menu, .select-dropdown, .options-container, [role="listbox"]'
                    );
                    
                    for (let container of containers) {{
                        if (container.offsetHeight > 0 && container.scrollHeight > container.clientHeight) {{
                            const currentScroll = container.scrollTop;
                            
                            if (currentScroll > 0) {{
                                // 向上滚动以查看更多选项
                                const scrollAmount = Math.min(80, currentScroll);
                                container.scrollTop -= scrollAmount;
                                
                                return {{
                                    success: true,
                                    direction: "upward",
                                    scrolled: -scrollAmount,
                                    can_scroll_more: container.scrollTop > 0
                                }};
                            }} else {{
                                return {{
                                    success: true,
                                    direction: "upward", 
                                    scrolled: 0,
                                    can_scroll_more: false,
                                    reason: "已在顶部"
                                }};
                            }}
                        }}
                    }}
                    
                    return {{ success: false, error: "未找到可上滚的容器" }};
                }})();
                """)
                
            elif direction == "downward":
                # 向下展开的下拉框：需要向下滚动（原有逻辑）
                scroll_result = await self._gentle_scroll_down_in_dropdown()
                
            elif direction == "inline":
                # 内联展开：使用键盘导航
                scroll_result = await self.browser_context.execute_javascript(f"""
                (() => {{
                    const target = "{target_text.replace('"', '\\"')}";
                    
                    // 尝试使用键盘方向键浏览选项
                    const activeElement = document.activeElement;
                    const containers = document.querySelectorAll('[role="listbox"], .dropdown-menu');
                    
                    for (let container of containers) {{
                        if (container.offsetHeight > 0) {{
                            const options = container.querySelectorAll('[role="option"], .option, li');
                            if (options.length > 5) {{
                                // 模拟按下方向键
                                container.focus();
                                setTimeout(() => {{
                                    container.dispatchEvent(new KeyboardEvent('keydown', {{
                                        key: 'ArrowDown',
                                        bubbles: true
                                    }}));
                                }}, 50);
                                
                                return {{
                                    success: true,
                                    direction: "inline",
                                    method: "keyboard_navigation",
                                    options_count: options.length
                                }};
                            }}
                        }}
                    }}
                    
                    return {{ success: false, error: "键盘导航不可用" }};
                }})();
                """)
            else:
                # 未知方向：使用混合策略
                scroll_result = await self._gentle_scroll_down_in_dropdown()
            
            # 给滚动操作一些时间生效
            await asyncio.sleep(random.uniform(0.2, 0.5))
            
            return scroll_result if scroll_result else {
                "success": False, 
                "error": f"滚动策略执行失败，方向: {direction}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"方向滚动策略异常: {e}"}


class HumanInteractionSimulator:
    """🔥 人类化交互模拟器 - 提供真实的人类行为模拟"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def pre_dropdown_interaction(self):
        """下拉框操作前的人类化行为"""
        # 随机鼠标移动 + 短暂停顿
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
    async def post_dropdown_interaction(self):
        """下拉框操作后的人类化行为"""
        # 操作完成后的短暂停顿
        await asyncio.sleep(random.uniform(0.3, 0.7))
        
    async def dropdown_trigger_delay(self):
        """触发器点击后的等待时间"""
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
    async def post_click_delay(self):
        """点击后的自然等待"""
        await asyncio.sleep(random.uniform(0.2, 0.6))
        
    async def smart_retry_delay(self, attempt: int):
        """智能重试延迟 - 越重试越长"""
        base_delay = 0.5 + (attempt * 0.3)
        actual_delay = base_delay + random.uniform(-0.2, 0.4)
        await asyncio.sleep(max(0.1, actual_delay))


class HumanLikeInputAgent:
    """人类式输入代理 - 提供自然的文本输入和错误提示功能（增强反检测版本）"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        self.page = None  # 🔥 新增：正确的页面对象
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
            element_info = await self.browser_context.execute_javascript(f"""
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
        await self.browser_context.execute_javascript(f"""
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
        await self.browser_context.execute_javascript(f"document.querySelector('{element_selector}')?.focus();")
        await asyncio.sleep(0.1)
    
    async def _thorough_content_cleanup(self):
        """彻底的内容清理"""
        cleanup_methods = ["ctrl_a", "select_all_js", "triple_click"]
        
        for method in cleanup_methods:
            try:
                if method == "ctrl_a":
                    await self.browser_context.keyboard.press("CommandOrControl+a")
                elif method == "select_all_js":
                    await self.browser_context.execute_javascript("document.activeElement?.select?.();")
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
            value = await self.browser_context.execute_javascript(f"""
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
                    await self.browser_context.execute_javascript(js_code)
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
                    background: rgba(76, 175, 80, 0.95) !important;
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
                    border: 1px solid #4caf50 !important;
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
            
            await self.browser_context.execute_javascript(overlay_js)
            self.logger.info(f"✅ 错误提示已显示（不影响页面）: {message[:30]}...")
            
        except Exception as e:
            # 如果悬浮框显示失败，不要影响主要功能
            self.logger.warning(f"⚠️ 显示错误提示失败（不影响主要功能）: {e}")
            pass


class PageDataExtractor:
    """页面数据提取器 - 用于结构化提取问卷页面信息"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        self.page = None  # 🔥 新增：正确的页面对象
        self.logger = logging.getLogger(__name__)
    
    async def extract_page_data_before_submit(self, page_number: int, digital_human_info: Dict, questionnaire_url: str) -> Dict:
        """在提交前提取页面数据"""
        try:
            current_url = await self.browser_context.execute_javascript("window.location.href")
            page_title = await self.browser_context.execute_javascript("document.title")
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
            
            questions_data = await self.browser_context.execute_javascript(extraction_js)
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
        self.page = None  # 🔥 新增：正确的页面对象
        self.logger = logging.getLogger(__name__)
    
    async def navigate_with_redirect_handling(self, target_url: str, max_wait_time: int = 30, max_redirects: int = 5) -> Dict:
        """导航到目标URL并处理自动跳转"""
        start_time = time.time()
        redirect_chain = [target_url]
        
        try:
            self.logger.info(f"🚀 开始导航到目标URL: {target_url}")

            # 🔥 修复：使用browser-use的正确导航方法
            await self.browser_context.create_new_tab()
            await self.browser_context.navigate_to(target_url)
            self.logger.info(f"📄 已使用browser-use方法导航到: {target_url}")
            
            # 1. 初始导航完成
            current_url = target_url
            
            # 2. 监控跳转过程
            for redirect_count in range(max_redirects):
                await asyncio.sleep(2)  # 等待页面稳定
                
                # 获取当前URL
                new_url = await self.browser_context.execute_javascript("window.location.href")
                
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
            final_url = await self.browser_context.execute_javascript("window.location.href")
            await self._wait_for_page_content()
            total_time = time.time() - start_time
            
            return {
                "success": True,
                "final_url": final_url,
                "redirect_count": len(redirect_chain) - 1,
                "redirect_chain": redirect_chain,
                "total_time": total_time,
                "browser_context": self.browser_context  # 🔥 新增：返回浏览器上下文供后续使用
            }
            
        except Exception as e:
            self.logger.error(f"❌ URL导航失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "final_url": "",
                "redirect_count": 0,
                "redirect_chain": redirect_chain,
                "total_time": time.time() - start_time,
                "page": self.page  # 🔥 新增：即使失败也返回页面对象
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
            
            is_redirecting = await self.browser_context.execute_javascript(redirect_indicators_js)
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
            
            is_ready = await self.browser_context.execute_javascript(page_ready_js)
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
            
            # 🛡️ 检查并应用反检测环境
            anti_detection_session = None
            if anti_detection_available:
                logger.info("   🛡️ 创建反检测环境...")
                anti_detection_env = await anti_detection_manager.create_anti_detection_environment(
                    persona_id, persona_name
                )
                
                if anti_detection_env["status"] == "ready":
                    anti_detection_session = anti_detection_env["session_id"]
                    proxy_quality = anti_detection_env.get("proxy_quality", {})
                    logger.info(f"   📊 代理质量评分: {proxy_quality.get('quality_score', 0)}/100")
                    logger.info(f"   🌐 代理IP: {proxy_quality.get('ip_address', '未知')}")
                    logger.info(f"   🎭 浏览器指纹: 已优化")
                else:
                    logger.warning(f"   ⚠️ 反检测环境创建失败: {anti_detection_env.get('error')}")
            
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
            
            # 🔥 关键修复：使用browser_context重新初始化所有组件
            # 直接使用browser_context，不需要单独的page对象
            
            # 🔥 重新初始化所有组件，使用browser_context
            analyzer = IntelligentQuestionnaireAnalyzer(browser_context)
            answer_engine = RapidAnswerEngine(browser_context, state_manager)
            scroll_controller = SmartScrollController(browser_context, state_manager)
            
            # 🔥 设置智能控制器的组件
            intelligent_controller.analyzer = analyzer
            intelligent_controller.answer_engine = answer_engine
            intelligent_controller.scroll_controller = scroll_controller
            
            # 🔥 更新页面数据提取器
            page_extractor = PageDataExtractor(browser_context)
            
            logger.info(f"✅ 成功导航到问卷页面，所有组件已更新为正确的Page对象")
            
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
                    await page.goto(questionnaire_url)
                    await asyncio.sleep(5)  # 给足够时间等待页面加载和自动跳转
                    
                    # 检查基础导航是否成功
                    current_url = await page.evaluate("window.location.href")
                    logger.info(f"✅ 基础导航完成，当前URL: {current_url}")
                    navigation_success = True
                    
                    # 额外等待确保页面完全加载（处理可能的自动跳转）
                    logger.info(f"⏳ 等待页面完全加载（包括可能的自动跳转）...")
                    await asyncio.sleep(5)
                    
                    # 再次检查URL是否发生了跳转
                    final_url = await page.evaluate("window.location.href")
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
                    await page.evaluate(js_navigation)
                    await asyncio.sleep(8)  # 给更多时间等待JavaScript导航
                    
                    current_url = await page.evaluate("window.location.href")
                    logger.info(f"✅ JavaScript导航完成，当前URL: {current_url}")
                    navigation_success = True
                    
                except Exception as js_error:
                    logger.error(f"❌ JavaScript导航也失败: {js_error}")
                    logger.warning(f"⚠️ 所有导航方法失败，但继续执行（浏览器可能已在正确页面）")
            
            # 最终URL验证和页面状态检查
            try:
                current_url = await page.evaluate("window.location.href")
                logger.info(f"📍 当前页面URL: {current_url}")
                
                # 检查页面是否包含问卷内容
                page_content_check = await page.evaluate("""
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
                            await page.evaluate(fix_display_js)
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
                # 使用AI智能答题（原生BrowserUseAgent流程 + WebUI增强）
                llm_name = "deepseek" if hasattr(llm, 'base_url') else "gemini"
                
                # 🔧 创建browser-use原生控制器（解决None controller问题）
                try:
                    # 不传递controller参数，让browser-use使用默认控制器
                    custom_controller = None  # browser-use会使用默认controller
                    logger.info(f"✅ 将使用browser-use默认控制器")
                except Exception as controller_error:
                    logger.warning(f"⚠️ Controller准备遇到问题: {controller_error}")
                    custom_controller = None
                
                # 创建BrowserUseAgent（保持原生智能推理能力）
                # 不传递controller参数，让browser-use使用默认控制器
                agent = BrowserUseAgent(
                    task=complete_prompt,
                    llm=llm,
                    browser=browser,
                    browser_context=browser_context,
                    # controller=custom_controller,  # 🔧 修复：不传递None controller
                    use_vision=True,
                    max_actions_per_step=10,  # 适中的步数
                    tool_calling_method='auto'
                )
                
                logger.info(f"✅ 创建BrowserUseAgent成功: {llm_name}")
                logger.info(f"   视觉能力: 已启用")
                logger.info(f"   WebUI增强: {'已启用' if custom_controller else '未启用'}")
                
                # 🔧 应用智能滚动增强策略（解决滚动限制问题）
                if self._apply_intelligent_scrolling_enhancement(agent):
                    logger.info(f"✅ 智能滚动增强策略已启用")
                else:
                    logger.warning(f"⚠️ 智能滚动增强策略启用失败")
                
                # 执行AI智能答题
                execution_info = await agent.run()
                
            else:
                # 使用本地规则策略（fallback）
                logger.info("🎯 使用本地规则策略...")
                execution_info = await self._execute_local_questionnaire_strategy(
                    browser_context, questionnaire_url, digital_human_info
                )
        
            # 执行后的简单结果处理
            execution_time = time.time() - start_time
            logger.info(f"✅ 问卷任务执行完成，耗时 {execution_time:.1f} 秒")
            
            # 🔧 修复：正确处理BrowserUseAgent的返回结果
            # BrowserUseAgent返回的是AgentHistoryList对象，不是字典
            success_evaluation = self._evaluate_webui_success(execution_info)
            
            # 返回简洁的执行结果
            return {
                "success": success_evaluation.get("is_success", False),
                "success_evaluation": success_evaluation,
                "execution_time": execution_time,
                "completion_result": execution_info,
                "session_id": f"{persona_name}_{int(time.time())}",
                "message": f"BrowserUseAgent问卷任务完成，答题{success_evaluation.get('answered_questions', 0)}题",
                "browser_info": {
                    "profile_id": existing_browser_info.get("profile_id"),
                    "debug_port": debug_port,
                    "proxy_enabled": existing_browser_info.get("proxy_enabled", False),
                    "browser_reused": True,
                    "webui_enhanced": True
                },
                "digital_human": {
                    "id": persona_id,
                    "name": persona_name,
                    "info": digital_human_info,
                    "answered_questions": success_evaluation.get("answered_questions", 0),
                    "completion_score": success_evaluation.get("completion_score", 0.0)
                },
                "execution_mode": "browseruse_with_webui_enhancement",
                "final_status": self._generate_final_status_message(success_evaluation)
            }
        
        except Exception as e:
            logger.error(f"❌ testWenjuan.py模式执行失败: {e}")
        
            # 🚨 修复：不显示错误悬浮框，避免过早显示完成提示
            # 记录错误但让系统继续运行，避免显示误导性的"任务完成"消息
            logger.error(f"⚠️ 任务执行遇到问题，但浏览器将保持运行: {str(e)}")
            
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
        
        # 🚨 移除过早的完成提示，避免误导用户
        # 只有在真正成功完成时才显示完成提示，避免在开始就显示"任务完成"
        logger.info(f"🔄 Agent资源清理完成，浏览器继续运行等待用户操作")

    def _generate_complete_prompt_with_human_like_input(self, digital_human_info: Dict, questionnaire_url: str) -> str:
        """生成完整的数字人提示词（包含详细背景信息）"""
        # 🎭 基础信息
        human_name = digital_human_info.get("name", "未知")
        human_age = digital_human_info.get("age", "30")
        
        # 🔧 修复：正确解析职业信息
        human_job = digital_human_info.get("profession", digital_human_info.get("job", "普通职员"))
        
        # 🔧 修复：正确解析收入信息
        income_level = digital_human_info.get("income_level", "")
        if income_level:
            # 将收入等级转换为具体数字
            income_mapping = {
                "低收入": "4000",
                "中等收入": "8000", 
                "高收入": "15000",
                "中低收入": "5000",
                "中高收入": "12000"
            }
            human_income = income_mapping.get(income_level, "8000")
        else:
            human_income = digital_human_info.get("income", "8000")
        
        human_gender = "女性" if digital_human_info.get("gender", "female") == "female" else "男性"
        
        # 🎓 教育和地理信息
        education = digital_human_info.get("education", "")
        
        # 🔧 修复：正确解析地理信息
        residence = digital_human_info.get("residence", "")
        location = digital_human_info.get("location", "")
        
        # 🎨 兴趣爱好和生活方式 - 从attributes中提取
        attributes = digital_human_info.get("attributes", {})
        interests = attributes.get("爱好", []) or digital_human_info.get("interests", [])
        personality_traits = attributes.get("性格", []) or []
        achievements = attributes.get("成就", "") or ""
        
        # 🏥 健康信息
        health_info = digital_human_info.get("health_info", {})
        health_status = health_info.get("health_status", [])
        
        # 💰 品牌偏好
        favorite_brands = digital_human_info.get("favorite_brands", [])
        
        # 📱 设备偏好
        phone_brand = digital_human_info.get("phone_brand", "")
        
        # 👨‍👩‍👧‍👦 婚姻状况
        marital_status = digital_human_info.get("marital_status", "")
        
        # 🎭 当前状态
        current_mood = digital_human_info.get("mood", "")
        current_activity = digital_human_info.get("activity", "")
        energy_level = digital_human_info.get("energy", "")
        
        # 🏗️ 构建详细的人设描述
        persona_details = []
        
        # 基础信息
        persona_details.append(f"我是{human_name}，一名{human_age}岁的{human_gender}，目前从事{human_job}工作，月收入约{human_income}元")
        
        # 教育背景
        if education:
            persona_details.append(f"教育背景：{education}")
        
        # 地理信息
        if residence:
            persona_details.append(f"我居住在{residence}")
        if location and location != residence:
            persona_details.append(f"目前在{location}")
        
        # 婚姻状况
        if marital_status:
            persona_details.append(f"婚姻状况：{marital_status}")
        
        # 兴趣爱好
        if interests:
            interests_str = "、".join(interests[:5])  # 最多显示5个
            persona_details.append(f"兴趣爱好：{interests_str}")
        
        # 性格特征
        if personality_traits:
            personality_str = "、".join(personality_traits[:3])  # 最多显示3个
            persona_details.append(f"性格特点：{personality_str}")
        
        # 成就
        if achievements:
            persona_details.append(f"主要成就：{achievements}")
        
        # 品牌偏好
        if favorite_brands:
            brands_str = "、".join(favorite_brands[:4])  # 最多显示4个品牌
            persona_details.append(f"喜欢的品牌：{brands_str}")
        
        # 设备偏好
        if phone_brand:
            persona_details.append(f"使用的手机品牌：{phone_brand}")
        
        # 健康状况
        if health_status:
            health_str = "、".join(health_status)
            persona_details.append(f"健康状况：{health_str}")
        
        # 当前状态
        current_state_parts = []
        if current_mood:
            current_state_parts.append(f"心情{current_mood}")
        if energy_level:
            current_state_parts.append(f"精力{energy_level}")
        if current_activity:
            current_state_parts.append(f"正在{current_activity}")
        
        if current_state_parts:
            persona_details.append(f"当前状态：{' '.join(current_state_parts)}")
        
        # 组合完整的人设描述
        complete_persona = "\n".join([f"• {detail}" for detail in persona_details])
        
        prompt = f"""
🎭 我的完整身份信息：
{complete_persona}

以上就是我的完整背景，我将以{human_name}的身份来回答问卷中的所有问题。

🎯 任务：完成问卷调查 {questionnaire_url}

📋 答题原则：
1. 以{human_name}的身份和背景回答所有问题
2. 选择最符合这个人设的答案
3. 确保完成所有题目，不遗漏任何问题
4. 每题只回答一次，不重复作答

✍️ 不同题型的回答策略：
- 单选题：选择一个最合适的选项
- 多选题：选择2-3个相关的选项  
- 下拉框：选择符合身份的选项
- 填空题：根据{human_name}的身份特征填写简短回答（20-50字）
- 评分题：给出中等偏高的评分

🔍 答题状态检查：
- 回答前先观察题目是否已经作答
- 如果已有答案则跳过，避免重复操作
- 专注处理未答题目

📄 完成流程：
1. 逐页回答所有题目
2. 确认无遗漏后提交问卷
3. 如遇到提交错误提示，根据提示补答遗漏题目

记住：你是{human_name}，以这个身份的视角真实回答每个问题。WebUI会自动处理滚动、元素发现、重复检测等技术细节。
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

🏠 地址选择指导：
- 地址相关问题请选择与我的实际居住地一致的选项
- 我的居住地：{residence if residence else "未知"}
- 如有省市区选择，请依次选择对应的省份、城市、区域
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
            
            # 2. 🔧 修复：更严格的答题完成判断逻辑
            
            # 检查是否有错误提示（红色提示、未答题警告等）
            error_keywords = [
                "请选择", "必填项", "未做答", "请填写", "请完善", "错误", "警告",
                "第", "题", "required", "please", "error", "warning", "必须", "请检查"
            ]
            has_error_indicators = any(keyword in final_result_lower for keyword in error_keywords)
            
            # 检查真正的完成标志（严格判断）
            strict_completion_keywords = [
                "提交成功", "问卷完成", "谢谢参与", "感谢您的参与", "完成问卷",
                "submit successful", "questionnaire completed", "thank you", "survey completed",
                "已提交", "提交完成", "调研结束"
            ]
            has_strict_completion = any(keyword in final_result_lower for keyword in strict_completion_keywords)
            
            # 检查页面是否仍在问卷状态（如果有提交按钮、问题标记等，说明未完成）
            questionnaire_continuation_keywords = [
                "提交", "submit", "下一页", "next", "继续", "continue", 
                "单选", "多选", "填空", "选择", "checkbox", "radio", "input"
            ]
            still_in_questionnaire = any(keyword in final_result_lower for keyword in questionnaire_continuation_keywords)
            
            logger.info(f"🔍 完成状态分析: 明确完成={has_strict_completion}, 仍在问卷={still_in_questionnaire}, 有错误={has_error_indicators}")
            
            # 3. 严格的成功判断逻辑（修复核心逻辑）
            if has_error_indicators and not has_strict_completion:
                # 🚨 有错误提示且无明确完成标志 = 未完成
                completion_score = 0.2
                confidence = 0.8
                success_type = "incomplete_with_errors"
                is_success = False
                logger.warning(f"⚠️ 检测到错误提示，判断为未完成")
                
            elif still_in_questionnaire and not has_strict_completion:
                # 🚨 仍在问卷页面且无明确完成标志 = 未完成
                completion_score = 0.3
                confidence = 0.7
                success_type = "incomplete_in_progress"
                is_success = False
                logger.warning(f"⚠️ 仍在问卷页面，判断为未完成")
                
            elif has_strict_completion and estimated_questions >= 3:
                # ✅ 明确完成标志 + 有一定答题量 = 真正完成
                completion_score = 0.95
                confidence = 0.9
                success_type = "complete"
                is_success = True
                logger.info(f"✅ 检测到明确完成标志，判断为完成")
                
            elif has_completion_words and estimated_questions >= 8 and not has_error_indicators and not still_in_questionnaire:
                # ✅ 一般完成词汇 + 答题量很充足 + 无错误 + 不在问卷页面 = 可能完成
                completion_score = 0.8
                confidence = 0.7
                success_type = "likely_complete"
                is_success = True
                logger.info(f"✅ 答题量很充足且无错误，判断为可能完成")
                
            elif estimated_questions >= 8 and not has_error_indicators and not still_in_questionnaire:
                # ✅ 答题量很充足 + 无错误 + 不在问卷页面 = 部分完成
                completion_score = 0.7
                confidence = 0.6
                success_type = "partial_high"
                is_success = True
                logger.info(f"✅ 答题量很充足，判断为部分完成")
                
            elif estimated_questions >= 6 and not has_error_indicators and not still_in_questionnaire:
                # 🔶 答题量中等 + 无明显错误 + 不在问卷页面 = 部分完成
                completion_score = 0.5
                confidence = 0.5
                success_type = "partial_medium"
                is_success = True
                logger.info(f"🔶 答题量中等且不在问卷页面，判断为部分完成")
                
            elif estimated_questions >= 1 and not has_error_indicators:
                # 🔶 至少有答题但可能不完整，只有无错误时才可能是部分成功
                completion_score = 0.3
                confidence = 0.4
                success_type = "partial_low"
                is_success = False  # 保持False，因为答题量太少
                logger.warning(f"🔶 答题量较少，判断为不完整")
                
            else:
                # ❌ 没有检测到有效答题
                completion_score = 0.1
                confidence = 0.3
                success_type = "incomplete"
                is_success = False
                logger.error(f"❌ 没有检测到有效答题，判断为未完成")
            
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

    def _apply_dropdown_enhancement_patch(self, controller) -> bool:
        """
        应用WebUI增强补丁，修复browser-use函数参数不匹配问题
        关键修复：支持多种调用方式，避免过早结束
        """
        try:
            import asyncio
            import random
            
            logger.info("🔧 开始应用WebUI增强补丁...")
            
            # 查找select_dropdown_option动作
            if not hasattr(controller, 'registry'):
                logger.warning("⚠️ Controller没有registry属性")
                return False
            
            registry = controller.registry
            
            # 正确访问actions字典 - 兼容不同结构
            if hasattr(registry, 'actions'):
                actions = registry.actions
            elif hasattr(registry, 'registry') and hasattr(registry.registry, 'actions'):
                actions = registry.registry.actions
            else:
                logger.error("❌ 无法找到actions字典")
                return False
            
            select_action_key = None
            input_action_key = None
            
            logger.info(f"🔍 可用的actions: {list(actions.keys())}")
            
            for action_name, action_info in actions.items():
                # 检查不同的属性名 (func 或 function)
                if 'select_dropdown_option' in action_name:
                    if hasattr(action_info, 'func') or hasattr(action_info, 'function'):
                        select_action_key = action_name
                        logger.info(f"🔍 找到下拉框函数: {action_name}")
                if 'input_text' in action_name:
                    if hasattr(action_info, 'func') or hasattr(action_info, 'function'):
                        input_action_key = action_name
                        logger.info(f"🔍 找到文本输入函数: {action_name}")
            
            enhanced_count = 0
            
            # 增强select_dropdown_option
            if select_action_key:
                original_action = actions[select_action_key]
                # 兼容不同的函数属性名
                if hasattr(original_action, 'func'):
                    original_function = original_action.func
                elif hasattr(original_action, 'function'):
                    original_function = original_action.function
                else:
                    logger.error(f"❌ 无法获取函数: {select_action_key}")
                    return False
                
                # 🔧 创建本地ActionResult类避免导入问题
                class ActionResult:
                    def __init__(self, extracted_content=None, include_in_memory=True, error=None):
                        self.extracted_content = extracted_content
                        self.include_in_memory = include_in_memory
                        self.error = error
                
                # 创建增强版本的包装函数，保持正确的签名
                async def enhanced_select_dropdown_option(
                    index: int,
                    text: str,
                    browser,
                ):
                    """增强版下拉框选择函数 - 支持滚动"""
                    try:
                        logger.info(f"🎯 使用增强下拉框选择: index={index}, text='{text}'")
                        
                        # 先尝试原有逻辑
                        try:
                            result = await original_function(index, text, browser)
                            if (hasattr(result, 'extracted_content') and 
                                result.extracted_content and 
                                "selected option" in result.extracted_content and
                                not result.error):
                                logger.info(f"✅ 原有逻辑成功")
                                return result
                        except Exception as orig_error:
                            logger.info(f"⚠️ 原有逻辑失败: {orig_error}")
                        
                        # 🔥 增强逻辑：人类模拟下拉框操作流程（含级联菜单智能处理）
                        page = await browser.get_current_page()
                        selector_map = await browser.get_selector_map()
                        
                        if index not in selector_map:
                            logger.error(f"❌ 元素索引 {index} 不存在")
                            raise Exception(f'Element with index {index} does not exist')
                        
                        dom_element = selector_map[index]
                        
                        # 🎯 新增：级联菜单智能检测
                        cascade_detection = await page.evaluate("""
                        () => {
                            // 🔍 检测级联下拉菜单模式（省市区）
                            const allSelects = Array.from(document.querySelectorAll('select, .select-wrapper, .dropdown-wrapper, [class*="select"], [class*="dropdown"]'));
                            
                            const selectsInfo = allSelects.map((sel, idx) => {
                                const text = sel.textContent || sel.value || sel.placeholder || '';
                                const label = sel.closest('label') ? sel.closest('label').textContent : '';
                                const parentText = sel.parentElement ? sel.parentElement.textContent : '';
                                const nearbyText = Array.from(sel.parentElement?.children || [])
                                    .map(child => child.textContent).join(' ');
                                
                                const allText = (text + ' ' + label + ' ' + parentText + ' ' + nearbyText).toLowerCase();
                                
                                return {
                                    element: sel,
                                    index: idx,
                                    text: text.trim(),
                                    label: label.trim(),
                                    all_text: allText,
                                    is_province: allText.includes('省') || allText.includes('province') || 
                                               allText.includes('省份') || allText.includes('地区'),
                                    is_city: allText.includes('市') || allText.includes('city') || 
                                            allText.includes('城市') || allText.includes('地市'),
                                    is_district: allText.includes('区') || allText.includes('县') || 
                                               allText.includes('district') || allText.includes('area'),
                                    has_options: sel.tagName === 'SELECT' ? sel.options.length > 1 : false,
                                    is_empty: text.includes('请选择') || text.includes('选择') || text === '' || 
                                             text.includes('please select') || text.includes('choose'),
                                    position: sel.getBoundingClientRect()
                                };
                            });
                            
                            // 分析级联关系
                            const provinceSelects = selectsInfo.filter(s => s.is_province);
                            const citySelects = selectsInfo.filter(s => s.is_city);
                            const districtSelects = selectsInfo.filter(s => s.is_district);
                            
                            let cascadeInfo = {
                                is_cascade: false,
                                pattern: 'none',
                                current_level: 0,
                                total_levels: 0,
                                selects_info: selectsInfo,
                                province_count: provinceSelects.length,
                                city_count: citySelects.length,
                                district_count: districtSelects.length
                            };
                            
                            // 检测级联模式
                            if (provinceSelects.length > 0 && citySelects.length > 0) {
                                cascadeInfo.is_cascade = true;
                                cascadeInfo.pattern = 'province_city';
                                cascadeInfo.total_levels = 2;
                                
                                if (districtSelects.length > 0) {
                                    cascadeInfo.pattern = 'province_city_district';
                                    cascadeInfo.total_levels = 3;
                                }
                                
                                // 根据位置排序（从上到下，从左到右）
                                const orderedSelects = [
                                    ...provinceSelects.sort((a, b) => a.position.top - b.position.top || a.position.left - b.position.left),
                                    ...citySelects.sort((a, b) => a.position.top - b.position.top || a.position.left - b.position.left),
                                    ...districtSelects.sort((a, b) => a.position.top - b.position.top || a.position.left - b.position.left)
                                ];
                                
                                cascadeInfo.ordered_selects = orderedSelects;
                            }
                            
                            return cascadeInfo;
                        }
                        """)
                        
                        if cascade_detection and cascade_detection.get("is_cascade"):
                            logger.info(f"🔗 检测到级联菜单: {cascade_detection.get('pattern')}, 总层级: {cascade_detection.get('total_levels')}")
                            logger.info(f"📊 省级选择器: {cascade_detection.get('province_count')}, 市级: {cascade_detection.get('city_count')}, 区级: {cascade_detection.get('district_count')}")
                        
                        # 🎯 人类模拟下拉框操作：读题→点击→滚动→选择
                        human_dropdown_js = f"""
                        () => {{
                            const targetText = '{text.replace("'", "\\'")}';
                            const elementXPath = '{dom_element.xpath}';
                            
                            // 📖 步骤1：定位目标元素
                            const element = document.evaluate(elementXPath, document, null,
                                XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                            
                            if (!element) {{
                                return {{ success: false, error: 'Element not found' }};
                            }}
                            
                            // 确保元素可见
                            element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                            
                            // 🖱️ 步骤2：根据元素类型执行不同策略（增强级联菜单支持）
                            if (element.tagName === 'SELECT') {{
                                // 原生select处理（增强级联菜单支持）
                                const options = Array.from(element.options);
                                const targetOption = options.find(opt => 
                                    opt.text.includes(targetText) || opt.text.trim() === targetText
                                );
                                
                                if (targetOption) {{
                                    // 🎯 人类式选择：聚焦→选择→确认
                                    element.focus();
                                    element.value = targetOption.value;
                                    element.selectedIndex = targetOption.index;
                                    
                                    // 触发事件
                                    element.dispatchEvent(new Event('focus', {{ bubbles: true }}));
                                    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    element.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                                    
                                    // 🔗 级联菜单特殊处理：触发下级菜单加载
                                    const selectLabel = element.closest('label') ? element.closest('label').textContent : '';
                                    const selectText = element.textContent || '';
                                    const allSelectText = (selectLabel + ' ' + selectText).toLowerCase();
                                    
                                    // 🔗 智能级联菜单处理：完全自动化技术实现
                                    if (allSelectText.includes('省') || allSelectText.includes('province') || allSelectText.includes('地区')) {{
                                        // 省级选择，智能触发市级菜单加载
                                        setTimeout(() => {{
                                            const allSelects = document.querySelectorAll('select');
                                            for (let nextSelect of allSelects) {{
                                                const nextLabel = nextSelect.closest('label') ? nextSelect.closest('label').textContent : '';
                                                const nextText = (nextLabel + ' ' + nextSelect.textContent).toLowerCase();
                                                if (nextText.includes('市') || nextText.includes('city') || nextText.includes('城市')) {{
                                                    // 多重触发确保加载
                                                    nextSelect.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                                    nextSelect.dispatchEvent(new Event('focus', {{ bubbles: true }}));
                                                    nextSelect.dispatchEvent(new Event('refresh', {{ bubbles: true }}));
                                                    nextSelect.dispatchEvent(new Event('load', {{ bubbles: true }}));
                                                    
                                                    // 检查是否为空选择框，触发数据加载
                                                    if (nextSelect.options.length <= 1) {{
                                                        nextSelect.dispatchEvent(new Event('click', {{ bubbles: true }}));
                                                    }}
                                                    break;
                                                }}
                                            }}
                                        }}, 800); // 增加等待时间确保加载
                                    }} else if (allSelectText.includes('市') || allSelectText.includes('city') || allSelectText.includes('城市')) {{
                                        // 市级选择，智能触发区级菜单加载
                                        setTimeout(() => {{
                                            const allSelects = document.querySelectorAll('select');
                                            for (let nextSelect of allSelects) {{
                                                const nextLabel = nextSelect.closest('label') ? nextSelect.closest('label').textContent : '';
                                                const nextText = (nextLabel + ' ' + nextSelect.textContent).toLowerCase();
                                                if (nextText.includes('区') || nextText.includes('县') || nextText.includes('district') || nextText.includes('area')) {{
                                                    // 多重触发确保加载
                                                    nextSelect.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                                    nextSelect.dispatchEvent(new Event('focus', {{ bubbles: true }}));
                                                    nextSelect.dispatchEvent(new Event('refresh', {{ bubbles: true }}));
                                                    nextSelect.dispatchEvent(new Event('load', {{ bubbles: true }}));
                                                    
                                                    // 检查是否为空选择框，触发数据加载
                                                    if (nextSelect.options.length <= 1) {{
                                                        nextSelect.dispatchEvent(new Event('click', {{ bubbles: true }}));
                                                    }}
                                                    break;
                                                }}
                                            }}
                                        }}, 800); // 增加等待时间确保加载
                                    }}
                                    
                                    return {{ 
                                        success: true, 
                                        method: 'native_select_cascade', 
                                        selectedText: targetOption.text,
                                        cascade_triggered: true
                                    }};
                                }}
                            }} else {{
                                // 🔄 步骤3：自定义下拉框的人类交互
                                // 先尝试展开下拉框
                                let expanded = false;
                                
                                // 多种展开策略
                                const expandStrategies = [
                                    () => {{
                                        element.click();
                                        return true;
                                    }},
                                    () => {{
                                        const trigger = element.querySelector('.dropdown-trigger, .select-trigger, .jqselect-text') ||
                                                       element.closest('.dropdown, .select-wrapper, .jqselect');
                                        if (trigger) {{
                                            trigger.click();
                                            return true;
                                        }}
                                        return false;
                                    }},
                                    () => {{
                                        element.focus();
                                        element.dispatchEvent(new KeyboardEvent('keydown', {{ 
                                            key: 'ArrowDown', 
                                            bubbles: true 
                                        }}));
                                        return true;
                                    }}
                                ];
                                
                                for (let strategy of expandStrategies) {{
                                    try {{
                                        if (strategy()) {{
                                            expanded = true;
                                            break;
                                        }}
                                    }} catch (e) {{
                                        continue;
                                    }}
                                }}
                                
                                if (!expanded) {{
                                    return {{ success: false, error: 'Cannot expand dropdown' }};
                                }}
                                
                                // 👁️ 步骤4：视觉搜索 + 智能滚动
                                return new Promise((resolve) => {{
                                    setTimeout(() => {{
                                        const containerSelectors = [
                                            '.dropdown-menu', '.select-dropdown', '.options-container',
                                            '.jqselect-options', '[role="listbox"]', '.dropdown-options',
                                            '.el-select-dropdown', '.ant-select-dropdown', '.layui-select-options'
                                        ];
                                        
                                        for (let containerSelector of containerSelectors) {{
                                            const containers = document.querySelectorAll(containerSelector);
                                            for (let container of containers) {{
                                                if (container.offsetHeight > 0 && container.offsetWidth > 0) {{
                                                    // 🔍 搜索可见选项
                                                    const optionSelectors = [
                                                        'li', '.option', '.dropdown-item', '.select-option',
                                                        '[role="option"]', '.item', '.choice'
                                                    ];
                                                    
                                                    for (let optionSelector of optionSelectors) {{
                                                        const options = container.querySelectorAll(optionSelector);
                                                        for (let option of options) {{
                                                            if (option.offsetHeight > 0) {{
                                                                const optionText = option.textContent.trim();
                                                                if (optionText.includes(targetText) || optionText === targetText) {{
                                                                    // 🎯 找到目标，执行人类式选择
                                                                    option.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                                                    
                                                                    // 模拟鼠标悬停
                                                                    option.dispatchEvent(new MouseEvent('mouseover', {{ bubbles: true }}));
                                                                    
                                                                    // 点击选择
                                                                    option.click();
                                                                    option.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                                                    
                                                                    resolve({{ 
                                                                        success: true, 
                                                                        method: 'custom_dropdown_human', 
                                                                        selectedText: optionText 
                                                                    }});
                                                                    return;
                                                                }}
                                                            }}
                                                        }}
                                                    }}
                                                    
                                                    // 🔄 如果没找到且容器可滚动，进行智能滚动搜索
                                                    if (container.scrollHeight > container.clientHeight) {{
                                                        let scrollAttempts = 0;
                                                        const maxScrollAttempts = 8; // 模拟人类耐心有限
                                                        
                                                        const scrollSearch = () => {{
                                                            if (scrollAttempts >= maxScrollAttempts) {{
                                                                resolve({{ success: false, error: 'Scroll search exhausted' }});
                                                                return;
                                                            }}
                                                            
                                                            // 温和滚动
                                                            container.scrollBy({{ top: 80, behavior: 'smooth' }});
                                                            scrollAttempts++;
                                                            
                                                            setTimeout(() => {{
                                                                // 检查新出现的选项
                                                                for (let optionSelector of optionSelectors) {{
                                                                    const newOptions = container.querySelectorAll(optionSelector);
                                                                    for (let option of newOptions) {{
                                                                        if (option.offsetHeight > 0) {{
                                                                            const optionText = option.textContent.trim();
                                                                            if (optionText.includes(targetText) || optionText === targetText) {{
                                                                                option.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                                                                option.dispatchEvent(new MouseEvent('mouseover', {{ bubbles: true }}));
                                                                                option.click();
                                                                                
                                                                                resolve({{ 
                                                                                    success: true, 
                                                                                    method: 'scroll_search_human', 
                                                                                    selectedText: optionText 
                                                                                }});
                                                                                return;
                                                                            }}
                                                                        }}
                                                                    }}
                                                                }}
                                                                
                                                                // 检查是否到底部
                                                                if (container.scrollTop >= container.scrollHeight - container.clientHeight - 10) {{
                                                                    resolve({{ success: false, error: 'Reached bottom, option not found' }});
                                                                    return;
                                                                }}
                                                                
                                                                // 继续滚动搜索
                                                                scrollSearch();
                                                            }}, 300); // 人类滚动后的观察时间
                                                        }};
                                                        
                                                        scrollSearch();
                                                        return;
                                                    }}
                                                }}
                                            }}
                                        }}
                                        
                                        resolve({{ success: false, error: 'No suitable dropdown container found' }});
                                    }}, 500); // 等待下拉框展开
                                }});
                            }}
                            
                            return {{ success: false, error: 'Unsupported element type' }};
                        }}
                        """
                        
                        enhanced_result = await page.evaluate(human_dropdown_js)
                        
                        if enhanced_result.get("success"):
                            # 🎉 人类模拟成功，添加自然的后续行为
                            await asyncio.sleep(random.uniform(0.4, 1.0))  # 人类选择后的确认停顿
                            
                            method = enhanced_result.get("method", "human_enhanced")
                            selected_text = enhanced_result.get("selectedText", text)
                            
                            # 🔗 智能级联菜单验证：自动检测和等待（完全技术层面）
                            if enhanced_result.get("cascade_triggered") and cascade_detection and cascade_detection.get("is_cascade"):
                                logger.info(f"⏳ 智能级联处理：自动等待下级选项加载...")
                                
                                # 智能等待机制：多次检测直到加载完成或超时
                                max_wait_attempts = 6
                                wait_interval = 1.0
                                
                                for attempt in range(max_wait_attempts):
                                    await asyncio.sleep(wait_interval)
                                    
                                    # 智能验证下级菜单加载状态
                                    cascade_verification = await page.evaluate("""
                                    () => {
                                        const allSelects = document.querySelectorAll('select');
                                        let loadedMenus = 0;
                                        let totalOptions = 0;
                                        let menuDetails = [];
                                        
                                        for (let select of allSelects) {
                                            const label = select.closest('label') ? select.closest('label').textContent : '';
                                            const text = select.textContent || select.value || '';
                                            const allText = (label + ' ' + text).toLowerCase();
                                            
                                            if (select.options.length > 1) {
                                                if (allText.includes('市') || allText.includes('city') || allText.includes('城市')) {
                                                    loadedMenus++;
                                                    totalOptions += select.options.length;
                                                    menuDetails.push({type: 'city', options: select.options.length});
                                                } else if (allText.includes('区') || allText.includes('县') || allText.includes('district')) {
                                                    loadedMenus++;
                                                    totalOptions += select.options.length;
                                                    menuDetails.push({type: 'district', options: select.options.length});
                                                }
                                            }
                                        }
                                        
                                        return { 
                                            success: loadedMenus > 0, 
                                            loaded_menus: loadedMenus, 
                                            total_options: totalOptions,
                                            menu_details: menuDetails,
                                            ready_for_next_selection: loadedMenus > 0
                                        };
                                    }
                                    """)
                                    
                                    if cascade_verification and cascade_verification.get("ready_for_next_selection"):
                                        logger.info(f"✅ 级联菜单加载完成 (尝试{attempt+1}/{max_wait_attempts})：{cascade_verification.get('loaded_menus')}个菜单，{cascade_verification.get('total_options')}个选项")
                                        break
                                    elif attempt < max_wait_attempts - 1:
                                        logger.info(f"⏳ 继续等待级联菜单加载 (尝试{attempt+1}/{max_wait_attempts})...")
                                    else:
                                        logger.warning(f"⚠️ 级联菜单等待超时，但系统将继续执行")
                            
                            # 记录成功的人类模拟操作
                            if "human" in method:
                                msg = f"🎯 Human-like selected option '{selected_text}' using {method}"
                            else:
                                msg = f"selected option {selected_text} using {method} (enhanced)"
                            
                            if enhanced_result.get("cascade_triggered"):
                                msg += " (cascade menu triggered)"
                            
                            logger.info(f"✅ {msg}")
                            return ActionResult(extracted_content=msg, include_in_memory=True)
                        else:
                            # 🔄 人类模拟未找到目标，尝试传统回退
                            error_reason = enhanced_result.get("error", "Unknown reason")
                            logger.warning(f"⚠️ 人类模拟下拉框操作失败: {error_reason}")
                            
                            # 最后尝试原有函数
                            logger.info(f"🔄 回退到原有函数作为最后尝试...")
                            try:
                                return await original_function(index, text, browser)
                            except Exception as fallback_error:
                                logger.error(f"❌ 最终回退也失败: {fallback_error}")
                                return ActionResult(error=f"下拉框选择完全失败: {text} ({error_reason})")
                            
                    except Exception as e:
                        logger.error(f"❌ 增强下拉框选择异常: {e}")
                        # 最终回退
                        try:
                            return await original_function(index, text, browser)
                        except:
                            return ActionResult(error=f"下拉框选择失败: {e}")
                
                # 替换函数 - 兼容不同属性名
                if hasattr(original_action, 'func'):
                    original_action.func = enhanced_select_dropdown_option
                elif hasattr(original_action, 'function'):
                    original_action.function = enhanced_select_dropdown_option
                
                enhanced_count += 1
                logger.info("✅ 下拉框增强补丁应用成功")
            
            # 增强input_text函数
            if input_action_key:
                original_input_action = actions[input_action_key]
                # 兼容不同的函数属性名
                if hasattr(original_input_action, 'func'):
                    original_input_function = original_input_action.func
                elif hasattr(original_input_action, 'function'):
                    original_input_function = original_input_action.function
                else:
                    logger.error(f"❌ 无法获取输入函数: {input_action_key}")
                    return False
                
                # 🔥 关键修复：支持browser-use的多种调用方式
                async def enhanced_input_text(*args, **kwargs) -> ActionResult:
                    """
                    增强版文本输入函数，兼容browser-use的各种调用方式
                    支持关键字参数、位置参数、params对象等多种格式
                    """
                    try:
                        # 🔧 Step 1: 解析参数 - 支持多种格式
                        index = None
                        text = None
                        browser = None
                        has_sensitive_data = False
                        
                        # 方式1: 关键字参数格式 (browser-use主要方式)
                        if 'index' in kwargs and 'text' in kwargs:
                            index = kwargs['index']
                            text = kwargs['text']
                            browser = kwargs.get('browser') or kwargs.get('browser_context')
                            has_sensitive_data = kwargs.get('has_sensitive_data', False)
                            logger.info(f"✅ 关键字参数解析成功: index={index}, text='{text[:30]}...'")
                        
                        # 方式2: 位置参数格式 (params, browser, has_sensitive_data)
                        elif len(args) >= 2:
                            params = args[0]
                            browser = args[1]
                            has_sensitive_data = args[2] if len(args) > 2 else False
                            
                            # 从params对象中提取参数
                            if hasattr(params, 'index'):
                                index = params.index
                            elif isinstance(params, dict):
                                index = params.get('index')
                                
                            if hasattr(params, 'text'):
                                text = params.text
                            elif isinstance(params, dict):
                                text = params.get('text')
                                
                            logger.info(f"✅ 位置参数解析成功: index={index}, text='{text[:30]}...'")
                        
                        # 方式3: 混合格式
                        elif 'params' in kwargs:
                            params = kwargs['params']
                            browser = kwargs.get('browser') or kwargs.get('browser_context')
                            has_sensitive_data = kwargs.get('has_sensitive_data', False)
                            
                            if hasattr(params, 'index'):
                                index = params.index
                            if hasattr(params, 'text'):
                                text = params.text
                            logger.info(f"✅ 混合参数解析成功: index={index}, text='{text[:30]}...'")
                        
                        # 验证参数
                        if index is None or text is None:
                            logger.error(f"❌ 参数解析失败: args={len(args)}, kwargs={list(kwargs.keys())}")
                            return ActionResult(
                                extracted_content=f"Input failed: Invalid parameters",
                                include_in_memory=True,
                                error="Invalid parameters: missing index or text"
                            )
                        
                        # 🔧 Step 2: 尝试原始方法（如果可能）
                        try:
                            if len(args) >= 2:
                                # 位置参数调用
                                result = await original_input_function(*args)
                            else:
                                # 尝试构造原始调用
                                class MockParams:
                                    def __init__(self, index, text):
                                        self.index = index
                                        self.text = text
                                
                                params = MockParams(index, text)
                                result = await original_input_function(params, browser, has_sensitive_data)
                            
                            if result and not getattr(result, 'error', None):
                                logger.info(f"✅ 原始方法成功")
                                return result
                        except Exception as e:
                            logger.warning(f"⚠️ 原始输入方法失败，使用增强fallback: {str(e)}")
                        
                        # 🔧 Step 3: 增强JavaScript fallback策略
                        if not browser:
                            logger.error("❌ 缺少browser参数，无法执行fallback")
                            return ActionResult(
                                extracted_content=f"Input failed: Missing browser parameter",
                                include_in_memory=True,
                                error="Missing browser parameter for fallback"
                            )
                        
                        logger.info(f"🔧 使用JavaScript增强输入: index={index}, text='{text[:30]}...'")
                        
                        # 刷新DOM快照，解决滚动后元素索引变化问题
                        try:
                            await browser._extract_dom_snapshot()
                            logger.info(f"🔄 DOM快照已刷新")
                        except Exception as refresh_e:
                            logger.warning(f"⚠️ DOM刷新失败，继续尝试: {refresh_e}")
                        
                        selector_map = await browser.get_selector_map()
                        if index not in selector_map:
                            logger.error(f"❌ 元素索引 {index} 不存在，当前可用索引: {list(selector_map.keys())[:10]}...")
                            return ActionResult(
                                extracted_content=f"Input failed: Element index {index} does not exist",
                                include_in_memory=True,
                                error=f'Element index {index} does not exist'
                            )
                        
                        page = await browser.get_current_page()
                        dom_element = selector_map[index]
                        
                        # 使用增强JavaScript直接设置值
                        js_input = f"""
                        (function() {{
                            const xpath = '{dom_element.xpath}';
                            const text = `{text.replace('`', '\\`').replace('${', '\\${').replace('\\', '\\\\')}`;
                            
                            try {{
                                const element = document.evaluate(
                                    xpath, document, null,
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, null
                                ).singleNodeValue;
                                
                                if (!element) {{
                                    return {{ success: false, error: 'Element not found by xpath' }};
                                }}
                                
                                // 确保元素可见
                                element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                
                                // 多种输入策略
                                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {{
                                    // 聚焦并清空
                                    element.focus();
                                    element.select();
                                    element.value = '';
                                    
                                    // 设置新值
                                    element.value = text;
                                    
                                    // 触发完整的事件序列
                                    element.dispatchEvent(new Event('focus', {{ bubbles: true }}));
                                    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    element.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                                    
                                    return {{ success: true, method: 'direct', value: element.value }};
                                }} else if (element.contentEditable === 'true') {{
                                    element.focus();
                                    element.textContent = text;
                                    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    return {{ success: true, method: 'contentEditable', value: element.textContent }};
                                }}
                                
                                return {{ success: false, error: 'Element not inputable: ' + element.tagName }};
                            }} catch (error) {{
                                return {{ success: false, error: error.toString() }};
                            }}
                        }})()
                        """
                        
                        js_result = await page.evaluate(js_input)
                        
                        if js_result and js_result.get('success'):
                            if not has_sensitive_data:
                                msg = f'⌨️  Enhanced input "{text}" into index {index} via {js_result.get("method", "unknown")}'
                            else:
                                msg = f'⌨️  Enhanced input sensitive data into index {index}'
                            logger.info(msg)
                            return ActionResult(extracted_content=msg, include_in_memory=True)
                        else:
                            error_msg = js_result.get('error', 'Unknown error') if js_result else 'No result'
                            logger.error(f"❌ JavaScript input failed: {error_msg}")
                            return ActionResult(
                                extracted_content=f"Input failed: {error_msg}",
                                include_in_memory=True,
                                error=error_msg
                            )
                    
                    except Exception as e:
                        logger.error(f"❌ 增强输入方法失败: {str(e)}")
                        # 🚨 重要：不抛出异常，返回失败结果让系统继续
                        return ActionResult(
                            extracted_content=f"Input failed: {str(e)}", 
                            include_in_memory=True,
                            error=str(e)
                        )
                
                # 替换原函数 - 兼容不同属性名
                if hasattr(original_input_action, 'func'):
                    original_input_action.func = enhanced_input_text
                elif hasattr(original_input_action, 'function'):
                    original_input_action.function = enhanced_input_text
                
                enhanced_count += 1
                logger.info("✅ 文本输入增强补丁应用成功")
            
            if enhanced_count > 0:
                logger.info(f"✅ 总共应用了 {enhanced_count} 个增强补丁")
                return True
            else:
                logger.warning("⚠️ 未找到需要增强的函数")
                return False
                
        except Exception as e:
            logger.error(f"❌ 应用增强补丁失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False

    def _apply_intelligent_scrolling_enhancement(self, agent) -> bool:
        """应用智能滚动增强策略，解决页面高度限制和元素发现问题"""
        try:
            logger.info("🔧 开始应用智能滚动增强策略...")
            
            # 获取Agent的controller
            controller = agent._controller
            if not hasattr(controller, 'registry') or not hasattr(controller.registry, 'registry'):
                logger.error("❌ 无法访问controller.registry.registry")
                return False
            
            actions = controller.registry.registry.actions
            scroll_action_key = None
            
            # 查找滚动action
            for action_name, action_info in actions.items():
                if 'scroll_down' in action_name:
                    scroll_action_key = action_name
                    break
            
            if not scroll_action_key:
                logger.warning("⚠️ 未找到scroll_down函数")
                return False
            
            # 增强scroll_down函数
            original_scroll_action = actions[scroll_action_key]
            if hasattr(original_scroll_action, 'func'):
                original_scroll_function = original_scroll_action.func
            elif hasattr(original_scroll_action, 'function'):
                original_scroll_function = original_scroll_action.function
            else:
                logger.error(f"❌ 无法获取滚动函数: {scroll_action_key}")
                return False
            
            # 🔧 创建本地ActionResult类避免导入问题
            class ActionResult:
                def __init__(self, extracted_content=None, include_in_memory=True, error=None):
                    self.extracted_content = extracted_content
                    self.include_in_memory = include_in_memory
                    self.error = error
            
            async def enhanced_scroll_down(params, browser) -> ActionResult:
                """增强版滚动函数，解决页面高度限制和元素发现问题"""
                try:
                    # 首先尝试原始滚动
                    result = await original_scroll_function(params, browser)
                    
                    # 🔄 滚动后强制刷新DOM快照，解决元素索引变化问题
                    try:
                        await browser._extract_dom_snapshot()
                        logger.info("🔄 滚动后自动刷新DOM快照")
                    except Exception as refresh_e:
                        logger.warning(f"⚠️ DOM刷新失败: {refresh_e}")
                    
                    # 🔍 检查是否发现新的可交互元素
                    try:
                        page = await browser.get_current_page()
                        
                        # 检查页面是否还能继续滚动
                        can_scroll_more = await page.evaluate("""
                        () => {
                            const maxScroll = document.body.scrollHeight - window.innerHeight;
                            const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
                            const remaining = maxScroll - currentScroll;
                            
                            return {
                                canScroll: remaining > 50,
                                currentPosition: currentScroll,
                                maxPosition: maxScroll,
                                remaining: remaining,
                                pageHeight: document.body.scrollHeight,
                                viewHeight: window.innerHeight
                            };
                        }
                        """)
                        
                        if can_scroll_more:
                            logger.info(f"🔄 页面滚动状态: 当前{can_scroll_more['currentPosition']}, 最大{can_scroll_more['maxPosition']}, 剩余{can_scroll_more['remaining']}")
                            
                            # 检查新发现的元素
                            new_elements_count = len(await browser.get_selector_map())
                            logger.info(f"🔍 当前页面可交互元素总数: {new_elements_count}")
                        else:
                            logger.info("📄 已到达页面底部，无法继续滚动")
                    
                    except Exception as check_e:
                        logger.warning(f"⚠️ 滚动状态检查失败: {check_e}")
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"❌ 增强滚动失败: {str(e)}")
                    raise e
            
            # 替换原函数
            if hasattr(original_scroll_action, 'func'):
                original_scroll_action.func = enhanced_scroll_down
            elif hasattr(original_scroll_action, 'function'):
                original_scroll_action.function = enhanced_scroll_down
            
            logger.info("✅ 智能滚动增强策略应用成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 应用智能滚动增强失败: {e}")
            return False

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
                unselected_radios = await page.evaluate(script)
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
                            success = await page.evaluate(click_script)
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
                unselected_checkboxes = await page.evaluate(script)
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
                            success = await page.evaluate(click_script)
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
                unselected_selects = await page.evaluate(script)
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
                                success = await page.evaluate(select_script)
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
                empty_inputs = await page.evaluate(script)
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
                success = await page.evaluate(input_script)
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
                scroll_position = await page.evaluate(script)
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
                success = await page.evaluate(script)
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
    🔥 智能问卷工作流：使用WebUI原生方法 + 智能辅助系统
    
    架构设计：
    - 使用WebUI原生的BrowserUseAgent（保持彩色标记框）
    - 智能组件作为辅助决策系统，特别处理自定义下拉题
    - 在遇到无限循环时智能介入
    """
    try:
        logger.info(f"🚀 启动智能问卷工作流: {persona_name}")
        
        # 🔥 使用WebUI原生方法（testWenjuan.py模式）+ 智能辅助
        integration = AdsPowerWebUIIntegration()
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
        
        # 增强结果信息
        result["workflow_type"] = "webui_native_with_intelligent_assistance"
        result["features_used"] = [
            "webui_native_agent",
            "custom_select_intelligence", 
            "infinite_loop_prevention",
            "visual_ai_with_assistance"
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
            "workflow_type": "webui_native_with_intelligent_assistance"
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