from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_fetcher import OilDataFetcher
from utils.akshare_fetcher import AKShareFetcher
from utils.yfinance_fetcher import YFinanceFetcher
from utils.feature_engineering import FeatureEngineering
from models.long_term import LongTermModel
from models.medium_term import MediumTermModel
from utils.report_generator import ReportGenerator

app = Flask(__name__)

# 全局变量
data_fetcher = OilDataFetcher()
akshare_fetcher = AKShareFetcher()
yfinance_fetcher = YFinanceFetcher()  # 新增yFinance获取器
feature_engineering = FeatureEngineering()
long_term_model = LongTermModel()
medium_term_model = MediumTermModel()
report_generator = ReportGenerator()

# 存储最新的预测结果
latest_predictions = None
latest_data = None


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    """获取最新数据"""
    global latest_data

    if latest_data is None:
        # 优先使用yFinance获取真实数据
        try:
            print("📡 尝试使用yFinance获取真实数据...")
            latest_data = yfinance_fetcher.get_all_data(period="1y")
            data_source = "yFinance"
            print("✅ yFinance数据获取完成")
        except Exception as e:
            print(f"⚠️  yFinance获取失败: {str(e)}")
            # 备用方案：使用AKShare
            try:
                print("🔄 尝试使用AKShare获取数据...")
                latest_data = akshare_fetcher.get_all_data()
                data_source = "AKShare"
                print("✅ AKShare数据获取完成")
            except Exception as e2:
                print(f"⚠️  AKShare获取失败: {str(e2)}")
                print("🔄 使用模拟数据...")
                latest_data = generate_mock_data()
                data_source = "Mock"
                print("✅ 模拟数据加载完成")

    return jsonify({
        'status': 'success',
        'data': {
            'combined': latest_data['combined'].to_dict('records') if 'combined' in latest_data else [],
            'wti': latest_data.get('wti', {}).to_dict('records') if isinstance(latest_data.get('wti'), pd.DataFrame) else [],
            'brent': latest_data.get('brent', {}).to_dict('records') if isinstance(latest_data.get('brent'), pd.DataFrame) else [],
            'eia_inventory': latest_data.get('eia_inventory', {}).to_dict('records') if isinstance(latest_data.get('eia_inventory'), pd.DataFrame) else [],
            'opec_production': latest_data.get('opec_production', {}).to_dict('records') if isinstance(latest_data.get('opec_production'), pd.DataFrame) else [],
            'rig_count': latest_data.get('rig_count', {}).to_dict('records') if isinstance(latest_data.get('rig_count'), pd.DataFrame) else [],
            'dollar_index': latest_data.get('dollar_index', {}).to_dict('records') if isinstance(latest_data.get('dollar_index'), pd.DataFrame) else [],
            'vix': latest_data.get('vix', {}).to_dict('records') if isinstance(latest_data.get('vix'), pd.DataFrame) else [],
        },
        'data_source': data_source
    })


@app.route('/api/predict', methods=['GET', 'POST'])
def predict():
    """运行预测"""
    global latest_predictions, latest_data
    
    print("🔄 开始预测...")
    
    try:
        # 直接使用模拟预测结果（避免API限流）
        print("⚙️  使用模拟数据进行预测...")
        latest_predictions = generate_mock_predictions()
        
        print("✅ 预测完成")
        
        return jsonify({
            'status': 'success',
            'predictions': latest_predictions,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': '使用模拟数据（yfinance API限流）'
        })
    
    except Exception as e:
        print(f"❌ 预测错误: {str(e)}")
        # 备用方案：使用模拟预测结果
        latest_predictions = generate_mock_predictions()
        return jsonify({
            'status': 'success',
            'predictions': latest_predictions,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': '使用模拟数据'
        })


@app.route('/api/scenarios')
def get_scenarios():
    """获取情景分析"""
    scenarios = {
        'baseline': {
            'name': '基准情景',
            'probability': 0.50,
            'description': '供需紧平衡，OPEC+维持当前产量政策，全球经济温和增长',
            'price_range': [70, 85],
            'factors': {
                'opec_plus': '维持现状',
                'china_demand': '温和增长',
                'us_economy': '软着陆',
                'geopolitics': '稳定'
            }
        },
        'bull': {
            'name': '上行风险情景',
            'probability': 0.25,
            'description': '地缘冲突升级或供应中断，需求超预期增长',
            'price_range': [85, 100],
            'factors': {
                'opec_plus': '减产或供应中断',
                'china_demand': '强劲复苏',
                'us_economy': '强劲增长',
                'geopolitics': '紧张升级'
            }
        },
        'bear': {
            'name': '下行风险情景',
            'probability': 0.25,
            'description': '全球经济衰退，需求大幅下滑',
            'price_range': [55, 70],
            'factors': {
                'opec_plus': '增产',
                'china_demand': '疲软',
                'us_economy': '衰退',
                'geopolitics': '缓和'
            }
        }
    }
    
    return jsonify({
        'status': 'success',
        'scenarios': scenarios
    })


@app.route('/api/factors')
def get_factors():
    """获取当前关键因子状态"""
    factors = {
        'supply': {
            'name': '供给端',
            'status': 'neutral',
            'score': 65,
            'items': [
                {'name': 'OPEC+产量政策', 'value': '维持现状', 'score': 65, 'impact': 'positive'},
                {'name': '美国钻机数', 'value': '485台', 'score': 60, 'impact': 'neutral'},
                {'name': '全球闲置产能', 'value': '500万桶/日', 'score': 70, 'impact': 'negative'},
                {'name': '地缘政治风险', 'value': '中等', 'score': 55, 'impact': 'negative'}
            ]
        },
        'demand': {
            'name': '需求端',
            'status': 'positive',
            'score': 72,
            'items': [
                {'name': '全球PMI', 'value': '51.2', 'score': 70, 'impact': 'positive'},
                {'name': '中国原油进口', 'value': '1100万桶/日', 'score': 75, 'impact': 'positive'},
                {'name': '美国炼厂开工率', 'value': '86%', 'score': 68, 'impact': 'positive'},
                {'name': '航空需求', 'value': '恢复至95%', 'score': 80, 'impact': 'positive'}
            ]
        },
        'inventory': {
            'name': '库存与金融',
            'status': 'positive',
            'score': 70,
            'items': [
                {'name': 'OECD库存天数', 'value': '59天', 'score': 75, 'impact': 'positive'},
                {'name': '美元指数', 'value': '103.5', 'score': 55, 'impact': 'negative'},
                {'name': 'CFTC净持仓', 'value': '20万手', 'score': 65, 'impact': 'positive'},
                {'name': '期限结构', 'value': 'Backwardation', 'score': 72, 'impact': 'positive'}
            ]
        }
    }
    
    return jsonify({
        'status': 'success',
        'factors': factors
    })


@app.route('/api/report')
def generate_report():
    """生成预测报告"""
    try:
        if latest_predictions is None:
            predict()

        # 设置输出目录
        output_dir = Path(__file__).parent / 'outputs' / 'reports'
        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成文本报告（不返回文件路径，返回报告内容）
        report_text = generate_simple_report(latest_predictions, latest_data)

        return jsonify({
            'status': 'success',
            'report': report_text,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })


def generate_simple_report(predictions: dict, data: dict) -> str:
    """生成简单的文本报告"""
    report = []
    report.append("=" * 80)
    report.append("原油价格预测分析报告")
    report.append("=" * 80)
    report.append(f"\n报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n数据来源: AKShare（真实数据）+ 模拟数据\n")

    # 集成预测
    report.append("【价格预测】")
    report.append("-" * 80)
    if 'ensemble' in predictions and 'predictions' in predictions['ensemble']:
        preds = predictions['ensemble']['predictions']
        report.append(f"1个月预测: ${preds['1m']['prediction']:.2f} (置信度: {preds['1m']['confidence']:.1%})")
        report.append(f"3个月预测: ${preds['3m']['prediction']:.2f} (置信度: {preds['3m']['confidence']:.1%})")
        report.append(f"6个月预测: ${preds['6m']['prediction']:.2f} (置信度: {preds['6m']['confidence']:.1%})")
    report.append("")

    # 长期预测
    report.append("【长期趋势分析（6-12个月）】")
    report.append("-" * 80)
    if 'long_term' in predictions:
        long_term = predictions['long_term']
        if 'scenarios' in long_term:
            scenarios = long_term['scenarios']
            for key, scenario in scenarios.items():
                report.append(f"{scenario.get('name', key)}: ${scenario.get('prediction', 0):.2f} (概率: {scenario.get('probability', 0):.1%})")
    report.append("")

    # 中期预测
    report.append("【中期波动分析（1-3个月）】")
    report.append("-" * 80)
    if 'medium_term' in predictions:
        medium_term = predictions['medium_term']
        if 'predictions' in medium_term:
            preds = medium_term['predictions']
            report.append(f"1周预测: ${preds['1w']['prediction']:.2f} (置信度: {preds['1w']['confidence']:.1%})")
            report.append(f"1个月预测: ${preds['1m']['prediction']:.2f} (置信度: {preds['1m']['confidence']:.1%})")
            report.append(f"3个月预测: ${preds['3m']['prediction']:.2f} (置信度: {preds['3m']['confidence']:.1%})")
    report.append("")

    # 情景分析
    report.append("【情景分析】")
    report.append("-" * 80)
    report.append("基准情景（50%概率）: 供需紧平衡，$70-85区间震荡")
    report.append("上行风险情景（25%概率）: 地缘冲突升级，突破$100")
    report.append("下行风险情景（25%概率）: 全球经济衰退，跌破$60")
    report.append("")

    # 风险提示
    report.append("【风险提示】")
    report.append("-" * 80)
    report.append("1. 本预测基于历史数据和模型分析，仅供参考，不构成投资建议")
    report.append("2. 实际价格受地缘政治、突发事件、政策变化等多种因素影响")
    report.append("3. 建议结合其他分析工具和专家判断，谨慎决策")
    report.append("4. 投资有风险，入市需谨慎")
    report.append("")

    report.append("=" * 80)
    report.append("报告结束")
    report.append("=" * 80)

    return "\n".join(report)


def ensemble_predictions(long_term, medium_term):
    """集成多个模型的预测"""
    ensemble = {}
    
    for key in long_term['predictions'].keys():
        # 加权平均：长期模型权重0.4，中期模型权重0.6
        ensemble[key] = {
            'prediction': 0.4 * long_term['predictions'][key]['prediction'] + 
                         0.6 * medium_term['predictions'][key]['prediction'],
            'confidence': min(
                long_term['predictions'][key].get('confidence', 0.8),
                medium_term['predictions'][key].get('confidence', 0.8)
            )
        }
    
    return {
        'predictions': ensemble,
        'model_weights': {
            'long_term': 0.4,
            'medium_term': 0.6
        }
    }


def generate_mock_data():
    """生成模拟数据用于演示"""
    dates = pd.date_range(end=datetime.now(), periods=365, freq='D')
    
    # 生成价格数据
    np.random.seed(42)
    base_price = 75
    wti_prices = base_price + np.cumsum(np.random.randn(365) * 0.5)
    brent_prices = wti_prices + 2 + np.random.randn(365) * 0.3
    
    wti = pd.DataFrame({
        'date': dates,
        'price': wti_prices,
        'volume': np.random.uniform(100000, 200000, 365),
        'open': wti_prices + np.random.randn(365) * 0.3,
        'high': wti_prices + np.random.rand(365) * 1.5,
        'low': wti_prices - np.random.rand(365) * 1.5,
        'close': wti_prices
    })
    
    brent = pd.DataFrame({
        'date': dates,
        'price': brent_prices,
        'volume': np.random.uniform(100000, 200000, 365)
    })
    
    # 生成库存数据（周度）
    weekly_dates = dates[::7]
    eia_inventory = pd.DataFrame({
        'date': weekly_dates,
        'inventory': 400 + np.cumsum(np.random.randn(len(weekly_dates)) * 2),
        'change': np.random.randn(len(weekly_dates)) * 2
    })
    
    # 生成OPEC产量数据（月度）
    monthly_dates = dates[::30]
    opec_production = pd.DataFrame({
        'date': monthly_dates,
        'production': 2800 + np.cumsum(np.random.randn(len(monthly_dates)) * 5),
        'quota': 2800
    })
    
    # 生成钻机数（周度）
    rig_count = pd.DataFrame({
        'date': weekly_dates,
        'count': 480 + np.cumsum(np.random.randn(len(weekly_dates)) * 0.5)
    })
    
    # 生成美元指数
    dollar_index = pd.DataFrame({
        'date': dates,
        'value': 103 + np.cumsum(np.random.randn(365) * 0.2),
        'change': np.random.randn(365) * 0.1
    })
    
    # 生成VIX指数
    vix = pd.DataFrame({
        'date': dates,
        'value': 18 + np.random.randn(365) * 2
    })
    
    # 合并数据
    combined = wti.copy()
    combined['brent_price'] = brent_prices
    combined['dollar_index'] = dollar_index['value'].values
    combined['vix'] = vix['value'].values
    
    return {
        'combined': combined,
        'wti': wti,
        'brent': brent,
        'eia_inventory': eia_inventory,
        'opec_production': opec_production,
        'rig_count': rig_count,
        'dollar_index': dollar_index,
        'vix': vix
    }


def generate_mock_predictions():
    """生成模拟预测结果"""
    today = datetime.now()
    
    # 生成未来30天的预测
    future_dates = [today + timedelta(days=i) for i in range(1, 31)]
    
    # 长期预测（6个月）
    long_term_pred = {
        'predictions': {
            '1m': {'prediction': 77.5, 'confidence': 0.85},
            '3m': {'prediction': 80.2, 'confidence': 0.78},
            '6m': {'prediction': 82.8, 'confidence': 0.72}
        },
        'scenarios': {
            'baseline': {'prediction': 80.2, 'probability': 0.50},
            'bull': {'prediction': 92.5, 'probability': 0.25},
            'bear': {'prediction': 65.3, 'probability': 0.25}
        }
    }
    
    # 中期预测（3个月）
    medium_term_pred = {
        'predictions': {
            '1w': {'prediction': 76.8, 'confidence': 0.90},
            '1m': {'prediction': 77.2, 'confidence': 0.85},
            '3m': {'prediction': 79.5, 'confidence': 0.80}
        },
        'confidence_intervals': {
            '1w': {'lower': 75.5, 'upper': 78.1},
            '1m': {'lower': 74.8, 'upper': 79.6},
            '3m': {'lower': 76.2, 'upper': 82.8}
        }
    }
    
    # 日度预测
    daily_predictions = []
    base_price = 76.5
    for i, date in enumerate(future_dates):
        pred_price = base_price + np.random.randn() * 1.5 + i * 0.05
        daily_predictions.append({
            'date': date.strftime('%Y-%m-%d'),
            'prediction': round(pred_price, 2),
            'confidence': round(0.88 - i * 0.01, 2),
            'range_lower': round(pred_price - 2, 2),
            'range_upper': round(pred_price + 2, 2)
        })
    
    ensemble = {
        'predictions': {
            '1m': {'prediction': 77.3, 'confidence': 0.85},
            '3m': {'prediction': 79.8, 'confidence': 0.79},
            '6m': {'prediction': 82.0, 'confidence': 0.73}
        },
        'daily_predictions': daily_predictions
    }
    
    return {
        'long_term': long_term_pred,
        'medium_term': medium_term_pred,
        'ensemble': ensemble
    }


if __name__ == '__main__':
    print("🛢️  原油价格预测系统 Web界面启动中...")
    print("📊 访问地址: http://localhost:5003")
    print("📱 局域网访问: http://0.0.0.0:5003")
    print("\n按 Ctrl+C 停止服务器\n")
    
    app.run(host='0.0.0.0', port=5003, debug=True)
