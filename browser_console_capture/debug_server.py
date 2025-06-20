#!/usr/bin/env python3
"""
调试版本的MCP服务器
"""

import json
import sys
import traceback

def debug_log(message):
    """输出调试信息到stderr"""
    print(f"DEBUG: {message}", file=sys.stderr, flush=True)

def main():
    """主函数"""
    debug_log("MCP服务器启动")
    
    try:
        while True:
            debug_log("等待输入...")
            line = sys.stdin.readline()
            
            if not line:
                debug_log("收到EOF，退出")
                break
                
            line = line.strip()
            if not line:
                debug_log("收到空行，继续")
                continue
                
            debug_log(f"收到请求: {line}")
            
            try:
                request = json.loads(line)
                debug_log(f"解析的请求: {request}")
                
                # 处理不同的方法
                method = request.get("method")
                request_id = request.get("id")
                
                if method == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "browser-console-capture",
                                "version": "1.0.0"
                            }
                        }
                    }
                elif method == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "tools": [
                                {
                                    "name": "start_browser",
                                    "description": "启动浏览器",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "browser": {"type": "string", "default": "chrome"},
                                            "headless": {"type": "boolean", "default": False}
                                        }
                                    }
                                },
                                {
                                    "name": "navigate_to_url",
                                    "description": "导航到指定URL",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "url": {"type": "string"},
                                            "wait_for_load": {"type": "boolean", "default": True}
                                        },
                                        "required": ["url"]
                                    }
                                },
                                {
                                    "name": "close_browser",
                                    "description": "关闭浏览器",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {}
                                    }
                                }
                            ]
                        }
                    }
                elif method == "tools/call":
                    tool_name = request["params"]["name"]
                    arguments = request["params"].get("arguments", {})
                    
                    debug_log(f"调用工具: {tool_name}, 参数: {arguments}")
                    
                    if tool_name == "start_browser":
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "success": True,
                                "message": "浏览器启动成功（模拟）",
                                "browser_type": arguments.get("browser", "chrome")
                            }
                        }
                    elif tool_name == "navigate_to_url":
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "success": True,
                                "current_url": arguments["url"],
                                "title": "测试页面",
                                "load_time": 1.5
                            }
                        }
                    elif tool_name == "close_browser":
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "success": True,
                                "message": "浏览器关闭成功（模拟）"
                            }
                        }
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"未知工具: {tool_name}"
                            }
                        }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"未知方法: {method}"
                        }
                    }
                
                response_json = json.dumps(response)
                debug_log(f"发送响应: {response_json}")
                print(response_json, flush=True)
                
            except json.JSONDecodeError as e:
                debug_log(f"JSON解析错误: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                debug_log(f"处理请求时出错: {e}")
                debug_log(traceback.format_exc())
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
                
    except KeyboardInterrupt:
        debug_log("收到中断信号")
    except Exception as e:
        debug_log(f"主循环错误: {e}")
        debug_log(traceback.format_exc())
    finally:
        debug_log("MCP服务器停止")

if __name__ == "__main__":
    main()