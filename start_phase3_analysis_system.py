#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第三阶段知识库分析系统启动脚本
提供命令行界面来分析问卷画像和选择目标团队
"""

import asyncio
import argparse
import json
import sys
import logging
from datetime import datetime
from typing import Dict, List

from phase3_knowledge_analysis import Phase3KnowledgeAnalysisSystem, QuestionnaireProfile, PersonaMatch

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase3CommandLineInterface:
    """第三阶段命令行界面"""
    
    def __init__(self):
        self.analysis_system = Phase3KnowledgeAnalysisSystem()
        self.current_profile = None
        self.current_matches = None
    
    async def analyze_questionnaire_profile(self, session_id: str, questionnaire_url: str):
        """分析问卷画像"""
        print(f"📊 分析问卷画像")
        print(f"🆔 会话ID: {session_id}")
        print(f"📋 问卷URL: {questionnaire_url}")
        print("-" * 50)
        
        try:
            profile = await self.analysis_system.analyzer.analyze_questionnaire_profile(
                session_id, questionnaire_url
            )
            
            self.current_profile = profile
            
            print(f"✅ 问卷画像分析完成!")
            print(f"\n📊 问卷画像详情:")
            print(f"  🎯 难度等级: {profile.difficulty_level}")
            print(f"  📈 置信度分数: {profile.confidence_score:.2f}")
            print(f"  📝 样本数量: {profile.sample_size}")
            
            print(f"\n👥 目标人群特征:")
            demographics = profile.target_demographics
            age_range = demographics.get("age_range", {})
            if age_range:
                print(f"  📅 年龄范围: {age_range.get('min', '未知')}-{age_range.get('max', '未知')}岁")
                if age_range.get("avg"):
                    print(f"  📊 平均年龄: {age_range['avg']:.1f}岁")
            
            genders = demographics.get("preferred_genders", [])
            if genders:
                print(f"  👤 偏好性别: {', '.join(genders)}")
            
            professions = demographics.get("preferred_professions", [])
            if professions:
                print(f"  💼 偏好职业: {', '.join(professions[:5])}")  # 显示前5个
            
            print(f"\n✅ 成功模式 ({len(profile.success_patterns)}个):")
            for i, pattern in enumerate(profile.success_patterns[:3], 1):
                print(f"  {i}. {pattern}")
            
            print(f"\n❌ 失败模式 ({len(profile.failure_patterns)}个):")
            for i, pattern in enumerate(profile.failure_patterns[:3], 1):
                print(f"  {i}. {pattern}")
            
            print(f"\n💡 推荐策略 ({len(profile.recommended_strategies)}个):")
            for i, strategy in enumerate(profile.recommended_strategies, 1):
                print(f"  {i}. {strategy}")
            
            return profile
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            return None
    
    async def select_target_team(self, target_count: int = 10):
        """选择目标团队"""
        if not self.current_profile:
            print("❌ 请先分析问卷画像")
            return None
        
        print(f"🎯 选择目标团队")
        print(f"👥 目标人数: {target_count}")
        print("-" * 50)
        
        try:
            matches = await self.analysis_system.matching_engine.find_best_target_team(
                self.current_profile, target_count
            )
            
            self.current_matches = matches
            
            if matches:
                print(f"✅ 目标团队选择完成!")
                print(f"👥 找到 {len(matches)} 个匹配的数字人")
                
                # 计算统计信息
                avg_match_score = sum(m.match_score for m in matches) / len(matches)
                avg_predicted_success = sum(m.predicted_success_rate for m in matches) / len(matches)
                
                print(f"\n📊 团队统计:")
                print(f"  📈 平均匹配度: {avg_match_score:.2f}")
                print(f"  🎯 预期成功率: {avg_predicted_success:.2%}")
                
                print(f"\n👤 团队成员详情:")
                for i, match in enumerate(matches[:5], 1):  # 显示前5个
                    print(f"  {i}. {match.persona_name} (ID: {match.persona_id})")
                    print(f"     📊 匹配度: {match.match_score:.2f}")
                    print(f"     🎯 预期成功率: {match.predicted_success_rate:.2%}")
                    print(f"     💡 匹配原因: {', '.join(match.match_reasons[:2])}")
                
                if len(matches) > 5:
                    print(f"  ... 还有 {len(matches) - 5} 个成员")
                
                return matches
            else:
                print("❌ 没有找到合适的目标团队成员")
                return None
                
        except Exception as e:
            print(f"❌ 选择目标团队失败: {e}")
            return None
    
    async def generate_analysis_report(self):
        """生成分析报告"""
        if not self.current_profile or not self.current_matches:
            print("❌ 请先完成问卷分析和团队选择")
            return None
        
        print(f"📈 生成分析报告")
        print("-" * 50)
        
        try:
            report = self.analysis_system._generate_analysis_report(
                self.current_profile, self.current_matches
            )
            
            print(f"✅ 分析报告生成完成!")
            
            # 显示报告内容
            questionnaire_analysis = report.get("questionnaire_analysis", {})
            team_selection = report.get("team_selection", {})
            recommendations = report.get("recommendations", [])
            
            print(f"\n📊 问卷分析结果:")
            print(f"  🎯 难度等级: {questionnaire_analysis.get('difficulty_level', '未知')}")
            print(f"  📈 置信度分数: {questionnaire_analysis.get('confidence_score', 0):.2f}")
            print(f"  📝 样本数量: {questionnaire_analysis.get('sample_size', 0)}")
            print(f"  ✅ 成功模式: {questionnaire_analysis.get('success_patterns_count', 0)}个")
            print(f"  ❌ 失败模式: {questionnaire_analysis.get('failure_patterns_count', 0)}个")
            print(f"  💡 推荐策略: {questionnaire_analysis.get('strategies_count', 0)}个")
            
            print(f"\n👥 团队选择结果:")
            print(f"  🎯 需求人数: {team_selection.get('requested_count', 0)}")
            print(f"  ✅ 找到人数: {team_selection.get('found_count', 0)}")
            print(f"  📊 平均匹配度: {team_selection.get('avg_match_score', 0):.2f}")
            print(f"  🎯 平均预期成功率: {team_selection.get('avg_predicted_success', 0):.2%}")
            
            top_reasons = team_selection.get("top_match_reasons", [])
            if top_reasons:
                print(f"\n🔍 主要匹配原因:")
                for reason_info in top_reasons[:3]:
                    print(f"  • {reason_info['reason']} ({reason_info['count']}次)")
            
            print(f"\n💡 系统建议:")
            for i, recommendation in enumerate(recommendations, 1):
                print(f"  {i}. {recommendation}")
            
            print(f"\n📅 报告生成时间: {report.get('generated_at', '未知')}")
            
            return report
            
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")
            return None
    
    async def run_full_analysis(self, session_id: str, questionnaire_url: str, target_count: int = 10):
        """运行完整分析流程"""
        print(f"🎯 运行完整知识库分析流程")
        print(f"🆔 会话ID: {session_id}")
        print(f"📋 问卷URL: {questionnaire_url}")
        print(f"👥 目标团队人数: {target_count}")
        print("=" * 60)
        
        try:
            # 1. 分析问卷画像
            print(f"\n📍 阶段1: 分析问卷画像")
            profile = await self.analyze_questionnaire_profile(session_id, questionnaire_url)
            if not profile:
                return False
            
            # 2. 选择目标团队
            print(f"\n📍 阶段2: 选择目标团队")
            matches = await self.select_target_team(target_count)
            if not matches:
                return False
            
            # 3. 生成分析报告
            print(f"\n📍 阶段3: 生成分析报告")
            report = await self.generate_analysis_report()
            if not report:
                return False
            
            print(f"\n🎉 完整知识库分析流程执行成功!")
            print(f"📊 分析总结:")
            print(f"  - 问卷难度: {profile.difficulty_level}")
            print(f"  - 置信度: {profile.confidence_score:.2f}")
            print(f"  - 目标团队: {len(matches)}人")
            print(f"  - 平均匹配度: {sum(m.match_score for m in matches) / len(matches):.2f}")
            print(f"  - 预期成功率: {sum(m.predicted_success_rate for m in matches) / len(matches):.2%}")
            
            return True
            
        except Exception as e:
            print(f"❌ 完整分析流程异常: {e}")
            return False
    
    def show_help(self):
        """显示帮助信息"""
        print(f"🤖 第三阶段知识库分析系统 - 使用指南")
        print("=" * 60)
        print(f"📋 功能说明:")
        print(f"  本系统基于敢死队经验，智能分析问卷特征")
        print(f"  生成问卷画像，选择最佳目标团队")
        print(f"  为大规模自动化答题提供精准指导")
        
        print(f"\n🚀 使用方法:")
        print(f"  1. 完整分析模式:")
        print(f"     python start_phase3_analysis_system.py \\")
        print(f"       --session-id <会话ID> \\")
        print(f"       --url <问卷URL> \\")
        print(f"       --target-count 10 \\")
        print(f"       --full")
        
        print(f"  2. 分步执行模式:")
        print(f"     python start_phase3_analysis_system.py \\")
        print(f"       --session-id <会话ID> --url <问卷URL> --analyze")
        print(f"     python start_phase3_analysis_system.py --select --target-count 10")
        print(f"     python start_phase3_analysis_system.py --report")
        
        print(f"  3. 测试模式:")
        print(f"     python start_phase3_analysis_system.py --test")
        
        print(f"\n⚙️ 参数说明:")
        print(f"  --session-id ID    敢死队会话ID")
        print(f"  --url URL          问卷URL地址")
        print(f"  --target-count N   目标团队人数 (默认: 10)")
        print(f"  --full             运行完整分析流程")
        print(f"  --analyze          分析问卷画像")
        print(f"  --select           选择目标团队")
        print(f"  --report           生成分析报告")
        print(f"  --test             运行测试模式")
        print(f"  --help             显示帮助信息")
        
        print(f"\n💡 示例:")
        print(f"  # 基于第二阶段敢死队结果进行完整分析")
        print(f"  python start_phase3_analysis_system.py \\")
        print(f"    --session-id task_1748395420_459dd4bc \\")
        print(f"    --url https://www.wjx.cn/vm/example.aspx \\")
        print(f"    --target-count 10 --full")
        
        print(f"\n📞 技术支持:")
        print(f"  如遇问题，请检查:")
        print(f"  1. 第二阶段敢死队是否已完成")
        print(f"  2. 数据库中是否有经验数据")
        print(f"  3. 小社会系统是否正常运行")
        print(f"  4. 会话ID是否正确")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="第三阶段知识库分析系统")
    
    # 基本参数
    parser.add_argument("--session-id", type=str, help="敢死队会话ID")
    parser.add_argument("--url", type=str, help="问卷URL地址")
    parser.add_argument("--target-count", type=int, default=10, help="目标团队人数 (默认: 10)")
    
    # 操作模式
    parser.add_argument("--full", action="store_true", help="运行完整分析流程")
    parser.add_argument("--analyze", action="store_true", help="分析问卷画像")
    parser.add_argument("--select", action="store_true", help="选择目标团队")
    parser.add_argument("--report", action="store_true", help="生成分析报告")
    parser.add_argument("--test", action="store_true", help="运行测试模式")
    parser.add_argument("--help-guide", action="store_true", help="显示详细帮助")
    
    args = parser.parse_args()
    
    cli = Phase3CommandLineInterface()
    
    try:
        if args.help_guide:
            cli.show_help()
            return
        
        if args.test:
            print("🧪 启动测试模式...")
            from test_phase3_analysis_system import Phase3TestSuite
            test_suite = Phase3TestSuite()
            await test_suite.run_all_tests()
            return
        
        if args.full:
            if not args.session_id or not args.url:
                print("❌ 完整分析模式需要提供会话ID和问卷URL")
                print("   使用 --session-id <ID> --url <URL>")
                return
            
            success = await cli.run_full_analysis(args.session_id, args.url, args.target_count)
            if success:
                print("\n🎉 知识库分析全部完成!")
            else:
                print("\n❌ 知识库分析执行失败")
            return
        
        if args.analyze:
            if not args.session_id or not args.url:
                print("❌ 分析模式需要提供会话ID和问卷URL")
                print("   使用 --session-id <ID> --url <URL>")
                return
            
            profile = await cli.analyze_questionnaire_profile(args.session_id, args.url)
            if profile:
                print(f"\n💾 问卷画像已保存，可使用以下命令继续:")
                print(f"python start_phase3_analysis_system.py --select --target-count {args.target_count}")
            return
        
        if args.select:
            matches = await cli.select_target_team(args.target_count)
            if matches:
                print(f"\n💾 目标团队已选择，可使用以下命令生成报告:")
                print(f"python start_phase3_analysis_system.py --report")
            return
        
        if args.report:
            report = await cli.generate_analysis_report()
            if report:
                print(f"\n✅ 分析报告生成完成")
            return
        
        # 默认显示帮助
        cli.show_help()
        
    except KeyboardInterrupt:
        print("\n⚠️ 操作被用户中断")
    except Exception as e:
        print(f"\n❌ 系统异常: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 