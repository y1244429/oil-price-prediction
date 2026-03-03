#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
长期趋势模型（6-12个月）
基于全球供需平衡表和基本面因子
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import logging
from typing import Dict, List, Optional, Tuple, Tuple
from pathlib import Path
import joblib
import json

logger = logging.getLogger(__name__)


class LongTermModel:
    """长期趋势模型"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.metrics = {}
        self.is_fitted = False

        # 模型参数
        self.params = {
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }

        logger.info("长期趋势模型初始化完成")

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        准备长期模型的特征

        Args:
            data: 原始数据

        Returns:
            特征矩阵
        """
        logger.info("准备长期模型特征...")

        df = data.copy()

        # 选择长期相关特征
        long_term_features = []

        # 供给端特征
        supply_features = [
            'OPEC_Production', 'US_Rig_Count', 'Global_Spare_Capacity',
            'Geopolitical_Risk', 'OPEC_Production_Change', 'US_Rig_Count_Change'
        ]
        long_term_features.extend([f for f in supply_features if f in df.columns])

        # 需求端特征
        demand_features = [
            'Global_PMI', 'China_Import', 'US_Refinery_Utilization',
            'Jet_Fuel_Demand', 'PMI_Change', 'China_Import_Change'
        ]
        long_term_features.extend([f for f in demand_features if f in df.columns])

        # 库存与金融特征
        inventory_financial_features = [
            'Inventory_Deviation', 'Dollar_Index', 'CFTC_Net_Position',
            'Dollar_Index_Change', 'Spread'
        ]
        long_term_features.extend([f for f in inventory_financial_features if f in df.columns])

        # 技术特征（长期均线）
        technical_features = [
            'MA_20', 'MA_60', 'Price_vs_MA20',
            'Volatility_20', 'BB_Width'
        ]
        long_term_features.extend([f for f in technical_features if f in df.columns])

        # 筛选存在的特征
        available_features = [f for f in long_term_features if f in df.columns]

        logger.info(f"长期模型使用 {len(available_features)} 个特征")
        logger.info(f"特征列表: {available_features}")

        return df[available_features], available_features

    def prepare_target(self, data: pd.DataFrame, horizon: int = 12) -> pd.Series:
        """
        准备目标变量（未来价格）

        Args:
            data: 原始数据
            horizon: 预测周期（月）

        Returns:
            目标变量
        """
        if 'WTI_Close' not in data.columns:
            raise ValueError("数据中缺少 WTI_Close 列")

        # 计算未来价格变化率
        future_price = data['WTI_Close'].shift(-horizon)
        current_price = data['WTI_Close']

        # 计算目标：未来价格相对于当前价格的变化率
        target = (future_price - current_price) / current_price * 100

        return target

    def train(self, data: pd.DataFrame, horizon: int = 12) -> Dict:
        """
        训练模型

        Args:
            data: 训练数据
            horizon: 预测周期（月）

        Returns:
            训练指标
        """
        logger.info("=" * 60)
        logger.info("开始训练长期趋势模型...")
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

        # 时间序列分割
        tscv = TimeSeriesSplit(n_splits=5)

        # 训练XGBoost模型
        self.model = xgb.XGBRegressor(**self.params)

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

        # 打印特征重要性
        logger.info("\n特征重要性（Top 10）:")
        for i, (feature, importance) in enumerate(list(self.feature_importance.items())[:10], 1):
            logger.info(f"{i:2d}. {feature:30s}: {importance:.4f}")

        return self.metrics

    def predict(self, data: pd.DataFrame, horizon: int = 12) -> pd.DataFrame:
        """
        预测

        Args:
            data: 预测数据
            horizon: 预测周期（月）

        Returns:
            预测结果
        """
        if not self.is_fitted:
            raise ValueError("模型未训练，请先调用 train()")

        logger.info(f"开始长期预测（{horizon}个月）...")

        # 准备特征
        features_df, _ = self.prepare_features(data)

        # 预测价格变化率
        prediction = self.model.predict(features_df.iloc[[-1]])[0]

        # 当前价格
        current_price = data['WTI_Close'].iloc[-1]

        # 计算预测价格
        predicted_price = current_price * (1 + prediction / 100)

        # 创建情景分析
        scenarios = self._create_scenarios(current_price, prediction)

        result = {
            'model_type': '长期趋势模型',
            'horizon': f'{horizon}个月',
            'current_price': current_price,
            'predicted_change': prediction,
            'predicted_price': predicted_price,
            'confidence_interval': {
                'lower': current_price * (1 + (prediction - 2 * self.metrics['RMSE']) / 100),
                'upper': current_price * (1 + (prediction + 2 * self.metrics['RMSE']) / 100)
            },
            'scenarios': scenarios,
            'key_drivers': list(self.feature_importance.keys())[:5],
            'model_metrics': self.metrics
        }

        logger.info(f"当前价格: ${current_price:.2f}")
        logger.info(f"预测价格: ${predicted_price:.2f} ({prediction:+.2f}%)")

        return pd.DataFrame([result])

    def _create_scenarios(self, current_price: float, base_prediction: float) -> Dict:
        """
        创建情景分析

        Args:
            current_price: 当前价格
            base_prediction: 基准预测

        Returns:
            情景分析结果
        """
        scenarios = {
            'baseline': {
                'name': '基准情景',
                'probability': 0.50,
                'price': current_price * (1 + base_prediction / 100),
                'description': '供需紧平衡'
            },
            'bullish': {
                'name': '上行风险',
                'probability': 0.25,
                'price': current_price * (1 + (base_prediction + 10) / 100),
                'description': '地缘冲突升级、供应中断'
            },
            'bearish': {
                'name': '下行风险',
                'probability': 0.25,
                'price': current_price * (1 + (base_prediction - 10) / 100),
                'description': '全球经济衰退、需求疲软'
            }
        }

        return scenarios

    def save_model(self, filepath: Path):
        """
        保存模型

        Args:
            filepath: 保存路径
        """
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
        """
        加载模型

        Args:
            filepath: 模型路径
        """
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.metrics = model_data['metrics']
        self.feature_importance = model_data['feature_importance']
        self.params = model_data['params']
        self.config = model_data['config']
        self.is_fitted = True

        logger.info(f"模型已从 {filepath} 加载")


if __name__ == "__main__":
    # 测试长期模型
    from utils.data_fetcher import OilDataFetcher
    from utils.feature_engineering import FeatureEngineering

    # 获取数据
    logger.info("开始测试长期趋势模型...")
    fetcher = OilDataFetcher()
    all_data = fetcher.get_all_data()

    if all_data.get('combined') is not None:
        # 特征工程
        fe = FeatureEngineering()
        featured_data = fe.create_all_features(all_data['combined'])

        # 训练模型
        model = LongTermModel()
        metrics = model.train(featured_data, horizon=12)

        # 预测
        prediction = model.predict(featured_data, horizon=12)
        print("\n预测结果:")
        print(prediction.to_string())
