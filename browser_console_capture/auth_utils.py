"""浏览器MCP服务认证工具
提供test-token-eric特殊处理逻辑，用于浏览器MCP无法登录的情况下默认授权
"""

import logging
from functools import wraps
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

# 默认用户信息 - 使用数据库中的真实eric用户
DEFAULT_USER_DATA = {
    'user_id': '8e8cc625-8d74-40bc-bd8c-fc1ec30499a9',  # 数据库中eric用户的真实ID
    'username': '凌亚峰',
    'password': 'welcome1',
    'login_name': 'eric',
    'user_role': 'admin',  # 主要角色，用户还具有普通用户和专家角色
    'phone': '13800000000',
    'is_active': True,
    'is_locked': False
}

# 特殊token标识
TEST_TOKEN_ERIC = 'test-token-eric'

def authenticate_user(username: str, password: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    用户名密码认证
    
    Args:
        username: 用户名或登录名
        password: 密码
        
    Returns:
        tuple: (success, message, user_data)
    """
    try:
        # 检查是否为默认eric用户
        if (username in [DEFAULT_USER_DATA['username'], DEFAULT_USER_DATA['login_name']] and 
            password == DEFAULT_USER_DATA['password']):
            logger.info(f"用户 {username} 密码认证成功")
            return True, "认证成功", DEFAULT_USER_DATA.copy()
        
        # 这里可以添加其他用户的认证逻辑
        # 例如：从数据库查询用户信息并验证密码
        
        logger.warning(f"用户 {username} 认证失败：用户名或密码错误")
        return False, "用户名或密码错误", None
        
    except Exception as e:
        logger.error(f"用户认证异常: {str(e)}")
        return False, f"认证失败: {str(e)}", None

def verify_browser_mcp_token(token: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    验证浏览器MCP token
    
    Args:
        token: 要验证的token
        
    Returns:
        tuple: (success, message, user_data)
    """
    try:
        # 检查是否为特殊的test-token-eric
        if token == TEST_TOKEN_ERIC:
            logger.info("检测到test-token-eric，使用默认eric用户授权")
            return True, "浏览器MCP默认授权成功", DEFAULT_USER_DATA.copy()
        
        # 对于其他token，可以在这里添加正常的JWT验证逻辑
        # 但由于浏览器MCP无法正常登录，我们暂时只支持test-token-eric
        logger.warning(f"浏览器MCP收到未知token: {token[:10]}...")
        return False, "浏览器MCP仅支持test-token-eric授权", None
        
    except Exception as e:
        logger.error(f"浏览器MCP token验证异常: {str(e)}")
        return False, f"Token验证失败: {str(e)}", None

def browser_mcp_auth_required(f):
    """
    浏览器MCP认证装饰器
    自动为浏览器MCP提供test-token-eric授权
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 浏览器MCP默认使用test-token-eric授权
            # 这样可以确保浏览器MCP始终有权限访问需要认证的功能
            success, message, user_data = verify_browser_mcp_token(TEST_TOKEN_ERIC)
            
            if not success:
                logger.error(f"浏览器MCP认证失败: {message}")
                raise Exception(f"浏览器MCP认证失败: {message}")
            
            # 将用户信息添加到kwargs中，供被装饰的函数使用
            kwargs['current_user'] = user_data
            logger.debug(f"浏览器MCP认证成功，用户: {user_data['username']}")
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"浏览器MCP认证装饰器异常: {str(e)}")
            raise Exception(f"浏览器MCP认证失败: {str(e)}")
    
    return decorated_function

def get_browser_mcp_auth_headers() -> Dict[str, str]:
    """
    获取浏览器MCP认证头
    用于向后端API发送请求时携带认证信息
    
    Returns:
        dict: 包含Authorization头的字典
    """
    return {
        'Authorization': f'Bearer {TEST_TOKEN_ERIC}',
        'Content-Type': 'application/json',
        'User-Agent': 'Browser-MCP-Service/1.0'
    }

def log_browser_mcp_auth_info():
    """
    记录浏览器MCP认证信息
    """
    logger.info("=== 浏览器MCP认证配置 ===")
    logger.info(f"默认用户: {DEFAULT_USER_DATA['username']}")
    logger.info(f"默认角色: {DEFAULT_USER_DATA['user_role']}")
    logger.info(f"特殊Token: {TEST_TOKEN_ERIC}")
    logger.info("浏览器MCP将自动使用eric用户身份进行认证")
    logger.info("==========================")
