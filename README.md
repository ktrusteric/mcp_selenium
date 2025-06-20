# MCP Browser Console Capture Service

## 概述

MCP Browser Console Capture Service 是一个基于 FastMCP 框架的浏览器自动化服务，专门用于智能舆情分析系统。该服务提供了完整的浏览器控制、JavaScript 执行、控制台日志捕获和页面交互功能。

## 技术栈

- **FastMCP**: MCP (Model Context Protocol) 服务框架
- **Selenium**: 浏览器自动化工具
- **Chrome**: 主要支持的浏览器
- **ChromeDriver**: Chrome 浏览器驱动程序
- **Python 3.10.12+**: 运行环境

## 核心功能

### 🌐 浏览器控制
- 启动和管理 Chrome/Firefox 浏览器实例
- 页面导航和 URL 访问
- 窗口大小调整和管理
- 多会话支持

### 📝 JavaScript 执行
- 在页面中执行自定义 JavaScript 代码
- 获取执行结果和返回值
- 支持异步脚本执行

### 📊 控制台日志捕获
- 实时捕获浏览器控制台日志
- 支持多种日志级别（INFO、WARNING、ERROR、DEBUG）
- 结构化日志数据返回
- 可配置日志数量限制（最多10000条）

### 🎯 页面交互
- 元素点击和文本输入
- 元素等待和条件检查
- 页面截图功能
- Cookie 和页面信息获取

### 🔐 认证机制
- 支持 `test-token-eric` 特殊认证
- 默认管理员权限
- 完整的操作日志记录

## 环境配置步骤

### 1. 系统要求

```bash
# Ubuntu/Debian 系统
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# 安装必要的系统依赖
sudo apt install -y wget unzip curl
```

### 2. Chrome 浏览器 和  ChromeDriver 安装

**重要：** 本服务需要特定路径的 Chrome 浏览器


### 3. ChromeDriver 安装

**重要：** ChromeDriver 版本必须与 Chrome 版本匹配

Google Chrome for Testing 137.0.7151.119 
ChromeDriver 137.0.7151.119 (e0ac9d12dff5f2d33c935958b06bf1ded7f1c08c-refs/branch-heads/7151@{#2356})

请自行下载安装：json 源地址
https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json



# 验证安装
/opt/chromedriver-linux64/chromedriver --version
/opt/chrome-linux64/chrome --version

配置到对应路径到server.py

### 4. Python 环境配置

# 创建虚拟环境
```
python3 -m venv venv
source venv/bin/activate
```

# 安装依赖
```
pip install -r requirements.txt
```

# 安装 FastMCP（如果不在 requirements.txt 中）
```
pip install fastmcp
```

### 5. 配置文件设置

确保 `config.json` 中的路径配置正确：

```json
{
  "mcpServers": {
    "browser-console-capture": {
      "command": "/home/cooper/IntelligentPublicSentimentSystem/mcp_services/browser_console_capture/server.py",
      "args": [],
      "env": {
        "PYTHONPATH": "/home/cooper/IntelligentPublicSentimentSystem"
      }
    }
  }
}
```

### 6. 权限设置

```bash
# 确保 Chrome 和 ChromeDriver 有执行权限
sudo chmod +x /opt/chrome-linux64/chrome
sudo chmod +x /opt/chromedriver-linux64/chromedriver

# 创建必要的目录
mkdir -p ./screenshots
mkdir -p ./logs
```

### 7. 环境验证

```bash
# 测试 Chrome 启动
/opt/chrome-linux64/chrome --version --no-sandbox

# 测试 ChromeDriver
/opt/chromedriver-linux64/chromedriver --version

# 测试 Python 依赖
python3 -c "import selenium; print('Selenium version:', selenium.__version__)"
python3 -c "import fastmcp; print('FastMCP imported successfully')"
```

## 启动服务
IntelligentPublicSentimentSystem/mcp_services/browser_console_capture$ fastmcp run server.py:mcp
2025-06-20 03:02:09,006 - server_module - INFO - 日志系统初始化完成，配置已加载
2025-06-20 03:02:09,010 - auth_utils - INFO - === 浏览器MCP认证配置 ===
2025-06-20 03:02:09,010 - auth_utils - INFO - 默认用户: eric
2025-06-20 03:02:09,010 - auth_utils - INFO - 默认角色: admin
2025-06-20 03:02:09,010 - auth_utils - INFO - 特殊Token: test-token-eric
2025-06-20 03:02:09,011 - auth_utils - INFO - 浏览器MCP将自动使用eric用户身份进行认证
2025-06-20 03:02:09,011 - auth_utils - INFO - ==========================
2025-06-20 03:02:09,011 - server_module - INFO - 初始化FastMCP服务器...
2025-06-20 03:02:09,016 - server_module - INFO - FastMCP服务器初始化完成
2025-06-20 03:02:09,017 - server_module - INFO - 状态字典初始化完成

## 使用示例

### 基本浏览器操作

```python
# 启动浏览器
start_browser(browser_type="chrome", headless=False)

# 导航到页面
navigate_to_url("https://example.com")

# 执行 JavaScript
execute_javascript("console.log('Hello World'); return document.title;")

# 获取控制台日志
get_console_logs(level="ALL", limit=100)
```

### 页面交互

```python
# 点击元素
click_element("#submit-button", by="css")

# 输入文本
input_text("#search-input", "搜索内容", by="css")

# 等待元素
wait_for_element(".loading-complete", condition="visible")

# 截图
take_screenshot("page_screenshot.png", full_page=True)
```

## 配置说明

### 浏览器配置

- `chrome_binary_path`: Chrome 浏览器可执行文件路径
- `chromedriver_path`: ChromeDriver 可执行文件路径
- `headless`: 是否以无头模式运行
- `window_size`: 浏览器窗口大小

### 日志配置

- `log_level`: 日志级别（DEBUG, INFO, WARNING, ERROR）
- `log_file`: 日志文件路径
- `max_log_size`: 最大日志文件大小

### 性能配置

- `page_load_timeout`: 页面加载超时时间
- `script_timeout`: 脚本执行超时时间
- `implicit_wait`: 隐式等待时间

### MCP工具函数

| 函数名 | 描述 | 参数 |
|--------|------|------|
| `start_browser` | 启动浏览器实例 | `browser_type`, `headless`, `window_width`, `window_height` |
| `navigate_to_url` | 导航到指定URL | `url`, `wait_for_load` |
| `execute_javascript` | 执行JavaScript代码 | `script`, `capture_console` |
| `get_console_logs` | 获取控制台日志 | `level`, `limit`, `clear_after_get` |
| `click_element` | 点击页面元素 | `selector`, `by`, `timeout` |
| `input_text` | 输入文本 | `selector`, `text`, `by`, `clear_first` |
| `take_screenshot` | 截取页面截图 | `filename`, `full_page`, `element_selector` |
| `close_browser` | 关闭浏览器实例 | 无 |

## 安全注意事项

1. **生产环境配置**
   - 使用 headless 模式，默认为 True
   - 限制网络访问
   - 配置防火墙规则

2. **认证安全**
   - `test-token-eric` 
   需要有token的情况

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目 Issues: [GitHub Issues]()
- 邮箱: [项目邮箱]()
- 文档: [在线文档]()
