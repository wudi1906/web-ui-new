#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import argparse
from typing import Optional

from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from langchain_google_genai import ChatGoogleGenerativeAI

async def run_browser_task(url: str, prompt: str, api_key: str, model_name: str = "gemini-2.0-flash", auto_close: bool = False):
    """
    使用Browser-Use自动化执行指定的浏览器任务
    
    参数:
        url: 要访问的网站URL
        prompt: 提供给AI的提示词
        api_key: Gemini API密钥
        model_name: Gemini模型名称
        auto_close: 任务完成后是否自动关闭浏览器，默认为False（保持打开）
    """
    print(f"启动自动化任务...")
    print(f"目标URL: {url}")
    print(f"使用模型: {model_name}")
    print(f"任务完成后{'自动关闭' if auto_close else '保持打开'}浏览器")
    
    # 初始化浏览器
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
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.6,
        api_key=api_key,
    )
    print(f"已初始化LLM模型: {model_name}")
    
    # 创建并运行代理
    agent = BrowserUseAgent(
        task=prompt,
        llm=llm,
        browser=browser,
        browser_context=browser_context,
        use_vision=True,
        max_actions_per_step=20,
        tool_calling_method='auto',
        extend_system_message="确保完成所有问题的回答，直到表单填写完成。解析网页上所有可交互元素，并根据任务要求逐一完成。",
        source="testWenjuan"
    )
    
    # 首先导航到目标URL
    await browser_context.create_new_tab()
    await browser_context.navigate_to(url)
    print(f"已打开URL: {url}")
    
    # 运行代理执行任务
    try:
        print("开始执行代理任务...")
        print(f"提示词: {prompt}")
        print("等待代理完成任务，这可能需要一些时间...")
        result = await agent.run(max_steps=200)  # 增加最大步骤数，确保能完成所有操作
        print("任务完成!")
        print(f"执行结果: {result}")
        return result
    except Exception as e:
        print(f"任务执行过程中发生错误: {e}")
        raise
    finally:
        # 清理资源
        if auto_close:
            await browser_context.close()
            await browser.close()
            print("浏览器已关闭")
        else:
            print("浏览器保持打开状态，您可以手动关闭浏览器窗口")
            # 保持浏览器打开，但关闭代理以避免继续执行任务
            if agent:
                await agent.close()

def main():
    parser = argparse.ArgumentParser(description="自动化执行浏览器任务")
    parser.add_argument("--url", type=str, required=True, help="要访问的网站URL")
    parser.add_argument("--prompt", type=str, required=True, help="提供给AI的提示词")
    parser.add_argument("--api-key", type=str, required=True, help="Gemini API密钥")
    parser.add_argument("--model", type=str, default="gemini-2.0-flash", help="Gemini模型名称")
    parser.add_argument("--auto-close", action="store_true", help="任务完成后自动关闭浏览器")
    
    args = parser.parse_args()
    
    asyncio.run(run_browser_task(args.url, args.prompt, args.api_key, args.model, args.auto_close))

# 简易运行方式：直接设置参数并运行
def run_simple(url: str = "https://wjx.cn/vm/w4e8hc9.aspx", 
              prompt: str = "你现在是一名男性，名叫张三，今年36岁，生日是5月16日，大学老师，有体面的工作和收入，月薪15000，平时主要负责家里的日用品购买。主要在拼多多和淘宝、京东、抖音商城上购买。你现在打开：http://www.jinshengsurveys.com/?type=qtaskgoto&id=38752&token=FBC7E73EE2CE537C114EF3CCE3393DD5D2FFBC2BDDBE9F3CB4EEFB4B39D29D670EC6C5EC88BB86194F109B43670E8AB58386D6CE6525397A56B81C1CD5E1B48E。这个网站中有问卷题目，如果有不会的题目就选一个最符合你身份的那一项，所有有题目都要作答，不能有遗漏。你来进行作答并点击提交按钮或者下一题按钮，有的题目是每一页有若干题目，但是点击下一题之后跳转到下一页还有题目，所以你要一直重复答题、下一题操作。直到出现类似于“问卷作答完成”、“问卷已过期”、“调查已关闭”等类似的提示才停止操作，否则要一直循环答题。",
              api_key: str = "AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8",
              model: str = "gemini-2.0-flash",
              auto_close: bool = False):
    """
    简化的运行方式，直接设置参数并执行
    """
    asyncio.run(run_browser_task(url, prompt, api_key, model, auto_close))

if __name__ == "__main__":
    # 如果直接运行此脚本且不带参数，则使用简易运行方式
    import sys
    if len(sys.argv) == 1:
        print("使用预设参数运行...")
        run_simple()
    else:
        main() 