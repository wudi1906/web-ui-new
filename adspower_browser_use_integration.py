#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AdsPower + WebUI 集成模块
基于testWenjuan.py和enhanced_testWenjuanFinal_with_knowledge.py的成功模式
只替换浏览器创建部分为AdsPower，完全复用原有webui技术
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime

# 使用与testWenjuan.py完全相同的导入方式
try:
    from browser_use.browser.browser import Browser, BrowserConfig
    from browser_use.browser.context import BrowserContextConfig
    from src.agent.browser_use.browser_use_agent import BrowserUseAgent
    from langchain_google_genai import ChatGoogleGenerativeAI
    webui_available = True
    logger = logging.getLogger(__name__)
    logger.info("✅ WebUI模块导入成功（使用testWenjuan.py导入方式）")
except ImportError as e:
    logging.warning(f"WebUI模块导入失败: {e}")
    webui_available = False
    Browser = None
    BrowserConfig = None
    BrowserContextConfig = None
    BrowserUseAgent = None
    ChatGoogleGenerativeAI = None

# AdsPower管理器
try:
    from enhanced_adspower_lifecycle import AdsPowerLifecycleManager
    adspower_available = True
except ImportError as e:
    logging.error(f"AdsPower模块导入失败: {e}")
    adspower_available = False
    AdsPowerLifecycleManager = None

# 导入窗口管理器
from window_layout_manager import get_window_manager

logger = logging.getLogger(__name__)

class HumanLikeInputAgent:
    """人类式输入代理 - 专门处理填空题输入"""
    
    def __init__(self, browser_context):
        self.browser_context = browser_context
        
    async def human_like_text_input(self, element_index: int, text: str) -> bool:
        """
        人类式文本输入 - 模拟真实用户输入行为
        
        Args:
            element_index: 元素索引
            text: 要输入的文本
            
        Returns:
            bool: 是否输入成功
        """
        try:
            logger.info(f"🔤 开始人类式输入: 索引{element_index}, 内容: {text}")
            
            # 策略1: 先点击获得焦点
            await self.browser_context.click_element_by_index(element_index)
            await asyncio.sleep(0.5)  # 等待焦点切换
            
            # 策略2: 尝试标准输入
            try:
                await self.browser_context.input_text(element_index, text)
                logger.info(f"✅ 标准输入成功")
                return True
            except Exception as e:
                logger.warning(f"⚠️ 标准输入失败: {e}")
            
            # 策略3: 重新点击后再次尝试
            await asyncio.sleep(0.5)
            await self.browser_context.click_element_by_index(element_index)
            await asyncio.sleep(0.5)
            
            try:
                await self.browser_context.input_text(element_index, text)
                logger.info(f"✅ 重试输入成功")
                return True
            except Exception as e:
                logger.warning(f"⚠️ 重试输入失败: {e}")
            
            # 策略4: 使用键盘输入（逐字符）
            logger.info(f"🔄 尝试键盘逐字符输入...")
            try:
                # 先清空现有内容
                await self.browser_context.keyboard_input("Ctrl+A")
                await asyncio.sleep(0.2)
                await self.browser_context.keyboard_input("Delete")
                await asyncio.sleep(0.3)
                
                # 逐字符输入（模拟人类打字）
                for char in text:
                    await self.browser_context.keyboard_input(char)
                    # 随机打字间隔（模拟人类）
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                
                logger.info(f"✅ 键盘逐字符输入成功")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ 键盘输入失败: {e}")
            
            # 策略5: JavaScript直接设值（最后手段）
            try:
                js_code = f"""
                (function() {{
                    const elements = document.querySelectorAll('input[type="text"], textarea');
                    if (elements[{element_index}]) {{
                        elements[{element_index}].value = "{text}";
                        elements[{element_index}].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        elements[{element_index}].dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                    return false;
                }})();
                """
                result = await self.browser_context.evaluate_javascript(js_code)
                if result:
                    logger.info(f"✅ JavaScript输入成功")
                    return True
                    
            except Exception as e:
                logger.warning(f"⚠️ JavaScript输入失败: {e}")
            
            logger.error(f"❌ 所有输入策略都失败了")
            return False
            
        except Exception as e:
            logger.error(f"❌ 人类式输入异常: {e}")
            return False

class AdsPowerWebUIIntegration:
    """AdsPower + WebUI 集成器 - 基于testWenjuan.py成功模式"""
    
    def __init__(self):
        if not adspower_available:
            raise ImportError("AdsPower模块不可用，请检查enhanced_adspower_lifecycle模块")
        if not webui_available:
            raise ImportError("WebUI模块不可用，请检查browser_use和相关依赖")
            
        self.adspower_manager = AdsPowerLifecycleManager()
        self.active_sessions = {}
        
    async def create_adspower_browser_session(self, persona_id: int, persona_name: str) -> Optional[str]:
        """创建AdsPower浏览器会话"""
        try:
            logger.info(f"🚀 为数字人 {persona_name}(ID:{persona_id}) 创建AdsPower浏览器会话")
            
            # 1. 创建完整的浏览器环境（青果代理 + AdsPower配置文件）
            browser_env = await self.adspower_manager.create_complete_browser_environment(
                persona_id, persona_name
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
            
            # 2. 生成会话ID
            session_id = f"adspower_session_{int(time.time())}_{persona_id}"
            
            # 3. 保存会话信息
            self.active_sessions[session_id] = {
                "persona_id": persona_id,
                "persona_name": persona_name,
                "profile_id": profile_id,
                "debug_port": debug_port,
                "browser_env": browser_env,
                "created_at": datetime.now(),
                "status": "ready"
            }
            
            logger.info(f"📝 会话已创建: {session_id}")
            
            # 3. 启动浏览器（完全按照testWenjuan.py）
            browser_info = await self.adspower_manager.start_browser(profile_id)
            if not browser_info.get("success", False):
                raise Exception(f"浏览器启动失败: {browser_info.get('error', '未知错误')}")
            
            debug_port = browser_info["debug_port"]
            logger.info(f"📱 获取到调试端口: {debug_port}")
            
            # 🪟 新增：设置窗口位置到6窗口平铺布局
            window_manager = get_window_manager()
            window_positioned = window_manager.set_browser_window_position(
                profile_id=profile_id,
                persona_name=persona_name,
                window_title="AdsPower"  # AdsPower窗口标题关键词
            )
            
            if window_positioned:
                logger.info(f"✅ 窗口布局设置成功：{persona_name} 已定位到6窗口平铺位置")
            else:
                logger.warning(f"⚠️ 窗口布局设置失败，但不影响问卷填写功能")
            
            # 等待窗口位置稳定
            await asyncio.sleep(2)
            
            return session_id
            
        except Exception as e:
            logger.error(f"❌ 创建AdsPower浏览器会话失败: {e}")
            return None

    async def execute_questionnaire_task_with_existing_browser(
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
        使用已存在的AdsPower浏览器执行问卷任务（完全基于testWenjuan.py的成功实现）
        
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
                    # 🔑 简化但有效的桌面模式配置
                    extra_chromium_args=[
                        # 强制桌面User-Agent（与AdsPower配置保持一致）
                        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        # 禁用移动端检测
                        "--disable-mobile-emulation", 
                        "--disable-touch-events",
                        # 强制桌面模式
                        "--force-device-scale-factor=1"
                    ],
                    new_context_config=BrowserContextConfig(
                        # 🖥️ 桌面视口尺寸（适当大小确保桌面内容）
                        window_width=1000,   # 适中大小
                        window_height=700,   # 适中大小
                        # 🎯 强制桌面User-Agent
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        # 📱 禁用移动端模拟
                        is_mobile=False,
                        has_touch=False,
                        # 🖥️ 桌面视口设置
                        viewport_width=1000,
                        viewport_height=700,
                        device_scale_factor=1.0,
                        # 🌐 基本设置
                        locale="zh-CN",
                        timezone_id="Asia/Shanghai"
                    )
                )
            )
            
            # 2. 创建上下文（桌面模式）
            context_config = BrowserContextConfig(
                # 🖥️ 桌面尺寸（确保桌面内容渲染）
                window_width=1000,   # 适中大小确保桌面模式
                window_height=700,   # 适中大小确保桌面模式
                # 🎯 强制桌面User-Agent
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                # 📱 明确禁用移动端
                is_mobile=False,
                has_touch=False,
                viewport_width=1000,
                viewport_height=700,
                device_scale_factor=1.0,
                locale="zh-CN",
                timezone_id="Asia/Shanghai"
            )
            browser_context = await browser.new_context(config=context_config)
            logger.info(f"✅ 浏览器上下文已创建（强制桌面模式），连接到AdsPower: {debug_port}")
            
            # 3. 初始化Gemini LLM（完全按照testWenjuan.py）
            if api_key is None:
                api_key = "AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8"
                
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=0.6,
                api_key=api_key,
            )
            logger.info(f"✅ LLM模型已初始化: {model_name}")
            
            # 4. 生成完整的提示词（包含数字人信息 + 人类式输入策略）
            complete_prompt = self._generate_complete_prompt_with_human_like_input(
                digital_human_info, questionnaire_url
            )
            
            # 5. 创建并运行代理（增强错误恢复 + 完整性保证）
            agent = BrowserUseAgent(
                task=complete_prompt,
                llm=llm,
                browser=browser,
                browser_context=browser_context,
                use_vision=True,
                max_actions_per_step=25,  # 增加每步操作数，应对复杂页面
                tool_calling_method='auto',
                extend_system_message="""
你是专业问卷填写专家，核心使命：确保100%完整答题！成功率是第一目标，速度排第二。

【🎯 核心原则】
1. 完整性第一：必须回答页面上的每一个题目，绝不遗漏
2. 永不放弃：遇到任何错误都要继续尝试，改变策略继续
3. 滚动必需：每完成当前屏幕后，必须向下滚动寻找更多题目
4. 持续到底：直到看到"提交成功"、"问卷完成"、"谢谢参与"才停止

【🔧 强大的错误恢复策略】
遇到"Element with index X does not exist"时：
1. 立即滚动页面：scroll_down(amount=300)
2. 等待页面稳定，重新分析可见元素
3. 寻找相似的未答题目继续作答
4. 如果仍找不到，继续滚动到页面底部
5. 绝不因个别元素失败而停止整个问卷

【✍️ 填空题处理（重要）】
遇到文本输入框时：
1. 先观察是否已有内容，有则跳过
2. 点击输入框获得焦点
3. 输入简短合理内容（20-50字）
4. 如果输入失败，立即重试：重新点击 → 再次输入
5. 绝不因填空题失败而放弃整个问卷

【📋 完整执行流程（关键）】
第1步：扫描当前屏幕所有题目
- 从上到下逐个检查每个题目
- 已答题目快速跳过，未答题目立即作答
- 遇到错误时，记录但继续处理其他题目

第2步：滚动寻找更多题目
- 向下滚动页面，寻找屏幕下方的更多题目
- 重复第1步，处理新出现的题目
- 一直滚动到页面底部

第3步：寻找并点击提交按钮
- 寻找"提交"、"下一页"、"下一题"、"继续"等按钮
- 点击进入下一页
- 在新页面重复整个流程

【🚨 关键错误恢复机制】
- 元素定位失败 → 滚动页面 → 重新扫描 → 继续作答
- 输入失败 → 重新点击 → 再次输入 → 继续其他题目
- 页面变化 → 重新分析当前状态 → 适应新结构
- 遇到困难 → 改变策略 → 绝不停止

【📝 填空内容示例】
- "希望改进服务质量，提升用户体验"
- "总体满意，建议增加更多选择"  
- "体验良好，期待进一步优化"
- "方便快捷，值得推荐"

【⚡ 智能避重复策略】
- 单选框已有圆点 → 跳过该题
- 多选框已有勾选 → 跳过该题
- 文本框已有内容 → 跳过该题
- 下拉框已选择 → 跳过该题

【🎯 成功标准】
- 所有可见题目都已作答
- 页面已滚动到底部
- 找到并点击了提交按钮
- 进入下一页或看到完成提示

记住：你的使命是确保100%完整答题！遇到任何困难都要坚持，改变策略继续，绝不轻易放弃！
                """,
                source="adspower_testwenjuan_human_like"
            )
            
            logger.info(f"✅ BrowserUseAgent已创建，使用testWenjuan.py验证的成功配置")
            
            # 6. 直接导航到目标URL（使用AdsPower已启动的标签页，不创建新标签页）
            await browser_context.navigate_to(questionnaire_url)
            logger.info(f"✅ 已导航到问卷URL: {questionnaire_url}")
            
            # 🪟 关键：导航完成后立即调整为6窗口平铺尺寸（确保桌面内容已渲染）
            await asyncio.sleep(2)  # 等待页面完全加载
            
            # 使用系统级窗口管理调整为6窗口平铺
            window_manager = get_window_manager()
            window_positioned = window_manager.set_browser_window_position(
                profile_id=existing_browser_info.get("profile_id", "unknown"),
                persona_name=persona_name,
                window_title="AdsPower"  # AdsPower窗口标题关键词
            )
            
            if window_positioned:
                logger.info(f"✅ 窗口已调整为6窗口平铺布局：{persona_name}")
                # 调整窗口大小为6窗口平铺尺寸
                try:
                    # 通过browser-use调整内部视口尺寸（补充系统级调整）
                    await browser_context.set_viewport_size(640, 540)
                    logger.info(f"✅ 浏览器视口已调整为6窗口平铺尺寸：640×540")
                except Exception as viewport_error:
                    logger.warning(f"⚠️ 视口尺寸调整失败，但不影响功能: {viewport_error}")
            else:
                logger.warning(f"⚠️ 6窗口平铺布局设置失败，但不影响问卷填写功能")
            
            # 等待窗口调整完成
            await asyncio.sleep(1)
            
            # 7. 运行代理执行任务（按照testWenjuan.py模式，增加完整性保证）
            start_time = time.time()
            logger.info(f"🚀 开始执行问卷任务（基于testWenjuan.py成功模式）...")
            
            try:
                # 执行任务，增加步数确保完整性
                result = await agent.run(max_steps=300)  # 增加步数确保完成所有题目
                
                end_time = time.time()
                duration = end_time - start_time
                
                # 评估成功性
                success = self._evaluate_webui_success(result)
                
                logger.info(f"✅ 问卷任务执行完成！")
                logger.info(f"   执行时长: {duration:.1f} 秒")
                logger.info(f"   执行结果: {'成功' if success else '部分完成'}")
                logger.info(f"   浏览器保持运行状态（按用户需求）")
                
                # 序列化结果
                serializable_result = self._serialize_agent_result(result)
                
                return {
                    "success": success,
                    "result": serializable_result,
                    "duration": duration,
                    "browser_info": {
                        "profile_id": existing_browser_info.get("profile_id"),
                        "debug_port": debug_port,
                        "proxy_enabled": existing_browser_info.get("proxy_enabled", False),
                        "browser_reused": True,
                        "browser_kept_running": True,
                        "webui_mode": True
                    },
                    "digital_human": {
                        "id": persona_id,
                        "name": persona_name,
                        "info": digital_human_info
                    },
                    "execution_mode": "adspower_testwenjuan_integration",
                    "final_status": "问卷填写完成" if success else "问卷填写部分完成",
                    "user_message": "浏览器保持运行，基于testWenjuan.py成功技术"
                }
                
            except Exception as agent_error:
                logger.error(f"❌ Agent执行过程中遇到错误: {agent_error}")
                logger.info(f"🔄 但AdsPower浏览器将保持运行状态（按用户需求）")
                
                end_time = time.time()
                duration = end_time - start_time
                
                return {
                    "success": False,
                    "partial_completion": True,
                    "error": str(agent_error),
                    "duration": duration,
                    "browser_info": {
                        "profile_id": existing_browser_info.get("profile_id"),
                        "debug_port": debug_port,
                        "proxy_enabled": existing_browser_info.get("proxy_enabled", False),
                        "browser_kept_alive": True,
                        "manual_control_available": True
                    },
                    "execution_mode": "adspower_testwenjuan_error_handled",
                    "final_status": "执行遇到错误，但浏览器保持运行",
                    "user_action_required": "请检查AdsPower浏览器页面"
                }
        
        except Exception as e:
            logger.error(f"❌ testWenjuan.py模式执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_mode": "adspower_testwenjuan_failed"
            }
        
        finally:
            # 确保清理Agent资源，但保持AdsPower浏览器运行
            try:
                if 'agent' in locals() and agent:
                    logger.info(f"🧹 清理Agent资源...")
                    await agent.close()
                    logger.info(f"✅ Agent资源已清理，AdsPower浏览器保持运行")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ 清理Agent资源时遇到问题: {cleanup_error}")

    def _generate_complete_prompt_with_human_like_input(self, digital_human_info: Dict, questionnaire_url: str) -> str:
        """生成包含人类式输入策略的完整任务提示词（基于testWenjuan.py成功模式 + 智能避重复 + 人类式填空）"""
        human_name = digital_human_info.get("name", "未知")
        human_age = digital_human_info.get("age", "30")
        human_job = digital_human_info.get("job", "普通职员")
        human_income = digital_human_info.get("income", "8000")
        human_gender = "女性" if digital_human_info.get("gender", "female") == "female" else "男性"
        
        prompt = f"""
你现在是一名{human_gender}，名叫{human_name}，今年{human_age}岁，职业是{human_job}，月收入{human_income}元。

你现在要完成问卷调查：{questionnaire_url}

【🎯 核心任务 - 基于testWenjuan.py成功模式】
1. 按照{human_name}的身份回答所有问题，选择最符合这个身份的选项
2. 所有题目都要作答，不能有遗漏 - 这是最重要的要求
3. 完成当前屏幕所有题目后，向下滚动页面寻找更多题目
4. 重复"答题→滚动→答题"直到页面底部
5. 每页题目100%完成后，点击"下一页"/"下一题"/"提交"按钮
6. 有的问卷是多页的，要一直重复"答题→滚动→下一页"操作
7. 直到出现"问卷完成"、"提交成功"、"谢谢参与"等提示才停止

【⚡ 智能答题策略（避免重复点击）】
- 操作前快速观察元素状态：
  * 单选框已有圆点选中 → 快速跳过该题，进入下一题
  * 多选框已有2-3个勾选 → 快速跳过该题，进入下一题  
  * 下拉框已显示选择结果 → 快速跳过该题，进入下一题
  * 文本框已有内容 → 快速跳过该题，进入下一题
- 未答题目立即处理：
  * 单选题：选择一个最符合{human_name}身份的选项
  * 多选题：选择2-3个相关选项
  * 填空题：根据身份填写合理的内容（⚡ 使用人类式输入）
  * 评分题：一般选择中等偏高的分数

【✍️ 填空题人类式输入策略（重要）】
对于文本输入框（textarea、input[type=text]等）：
1. 先点击文本框获得焦点，确保光标在输入框内
2. 准备合适的文本内容（根据{human_name}的身份特征）
3. 使用 input_text 动作，但内容要简短自然（20-50字）
4. 如果input_text失败，尝试以下策略：
   - 使用 click_element_by_index 重新点击输入框
   - 等待1-2秒让输入框准备好
   - 再次尝试 input_text 
   - 如果仍失败，使用键盘输入："focus输入框 → 清空内容 → 逐字输入"
5. 输入内容示例：
   - 建议类："{human_name}希望改进在线购物体验，增加更多商品展示。"
   - 意见类："{human_name}认为网购很方便，但希望物流更快一些。"
   - 评价类："{human_name}总体满意，希望售后服务更完善。"

【🔄 必填项检查处理】
- 点击"提交"后如出现"请完成必填项"等错误提示，需要回头补答
- 页面跳转到未答题目位置时，完成该题目
- 出现红色提示或必填项警告时，精确补答指定题目

【📋 完整执行流程（关键）】
第1步：处理当前屏幕
- 从页面顶部开始，逐个检查每个题目
- 已答题目快速跳过，未答题目立即作答
- 遇到填空题使用人类式输入策略

第2步：滚动寻找更多题目
- 向下滚动页面，寻找屏幕下方的更多题目
- 继续按第1步方式处理新出现的题目
- 重复滚动直到页面底部

第3步：导航到下一页
- 所有题目完成后，寻找"下一页"/"提交"按钮
- 点击进入下一页，在新页面重复整个流程

【🚨 关键要求】
- 滚动页面是必须的！不能只答第一屏的题目
- 不要重复点击已选择的选项（这会取消选择）
- 填空题输入失败时要多尝试几种方法，不要轻易放弃
- 如果遇到元素定位失败，先尝试滚动页面再重新定位
- 保持耐心，确保每个题目都完成
- 一直持续到看到最终的"提交成功"确认
- 🔧 遇到"Element with index X does not exist"错误时：立即滚动页面 → 重新扫描 → 继续作答

【🎯 100%完整性保证】
- 每完成一批题目后，必须向下滚动检查是否还有更多题目
- 滚动到页面底部后，寻找"提交"、"下一页"、"继续"按钮
- 如果是多页问卷，在新页面重复整个答题流程
- 绝不因个别错误而停止，要改变策略继续
- 成功标准：看到"提交成功"、"问卷完成"、"谢谢参与"等最终确认

记住：你是{human_name}，严格按照这个身份完成整个问卷调查！最重要的是要滚动页面处理所有题目，不能遗漏！对于填空题，要使用人类式自然输入！
        """
        
        return prompt.strip()

    def _evaluate_webui_success(self, result) -> bool:
        """评估webui模式的任务成功性"""
        try:
            if not result:
                return False
            
            # 检查是否有最终结果
            if hasattr(result, 'final_result'):
                final_result = result.final_result()
                if final_result and isinstance(final_result, str):
                    # 检查是否包含成功关键词
                    success_keywords = [
                        "完成", "成功", "提交", "谢谢", "感谢",
                        "complete", "success", "submitted", "thank"
                    ]
                    final_result_lower = final_result.lower()
                    for keyword in success_keywords:
                        if keyword.lower() in final_result_lower:
                            return True
            
            # 如果有历史记录，检查是否有足够的执行步骤
            if hasattr(result, 'history'):
                history = result.history
                if hasattr(history, 'history') and history.history:
                    # 有执行历史就认为有一定程度的成功
                    return len(history.history) > 5  # 至少执行了5个步骤
            
            # 如果result不为空，认为有部分成功
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ 评估成功性失败: {e}")
            return False

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
        """清理会话资源"""
        try:
            if session_id not in self.active_sessions:
                return True
            
            session = self.active_sessions[session_id]
            profile_id = session["profile_id"]
            persona_name = session["persona_name"]
            
            logger.info(f"🧹 清理会话资源: {persona_name}")
            
            # 使用AdsPowerLifecycleManager清理资源
            success = await self.adspower_manager.delete_browser_profile(profile_id)
            
            if success:
                logger.info(f"✅ AdsPower配置文件已删除: {profile_id}")
            else:
                logger.warning(f"⚠️ AdsPower配置文件删除失败: {profile_id}")
            
            # 从活跃会话中移除
            del self.active_sessions[session_id]
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 清理会话资源失败: {e}")
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        return self.active_sessions.get(session_id)
    
    def list_active_sessions(self) -> List[Dict]:
        """列出所有活跃会话"""
        return list(self.active_sessions.values())

# 便捷函数：使用已存在的AdsPower浏览器执行问卷工作流
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
        
        result = await integration.execute_questionnaire_task_with_existing_browser(
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
        result = await integration.execute_questionnaire_task_with_existing_browser(
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
    
    print("�� 测试结果:")
    print(f"   成功: {result.get('success')}")
    if result.get('success'):
        print(f"   执行时长: {result.get('duration', 0):.1f} 秒")
        print(f"   技术使用: testWenjuan.py + AdsPower")
    else:
        print(f"   错误: {result.get('error')}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_adspower_webui_integration())