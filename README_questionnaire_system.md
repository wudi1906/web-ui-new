# 智能问卷填写系统

## 🎯 系统概述

智能问卷填写系统是一个基于AI的自动化问卷填写解决方案，通过"敢死队试探 → 知识库积累 → 精准投放"的策略，实现高成功率的问卷自动填写。

## 🏗️ 系统架构

### 核心模块

1. **问卷主管 (QuestionnaireManager)** - 系统核心协调器
2. **AdsPower管理器 (AdsPowerManager)** - 多浏览器环境管理
3. **小社会系统客户端 (XiaosheSystemClient)** - 数字人查询接口
4. **知识库管理器 (QuestionnaireKnowledgeBase)** - 答题经验管理
5. **数据库管理器 (DatabaseManager)** - 数据持久化

### 工作流程

```
问卷URL输入 → 敢死队试探 → 经验分析 → 目标团队选择 → 大规模答题 → 结果统计
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+
- AdsPower浏览器
- 小社会系统运行中

### 安装依赖

```bash
pip install pymysql requests asyncio
```

### 配置系统

1. **数据库配置**
   ```python
   # config.py
   DATABASE_CONFIG = {
       "host": "192.168.50.137",
       "port": 3306,
       "user": "root",
       "password": "123456",
       "database": "wenjuan"
   }
   ```

2. **AdsPower配置**
   ```python
   ADSPOWER_CONFIG = {
       "base_url": "http://localhost:50325"
   }
   ```

3. **小社会系统配置**
   ```python
   XIAOSHE_CONFIG = {
       "base_url": "http://localhost:5001"
   }
   ```

### 运行测试

```bash
# 测试系统基础功能
python test_questionnaire_system.py

# 验证配置
python config.py
```

## 📊 数据库结构

### 核心表结构

1. **questionnaire_tasks** - 任务管理表
2. **persona_assignments** - 数字人分配表
3. **questionnaire_knowledge** - 问卷知识库表
4. **answer_records** - 答题记录表

### 表关系

```sql
questionnaire_tasks (1) → (N) persona_assignments
questionnaire_tasks (1) → (N) questionnaire_knowledge
persona_assignments (1) → (N) answer_records
```

## 🎮 使用示例

### 基础使用

```python
import asyncio
from questionnaire_system import QuestionnaireManager

async def main():
    # 创建问卷主管
    manager = QuestionnaireManager()
    
    # 创建问卷任务
    task = await manager.create_questionnaire_task(
        url="https://example.com/questionnaire",
        scout_count=2,      # 敢死队数量
        target_count=10     # 目标团队数量
    )
    
    # 选择敢死队
    scout_team = await manager.select_scout_team(task)
    
    # 准备浏览器环境
    browser_profiles = await manager.prepare_browser_environments(scout_team)
    
    # 清理资源
    await manager.cleanup_task_resources(task)

asyncio.run(main())
```

### 高级配置

```python
# 自定义配置
from config import get_config, QUESTIONNAIRE_CONFIG

# 修改默认配置
QUESTIONNAIRE_CONFIG["default_scout_count"] = 3
QUESTIONNAIRE_CONFIG["max_concurrent_browsers"] = 8

# 获取配置
db_config = get_config("database")
```

## 🔧 系统配置

### 环境变量

```bash
# 数据库配置
export DB_HOST=192.168.50.137
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=123456
export DB_NAME=wenjuan

# AdsPower配置
export ADSPOWER_URL=http://localhost:50325

# 小社会系统配置
export XIAOSHE_URL=http://localhost:5001

# 日志级别
export LOG_LEVEL=INFO
```

### 配置文件

所有配置集中在 `config.py` 文件中，支持环境变量覆盖。

## 🧪 测试指南

### 测试类型

1. **基础功能测试**
   - 数据库连接测试
   - 数据库表初始化测试
   - 问卷主管基础功能测试

2. **外部系统测试**
   - 小社会系统连接测试
   - AdsPower连接测试

3. **完整流程测试**
   - 端到端工作流程测试

### 运行测试

```bash
# 运行所有测试
python test_questionnaire_system.py

# 测试特定功能
python -c "
import asyncio
from test_questionnaire_system import test_database_connection
asyncio.run(test_database_connection())
"
```

## 📈 系统监控

### 日志系统

- 日志级别：INFO, DEBUG, WARNING, ERROR
- 日志文件：`logs/questionnaire_system.log`
- 日志轮转：最大10MB，保留5个备份

### 性能指标

- 任务成功率
- 平均答题时间
- 浏览器资源使用率
- 数据库连接池状态

## 🔒 安全考虑

### 数据安全

- 数据库连接加密
- 敏感信息环境变量存储
- 定期清理临时数据

### 访问控制

- API密钥验证（可选）
- 速率限制
- 允许域名白名单

### 隐私保护

- 答题数据匿名化
- 浏览器指纹随机化
- 代理IP轮换

## 🚨 故障排除

### 常见问题

1. **数据库连接失败**
   ```
   解决方案：检查数据库配置和网络连接
   ```

2. **AdsPower连接失败**
   ```
   解决方案：确保AdsPower软件运行并开启API服务
   ```

3. **小社会系统连接失败**
   ```
   解决方案：检查小社会系统是否正常运行
   ```

4. **浏览器创建失败**
   ```
   解决方案：检查AdsPower配额和系统资源
   ```

### 调试模式

```python
# 启用详细日志
import logging
logging.getLogger().setLevel(logging.DEBUG)

# 测试单个模块
from questionnaire_system import DatabaseManager
db = DatabaseManager(DATABASE_CONFIG)
db.init_knowledge_base_tables()
```

## 🔄 版本更新

### 当前版本：v1.0.0 (阶段1)

**已完成功能：**
- ✅ 基础架构搭建
- ✅ 数据库设计和初始化
- ✅ AdsPower API集成
- ✅ 小社会系统集成
- ✅ 问卷主管基础框架
- ✅ 配置管理系统
- ✅ 测试框架

**下一阶段计划：**
- 🔄 敢死队答题功能
- 🔄 知识库经验提取
- 🔄 Browser-use集成
- 🔄 答题结果分析

## 📞 技术支持

如有问题，请检查：
1. 系统配置是否正确
2. 依赖服务是否运行
3. 日志文件中的错误信息
4. 运行测试脚本验证功能

## 📄 许可证

本项目采用 MIT 许可证。 