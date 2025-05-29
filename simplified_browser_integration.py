
class SimplifiedBrowserIntegration:
    """简化的浏览器集成，专注于稳定性"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.active_sessions = {}
    
    async def create_browser_session(self, persona_info: Dict, browser_config: Dict) -> str:
        """创建浏览器会话（简化版）"""
        try:
            from playwright.async_api import async_playwright
            
            session_id = f"session_{int(time.time())}_{persona_info['persona_id']}"
            
            # 启动playwright
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=browser_config.get('headless', False),
                args=browser_config.get('args', [])
            )
            context = await browser.new_context()
            page = await context.new_page()
            
            # 保存会话
            self.active_sessions[session_id] = {
                "persona_info": persona_info,
                "playwright": playwright,
                "browser": browser,
                "context": context,
                "page": page,
                "created_at": datetime.now()
            }
            
            return session_id
            
        except Exception as e:
            logger.error(f"创建浏览器会话失败: {e}")
            return None
    
    async def navigate_to_questionnaire(self, session_id: str, url: str) -> bool:
        """导航到问卷页面"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            page = session["page"]
            
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            
            return True
            
        except Exception as e:
            logger.error(f"导航失败: {e}")
            return False
    
    async def simulate_questionnaire_answering(self, session_id: str) -> Dict:
        """模拟问卷答题"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "会话不存在"}
            
            session = self.active_sessions[session_id]
            page = session["page"]
            persona_info = session["persona_info"]
            
            # 注入答题脚本
            result = await page.evaluate("""
                () => {
                    const questions = document.querySelectorAll('input[type="radio"], input[type="checkbox"], select, textarea, input[type="text"]');
                    let answered = 0;
                    
                    questions.forEach((element) => {
                        if (element.type === 'radio' && !element.checked) {
                            const radioGroup = document.querySelectorAll(`input[name="${element.name}"]`);
                            if (radioGroup.length > 0) {
                                const randomIndex = Math.floor(Math.random() * radioGroup.length);
                                radioGroup[randomIndex].checked = true;
                                answered++;
                            }
                        } else if (element.type === 'checkbox') {
                            if (Math.random() > 0.5) {
                                element.checked = true;
                                answered++;
                            }
                        } else if (element.tagName === 'SELECT') {
                            const options = element.options;
                            if (options.length > 1) {
                                const randomIndex = Math.floor(Math.random() * (options.length - 1)) + 1;
                                element.selectedIndex = randomIndex;
                                answered++;
                            }
                        } else if (element.type === 'text' || element.tagName === 'TEXTAREA') {
                            element.value = '这是一个测试回答';
                            answered++;
                        }
                    });
                    
                    return answered;
                }
            """)
            
            return {
                "success": True,
                "answered_questions": result,
                "persona_name": persona_info.get("persona_name", "未知"),
                "duration": 5.0
            }
            
        except Exception as e:
            logger.error(f"模拟答题失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def close_session(self, session_id: str):
        """关闭会话"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                await session["context"].close()
                await session["browser"].close()
                await session["playwright"].stop()
                
                del self.active_sessions[session_id]
                
        except Exception as e:
            logger.error(f"关闭会话失败: {e}")
