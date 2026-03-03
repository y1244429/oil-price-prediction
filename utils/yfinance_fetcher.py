#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
yFinance数据获取器
使用yfinance获取原油市场相关数据
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)


class YFinanceFetcher:
    """yFinance数据获取器"""

    def __init__(self):
        """初始化yFinance获取器"""
        logger.info("yFinance数据获取器初始化完成")
        self.request_delay = 2  # 请求间隔（秒）

    def _retry_request(self, func, max_retries=3, *args, **kwargs):
        """
        重试请求机制

        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果
        """
        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * self.request_delay
                    logger.warning(f"请求失败，{wait_time}秒后重试 ({attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"请求失败，已达到最大重试次数: {str(e)}")
                    raise

        return None

    def get_crude_oil_prices(self, period: str = "1y") -> Dict[str, pd.DataFrame]:
        """
        获取原油价格数据（WTI和Brent）

        Args:
            period: 时间周期，可选值: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'

        Returns:
            包含WTI和Brent数据的字典
        """
        results = {}

        try:
            logger.info(f"开始获取原油价格数据（周期: {period}）...")

            # 获取WTI原油期货 (CL=F) - 使用重试机制
            def get_wti():
                wti_ticker = yf.Ticker("CL=F")
                return wti_ticker.history(period=period, progress=False)

            try:
                wti_data = self._retry_request(get_wti, max_retries=3)

                if wti_data is not None and not wti_data.empty:
                    wti_data = wti_data.reset_index()
                    wti_data = wti_data.rename(columns={
                        'Date': 'date',
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume'
                    })

                    # 添加price字段（使用收盘价）
                    wti_data['price'] = wti_data['close']

                    # 转换日期格式
                    wti_data['date'] = pd.to_datetime(wti_data['date'])

                    results['wti'] = wti_data
                    logger.info(f"✅ 获取WTI数据成功: {len(wti_data)}条记录")
                    logger.info(f"   最新价格: ${wti_data['price'].iloc[-1]:.2f}")
                else:
                    logger.warning("⚠️  WTI数据为空")

            except Exception as e:
                logger.error(f"❌ 获取WTI数据失败: {str(e)}")

            # 添加延迟，避免请求过快
            time.sleep(self.request_delay)

            # 获取Brent原油期货 (BZ=F) - 使用重试机制
            def get_brent():
                brent_ticker = yf.Ticker("BZ=F")
                return brent_ticker.history(period=period, progress=False)

            try:
                brent_data = self._retry_request(get_brent, max_retries=3)

                if brent_data is not None and not brent_data.empty:
                    brent_data = brent_data.reset_index()
                    brent_data = brent_data.rename(columns={
                        'Date': 'date',
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume'
                    })

                    # 添加price字段（使用收盘价）
                    brent_data['price'] = brent_data['close']

                    # 转换日期格式
                    brent_data['date'] = pd.to_datetime(brent_data['date'])

                    results['brent'] = brent_data
                    logger.info(f"✅ 获取Brent数据成功: {len(brent_data)}条记录")
                    logger.info(f"   最新价格: ${brent_data['price'].iloc[-1]:.2f}")
                else:
                    logger.warning("⚠️  Brent数据为空")

            except Exception as e:
                logger.error(f"❌ 获取Brent数据失败: {str(e)}")

        except Exception as e:
            logger.error(f"❌ 获取原油价格数据失败: {str(e)}")

        return results

    def get_commodity_data(self, symbols: list, period: str = "1y") -> Dict[str, pd.DataFrame]:
        """
        获取大宗商品数据

        Args:
            symbols: 商品代码列表，如 ['CL=F', 'BZ=F', 'NG=F']
            period: 时间周期

        Returns:
            包含各商品数据的字典
        """
        results = {}

        try:
            logger.info(f"开始获取大宗商品数据...")

            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period=period, progress=False)

                    if not data.empty:
                        data = data.reset_index()
                        data = data.rename(columns={
                            'Date': 'date',
                            'Open': 'open',
                            'High': 'high',
                            'Low': 'low',
                            'Close': 'close',
                            'Volume': 'volume'
                        })
                        data['date'] = pd.to_datetime(data['date'])
                        data['price'] = data['close']

                        results[symbol] = data
                        logger.info(f"✅ 获取{symbol}数据成功: {len(data)}条")

                except Exception as e:
                    logger.warning(f"⚠️  获取{symbol}数据失败: {str(e)}")

        except Exception as e:
            logger.error(f"❌ 获取大宗商品数据失败: {str(e)}")

        return results

    def get_dollar_index(self, period: str = "1y") -> pd.DataFrame:
        """
        获取美元指数

        Args:
            period: 时间周期

        Returns:
            包含美元指数数据的DataFrame
        """
        try:
            logger.info("获取美元指数数据...")

            # 使用美元指数期货 (DX=F)
            ticker = yf.Ticker("DX=F")
            data = ticker.history(period=period, progress=False)

            if not data.empty:
                data = data.reset_index()
                data = data.rename(columns={
                    'Date': 'date',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
                data['date'] = pd.to_datetime(data['date'])
                data['value'] = data['close']

                # 计算日变化
                data['change'] = data['value'].diff()

                logger.info(f"✅ 获取美元指数成功: {len(data)}条记录")
                logger.info(f"   最新指数: {data['value'].iloc[-1]:.2f}")

                return data
            else:
                logger.warning("⚠️  美元指数数据为空")
                return self._generate_mock_dollar_index(period)

        except Exception as e:
            logger.error(f"❌ 获取美元指数失败: {str(e)}")
            return self._generate_mock_dollar_index(period)

    def get_oil_etfs(self, period: str = "1y") -> Dict[str, pd.DataFrame]:
        """
        获取原油ETF数据

        Args:
            period: 时间周期

        Returns:
            包含ETF数据的字典
        """
        results = {}
        etfs = {
            'USO': 'USO (美国原油ETF)',
            'BNO': 'BNO (布伦特原油ETF)',
            'XLE': 'XLE (能源板块ETF)'
        }

        try:
            logger.info("获取原油ETF数据...")

            for symbol, name in etfs.items():
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period=period, progress=False)

                    if not data.empty:
                        data = data.reset_index()
                        data = data.rename(columns={
                            'Date': 'date',
                            'Open': 'open',
                            'High': 'high',
                            'Low': 'low',
                            'Close': 'close',
                            'Volume': 'volume'
                        })
                        data['date'] = pd.to_datetime(data['date'])
                        data['price'] = data['close']

                        results[symbol] = data
                        logger.info(f"✅ 获取{name}成功: {len(data)}条")

                except Exception as e:
                    logger.warning(f"⚠️  获取{name}失败: {str(e)}")

        except Exception as e:
            logger.error(f"❌ 获取原油ETF数据失败: {str(e)}")

        return results

    def get_all_data(self, period: str = "1y") -> Dict[str, pd.DataFrame]:
        """
        获取所有原油市场数据

        Args:
            period: 时间周期

        Returns:
            包含所有数据的字典
        """
        logger.info("="*60)
        logger.info("开始使用yFinance获取所有原油市场数据...")
        logger.info("="*60)

        results = {}

        # 1. 获取原油期货价格
        logger.info("1. 获取原油期货价格...")
        futures_data = self.get_crude_oil_prices(period)
        results.update(futures_data)

        # 2. 获取美元指数
        logger.info("2. 获取美元指数...")
        dollar_data = self.get_dollar_index(period)
        results['dollar_index'] = dollar_data

        # 3. 生成其他模拟数据（yFinance不提供）
        logger.info("3. 生成其他市场数据（模拟）...")

        # EIA库存（模拟）
        results['eia_inventory'] = self._generate_mock_inventory(period)
        logger.info("   EIA库存数据: 模拟")

        # OPEC产量（模拟）
        results['opec_production'] = self._generate_mock_opec_production(period)
        logger.info("   OPEC产量数据: 模拟")

        # 钻机数（模拟）
        results['rig_count'] = self._generate_mock_rig_count(period)
        logger.info("   钻机数数据: 模拟")

        # VIX（使用真实数据）
        logger.info("4. 获取VIX指数...")
        vix_data = self._get_vix(period)
        results['vix'] = vix_data

        # 5. 合并数据
        logger.info("5. 合并数据...")
        combined = self._merge_data(results)
        results['combined'] = combined

        logger.info("="*60)
        logger.info("yFinance数据获取完成")
        logger.info("="*60)

        return results

    def _get_vix(self, period: str = "1y") -> pd.DataFrame:
        """获取VIX指数"""
        try:
            # 使用VIX期货 (^VIX)
            ticker = yf.Ticker("^VIX")
            data = ticker.history(period=period, progress=False)

            if not data.empty:
                data = data.reset_index()
                data = data.rename(columns={
                    'Date': 'date',
                    'Close': 'value'
                })
                data['date'] = pd.to_datetime(data['date'])
                data = data[['date', 'value']]

                logger.info(f"✅ 获取VIX成功: {len(data)}条记录")
                logger.info(f"   最新VIX: {data['value'].iloc[-1]:.2f}")

                return data
            else:
                logger.warning("⚠️  VIX数据为空，使用模拟数据")
                return self._generate_mock_vix(period)

        except Exception as e:
            logger.warning(f"⚠️  获取VIX失败: {str(e)}，使用模拟数据")
            return self._generate_mock_vix(period)

    def _merge_data(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """合并所有数据到统一的时间序列"""
        try:
            # 找到日期范围最大的数据集
            main_data = None
            for key, df in data_dict.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    if 'date' in df.columns:
                        if main_data is None or len(df) > len(main_data):
                            main_data = df
                            main_key = key

            if main_data is None:
                logger.warning("没有找到有效的主数据集")
                return pd.DataFrame()

            # 合并其他数据
            combined = main_data.copy()

            for key, df in data_dict.items():
                if key == 'combined':
                    continue

                if isinstance(df, pd.DataFrame) and not df.empty and 'date' in df.columns:
                    if key != main_key:
                        for col in df.columns:
                            if col != 'date' and col not in combined.columns:
                                combined = pd.merge(
                                    combined,
                                    df[['date', col]],
                                    on='date',
                                    how='left'
                                )

            logger.info(f"数据合并完成，共{len(combined)}条记录")
            return combined

        except Exception as e:
            logger.error(f"数据合并失败: {str(e)}")
            return pd.DataFrame()

    def _generate_mock_dollar_index(self, period: str = "1y") -> pd.DataFrame:
        """生成模拟美元指数数据"""
        # 根据period参数确定天数
        period_days = {
            '1mo': 30,
            '3mo': 90,
            '6mo': 180,
            '1y': 365,
            '2y': 730,
            '5y': 1825
        }
        days = period_days.get(period, 365)

        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        np.random.seed(42)
        df = pd.DataFrame({
            'date': dates,
            'value': 103 + np.cumsum(np.random.randn(days) * 0.2),
            'change': np.random.randn(days) * 0.1
        })
        return df

    def _generate_mock_vix(self, period: str = "1y") -> pd.DataFrame:
        """生成模拟VIX指数数据"""
        period_days = {
            '1mo': 30,
            '3mo': 90,
            '6mo': 180,
            '1y': 365,
            '2y': 730,
            '5y': 1825
        }
        days = period_days.get(period, 365)

        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        np.random.seed(43)
        df = pd.DataFrame({
            'date': dates,
            'value': 18 + np.random.randn(days) * 2
        })
        return df

    def _generate_mock_inventory(self, period: str = "1y") -> pd.DataFrame:
        """生成模拟库存数据"""
        period_weeks = {
            '1mo': 4,
            '3mo': 12,
            '6mo': 26,
            '1y': 52,
            '2y': 104
        }
        weeks = period_weeks.get(period, 52)

        dates = pd.date_range(end=datetime.now(), periods=weeks, freq='W-MON')
        np.random.seed(44)
        df = pd.DataFrame({
            'date': dates,
            'inventory': 400 + np.cumsum(np.random.randn(weeks) * 2),
            'change': np.random.randn(weeks) * 2
        })
        return df

    def _generate_mock_opec_production(self, period: str = "1y") -> pd.DataFrame:
        """生成模拟OPEC产量数据"""
        period_months = {
            '1mo': 1,
            '3mo': 3,
            '6mo': 6,
            '1y': 12,
            '2y': 24
        }
        months = period_months.get(period, 12)

        dates = pd.date_range(end=datetime.now(), periods=months, freq='ME')
        np.random.seed(45)
        df = pd.DataFrame({
            'date': dates,
            'production': 2800 + np.cumsum(np.random.randn(months) * 5),
            'quota': 2800
        })
        return df

    def _generate_mock_rig_count(self, period: str = "1y") -> pd.DataFrame:
        """生成模拟钻机数数据"""
        period_weeks = {
            '1mo': 4,
            '3mo': 12,
            '6mo': 26,
            '1y': 52,
            '2y': 104
        }
        weeks = period_weeks.get(period, 52)

        dates = pd.date_range(end=datetime.now(), periods=weeks, freq='W-MON')
        np.random.seed(46)
        df = pd.DataFrame({
            'date': dates,
            'count': 480 + np.cumsum(np.random.randn(weeks) * 0.5)
        })
        return df


if __name__ == '__main__':
    # 测试yFinance获取器
    logging.basicConfig(level=logging.INFO)

    fetcher = YFinanceFetcher()
    data = fetcher.get_all_data()

    print("\n获取到的数据:")
    for key, df in data.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            print(f"\n{key}: {len(df)}条记录")
            if 'price' in df.columns:
                print(f"  最新价格: ${df['price'].iloc[-1]:.2f}")
            elif 'value' in df.columns:
                print(f"  最新值: {df['value'].iloc[-1]:.2f}")
