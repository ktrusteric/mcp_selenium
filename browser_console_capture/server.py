#!/usr/bin/env python3
"""
Browser Console Capture MCP Server

优化版本 - 基于Chrome DevTools Console API标准
增强的日志捕获、JavaScript执行和页面元素交互功能
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局状态管理
state = {
    "drivers": {},  # session_id -> driver
    "current_session": None,
    "auth_users": {"eric": "welcome1"}  # 简单的用户认证
}

# MCP服务器实例
mcp = Server("browser-console-capture")

def browser_mcp_auth_required(func):
    """装饰器：要求浏览器MCP认证"""
    def wrapper(*args, **kwargs):
        # 简单的认证检查
        current_user = kwargs.get('current_user', {})
        if not current_user.get('authenticated', False):
            return {
                "success": False,
                "error": "Authentication required",
                "message": "请先使用authenticate_user工具进行认证"
            }
        return func(*args, **kwargs)
    return wrapper

def get_driver(session_id: str = None) -> webdriver.Chrome:
    """获取或创建WebDriver实例"""
    if session_id is None:
        session_id = state["current_session"]
    
    if session_id and session_id in state["drivers"]:
        return state["drivers"][session_id]
    
    # 创建新的driver
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 启用日志记录
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--log-level=0")
    chrome_options.set_capability('goog:loggingPrefs', {
        'browser': 'ALL',
        'driver': 'ALL',
        'performance': 'ALL'
    })
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 存储driver
    if session_id is None:
        session_id = f"session_{int(time.time())}"
    
    state["drivers"][session_id] = driver
    state["current_session"] = session_id
    
    logger.info(f"创建新的浏览器会话: {session_id}")
    return driver

def parse_console_message(message: str) -> dict:
    """
    Parse console message to extract useful information
    Based on Chrome DevTools Console API format
    """
    try:
        # 常见的console消息格式解析
        if message.startswith('"'):
            # 简单字符串消息
            return {
                "type": "string",
                "clean_message": message.strip('"'),
                "source": "console.log"
            }
        elif "console-api" in message:
            # Console API调用
            parts = message.split('"')
            if len(parts) >= 2:
                return {
                    "type": "console_api",
                    "clean_message": parts[1],
                    "source": "console API"
                }
        elif "Uncaught" in message:
            # JavaScript错误
            return {
                "type": "javascript_error",
                "clean_message": message,
                "source": "JavaScript Runtime"
            }
        elif "Failed to load resource" in message:
            # 资源加载错误
            return {
                "type": "resource_error",
                "clean_message": message,
                "source": "Network"
            }
        else:
            # 其他类型消息
            return {
                "type": "other",
                "clean_message": message,
                "source": "browser"
            }
    except Exception:
        return {
            "type": "unknown",
            "clean_message": message,
            "source": "unknown"
        }

def get_console_logs_internal(level: str = "ALL", limit: int = 1000, format_output: bool = True):
    """
    Internal function to get console logs (used by other functions)
    """
    try:
        driver = get_driver()
        
        # Get browser logs with enhanced error handling
        all_logs = []
        log_types = ['browser']  # 主要关注browser日志，其他类型通常噪音较多
        
        for log_type in log_types:
            try:
                logs = driver.get_log(log_type)
                for log in logs:
                    log['log_type'] = log_type
                    all_logs.append(log)
            except Exception as type_error:
                logger.debug(f"无法获取{log_type}日志: {type_error}")
        
        # 按时间戳排序
        all_logs.sort(key=lambda x: x.get('timestamp', 0))
        
        # Enhanced log formatting with better message parsing
        formatted_logs = []
        for log in all_logs:
            # 解析日志消息，提取更有用的信息
            message = log['message']
            parsed_info = parse_console_message(message)
            
            formatted_log = {
                "level": log['level'],
                "message": message,
                "parsed_message": parsed_info['clean_message'],
                "message_type": parsed_info['type'],
                "source_info": parsed_info['source'],
                "timestamp": log['timestamp'],
                "log_type": log.get('log_type', 'browser'),
                "datetime": datetime.fromtimestamp(log['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                "relative_time": f"+{round((log['timestamp'] - all_logs[0]['timestamp']) / 1000, 3)}s" if all_logs else "0s"
            }
            formatted_logs.append(formatted_log)
        
        # Filter by level
        if level != "ALL":
            formatted_logs = [log for log in formatted_logs if log['level'].upper() == level.upper()]
        
        # Apply limit to most recent logs
        if limit and len(formatted_logs) > limit:
            formatted_logs = formatted_logs[-limit:]
        
        # 统计各级别日志数量
        level_counts = {}
        for log in formatted_logs:
            log_level = log['level']
            level_counts[log_level] = level_counts.get(log_level, 0) + 1
        
        return {
            "success": True,
            "total_count": len(all_logs),
            "filtered_count": len(formatted_logs),
            "level_filter": level,
            "level_counts": level_counts,
            "logs": formatted_logs
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "logs": []
        }

@mcp.tool()
def authenticate_user(username: str, password: str):
    """
    Authenticate user for browser operations.
    :param username: Username
    :param password: Password
    """
    if username in state["auth_users"] and state["auth_users"][username] == password:
        return {
            "success": True,
            "message": "Authentication successful",
            "user_info": {
                "username": username,
                "authenticated": True,
                "session_id": f"auth_{int(time.time())}"
            }
        }
    else:
        return {
            "success": False,
            "error": "Invalid credentials",
            "message": "用户名或密码错误"
        }

@mcp.tool()
@browser_mcp_auth_required
def open_browser(headless: bool = False, window_size: str = "1920,1080", **kwargs):
    """
    Open a new browser instance with enhanced configuration.
    :param headless: Whether to run in headless mode
    :param window_size: Browser window size (width,height)
    """
    current_user = kwargs.get('current_user', {})
    logger.info(f"用户 {current_user.get('username', 'unknown')} 请求打开浏览器")
    
    try:
        driver = get_driver()
        
        if headless:
            driver.execute_script("window.resizeTo(arguments[0], arguments[1]);", 
                                *map(int, window_size.split(',')))
        
        return {
            "success": True,
            "message": "Browser opened successfully",
            "session_id": state["current_session"],
            "window_size": driver.get_window_size(),
            "user_agent": driver.execute_script("return navigator.userAgent;")
        }
        
    except Exception as e:
        logger.error(f"打开浏览器失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to open browser"
        }

@mcp.tool()
@browser_mcp_auth_required
def navigate_to_url(url: str, wait_for_load: bool = True, timeout: int = 30, **kwargs):
    """
    Navigate to a specific URL with enhanced loading detection.
    :param url: Target URL
    :param wait_for_load: Whether to wait for page load completion
    :param timeout: Maximum wait time for page load
    """
    current_user = kwargs.get('current_user', {})
    logger.info(f"用户 {current_user.get('username', 'unknown')} 请求导航到: {url}")
    
    try:
        driver = get_driver()
        logger.debug(f"开始导航到: {url}")
        
        start_time = time.time()
        driver.get(url)
        logger.debug(f"页面加载请求已发送")
        
        if wait_for_load:
            logger.debug(f"等待页面加载完成，超时时间: {timeout}秒")
            wait = WebDriverWait(driver, timeout)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            logger.debug("页面加载完成")
        
        load_time = round((time.time() - start_time) * 1000, 2)
        title = driver.title
        
        logger.info(f"成功导航到 {url}，页面标题: {title}")
        return {
            "success": True,
            "message": f"Successfully navigated to {url}",
            "url": driver.current_url,
            "title": title,
            "load_time_ms": load_time,
            "ready_state": driver.execute_script("return document.readyState")
        }
        
    except Exception as e:
        logger.error(f"导航失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Navigation failed"
        }

@mcp.tool()
@browser_mcp_auth_required
def execute_javascript(script: str, capture_console: bool = True, timeout: int = 30, return_value: bool = True, **kwargs):
    """
    Execute JavaScript code in the current page with enhanced console capture.
    :param script: JavaScript code to execute
    :param capture_console: Whether to capture and return console logs immediately
    :param timeout: Execution timeout in seconds
    :param return_value: Whether to return the script execution result
    
    Enhanced features:
    - Automatic console log capture with proper formatting
    - Support for async JavaScript execution
    - Better error handling and reporting
    - Performance timing information
    """
    # 获取认证用户信息
    current_user = kwargs.get('current_user', {})
    logger.info(f"用户 {current_user.get('username', 'unknown')} 执行JavaScript: {script[:200]}{'...' if len(script) > 200 else ''}, capture_console={capture_console}")
    
    try:
        driver = get_driver()
        logger.debug("获取到驱动器，开始执行JavaScript")
        
        # 记录执行开始时间
        start_time = time.time()
        
        # 如果需要捕获console，先清空之前的日志
        if capture_console:
            try:
                # 清空现有日志缓冲区
                driver.get_log('browser')
            except:
                pass
        
        # Execute JavaScript with timeout handling
        try:
            if return_value:
                result = driver.execute_script(script)
            else:
                driver.execute_script(script)
                result = None
        except Exception as js_error:
            logger.error(f"JavaScript执行错误: {str(js_error)}")
            return {
                "success": False,
                "error": str(js_error),
                "error_type": "execution_error",
                "script_executed": script[:200] + ('...' if len(script) > 200 else ''),
                "execution_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        
        execution_time = round((time.time() - start_time) * 1000, 2)
        logger.debug(f"JavaScript执行完成，耗时: {execution_time}ms")
        
        response_data = {
            "success": True,
            "result": result,
            "script_executed": script[:200] + ('...' if len(script) > 200 else ''),
            "execution_time_ms": execution_time,
            "console_logs": []
        }
        
        # 如果需要捕获console日志
        if capture_console:
            try:
                # 获取执行后的console日志
                console_result = get_console_logs_internal(level="ALL", limit=100, format_output=True)
                if console_result["success"]:
                    response_data["console_logs"] = console_result["logs"]
                    response_data["console_summary"] = {
                        "total_count": len(console_result["logs"]),
                        "level_counts": console_result["level_counts"],
                        "has_errors": any(log["level"] in ["ERROR", "SEVERE"] for log in console_result["logs"])
                    }
                else:
                    response_data["console_logs_error"] = console_result["error"]
            except Exception as console_error:
                logger.warning(f"获取console日志失败: {console_error}")
                response_data["console_logs_error"] = str(console_error)
        
        logger.info(f"JavaScript执行成功，耗时: {execution_time}ms")
        return response_data
        
    except Exception as e:
        logger.error(f"执行JavaScript失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": "system_error",
            "script_executed": script[:200] + ('...' if len(script) > 200 else '')
        }

@mcp.tool()
def get_console_logs(level: str = "ALL", clear_after_get: bool = False, limit: int = 1000, include_performance: bool = True):
    """
    Get console logs from the browser with enhanced formatting and analysis.
    Based on Chrome DevTools Console API standards.
    
    :param level: Log level filter (ALL, INFO, WARNING, ERROR, SEVERE)
    :param clear_after_get: Whether to clear logs after getting them
    :param limit: Maximum number of logs to return (default: 1000)
    :param include_performance: Whether to include performance timing information
    
    Enhanced features:
    - Better message parsing and formatting
    - Performance timing analysis
    - Error categorization
    - Source information extraction
    """
    try:
        driver = get_driver()
        logger.debug(f"开始获取控制台日志，级别: {level}, 限制: {limit}")
        
        # 获取性能信息（如果需要）
        performance_info = {}
        if include_performance:
            try:
                performance_info = driver.execute_script("""
                    return {
                        navigation: performance.getEntriesByType('navigation')[0] || {},
                        memory: performance.memory || {},
                        timing: performance.timing || {}
                    };
                """)
            except Exception as perf_error:
                logger.debug(f"无法获取性能信息: {perf_error}")
        
        # 获取日志
        result = get_console_logs_internal(level, limit, True)
        
        if not result["success"]:
            return result
        
        # 增强的响应数据
        enhanced_response = {
            "success": True,
            "total_count": result["total_count"],
            "filtered_count": result["filtered_count"],
            "level_filter": level,
            "level_counts": result["level_counts"],
            "logs": result["logs"],
            "summary": {
                "has_errors": any(log["level"] in ["ERROR", "SEVERE"] for log in result["logs"]),
                "has_warnings": any(log["level"] == "WARNING" for log in result["logs"]),
                "message_types": {},
                "time_range": None
            },
            "capture_settings": {
                "limit": limit,
                "cleared_after_get": clear_after_get,
                "include_performance": include_performance
            }
        }
        
        # 分析消息类型
        message_types = {}
        if result["logs"]:
            for log in result["logs"]:
                msg_type = log.get("message_type", "unknown")
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            # 计算时间范围
            if len(result["logs"]) > 1:
                first_time = result["logs"][0]["timestamp"]
                last_time = result["logs"][-1]["timestamp"]
                enhanced_response["summary"]["time_range"] = {
                    "duration_ms": last_time - first_time,
                    "start": result["logs"][0]["datetime"],
                    "end": result["logs"][-1]["datetime"]
                }
        
        enhanced_response["summary"]["message_types"] = message_types
        
        # 添加性能信息
        if include_performance and performance_info:
            enhanced_response["performance"] = performance_info
        
        # Optional: Clear logs after retrieval
        if clear_after_get:
            try:
                driver.execute_script("console.clear();");
                logger.debug("已清除浏览器控制台日志")
            except Exception as clear_error:
                logger.warning(f"清除日志失败: {clear_error}")
        
        logger.info(f"成功获取{enhanced_response['filtered_count']}条控制台日志")
        return enhanced_response
        
    except Exception as e:
        logger.error(f"获取控制台日志失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "获取控制台日志时发生异常",
            "logs": []
        }

@mcp.tool()
def click_element(selector: str, by: str = "css", timeout: int = 10, wait_after_click: float = 1, capture_before_after: bool = False):
    """
    Click an element on the current page with enhanced feedback.
    :param selector: Element selector
    :param by: Selection method (css, xpath, id, name, tag, class)
    :param timeout: Maximum time to wait for element
    :param wait_after_click: Time to wait after clicking
    :param capture_before_after: Whether to capture element state before and after click
    """
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, timeout)
        
        # 支持更多选择器类型
        by_methods = {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "name": By.NAME,
            "tag": By.TAG_NAME,
            "class": By.CLASS_NAME
        }
        
        by_method = by_methods.get(by.lower())
        if not by_method:
            return {
                "success": False,
                "error": f"Unsupported selection method: {by}. Supported: {list(by_methods.keys())}"
            }
        
        # 等待元素可点击
        element = wait.until(EC.element_to_be_clickable((by_method, selector)))
        
        # 获取点击前的元素信息
        before_info = {}
        if capture_before_after:
            before_info = {
                "text": element.text,
                "tag_name": element.tag_name,
                "is_displayed": element.is_displayed(),
                "is_enabled": element.is_enabled(),
                "location": element.location,
                "size": element.size,
                "attributes": {
                    "class": element.get_attribute("class"),
                    "id": element.get_attribute("id"),
                    "type": element.get_attribute("type")
                }
            }
        
        # 执行点击
        start_time = time.time()
        element.click()
        click_time = round((time.time() - start_time) * 1000, 2)
        
        # 等待指定时间
        if wait_after_click > 0:
            time.sleep(wait_after_click)
        
        # 获取点击后的信息
        after_info = {}
        if capture_before_after:
            try:
                # 重新获取元素（可能已经改变）
                element_after = driver.find_element(by_method, selector)
                after_info = {
                    "text": element_after.text,
                    "is_displayed": element_after.is_displayed(),
                    "is_enabled": element_after.is_enabled(),
                    "location": element_after.location,
                    "attributes": {
                        "class": element_after.get_attribute("class"),
                        "id": element_after.get_attribute("id"),
                        "type": element_after.get_attribute("type")
                    }
                }
            except Exception as after_error:
                after_info = {"error": f"无法获取点击后状态: {str(after_error)}"}
        
        response = {
            "success": True,
            "message": f"Successfully clicked element: {selector}",
            "element_info": {
                "selector": selector,
                "by_method": by,
                "tag_name": element.tag_name,
                "text_preview": element.text[:100] + ('...' if len(element.text) > 100 else '')
            },
            "click_time_ms": click_time,
            "wait_after_click": wait_after_click
        }
        
        if capture_before_after:
            response["state_comparison"] = {
                "before": before_info,
                "after": after_info
            }
        
        return response
        
    except TimeoutException:
        return {
            "success": False,
            "error": f"Element not found or not clickable within {timeout} seconds: {selector}",
            "error_type": "timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "click_error",
            "selector": selector
        }

@mcp.tool()
def input_text(selector: str, text: str, by: str = "css", clear_first: bool = True, timeout: int = 10, simulate_typing: bool = False):
    """
    Input text into an element on the current page with enhanced features.
    :param selector: Element selector
    :param text: Text to input
    :param by: Selection method (css, xpath, id, name, tag, class)
    :param clear_first: Whether to clear existing text first
    :param timeout: Maximum time to wait for element
    :param simulate_typing: Whether to simulate human-like typing with delays
    """
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, timeout)
        
        # 支持更多选择器类型
        by_methods = {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "name": By.NAME,
            "tag": By.TAG_NAME,
            "class": By.CLASS_NAME
        }
        
        by_method = by_methods.get(by.lower())
        if not by_method:
            return {
                "success": False,
                "error": f"Unsupported selection method: {by}. Supported: {list(by_methods.keys())}"
            }
        
        # 等待元素出现并可交互
        element = wait.until(EC.element_to_be_clickable((by_method, selector)))
        
        # 获取输入前的状态
        before_value = element.get_attribute("value") or ""
        element_type = element.get_attribute("type") or element.tag_name
        
        # 清空现有文本
        if clear_first:
            element.clear()
        
        # 输入文本
        start_time = time.time()
        if simulate_typing:
            # 模拟人类打字
            for char in text:
                element.send_keys(char)
                time.sleep(0.05 + (0.1 * (time.time() % 1)))  # 随机延迟
        else:
            element.send_keys(text)
        
        input_time = round((time.time() - start_time) * 1000, 2)
        
        # 获取输入后的值
        after_value = element.get_attribute("value") or ""
        
        # 验证输入是否成功
        input_successful = text in after_value if not clear_first else after_value == text
        
        return {
            "success": True,
            "message": f"Successfully input text into element: {selector}",
            "element_info": {
                "selector": selector,
                "by_method": by,
                "element_type": element_type,
                "tag_name": element.tag_name
            },
            "input_details": {
                "text_length": len(text),
                "before_value": before_value,
                "after_value": after_value,
                "input_successful": input_successful,
                "cleared_first": clear_first,
                "simulated_typing": simulate_typing
            },
            "input_time_ms": input_time
        }
        
    except TimeoutException:
        return {
            "success": False,
            "error": f"Element not found or not interactable within {timeout} seconds: {selector}",
            "error_type": "timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "input_error",
            "selector": selector
        }

@mcp.tool()
def take_screenshot(filename: str = None, full_page: bool = False, element_selector: str = None, include_metadata: bool = True):
    """
    Take a screenshot of the current page with enhanced features.
    :param filename: Screenshot filename (auto-generated if not provided)
    :param full_page: Whether to capture full page
    :param element_selector: CSS selector for specific element screenshot
    :param include_metadata: Whether to include screenshot metadata
    """
    try:
        driver = get_driver()
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if element_selector:
                filename = f"element_screenshot_{timestamp}.png"
            elif full_page:
                filename = f"fullpage_screenshot_{timestamp}.png"
            else:
                filename = f"screenshot_{timestamp}.png"
        
        # Ensure screenshot directory exists
        screenshot_dir = "./screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        # 获取截图前的信息
        before_info = {
            "url": driver.current_url,
            "title": driver.title,
            "window_size": driver.get_window_size(),
            "timestamp": datetime.now().isoformat()
        }
        
        start_time = time.time()
        
        if element_selector:
            # Screenshot specific element
            element = driver.find_element(By.CSS_SELECTOR, element_selector)
            element.screenshot(filepath)
            screenshot_info = {
                "type": "element",
                "element_info": {
                    "selector": element_selector,
                    "tag_name": element.tag_name,
                    "location": element.location,
                    "size": element.size,
                    "text_preview": element.text[:100] + ('...' if len(element.text) > 100 else '')
                }
            }
        else:
            # Screenshot entire page
            if full_page:
                # 尝试全页面截图
                try:
                    # 获取页面总高度
                    total_height = driver.execute_script("return document.body.scrollHeight")
                    driver.set_window_size(driver.get_window_size()["width"], total_height)
                    driver.save_screenshot(filepath)
                    screenshot_info = {"type": "full_page", "total_height": total_height}
                except Exception as full_page_error:
                    # 如果全页面截图失败，使用普通截图
                    driver.save_screenshot(filepath)
                    screenshot_info = {"type": "viewport", "full_page_error": str(full_page_error)}
            else:
                driver.save_screenshot(filepath)
                screenshot_info = {"type": "viewport"}
        
        screenshot_time = round((time.time() - start_time) * 1000, 2)
        
        # 获取文件信息
        file_size = os.path.getsize(filepath)
        
        response = {
            "success": True,
            "message": f"Screenshot saved: {filepath}",
            "screenshot_info": {
                "filepath": filepath,
                "filename": filename,
                "file_size_bytes": file_size,
                "screenshot_time_ms": screenshot_time,
                **screenshot_info
            }
        }
        
        if include_metadata:
            response["metadata"] = before_info
        
        return response
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "screenshot_error"
        }

@mcp.tool()
def get_page_info(include_html: bool = False, include_cookies: bool = False, include_performance: bool = True, include_console_summary: bool = True):
    """
    Get comprehensive information about the current page.
    :param include_html: Whether to include page HTML
    :param include_cookies: Whether to include cookies
    :param include_performance: Whether to include performance metrics
    :param include_console_summary: Whether to include console log summary
    """
    try:
        driver = get_driver()
        
        # 基础页面信息
        page_info = {
            "url": driver.current_url,
            "title": driver.title,
            "window_size": driver.get_window_size(),
            "ready_state": driver.execute_script("return document.readyState")
        }
        
        # HTML信息
        if include_html:
            html_source = driver.page_source
            page_info["html"] = {
                "length": len(html_source),
                "preview": html_source[:1000] + ('...' if len(html_source) > 1000 else '')
            }
        
        # Cookie信息
        if include_cookies:
            cookies = driver.get_cookies()
            page_info["cookies"] = {
                "count": len(cookies),
                "details": cookies
            }
        
        # 性能信息
        if include_performance:
            try:
                performance_data = driver.execute_script("""
                    var perf = performance;
                    var nav = perf.getEntriesByType('navigation')[0] || {};
                    return {
                        navigation: {
                            loadEventEnd: nav.loadEventEnd || 0,
                            domContentLoadedEventEnd: nav.domContentLoadedEventEnd || 0,
                            responseEnd: nav.responseEnd || 0,
                            requestStart: nav.requestStart || 0
                        },
                        memory: perf.memory ? {
                            usedJSHeapSize: perf.memory.usedJSHeapSize,
                            totalJSHeapSize: perf.memory.totalJSHeapSize,
                            jsHeapSizeLimit: perf.memory.jsHeapSizeLimit
                        } : null,
                        timing: {
                            loadComplete: perf.timing.loadEventEnd - perf.timing.navigationStart,
                            domReady: perf.timing.domContentLoadedEventEnd - perf.timing.navigationStart,
                            firstByte: perf.timing.responseStart - perf.timing.navigationStart
                        }
                    };
                """)
                page_info["performance"] = performance_data
            except Exception as perf_error:
                page_info["performance"] = {"error": str(perf_error)}
        
        # Console日志摘要
        if include_console_summary:
            try:
                console_result = get_console_logs_internal("ALL", 50, False)
                if console_result["success"]:
                    page_info["console_summary"] = {
                        "total_logs": console_result["total_count"],
                        "level_counts": console_result["level_counts"],
                        "has_errors": any(log["level"] in ["ERROR", "SEVERE"] for log in console_result["logs"]),
                        "recent_errors": [log for log in console_result["logs"] if log["level"] in ["ERROR", "SEVERE"]][-3:]
                    }
                else:
                    page_info["console_summary"] = {"error": console_result["error"]}
            except Exception as console_error:
                page_info["console_summary"] = {"error": str(console_error)}
        
        # 页面元素统计
        try:
            element_stats = driver.execute_script("""
                return {
                    total_elements: document.querySelectorAll('*').length,
                    forms: document.forms.length,
                    images: document.images.length,
                    links: document.links.length,
                    scripts: document.scripts.length
                };
            """)
            page_info["element_stats"] = element_stats
        except Exception as stats_error:
            page_info["element_stats"] = {"error": str(stats_error)}
        
        return {
            "success": True,
            "page_info": page_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "获取页面信息时发生异常"
        }

@mcp.tool()
def close_browser():
    """
    Close the browser instance with detailed reporting.
    """
    try:
        # Close all drivers in state
        closed_sessions = []
        failed_sessions = []
        
        for session_id, driver in list(state["drivers"].items()):
            if driver:
                try:
                    driver.quit()
                    closed_sessions.append(session_id)
                    logger.debug(f"已关闭会话: {session_id}")
                except Exception as close_error:
                    failed_sessions.append({"session_id": session_id, "error": str(close_error)})
                    logger.warning(f"关闭会话{session_id}时出错: {close_error}")
        
        # 清空状态
        state["drivers"].clear()
        state["current_session"] = None
        
        return {
            "success": True,
            "message": f"Browser cleanup completed",
            "closed_sessions": closed_sessions,
            "failed_sessions": failed_sessions,
            "total_closed": len(closed_sessions),
            "total_failed": len(failed_sessions)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error during browser cleanup"
        }

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="browser-console-capture",
                server_version="2.0.0",
                capabilities=mcp.server.ServerCapabilities(
                    tools={},
                )
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
