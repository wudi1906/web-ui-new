# AdsPower集成测试完整指南

## 🎯 测试目标

验证AdsPower浏览器环境隔离功能，确保每个数字人都有独立的"新电脑"环境，满足问卷网站的高要求。

## 📋 准备工作

### 1. 环境准备

#### 1.1 安装依赖
```bash
# 安装Python依赖
pip install -r requirements.txt

# 如果上面命令失败，手动安装
pip install pymysql requests selenium asyncio
```

#### 1.2 下载ChromeDriver
1. 访问 https://chromedriver.chromium.org/
2. 下载与你的Chrome版本匹配的ChromeDriver
3. 将chromedriver放到系统PATH中，或放到项目目录

#### 1.3 安装AdsPower
1. 访问 https://www.adspower.net/
2. 下载并安装AdsPower客户端
3. 注册账号并登录

### 2. 配置AdsPower

#### 2.1 启用API服务
1. 打开AdsPower客户端
2. 点击右上角"设置"图标
3. 左侧菜单选择"本地API"
4. 开启"启用本地API"开关
5. 确认端口为50325
6. 点击"保存"

#### 2.2 验证API连接
在浏览器中访问：
```
http://localhost:50325/api/v1/user/list?page=1&page_size=1
```
应该返回JSON格式的响应。

## 🚀 开始测试

### 第一步：基础连接测试

```bash
# 验证系统配置
python config.py
```

预期输出：
```
🔧 问卷系统配置
========================================
📋 系统配置摘要:
   数据库: 192.168.50.137:3306/wenjuan
   AdsPower: http://localhost:50325
   小社会系统: http://localhost:5001
   默认敢死队数量: 2
   默认目标团队数量: 10
   最大并发浏览器: 5
   代理启用: 否
   日志级别: INFO

========================================
✅ 配置验证通过
```

### 第二步：AdsPower基础功能测试

```bash
# 运行AdsPower集成测试
python test_adspower_integration.py
```

这个测试会：
1. 测试API连接
2. 创建3个测试浏览器配置文件
3. 启动浏览器
4. 生成手动测试指令

### 第三步：自动化指纹检测

```bash
# 运行自动化指纹检测
python browser_fingerprint_checker.py
```

这个测试会：
1. 自动创建3个浏览器
2. 通过Selenium连接每个浏览器
3. 自动检测各种指纹信息
4. 生成详细的分析报告

## 🔍 手动验证步骤

### 验证网站列表

在每个AdsPower浏览器中访问以下网站：

#### 1. IP地址检测
- https://whatismyipaddress.com/
- https://www.ip.cn/
- https://ipinfo.io/

**检查要点**：
- 每个浏览器显示的IP地址是否不同
- IP地址是否看起来真实（不是明显的数据中心IP）

#### 2. 浏览器指纹检测
- https://browserleaks.com/
- https://amiunique.org/
- https://coveryourtracks.eff.org/

**检查要点**：
- User-Agent字符串是否不同
- 浏览器版本信息是否合理
- 插件列表是否正常

#### 3. Canvas指纹检测
- https://browserleaks.com/canvas
- https://canvasblocker.kkapsner.de/test/

**检查要点**：
- 每个浏览器的Canvas指纹是否不同
- 指纹是否看起来自然（不是明显的噪声）

#### 4. WebRTC检测
- https://browserleaks.com/webrtc
- https://ipleak.net/

**检查要点**：
- 是否泄露真实IP地址
- WebRTC指纹是否不同

#### 5. 其他检测
- https://browserleaks.com/timezone （时区检测）
- https://browserleaks.com/geo （地理位置检测）

## 📊 评估标准

### ✅ 优秀标准（推荐用于生产）
- IP地址：每个浏览器完全不同
- User-Agent：每个浏览器完全不同
- Canvas指纹：每个浏览器完全不同
- WebGL指纹：每个浏览器完全不同
- 时区：与IP地址匹配
- 无WebRTC泄露

### ✅ 良好标准（可用于测试）
- IP地址：80%以上不同
- User-Agent：90%以上不同
- Canvas指纹：100%不同
- WebGL指纹：80%以上不同
- 基本无泄露

### ⚠️ 需要优化
- Canvas指纹：50-80%不同
- 部分指纹信息相同
- 轻微泄露问题

### ❌ 不合格（需要重新配置）
- 大量指纹信息相同
- 明显的机器特征
- 严重的隐私泄露

## 🛠️ 优化建议

### 如果指纹相似度过高

1. **调整指纹配置**
```python
# 在questionnaire_system.py中修改AdsPowerManager的配置
"fingerprint": {
    "canvas": "noise",  # 确保Canvas噪声开启
    "webgl": "noise",   # 确保WebGL噪声开启
    "ua": "random",     # 确保UA随机化
    "screen_resolution": "random",  # 随机分辨率
    # ... 其他配置
}
```

2. **配置代理IP**
```python
"proxy": {
    "proxy_type": "http",  # 或 "socks5"
    "proxy_host": "your-proxy-host",
    "proxy_port": "your-proxy-port",
    "proxy_user": "username",
    "proxy_password": "password"
}
```

### 如果浏览器启动失败

1. 检查系统资源（内存、CPU）
2. 关闭不必要的程序
3. 减少并发浏览器数量
4. 检查AdsPower客户端状态

### 如果API连接失败

1. 确认AdsPower客户端正在运行
2. 检查API服务是否启用
3. 确认端口号正确（默认50325）
4. 检查防火墙设置

## 📝 测试记录模板

### 测试环境
- 操作系统：
- AdsPower版本：
- Chrome版本：
- 测试时间：

### 测试结果

| 浏览器 | IP地址 | User-Agent前50字符 | Canvas指纹前20字符 | WebGL厂商 | 评估 |
|--------|--------|-------------------|-------------------|-----------|------|
| 浏览器1 |        |                   |                   |           |      |
| 浏览器2 |        |                   |                   |           |      |
| 浏览器3 |        |                   |                   |           |      |

### 总体评估
- [ ] 优秀 - 可用于生产环境
- [ ] 良好 - 可用于测试环境
- [ ] 需要优化 - 需要调整配置
- [ ] 不合格 - 需要重新配置

### 问题和建议
（记录发现的问题和改进建议）

## 🎯 下一步

测试通过后，我们将进入阶段2开发：
1. 集成Browser-use自动化框架
2. 实现敢死队答题功能
3. 开发知识库经验提取
4. 构建智能答题策略

## ❓ 常见问题

**Q: 为什么需要这么严格的测试？**
A: 问卷网站有先进的反机器人检测系统，如果被识别为机器人，会导致问卷失效，影响整个项目的成功率。

**Q: 可以跳过某些测试吗？**
A: 不建议。每个测试都验证了系统的关键功能，跳过可能导致后续问题。

**Q: 测试失败怎么办？**
A: 按照优化建议调整配置，重新测试。如果持续失败，可能需要升级AdsPower版本或更换代理服务。

**Q: 需要购买代理IP吗？**
A: 强烈建议购买高质量的住宅代理IP，这是确保隔离效果的关键因素。 