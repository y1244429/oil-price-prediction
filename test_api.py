#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Web应用的所有API端点
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5003"

def test_api_endpoint(name, url, method='GET', data=None):
    """测试API端点"""
    print(f"\n{'='*60}")
    print(f"🧪 测试: {name}")
    print(f"📡 端点: {method} {url}")
    print(f"{'='*60}")

    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)

        print(f"✅ 状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 响应状态: {result.get('status', 'N/A')}")

            # 显示关键信息
            if 'data' in result:
                data = result['data']
                print(f"📊 数据项数:")
                for key, value in data.items():
                    print(f"   - {key}: {len(value)} 条记录")

            if 'predictions' in result:
                preds = result['predictions']
                print(f"🎯 预测结果:")
                if 'ensemble' in preds:
                    ensemble = preds['ensemble']
                    if 'predictions' in ensemble:
                        for period, pred in ensemble['predictions'].items():
                            print(f"   - {period}: ${pred['prediction']:.2f} (置信度: {pred['confidence']:.1%})")

            if 'factors' in result:
                factors = result['factors']
                print(f"📈 因子分析:")
                for category, data in factors.items():
                    print(f"   - {data['name']}: {data['score']}分 ({data['status']})")

            if 'scenarios' in result:
                scenarios = result['scenarios']
                print(f"🎲 情景分析:")
                for key, scenario in scenarios.items():
                    print(f"   - {scenario['name']}: {scenario['probability']:.0%}概率, ${scenario['price_range'][0]}-${scenario['price_range'][1]}")

            if 'report' in result:
                report = result['report']
                print(f"📄 报告长度: {len(report)} 字符")

            return True
        else:
            print(f"❌ 请求失败")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接失败 - 服务器可能未启动")
        return False
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print("🛢️  原油价格预测系统 - API测试")
    print(f"{'='*60}")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 基础URL: {BASE_URL}")

    # 测试所有API端点
    tests = [
        ("获取数据", f"{BASE_URL}/api/data", 'GET'),
        ("运行预测", f"{BASE_URL}/api/predict", 'POST'),
        ("获取因子", f"{BASE_URL}/api/factors", 'GET'),
        ("获取情景", f"{BASE_URL}/api/scenarios", 'GET'),
        ("生成报告", f"{BASE_URL}/api/report", 'GET'),
    ]

    results = []
    for name, url, method in tests:
        success = test_api_endpoint(name, url, method)
        results.append((name, success))

    # 总结
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print(f"{'='*60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！系统运行正常！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查服务器状态")


if __name__ == '__main__':
    main()
