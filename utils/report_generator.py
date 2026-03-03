#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告生成器模块
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""

    def __init__(self):
        self.report_time = datetime.now()
        logger.info("报告生成器初始化完成")

    def generate_text_report(self, data: dict, predictions: dict, output_dir: Path):
        """
        生成文本报告

        Args:
            data: 原始数据
            predictions: 预测结果
            output_dir: 输出目录
        """
        logger.info("生成文本报告...")

        timestamp = self.report_time.strftime('%Y%m%d_%H%M%S')
        report_path = output_dir / f'oil_prediction_report_{timestamp}.txt'

        with open(report_path, 'w', encoding='utf-8') as f:
            # 报告标题
            f.write("=" * 80 + "\n")
            f.write("原油价格预测分析报告\n")
            f.write("=" * 80 + "\n\n")

            # 基本信息
            f.write(f"报告生成时间: {self.report_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数据期间: {data['combined'].index[0].strftime('%Y-%m-%d')} ~ "
                   f"{data['combined'].index[-1].strftime('%Y-%m-%d')}\n\n")

            # 市场概况
            f.write("【市场概况】\n")
            f.write("-" * 80 + "\n")
            if 'combined' in data and len(data['combined']) > 0:
                latest = data['combined'].iloc[-1]
                f.write(f"WTI原油当前价格: ${latest.get('WTI_Close', 0):.2f}/桶\n")
                f.write(f"Brent原油当前价格: ${latest.get('Brent_Close', 0):.2f}/桶\n")
                f.write(f"价差 (Brent-WTI): ${latest.get('Spread', 0):.2f}\n")
                f.write(f"美元指数: {latest.get('Dollar_Index', 0):.2f}\n")
                f.write(f"VIX恐慌指数: {latest.get('VIX_Index', 0):.2f}\n\n")

            # 长期趋势模型
            if 'long_term' in predictions:
                f.write("【长期趋势模型预测（6-12个月）】\n")
                f.write("-" * 80 + "\n")
                pred = predictions['long_term'].iloc[0]
                f.write(f"当前价格: ${pred['current_price']:.2f}/桶\n")
                f.write(f"预测价格: ${pred['predicted_price']:.2f}/桶 "
                       f"({pred['predicted_change']:+.2f}%)\n")
                f.write(f"置信区间: [${pred['confidence_interval']['lower']:.2f}, "
                       f"${pred['confidence_interval']['upper']:.2f}]\n")
                f.write(f"模型性能: RMSE={pred['model_metrics']['RMSE']:.4f}, "
                       f"MAE={pred['model_metrics']['MAE']:.4f}, "
                       f"R²={pred['model_metrics']['R2']:.4f}\n")
                f.write(f"关键驱动因素:\n")
                for i, driver in enumerate(pred['key_drivers'], 1):
                    f.write(f"  {i}. {driver}\n")

                # 情景分析
                f.write(f"\n情景分析:\n")
                for scenario_name, scenario in pred['scenarios'].items():
                    f.write(f"  {scenario['name']} (概率{scenario['probability']:.0%}): "
                           f"${scenario['price']:.2f}/桶 - {scenario['description']}\n")

                f.write("\n")

            # 中期波动模型
            if 'medium_term' in predictions:
                f.write("【中期波动模型预测（1-3个月）】\n")
                f.write("-" * 80 + "\n")
                pred = predictions['medium_term'].iloc[0]
                f.write(f"当前价格: ${pred['current_price']:.2f}/桶\n")
                f.write(f"预测价格: ${pred['predicted_price']:.2f}/桶 "
                       f"({pred['predicted_change']:+.2f}%)\n")
                f.write(f"置信区间: [${pred['confidence_interval']['lower']:.2f}, "
                       f"${pred['confidence_interval']['upper']:.2f}]\n")
                f.write(f"模型性能: RMSE={pred['model_metrics']['RMSE']:.4f}, "
                       f"MAE={pred['model_metrics']['MAE']:.4f}, "
                       f"R²={pred['model_metrics']['R2']:.4f}\n")
                f.write(f"关键驱动因素:\n")
                for i, driver in enumerate(pred['key_drivers'], 1):
                    f.write(f"  {i}. {driver}\n")

                f.write("\n")

            # 集成预测
            if 'ensemble' in predictions:
                f.write("【集成预测】\n")
                f.write("-" * 80 + "\n")
                pred = predictions['ensemble'].iloc[0]
                f.write(f"当前价格: ${pred['current_price']:.2f}/桶\n")
                f.write(f"预测价格: ${pred['predicted_price']:.2f}/桶 "
                       f"({pred['predicted_change']:+.2f}%)\n")
                f.write(f"置信区间: [${pred['confidence_interval']['lower']:.2f}, "
                       f"${pred['confidence_interval']['upper']:.2f}]\n")
                f.write(f"集成RMSE: {pred['ensemble_rmse']:.4f}\n")

                f.write("\n模型贡献:\n")
                f.write(f"  长期模型: {pred['long_term_contribution']['prediction']:+.2f}% "
                       f"(权重{pred['long_term_contribution']['weight']:.0%})\n")
                f.write(f"  中期模型: {pred['medium_term_contribution']['prediction']:+.2f}% "
                       f"(权重{pred['medium_term_contribution']['weight']:.0%})\n")

                f.write("\n")

            # 免责声明
            f.write("=" * 80 + "\n")
            f.write("免责声明\n")
            f.write("=" * 80 + "\n")
            f.write("本报告仅供参考，不构成投资建议。原油价格预测存在不确定性，\n")
            f.write("实际价格可能与预测结果存在较大偏差。投资者应根据自身风险承受能力\n")
            f.write("做出独立判断，并对投资决策负责。\n\n")
            f.write("报告生成: 原油价格预测系统 v1.0\n")

        logger.info(f"文本报告已保存到: {report_path}")

    def generate_html_report(self, data: dict, predictions: dict, output_dir: Path):
        """
        生成HTML报告

        Args:
            data: 原始数据
            predictions: 预测结果
            output_dir: 输出目录
        """
        logger.info("生成HTML报告...")

        timestamp = self.report_time.strftime('%Y%m%d_%H%M%S')
        report_path = output_dir / f'oil_prediction_report_{timestamp}.html'

        # HTML模板
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>原油价格预测分析报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 10px;
            margin-top: 30px;
        }}
        .metric {{
            display: inline-block;
            margin: 10px;
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
            min-width: 200px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-label {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .positive {{
            color: #27ae60;
        }}
        .negative {{
            color: #e74c3c;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .disclaimer {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛢️ 原油价格预测分析报告</h1>

        <p><strong>报告生成时间:</strong> {self.report_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
"""

        # 市场概况
        if 'combined' in data and len(data['combined']) > 0:
            latest = data['combined'].iloc[-1]
            html_content += """
        <h2>📊 市场概况</h2>
        <div class="metric">
            <div class="metric-value">${:.2f}</div>
            <div class="metric-label">WTI原油价格</div>
        </div>
        <div class="metric">
            <div class="metric-value">${:.2f}</div>
            <div class="metric-label">Brent原油价格</div>
        </div>
        <div class="metric">
            <div class="metric-value">${:.2f}</div>
            <div class="metric-label">价差 (Brent-WTI)</div>
        </div>
        <div class="metric">
            <div class="metric-value">{:.2f}</div>
            <div class="metric-label">美元指数</div>
        </div>
        <div class="metric">
            <div class="metric-value">{:.2f}</div>
            <div class="metric-label">VIX恐慌指数</div>
        </div>
""".format(
    latest.get('WTI_Close', 0),
    latest.get('Brent_Close', 0),
    latest.get('Spread', 0),
    latest.get('Dollar_Index', 0),
    latest.get('VIX_Index', 0)
)

        # 长期趋势模型
        if 'long_term' in predictions:
            pred = predictions['long_term'].iloc[0]
            change_class = 'positive' if pred['predicted_change'] > 0 else 'negative'

            html_content += f"""
        <h2>📈 长期趋势模型预测（6-12个月）</h2>
        <div class="metric">
            <div class="metric-value">${pred['current_price']:.2f}</div>
            <div class="metric-label">当前价格</div>
        </div>
        <div class="metric">
            <div class="metric-value ${change_class}">${pred['predicted_price']:.2f}</div>
            <div class="metric-label">预测价格 ({pred['predicted_change']:+.2f}%)</div>
        </div>
        <div class="metric">
            <div class="metric-value">${pred['confidence_interval']['lower']:.2f} - ${pred['confidence_interval']['upper']:.2f}</div>
            <div class="metric-label">置信区间 (95%)</div>
        </div>

        <h3>模型性能</h3>
        <table>
            <tr><th>指标</th><th>值</th></tr>
            <tr><td>RMSE</td><td>{pred['model_metrics']['RMSE']:.4f}</td></tr>
            <tr><td>MAE</td><td>{pred['model_metrics']['MAE']:.4f}</td></tr>
            <tr><td>R²</td><td>{pred['model_metrics']['R2']:.4f}</td></tr>
        </table>

        <h3>关键驱动因素</h3>
        <table>
            <tr><th>排名</th><th>因子</th></tr>
"""

            for i, driver in enumerate(pred['key_drivers'], 1):
                html_content += f"            <tr><td>{i}</td><td>{driver}</td></tr>\n"

            html_content += "        </table>\n"

        # 中期波动模型
        if 'medium_term' in predictions:
            pred = predictions['medium_term'].iloc[0]
            change_class = 'positive' if pred['predicted_change'] > 0 else 'negative'

            html_content += f"""
        <h2>📊 中期波动模型预测（1-3个月）</h2>
        <div class="metric">
            <div class="metric-value">${pred['current_price']:.2f}</div>
            <div class="metric-label">当前价格</div>
        </div>
        <div class="metric">
            <div class="metric-value ${change_class}">${pred['predicted_price']:.2f}</div>
            <div class="metric-label">预测价格 ({pred['predicted_change']:+.2f}%)</div>
        </div>
        <div class="metric">
            <div class="metric-value">${pred['confidence_interval']['lower']:.2f} - ${pred['confidence_interval']['upper']:.2f}</div>
            <div class="metric-label">置信区间 (95%)</div>
        </div>

        <h3>模型性能</h3>
        <table>
            <tr><th>指标</th><th>值</th></tr>
            <tr><td>RMSE</td><td>{pred['model_metrics']['RMSE']:.4f}</td></tr>
            <tr><td>MAE</td><td>{pred['model_metrics']['MAE']:.4f}</td></tr>
            <tr><td>R²</td><td>{pred['model_metrics']['R2']:.4f}</td></tr>
        </table>
"""

        # 集成预测
        if 'ensemble' in predictions:
            pred = predictions['ensemble'].iloc[0]
            change_class = 'positive' if pred['predicted_change'] > 0 else 'negative'

            html_content += f"""
        <h2>🎯 集成预测</h2>
        <div class="metric">
            <div class="metric-value">${pred['predicted_price']:.2f}</div>
            <div class="metric-label">预测价格 ({pred['predicted_change']:+.2f}%)</div>
        </div>
        <div class="metric">
            <div class="metric-value">${pred['confidence_interval']['lower']:.2f} - ${pred['confidence_interval']['upper']:.2f}</div>
            <div class="metric-label">置信区间 (95%)</div>
        </div>

        <h3>模型贡献</h3>
        <table>
            <tr><th>模型</th><th>预测</th><th>权重</th></tr>
            <tr><td>长期趋势模型</td><td>{pred['long_term_contribution']['prediction']:+.2f}%</td><td>{pred['long_term_contribution']['weight']:.0%}</td></tr>
            <tr><td>中期波动模型</td><td>{pred['medium_term_contribution']['prediction']:+.2f}%</td><td>{pred['medium_term_contribution']['weight']:.0%}</td></tr>
        </table>
"""

        # 免责声明
        html_content += """
        <div class="disclaimer">
            <h3>⚠️ 免责声明</h3>
            <p>本报告仅供参考，不构成投资建议。原油价格预测存在不确定性，实际价格可能与预测结果存在较大偏差。投资者应根据自身风险承受能力做出独立判断，并对投资决策负责。</p>
            <p><strong>报告生成: 原油价格预测系统 v1.0</strong></p>
        </div>
    </div>
</body>
</html>
"""

        # 保存HTML文件
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"HTML报告已保存到: {report_path}")


if __name__ == "__main__":
    # 测试报告生成器
    from utils.data_fetcher import OilDataFetcher
    from utils.feature_engineering import FeatureEngineering
    from models.long_term import LongTermModel

    logger.info("开始测试报告生成器...")

    # 获取数据并训练模型
    fetcher = OilDataFetcher()
    all_data = fetcher.get_all_data()

    if all_data.get('combined') is not None:
        fe = FeatureEngineering()
        featured_data = fe.create_all_features(all_data['combined'])

        model = LongTermModel()
        model.train(featured_data, horizon=12)
        predictions = {'long_term': model.predict(featured_data, horizon=12)}

        # 生成报告
        generator = ReportGenerator()
        generator.generate_text_report(all_data, predictions, REPORTS_DIR)
        generator.generate_html_report(all_data, predictions, REPORTS_DIR)

        logger.info("报告生成器测试完成！")
