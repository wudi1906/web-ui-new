#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🎯 WebUI问卷集成系统
直接调用WebUI的核心执行接口，跳过Gradio界面
保持WebUI原生BrowserUseAgent能力 + 增强问卷提示词
"""

import asyncio
import logging
import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

# WebUI核心组件
from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.browser.custom_browser import CustomBrowser
from src.controller.custom_controller import CustomController
from src.utils import llm_provider
from src.webui.webui_manager import WebuiManager

# Browser-use核心组件
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.agent.views import AgentHistoryList, AgentOutput
from browser_use.browser.views import BrowserState

# LangChain
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

class WebUIQuestionnaireRunner:
    """
    🔥 WebUI问卷执行器
    
    直接调用WebUI核心接口，保持：
    - ✅ WebUI原生BrowserUseAgent执行能力
    - ✅ 彩色标记框和视觉AI
    - ✅ 截图和经验总结功能
    - ✅ 增强问卷提示词
    """
    
    def __init__(self):
        self.webui_manager = None
        self.task_id = None
        self.action_history = []
        
    async def run_questionnaire_with_webui_core(
        self,
        questionnaire_url: str,
        digital_human_info: Dict[str, Any],
        gemini_api_key: str,
        model_name: str = "gemini-2.0-flash",
        max_steps: int = 200,
        keep_browser_open: bool = False
    ) -> Dict[str, Any]:
        """
        🚀 使用WebUI核心执行问卷作答
        
        直接调用WebUI的BrowserUseAgent，跳过Gradio界面
        """
        try:
            logger.info(f"🎯 启动WebUI核心问卷执行: {questionnaire_url}")
            
            # 1. 生成增强问卷提示词
            enhanced_prompt = self._generate_questionnaire_prompt(
                digital_human_info, questionnaire_url
            )
            logger.info(f"✅ 已生成增强问卷提示词")
            
            # 2. 初始化WebUI管理器
            await self._initialize_webui_manager()
            
            # 3. 初始化LLM
            llm = await self._initialize_llm(
                api_key=gemini_api_key,
                model_name=model_name
            )
            if not llm:
                raise ValueError("LLM初始化失败")
            
            # 4. 初始化浏览器
            await self._initialize_browser(keep_browser_open)
            
            # 5. 创建WebUI原生BrowserUseAgent
            agent = await self._create_webui_agent(
                task=enhanced_prompt,
                llm=llm,
                max_steps=max_steps
            )
            
            # 6. 导航到问卷URL
            await self.webui_manager.bu_browser_context.create_new_tab()
            await self.webui_manager.bu_browser_context.navigate_to(questionnaire_url)
            logger.info(f"✅ 已导航到问卷URL: {questionnaire_url}")
            
            # 7. 执行WebUI原生agent任务
            logger.info("🚀 开始执行WebUI原生BrowserUseAgent任务...")
            history = await agent.run(max_steps=max_steps)
            
            # 8. 处理执行结果
            result = await self._process_execution_result(history)
            
            # 9. 清理资源
            if not keep_browser_open:
                await self._cleanup_resources()
            
            logger.info("✅ 问卷执行完成")
            return result
            
        except Exception as e:
            logger.error(f"❌ 问卷执行失败: {e}")
            await self._cleanup_resources()
            raise
    
    async def _initialize_webui_manager(self):
        """初始化WebUI管理器"""
        try:
            self.webui_manager = WebuiManager()
            self.task_id = f"questionnaire_{int(datetime.now().timestamp())}"
            self.webui_manager.bu_agent_task_id = self.task_id
            self.webui_manager.bu_chat_history = []
            logger.info("✅ WebUI管理器初始化成功")
            
        except Exception as e:
            logger.error(f"❌ WebUI管理器初始化失败: {e}")
            raise
    
    async def _initialize_llm(
        self,
        api_key: str,
        model_name: str = "gemini-2.0-flash",
        temperature: float = 0.6
    ) -> BaseChatModel:
        """初始化LLM - 使用WebUI的方式"""
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                api_key=api_key,
            )
            logger.info(f"✅ LLM初始化成功: {model_name}")
            return llm
            
        except Exception as e:
            logger.error(f"❌ LLM初始化失败: {e}")
            raise
    
    async def _initialize_browser(self, keep_browser_open: bool = False):
        """初始化浏览器 - 使用WebUI的方式"""
        try:
            # 清理现有浏览器（如果不保持打开）
            if not keep_browser_open:
                if self.webui_manager.bu_browser_context:
                    await self.webui_manager.bu_browser_context.close()
                    self.webui_manager.bu_browser_context = None
                if self.webui_manager.bu_browser:
                    await self.webui_manager.bu_browser.close()
                    self.webui_manager.bu_browser = None
            
            # 创建新浏览器
            if not self.webui_manager.bu_browser:
                browser_config = BrowserConfig(
                    headless=False,  # 显示浏览器，便于观察
                    disable_security=True,
                    browser_binary_path=None,
                    new_context_config=BrowserContextConfig(
                        window_width=1280,
                        window_height=800,
                    )
                )
                
                self.webui_manager.bu_browser = CustomBrowser(config=browser_config)
                logger.info("✅ 浏览器初始化成功")
            
            # 创建浏览器上下文
            if not self.webui_manager.bu_browser_context:
                context_config = BrowserContextConfig(
                    window_width=1280,
                    window_height=800,
                )
                self.webui_manager.bu_browser_context = await self.webui_manager.bu_browser.new_context(
                    config=context_config
                )
                logger.info("✅ 浏览器上下文创建成功")
                
        except Exception as e:
            logger.error(f"❌ 浏览器初始化失败: {e}")
            raise
    
    async def _create_webui_agent(
        self,
        task: str,
        llm: BaseChatModel,
        max_steps: int = 200
    ) -> BrowserUseAgent:
        """创建WebUI原生BrowserUseAgent"""
        try:
            # 初始化控制器
            if not self.webui_manager.bu_controller:
                self.webui_manager.bu_controller = CustomController()
            
            # 步骤回调函数
            async def step_callback(state: BrowserState, output: AgentOutput, step_num: int):
                logger.info(f"📸 Step {step_num} 完成")
                # 记录操作历史
                self.action_history.append({
                    'step': step_num,
                    'url': state.url if hasattr(state, 'url') else '',
                    'title': state.title if hasattr(state, 'title') else '',
                    'timestamp': datetime.now().isoformat()
                })
                # 这里可以添加截图保存等功能
            
            # 完成回调函数
            def done_callback(history: AgentHistoryList):
                logger.info("🏁 任务执行完成")
            
            # 创建WebUI原生BrowserUseAgent
            agent = BrowserUseAgent(
                task=task,
                llm=llm,
                browser=self.webui_manager.bu_browser,
                browser_context=self.webui_manager.bu_browser_context,
                controller=self.webui_manager.bu_controller,
                register_new_step_callback=step_callback,
                register_done_callback=done_callback,
                use_vision=True,  # 启用视觉功能（彩色标记框）
                max_actions_per_step=15,  # 每步最大操作数
                tool_calling_method='auto',
                extend_system_message=self._get_webui_extend_prompt(),
                source="questionnaire_webui"
            )
            
            agent.state.agent_id = self.task_id
            self.webui_manager.bu_agent = agent
            
            logger.info("✅ WebUI原生BrowserUseAgent创建成功")
            return agent
            
        except Exception as e:
            logger.error(f"❌ BrowserUseAgent创建失败: {e}")
            raise
    
    def _generate_questionnaire_prompt(
        self,
        digital_human_info: Dict[str, Any],
        questionnaire_url: str
    ) -> str:
        """生成增强问卷提示词"""
        try:
            # 提取人物信息
            name = digital_human_info.get('name', '张三')
            age = digital_human_info.get('age', 30)
            gender = digital_human_info.get('gender', '男')
            occupation = digital_human_info.get('occupation', '上班族')
            income = digital_human_info.get('income', 8000)
            
            # 网站特定策略
            site_strategy = self._get_site_strategy(questionnaire_url)
            
            prompt = f"""
你是 {name}，{age}岁{gender}性，职业是{occupation}，月收入约{income}元。

目标：完成问卷调查 {questionnaire_url}

【🎯 核心执行流程 - 防重复作答策略】

## 第一步：状态扫描检查（每次进入新区域必做）
在任何操作前，先仔细观察当前屏幕：
1. 扫描所有可见题目，识别每题的答题状态
2. 单选题：检查是否有圆点/勾选标记
3. 多选题：检查复选框是否已勾选
4. 下拉框：检查是否显示具体选项（而非"请选择"）
5. 填空题：检查输入框是否已有文字内容
6. 制定答题计划：未答题目→需要操作，已答题目→立即跳过

## 第二步：精准操作执行
**对于未答题目**：
- 单选题：选择一个符合{name}身份的选项，点击一次
- 多选题：选择2-3个相关选项，每个只点击一次  
- 下拉框：点击下拉区域 → 等待选项出现 → 点击合适选项
- 填空题：点击输入框 → 输入简短内容（20-30字）

**对于已答题目**：
- 发现任何已经选择/填写的题目，立即跳过，绝不再操作
- 不要点击已选中的选项，这会取消选择

## 第三步：滚动寻找策略
每完成当前屏幕所有未答题目后：
1. 向下滚动300-500像素查找更多题目
2. 在新区域重复第一步和第二步
3. 如果滚动后没有新题目，寻找"下一页"/"提交"按钮

## 第四步：导航操作
- 优先寻找"下一题"、"下一页"、"继续"按钮
- 确认当前页面所有题目完成后才点击
- 最后页面寻找"提交"、"完成"按钮

## 第五步：提交后检查（关键新增）
**点击提交后必须检查是否有错误提示**：
1. 等待3秒观察页面反应
2. 查找红色错误提示、弹窗、警告信息
3. 常见错误提示：
   - "请完成必填项"
   - "第X题为必填项"
   - "题目未做答"
   - 红色标记的题目号

**如果发现错误提示**：
1. 不要慌张，这是正常的补救机会
2. 根据错误提示定位到具体未答题目
3. 滚动页面找到对应题目位置
4. 检查该题状态：如果确实未答，立即补答
5. 再次尝试提交，重复直到成功

**判断真正完成的标志**：
- 看到"提交成功"、"问卷完成"、"谢谢参与"
- 页面跳转到感谢页面
- 没有任何红色错误提示

【🛡️ 防重复死循环机制】

## 智能重试规则
- 连续3次在同一个元素上失败 → 跳过该元素，处理下一个
- 连续5次"Element not exist"错误 → 滚动页面，重新扫描
- 在同一屏幕停留超过10次操作 → 强制滚动到下一区域

## 填空题特殊处理
1. 点击输入框确保获得焦点
2. 如果input_text失败，等待2秒重试
3. 再次失败则跳过该题，继续其他题目
4. 内容示例："{name}认为这个很好，希望可以改进XXX方面"

## 下拉框特殊处理（重点）
针对自定义下拉框的无限循环问题：
1. 首次点击：点击下拉框触发区域
2. 等待1-2秒让选项列表出现
3. 点击具体选项文字
4. 如果失败，尝试点击选项的不同位置
5. 如果仍失败，尝试键盘操作：Tab键导航+Enter确认
6. 连续3次失败则跳过该题

【⚡ 网站特定策略】
{site_strategy}

【🚨 关键原则】
1. **零重复原则**：已答题目绝对不再操作
2. **100%完整原则**：所有题目都必须尝试作答
3. **智能补救原则**：提交失败时必须根据错误提示补答
4. **耐心持续原则**：遇到困难不轻易放弃，尝试多种方法
5. **状态优先原则**：操作前必先检查状态，制定策略

记住：你是{name}，要保持角色特征一致性，理性务实地回答问题。

现在开始执行问卷作答，严格按照上述流程操作！
"""
            
            return prompt.strip()
            
        except Exception as e:
            logger.error(f"❌ 提示词生成失败: {e}")
            return f"请完成问卷调查：{questionnaire_url}"
    
    def _get_site_strategy(self, url: str) -> str:
        """获取网站特定策略"""
        try:
            if 'wjx.cn' in url:
                return """
**问卷星特殊处理策略**：
- 下拉框多为自定义组件，点击后需等待选项列表展开
- 必填项有红色星号(*)标记，提交时会有红色错误提示
- 常见的下拉框触发元素：span.select2-selection__rendered
- 下拉选项通常在ul.select2-results__options中
- 提交按钮通常是input[type=submit]或button标签
- 错误提示通常是红色文字，包含具体题目信息
- 页面滚动后元素索引会改变，需要重新扫描
"""
            elif 'jinshengsurveys.com' in url:
                return """
**金盛调研特殊处理策略**：
- 大量使用div模拟下拉框，需要特殊识别
- JS动态加载内容较多，需要更长等待时间
- 提交验证较严格，必须完成所有必填项
"""
            elif 'sojump.com' in url:
                return """
**问卷网特殊处理策略**：
- 界面相对简洁，多数为标准HTML元素
- 下拉框多为原生select元素
- 验证机制相对宽松
"""
            else:
                return """
**通用问卷策略**：
- 优先尝试标准HTML操作
- 观察页面布局和元素特征
- 适应性处理各种自定义组件
"""
        except:
            return "采用通用问卷作答策略"
    
    def _get_webui_extend_prompt(self) -> str:
        """获取WebUI扩展提示词"""
        return """
🔧 **WebUI增强执行指令**：

## 📋 操作前检查清单（每次action前必做）
1. **状态检查**：观察页面当前状态，识别已答/未答题目
2. **计划制定**：只对未答题目进行操作，已答题目跳过
3. **防重复**：绝不对已选中的选项再次点击

## 🎯 精确元素操作策略
- **视觉AI定位**：使用彩色标记框准确识别页面元素
- **智能等待**：操作前确保元素完全加载和可交互
- **多重备选**：一种方法失败时立即尝试替代方案

## 🔄 循环防护机制
- **重复检测**：连续3次相同操作失败→跳过该元素
- **区域切换**：同一屏幕操作超过10次→强制滚动
- **智能滚动**：遇到"Element not exist"→滚动页面重新扫描

## 📝 填空题处理升级
- **焦点确认**：点击输入框后等待光标出现
- **内容检查**：输入前检查是否已有内容，有则跳过
- **失败处理**：input_text失败时等待2秒重试，再失败则跳过

## 📦 下拉框处理升级（重点）
- **类型识别**：区分原生select和自定义div下拉框
- **步骤执行**：点击触发→等待展开→点击选项→验证选择
- **循环终止**：检测到无限循环时立即切换策略
- **键盘备选**：点击失败时使用Tab+Enter键导航

## ✅ 提交验证强化（关键新增）
**提交按钮点击后的必做步骤**：
1. **等待反应**：点击提交后等待3-5秒观察页面
2. **错误扫描**：检查是否出现红色提示、弹窗、警告
3. **文本识别**：寻找"必填项"、"未做答"、"第X题"等关键词
4. **状态判断**：
   - 有错误提示→执行补救流程
   - 页面跳转/显示感谢→真正完成
   - 无明显变化→再次检查页面状态

**补救执行流程**：
1. **定位问题**：根据错误提示找到具体题目位置
2. **滚动定位**：滚动到指定题目区域
3. **状态再检**：确认该题确实未答
4. **精准补答**：按照题型策略快速补答
5. **重新提交**：补答完成后再次点击提交
6. **循环验证**：重复此流程直到真正成功

**判断真正完成的标准（重要）**：
✅ **确认完成的条件**：
- 页面URL发生跳转到感谢页面
- 出现明确完成文字："提交成功"、"问卷完成"、"谢谢参与"、"感谢您的参与"
- 页面结构完全改变（从问卷页面变为结果页面）
- 连续3次提交均无任何错误提示且页面稳定

❌ **不能判断为完成的情况**：
- 仍在原问卷页面且未出现感谢信息
- 存在任何红色错误提示或警告
- 页面中仍有未答题目标记（红色星号*、空白选项等）
- 提交按钮仍然可见且可点击但页面无变化
- 出现"请检查"、"请完善"、"有必填项"等提示

**错误补救机制强化**：
1. **红色提示处理**：发现任何红色文字立即定位相关题目
2. **空白检测**：扫描页面所有表单元素，确保无空白必填项
3. **循环补答**：对每个错误提示的题目进行针对性补答
4. **多轮验证**：最多进行5轮补答-提交循环，确保彻底完成

## 🧠 记忆与追踪
- **截图记录**：关键步骤自动截图便于错误诊断
- **进度追踪**：实时记录已答题目数量和位置
- **状态缓存**：记住页面滚动位置和已答题目状态

## ⚡ 执行效率优化
- **批量处理**：识别当前屏幕所有未答题目，批量操作
- **智能跳过**：快速识别并跳过已答题目
- **路径优化**：优先处理简单题型，复杂题型留后处理

## 🚨 终止条件识别（核心增强）
**真正完成的确认标志**：
- 页面URL发生跳转（通常跳转到感谢页面）
- 出现明确的完成文字："提交成功"、"问卷完成"、"谢谢参与"
- 页面结构完全改变（从问卷页面变为结果页面）
- 连续多次提交均无错误提示且页面显示感谢信息

**必须继续执行的标志**：
- 仍在原问卷页面
- 存在红色错误提示
- 页面有未答题目标记（红色*、空白选项等）
- 提交按钮仍然可见但页面无明显完成信息
- 出现任何形式的"请完善"、"未填写"提示

🎯 **执行原则**：状态优先，防重复，强补救，确保100%完整答题！只有明确的完成标志才能判断为真正完成！
"""
    
    async def _process_execution_result(self, history: AgentHistoryList) -> Dict[str, Any]:
        """处理执行结果"""
        try:
            result = {
                'success': True,
                'task_id': self.task_id,
                'total_steps': len(history.history) if history else 0,
                'action_history': self.action_history,
                'completion_time': datetime.now().isoformat(),
                'final_status': 'completed'
            }
            
            # 检查是否成功完成
            if history and history.history:
                last_step = history.history[-1]
                if hasattr(last_step, 'result') and last_step.result:
                    for action_result in last_step.result:
                        if hasattr(action_result, 'error') and action_result.error:
                            result['success'] = False
                            result['final_status'] = 'error'
                            result['error'] = action_result.error
                            break
            
            logger.info(f"📊 执行结果: {result['final_status']}, 总步数: {result['total_steps']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 结果处理失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'task_id': self.task_id,
                'completion_time': datetime.now().isoformat()
            }
    
    async def _cleanup_resources(self):
        """清理资源"""
        try:
            if self.webui_manager:
                if self.webui_manager.bu_browser_context:
                    await self.webui_manager.bu_browser_context.close()
                    self.webui_manager.bu_browser_context = None
                if self.webui_manager.bu_browser:
                    await self.webui_manager.bu_browser.close()
                    self.webui_manager.bu_browser = None
                self.webui_manager.bu_agent = None
            logger.info("✅ 资源清理完成")
            
        except Exception as e:
            logger.error(f"❌ 资源清理失败: {e}")

# 便捷调用函数
async def run_questionnaire_with_webui(
    questionnaire_url: str,
    digital_human_info: Dict[str, Any],
    gemini_api_key: str = "AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8",
    model_name: str = "gemini-2.0-flash",
    max_steps: int = 200,
    keep_browser_open: bool = False
) -> Dict[str, Any]:
    """
    🚀 便捷函数：使用WebUI核心运行问卷
    
    直接调用WebUI的BrowserUseAgent，保持原生能力
    """
    runner = WebUIQuestionnaireRunner()
    return await runner.run_questionnaire_with_webui_core(
        questionnaire_url=questionnaire_url,
        digital_human_info=digital_human_info,
        gemini_api_key=gemini_api_key,
        model_name=model_name,
        max_steps=max_steps,
        keep_browser_open=keep_browser_open
    )

# 与现有系统集成的函数
async def run_webui_questionnaire_workflow(
    persona_id: int,
    persona_name: str,
    digital_human_info: Dict,
    questionnaire_url: str,
    gemini_api_key: str = "AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8",
    model_name: str = "gemini-2.0-flash"
) -> Dict:
    """
    🔥 与现有系统集成的WebUI问卷工作流
    
    替代原来的智能组件系统，直接使用WebUI原生能力
    """
    try:
        logger.info(f"🚀 启动WebUI问卷工作流: {persona_name}")
        
        # 运行WebUI核心问卷系统
        result = await run_questionnaire_with_webui(
            questionnaire_url=questionnaire_url,
            digital_human_info=digital_human_info,
            gemini_api_key=gemini_api_key,
            model_name=model_name,
            max_steps=200,
            keep_browser_open=False
        )
        
        # 格式化返回结果以兼容现有系统
        return {
            'success': result.get('success', False),
            'persona_id': persona_id,
            'persona_name': persona_name,
            'questionnaire_url': questionnaire_url,
            'execution_result': result,
            'total_steps': result.get('total_steps', 0),
            'completion_time': result.get('completion_time'),
            'method': 'webui_native'
        }
        
    except Exception as e:
        logger.error(f"❌ WebUI问卷工作流失败: {e}")
        return {
            'success': False,
            'persona_id': persona_id,
            'persona_name': persona_name,
            'questionnaire_url': questionnaire_url,
            'error': str(e),
            'method': 'webui_native'
        } 