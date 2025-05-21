#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import argparse
import json
import pymysql
import pymysql.cursors
import time
import sys
from typing import Optional, Dict, Any, List

# 导入所需模块
try:
    from browser_use.browser.browser import Browser, BrowserConfig
    from browser_use.browser.context import BrowserContextConfig
    from src.agent.browser_use.browser_use_agent import BrowserUseAgent
    from langchain_google_genai import ChatGoogleGenerativeAI
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

async def run_browser_task(url: str, prompt: str, formatted_prompt: str, api_key: str, 
                          model_name: str = "gemini-2.0-flash", 
                          temperature: float = 0.5,
                          auto_close: bool = False):
    """
    使用Browser-Use自动化执行指定的浏览器任务
    
    参数:
        url: 要访问的网站URL
        prompt: 提供给AI的提示词
        formatted_prompt: 格式化后的提示词（用于显示）
        api_key: Gemini API密钥
        model_name: Gemini模型名称
        temperature: 模型温度参数
        auto_close: 任务完成后是否自动关闭浏览器
    """
    print("\n" + "=" * 40)
    print("🚀 启动自动化问卷填写任务")
    print("=" * 40)
    print(f"📝 使用模型: {model_name}")
    print(f"🌡️ 模型温度: {temperature}")
    print(f"🔗 目标URL: {url}")
    print(f"🤖 任务完成后{'自动关闭' if auto_close else '保持打开'}浏览器")
    print("\n📋 提示词概览:")
    print(formatted_prompt[:500] + "...\n")
    
    # 初始化浏览器
    print("🔧 初始化浏览器...")
    browser = Browser(
        config=BrowserConfig(
            headless=False,
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
    
    # 初始化Gemini LLM
    print(f"🧠 初始化LLM模型: {model_name}")
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
    )
    
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

务必坚持到问卷全部完成并提交!
"""

    # 创建并运行代理
    agent = BrowserUseAgent(
        task=prompt,
        llm=llm,
        browser=browser,
        browser_context=browser_context,
        use_vision=True,
        max_actions_per_step=20,  # 增加每步可执行的动作数
        tool_calling_method='auto',
        extend_system_message=system_message,
        source="wenjuan_automation"
    )
    
    # 运行代理执行任务
    try:
        print("\n🚀 开始执行代理任务...")
        print("⏳ 等待代理完成任务，这可能需要一些时间...\n")
        
        # 获取agent运行的支持参数
        import inspect
        run_params = inspect.signature(agent.run).parameters
        run_args = {}
        
        # 如果支持max_steps参数，添加较大的值确保能完成所有问题
        if 'max_steps' in run_params:
            run_args['max_steps'] = 200
            print("⚙️ 设置最大步数: 200")
        
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
        print(f"\n❌ 任务执行过程中发生错误: {e}")
        print("将保持浏览器打开状态，便于手动检查")
        raise
    finally:
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

def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description="数字人问卷自动填写工具")
    parser.add_argument("--url", type=str, default="https://wjx.cn/vm/w4e8hc9.aspx", 
                        help="要访问的问卷URL")
    parser.add_argument("--digital-human-id", "-id", type=int, 
                        help="数字人ID，从数据库获取对应数字人信息")
    parser.add_argument("--api-key", type=str, 
                       default="AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8",
                       help="Gemini API密钥")
    parser.add_argument("--model", type=str, default="gemini-2.0-flash", 
                       help="Gemini模型名称")
    parser.add_argument("--temperature", type=float, default=0.5, 
                       help="模型温度参数，控制创造性，值越大越有创造性，范围0-1")
    parser.add_argument("--auto-close", action="store_true", 
                       help="任务完成后自动关闭浏览器")
    parser.add_argument("--test-db", action="store_true", 
                       help="测试数据库连接")
    parser.add_argument("--list", action="store_true", 
                       help="列出所有数字人")
    parser.add_argument("--show-prompt", action="store_true", 
                       help="显示完整提示词但不执行任务")
    
    args = parser.parse_args()
    
    # 处理特殊命令
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
    asyncio.run(run_browser_task(
        url=args.url, 
        prompt=prompt,
        formatted_prompt=formatted_prompt,
        api_key=args.api_key, 
        model_name=args.model,
        temperature=args.temperature,
        auto_close=args.auto_close
    ))

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
    except Exception as e:
        print(f"\n❌ 执行过程中发生错误: {e}") 