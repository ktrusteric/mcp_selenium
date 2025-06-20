# 浏览器MCP服务 test-token-eric 认证功能说明

## 概述

浏览器MCP服务现在支持 `test-token-eric` 特殊认证机制，专门为解决浏览器MCP无法正常登录的问题而设计。该功能允许浏览器MCP服务默认以 `eric` 用户身份访问系统，并自带完整的管理员权限。

## 功能特点

### 🔐 自动认证
- **无需手动登录**: 浏览器MCP服务启动时自动配置认证
- **默认用户身份**: 自动使用 `eric` 用户身份
- **管理员权限**: 具有完整的系统管理员权限
- **特殊Token**: 使用 `test-token-eric` 作为认证标识

### 🛡️ 安全机制
- **专用认证**: 仅适用于浏览器MCP服务
- **权限控制**: 基于角色的访问控制
- **日志记录**: 完整的操作日志追踪
- **错误处理**: 完善的异常处理机制

## 技术实现

### 核心文件

1. **`auth_utils.py`** - 认证工具模块
   - `verify_browser_mcp_token()` - Token验证函数
   - `browser_mcp_auth_required` - 认证装饰器
   - `get_browser_mcp_auth_headers()` - 认证头生成
   - `DEFAULT_USER_DATA` - 默认用户配置

2. **`server.py`** - 主服务文件（已集成认证）
   - 导入认证工具
   - 为关键功能添加认证装饰器
   - 记录用户操作日志

3. **`test_auth_example.py`** - 测试示例
   - 验证认证功能
   - 演示使用方法

### 默认用户配置

```python
DEFAULT_USER_DATA = {
    'user_id': 'eric-browser-mcp-user',
    'username': 'eric',
    'login_name': 'eric',
    'user_role': 'admin',
    'phone': '13800000000',
    'is_active': True,
    'is_locked': False
}
```

### 特殊Token

```python
TEST_TOKEN_ERIC = 'test-token-eric'
```

## 使用方法

### 1. 启动浏览器MCP服务

```bash
cd /home/cooper/IntelligentPublicSentimentSystem/mcp_services/browser_console_capture
python3 server.py
```

服务启动时会自动显示认证配置信息：

```
=== 浏览器MCP认证配置 ===
默认用户: eric
默认角色: admin
特殊Token: test-token-eric
浏览器MCP将自动使用eric用户身份进行认证
==========================
```

### 2. 使用认证功能

所有需要认证的浏览器操作都会自动使用 `eric` 用户身份：

- `start_browser()` - 启动浏览器
- `navigate_to_url()` - 导航到URL
- `execute_javascript()` - 执行JavaScript
- 其他需要认证的操作

### 3. 日志记录

所有操作都会记录用户信息：

```
用户 eric 启动浏览器: chrome, 无头模式: True, 窗口大小: 1920,1080
用户 eric 导航到URL: https://example.com, 等待加载: True, 超时: 30秒
用户 eric 执行JavaScript: console.log('Hello World'), capture_console=True
```

### 4. 测试认证功能

运行测试脚本验证功能：

```bash
python3 test_auth_example.py
```

## API接口

### 认证验证

```python
from auth_utils import verify_browser_mcp_token

success, message, user_data = verify_browser_mcp_token('test-token-eric')
if success:
    print(f"认证成功，用户: {user_data['username']}")
```

### 认证装饰器

```python
from auth_utils import browser_mcp_auth_required

@browser_mcp_auth_required
def my_function(**kwargs):
    current_user = kwargs.get('current_user', {})
    print(f"当前用户: {current_user['username']}")
```

### 认证头生成

```python
from auth_utils import get_browser_mcp_auth_headers

headers = get_browser_mcp_auth_headers()
# 用于向后端API发送请求
```

## 与后端系统集成

### 后端认证支持

为了让后端系统识别 `test-token-eric`，需要在后端认证模块中添加相应的处理逻辑：

```python
# 在后端 auth_service.py 或相关认证模块中
def verify_token(token):
    if token == 'test-token-eric':
        # 返回eric用户信息
        return {
            'user_id': 'eric-browser-mcp-user',
            'username': 'eric',
            'user_role': 'admin',
            'is_active': True
        }
    # 其他正常token验证逻辑...
```

### API请求示例

浏览器MCP向后端发送请求时会自动携带认证头：

```python
import requests
from auth_utils import get_browser_mcp_auth_headers

headers = get_browser_mcp_auth_headers()
response = requests.get('http://localhost:5000/api/some-endpoint', headers=headers)
```

## 安全注意事项

1. **仅限开发环境**: `test-token-eric` 仅应在开发和测试环境中使用
2. **生产环境**: 生产环境应使用正常的JWT认证机制
3. **权限控制**: 虽然具有管理员权限，但仍需遵循最小权限原则
4. **日志监控**: 定期检查操作日志，确保没有异常活动

## 故障排除

### 常见问题

1. **认证失败**
   - 检查 `auth_utils.py` 是否正确导入
   - 确认 `TEST_TOKEN_ERIC` 常量值正确

2. **用户信息获取失败**
   - 检查 `DEFAULT_USER_DATA` 配置
   - 确认装饰器正确应用

3. **后端不识别token**
   - 确认后端已添加 `test-token-eric` 处理逻辑
   - 检查请求头格式是否正确

### 调试方法

1. **启用详细日志**
   ```python
   logging.getLogger().setLevel(logging.DEBUG)
   ```

2. **运行测试脚本**
   ```bash
   python3 test_auth_example.py
   ```

3. **检查认证流程**
   - 查看服务启动日志
   - 检查操作日志中的用户信息
   - 验证认证装饰器是否正常工作

## 更新日志

### v1.0.0 (当前版本)
- ✅ 实现 `test-token-eric` 特殊认证机制
- ✅ 添加默认 `eric` 用户配置
- ✅ 为关键功能添加认证装饰器
- ✅ 完善日志记录和错误处理
- ✅ 提供完整的测试示例

## 联系支持

如有问题或建议，请联系开发团队或查看项目文档。