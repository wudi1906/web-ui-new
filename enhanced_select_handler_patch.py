#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强下拉框处理补丁
解决自定义UI组件下拉框（如问卷星样式）的作答问题
"""

# 这个补丁文件包含了修复自定义下拉框问题的所有代码
print("🔽 增强下拉框处理补丁已准备好")

ENHANCED_SELECT_ANALYZER_PATCH = '''
    async def analyze_questionnaire_structure(self) -> Dict:
        """分析问卷结构，识别所有题目类型和位置（增强版 - 支持自定义下拉框）"""
        try:
            structure_analysis_js = """
            (function() {
                const analysis = {
                    radio_questions: [],
                    checkbox_questions: [],
                    select_questions: [],
                    custom_select_questions: [],  // 新增：自定义下拉框
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
                
                // 🔥 新增：分析自定义下拉框（问卷星、腾讯问卷等）
                const customSelectSelectors = [
                    // 问卷星样式
                    '.jqselect',
                    '.jqselect-wrapper', 
                    '.select-wrapper',
                    '.dropdown-wrapper',
                    // 其他常见自定义下拉框
                    '[class*="select"]',
                    '[class*="dropdown"]',
                    '.ui-select',
                    '.custom-select'
                ];
                
                customSelectSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach((customSelect, index) => {
                        // 检查是否已经处理过
                        if (customSelect.hasAttribute('data-analyzed')) return;
                        customSelect.setAttribute('data-analyzed', 'true');
                        
                        // 查找触发元素（点击展开的部分）
                        const trigger = customSelect.querySelector('.jqselect-text, .select-text, .dropdown-trigger, .selected-value') || 
                                       customSelect.querySelector('[class*="text"], [class*="display"], [class*="current"]') ||
                                       customSelect;
                                       
                        // 查找选项容器
                        const optionsContainer = customSelect.querySelector('.jqselect-options, .select-options, .dropdown-options, .options-list') ||
                                               document.querySelector(`[data-for="${customSelect.id}"]`) ||
                                               customSelect.nextElementSibling;
                        
                        // 获取题目文本
                        const questionContainer = customSelect.closest('.question') || 
                                                customSelect.closest('.form-group') || 
                                                customSelect.closest('tr') || 
                                                customSelect.closest('div');
                        
                        let questionText = '';
                        if (questionContainer) {
                            // 查找题目标题（通常在下拉框前面）
                            const questionElements = questionContainer.querySelectorAll('label, .question-text, .q-text, .title, h3, h4, strong');
                            for (let elem of questionElements) {
                                const text = elem.textContent.trim();
                                if (text && text.length > questionText.length && !text.includes('请选择')) {
                                    questionText = text;
                                }
                            }
                            
                            // 如果没找到，使用前面的文本节点
                            if (!questionText) {
                                const walker = document.createTreeWalker(
                                    questionContainer,
                                    NodeFilter.SHOW_TEXT,
                                    null,
                                    false
                                );
                                let node;
                                while (node = walker.nextNode()) {
                                    const text = node.textContent.trim();
                                    if (text && text.length > 5 && !text.includes('请选择')) {
                                        questionText = text;
                                        break;
                                    }
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
                        
                        // 尝试获取选项（如果容器可见或可查找到）
                        let options = [];
                        if (optionsContainer) {
                            const optionElements = optionsContainer.querySelectorAll('li, .option, .item, [data-value]');
                            options = Array.from(optionElements).map((opt, idx) => ({
                                element: opt,
                                value: opt.getAttribute('data-value') || opt.textContent.trim() || `option_${idx}`,
                                text: opt.textContent.trim(),
                                index: idx
                            })).filter(opt => opt.text && opt.text !== '');
                        }
                        
                        // 如果找不到选项，尝试通过点击获取
                        if (options.length === 0) {
                            // 标记为需要动态获取选项
                            options = 'dynamic'; 
                        }
                        
                        analysis.custom_select_questions.push({
                            name: customSelect.id || customSelect.className || `custom_select_${index}`,
                            question_text: questionText || `自定义下拉题${index + 1}`,
                            is_answered: isAnswered,
                            current_value: currentText,
                            trigger_element: trigger,
                            options_container: optionsContainer,
                            options: options,
                            element_type: 'custom_select',
                            selector_info: {
                                trigger_selector: trigger.tagName.toLowerCase() + (trigger.className ? '.' + trigger.className.split(' ').join('.') : ''),
                                container_selector: customSelect.tagName.toLowerCase() + (customSelect.className ? '.' + customSelect.className.split(' ').join('.') : '')
                            }
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
                                         analysis.text_questions.length;
                
                return analysis;
            })();
            """
            
            structure = await self.browser_context.evaluate(structure_analysis_js)
            self.logger.info(f"📊 问卷结构分析完成: {structure['total_questions']}题 (单选:{len(structure['radio_questions'])}, 多选:{len(structure['checkbox_questions'])}, 原生下拉:{len(structure['select_questions'])}, 自定义下拉:{len(structure['custom_select_questions'])}, 文本:{len(structure['text_questions'])})")
            
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
'''

ENHANCED_RAPID_ANSWER_ENGINE_PATCH = '''
    async def rapid_answer_visible_area(self, persona_info: Dict, questionnaire_structure: Dict) -> Dict:
        """快速作答当前可见区域的所有未答题目（增强版 - 支持自定义下拉框）"""
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
                    
                await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # 🔥 4. 处理自定义下拉题（新增）
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
                    else:
                        error_count += 1
                except Exception as e:
                    self.logger.warning(f"⚠️ 自定义下拉题作答失败: {e}")
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
                    
                await asyncio.sleep(random.uniform(0.5, 1.0))
            
            self.logger.info(f"📝 批量作答完成: 新答{answered_count}题, 跳过{skipped_count}题, 失败{error_count}题")
            
            return {
                "success": True,
                "answered_count": answered_count,
                "skipped_count": skipped_count,
                "error_count": error_count,
                "total_processed": answered_count + skipped_count + error_count
            }
            
        except Exception as e:
            self.logger.error(f"❌ 批量作答失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "answered_count": answered_count,
                "skipped_count": skipped_count,
                "error_count": error_count
            }
'''

ENHANCED_CUSTOM_SELECT_METHOD = '''
    async def _answer_custom_select_question(self, custom_select: Dict, persona_info: Dict) -> Dict:
        """作答自定义下拉题（问卷星、腾讯问卷等样式）"""
        try:
            question_text = custom_select.get("question_text", "")
            current_value = custom_select.get("current_value", "")
            options = custom_select.get("options", [])
            
            self.logger.info(f"🔽 处理自定义下拉题: {question_text[:30]}...")
            
            # 如果需要动态获取选项，先点击展开
            if options == 'dynamic' or len(options) == 0:
                options = await self._get_dynamic_select_options(custom_select)
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
                self.logger.info(f"✅ 自定义下拉题作答成功: {selected_option['text']}")
                return {"success": True, "selected": selected_option["text"]}
            else:
                return {"success": False, "error": "点击选项失败"}
            
        except Exception as e:
            self.logger.error(f"❌ 自定义下拉题作答异常: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_dynamic_select_options(self, custom_select: Dict) -> List[Dict]:
        """动态获取自定义下拉框的选项"""
        try:
            # 获取触发元素的选择器信息
            container_selector = custom_select.get("selector_info", {}).get("container_selector", "")
            
            # 通过JavaScript获取选项
            get_options_js = f"""
            (function() {{
                // 尝试多种方式查找和点击触发元素
                const selectors = [
                    '{container_selector}',
                    '.jqselect',
                    '.jqselect-wrapper',
                    '.select-wrapper',
                    '[class*="select"]'
                ];
                
                let triggerElement = null;
                let optionsContainer = null;
                
                // 查找触发元素
                for (let selector of selectors) {{
                    const elements = document.querySelectorAll(selector);
                    for (let element of elements) {{
                        if (element.offsetHeight > 0 && element.offsetWidth > 0) {{
                            const trigger = element.querySelector('.jqselect-text, .select-text, .dropdown-trigger, .selected-value') || element;
                            if (trigger) {{
                                triggerElement = trigger;
                                break;
                            }}
                        }}
                    }}
                    if (triggerElement) break;
                }}
                
                if (!triggerElement) {{
                    return {{ success: false, error: "找不到触发元素" }};
                }}
                
                // 点击展开下拉框
                triggerElement.click();
                
                // 等待选项出现
                setTimeout(() => {{
                    // 查找选项容器
                    const optionSelectors = [
                        '.jqselect-options',
                        '.select-options', 
                        '.dropdown-options',
                        '.options-list',
                        '.dropdown-menu'
                    ];
                    
                    for (let selector of optionSelectors) {{
                        const container = document.querySelector(selector);
                        if (container && container.offsetHeight > 0) {{
                            optionsContainer = container;
                            break;
                        }}
                    }}
                    
                    if (!optionsContainer) {{
                        // 尝试查找在DOM中新出现的选项元素
                        const allOptions = document.querySelectorAll('li[data-value], .option[data-value], .item[data-value]');
                        const visibleOptions = Array.from(allOptions).filter(opt => opt.offsetHeight > 0 && opt.offsetWidth > 0);
                        if (visibleOptions.length > 0) {{
                            optionsContainer = visibleOptions[0].parentElement;
                        }}
                    }}
                }}, 200);
                
                return {{ success: true, triggered: true }};
            }})();
            """
            
            # 先触发展开
            trigger_result = await self.browser_context.evaluate(get_options_js)
            if not trigger_result.get("success"):
                return []
            
            # 等待选项加载
            await asyncio.sleep(0.5)
            
            # 获取选项列表
            get_options_list_js = """
            (function() {
                const options = [];
                const optionSelectors = [
                    '.jqselect-options li',
                    '.select-options li',
                    '.dropdown-options li',
                    '.options-list li',
                    '.dropdown-menu li',
                    'li[data-value]',
                    '.option',
                    '.item'
                ];
                
                for (let selector of optionSelectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        elements.forEach((element, index) => {
                            const text = element.textContent.trim();
                            const value = element.getAttribute('data-value') || text || `option_${index}`;
                            if (text && text !== '请选择' && !text.includes('选择')) {
                                options.push({
                                    text: text,
                                    value: value,
                                    index: index,
                                    element: element
                                });
                            }
                        });
                        break; // 找到一组选项就停止
                    }
                }
                
                return options;
            })();
            """
            
            options = await self.browser_context.evaluate(get_options_list_js)
            self.logger.info(f"🔍 动态获取到 {len(options)} 个选项")
            
            return options if isinstance(options, list) else []
            
        except Exception as e:
            self.logger.error(f"❌ 动态获取选项失败: {e}")
            return []
    
    async def _click_custom_select_option(self, custom_select: Dict, selected_option: Dict) -> bool:
        """点击自定义下拉框选项"""
        try:
            option_text = selected_option["text"]
            option_value = selected_option.get("value", option_text)
            
            # 通过JavaScript执行点击
            click_option_js = f"""
            (function() {{
                // 先确保下拉框是展开状态
                const triggerSelectors = [
                    '.jqselect-text',
                    '.select-text',
                    '.dropdown-trigger',
                    '.selected-value',
                    '.jqselect'
                ];
                
                let triggered = false;
                for (let selector of triggerSelectors) {{
                    const triggers = document.querySelectorAll(selector);
                    for (let trigger of triggers) {{
                        if (trigger.offsetHeight > 0 && trigger.offsetWidth > 0) {{
                            trigger.click();
                            triggered = true;
                            break;
                        }}
                    }}
                    if (triggered) break;
                }}
                
                // 等待一下然后查找并点击选项
                setTimeout(() => {{
                    const optionSelectors = [
                        '.jqselect-options li',
                        '.select-options li', 
                        '.dropdown-options li',
                        '.options-list li',
                        'li[data-value]',
                        '.option'
                    ];
                    
                    let found = false;
                    for (let selector of optionSelectors) {{
                        const options = document.querySelectorAll(selector);
                        for (let option of options) {{
                            const text = option.textContent.trim();
                            const value = option.getAttribute('data-value') || text;
                            
                            if (text === "{option_text}" || value === "{option_value}") {{
                                option.click();
                                found = true;
                                
                                // 触发change事件
                                option.dispatchEvent(new Event('click', {{ bubbles: true }}));
                                option.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                
                                console.log('✅ 成功点击选项:', text);
                                break;
                            }}
                        }}
                        if (found) break;
                    }}
                    
                    if (!found) {{
                        console.log('❌ 未找到匹配的选项:', "{option_text}");
                    }}
                }}, 300);
                
                return {{ triggered: triggered }};
            }})();
            """
            
            result = await self.browser_context.evaluate(click_option_js)
            
            # 等待选择完成
            await asyncio.sleep(0.8)
            
            # 验证选择是否成功
            verify_js = f"""
            (function() {{
                const triggers = document.querySelectorAll('.jqselect-text, .select-text, .dropdown-trigger, .selected-value');
                for (let trigger of triggers) {{
                    const text = trigger.textContent.trim();
                    if (text === "{option_text}" || text.includes("{option_text}")) {{
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
                return False
            
        except Exception as e:
            self.logger.error(f"❌ 点击自定义选项失败: {e}")
            return False
'''

if __name__ == "__main__":
    print("🔽 增强下拉框处理补丁已准备好")
    print("需要应用以下修改:")
    print("1. 替换 IntelligentQuestionnaireAnalyzer.analyze_questionnaire_structure 方法")
    print("2. 替换 RapidAnswerEngine.rapid_answer_visible_area 方法") 
    print("3. 添加 RapidAnswerEngine._answer_custom_select_question 等新方法") 