# 增强版智能问卷自动填写系统 - 使用指南

## 🎯 系统概述

本系统是基于browser-use webui的智能问卷自动填写系统的增强版本，完美集成了`testWenjuanFinal.py`中已验证的browser-use API，提供真实的问卷填写能力。

### 核心特性
- ✅ **真实答题**: 基于testWenjuanFinal.py的完整Agent执行流程
- ✅ **多种模式**: 单个数字人、敢死队、批量自动化
- ✅ **Web界面**: 可视化管理和实时监控
- ✅ **知识库**: 详细的执行记录和经验积累
- ✅ **资源统计**: 实时的成本和消耗分析

## 🚀 快速开始

### 1. 系统检查
```bash
# 快速测试系统状态
python quick_enhanced_test.py
```

### 2. 启动Web界面
```bash
# 启动增强版Web界面
python start_enhanced_web_interface.py

# 访问 http://localhost:5002
```

### 3. 单个数字人答题
```bash
# 直接使用testWenjuanFinal.py（推荐）
python testWenjuanFinal.py --digital-human-id 1 --url "问卷URL"
```

## 📋 详细使用方法

### 方法一：直接使用testWenjuanFinal.py

这是最简单直接的方式，适合单个问卷的快速填写：

```bash
# 使用指定数字人填写问卷
python testWenjuanFinal.py --digital-human-id 1 --url "http://example.com/questionnaire"

# 查看可用的数字人
python -c "import testWenjuanFinal; print([testWenjuanFinal.get_digital_human_by_id(i) for i in range(1,6)])"
```

### 方法二：使用增强系统API

适合需要更多控制和集成的场景：

```python
import asyncio
from demo_enhanced_integration import EnhancedQuestionnaireSystem

async def main():
    system = EnhancedQuestionnaireSystem()
    
    # 单个数字人答题
    result = await system.run_single_digital_human_questionnaire(
        digital_human_id=1,
        questionnaire_url="http://example.com/questionnaire"
    )
    print(f"结果: {result}")

asyncio.run(main())
```

### 方法三：敢死队模式

适合探索性答题和知识库积累：

```python
import asyncio
from phase2_scout_automation import EnhancedScoutAutomationSystem

async def main():
    system = EnhancedScoutAutomationSystem()
    
    # 启动敢死队任务
    mission_id = await system.start_enhanced_scout_mission(
        questionnaire_url="http://example.com/questionnaire",
        scout_count=2
    )
    
    # 执行答题
    results = await system.execute_enhanced_scout_answering(mission_id)
    print(f"敢死队结果: {results}")
    
    # 清理资源
    await system.cleanup_scout_mission(mission_id)

asyncio.run(main())
```

### 方法四：批量自动化

适合大规模问卷填写：

```python
import asyncio
from demo_enhanced_integration import EnhancedQuestionnaireSystem

async def main():
    system = EnhancedQuestionnaireSystem()
    
    # 批量答题
    results = await system.run_batch_questionnaire_with_testWenjuan_data(
        questionnaire_url="http://example.com/questionnaire",
        digital_human_ids=[1, 2, 3, 4, 5]
    )
    print(f"批量结果: {results}")

asyncio.run(main())
```

### 方法五：Web界面操作

最用户友好的方式：

1. 启动Web界面：`python start_enhanced_web_interface.py`
2. 访问：http://localhost:5002
3. 选择任务类型：
   - **单个数字人答题**: 快速单任务
   - **敢死队任务**: 探索性多人答题
   - **批量自动化**: 大规模答题
   - **系统监控**: 查看任务状态和资源消耗

## 🔧 环境配置

### 必需依赖
```bash
pip install browser-use langchain_google_genai pymysql flask
```

### 环境变量
```bash
# 设置Google API密钥
export GOOGLE_API_KEY="your_gemini_api_key"
```

### 数据库配置
确保MySQL数据库配置正确（在`questionnaire_system.py`中的`DB_CONFIG`）

## 📊 系统架构

```
testWenjuanFinal.py (已验证的答题功能)
         ↓
EnhancedBrowserUseIntegration (基于testWenjuanFinal.py的API)
         ↓
EnhancedScoutAutomationSystem (增强敢死队系统)
         ↓
EnhancedQuestionnaireSystem (统一接口)
         ↓
Web界面 / 批量处理 / 敢死队任务
```

## 🧪 测试和验证

### 快速测试
```bash
# 运行快速测试
python quick_enhanced_test.py

# 运行完整测试
python test_enhanced_system.py

# 运行演示
python demo_enhanced_integration.py
```

### 测试结果示例
```
📈 测试统计:
  总测试数: 11
  通过测试: 11
  失败测试: 0
  成功率: 100.0%
```

## 📁 核心文件说明

| 文件 | 功能 | 用途 |
|------|------|------|
| `testWenjuanFinal.py` | 原始答题功能 | 单个数字人直接答题 |
| `enhanced_browser_use_integration.py` | 增强集成 | 基于testWenjuanFinal.py的API封装 |
| `phase2_scout_automation.py` | 敢死队系统 | 多人并发探索性答题 |
| `demo_enhanced_integration.py` | 演示系统 | 统一的问卷系统接口 |
| `web_interface.py` | Web界面 | 可视化管理和监控 |
| `start_enhanced_web_interface.py` | 启动脚本 | 智能启动和环境检查 |
| `quick_enhanced_test.py` | 快速测试 | 系统状态验证 |

## 🎛️ Web界面功能

### 主要页面
- **首页**: 系统状态和快速启动
- **单任务**: 单个数字人答题
- **敢死队**: 多人并发答题
- **批量任务**: 大规模自动化
- **任务监控**: 实时进度查看
- **知识库**: 历史记录和经验
- **资源消耗**: 成本统计分析

### API端点
- `POST /enhanced_single_task`: 启动单个数字人任务
- `POST /enhanced_batch_task`: 启动批量任务
- `POST /create_task`: 启动敢死队任务
- `GET /system_status`: 获取系统状态
- `GET /active_tasks`: 查看活跃任务
- `GET /task_history`: 查看任务历史

## 🔍 故障排除

### 常见问题

1. **browser-use导入失败**
   ```bash
   pip install browser-use
   ```

2. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 验证数据库配置信息

3. **GOOGLE_API_KEY未设置**
   ```bash
   export GOOGLE_API_KEY="your_api_key"
   ```

4. **testWenjuanFinal.py不可用**
   - 确保文件在当前目录
   - 检查文件权限

### 调试模式
```bash
# 启用详细日志
export PYTHONPATH=.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

## 📈 性能优化

### 建议配置
- **单任务**: 适合快速验证，资源消耗最小
- **敢死队**: 2-3人最佳，平衡探索效果和资源消耗
- **批量任务**: 根据服务器性能调整并发数

### 资源管理
- 系统自动记录资源消耗
- 支持成本优化建议
- 实时监控任务状态

## 🎯 最佳实践

1. **首次使用**: 先运行`quick_enhanced_test.py`验证环境
2. **单个测试**: 使用`testWenjuanFinal.py`进行快速验证
3. **批量处理**: 先用敢死队探索，再进行批量自动化
4. **监控管理**: 使用Web界面进行可视化管理
5. **资源优化**: 定期查看资源消耗统计

## 🔄 更新和维护

### 系统更新
```bash
# 拉取最新代码
git pull

# 重新测试
python quick_enhanced_test.py

# 重启服务
python start_enhanced_web_interface.py
```

### 数据备份
- 定期备份数据库
- 保存重要的任务记录
- 导出知识库数据

## 📞 支持和反馈

如果遇到问题或有改进建议，请：
1. 运行`quick_enhanced_test.py`获取系统状态
2. 查看日志文件了解详细错误信息
3. 检查环境配置和依赖安装

---

**系统已完全准备就绪，可以投入实际使用！** 🎉

选择最适合您需求的使用方式，开始您的智能问卷自动填写之旅！ 