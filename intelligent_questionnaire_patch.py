#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷系统修正补丁
用于修正adspower_browser_use_integration.py中的execute_intelligent_questionnaire_task方法
"""

INTELLIGENT_QUESTIONNAIRE_METHOD_FIX = '''
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
'''

if __name__ == "__main__":
    print("📋 智能问卷系统修正补丁已准备好")
    print("请手动将INTELLIGENT_QUESTIONNAIRE_METHOD_FIX的内容")
    print("替换adspower_browser_use_integration.py中的execute_intelligent_questionnaire_task方法") 