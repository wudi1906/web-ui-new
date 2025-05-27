#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
问卷系统启动脚本
提供命令行接口来操作问卷系统
"""

import asyncio
import argparse
import sys
from questionnaire_system import QuestionnaireManager
from config import validate_config, print_config_summary

async def create_task(url: str, scout_count: int = 2, target_count: int = 10):
    """创建问卷任务"""
    print(f"🚀 创建问卷任务...")
    print(f"   URL: {url}")
    print(f"   敢死队数量: {scout_count}")
    print(f"   目标团队数量: {target_count}")
    
    try:
        manager = QuestionnaireManager()
        task = await manager.create_questionnaire_task(url, scout_count, target_count)
        
        print(f"✅ 任务创建成功!")
        print(f"   任务ID: {task.task_id}")
        print(f"   会话ID: {task.session_id}")
        
        return task
    except Exception as e:
        print(f"❌ 任务创建失败: {e}")
        return None

async def run_scout_phase(task_id: str):
    """运行敢死队阶段"""
    print(f"🔍 开始敢死队阶段...")
    # TODO: 实现敢死队答题逻辑
    print("⚠️ 敢死队功能尚未实现，将在阶段2开发")

async def run_target_phase(task_id: str):
    """运行目标团队阶段"""
    print(f"🎯 开始目标团队阶段...")
    # TODO: 实现目标团队答题逻辑
    print("⚠️ 目标团队功能尚未实现，将在阶段2开发")

async def show_task_status(task_id: str):
    """显示任务状态"""
    print(f"📊 任务状态查询...")
    # TODO: 实现任务状态查询
    print("⚠️ 状态查询功能尚未实现")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="智能问卷填写系统")
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 配置命令
    config_parser = subparsers.add_parser('config', help='显示系统配置')
    
    # 测试命令
    test_parser = subparsers.add_parser('test', help='运行系统测试')
    
    # 创建任务命令
    create_parser = subparsers.add_parser('create', help='创建问卷任务')
    create_parser.add_argument('url', help='问卷URL')
    create_parser.add_argument('--scout-count', type=int, default=2, help='敢死队数量')
    create_parser.add_argument('--target-count', type=int, default=10, help='目标团队数量')
    
    # 运行敢死队命令
    scout_parser = subparsers.add_parser('scout', help='运行敢死队阶段')
    scout_parser.add_argument('task_id', help='任务ID')
    
    # 运行目标团队命令
    target_parser = subparsers.add_parser('target', help='运行目标团队阶段')
    target_parser.add_argument('task_id', help='任务ID')
    
    # 查看状态命令
    status_parser = subparsers.add_parser('status', help='查看任务状态')
    status_parser.add_argument('task_id', help='任务ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 处理命令
    if args.command == 'config':
        print("🔧 系统配置信息")
        print("=" * 40)
        print_config_summary()
        print("\n" + "=" * 40)
        validate_config()
        
    elif args.command == 'test':
        print("🧪 运行系统测试...")
        import subprocess
        subprocess.run([sys.executable, 'test_questionnaire_system.py'])
        
    elif args.command == 'create':
        task = asyncio.run(create_task(args.url, args.scout_count, args.target_count))
        if task:
            print(f"\n💡 下一步操作:")
            print(f"   运行敢死队: python {sys.argv[0]} scout {task.task_id}")
            print(f"   查看状态: python {sys.argv[0]} status {task.task_id}")
        
    elif args.command == 'scout':
        asyncio.run(run_scout_phase(args.task_id))
        
    elif args.command == 'target':
        asyncio.run(run_target_phase(args.task_id))
        
    elif args.command == 'status':
        asyncio.run(show_task_status(args.task_id))

if __name__ == "__main__":
    print("🚀 智能问卷填写系统")
    print("=" * 50)
    main() 