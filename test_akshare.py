#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试AKShare数据获取
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.akshare_fetcher import AKShareFetcher
import pandas as pd

def test_akshare():
    """测试AKShare数据获取"""
    print("="*60)
    print("🧪 测试AKShare数据获取")
    print("="*60)

    fetcher = AKShareFetcher()

    # 测试1: 获取所有数据
    print("\n📊 测试1: 获取所有数据")
    print("-"*60)
    try:
        data = fetcher.get_all_data()

        print("\n✅ 数据获取成功！")
        print("\n📈 数据概览:")
        for key, df in data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                print(f"\n  {key}:")
                print(f"    - 记录数: {len(df)}")
                print(f"    - 列数: {len(df.columns)}")
                print(f"    - 日期范围: {df['date'].min()} 至 {df['date'].max()}")
                print(f"    - 列名: {list(df.columns)}")

    except Exception as e:
        print(f"\n❌ 获取数据失败: {str(e)}")
        return False

    # 测试2: 检查数据质量
    print("\n\n📊 测试2: 检查数据质量")
    print("-"*60)

    if 'combined' in data and not data['combined'].empty:
        df = data['combined']
        print(f"\n✅ 合并数据质量:")
        print(f"  - 总记录数: {len(df)}")
        print(f"  - 缺失值统计:")
        missing = df.isnull().sum()
        for col in df.columns:
            if missing[col] > 0:
                print(f"    - {col}: {missing[col]} ({missing[col]/len(df)*100:.1f}%)")
            else:
                print(f"    - {col}: ✅ 无缺失值")
    else:
        print("\n⚠️  合并数据为空")

    # 测试3: 检查价格数据
    print("\n\n📊 测试3: 检查价格数据")
    print("-"*60)

    if 'wti' in data and not data['wti'].empty:
        wti = data['wti']
        print(f"\n✅ WTI数据:")
        print(f"  - 最新价格: ${wti['close'].iloc[-1]:.2f}")
        print(f"  - 日期: {wti['date'].iloc[-1]}")
        print(f"  - 成交量: {wti['volume'].iloc[-1]:,.0f}")
    else:
        print("\n⚠️  WTI数据为空")

    if 'brent' in data and not data['brent'].empty:
        brent = data['brent']
        print(f"\n✅ Brent数据:")
        print(f"  - 最新价格: ${brent['close'].iloc[-1]:.2f}")
        print(f"  - 日期: {brent['date'].iloc[-1]}")
        print(f"  - 成交量: {brent['volume'].iloc[-1]:,.0f}")
    else:
        print("\n⚠️  Brent数据为空")

    # 测试4: 检查宏观数据
    print("\n\n📊 测试4: 检查宏观数据")
    print("-"*60)

    if 'pmi' in data and not data['pmi'].empty:
        pmi = data['pmi']
        print(f"\n✅ PMI数据:")
        print(f"  - 记录数: {len(pmi)}")
        print(f"  - 最新PMI: {pmi.iloc[-1]['当月']}")
        print(f"  - 日期: {pmi.iloc[-1]['月份']}")
    else:
        print("\n⚠️  PMI数据为空")

    # 测试5: 数据统计
    print("\n\n📊 测试5: 数据统计")
    print("-"*60)

    if 'wti' in data and not data['wti'].empty:
        wti = data['wti']
        print(f"\n✅ WTI价格统计:")
        print(f"  - 最高价: ${wti['high'].max():.2f}")
        print(f"  - 最低价: ${wti['low'].min():.2f}")
        print(f"  - 平均价: ${wti['close'].mean():.2f}")
        print(f"  - 波动率: {wti['close'].pct_change().std()*100:.2f}%")

    print("\n\n" + "="*60)
    print("🎉 AKShare数据测试完成！")
    print("="*60)

    return True


if __name__ == '__main__':
    try:
        success = test_akshare()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
