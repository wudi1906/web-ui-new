#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问卷自动填写系统 - 直接集成testWenjuanFinal.py
实现：查找数字人 -> 打开浏览器 -> 调用testWenjuanFinal答题
"""

import asyncio
import logging
import time
import json
import requests
import os
from datetime import datetime
from typing import Dict, List, Optional

# 导入testWenjuanFinal.py的方法
from testWenjuanFinal import run_browser_task, generate_detailed_person_description, generate_complete_prompt
from questionnaire_system import DatabaseManager, DB_CONFIG
from config import get_config

# 设置Gemini API密钥环境变量
llm_config = get_config("llm")
if llm_config and llm_config.get("api_key"):
    os.environ["GOOGLE_API_KEY"] = llm_config["api_key"]
    print(f"✅ 已设置Gemini API密钥: {llm_config['api_key'][:20]}...")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'questionnaire_automation_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QuestionnaireAutomationSystem:
    """问卷自动化系统 - 直接集成testWenjuanFinal.py"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(DB_CONFIG)
        self.active_tasks = {}
    
    async def run_questionnaire_automation(self, questionnaire_url: str, target_count: int = 3) -> Dict:
        """运行问卷自动化流程"""
        logger.info(f"🚀 开始问卷自动化流程")
        logger.info(f"📋 问卷URL: {questionnaire_url}")
        logger.info(f"🎯 目标数量: {target_count}")
        
        try:
            # 步骤1: 查找符合条件的数字人
            personas = await self._get_suitable_personas(target_count)
            
            if not personas:
                logger.error("❌ 没有找到符合条件的数字人")
                return {"success": False, "error": "没有找到符合条件的数字人"}
            
            logger.info(f"✅ 找到 {len(personas)} 个符合条件的数字人")
            
            # 步骤2: 为每个数字人执行问卷填写
            results = []
            
            for i, persona in enumerate(personas):
                logger.info(f"👤 开始处理数字人 {i+1}/{len(personas)}: {persona['persona_name']}")
                
                try:
                    # 转换为testWenjuanFinal.py期望的格式
                    digital_human_data = self._convert_persona_to_digital_human(persona)
                    
                    # 生成详细的人物描述和提示词
                    person_description = generate_detailed_person_description(digital_human_data)
                    task_prompt, formatted_prompt = generate_complete_prompt(digital_human_data, questionnaire_url)
                    
                    logger.info(f"📝 {persona['persona_name']} 开始执行问卷填写")
                    
                    # 直接调用testWenjuanFinal.py的run_browser_task方法
                    start_time = time.time()
                    
                    await run_browser_task(
                        url=questionnaire_url,
                        prompt=task_prompt,
                        formatted_prompt=formatted_prompt,
                        model_type="gemini",
                        model_name=llm_config.get("model", "gemini-2.0-flash"),
                        api_key=llm_config.get("api_key"),  # 使用配置文件中的API密钥
                        temperature=llm_config.get("temperature", 0.5),
                        base_url=None,
                        auto_close=False,  # 保持浏览器打开
                        disable_memory=True,  # 禁用内存功能
                        max_retries=5,
                        retry_delay=5,
                        headless=False  # 显示浏览器
                    )
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    logger.info(f"✅ {persona['persona_name']} 问卷填写完成，用时: {duration:.2f}秒")
                    
                    # 保存执行记录
                    await self._save_execution_record(persona, questionnaire_url, True, duration, None)
                    
                    results.append({
                        "persona_name": persona['persona_name'],
                        "persona_id": persona['persona_id'],
                        "success": True,
                        "duration": duration,
                        "error": None
                    })
                    
                except Exception as e:
                    logger.error(f"❌ {persona['persona_name']} 问卷填写失败: {e}")
                    
                    # 保存失败记录
                    await self._save_execution_record(persona, questionnaire_url, False, 0, str(e))
                    
                    results.append({
                        "persona_name": persona['persona_name'],
                        "persona_id": persona['persona_id'],
                        "success": False,
                        "duration": 0,
                        "error": str(e)
                    })
                
                # 间隔执行，避免资源冲突
                if i < len(personas) - 1:
                    logger.info("⏳ 等待5秒后处理下一个数字人...")
                    await asyncio.sleep(5)
            
            # 统计结果
            successful_count = sum(1 for r in results if r["success"])
            success_rate = successful_count / len(results) if results else 0
            
            logger.info(f"🎉 问卷自动化流程完成!")
            logger.info(f"📊 成功率: {successful_count}/{len(results)} ({success_rate*100:.1f}%)")
            
            return {
                "success": True,
                "total_count": len(results),
                "successful_count": successful_count,
                "success_rate": success_rate,
                "results": results,
                "questionnaire_url": questionnaire_url
            }
            
        except Exception as e:
            logger.error(f"❌ 问卷自动化流程失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_suitable_personas(self, count: int) -> List[Dict]:
        """获取符合条件的数字人"""
        try:
            # 方法1: 尝试从小社会系统获取
            personas = await self._get_personas_from_xiaoshe(count)
            
            if personas:
                logger.info(f"✅ 从小社会系统获取到 {len(personas)} 个数字人")
                return personas
            
            # 方法2: 从数据库获取
            personas = await self._get_personas_from_database(count)
            
            if personas:
                logger.info(f"✅ 从数据库获取到 {len(personas)} 个数字人")
                return personas
            
            # 方法3: 使用模拟数据
            logger.warning("⚠️ 使用模拟数字人数据")
            return self._generate_mock_personas(count)
            
        except Exception as e:
            logger.error(f"❌ 获取数字人失败: {e}")
            return []
    
    async def _get_personas_from_xiaoshe(self, count: int) -> List[Dict]:
        """从小社会系统获取数字人"""
        try:
            personas = []
            
            for i in range(1, count + 1):
                try:
                    response = requests.get(f"http://localhost:5001/api/persona/{i}", timeout=10)
                    
                    if response.status_code == 200:
                        persona_data = response.json()
                        personas.append(persona_data)
                        logger.info(f"✅ 获取数字人 {i}: {persona_data.get('persona_name', '未知')}")
                    else:
                        logger.warning(f"⚠️ 数字人 {i} 获取失败: {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ 数字人 {i} 获取异常: {e}")
            
            return personas
            
        except Exception as e:
            logger.error(f"❌ 从小社会系统获取数字人失败: {e}")
            return []
    
    async def _get_personas_from_database(self, count: int) -> List[Dict]:
        """从数据库获取数字人"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT id, name, age, gender, profession, birthplace_str, residence_str, attributes
                FROM digital_humans 
                ORDER BY RAND() 
                LIMIT %s
                """, (count,))
                
                results = cursor.fetchall()
                
                personas = []
                for row in results:
                    persona = {
                        "persona_id": row[0],
                        "persona_name": row[1],
                        "age": row[2],
                        "gender": row[3],
                        "profession": row[4],
                        "birthplace_str": row[5] or "未知",
                        "residence_str": row[6] or "未知",
                        "attributes": json.loads(row[7]) if row[7] else {}
                    }
                    personas.append(persona)
                
                return personas
                
        except Exception as e:
            logger.error(f"❌ 从数据库获取数字人失败: {e}")
            return []
        finally:
            if 'connection' in locals():
                connection.close()
    
    def _generate_mock_personas(self, count: int) -> List[Dict]:
        """生成模拟数字人数据"""
        mock_personas = [
            {
                "persona_id": 1,
                "persona_name": "林心怡",
                "age": 35,
                "gender": "女",
                "profession": "高级时尚顾问",
                "birthplace_str": "上海",
                "residence_str": "北京",
                "attributes": {
                    "education": "本科",
                    "income": "高收入",
                    "interests": ["时尚", "购物", "旅行"]
                }
            },
            {
                "persona_id": 2,
                "persona_name": "张明",
                "age": 28,
                "gender": "男",
                "profession": "软件工程师",
                "birthplace_str": "北京",
                "residence_str": "深圳",
                "attributes": {
                    "education": "硕士",
                    "income": "中高收入",
                    "interests": ["编程", "游戏", "科技"]
                }
            },
            {
                "persona_id": 3,
                "persona_name": "王丽",
                "age": 42,
                "gender": "女",
                "profession": "市场经理",
                "birthplace_str": "广州",
                "residence_str": "上海",
                "attributes": {
                    "education": "本科",
                    "income": "高收入",
                    "interests": ["营销", "管理", "健身"]
                }
            },
            {
                "persona_id": 4,
                "persona_name": "李强",
                "age": 31,
                "gender": "男",
                "profession": "产品经理",
                "birthplace_str": "杭州",
                "residence_str": "杭州",
                "attributes": {
                    "education": "硕士",
                    "income": "高收入",
                    "interests": ["产品设计", "用户体验", "创新"]
                }
            },
            {
                "persona_id": 5,
                "persona_name": "陈雅",
                "age": 26,
                "gender": "女",
                "profession": "UI设计师",
                "birthplace_str": "成都",
                "residence_str": "北京",
                "attributes": {
                    "education": "本科",
                    "income": "中等收入",
                    "interests": ["设计", "艺术", "摄影"]
                }
            }
        ]
        
        return mock_personas[:count]
    
    def _convert_persona_to_digital_human(self, persona_info: Dict) -> Dict:
        """将persona_info转换为testWenjuanFinal.py期望的digital_human格式"""
        try:
            # 处理不同的persona_info结构
            if "background" in persona_info and isinstance(persona_info["background"], dict):
                # 敢死队格式，丰富信息在background中
                background = persona_info["background"]
                base_info = {
                    "id": persona_info.get('persona_id', background.get('id', 0)),
                    "name": persona_info.get('persona_name', background.get('name', '未知')),
                    "age": background.get('age', 30),
                    "gender": background.get('gender', '未知'),
                    "profession": background.get('profession', background.get('occupation', '未知')),
                    "birthplace_str": background.get('birthplace_str', background.get('birthplace', '未知')),
                    "residence_str": background.get('residence_str', background.get('residence', '未知')),
                    "attributes": background
                }
            else:
                # 直接格式，信息在根级别
                base_info = {
                    "id": persona_info.get('persona_id', persona_info.get('id', 0)),
                    "name": persona_info.get('persona_name', persona_info.get('name', '未知')),
                    "age": persona_info.get('age', 30),
                    "gender": persona_info.get('gender', '未知'),
                    "profession": persona_info.get('profession', persona_info.get('occupation', '未知')),
                    "birthplace_str": persona_info.get('birthplace_str', persona_info.get('birthplace', '未知')),
                    "residence_str": persona_info.get('residence_str', persona_info.get('residence', '未知')),
                    "attributes": persona_info.get('attributes', {})
                }
            
            logger.info(f"✅ 转换persona为digital_human格式: {base_info['name']}")
            return base_info
            
        except Exception as e:
            logger.error(f"❌ 转换persona格式失败: {e}")
            # 返回基本格式
            return {
                "id": persona_info.get('persona_id', 0),
                "name": persona_info.get('persona_name', '未知'),
                "age": 30,
                "gender": "未知",
                "profession": "未知",
                "birthplace_str": "未知",
                "residence_str": "未知",
                "attributes": {}
            }
    
    async def _save_execution_record(self, persona: Dict, questionnaire_url: str, 
                                   success: bool, duration: float, error: Optional[str]):
        """保存执行记录到数据库"""
        try:
            connection = self.db_manager.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO questionnaire_sessions 
                (session_id, questionnaire_url, persona_id, persona_name,
                 total_questions, successful_answers, success_rate, total_time,
                 session_type, strategy_used, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    f"testWenjuanFinal_{int(time.time())}_{persona['persona_id']}",
                    questionnaire_url,
                    persona['persona_id'],
                    persona['persona_name'],
                    1 if success else 0,
                    1 if success else 0,
                    100.0 if success else 0.0,
                    duration,
                    "testWenjuanFinal_integration",
                    "direct_integration",
                    datetime.now()
                ))
                connection.commit()
                logger.info(f"✅ 执行记录已保存: {persona['persona_name']}")
        except Exception as e:
            logger.error(f"❌ 保存执行记录失败: {e}")
        finally:
            if 'connection' in locals():
                connection.close()

async def main():
    """主函数"""
    print("🤖 智能问卷自动填写系统")
    print("=" * 50)
    
    # 获取问卷URL
    questionnaire_url = input("请输入问卷URL: ").strip()
    if not questionnaire_url:
        questionnaire_url = "https://www.wjx.cn/vm/ml5AbmN.aspx"  # 默认测试问卷
        print(f"使用默认问卷: {questionnaire_url}")
    
    # 获取目标数量
    try:
        target_count = int(input("请输入目标数字人数量 (默认3): ").strip() or "3")
    except ValueError:
        target_count = 3
        print("使用默认数量: 3")
    
    print("=" * 50)
    
    # 创建自动化系统
    automation_system = QuestionnaireAutomationSystem()
    
    # 执行自动化流程
    result = await automation_system.run_questionnaire_automation(questionnaire_url, target_count)
    
    # 显示结果
    if result["success"]:
        print(f"\n🎉 自动化流程执行完成!")
        print(f"📊 总数: {result['total_count']}")
        print(f"✅ 成功: {result['successful_count']}")
        print(f"📈 成功率: {result['success_rate']*100:.1f}%")
        
        print("\n📋 详细结果:")
        for r in result["results"]:
            status = "✅ 成功" if r["success"] else f"❌ 失败: {r['error']}"
            print(f"  {r['persona_name']}: {status}")
            if r["success"]:
                print(f"    用时: {r['duration']:.2f}秒")
    else:
        print(f"\n❌ 自动化流程失败: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main()) 