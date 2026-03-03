#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
特征工程模块
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FeatureEngineering:
    """特征工程类"""

    def __init__(self):
        self.feature_names = []
        logger.info("特征工程模块初始化完成")

    def create_technical_features(self, data: pd.DataFrame, price_col: str = 'WTI_Close') -> pd.DataFrame:
        """
        创建技术分析特征

        Args:
            data: 原始数据
            price_col: 价格列名

        Returns:
            包含技术特征的DataFrame
        """
        logger.info("开始创建技术分析特征...")

        df = data.copy()

        # 移动平均线
        df['MA_5'] = df[price_col].rolling(window=5).mean()
        df['MA_10'] = df[price_col].rolling(window=10).mean()
        df['MA_20'] = df[price_col].rolling(window=20).mean()
        df['MA_60'] = df[price_col].rolling(window=60).mean()

        # 价格相对均线的位置
        df['Price_vs_MA5'] = (df[price_col] - df['MA_5']) / df['MA_5'] * 100
        df['Price_vs_MA10'] = (df[price_col] - df['MA_10']) / df['MA_10'] * 100
        df['Price_vs_MA20'] = (df[price_col] - df['MA_20']) / df['MA_20'] * 100

        # 均线排列
        df['MA_Bullish'] = ((df['MA_5'] > df['MA_10']) &
                           (df['MA_10'] > df['MA_20'])).astype(int)

        # 动量指标
        df['Momentum_5'] = df[price_col].pct_change(5)
        df['Momentum_10'] = df[price_col].pct_change(10)
        df['Momentum_20'] = df[price_col].pct_change(20)

        # 波动率
        df['Volatility_5'] = df[price_col].pct_change().rolling(window=5).std()
        df['Volatility_10'] = df[price_col].pct_change().rolling(window=10).std()
        df['Volatility_20'] = df[price_col].pct_change().rolling(window=20).std()

        # RSI（相对强弱指标）
        df['RSI_14'] = self._calculate_rsi(df[price_col], window=14)

        # MACD
        df['MACD'], df['MACD_Signal'] = self._calculate_macd(df[price_col])

        # 布林带
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = self._calculate_bollinger_bands(df[price_col])
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle'] * 100
        df['BB_Position'] = (df[price_col] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])

        # ATR（真实波幅）
        df['ATR_14'] = self._calculate_atr(df, price_col, window=14)

        logger.info(f"成功创建 {len([col for col in df.columns if col not in data.columns])} 个技术特征")
        return df

    def create_fundamental_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        创建基本面特征

        Args:
            data: 原始数据

        Returns:
            包含基本面特征的DataFrame
        """
        logger.info("开始创建基本面特征...")

        df = data.copy()

        # 供给端特征
        if 'OPEC_Production' in df.columns:
            # OPEC产量变化
            df['OPEC_Production_Change'] = df['OPEC_Production'].pct_change()
            df['OPEC_Production_MA7'] = df['OPEC_Production'].rolling(window=7).mean()

        if 'US_Rig_Count' in df.columns:
            # 美国钻机数变化
            df['US_Rig_Count_Change'] = df['US_Rig_Count'].pct_change()
            df['US_Rig_Count_MA30'] = df['US_Rig_Count'].rolling(window=30).mean()

        if 'Global_Spare_Capacity' in df.columns:
            # 全球闲置产能
            df['Spare_Capacity_Ratio'] = df['Global_Spare_Capacity'] / df['OPEC_Production']

        # 需求端特征
        if 'Global_PMI' in df.columns:
            # PMI变化
            df['PMI_Change'] = df['Global_PMI'].diff()
            df['PMI_MA30'] = df['Global_PMI'].rolling(window=30).mean()
            # PMI与50的分界线（荣枯线）
            df['PMI_Above_50'] = (df['Global_PMI'] > 50).astype(int)

        if 'China_Import' in df.columns:
            # 中国进口变化
            df['China_Import_Change'] = df['China_Import'].pct_change()
            df['China_Import_MA30'] = df['China_Import'].rolling(window=30).mean()

        if 'US_Refinery_Utilization' in df.columns:
            # 美国炼厂开工率
            df['Refinery_Utilization_Change'] = df['US_Refinery_Utilization'].diff()
            df['Refinery_Utilization_MA30'] = df['US_Refinery_Utilization'].rolling(window=30).mean()

        # 库存特征
        if 'Inventory_Deviation' in df.columns:
            # 库存偏离度分类
            df['Inventory_Status'] = pd.cut(
                df['Inventory_Deviation'],
                bins=[-np.inf, -10, 10, np.inf],
                labels=['Oversupply', 'Balanced', 'Shortage']
            ).astype(str)

        # 金融特征
        if 'Dollar_Index' in df.columns:
            # 美元指数变化
            df['Dollar_Index_Change'] = df['Dollar_Index'].pct_change()
            df['Dollar_Index_MA30'] = df['Dollar_Index'].rolling(window=30).mean()

        if 'VIX_Index' in df.columns:
            # VIX变化
            df['VIX_Index_Change'] = df['VIX_Index'].pct_change()
            df['VIX_Index_MA30'] = df['VIX_Index'].rolling(window=30).mean()

        # 价差特征
        if 'Spread' in df.columns:
            # WTI-Brent价差
            df['Spread_Change'] = df['Spread'].pct_change()
            df['Spread_MA30'] = df['Spread'].rolling(window=30).mean()
            # 价差统计特征
            df['Spread_Std'] = df['Spread'].rolling(window=30).std()
            df['Spread_ZScore'] = (df['Spread'] - df['Spread_MA30']) / df['Spread_Std']

        # 地缘政治风险特征
        if 'Geopolitical_Risk' in df.columns:
            df['GPR_Change'] = df['Geopolitical_Risk'].pct_change()
            df['GPR_MA30'] = df['Geopolitical_Risk'].rolling(window=30).mean()
            # 风险等级
            df['GPR_Level'] = pd.cut(
                df['Geopolitical_Risk'],
                bins=[-np.inf, 80, 120, np.inf],
                labels=['Low', 'Medium', 'High']
            ).astype(str)

        logger.info("成功创建基本面特征")
        return df

    def create_macro_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        创建宏观经济特征

        Args:
            data: 原始数据

        Returns:
            包含宏观特征的DataFrame
        """
        logger.info("开始创建宏观经济特征...")

        df = data.copy()

        # 滞后特征
        for lag in [1, 3, 5, 10, 20]:
            if 'WTI_Close' in df.columns:
                df[f'WTI_Close_Lag{lag}'] = df['WTI_Close'].shift(lag)
            if 'Dollar_Index' in df.columns:
                df[f'Dollar_Lag{lag}'] = df['Dollar_Index'].shift(lag)
            if 'VIX_Index' in df.columns:
                df[f'VIX_Lag{lag}'] = df['VIX_Index'].shift(lag)

        # 差分特征
        if 'WTI_Close' in df.columns:
            df['WTI_Close_Diff1'] = df['WTI_Close'].diff(1)
            df['WTI_Close_Diff5'] = df['WTI_Close'].diff(5)
            df['WTI_Close_Diff20'] = df['WTI_Close'].diff(20)

        # 滚动统计特征
        for window in [5, 10, 20, 60]:
            if 'WTI_Close' in df.columns:
                df[f'WTI_Rolling_Mean_{window}'] = df['WTI_Close'].rolling(window).mean()
                df[f'WTI_Rolling_Std_{window}'] = df['WTI_Close'].rolling(window).std()
                df[f'WTI_Rolling_Max_{window}'] = df['WTI_Close'].rolling(window).max()
                df[f'WTI_Rolling_Min_{window}'] = df['WTI_Close'].rolling(window).min()
                df[f'WTI_Rolling_Range_{window}'] = (
                    df[f'WTI_Rolling_Max_{window}'] - df[f'WTI_Rolling_Min_{window}']
                ) / df[f'WTI_Rolling_Mean_{window}'] * 100

        # 交叉特征
        if 'Dollar_Index' in df.columns and 'WTI_Close' in df.columns:
            # 美元指数与原油价格的相关性（滚动窗口）
            df['Dollar_Price_Corr_20'] = df['Dollar_Index'].rolling(20).corr(df['WTI_Close'])

        if 'VIX_Index' in df.columns and 'WTI_Close' in df.columns:
            # VIX与原油价格的相关性
            df['VIX_Price_Corr_20'] = df['VIX_Index'].rolling(20).corr(df['WTI_Close'])

        logger.info("成功创建宏观经济特征")
        return df

    def create_calendar_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        创建日历特征

        Args:
            data: 原始数据

        Returns:
            包含日历特征的DataFrame
        """
        logger.info("开始创建日历特征...")

        df = data.copy()

        # 确保索引是日期类型
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # 基础日历特征
        df['Day_of_Week'] = df.index.dayofweek
        df['Day_of_Month'] = df.index.day
        df['Week_of_Year'] = df.index.isocalendar().week
        df['Month'] = df.index.month
        df['Quarter'] = df.index.quarter
        df['Year'] = df.index.year

        # 周末标识
        df['Is_Weekend'] = (df.index.dayofweek >= 5).astype(int)

        # 月初/月末标识
        df['Is_Month_Start'] = df.index.is_month_start.astype(int)
        df['Is_Month_End'] = df.index.is_month_end.astype(int)

        # 季度标识
        df['Is_Quarter_Start'] = df.index.is_quarter_start.astype(int)
        df['Is_Quarter_End'] = df.index.is_quarter_end.astype(int)

        # 季节性特征（正弦/余弦编码）
        df['Month_Sin'] = np.sin(2 * np.pi * df['Month'] / 12)
        df['Month_Cos'] = np.cos(2 * np.pi * df['Month'] / 12)
        df['Day_of_Week_Sin'] = np.sin(2 * np.pi * df['Day_of_Week'] / 7)
        df['Day_of_Week_Cos'] = np.cos(2 * np.pi * df['Day_of_Week'] / 7)

        logger.info("成功创建日历特征")
        return df

    def create_all_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        创建所有特征

        Args:
            data: 原始数据

        Returns:
            包含所有特征的DataFrame
        """
        logger.info("开始创建所有特征...")

        df = data.copy()

        # 依次创建各类特征
        df = self.create_technical_features(df)
        df = self.create_fundamental_features(df)
        df = self.create_macro_features(df)
        df = self.create_calendar_features(df)

        # 记录特征名称
        self.feature_names = [col for col in df.columns if col not in data.columns]

        logger.info(f"特征工程完成！总共创建 {len(self.feature_names)} 个特征")
        return df

    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices: pd.Series,
                       fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
        """计算MACD指标"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        return macd, macd_signal

    def _calculate_bollinger_bands(self, prices: pd.Series,
                                    window: int = 20, num_std: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算布林带"""
        middle = prices.rolling(window).mean()
        std = prices.rolling(window).std()
        upper = middle + num_std * std
        lower = middle - num_std * std
        return upper, middle, lower

    def _calculate_atr(self, df: pd.DataFrame, price_col: str, window: int = 14) -> pd.Series:
        """计算ATR（真实波幅）"""
        high = df[price_col]
        low = df[price_col]
        close = df[price_col]

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()

        return atr


if __name__ == "__main__":
    # 测试特征工程
    from utils.data_fetcher import OilDataFetcher

    # 获取数据
    fetcher = OilDataFetcher()
    all_data = fetcher.get_all_data()

    if all_data.get('combined') is not None:
        # 创建特征
        fe = FeatureEngineering()
        featured_data = fe.create_all_features(all_data['combined'])

        print("\n" + "=" * 60)
        print("特征工程结果")
        print("=" * 60)
        print(f"原始特征数: {len(all_data['combined'].columns)}")
        print(f"新特征数: {len(fe.feature_names)}")
        print(f"总特征数: {len(featured_data.columns)}")

        print("\n新增特征:")
        for i, feature in enumerate(fe.feature_names, 1):
            print(f"{i:3d}. {feature}")
