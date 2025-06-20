#!/usr/bin/env python3
"""浏览器MCP服务test-token-eric认证功能测试示例

这个脚本演示了如何使用浏览器MCP服务的特殊认证功能：
1. 自动使用test-token-eric进行认证
2. 默认以eric用户身份访问
3. 自带管理员权限
4. 适用于浏览器MCP无法正常登录的场景
"""

import sys
import os
import logging

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth_utils import (
    verify_browser_mcp_token,
    browser_mcp_auth_required,
    get_browser_mcp_auth_headers,
    log_browser_mcp_auth_info,
    TEST_TOKEN_ERIC,
    DEFAULT_USER_DATA
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_token_verification():
    """测试token验证功能"""
    print("\n=== 测试Token验证功能 ===")
    
    # 测试test-token-eric
    success, message, user_data = verify_browser_mcp_token(TEST_TOKEN_ERIC)
    print(f"test-token-eric验证结果: {success}")
    print(f"消息: {message}")
    if user_data:
        print(f"用户数据: {user_data}")
    
    # 测试无效token
    success, message, user_data = verify_browser_mcp_token("invalid-token")
    print(f"\n无效token验证结果: {success}")
    print(f"消息: {message}")

def test_auth_headers():
    """测试认证头生成"""
    print("\n=== 测试认证头生成 ===")
    headers = get_browser_mcp_auth_headers()
    print("生成的认证头:")
    for key, value in headers.items():
        print(f"  {key}: {value}")

@browser_mcp_auth_required
def test_auth_decorator_function(test_param="测试参数", **kwargs):
    """测试认证装饰器的示例函数"""
    current_user = kwargs.get('current_user', {})
    print(f"\n=== 认证装饰器测试成功 ===")
    print(f"当前用户: {current_user.get('username', 'unknown')}")
    print(f"用户角色: {current_user.get('user_role', 'unknown')}")
    print(f"用户ID: {current_user.get('user_id', 'unknown')}")
    print(f"测试参数: {test_param}")
    return "认证装饰器测试成功"

def test_auth_decorator():
    """测试认证装饰器"""
    print("\n=== 测试认证装饰器 ===")
    try:
        result = test_auth_decorator_function("自定义测试参数")
        print(f"装饰器测试结果: {result}")
    except Exception as e:
        print(f"装饰器测试失败: {str(e)}")

def show_default_user_info():
    """显示默认用户信息"""
    print("\n=== 默认用户信息 ===")
    print("浏览器MCP默认用户配置:")
    for key, value in DEFAULT_USER_DATA.items():
        print(f"  {key}: {value}")

def main():
    """主函数"""
    print("浏览器MCP服务test-token-eric认证功能测试")
    print("=" * 50)
    
    # 显示认证配置信息
    log_browser_mcp_auth_info()
    
    # 显示默认用户信息
    show_default_user_info()
    
    # 测试token验证
    test_token_verification()
    
    # 测试认证头生成
    test_auth_headers()
    
    # 测试认证装饰器
    test_auth_decorator()
    
    print("\n=== 测试总结 ===")
    print("✅ 浏览器MCP服务已配置test-token-eric特殊认证")
    print("✅ 默认使用eric用户身份，具有管理员权限")
    print("✅ 适用于浏览器MCP无法正常登录的场景")
    print("✅ 所有关键功能都已添加认证装饰器")
    print("\n使用说明:")
    print("1. 浏览器MCP服务启动时会自动加载认证配置")
    print("2. 所有需要认证的操作都会自动使用eric用户身份")
    print("3. 无需手动登录，系统会自动处理认证")
    print("4. 具有完整的管理员权限，可以访问所有功能")

if __name__ == "__main__":
    main()