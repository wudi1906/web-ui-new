import asyncio
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def get_llm(): return {}
def get_digital_human_by_id(human_id): return {"id": human_id, "name": "张小雅"}
def generate_detailed_person_description(digital_human): return f"数字人: {digital_human.get("name", "未知")}"
def generate_complete_prompt(digital_human, url): return "prompt", "prompt"
async def run_browser_task(url, prompt, digital_human, **kwargs): return {"success": True}
async def run_browser_task_with_adspower(url, prompt, formatted_prompt, adspower_debug_port, digital_human, **kwargs): print(f"AdsPower: {digital_human.get("name")}"); await asyncio.sleep(1); return {"success": True}