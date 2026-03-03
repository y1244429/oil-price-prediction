#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
原油价格预测系统配置文件
"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"
DOCS_DIR = BASE_DIR / "docs"

# 数据目录配置
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

# 输出目录配置
PREDICTIONS_DIR = OUTPUTS_DIR / "predictions"
REPORTS_DIR = OUTPUTS_DIR / "reports"
VISUALIZATIONS_DIR = OUTPUTS_DIR / "visualizations"

# 创建必要的目录
for dir_path in [DATA_DIR, MODELS_DIR, OUTPUTS_DIR,
                 RAW_DATA_DIR, PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR,
                 PREDICTIONS_DIR, REPORTS_DIR, VISUALIZATIONS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============ 数据源配置 ============

# AKShare配置
AKSHARE_ENABLED = True

# EIA API配置（需要API Key）
EIA_API_KEY = os.getenv("EIA_API_KEY", "")

# ============ 模型配置 ============

# 长期趋势模型配置
LONG_TERM_MODEL = {
    "name": "长期趋势模型",
    "horizon": 12,  # 预测12个月
    "features": {
        "supply": [
            "opec_production",
            "us_rig_count",
            "global_spare_capacity",
            "geopolitical_risk"
        ],
        "demand": [
            "global_pmi",
            "china_import",
            "us_refinery_utilization",
            "jet_fuel_demand"
        ],
        "inventory": [
            "oecd_inventory_days",
            "dollar_index",
            "cftc_net_position"
        ]
    },
    "model_type": "xgboost",
    "train_window": 24,  # 使用24个月数据训练
    "retrain_frequency": "monthly"
}

# 中期波动模型配置
MEDIUM_TERM_MODEL = {
    "name": "中期波动模型",
    "horizon": 3,  # 预测3个月
    "features": {
        "macro": [
            "dollar_index",
            "vix_index",
            "bond_spread",
            "inflation_expectation"
        ],
        "supply_demand": [
            "inventory_change",
            "rig_count",
            "refinery_throughput",
            "import_export"
        ],
        "sentiment": [
            "position_data",
            "news_sentiment",
            "search_index"
        ]
    },
    "model_type": "lightgbm",
    "train_window": 12,  # 使用12个月数据训练
    "retrain_frequency": "weekly"
}

# 短期交易模型配置
SHORT_TERM_MODEL = {
    "name": "短期交易模型",
    "horizon": 7,  # 预测7天
    "features": {
        "technical": [
            "ma_5",
            "ma_10",
            "ma_20",
            "volatility",
            "volume"
        ],
        "microstructure": [
            "order_flow",
            "vpin",
            "bid_ask_spread"
        ],
        "calendar": [
            "day_of_week",
            "month",
            "quarter"
        ]
    },
    "model_type": "lstm",
    "train_window": 60,  # 使用60天数据训练
    "retrain_frequency": "daily"
}

# 集成模型配置
ENSEMBLE_MODEL = {
    "name": "集成模型",
    "weights": {
        "long_term": 0.3,
        "medium_term": 0.4,
        "short_term": 0.3
    },
    "method": "weighted_average"
}

# ============ 基本面因子权重 ============

# 供给端因子权重
SUPPLY_FACTORS = {
    "opec_production": 0.30,
    "us_rig_count": 0.20,
    "global_spare_capacity": 0.25,
    "geopolitical_risk": 0.25
}

# 需求端因子权重
DEMAND_FACTORS = {
    "global_pmi": 0.30,
    "china_import": 0.35,
    "us_refinery_utilization": 0.20,
    "jet_fuel_demand": 0.15
}

# 库存与金融因子权重
INVENTORY_FINANCIAL_FACTORS = {
    "oecd_inventory_days": 0.35,
    "dollar_index": 0.30,
    "cftc_net_position": 0.20,
    "term_structure": 0.15
}

# ============ 情景分析配置 ============

SCENARIOS = {
    "baseline": {
        "name": "基准情景",
        "probability": 0.50,
        "price_range": [70, 85],
        "description": "供需紧平衡"
    },
    "bullish": {
        "name": "上行风险",
        "probability": 0.25,
        "price_range": [100, 120],
        "description": "地缘冲突升级"
    },
    "bearish": {
        "name": "下行风险",
        "probability": 0.25,
        "price_range": [50, 60],
        "description": "全球经济衰退"
    }
}

# ============ 风险阈值配置 ============

# 价格波动率阈值
VOLATILITY_THRESHOLDS = {
    "low": 0.15,      # 15%以下为低波动
    "medium": 0.25,   # 15%-25%为中波动
    "high": 0.25      # 25%以上为高波动
}

# 库存偏离度阈值
INVENTORY_DEVIATION_THRESHOLDS = {
    "oversupply": -10,    # 低于-10%为供应过剩
    "balanced": [-10, 10], # -10%到10%为平衡
    "shortage": 10        # 高于10%为供应短缺
}

# ============ 报告配置 ============

REPORT_CONFIG = {
    "output_format": ["html", "pptx", "txt"],  # 输出格式
    "include_charts": True,                    # 包含图表
    "include_forecasts": True,                 # 包含预测
    "include_scenarios": True,                 # 包含情景分析
    "language": "zh-CN"                        # 语言
}

# ============ 日志配置 ============

LOG_CONFIG = {
    "level": "INFO",                          # 日志级别
    "file": "logs/oil_prediction.log",        # 日志文件
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

# ============ 模型评估指标 ============

METRICS = [
    "rmse",      # 均方根误差
    "mae",       # 平均绝对误差
    "mape",      # 平均绝对百分比误差
    "r2",        # R²决定系数
    "direction_accuracy"  # 方向准确率
]

# ============ 数据更新频率 ============

DATA_UPDATE_FREQUENCY = {
    "price_data": "daily",           # 价格数据：每日
    "inventory_data": "weekly",       # 库存数据：每周
    "production_data": "monthly",     # 产量数据：每月
    "macro_data": "monthly"          # 宏观数据：每月
}

# ============ API配置 ============

API_CONFIG = {
    "timeout": 30,                    # 请求超时时间（秒）
    "retry_times": 3,                 # 重试次数
    "retry_delay": 5                  # 重试延迟（秒）
}

# ============ 显示配置 ============

DISPLAY_CONFIG = {
    "max_rows": 100,                  # 最大显示行数
    "max_columns": 50,                # 最大显示列数
    "float_format": "{:.2f}",        # 浮点数格式
    "date_format": "%Y-%m-%d"        # 日期格式
}
