#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebUI问卷作答增强模块
专门解决问卷作答中的滚动不充分、重复作答、题目遗漏等问题
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class QuestionnaireCompletionTracker:
    """问卷完成度追踪器 - 确保100%完成所有题目"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.answered_questions: Set[str] = set()
        self.discovered_questions: Set[str] = set()
        self.page_areas_scanned: List[Dict] = []
        self.scroll_positions: List[int] = []
        self.last_new_question_time = time.time()
        
    def add_discovered_question(self, question_id: str, question_text: str, question_type: str):
        """发现新题目"""
        self.discovered_questions.add(question_id)
        logger.info(f"🔍 发现新题目: {question_type} - {question_text[:50]}...")
        
    def mark_question_answered(self, question_id: str):
        """标记题目已回答"""
        self.answered_questions.add(question_id)
        self.last_new_question_time = time.time()
        logger.info(f"✅ 题目已回答: {question_id}")
        
    def is_question_answered(self, question_id: str) -> bool:
        """检查题目是否已回答"""
        return question_id in self.answered_questions
    
    def get_completion_rate(self) -> float:
        """获取完成率"""
        if not self.discovered_questions:
            return 0.0
        return len(self.answered_questions) / len(self.discovered_questions)
    
    def get_unanswered_questions(self) -> Set[str]:
        """获取未回答的题目"""
        return self.discovered_questions - self.answered_questions
    
    def should_continue_scrolling(self) -> bool:
        """是否应该继续滚动查找更多题目"""
        # 如果最近5秒内没有发现新题目，且完成率未达到100%，继续滚动
        time_since_last_question = time.time() - self.last_new_question_time
        completion_rate = self.get_completion_rate()
        
        if completion_rate < 1.0 and time_since_last_question < 10:
            return True
        
        # 如果发现的题目都已回答，但可能还有更多题目，继续滚动一段时间
        if completion_rate >= 1.0 and time_since_last_question < 5:
            return True
            
        return False

class IntelligentScrollController:
    """智能滚动控制器 - 确保发现所有题目"""
    
    def __init__(self, browser_context, tracker: QuestionnaireCompletionTracker):
        self.browser_context = browser_context
        self.tracker = tracker
        self.scroll_attempts = 0
        self.max_scroll_attempts = 20
        self.last_scroll_height = 0
        self.consecutive_no_new_questions = 0
        
    async def discover_all_questions_with_smart_scroll(self) -> Dict:
        """智能滚动发现所有题目"""
        logger.info("🔍 开始智能滚动发现所有题目...")
        
        try:
            page = await self.browser_context.get_current_page()
            
            # 先从顶部开始扫描
            await self.scroll_to_top()
            await self.scan_current_viewport()
            
            while (self.scroll_attempts < self.max_scroll_attempts and 
                   self.tracker.should_continue_scrolling()):
                
                # 智能滚动策略
                scroll_result = await self.smart_scroll_down()
                
                if not scroll_result['success']:
                    break
                    
                # 扫描新内容
                new_questions = await self.scan_current_viewport()
                
                if new_questions == 0:
                    self.consecutive_no_new_questions += 1
                else:
                    self.consecutive_no_new_questions = 0
                
                # 如果连续3次滚动都没发现新题目，尝试更大幅度滚动
                if self.consecutive_no_new_questions >= 3:
                    logger.info("🔄 尝试大幅度滚动寻找更多内容...")
                    await self.large_scroll_down()
                    await self.scan_current_viewport()
                
                # 检查是否到达页面底部
                if await self.is_at_bottom():
                    logger.info("📍 已到达页面底部")
                    break
                
                await asyncio.sleep(0.5)  # 等待内容加载
            
            completion_stats = {
                'discovered_questions': len(self.tracker.discovered_questions),
                'answered_questions': len(self.tracker.answered_questions),
                'completion_rate': self.tracker.get_completion_rate(),
                'scroll_attempts': self.scroll_attempts,
                'unanswered_count': len(self.tracker.get_unanswered_questions())
            }
            
            logger.info(f"🎯 智能滚动完成: 发现{completion_stats['discovered_questions']}题，完成率{completion_stats['completion_rate']:.1%}")
            
            return {
                'success': True,
                'stats': completion_stats,
                'unanswered_questions': list(self.tracker.get_unanswered_questions())
            }
            
        except Exception as e:
            logger.error(f"❌ 智能滚动发现失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def scroll_to_top(self):
        """滚动到页面顶部"""
        try:
            page = await self.browser_context.get_current_page()
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"⚠️ 滚动到顶部失败: {e}")
    
    async def smart_scroll_down(self) -> Dict:
        """智能向下滚动"""
        try:
            page = await self.browser_context.get_current_page()
            
            # 获取当前页面信息
            page_info = await page.evaluate("""
            () => {
                return {
                    scrollHeight: document.body.scrollHeight,
                    scrollTop: window.pageYOffset,
                    clientHeight: window.innerHeight,
                    hasMoreContent: (window.pageYOffset + window.innerHeight) < document.body.scrollHeight
                };
            }
            """)
            
            if not page_info['hasMoreContent']:
                return {'success': False, 'reason': 'No more content'}
            
            # 智能计算滚动距离
            scroll_distance = min(400, page_info['clientHeight'] // 2)
            
            # 执行滚动
            await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            await asyncio.sleep(0.3)  # 等待滚动动画
            
            self.scroll_attempts += 1
            
            return {
                'success': True,
                'scroll_distance': scroll_distance,
                'new_position': page_info['scrollTop'] + scroll_distance
            }
            
        except Exception as e:
            logger.error(f"❌ 智能滚动失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def large_scroll_down(self):
        """大幅度滚动"""
        try:
            page = await self.browser_context.get_current_page()
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"⚠️ 大幅度滚动失败: {e}")
    
    async def scan_current_viewport(self) -> int:
        """扫描当前视口的问卷元素"""
        try:
            page = await self.browser_context.get_current_page()
            
            # 扫描各种题型的元素
            scan_result = await page.evaluate("""
            () => {
                const questions = [];
                let questionCount = 0;
                
                // 扫描单选题
                const radioGroups = {};
                document.querySelectorAll('input[type="radio"]').forEach((radio, index) => {
                    const name = radio.name || `radio_group_${index}`;
                    if (!radioGroups[name]) {
                        radioGroups[name] = {
                            type: 'radio',
                            name: name,
                            question: radio.closest('label, .question, .form-group')?.textContent?.trim() || '',
                            element: radio
                        };
                        questions.push(radioGroups[name]);
                    }
                });
                
                // 扫描多选题
                document.querySelectorAll('input[type="checkbox"]').forEach((checkbox, index) => {
                    const rect = checkbox.getBoundingClientRect();
                    if (rect.top >= 0 && rect.top <= window.innerHeight) {
                        questions.push({
                            type: 'checkbox',
                            id: `checkbox_${index}`,
                            question: checkbox.closest('label, .question, .form-group')?.textContent?.trim() || '',
                            element: checkbox
                        });
                    }
                });
                
                // 扫描下拉框
                document.querySelectorAll('select').forEach((select, index) => {
                    const rect = select.getBoundingClientRect();
                    if (rect.top >= 0 && rect.top <= window.innerHeight) {
                        questions.push({
                            type: 'select',
                            id: `select_${index}`,
                            question: select.closest('label, .question, .form-group')?.textContent?.trim() || '',
                            element: select
                        });
                    }
                });
                
                // 扫描文本输入框
                document.querySelectorAll('input[type="text"], textarea').forEach((input, index) => {
                    const rect = input.getBoundingClientRect();
                    if (rect.top >= 0 && rect.top <= window.innerHeight) {
                        questions.push({
                            type: 'text',
                            id: `text_${index}`,
                            question: input.closest('label, .question, .form-group')?.textContent?.trim() || '',
                            element: input
                        });
                    }
                });
                
                return {
                    questions: questions.map(q => ({
                        type: q.type,
                        id: q.id || q.name,
                        question: q.question.substring(0, 100)
                    })),
                    totalCount: questions.length
                };
            }
            """)
            
            new_questions_count = 0
            for question in scan_result['questions']:
                question_id = f"{question['type']}_{question['id']}"
                if question_id not in self.tracker.discovered_questions:
                    self.tracker.add_discovered_question(
                        question_id, 
                        question['question'], 
                        question['type']
                    )
                    new_questions_count += 1
            
            return new_questions_count
            
        except Exception as e:
            logger.error(f"❌ 扫描视口失败: {e}")
            return 0
    
    async def is_at_bottom(self) -> bool:
        """检查是否到达页面底部"""
        try:
            page = await self.browser_context.get_current_page()
            result = await page.evaluate("""
            () => {
                return (window.innerHeight + window.pageYOffset) >= document.body.scrollHeight - 100;
            }
            """)
            return result
        except Exception as e:
            logger.warning(f"⚠️ 检查页面底部失败: {e}")
            return False

class SmartAnswerStateDetector:
    """智能答题状态检测器 - 避免重复作答"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        
    async def detect_answered_questions(self) -> Dict:
        """检测已回答的题目"""
        try:
            page = await self.browser_context.get_current_page()
            
            result = await page.evaluate("""
            () => {
                const answeredQuestions = [];
                
                // 检测已选择的单选题
                document.querySelectorAll('input[type="radio"]:checked').forEach((radio, index) => {
                    answeredQuestions.push({
                        type: 'radio',
                        name: radio.name,
                        value: radio.value,
                        status: 'answered'
                    });
                });
                
                // 检测已选择的多选题
                document.querySelectorAll('input[type="checkbox"]:checked').forEach((checkbox, index) => {
                    answeredQuestions.push({
                        type: 'checkbox',
                        id: `checkbox_${index}`,
                        value: checkbox.value,
                        status: 'answered'
                    });
                });
                
                // 检测已选择的下拉框
                document.querySelectorAll('select').forEach((select, index) => {
                    if (select.value && select.value !== '' && select.selectedIndex > 0) {
                        answeredQuestions.push({
                            type: 'select',
                            id: `select_${index}`,
                            value: select.value,
                            status: 'answered'
                        });
                    }
                });
                
                // 检测已填写的文本框
                document.querySelectorAll('input[type="text"], textarea').forEach((input, index) => {
                    if (input.value && input.value.trim() !== '') {
                        answeredQuestions.push({
                            type: 'text',
                            id: `text_${index}`,
                            value: input.value.substring(0, 50),
                            status: 'answered'
                        });
                    }
                });
                
                return {
                    answeredQuestions: answeredQuestions,
                    totalAnswered: answeredQuestions.length
                };
            }
            """)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 检测答题状态失败: {e}")
            return {'answeredQuestions': [], 'totalAnswered': 0}

class SubmitButtonDetector:
    """提交按钮检测器 - 智能寻找提交按钮"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        
    async def find_submit_button(self) -> Optional[Dict]:
        """智能寻找提交按钮"""
        try:
            page = await self.browser_context.get_current_page()
            
            result = await page.evaluate("""
            () => {
                // 各种提交按钮的选择器
                const submitSelectors = [
                    'input[type="submit"]',
                    'button[type="submit"]',
                    'button:contains("提交")',
                    'button:contains("完成")',
                    'button:contains("下一页")',
                    'button:contains("继续")',
                    'a:contains("提交")',
                    '.submit-btn',
                    '.next-btn',
                    '.continue-btn'
                ];
                
                for (let selector of submitSelectors) {
                    try {
                        let elements;
                        if (selector.includes(':contains')) {
                            // 处理包含文本的选择器
                            const tag = selector.split(':')[0];
                            const text = selector.match(/\\("([^"]+)"\\)/)[1];
                            elements = Array.from(document.querySelectorAll(tag)).filter(
                                el => el.textContent.includes(text)
                            );
                        } else {
                            elements = Array.from(document.querySelectorAll(selector));
                        }
                        
                        for (let element of elements) {
                            const rect = element.getBoundingClientRect();
                            const isVisible = rect.width > 0 && rect.height > 0 && 
                                            getComputedStyle(element).visibility !== 'hidden';
                            
                            if (isVisible) {
                                return {
                                    found: true,
                                    selector: selector,
                                    text: element.textContent.trim(),
                                    tagName: element.tagName,
                                    position: {
                                        x: rect.left + rect.width / 2,
                                        y: rect.top + rect.height / 2
                                    }
                                };
                            }
                        }
                    } catch (e) {
                        continue;
                    }
                }
                
                return { found: false };
            }
            """)
            
            return result if result.get('found') else None
            
        except Exception as e:
            logger.error(f"❌ 寻找提交按钮失败: {e}")
            return None

# 导出类
__all__ = [
    'QuestionnaireCompletionTracker',
    'IntelligentScrollController', 
    'SmartAnswerStateDetector',
    'SubmitButtonDetector'
] 