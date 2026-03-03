#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中期波动模型（1-3个月）
基于宏观流动性和美元周期
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import joblib

logger = logging.getLogger(__name__)


class MediumTermModel:
    """中期波动模型"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.metrics = {}
        self.is_fitted = False

        # 模型参数
        self.params = {
            'n_estimators': 300,
            'max_depth': 8,
            'learning_rate': 0.05,
            'num_leaves': 31,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }

        logger.info("中期波动模型初始化完成")

    def prepare_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """准备中期模型特征"""
        logger.info("准备中期模型特征...")

        df = data.copy()

        # 选择中期相关特征
        medium_term_features = []

        # 宏观因子
        macro_features = [
            'Dollar_Index', 'VIX_Index', 'Dollar_Index_Change', 'VIX_Index_Change',
            'Dollar_Index_MA30', 'VIX_Index_MA30'
        ]
        medium_term_features.extend([f for f in macro_features if f in df.columns])

        # 供需因子
        supply_demand_features = [
            'Inventory_Deviation', 'OPEC_Production_Change', 'US_Refinery_Utilization_Change',
            'China_Import_Change', 'Inventory_Deviation'
        ]
        medium_term_features.extend([f for f in supply_demand_features if f in df.columns])

        # 技术因子（中期）
        technical_features = [
            'MA_10', 'MA_20', 'Price_vs_MA10', 'Price_vs_MA20',
            'Momentum_10', 'Volatility_10', 'RSI_14', 'MACD'
        ]
        medium_term_features.extend([f for f in technical_features if f in df.columns])

        # 滞后特征
        lag_features = [
            'WTI_Close_Lag1', 'WTI_Close_Lag3', 'WTI_Close_Lag5',
            'WTI_Close_Diff1', 'WTI_Close_Diff5'
        ]
        medium_term_features.extend([f for f in lag_features if f in df.columns])

        # 筛选存在的特征
        available_features = [f for f in medium_term_features if f in df.columns]

        logger.info(f"中期模型使用 {len(available_features)} 个特征")
        return df[available_features], available_features

    def prepare_target(self, data: pd.DataFrame, horizon: int = 3) -> pd.Series:
        """准备目标变量（未来价格变化率）"""
        if 'WTI_Close' not in data.columns:
            raise ValueError("数据中缺少 WTI_Close 列")

        # 计算未来价格（假设每周一个数据点，3个月约12周）
        future_price = data['WTI_Close'].shift(-horizon * 4)
        current_price = data['WTI_Close']

        target = (future_price - current_price) / current_price * 100
        return target

    def train(self, data: pd.DataFrame, horizon: int = 3) -> Dict:
        """训练模型"""
        logger.info("=" * 60)
        logger.info("开始训练中期波动模型...")
        logger.info("=" * 60)

        # 准备特征和目标
        features_df, feature_names = self.prepare_features(data)
        target = self.prepare_target(data, horizon=horizon)

        # 删除缺失值
        valid_idx = ~(features_df.isna().any(axis=1) | target.isna())
        X = features_df[valid_idx]
        y = target[valid_idx]

        logger.info(f"训练样本数: {len(X)}")
        logger.info(f"特征数: {len(feature_names)}")

        # 训练LightGBM模型
        self.model = lgb.LGBMRegressor(**self.params, verbose=-1)

        # 训练
        self.model.fit(X, y)

        # 预测
        y_pred = self.model.predict(X)

        # 计算指标
        self.metrics['RMSE'] = np.sqrt(mean_squared_error(y, y_pred))
        self.metrics['MAE'] = mean_absolute_error(y, y_pred)
        self.metrics['R2'] = r2_score(y, y_pred)

        # 特征重要性
        self.feature_importance = dict(zip(
            feature_names,
            self.model.feature_importances_
        ))
        self.feature_importance = dict(sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))

        self.is_fitted = True

        logger.info("=" * 60)
        logger.info("训练完成！")
        logger.info(f"RMSE: {self.metrics['RMSE']:.4f}")
        logger.info(f"MAE: {self.metrics['MAE']:.4f}")
        logger.info(f"R²: {self.metrics['R2']:.4f}")
        logger.info("=" * 60)

        return self.metrics

    def predict(self, data: pd.DataFrame, horizon: int = 3) -> pd.DataFrame:
        """预测"""
        if not self.is_fitted:
            raise ValueError("模型未训练，请先调用 train()")

        logger.info(f"开始中期预测（{horizon}个月）...")

        # 准备特征
        features_df, _ = self.prepare_features(data)

        # 预测价格变化率
        prediction = self.model.predict(features_df.iloc[[-1]])[0]

        # 当前价格
        current_price = data['WTI_Close'].iloc[-1]

        # 计算预测价格
        predicted_price = current_price * (1 + prediction / 100)

        result = {
            'model_type': '中期波动模型',
            'horizon': f'{horizon}个月',
            'current_price': current_price,
            'predicted_change': prediction,
            'predicted_price': predicted_price,
            'confidence_interval': {
                'lower': current_price * (1 + (prediction - 2 * self.metrics['RMSE']) / 100),
                'upper': current_price * (1 + (prediction + 2 * self.metrics['RMSE']) / 100)
            },
            'key_drivers': list(self.feature_importance.keys())[:5],
            'model_metrics': self.metrics
        }

        logger.info(f"当前价格: ${current_price:.2f}")
        logger.info(f"预测价格: ${predicted_price:.2f} ({prediction:+.2f}%)")

        return pd.DataFrame([result])

    def save_model(self, filepath: Path):
        """保存模型"""
        if not self.is_fitted:
            raise ValueError("模型未训练")

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'metrics': self.metrics,
            'feature_importance': self.feature_importance,
            'params': self.params,
            'config': self.config
        }

        joblib.dump(model_data, filepath)
        logger.info(f"模型已保存到: {filepath}")

    def load_model(self, filepath: Path):
        """加载模型"""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.metrics = model_data['metrics']
        self.feature_importance = model_data['feature_importance']
        self.params = model_data['params']
        self.config = model_data['config']
        self.is_fitted = True

        logger.info(f"模型已从 {filepath} 加载")
