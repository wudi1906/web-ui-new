#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加缺失的方法到三阶段智能核心
"""

def add_missing_methods():
    """添加缺失的方法"""
    
    # 读取原文件
    with open('intelligent_three_stage_core.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 新方法代码
    new_methods = '''
    async def _execute_gemini_screenshot_analysis(
        self, 
        session_id: str, 
        questionnaire_url: str, 
        successful_experiences: List[ScoutExperience]
    ) -> str:
        """
        执行Gemini截图分析，生成大部队作答经验指导
        """
        try:
            if not ADSPOWER_WEBUI_AVAILABLE:
                logger.warning("⚠️ AdsPowerWebUI不可用，跳过Gemini截图分析")
                return ""
            
            from adspower_browser_use_integration import GeminiScreenshotAnalyzer
            gemini_analyzer = GeminiScreenshotAnalyzer(self.gemini_api_key)
            
            best_experience = successful_experiences[0] if successful_experiences else None
            if not best_experience or not best_experience.page_screenshot:
                logger.warning("⚠️ 没有可用的成功截图，跳过Gemini分析")
                return ""
            
            logger.info(f"🖼️ 分析最成功敢死队 {best_experience.scout_name} 的截图")
            
            digital_human_info = {
                "name": best_experience.scout_name,
                "gender": "未知",
                "age": "未知", 
                "profession": "未知",
                "income": "未知"
            }
            
            optimized_screenshot, size_kb, saved_filepath = await gemini_analyzer.optimize_screenshot_for_gemini(
                best_experience.page_screenshot, best_experience.scout_name, session_id
            )
            
            logger.info(f"📸 截图已优化: {size_kb}KB, 保存至: {saved_filepath}")
            
            analysis_result = await gemini_analyzer.analyze_questionnaire_screenshot(
                optimized_screenshot, digital_human_info, questionnaire_url
            )
            
            guidance_text = analysis_result.get("guidance_for_troops", "")
            
            if guidance_text:
                logger.info(f"✅ Gemini截图分析成功，生成经验指导")
                
                if not hasattr(self, 'session_gemini_analysis'):
                    self.session_gemini_analysis = {}
                    
                self.session_gemini_analysis[session_id] = {
                    "analysis_result": analysis_result,
                    "best_scout": best_experience.scout_name,
                    "screenshot_filepath": saved_filepath,
                    "analysis_time": datetime.now().isoformat(),
                    "guidance_preview": guidance_text[:200] + "..." if len(guidance_text) > 200 else guidance_text
                }
                
                return guidance_text
            else:
                logger.warning("⚠️ Gemini分析未生成有效的经验指导")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Gemini截图分析失败: {e}")
            return ""
    
    def get_session_gemini_analysis(self, session_id: str) -> Optional[Dict]:
        """获取会话的Gemini分析结果"""
        if hasattr(self, 'session_gemini_analysis'):
            return self.session_gemini_analysis.get(session_id)
        return None

'''
    
    # 在__init__方法中添加session_gemini_analysis初始化
    init_addition = '''        
        # 🆕 新增：初始化Gemini分析会话数据存储
        self.session_gemini_analysis = {}
        '''
    
    # 替换内容
    if '# 导出核心类供app.py使用' in content:
        content = content.replace('# 导出核心类供app.py使用', new_methods + '# 导出核心类供app.py使用')
    
    # 在__init__方法的最后添加初始化
    if 'logger.info("✅ 三阶段智能核心系统初始化完成")' in content:
        content = content.replace(
            'logger.info("✅ 三阶段智能核心系统初始化完成")',
            init_addition + '\n        logger.info("✅ 三阶段智能核心系统初始化完成")'
        )
    
    # 写回文件
    with open('intelligent_three_stage_core.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✅ 方法已添加到三阶段智能核心')

if __name__ == "__main__":
    add_missing_methods() 