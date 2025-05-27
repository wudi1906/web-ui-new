# AdsPower配置和测试指南

## 🔧 第一步：安装和配置AdsPower

### 1.1 下载安装
1. 访问 [AdsPower官网](https://www.adspower.net/)
2. 下载适合你系统的版本（Windows/Mac/Linux）
3. 安装并启动AdsPower客户端

### 1.2 启用API服务
1. 打开AdsPower客户端
2. 点击右上角的"设置"图标（齿轮图标）
3. 在左侧菜单中找到"本地API"
4. 确保"启用本地API"开关是打开状态
5. 检查端口号（默认50325）
6. 点击"保存"

### 1.3 验证API服务
在浏览器中访问：`http://localhost:50325/api/v1/user/list?page=1&page_size=1`
如果返回JSON数据，说明API服务正常。

## 🚀 第二步：运行测试脚本

### 2.1 检查配置
```bash
# 确保配置正确
python config.py
```

### 2.2 运行AdsPower集成测试
```bash
python test_adspower_integration.py
```

## 🔍 第三步：手动验证浏览器环境

### 3.1 测试网站列表
测试脚本会创建3个浏览器配置文件，请在每个浏览器中访问以下网站：

#### 基础检测网站
1. **IP地址检测**
   - https://whatismyipaddress.com/
   - https://www.ip.cn/
   - https://ipinfo.io/

2. **浏览器指纹检测**
   - https://browserleaks.com/
   - https://amiunique.org/
   - https://coveryourtracks.eff.org/

3. **Canvas指纹检测**
   - https://browserleaks.com/canvas
   - https://canvasblocker.kkapsner.de/test/

4. **WebRTC检测**
   - https://browserleaks.com/webrtc
   - https://ipleak.net/

5. **时区和地理位置**
   - https://browserleaks.com/timezone
   - https://browserleaks.com/geo

### 3.2 关键验证点

#### ✅ 合格标准
1. **IP地址**：每个浏览器显示不同的IP（如果配置了代理）
2. **User-Agent**：每个浏览器的UA字符串不同
3. **Canvas指纹**：每个浏览器的Canvas指纹不同
4. **WebGL指纹**：每个浏览器的WebGL指纹不同
5. **屏幕分辨率**：可以相同，但最好有差异
6. **时区**：根据IP地址自动匹配
7. **语言设置**：符合地区特征

#### ❌ 不合格情况
1. 多个浏览器显示相同的指纹
2. 指纹信息过于规律或明显是机器生成
3. WebRTC泄露真实IP地址
4. Canvas指纹完全相同
5. 浏览器行为异常（如缺少插件、异常的硬件信息）

## 🛡️ 第四步：增强隐私保护

### 4.1 配置代理IP
```python
# 在profile_config中添加代理配置
"proxy": {
    "proxy_type": "http",  # 或 "socks5"
    "proxy_host": "your-proxy-host",
    "proxy_port": "your-proxy-port",
    "proxy_user": "username",  # 如果需要认证
    "proxy_password": "password"  # 如果需要认证
}
```

### 4.2 优化指纹配置
```python
"fingerprint": {
    "automatic_timezone": 1,  # 根据IP自动设置时区
    "language": ["zh-CN", "zh", "en-US", "en"],
    "screen_resolution": "random",  # 随机分辨率
    "ua": "random",  # 随机User-Agent
    "webrtc": "proxy",  # WebRTC使用代理
    "location": "proxy",  # 地理位置使用代理
    "cookie": 1,
    "canvas": "noise",  # Canvas指纹添加噪声
    "webgl": "noise",  # WebGL指纹添加噪声
    "audio": "noise",  # 音频指纹添加噪声
    "media_devices": "noise",  # 媒体设备噪声
    "client_rects": "noise",  # 客户端矩形噪声
    "speech_voices": "random",  # 随机语音
    "hardware_concurrency": "random",  # 随机CPU核心数
    "device_memory": "random",  # 随机设备内存
    "platform": "random",  # 随机平台
    "do_not_track": "random"  # 随机DNT设置
}
```

## 📊 第五步：测试结果分析

### 5.1 记录测试数据
为每个浏览器记录以下信息：

| 浏览器 | IP地址 | User-Agent | Canvas指纹 | WebGL指纹 | 时区 | 分辨率 |
|--------|--------|------------|------------|-----------|------|--------|
| 浏览器1 | xxx.xxx.xxx.xxx | Mozilla/5.0... | abc123... | def456... | GMT+8 | 1920x1080 |
| 浏览器2 | yyy.yyy.yyy.yyy | Mozilla/5.0... | ghi789... | jkl012... | GMT+8 | 1920x1080 |
| 浏览器3 | zzz.zzz.zzz.zzz | Mozilla/5.0... | mno345... | pqr678... | GMT+8 | 1920x1080 |

### 5.2 评估隔离效果
1. **优秀**：所有指纹信息都不同，看起来像真实用户
2. **良好**：大部分指纹信息不同，少数相同
3. **一般**：部分指纹信息相同，需要优化配置
4. **差**：大量指纹信息相同，隔离失败

## ⚠️ 重要注意事项

### 安全建议
1. **代理IP**：强烈建议配置高质量的住宅代理IP
2. **指纹随机化**：确保每个配置文件的指纹都不同
3. **行为模拟**：避免机器化的操作模式
4. **定期更新**：定期更新配置文件和代理IP

### 常见问题
1. **API连接失败**：检查AdsPower是否启动，端口是否正确
2. **浏览器启动失败**：检查系统资源，关闭不必要的程序
3. **指纹相同**：调整fingerprint配置，增加随机性
4. **代理连接失败**：检查代理服务器状态和认证信息

## 🎯 下一步计划

测试通过后，我们将：
1. 集成Browser-use进行自动化操作
2. 实现敢死队答题功能
3. 添加更多的反检测机制
4. 优化性能和稳定性 