#!/usr/bin/env python3
"""浏览器Console报错捕捉MCP服务
提供浏览器自动化和错误捕捉功能，让AI模型能够自动操作浏览器并获取错误信息
支持test-token-eric特殊认证，默认以eric用户身份访问并自带授权
"""

import base64
import time
import logging
import os
import json
import requests
from datetime import datetime
from typing import Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException
from mcp.server.fastmcp import FastMCP
from auth_utils import (
    browser_mcp_auth_required, 
    get_browser_mcp_auth_headers, 
    log_browser_mcp_auth_info,
    authenticate_user,
    TEST_TOKEN_ERIC
)

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Configure logging based on config
logging.basicConfig(
    level=getattr(logging, config['logging']['level']),
    format=config['logging']['format'],
    handlers=[
        logging.FileHandler(config['logging']['file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("日志系统初始化完成，配置已加载")

# 记录认证配置信息
log_browser_mcp_auth_info()

logger.info("初始化FastMCP服务器...")
mcp = FastMCP(
    name="browser-console-capture",
    instructions="This is a browser console capture MCP service with test-token-eric authentication support.",
)
logger.info("FastMCP服务器初始化完成")

# Global state to store browser instances
state = {
    "drivers": {},
    "current_session": None
}
logger.info("状态字典初始化完成")


def get_driver():
    """Get the current active driver"""
    logger.debug(f"获取驱动器，当前会话: {state['current_session']}")
    logger.debug(f"可用驱动器: {list(state['drivers'].keys())}")
    
    if not state["drivers"]:
        logger.error("没有活动的浏览器会话")
        raise Exception("No browser session active. Please start a browser first.")
    
    # Return the current session driver or the first available driver
    if state["current_session"] and state["current_session"] in state["drivers"]:
        driver = state["drivers"][state["current_session"]]
        logger.debug(f"成功获取当前会话驱动器: {type(driver)}")
        return driver
    
    # Return the first available driver
    for session_id, driver in state["drivers"].items():
        if driver:
            state["current_session"] = session_id
            logger.debug(f"成功获取第一个可用驱动器: {type(driver)}")
            return driver
    
    logger.error("没有找到活动的浏览器会话")
    raise Exception("No active browser session found.")


def generate_session_id(browser: str) -> str:
    """生成会话ID"""
    import time
    timestamp = int(time.time())
    return f"{browser}_{timestamp}"


@mcp.tool()
def authenticate_user(username: str, password: str):
    """
    Authenticate user for browser operations.
    :param username: Username
    :param password: Password
    """
    try:
        from auth_utils import authenticate_user as auth_func
        success, message, user_data = auth_func(username, password)
        
        if success:
            logger.info(f"用户认证成功: {user_data['username']} ({user_data['login_name']})")
            return {
                "success": True,
                "message": message,
                "user_data": {
                    "user_id": user_data['user_id'],
                    "username": user_data['username'],
                    "login_name": user_data['login_name'],
                    "user_role": user_data['user_role'],
                    "phone": user_data['phone'],
                    "is_active": user_data['is_active']
                }
            }
        else:
            logger.warning(f"用户认证失败: {message}")
            return {
                "success": False,
                "message": message,
                "user_data": None
            }
            
    except Exception as e:
        error_msg = f"认证过程异常: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "user_data": None
        }


@mcp.tool()
@browser_mcp_auth_required
def start_browser(browser: str = "chrome", headless: bool = True, window_size: str = "1920,1080", **kwargs):
    """
    Start a browser (supports Chrome and Firefox)
    :param browser: Browser type ("chrome" or "firefox")
    :param headless: Whether to run in headless mode
    :param window_size: Browser window size
    """
    try:
        # 获取认证用户信息
        current_user = kwargs.get('current_user', {})
        logger.info(f"用户 {current_user.get('username', 'unknown')} 启动浏览器: {browser}, 无头模式: {headless}, 窗口大小: {window_size}")
        if browser not in ["chrome", "firefox"]:
            logger.error(f"不支持的浏览器类型: {browser}")
            raise ValueError("Unsupported browser type. Use 'chrome' or 'firefox'.")

        driver = None
        logger.debug(f"准备启动{browser}浏览器")
        if browser == "chrome":
            chrome_options = ChromeOptions()
            if headless:
                chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument(f"--window-size={window_size}")
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            # 启用日志记录
            chrome_options.add_argument("--enable-logging")
            chrome_options.add_argument("--log-level=0")
            chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
            
            try:
                # 使用指定的Chrome和ChromeDriver路径
                chrome_binary_path = "/opt/chrome-linux64/chrome"
                chromedriver_path = "/opt/chromedriver-linux64/chromedriver"
                
                # 设置Chrome二进制路径
                chrome_options.binary_location = chrome_binary_path
                
                # 使用指定的ChromeDriver路径
                from selenium.webdriver.chrome.service import Service
                service = Service(chromedriver_path)
                
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as chrome_error:
                # 如果指定路径失败，尝试使用系统默认Chrome
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception:
                    # 如果Chrome完全失败，尝试使用Firefox
                    firefox_options = FirefoxOptions()
                    if headless:
                        firefox_options.add_argument("--headless")
                    firefox_options.add_argument("--no-sandbox")
                    firefox_options.add_argument("--disable-dev-shm-usage")
                    
                    driver = webdriver.Firefox(options=firefox_options)

        elif browser == "firefox":
            firefox_options = FirefoxOptions()
            if headless:
                firefox_options.add_argument("--headless")
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Firefox(options=firefox_options)

        session_id = generate_session_id(browser)
        state["drivers"][session_id] = driver
        state["current_session"] = session_id
        
        logger.info(f"浏览器启动成功，会话ID: {session_id}")
        logger.debug(f"当前状态: drivers={list(state['drivers'].keys())}, current_session={state['current_session']}")
        return f"Browser started with session_id: {session_id}"

    except Exception as e:
        logger.error(f"启动浏览器失败: {str(e)}", exc_info=True)
        return f"Error starting browser: {str(e)}"

    
@mcp.tool()
@browser_mcp_auth_required
def navigate_to_url(url: str, wait_for_load: bool = True, timeout: int = 30, **kwargs):
    """
    Navigates the browser to a specified URL.
    :param url: The URL to navigate to.
    :param wait_for_load: Whether to wait for page load completion
    :param timeout: Maximum time to wait for page load
    """
    try:
        # 获取认证用户信息
        current_user = kwargs.get('current_user', {})
        logger.info(f"用户 {current_user.get('username', 'unknown')} 导航到URL: {url}, wait_for_load={wait_for_load}, timeout={timeout}")
        driver = get_driver()
        logger.debug(f"获取到驱动器，开始导航到: {url}")
        driver.get(url)
        logger.debug(f"页面加载请求已发送")
        
        if wait_for_load:
            logger.debug(f"等待页面加载完成，超时时间: {timeout}秒")
            wait = WebDriverWait(driver, timeout)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            logger.debug("页面加载完成")
        
        title = driver.title
        logger.info(f"成功导航到 {url}，页面标题: {title}")
        return f"Navigated to {url}. Current title: {title}. The next setp is execute_javascript "
    except Exception as e:
        logger.error(f"导航失败: {str(e)}", exc_info=True)
        return f"Error navigating: {str(e)}"
    
@mcp.tool()
@browser_mcp_auth_required
def execute_javascript(script: str, capture_console: bool = True, timeout: int = 10, max_logs: int = 1000, **kwargs):
    """
    Execute JavaScript code in the current page.
    :param script: JavaScript code to execute
    :param capture_console: Whether to show console logs note (use get_console_logs separately to avoid buffer clearing)
    :param timeout: Execution timeout
    :param max_logs: Deprecated parameter (kept for compatibility)
    
    Note: To properly capture console logs, execute JavaScript with capture_console=False,
    then call get_console_logs separately to avoid log buffer being cleared.
    """
    # 获取认证用户信息
    current_user = kwargs.get('current_user', {})
    logger.info(f"用户 {current_user.get('username', 'unknown')} 执行JavaScript: {script[:200]}{'...' if len(script) > 200 else ''}, capture_console={capture_console}")
    try:
        driver = get_driver()
        logger.debug("获取到驱动器，开始执行JavaScript")
        
        # Execute JavaScript
        result = driver.execute_script(script)
        logger.debug(f"JavaScript执行完成，结果: {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
        
        response_data = {
            "success": True,
            "result": result,
            "script_executed": script[:200] + ('...' if len(script) > 200 else ''),
            "console_logs": []
        }
        
        if capture_console:
            logger.debug("JavaScript执行完成，建议使用get_console_logs获取日志")
            response_data["console_logs_note"] = "JavaScript执行完成，请使用get_console_logs工具获取控制台日志以避免日志缓冲区被清空"
            response_data["console_count"] = "请使用get_console_logs查看"
        
        logger.info("JavaScript执行成功")
        return response_data
        
    except Exception as e:
        logger.error(f"执行JavaScript失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "script_executed": script[:200] + ('...' if len(script) > 200 else '')
        }

    
@mcp.tool()
def get_console_logs(level: str = "ALL", clear_after_get: bool = False, limit: int = 1000, include_performance: bool = True, exclude_info: bool = False):
    """
    Get console logs from the browser with enhanced formatting and analysis.
    Based on Chrome DevTools Console API standards.
    
    :param level: Log level filter (ALL, INFO, WARNING, ERROR, SEVERE)
    :param clear_after_get: Whether to clear logs after getting them
    :param limit: Maximum number of logs to return (default: 1000)
    :param include_performance: Whether to include performance timing information
    :param exclude_info: Whether to exclude INFO level logs from the response (useful for AI model processing)
    
    Enhanced features:
    - Better message parsing and formatting
    - Performance timing analysis
    - Error categorization
    - Source information extraction
    - Optional INFO level filtering for AI model optimization
    """
    try:
        driver = get_driver()
        logger.debug(f"开始获取控制台日志，级别: {level}, 限制: {limit}")
        
        # Chrome DevTools Console API 日志级别映射
        # 参考: https://developer.chrome.com/docs/devtools/console/api
        console_level_mapping = {
            'SEVERE': 'ERROR',     # console.error(), console.assert(false)
            'WARNING': 'WARNING',  # console.warn()
            'INFO': 'INFO',        # console.log(), console.info(), console.dir(), console.table()
            'DEBUG': 'VERBOSE',    # console.debug()
            'FINE': 'VERBOSE',     # 详细调试信息
            'FINER': 'VERBOSE',    # 更详细的调试信息
            'FINEST': 'VERBOSE'    # 最详细的调试信息
        }
        
        # Get browser logs - 获取所有类型的日志
        all_logs = []
        log_types = ['browser', 'driver', 'client', 'server']
        
        for log_type in log_types:
            try:
                logs = driver.get_log(log_type)
                for log in logs:
                    log['log_type'] = log_type
                    all_logs.append(log)
                logger.debug(f"从{log_type}获取到{len(logs)}条日志")
            except Exception as type_error:
                logger.debug(f"无法获取{log_type}日志: {type_error}")
        
        # 按时间戳排序
        all_logs.sort(key=lambda x: x.get('timestamp', 0))
        
        # Enhanced log formatting with Chrome DevTools standards
        formatted_logs = []
        error_count = 0
        warning_count = 0
        
        for log in all_logs:
            # 解析消息内容，提取堆栈跟踪信息
            message = log.get('message', '')
            
            # 检测是否包含堆栈跟踪
            has_stack_trace = 'at ' in message or 'Error:' in message or 'TypeError:' in message
            
            # 提取源文件信息
            source_info = log.get('source', 'unknown')
            if 'console-api' in source_info:
                source_type = 'console-api'  # console.log/error/warn等
            elif 'javascript' in source_info:
                source_type = 'javascript'   # JavaScript运行时错误
            elif 'network' in source_info:
                source_type = 'network'      # 网络请求错误
            else:
                source_type = 'other'
            
            # 标准化日志级别
            original_level = log.get('level', 'INFO')
            normalized_level = console_level_mapping.get(original_level, original_level)
            
            # 解析错误类型
            error_type = None
            if normalized_level in ['ERROR', 'SEVERE']:
                error_count += 1
                if 'TypeError:' in message:
                    error_type = 'TypeError'
                elif 'ReferenceError:' in message:
                    error_type = 'ReferenceError'
                elif 'SyntaxError:' in message:
                    error_type = 'SyntaxError'
                elif 'NetworkError:' in message or '404' in message:
                    error_type = 'NetworkError'
                elif 'console.assert' in message:
                    error_type = 'AssertionError'
                else:
                    error_type = 'UnknownError'
            elif normalized_level == 'WARNING':
                warning_count += 1
            
            # 提取文件和行号信息
            file_info = None
            line_number = None
            if ' at ' in message:
                # 尝试提取堆栈跟踪中的文件信息
                import re
                file_match = re.search(r'at\s+.*?\((.*?):(\d+):(\d+)\)', message)
                if file_match:
                    file_info = file_match.group(1)
                    line_number = int(file_match.group(2))
            
            formatted_log = {
                "level": normalized_level,
                "original_level": original_level,
                "message": message,
                "timestamp": log['timestamp'],
                "datetime": datetime.fromtimestamp(log['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                "source": source_info,
                "source_type": source_type,
                "log_type": log.get('log_type', 'browser'),
                "has_stack_trace": has_stack_trace,
                "error_type": error_type,
                "file_info": file_info,
                "line_number": line_number,
                "console_method": _detect_console_method(message)  # 检测使用的console方法
            }
            formatted_logs.append(formatted_log)
        
        # Filter by level
        if level != "ALL":
            if level.upper() == "VERBOSE":
                # VERBOSE包含所有级别
                pass
            else:
                formatted_logs = [log for log in formatted_logs if log['level'].upper() == level.upper()]
        
        # Optional: Exclude INFO level logs for AI model processing
        if exclude_info:
            formatted_logs = [log for log in formatted_logs if log['level'].upper() != 'INFO']
            logger.debug(f"已过滤INFO级别日志，剩余{len(formatted_logs)}条日志")
        
        # Apply limit to most recent logs
        if limit and len(formatted_logs) > limit:
            formatted_logs = formatted_logs[-limit:]
        
        # 统计各级别日志数量
        level_counts = {}
        console_method_counts = {}
        for log in formatted_logs:
            log_level = log['level']
            level_counts[log_level] = level_counts.get(log_level, 0) + 1
            
            console_method = log.get('console_method', 'unknown')
            console_method_counts[console_method] = console_method_counts.get(console_method, 0) + 1
        
        # Performance analysis
        performance_info = {}
        if include_performance:
            try:
                # 获取页面性能信息
                performance_timing = driver.execute_script("""
                    return {
                        loadEventEnd: performance.timing.loadEventEnd,
                        navigationStart: performance.timing.navigationStart,
                        domContentLoadedEventEnd: performance.timing.domContentLoadedEventEnd,
                        firstPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime,
                        firstContentfulPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-contentful-paint')?.startTime
                    };
                """)
                
                if performance_timing['loadEventEnd'] > 0:
                    load_time = performance_timing['loadEventEnd'] - performance_timing['navigationStart']
                    dom_ready_time = performance_timing['domContentLoadedEventEnd'] - performance_timing['navigationStart']
                    
                    performance_info = {
                        "page_load_time_ms": load_time,
                        "dom_ready_time_ms": dom_ready_time,
                        "first_paint_ms": performance_timing.get('firstPaint'),
                        "first_contentful_paint_ms": performance_timing.get('firstContentfulPaint')
                    }
            except Exception as perf_error:
                logger.debug(f"无法获取性能信息: {perf_error}")
                performance_info = {"error": "无法获取性能信息"}
        
        # Optional: Clear logs after retrieval
        if clear_after_get:
            driver.execute_script("console.clear();")
            logger.debug("已清除浏览器控制台日志")
        
        logger.info(f"成功获取{len(formatted_logs)}条控制台日志")
        
        # Return comprehensive structured response
        return {
            "success": True,
            "total_count": len(all_logs),
            "filtered_count": len(formatted_logs),
            "level_filter": level,
            "level_counts": level_counts,
            "console_method_counts": console_method_counts,
            "error_summary": {
                "total_errors": error_count,
                "total_warnings": warning_count,
                "has_critical_errors": error_count > 0
            },
            "performance_info": performance_info,
            "logs": formatted_logs,
            "message": f"成功获取{len(formatted_logs)}条控制台日志 (总共{len(all_logs)}条，错误{error_count}条，警告{warning_count}条)",
            "capture_settings": {
                "limit": limit,
                "include_performance": include_performance,
                "cleared_after_get": clear_after_get,
                "exclude_info": exclude_info
            },
            "chrome_devtools_compliance": True  # 标识符合Chrome DevTools标准
        }
        
    except Exception as e:
        logger.error(f"获取控制台日志失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "获取控制台日志时发生异常",
            "logs": []
        }
    
def _detect_console_method(message):
        """
        检测使用的console方法类型
        基于Chrome DevTools Console API规范
        """
        if 'console.error' in message or 'Error:' in message:
            return 'console.error'
        elif 'console.warn' in message or 'Warning:' in message:
            return 'console.warn'
        elif 'console.info' in message:
            return 'console.info'
        elif 'console.debug' in message:
            return 'console.debug'
        elif 'console.table' in message:
            return 'console.table'
        elif 'console.trace' in message:
            return 'console.trace'
        elif 'console.assert' in message:
            return 'console.assert'
        elif 'console.log' in message:
            return 'console.log'
        else:
            return 'unknown'
    
@mcp.tool()
def click_element(selector: str, by: str = "css", timeout: int = 10, wait_after_click: float = 1):
    """
    Click an element on the current page.
    :param selector: Element selector
    :param by: Selection method (css, xpath)
    :param timeout: Maximum time to wait for element
    :param wait_after_click: Time to wait after clicking
    """
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, timeout)
        
        if by.lower() == "css":
            by_method = By.CSS_SELECTOR
        elif by.lower() == "xpath":
            by_method = By.XPATH
        else:
            return f"Unsupported selection method: {by}"
        
        element = wait.until(EC.element_to_be_clickable((by_method, selector)))
        element.click()
        
        if wait_after_click > 0:
            time.sleep(wait_after_click)
        
        return f"Successfully clicked element: {selector}"
        
    except Exception as e:
        return f"Error clicking element: {str(e)}"
    
@mcp.tool()
def input_text(selector: str, text: str, by: str = "css", clear_first: bool = True, timeout: int = 10):
    """
    Input text into an element on the current page.
    :param selector: Element selector
    :param text: Text to input
    :param by: Selection method (css, xpath)
    :param clear_first: Whether to clear existing text first
    :param timeout: Maximum time to wait for element
    """
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, timeout)
        
        if by.lower() == "css":
            by_method = By.CSS_SELECTOR
        elif by.lower() == "xpath":
            by_method = By.XPATH
        else:
            return f"Unsupported selection method: {by}"
        
        element = wait.until(EC.presence_of_element_located((by_method, selector)))
        
        if clear_first:
            element.clear()
        
        element.send_keys(text)
        
        return f"Successfully input text '{text}' into element: {selector}"
        
    except Exception as e:
        return f"Error inputting text: {str(e)}"
    
@mcp.tool()
def take_screenshot(filename: str = None, full_page: bool = False, element_selector: str = None):
    """
    Take a screenshot of the current page.
    :param filename: Screenshot filename (auto-generated if not provided)
    :param full_page: Whether to capture full page
    :param element_selector: CSS selector for specific element screenshot
    """
    try:
        driver = get_driver()
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        # Ensure screenshot directory exists
        screenshot_dir = "./screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        if element_selector:
            # Screenshot specific element
            element = driver.find_element(By.CSS_SELECTOR, element_selector)
            element.screenshot(filepath)
        else:
            # Screenshot entire page
            driver.save_screenshot(filepath)
        
        return f"Screenshot saved: {filepath}"
        
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"
    
@mcp.tool()
def wait_for_element(selector: str, by: str = "css", timeout: int = 10, condition: str = "presence"):
    """
    Wait for an element to appear on the page.
    :param selector: Element selector
    :param by: Selection method (css, xpath)
    :param timeout: Maximum time to wait
    :param condition: Wait condition (presence, visible, clickable)
    """
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, timeout)
        
        if by.lower() == "css":
            by_method = By.CSS_SELECTOR
        elif by.lower() == "xpath":
            by_method = By.XPATH
        else:
            return f"Unsupported selection method: {by}"
        
        if condition == "presence":
            element = wait.until(EC.presence_of_element_located((by_method, selector)))
        elif condition == "visible":
            element = wait.until(EC.visibility_of_element_located((by_method, selector)))
        elif condition == "clickable":
            element = wait.until(EC.element_to_be_clickable((by_method, selector)))
        else:
            return f"Unsupported wait condition: {condition}"
        
        return f"Element found: {element.tag_name}(text: '{element.text[:50]}...', visible: {element.is_displayed()})"
        
    except TimeoutException:
        return f"Element wait timeout: {selector}"
    except Exception as e:
        return f"Error waiting for element: {str(e)}"
    
@mcp.tool()
def get_page_info(include_html: bool = False, include_cookies: bool = False):
    """
    Get information about the current page.
    :param include_html: Whether to include page HTML
    :param include_cookies: Whether to include cookies
    """
    try:
        driver = get_driver()
        
        info = f"URL: {driver.current_url}\nTitle: {driver.title}\nWindow size: {driver.get_window_size()}"
        
        if include_html:
            html_length = len(driver.page_source)
            info += f"\nHTML length: {html_length} characters"
        
        if include_cookies:
            cookies = driver.get_cookies()
            info += f"\nCookies count: {len(cookies)}"
        
        return info
        
    except Exception as e:
        return f"Error getting page info: {str(e)}"

@mcp.tool()
def close_browser():
    """
    Close the browser instance.
    """
    try:
        # Close all drivers in state
        closed_count = 0
        for session_id, driver in list(state["drivers"].items()):
            if driver:
                try:
                    driver.quit()
                    logger.debug(f"已关闭会话: {session_id}")
                except Exception as close_error:
                    logger.warning(f"关闭会话{session_id}时出错: {close_error}")
                closed_count += 1
        
        # 清空状态
        state["drivers"].clear()
        state["current_session"] = None
        
        return f"Closed {closed_count} browser session(s)"
    except Exception as e:
        return f"Error closing browser: {str(e)}"

# Run the FastMCP server
if __name__ == "__main__":
    logger.info("启动FastMCP服务器...")
    logger.info(f"日志文件位置: /tmp/browser_mcp_server.log")
    logger.info(f"当前工作目录: {os.getcwd()}")
    logger.info(f"Python路径: {os.sys.executable}")
    
    try:
        logger.info("开始运行MCP服务器")
        mcp.run()
    except Exception as e:
        logger.error(f"MCP服务器运行失败: {str(e)}", exc_info=True)
        raise
