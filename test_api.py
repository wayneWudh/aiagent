#!/usr/bin/env python3
"""
API功能测试脚本
测试技术信号查询API的各项功能
"""
import json
import time
import requests
from typing import Dict, Any


class APITester:
    """API测试类"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """初始化测试器"""
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'API-Tester/1.0'
        })
    
    def test_health_check(self) -> bool:
        """测试健康检查端点"""
        print("🔍 测试健康检查端点...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health")
            
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"服务状态: {data.get('status')}")
                print(f"数据库状态: {data.get('database', {}).get('status')}")
                print("✅ 健康检查通过")
                return True
            else:
                print(f"❌ 健康检查失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    def test_supported_symbols(self) -> bool:
        """测试获取支持的币种列表"""
        print("\n🔍 测试获取支持的币种列表...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/symbols")
            
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    symbols = data.get('data', {}).get('symbols', [])
                    timeframes = data.get('data', {}).get('timeframes', [])
                    print(f"支持的币种: {symbols}")
                    print(f"支持的时间周期: {timeframes}")
                    print("✅ 获取支持币种列表成功")
                    return True
                else:
                    print(f"❌ 获取失败: {data.get('message')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False
    
    def test_query_signals_post(self, symbol: str = "BTC", timeframes: list = None) -> bool:
        """测试POST方式查询技术信号"""
        print(f"\n🔍 测试POST方式查询技术信号 (币种: {symbol})...")
        try:
            payload = {"symbol": symbol}
            if timeframes:
                payload["timeframes"] = timeframes
            
            response = self.session.post(
                f"{self.base_url}/api/v1/signals",
                json=payload
            )
            
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = data.get('data', {})
                    print(f"查询币种: {result.get('symbol')}")
                    print(f"查询时间: {result.get('query_time')}")
                    print(f"时间周期数量: {len(result.get('timeframes', []))}")
                    
                    # 显示汇总信息
                    summary = result.get('summary', {})
                    print(f"总时段数量: {summary.get('total_periods', 0)}")
                    print(f"总信号数量: {summary.get('total_signals', 0)}")
                    print(f"有信号: {'是' if summary.get('has_signals') else '否'}")
                    
                    # 显示部分信号详情
                    timeframes_data = result.get('timeframes', [])
                    for tf_data in timeframes_data[:2]:  # 只显示前两个时间周期
                        tf = tf_data.get('timeframe')
                        periods = tf_data.get('recent_periods', [])
                        print(f"  {tf} 周期: {len(periods)} 个时段")
                        for period in periods:
                            signals = period.get('signals', [])
                            if signals:
                                print(f"    时间: {period.get('timestamp')}")
                                print(f"    价格: {period.get('close')}")
                                print(f"    信号: {signals[:3]}...")  # 只显示前3个信号
                    
                    print("✅ POST查询技术信号成功")
                    return True
                else:
                    print(f"❌ 查询失败: {data.get('message')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False
    
    def test_query_signals_get(self, symbol: str = "BTC", timeframes: str = None) -> bool:
        """测试GET方式查询技术信号"""
        print(f"\n🔍 测试GET方式查询技术信号 (币种: {symbol})...")
        try:
            url = f"{self.base_url}/api/v1/signals/{symbol}"
            if timeframes:
                url += f"?timeframes={timeframes}"
            
            response = self.session.get(url)
            
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = data.get('data', {})
                    print(f"查询币种: {result.get('symbol')}")
                    print(f"时间周期数量: {len(result.get('timeframes', []))}")
                    
                    summary = result.get('summary', {})
                    print(f"总信号数量: {summary.get('total_signals', 0)}")
                    print("✅ GET查询技术信号成功")
                    return True
                else:
                    print(f"❌ 查询失败: {data.get('message')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False
    
    def test_api_docs(self) -> bool:
        """测试API文档端点"""
        print("\n🔍 测试API文档端点...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/docs")
            
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"API标题: {data.get('title')}")
                print(f"API版本: {data.get('api_version')}")
                print(f"端点数量: {len(data.get('endpoints', {}))}")
                print("✅ 获取API文档成功")
                return True
            else:
                print(f"❌ 获取文档失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """测试错误处理"""
        print("\n🔍 测试错误处理...")
        success_count = 0
        
        # 测试无效币种
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/signals",
                json={"symbol": "INVALID"}
            )
            if response.status_code == 400:
                print("✅ 无效币种错误处理正确")
                success_count += 1
            else:
                print("❌ 无效币种错误处理失败")
        except Exception as e:
            print(f"❌ 无效币种测试异常: {e}")
        
        # 测试空请求体
        try:
            response = self.session.post(f"{self.base_url}/api/v1/signals")
            if response.status_code == 400:
                print("✅ 空请求体错误处理正确")
                success_count += 1
            else:
                print("❌ 空请求体错误处理失败")
        except Exception as e:
            print(f"❌ 空请求体测试异常: {e}")
        
        # 测试无效时间周期
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/signals",
                json={"symbol": "BTC", "timeframes": ["invalid"]}
            )
            if response.status_code == 400:
                print("✅ 无效时间周期错误处理正确")
                success_count += 1
            else:
                print("❌ 无效时间周期错误处理失败")
        except Exception as e:
            print(f"❌ 无效时间周期测试异常: {e}")
        
        return success_count >= 2
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始API功能测试...\n")
        
        tests = [
            ("健康检查", self.test_health_check),
            ("支持的币种列表", self.test_supported_symbols),
            ("POST查询信号", lambda: self.test_query_signals_post("BTC", ["5m", "1h"])),
            ("GET查询信号", lambda: self.test_query_signals_get("ETH", "5m,1h")),
            ("API文档", self.test_api_docs),
            ("错误处理", self.test_error_handling),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                time.sleep(1)  # 间隔1秒
            except Exception as e:
                print(f"❌ {test_name}测试异常: {e}")
        
        print(f"\n📊 测试结果: {passed}/{total} 通过")
        success_rate = (passed / total) * 100
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 API测试总体通过！")
            return True
        else:
            print("⚠️ API测试存在问题，请检查")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试技术信号查询API')
    parser.add_argument('--url', default='http://localhost:5000', help='API服务地址')
    parser.add_argument('--test', choices=['health', 'symbols', 'signals', 'docs', 'errors', 'all'], 
                        default='all', help='要运行的测试类型')
    
    args = parser.parse_args()
    
    tester = APITester(args.url)
    
    if args.test == 'all':
        success = tester.run_all_tests()
    elif args.test == 'health':
        success = tester.test_health_check()
    elif args.test == 'symbols':
        success = tester.test_supported_symbols()
    elif args.test == 'signals':
        success = tester.test_query_signals_post() and tester.test_query_signals_get()
    elif args.test == 'docs':
        success = tester.test_api_docs()
    elif args.test == 'errors':
        success = tester.test_error_handling()
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main()) 