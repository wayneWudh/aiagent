#!/usr/bin/env python3
"""
MCP客户端测试脚本
测试MCP服务器的各项功能
"""
import asyncio
import websockets
import json
import logging
import argparse
from typing import Dict, Any

class MCPTestClient:
    """MCP测试客户端"""
    
    def __init__(self, uri: str = "ws://localhost:8080"):
        self.uri = uri
        self.websocket = None
        self.request_id = 0
        
    def get_next_id(self) -> int:
        """获取下一个请求ID"""
        self.request_id += 1
        return self.request_id
    
    async def connect(self):
        """连接到MCP服务器"""
        try:
            self.websocket = await websockets.connect(self.uri)
            print(f"✅ 连接到MCP服务器: {self.uri}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息并等待响应"""
        if not self.websocket:
            raise Exception("未连接到服务器")
        
        # 发送消息
        await self.websocket.send(json.dumps(message))
        print(f"📤 发送: {message['method']}")
        
        # 接收响应
        response = await self.websocket.recv()
        result = json.loads(response)
        print(f"📥 响应: {result.get('result', result.get('error', 'Unknown'))}")
        
        return result
    
    async def initialize(self) -> bool:
        """初始化连接"""
        message = {
            "jsonrpc": "2.0",
            "id": self.get_next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",
                "clientInfo": {
                    "name": "mcp-test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        try:
            response = await self.send_message(message)
            if "result" in response:
                server_info = response["result"]["serverInfo"]
                print(f"🎯 服务器: {server_info['name']} v{server_info['version']}")
                return True
            else:
                print(f"❌ 初始化失败: {response.get('error')}")
                return False
        except Exception as e:
            print(f"❌ 初始化异常: {e}")
            return False
    
    async def list_tools(self) -> bool:
        """获取工具列表"""
        message = {
            "jsonrpc": "2.0",
            "id": self.get_next_id(),
            "method": "tools/list",
            "params": {}
        }
        
        try:
            response = await self.send_message(message)
            if "result" in response:
                tools = response["result"]["tools"]
                print(f"🔧 可用工具数量: {len(tools)}")
                for tool in tools:
                    print(f"   - {tool['name']}: {tool['description']}")
                return True
            else:
                print(f"❌ 获取工具列表失败: {response.get('error')}")
                return False
        except Exception as e:
            print(f"❌ 获取工具列表异常: {e}")
            return False
    
    async def test_tool(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """测试工具调用"""
        message = {
            "jsonrpc": "2.0",
            "id": self.get_next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            response = await self.send_message(message)
            if "result" in response:
                content = response["result"]["content"]
                if content and len(content) > 0:
                    text_content = content[0].get("text", "")
                    try:
                        parsed_result = json.loads(text_content)
                        print(f"✅ 工具 {tool_name} 执行成功")
                        print(f"   数据预览: {str(parsed_result)[:200]}...")
                        return True
                    except json.JSONDecodeError:
                        print(f"✅ 工具 {tool_name} 执行成功 (文本响应)")
                        print(f"   响应: {text_content[:200]}...")
                        return True
                else:
                    print(f"⚠️ 工具 {tool_name} 返回空内容")
                    return False
            else:
                error = response.get('error', {})
                print(f"❌ 工具 {tool_name} 执行失败: {error.get('message', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ 工具 {tool_name} 调用异常: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """运行所有测试"""
        success_count = 0
        total_tests = 0
        
        try:
            print("🚀 开始MCP服务器测试...")
            print("=" * 50)
            
            # 1. 连接测试
            total_tests += 1
            if await self.connect():
                success_count += 1
            else:
                return False
            
            # 2. 初始化测试
            total_tests += 1
            if await self.initialize():
                success_count += 1
            else:
                return False
            
            # 3. 工具列表测试
            total_tests += 1
            if await self.list_tools():
                success_count += 1
            
            print("\n" + "=" * 50)
            print("🧪 开始工具功能测试...")
            
            # 4. 测试 get_supported_symbols
            total_tests += 1
            print(f"\n🔧 测试工具: get_supported_symbols")
            if await self.test_tool("get_supported_symbols", {}):
                success_count += 1
            
            # 5. 测试 check_system_health
            total_tests += 1
            print(f"\n🔧 测试工具: check_system_health")
            if await self.test_tool("check_system_health", {}):
                success_count += 1
            
            # 6. 测试 query_crypto_signals (BTC)
            total_tests += 1
            print(f"\n🔧 测试工具: query_crypto_signals (BTC)")
            if await self.test_tool("query_crypto_signals", {
                "symbol": "BTC",
                "timeframes": ["1h"]
            }):
                success_count += 1
            
            # 7. 测试 query_crypto_signals (ETH)
            total_tests += 1
            print(f"\n🔧 测试工具: query_crypto_signals (ETH)")
            if await self.test_tool("query_crypto_signals", {
                "symbol": "ETH",
                "timeframes": ["5m", "1h"]
            }):
                success_count += 1
            
            # 8. 测试 analyze_signal_patterns
            total_tests += 1
            print(f"\n🔧 测试工具: analyze_signal_patterns")
            if await self.test_tool("analyze_signal_patterns", {
                "symbol": "BTC",
                "timeframes": ["1h", "1d"]
            }):
                success_count += 1
            
            # 9. 测试错误处理 (无效币种)
            total_tests += 1
            print(f"\n🔧 测试错误处理: 无效币种")
            response = await self.send_message({
                "jsonrpc": "2.0",
                "id": self.get_next_id(),
                "method": "tools/call",
                "params": {
                    "name": "query_crypto_signals",
                    "arguments": {"symbol": "INVALID"}
                }
            })
            if "error" in response:
                print("✅ 错误处理正确")
                success_count += 1
            else:
                print("❌ 错误处理失败")
            
            # 10. 测试无效工具
            total_tests += 1
            print(f"\n🔧 测试无效工具调用")
            response = await self.send_message({
                "jsonrpc": "2.0",
                "id": self.get_next_id(),
                "method": "tools/call",
                "params": {
                    "name": "invalid_tool",
                    "arguments": {}
                }
            })
            if "error" in response:
                print("✅ 无效工具处理正确")
                success_count += 1
            else:
                print("❌ 无效工具处理失败")
            
        except Exception as e:
            print(f"❌ 测试过程中发生异常: {e}")
            
        finally:
            if self.websocket:
                await self.websocket.close()
        
        # 显示测试结果
        print("\n" + "=" * 50)
        print("📊 测试结果汇总")
        print(f"总测试数: {total_tests}")
        print(f"成功数量: {success_count}")
        print(f"失败数量: {total_tests - success_count}")
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 MCP服务器测试总体通过！")
            return True
        else:
            print("⚠️ MCP服务器测试存在问题，请检查")
            return False
    
    async def interactive_mode(self):
        """交互模式"""
        print("🎮 进入MCP交互测试模式")
        print("可用命令: init, list, call <tool_name>, quit")
        
        if not await self.connect():
            return
        
        while True:
            try:
                command = input("\n> ").strip().split()
                if not command:
                    continue
                
                if command[0] == "quit":
                    break
                elif command[0] == "init":
                    await self.initialize()
                elif command[0] == "list":
                    await self.list_tools()
                elif command[0] == "call" and len(command) > 1:
                    tool_name = command[1]
                    print(f"调用工具: {tool_name}")
                    print("请输入参数 (JSON格式，空行表示无参数):")
                    args_input = input("参数: ").strip()
                    
                    try:
                        args = json.loads(args_input) if args_input else {}
                        await self.test_tool(tool_name, args)
                    except json.JSONDecodeError:
                        print("❌ 参数格式错误，请使用JSON格式")
                else:
                    print("未知命令")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        if self.websocket:
            await self.websocket.close()
        
        print("\n👋 退出交互模式")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MCP服务器测试客户端')
    parser.add_argument('--uri', default='ws://localhost:8080', help='MCP服务器URI')
    parser.add_argument('--interactive', action='store_true', help='交互模式')
    parser.add_argument('--debug', action='store_true', help='启用调试日志')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    
    client = MCPTestClient(args.uri)
    
    if args.interactive:
        await client.interactive_mode()
    else:
        success = await client.run_all_tests()
        return 0 if success else 1


if __name__ == '__main__':
    exit(asyncio.run(main())) 