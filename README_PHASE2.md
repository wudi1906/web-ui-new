# 第二阶段：敢死队自动化系统

## 🎯 阶段目标

第二阶段实现敢死队自动答题功能，通过2人敢死队试探问卷，收集成功/失败经验，为后续精准投放提供数据支持。

## 📋 功能特性

### 🤖 敢死队自动化
- **智能数字人选择**：从小社会系统选择不同背景的数字人作为敢死队
- **多策略答题**：保守策略、激进策略、随机策略
- **并发执行**：多个敢死队成员同时答题，提高效率
- **实时监控**：答题过程实时监控和日志记录

### 🌐 浏览器环境隔离
- **独立浏览器**：每个敢死队成员使用独立的AdsPower浏览器
- **代理IP隔离**：集成青果隧道代理，实现IP地址隔离
- **指纹随机化**：不同的浏览器指纹，模拟真实用户

### 📊 页面内容抓取
- **智能识别**：自动识别问卷页面结构和问题类型
- **多类型支持**：单选题、多选题、文本输入题
- **截图记录**：每个步骤自动截图，便于调试和分析

### 💾 经验收集与分析
- **成功经验**：记录成功答题的策略和选择
- **失败分析**：分析失败原因和模式
- **知识库积累**：将经验存储到MySQL知识库
- **智能分析**：提取目标人群特征和答题模式

## 🏗️ 系统架构

```
第二阶段敢死队系统
├── ScoutAutomationSystem (敢死队自动化系统)
│   ├── 任务管理
│   ├── 敢死队选择
│   ├── 浏览器环境创建
│   └── 答题执行协调
├── BrowserUseIntegration (Browser-use集成)
│   ├── 页面导航
│   ├── 内容提取
│   ├── 自动答题
│   └── 截图记录
├── ScoutAnsweringStrategy (答题策略)
│   ├── 保守策略
│   ├── 激进策略
│   └── 随机策略
└── 数据持久化
    ├── 答题记录
    ├── 经验存储
    └── 知识库分析
```

## 📁 核心文件

### 主要模块
- **`phase2_scout_automation.py`** - 敢死队自动化核心模块
- **`browser_use_integration.py`** - Browser-use真实集成模块
- **`start_phase2_scout_system.py`** - 命令行启动脚本
- **`test_phase2_scout_system.py`** - 完整测试套件

### 依赖模块（第一阶段）
- **`questionnaire_system.py`** - 问卷管理系统
- **`final_browser_isolation_system.py`** - 浏览器隔离系统
- **`qinguo_tunnel_proxy_manager.py`** - 青果代理管理

## 🚀 快速开始

### 1. 环境准备

```bash
# 确保第一阶段环境已配置
# 安装Browser-use（如需真实集成）
pip install browser-use

# 确保数据库和AdsPower正常运行
```

### 2. 运行完整敢死队任务

```bash
# 运行完整任务流程
python start_phase2_scout_system.py \
  --url "https://www.wjx.cn/vm/example.aspx" \
  --scouts 2 \
  --full
```

### 3. 分步执行模式

```bash
# 1. 启动敢死队任务
python start_phase2_scout_system.py \
  --url "https://www.wjx.cn/vm/example.aspx" \
  --start

# 2. 执行答题
python start_phase2_scout_system.py --execute

# 3. 分析结果
python start_phase2_scout_system.py --analyze

# 4. 清理资源
python start_phase2_scout_system.py --cleanup
```

### 4. 测试模式

```bash
# 运行完整测试套件
python start_phase2_scout_system.py --test

# 或直接运行测试
python test_phase2_scout_system.py
```

## 📊 数据流程

### 1. 任务启动阶段
```
问卷URL → 创建任务 → 选择敢死队 → 创建浏览器环境 → 准备就绪
```

### 2. 答题执行阶段
```
页面导航 → 内容提取 → 策略选择 → 自动答题 → 结果记录
```

### 3. 经验分析阶段
```
收集经验 → 模式识别 → 人群分析 → 知识库更新 → 生成建议
```

## 🎭 答题策略

### 保守策略
- 选择最常见、最安全的选项
- 适用于风险规避型问卷
- 文本输入使用中性回答

### 激进策略
- 选择特殊、边缘的选项
- 测试问卷的包容性
- 文本输入使用特殊情况

### 随机策略
- 随机选择选项
- 增加答题多样性
- 发现意外的成功模式

## 📈 分析输出

### 目标人群特征
```json
{
  "age_range": "26-35岁",
  "occupation": "上班族",
  "education": "本科",
  "income": "中等收入"
}
```

### 成功模式
```json
[
  "保守策略在年龄问题上成功率高",
  "激进策略在职业问题上表现良好",
  "文本输入需要简短回答"
]
```

### 推荐查询
```
查询条件：年龄26-35岁，职业为上班族，教育程度本科以上的数字人
```

## 🔧 配置说明

### 数据库配置
```python
DB_CONFIG = {
    "host": "192.168.50.137",
    "port": 3306,
    "user": "root", 
    "password": "123456",
    "database": "wenjuan"
}
```

### AdsPower配置
```python
ADSPOWER_CONFIG = {
    "base_url": "http://localhost:50325",
    "api_key": "cd606f2e6e4558c9c9f2980e7017b8e9"
}
```

### 青果代理配置
```python
QINGUO_CONFIG = {
    "authkey": "A942CE1E",
    "authpwd": "B9FCD013057A",
    "tunnel_address": "tun-szbhry.qg.net:17790"
}
```

## 🧪 测试验证

### 测试覆盖范围
- ✅ 数据库连接测试
- ✅ 敢死队任务启动测试
- ✅ 敢死队答题执行测试
- ✅ 经验分析测试
- ✅ 资源清理测试
- ✅ 完整流程集成测试

### 成功标准
- 成功率 ≥ 80%：第二阶段基本完成
- 成功率 ≥ 60%：部分完成，需要优化
- 成功率 < 60%：需要重点修复

## 🔍 故障排除

### 常见问题

#### 1. 敢死队任务启动失败
```bash
# 检查数据库连接
mysql -h 192.168.50.137 -u root -p wenjuan

# 检查小社会系统
curl http://localhost:5001/health

# 检查AdsPower
curl http://localhost:50325/status
```

#### 2. 浏览器创建失败
```bash
# 检查AdsPower API Key
# 确认AdsPower客户端已启动
# 检查代理配置
```

#### 3. 答题执行失败
```bash
# 检查Browser-use安装
pip install browser-use

# 检查页面URL是否可访问
# 检查页面结构是否支持
```

#### 4. 经验分析失败
```bash
# 检查数据库表结构
# 确认答题记录已保存
# 检查知识库数据
```

## 📞 技术支持

### 日志查看
```bash
# 查看系统日志
tail -f /var/log/questionnaire_system.log

# 查看错误日志
grep ERROR /var/log/questionnaire_system.log
```

### 数据库查询
```sql
-- 查看任务状态
SELECT * FROM questionnaire_tasks ORDER BY created_at DESC LIMIT 10;

-- 查看答题记录
SELECT * FROM answer_records WHERE task_id = 'your_task_id';

-- 查看知识库
SELECT * FROM questionnaire_knowledge WHERE session_id = 'your_session_id';
```

## 🚀 下一阶段预告

第三阶段将实现：
- **知识库智能分析**：深度分析敢死队经验
- **目标团队选择**：基于分析结果选择最佳数字人
- **大规模自动化**：10人目标团队并发答题
- **成功率优化**：基于知识库的智能答题策略

---

## 📝 更新日志

### v2.0.0 (当前版本)
- ✅ 敢死队自动化系统
- ✅ Browser-use集成框架
- ✅ 多策略答题系统
- ✅ 经验收集和分析
- ✅ 完整测试套件

### 计划中的功能
- 🔄 真实Browser-use集成
- 🔄 智能页面结构识别
- �� 高级答题策略
- 🔄 实时监控面板 