#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import argparse
import json
import pymysql
import pymysql.cursors
import time
import sys
import os
from typing import Optional, Dict, Any, List, Union

# 导入所需模块
try:
    # 以下导入可能在某些IDE中显示为未解析，但在实际运行环境中是可用的
    from browser_use import Browser, BrowserConfig, Agent
    from browser_use.browser.context import BrowserContextConfig
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    # 不再需要ollama支持
    OLLAMA_AVAILABLE = False
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装必要的依赖，可以运行：")
    print("pip install browser-use langchain_google_genai pymysql")
    sys.exit(1)

# 数据库配置
DB_CONFIG = {
    "host": "192.168.50.137",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "wenjuan",
    "charset": "utf8mb4"
}

# 模型配置
MODEL_CONFIGS = {
    "gemini": {
        "base_url": None,  # 使用默认URL
        "models": ["gemini-2.0-flash"]
    }
}

def test_db_connection():
    """测试数据库连接"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✅ 数据库连接成功！")
                return True
            return False
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    finally:
        if 'connection' in locals() and connection:
            connection.close()

def list_digital_humans():
    """列出所有数字人"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, name, age, gender, profession FROM digital_humans")
            results = cursor.fetchall()
            
            print("\n📋 数字人列表:")
            print(f"{'ID':<5} {'姓名':<10} {'年龄':<5} {'性别':<5} {'职业':<20}")
            print("-" * 50)
            
            for human in results:
                print(f"{human['id']:<5} {human['name']:<10} {human['age']:<5} {human['gender']:<5} {human['profession']:<20}")
            
            return results
    except Exception as e:
        print(f"❌ 获取数字人列表失败: {e}")
        return []
    finally:
        if 'connection' in locals() and connection:
            connection.close()

def get_digital_human_by_id(human_id: int) -> Optional[Dict[str, Any]]:
    """
    从数据库获取指定ID的数字人完整信息
    
    参数:
        human_id: 数字人ID
    
    返回:
        数字人信息字典
    """
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 查询数字人信息，包括外键关联数据
            sql = """
            SELECT dh.*, 
                c1.name as birthplace_country, p1.name as birthplace_province, city1.name as birthplace_city,
                c2.name as residence_country, p2.name as residence_province, city2.name as residence_city
            FROM digital_humans dh
            LEFT JOIN countries c1 ON dh.birthplace_country_id = c1.id
            LEFT JOIN provinces p1 ON dh.birthplace_province_id = p1.id
            LEFT JOIN cities city1 ON dh.birthplace_city_id = city1.id
            LEFT JOIN countries c2 ON dh.residence_country_id = c2.id
            LEFT JOIN provinces p2 ON dh.residence_province_id = p2.id
            LEFT JOIN cities city2 ON dh.residence_city_id = city2.id
            WHERE dh.id = %s
            """
            cursor.execute(sql, (human_id,))
            result = cursor.fetchone()
            
            if result:
                # 将JSON格式的attributes解析为Python对象
                if result.get('attributes'):
                    if isinstance(result['attributes'], str):
                        result['attributes'] = json.loads(result['attributes'])
                
                print(f"✅ 成功获取 ID={human_id} 的数字人: {result['name']}")
            else:
                print(f"❌ 未找到 ID={human_id} 的数字人")
            
            return result
    except Exception as e:
        print(f"❌ 数据库连接或查询错误: {e}")
        return None
    finally:
        if 'connection' in locals() and connection:
            connection.close()

def generate_detailed_person_description(digital_human: Dict[str, Any]) -> str:
    """
    生成详细的人物描述
    
    参数:
        digital_human: 数字人信息
        
    返回:
        格式化的人物描述
    """
    if not digital_human:
        return "无法获取人物信息"
    
    # 基本信息
    birthplace = digital_human.get('birthplace_str') or f"{digital_human.get('birthplace_country', '')} {digital_human.get('birthplace_province', '')} {digital_human.get('birthplace_city', '')}"
    residence = digital_human.get('residence_str') or f"{digital_human.get('residence_country', '')} {digital_human.get('residence_province', '')} {digital_human.get('residence_city', '')}"
    
    birth_month = 5  # 默认月份
    birth_day = 16  # 默认日期
    
    # 人物基本描述
    basic_info = (
        f"你现在是一名{digital_human['gender']}性，名叫{digital_human['name']}，今年{digital_human['age']}岁，"
        f"生日是{birth_month}月{birth_day}日，职业是{digital_human['profession']}，"
        f"出生于{birthplace}，现居住在{residence}。"
    )
    
    # 处理属性信息
    attributes = digital_human.get('attributes', {})
    attributes_text = ""
    
    if attributes:
        # 先处理常规属性（非列表）
        regular_attrs = []
        for key, value in attributes.items():
            if not isinstance(value, list):
                regular_attrs.append(f"{key}是{value}")
        
        if regular_attrs:
            attributes_text += "，".join(regular_attrs) + "。"
        
        # 再处理列表属性
        list_attrs = []
        for key, value in attributes.items():
            if isinstance(value, list) and value:
                list_attrs.append(f"{key}包括{', '.join(value)}")
        
        if list_attrs:
            attributes_text += "，".join(list_attrs) + "。"
    
    # 完整人物描述
    full_description = basic_info + attributes_text
    
    return full_description

def generate_task_instructions(url: str) -> str:
    """
    生成详细的任务指导说明
    
    参数:
        url: 问卷URL
        
    返回:
        格式化的任务指导说明
    """
    return f"""
你将在浏览器中访问此问卷: {url}

【作答要求】
1. 仔细阅读每一个问题，认真思考后再回答
2. 所有问题都必须作答，不能有遗漏
3. 每回答完当前页面的问题，点击"下一页"或"提交"按钮继续
4. 持续回答问题直到看到"问卷已提交"、"问卷作答完成"等类似提示

【技术指导与元素定位策略】
1. 优先使用文本内容定位元素，不要依赖元素索引，例如:
   - 查找文字为"下一页"的按钮：点击显示"下一页"文字的按钮
   - 选择选项时，查找选项文本：选择"非常满意"选项
   
2. 滚动策略:
   - 滚动前，先记住当前可见元素
   - 滚动后，等待500毫秒让页面稳定
   - 滚动后重新观察页面中的所有元素，因为索引很可能已变化
   - 使用小幅度、渐进式滚动，而不是一次滚到底部
   
3. 元素交互:
   - 单选题：点击选项前的圆形按钮或选项文本
   - 多选题：点击选项前的方形按钮或选项文本
   - 文本输入：找到输入框并输入文字
   - 下拉选择：先点击下拉框，再选择合适选项
   
4. 错误处理:
   - 如果点击失败，尝试先滚动使元素进入视图
   - 如果找不到元素，使用相邻文本或问题标题辅助定位
   - 遇到弹窗，先处理弹窗再继续

记住：始终根据你的人物身份来回答，保持一致性，确保回答符合你的角色设定和个人特征。

【省市选择与输入特别说明】
当遇到居住地/出生地等省市选择时：
1. 对于省级选择：找到省份输入框，直接输入完整省份名称（如"浙江省"）
2. 对于城市输入：在输入省份后，找到城市输入框（通常是下一个输入框），直接输入城市全名（如"杭州市"）
3. 填写完毕后，点击"确定"或"下一步"按钮继续

重要：不要尝试点击下拉框中的选项，而是直接在输入框中键入完整地名

【元素识别技巧】
1. 对于输入框，查找靠近"省/直辖市"或"城市/镇"等标签的输入元素
2. 输入框通常以<input>标签表示，可能有placeholder属性提示要输入什么
3. 如果输入后页面发生变化，等待页面稳定再进行下一步操作
4. 如果看到下拉选项出现，忽略它们，继续完成当前输入并按回车或点击空白区域确认

【应对页面刷新策略】
1. 如果页面刷新或重载，保持冷静，重新开始输入操作
2. 每完成一个输入后，确认输入已被接受再继续下一步
3. 如果发现同一操作反复失败，尝试替代方法，如先点击输入框使其获得焦点再输入
"""

def generate_complete_prompt(digital_human: Dict[str, Any], url: str) -> tuple[str, str]:
    """
    根据数字人信息和URL生成完整的提示词
    
    参数:
        digital_human: 数字人信息
        url: 问卷URL
        
    返回:
        元组: (原始提示词, 格式化的提示词用于显示)
    """
    # 第一部分：人物描述
    person_description = generate_detailed_person_description(digital_human)
    
    # 第二部分：任务指导
    task_instructions = generate_task_instructions(url)
    
    # 组合完整提示词
    full_prompt = f"{person_description}\n\n{task_instructions}"
    
    # 添加分隔和格式化，提高可读性
    formatted_prompt = "=" * 80 + "\n"
    formatted_prompt += "【人物设定】\n" + person_description + "\n\n"
    formatted_prompt += "【任务要求】\n" + task_instructions + "\n"
    formatted_prompt += "=" * 80
    
    return full_prompt, formatted_prompt

def get_llm(model_type: str, model_name: str, api_key: Optional[str] = None, temperature: float = 0.5, base_url: Optional[str] = None):
    """
    根据指定的模型类型和名称创建LLM实例
    
    参数:
        model_type: 模型类型（仅支持'gemini'）
        model_name: 模型名称
        api_key: API密钥（如需要）
        temperature: 模型温度参数
        base_url: 模型服务器基础URL（对gemini无效）
        
    返回:
        LLM实例或配置信息
    """
    if model_type != "gemini":
        raise ValueError(f"不支持的模型类型: {model_type}，仅支持gemini")
        
    # 如果没有提供API密钥，尝试从环境变量获取
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("必须提供Gemini API密钥，或设置GOOGLE_API_KEY环境变量")
            
    # 设置环境变量以避免memory模块的警告
    os.environ["GOOGLE_API_KEY"] = api_key
    
    # 确保清除之前可能设置的ollama环境变量
    for env_var in ["BROWSER_USE_OLLAMA_ONLY", "BROWSER_USE_LLM_PROVIDER", "BROWSER_USE_LLM_MODEL", 
                   "BROWSER_USE_LLM_BASE_URL", "BROWSER_USE_LLM_TEMPERATURE"]:
        if env_var in os.environ:
            del os.environ[env_var]
    
    print("🔄 使用Gemini API")
    return ChatGoogleGenerativeAI(
        model=model_name or "gemini-2.0-flash",
        temperature=temperature,
        api_key=api_key,
    )

async def run_browser_task(url: str, prompt: str, formatted_prompt: str, 
                          model_type: str = "gemini",
                          model_name: str = "gemini-2.0-flash", 
                          api_key: Optional[str] = None,
                          temperature: float = 0.5,
                          base_url: Optional[str] = None,
                          auto_close: bool = False,
                          disable_memory: bool = False,
                          max_retries: int = 5,  # 增加默认重试次数
                          retry_delay: int = 5,
                          headless: bool = False):
    """
    使用Browser-Use自动化执行指定的浏览器任务
    
    参数:
        url: 要访问的网站URL
        prompt: 提供给AI的提示词
        formatted_prompt: 格式化后的提示词（用于显示）
        model_type: 模型类型（仅支持'gemini'）
        model_name: 模型名称
        api_key: API密钥（如需要）
        temperature: 模型温度参数
        base_url: 模型服务器基础URL（对gemini无效）
        auto_close: 任务完成后是否自动关闭浏览器
        disable_memory: 是否禁用内存功能（避免API密钥缺失警告）
        max_retries: 遇到API错误时的最大重试次数
        retry_delay: 重试之间的延迟秒数
        headless: 是否在无头模式下运行浏览器
    """
    print("\n" + "=" * 40)
    print("🚀 启动自动化问卷填写任务")
    print("=" * 40)
    print(f"📝 使用模型类型: {model_type}")
    print(f"📝 使用模型: {model_name}")
    print(f"🌡️ 模型温度: {temperature}")
    print(f"🔗 目标URL: {url}")
    print(f"🤖 任务完成后{'自动关闭' if auto_close else '保持打开'}浏览器")
    print(f"🧠 内存功能: {'禁用' if disable_memory else '启用'}")
    print(f"🖥️ 浏览器模式: {'无头模式' if headless else '可见模式'}")
    print("\n📋 提示词概览:")
    print(formatted_prompt[:500] + "...\n")
    
    # 如果禁用内存功能，设置环境变量
    if disable_memory:
        os.environ["BROWSER_USE_DISABLE_MEMORY"] = "true"
    
    # 模型回退机制
    current_model_type = model_type
    current_model_name = model_name
    retry_count = 0
    
    # 初始化浏览器
    print("🔧 初始化浏览器...")
    browser = Browser(
        config=BrowserConfig(
            headless=headless,  # 根据参数设置是否无头模式
            disable_security=True,
            browser_binary_path=None,
            new_context_config=BrowserContextConfig(
                window_width=1280,
                window_height=800,
            )
        )
    )
    
    # 创建上下文
    context_config = BrowserContextConfig(
        window_width=1280,
        window_height=800,
    )
    browser_context = await browser.new_context(config=context_config)
    
    # 导航到目标URL
    try:
        print("🌐 打开浏览器标签页...")
        await browser_context.create_new_tab()
        
        print(f"🔍 导航至问卷URL: {url}")
        await browser_context.navigate_to(url)
        
        # 等待页面加载
        print("⏳ 等待页面初始加载...")
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ 打开URL时发生错误: {e}")
        # 清理资源
        await browser_context.close()
        await browser.close()
        raise
    
    # 循环尝试不同的模型配置
    while retry_count <= max_retries:
        try:
            # 获取LLM配置
            print(f"🧠 初始化LLM模型: {current_model_type}/{current_model_name}")
            try:
                llm_config = get_llm(current_model_type, current_model_name, api_key, temperature, base_url)
                print(f"✅ 成功创建LLM对象: {llm_config}")
                # 检查LLM对象是否有必要的方法
                has_get_method = hasattr(llm_config, 'get') and callable(getattr(llm_config, 'get'))
                has_invoke_method = hasattr(llm_config, 'invoke') and callable(getattr(llm_config, 'invoke'))
                print(f"📊 LLM对象方法检查: get={has_get_method}, invoke={has_invoke_method}")
                
                # 使用Gemini模式
                print("✅ 使用gemini-2.0-flash模型")
            except Exception as e:
                print(f"⚠️ 创建LLM对象失败: {e}")
                # 直接抛出异常
                raise
            
            # 创建代理配置
            print("🤖 配置AI代理...")
            
            # 系统消息，包含技术指导
            system_message = """你是一个专业的问卷填写助手，擅长按照人物角色填写各类在线问卷。

关于元素定位:
1. 始终优先使用文本内容定位元素，例如：点击"下一页"按钮、选择"非常满意"选项
2. 如果文本定位失败，尝试使用元素类型和属性，例如：点击类型为radio的输入框
3. 尽量避免使用元素索引，因为它们在页面变化时不可靠

关于页面滚动:
1. 滚动后等待页面稳定再继续操作
2. 滚动后重新评估可见元素，不要假设元素位置不变
3. 采用小幅度多次滚动策略，而非一次大幅度滚动

关于问题回答:
1. 分析问题类型（单选、多选、文本输入等）后再操作
2. 按照人物角色特征选择最合适的选项
3. 确保所有问题都有回答，不留空白
4. Heuristics: 优先选择第一个或带"满意"字样的选项，如确实不适合角色再选其他

交互策略:
1. 完成当前页面所有问题后，寻找"下一页"或"提交"按钮
2. 如果找不到下一步按钮，尝试滚动页面寻找
3. 遇到弹窗先处理再继续
4. 保持耐心，一个页面一个页面地完成
5. 如果遇到错误或异常，不要立即终止任务，而是尝试恢复并继续

重要提示:
1. 绝对不要在看到"感谢您的参与"、"问卷已提交成功"或类似最终确认页面之前终止任务
2. 如果一种方法失败，尝试其他方法完成相同的目标
3. 永远不要放弃，即使你认为任务可能已经失败，仍然继续尝试
4. 当且仅当看到明确的问卷完成或提交成功页面时，才可以使用done命令

必须确保坚持到问卷真正提交成功为止!
"""

            # 创建代理基本参数 
            agent_kwargs = {
                "task": prompt,
                "browser": browser,
                "browser_context": browser_context,
                "use_vision": True,
                "max_actions_per_step": 20,  # 增加每步可执行的动作数
                "tool_calling_method": 'auto',
                "extend_system_message": system_message,
                "source": "wenjuan_automation"
            }
            
            # 设置LLM参数
            agent_kwargs["llm"] = llm_config
            print(f"✅ 为Gemini设置LLM: {llm_config}")
            
            # 创建并运行代理
            try:
                print("✅ 创建AI代理")
                # 常规方式创建Agent
                agent = Agent(**agent_kwargs)
                print("✅ 使用正常方式成功创建Agent")
                
                # 运行代理执行任务
                print("\n🚀 开始执行代理任务...")
                print("⏳ 等待代理完成任务，这可能需要一些时间...\n")
                
                # 获取agent运行的支持参数
                import inspect
                run_params = inspect.signature(agent.run).parameters
                run_args = {}
                
                # 如果支持max_steps参数，添加较大的值确保能完成所有问题
                if 'max_steps' in run_params:
                    run_args['max_steps'] = 500  # 增加最大步数以确保完成所有问题
                    print("⚙️ 设置最大步数: 500")
                    
                # 设置较长的超时时间    
                if 'timeout' in run_params:
                    run_args['timeout'] = 3600  # 1小时超时
                    print("⚙️ 设置超时时间: 3600秒")
                
                # 执行任务
                start_time = time.time()
                result = await agent.run(**run_args)
                end_time = time.time()
                
                # 任务完成信息
                duration = end_time - start_time
                print("\n" + "=" * 40)
                print(f"✅ 任务完成! 用时: {duration:.2f}秒")
                
                # 提取完成的步骤数
                step_count = 0
                if hasattr(result, 'all_results'):
                    step_count = len(result.all_results)
                
                print(f"📊 总共执行步骤: {step_count}")
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                if "quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                    retry_count += 1
                    print(f"\n⚠️ API配额限制错误，尝试切换模型配置 (尝试 {retry_count}/{max_retries})...")
                    
                    # 只使用gemini-2.0-flash，不切换模型
                    if current_model_type == "gemini":
                        print(f"⚠️ API配额限制错误，但继续使用gemini-2.0-flash模型")
                        
                        if retry_count <= max_retries:
                            print(f"⏳ 等待 {retry_delay} 秒后重试...")
                            await asyncio.sleep(retry_delay)
                            continue
                    else:
                        # 在deepseek/ollama模式下不自动切换到gemini
                        print(f"\n❌ API错误，但不会切换到Gemini模式: {e}")
                        # 可以选择重试当前模型或直接失败
                        if retry_count <= max_retries:
                            print(f"⏳ 等待 {retry_delay} 秒后重试同一模型...")
                            await asyncio.sleep(retry_delay)
                            continue
                
                print(f"\n❌ 任务执行过程中发生错误: {e}")
                print("将保持浏览器打开状态，便于手动检查")
                raise
        except Exception as e:
            print(f"❌ 初始化LLM失败: {e}")
            retry_count += 1
            if retry_count <= max_retries:
                print(f"⏳ 尝试切换模型，等待 {retry_delay} 秒后重试...")
                await asyncio.sleep(retry_delay)
                
                # 不切换模型，仅重试
                if current_model_type == "gemini":
                    print(f"🔄 重试当前模型: {current_model_name}")
                    continue
            
            # 清理资源
            await browser_context.close()
            await browser.close()
            raise
            
    # 如果所有重试都失败
    print("\n❌ 所有模型配置都失败，无法完成任务")
    
    # 清理环境
    try:
        # 清理环境变量
        if disable_memory and "BROWSER_USE_DISABLE_MEMORY" in os.environ:
            del os.environ["BROWSER_USE_DISABLE_MEMORY"]
        
        # 清理模型环境变量
        for env_var in ["BROWSER_USE_OLLAMA_ONLY", "BROWSER_USE_LLM_PROVIDER", "BROWSER_USE_LLM_MODEL", 
                        "BROWSER_USE_LLM_BASE_URL", "BROWSER_USE_LLM_TEMPERATURE"]:
            if env_var in os.environ:
                del os.environ[env_var]
        
        # 资源清理
        if auto_close:
            await browser_context.close()
            await browser.close()
            print("🔒 浏览器已关闭")
        else:
            print("🔓 浏览器保持打开状态，请手动关闭浏览器窗口")
            # 关闭代理但保持浏览器打开
            if 'agent' in locals():
                await agent.close()
    except Exception as e:
        print(f"⚠️ 清理资源时发生错误: {e}")

def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description="数字人问卷自动填写工具")
    parser.add_argument("--url", type=str, default="http://www.jinshengsurveys.com/?type=qtaskgoto&id=38784&token=FBC7E73EE2CE537C114EF3CCE3393DD5D2FFBC2BDDBE9F3CB4EEFB4B39D29D670EC6C5EC88BB86194F109B43670E8AB58386D6CE6525397A56B81C1CD5E1B48E", 
                        help="要访问的问卷URL")
    parser.add_argument("--digital-human-id", "-id", type=int, 
                        help="数字人ID，从数据库获取对应数字人信息")
    parser.add_argument("--api-key", type=str, 
                       help="API密钥（用于Gemini等需要密钥的模型）")
    parser.add_argument("--model-type", type=str, choices=["gemini"], default="gemini",
                       help="要使用的模型类型（目前仅支持gemini）")
    parser.add_argument("--model", type=str, default="gemini-2.0-flash",
                       help="具体的模型名称（默认使用gemini-2.0-flash）")
    parser.add_argument("--base-url", type=str,
                       help="模型服务的基础URL（可选，默认使用模型类型的默认URL）")
    parser.add_argument("--temperature", type=float, default=0.5, 
                       help="模型温度参数，控制创造性，值越大越有创造性，范围0-1")
    parser.add_argument("--auto-close", action="store_true", 
                       help="任务完成后自动关闭浏览器")
    parser.add_argument("--disable-memory", action="store_true", 
                       help="禁用内存功能，避免API密钥缺失警告")
    parser.add_argument("--headless", action="store_true",
                       help="在无头模式下运行浏览器（不显示浏览器界面）")
    parser.add_argument("--max-retries", type=int, default=5,
                       help="API错误时的最大重试次数")
    parser.add_argument("--retry-delay", type=int, default=5,
                       help="重试之间的等待秒数")
    parser.add_argument("--test-db", action="store_true", 
                       help="测试数据库连接")
    parser.add_argument("--list", action="store_true", 
                       help="列出所有数字人")
    parser.add_argument("--show-prompt", action="store_true", 
                       help="显示完整提示词但不执行任务")
    parser.add_argument("--list-models", action="store_true",
                       help="列出支持的模型类型和名称")
    parser.add_argument("--model-details", action="store_true",
                       help="显示所有支持模型的详细信息和使用指南")
    parser.add_argument("--debug", action="store_true",
                       help="启用详细调试日志，帮助诊断问题")

    
    args = parser.parse_args()
    
    # 启用调试模式
    if args.debug:
        print("\n📝 调试模式已启用，将显示详细日志")
        # 设置环境变量使程序输出更多日志
        os.environ["BROWSER_USE_DEBUG"] = "true"
        os.environ["LANGCHAIN_TRACING"] = "true"
    
    # 处理特殊命令
    if args.model_details:
        print("\n📋 支持模型详细信息:")
        print("\n=== Gemini模型 ===")
        print("模型类型: gemini")
        print("可用模型:")
        print("  - gemini-2.0-flash: 速度快，成本低，适合大多数问卷场景")
        print("  - gemini-1.5-pro: 能力较强，处理复杂任务")
        print("如何使用: python testWenjuanFinal.py <ID> --model-type gemini --model gemini-2.0-flash --api-key YOUR_API_KEY")
        print("API密钥: 需要Google AI Studio API密钥")
        print("优势: 稳定，响应速度快")
        print("限制: 有API配额限制")
        
        # Gemini API支持信息
        print("\n=== Gemini API信息 ===")
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            print("✅ 检测到环境变量GOOGLE_API_KEY")
        else:
            print("❌ 未检测到环境变量GOOGLE_API_KEY")
            print("请通过--api-key参数提供API密钥，或设置GOOGLE_API_KEY环境变量")
        
        print("\n高级用法:")
        print("1. 无头模式运行: 添加 --headless 参数")
        print("2. 自动关闭浏览器: 添加 --auto-close 参数")
        print("3. 设置最大重试次数: --max-retries 5")
        print("4. 显示完整提示词: --show-prompt")
        return
    
    if args.list_models:
        print("\n📋 支持的模型列表:")
        for model_type, config in MODEL_CONFIGS.items():
            print(f"模型类型: {model_type}")
            print(f"  基础URL: {config['base_url'] or '默认'}")
            print(f"  可用模型: {', '.join(config['models'])}")
            print()
        return
    
    if args.test_db:
        test_db_connection()
        return
    
    if args.list:
        list_digital_humans()
        return
    
    # 检查数字人ID
    if not args.digital_human_id:
        print("❌ 错误: 必须提供数字人ID参数")
        print("例如: python testWenjuanFinal.py --digital-human-id 12")
        print("或简化方式: python testWenjuanFinal.py 12")
        return
    
    # 根据model_type自动设置模型和base_url（如果用户没有显式指定）
    if args.model_type in MODEL_CONFIGS:
        # 如果用户没有指定模型，使用该类型的第一个默认模型
        if not args.model:
            args.model = MODEL_CONFIGS[args.model_type]["models"][0]
            print(f"📝 自动选择默认模型: {args.model}")
        
        # 如果用户没有指定base_url，使用该类型的默认base_url
        if not args.base_url:
            args.base_url = MODEL_CONFIGS[args.model_type]["base_url"]
            if args.base_url:
                print(f"📝 自动选择默认服务器: {args.base_url}")
    
    # 设置默认API密钥，如果未指定
    if args.model_type == "gemini" and not args.api_key:
        # 检查环境变量
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            # 提供默认API密钥
            args.api_key = "AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8"
            print(f"📝 使用默认Gemini API密钥")
    
    # Gemini模式检查API密钥
    if args.model_type == "gemini" and not args.api_key and not os.environ.get("GOOGLE_API_KEY"):
        print("❌ 错误: 使用Gemini模型需要提供API密钥")
        print("可以通过--api-key参数提供，或设置GOOGLE_API_KEY环境变量")
        return
    
    # 不再支持其他模型类型
    if args.model_type != "gemini":
        print(f"❌ 错误: 不支持的模型类型: {args.model_type}")
        print("当前版本仅支持gemini模型")
        return
    
    # 获取数字人信息
    digital_human = get_digital_human_by_id(args.digital_human_id)
    if not digital_human:
        print(f"❌ 错误: 无法获取ID为{args.digital_human_id}的数字人信息")
        return
    
    # 生成完整提示词
    prompt, formatted_prompt = generate_complete_prompt(digital_human, args.url)
    
    # 打印完整提示词
    print("\n" + "=" * 40)
    print("📝 完整提示词")
    print("=" * 40)
    print(formatted_prompt)
    
    # 如果只显示提示词，不执行任务
    if args.show_prompt:
        print("\n仅显示提示词，不执行任务")
        return
    
    # 执行浏览器任务
    try:
        # 设置Gemini API相关环境变量
        if args.api_key:
            os.environ["GOOGLE_API_KEY"] = args.api_key
            
        # 如果启用了调试模式，检查相关库
        if args.debug:
            try:
                import importlib
                
                # 检查browser_use版本
                try:
                    import browser_use
                    print(f"✅ browser_use版本: {getattr(browser_use, '__version__', '未知')}")
                except (ImportError, AttributeError) as e:
                    print(f"❌ 获取browser_use版本失败: {e}")
            except Exception as e:
                print(f"❌ 依赖项检查失败: {e}")
        
        asyncio.run(run_browser_task(
            url=args.url, 
            prompt=prompt,
            formatted_prompt=formatted_prompt,
            model_type=args.model_type,
            model_name=args.model,
            api_key=args.api_key, 
            base_url=args.base_url,
            temperature=args.temperature,
            auto_close=args.auto_close,
            disable_memory=args.disable_memory,
            max_retries=args.max_retries,
            retry_delay=args.retry_delay,
            headless=args.headless
        ))
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 执行任务时出错: {error_msg}")
        
        if args.debug:
            import traceback
            print("\n📝 详细错误堆栈:")
            traceback.print_exc()
    finally:
        # 清理环境变量
        for env_var in ["BROWSER_USE_OLLAMA_ONLY", "BROWSER_USE_LLM_PROVIDER", 
                       "BROWSER_USE_LLM_MODEL", "BROWSER_USE_LLM_BASE_URL", 
                       "BROWSER_USE_LLM_TEMPERATURE", "BROWSER_USE_DISABLE_MEMORY",
                       "BROWSER_USE_DEBUG", "LANGCHAIN_TRACING"]:
            if env_var in os.environ:
                del os.environ[env_var]

if __name__ == "__main__":
    try:
        # 处理简化的命令行方式 python script.py <id>
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            # 备份原始参数
            original_args = sys.argv.copy()
            # 重置参数列表，只保留程序名
            sys.argv = [original_args[0]]
            # 添加--digital-human-id参数和ID值
            sys.argv.append('--digital-human-id')
            sys.argv.append(original_args[1])
            # 添加其他参数
            sys.argv.extend(original_args[2:])
            
        main()
    except KeyboardInterrupt:
        print("\n⚠️ 任务被用户中断")
        # 确保清理环境变量
        for env_var in ["BROWSER_USE_OLLAMA_ONLY", "BROWSER_USE_LLM_PROVIDER", 
                       "BROWSER_USE_LLM_MODEL", "BROWSER_USE_LLM_BASE_URL", 
                       "BROWSER_USE_LLM_TEMPERATURE", "BROWSER_USE_DISABLE_MEMORY"]:
            if env_var in os.environ:
                del os.environ[env_var]
    except Exception as e:
        print(f"\n❌ 执行过程中发生错误: {e}")
        # 确保清理环境变量
        for env_var in ["BROWSER_USE_OLLAMA_ONLY", "BROWSER_USE_LLM_PROVIDER", 
                       "BROWSER_USE_LLM_MODEL", "BROWSER_USE_LLM_BASE_URL", 
                       "BROWSER_USE_LLM_TEMPERATURE", "BROWSER_USE_DISABLE_MEMORY"]:
            if env_var in os.environ:
                del os.environ[env_var] 