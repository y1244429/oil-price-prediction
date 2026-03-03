#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
原油价格预测系统主程序
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import *
from utils.data_fetcher import OilDataFetcher
from utils.feature_engineering import FeatureEngineering
from utils.report_generator import ReportGenerator
from models.long_term import LongTermModel
from models.medium_term import MediumTermModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OilPricePredictionSystem:
    """原油价格预测系统"""

    def __init__(self):
        self.fetcher = OilDataFetcher()
        self.fe = FeatureEngineering()
        self.report_generator = ReportGenerator()

        self.long_term_model = LongTermModel(LONG_TERM_MODEL)
        self.medium_term_model = MediumTermModel(MEDIUM_TERM_MODEL)

        self.data = None
        self.featured_data = None
        self.predictions = {}

        logger.info("原油价格预测系统初始化完成")

    def run_full_prediction(self):
        """运行完整预测"""
        logger.info("=" * 80)
        logger.info("开始运行完整原油价格预测系统")
        logger.info("=" * 80)

        # 1. 数据获取
        self.data = self.fetcher.get_all_data()

        if self.data.get('combined') is None:
            logger.error("数据获取失败！")
            return

        # 保存原始数据
        self.fetcher.save_data(self.data['combined'], 'oil_market_data.csv')

        # 2. 特征工程
        logger.info("\n" + "=" * 80)
        logger.info("第二步：特征工程")
        logger.info("=" * 80)
        self.featured_data = self.fe.create_all_features(self.data['combined'])

        # 3. 训练和预测
        logger.info("\n" + "=" * 80)
        logger.info("第三步：模型训练与预测")
        logger.info("=" * 80)

        # 长期趋势模型
        logger.info("\n【长期趋势模型（6-12个月）】")
        self.long_term_model.train(self.featured_data, horizon=12)
        self.predictions['long_term'] = self.long_term_model.predict(self.featured_data, horizon=12)

        # 中期波动模型
        logger.info("\n【中期波动模型（1-3个月）】")
        self.medium_term_model.train(self.featured_data, horizon=3)
        self.predictions['medium_term'] = self.medium_term_model.predict(self.featured_data, horizon=3)

        # 4. 集成预测
        logger.info("\n" + "=" * 80)
        logger.info("第四步：集成预测")
        logger.info("=" * 80)
        self.predictions['ensemble'] = self._ensemble_predictions()

        # 5. 生成报告
        logger.info("\n" + "=" * 80)
        logger.info("第五步：生成报告")
        logger.info("=" * 80)
        self.generate_reports()

        logger.info("\n" + "=" * 80)
        logger.info("预测完成！")
        logger.info("=" * 80)

        # 打印汇总
        self.print_summary()

    def run_long_term_only(self):
        """仅运行长期趋势模型"""
        logger.info("=" * 80)
        logger.info("运行长期趋势模型")
        logger.info("=" * 80)

        self.data = self.fetcher.get_all_data()

        if self.data.get('combined') is None:
            logger.error("数据获取失败！")
            return

        self.featured_data = self.fe.create_all_features(self.data['combined'])

        self.long_term_model.train(self.featured_data, horizon=12)
        self.predictions['long_term'] = self.long_term_model.predict(self.featured_data, horizon=12)

        self.print_long_term_summary()

    def run_medium_term_only(self):
        """仅运行中期波动模型"""
        logger.info("=" * 80)
        logger.info("运行中期波动模型")
        logger.info("=" * 80)

        self.data = self.fetcher.get_all_data()

        if self.data.get('combined') is None:
            logger.error("数据获取失败！")
            return

        self.featured_data = self.fe.create_all_features(self.data['combined'])

        self.medium_term_model.train(self.featured_data, horizon=3)
        self.predictions['medium_term'] = self.medium_term_model.predict(self.featured_data, horizon=3)

        self.print_medium_term_summary()

    def _ensemble_predictions(self) -> pd.DataFrame:
        """集成预测"""
        logger.info("开始集成预测...")

        # 获取各模型预测
        long_pred = self.predictions['long_term'].iloc[0]
        medium_pred = self.predictions['medium_term'].iloc[0]

        # 加权平均
        weights = ENSEMBLE_MODEL['weights']
        ensemble_change = (
            weights['long_term'] * long_pred['predicted_change'] +
            weights['medium_term'] * medium_pred['predicted_change']
        )

        current_price = long_pred['current_price']
        ensemble_price = current_price * (1 + ensemble_change / 100)

        # 计算置信区间
        ensemble_rmse = np.sqrt(
            weights['long_term'] * long_pred['model_metrics']['RMSE']**2 +
            weights['medium_term'] * medium_pred['model_metrics']['RMSE']**2
        )

        result = {
            'model_type': '集成模型',
            'horizon': '综合预测',
            'current_price': current_price,
            'predicted_change': ensemble_change,
            'predicted_price': ensemble_price,
            'confidence_interval': {
                'lower': current_price * (1 + (ensemble_change - 2 * ensemble_rmse) / 100),
                'upper': current_price * (1 + (ensemble_change + 2 * ensemble_rmse) / 100)
            },
            'long_term_contribution': {
                'prediction': long_pred['predicted_change'],
                'weight': weights['long_term']
            },
            'medium_term_contribution': {
                'prediction': medium_pred['predicted_change'],
                'weight': weights['medium_term']
            },
            'ensemble_rmse': ensemble_rmse
        }

        logger.info(f"集成预测: ${ensemble_price:.2f} ({ensemble_change:+.2f}%)")
        logger.info(f"置信区间: [${current_price * (1 + (ensemble_change - 2 * ensemble_rmse) / 100):.2f}, "
                   f"${current_price * (1 + (ensemble_change + 2 * ensemble_rmse) / 100):.2f}]")

        return pd.DataFrame([result])

    def generate_reports(self):
        """生成报告"""
        logger.info("生成分析报告...")

        # 生成文本报告
        report_generator = ReportGenerator()
        report_generator.generate_text_report(
            self.data,
            self.predictions,
            REPORTS_DIR
        )

        # 生成HTML报告
        report_generator.generate_html_report(
            self.data,
            self.predictions,
            REPORTS_DIR
        )

        logger.info("报告生成完成！")

    def print_summary(self):
        """打印预测汇总"""
        logger.info("\n" + "=" * 80)
        logger.info("预测结果汇总")
        logger.info("=" * 80)

        # 当前价格
        current_price = self.predictions['long_term'].iloc[0]['current_price']

        logger.info(f"\n【当前市场价格】")
        logger.info(f"  WTI原油价格: ${current_price:.2f}/桶")

        # 长期预测
        logger.info(f"\n【长期趋势模型（6-12个月）】")
        long_pred = self.predictions['long_term'].iloc[0]
        logger.info(f"  预测价格: ${long_pred['predicted_price']:.2f}/桶 "
                   f"({long_pred['predicted_change']:+.2f}%)")
        logger.info(f"  置信区间: [${long_pred['confidence_interval']['lower']:.2f}, "
                   f"${long_pred['confidence_interval']['upper']:.2f}]")
        logger.info(f"  关键驱动因素: {', '.join(long_pred['key_drivers'])}")

        # 中期预测
        logger.info(f"\n【中期波动模型（1-3个月）】")
        medium_pred = self.predictions['medium_term'].iloc[0]
        logger.info(f"  预测价格: ${medium_pred['predicted_price']:.2f}/桶 "
                   f"({medium_pred['predicted_change']:+.2f}%)")
        logger.info(f"  置信区间: [${medium_pred['confidence_interval']['lower']:.2f}, "
                   f"${medium_pred['confidence_interval']['upper']:.2f}]")
        logger.info(f"  关键驱动因素: {', '.join(medium_pred['key_drivers'])}")

        # 集成预测
        logger.info(f"\n【集成预测】")
        ensemble_pred = self.predictions['ensemble'].iloc[0]
        logger.info(f"  预测价格: ${ensemble_pred['predicted_price']:.2f}/桶 "
                   f"({ensemble_pred['predicted_change']:+.2f}%)")
        logger.info(f"  置信区间: [${ensemble_pred['confidence_interval']['lower']:.2f}, "
                   f"${ensemble_pred['confidence_interval']['upper']:.2f}]")

        # 情景分析
        logger.info(f"\n【情景分析】")
        scenarios = long_pred['scenarios']
        for scenario_name, scenario in scenarios.items():
            logger.info(f"  {scenario['name']} (概率{scenario['probability']:.0%}): "
                       f"${scenario['price']:.2f}/桶 - {scenario['description']}")

        logger.info("\n" + "=" * 80)

    def print_long_term_summary(self):
        """打印长期模型汇总"""
        pred = self.predictions['long_term'].iloc[0]

        logger.info(f"\n【长期趋势模型预测结果】")
        logger.info(f"  当前价格: ${pred['current_price']:.2f}/桶")
        logger.info(f"  预测价格: ${pred['predicted_price']:.2f}/桶 "
                   f"({pred['predicted_change']:+.2f}%)")
        logger.info(f"  置信区间: [${pred['confidence_interval']['lower']:.2f}, "
                   f"${pred['confidence_interval']['upper']:.2f}]")

    def print_medium_term_summary(self):
        """打印中期模型汇总"""
        pred = self.predictions['medium_term'].iloc[0]

        logger.info(f"\n【中期波动模型预测结果】")
        logger.info(f"  当前价格: ${pred['current_price']:.2f}/桶")
        logger.info(f"  预测价格: ${pred['predicted_price']:.2f}/桶 "
                   f"({pred['predicted_change']:+.2f}%)")
        logger.info(f"  置信区间: [${pred['confidence_interval']['lower']:.2f}, "
                   f"${pred['confidence_interval']['upper']:.2f}]")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='原油价格预测系统')

    parser.add_argument(
        '--full',
        action='store_true',
        help='运行完整预测（默认）'
    )

    parser.add_argument(
        '--model',
        choices=['long-term', 'medium-term', 'short-term'],
        help='指定运行模型'
    )

    parser.add_argument(
        '--demo',
        action='store_true',
        help='演示模式'
    )

    args = parser.parse_args()

    # 创建系统实例
    system = OilPricePredictionSystem()

    # 根据参数运行
    if args.model == 'long-term':
        system.run_long_term_only()
    elif args.model == 'medium-term':
        system.run_medium_term_only()
    else:
        # 默认运行完整预测
        system.run_full_prediction()


if __name__ == "__main__":
    main()
