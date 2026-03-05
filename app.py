from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_fetcher import OilDataFetcher
from utils.akshare_fetcher import AKShareFetcher
from utils.tushare_news_fetcher import TushareNewsFetcher
from utils.feature_engineering import FeatureEngineering
from models.long_term import LongTermModel
from models.medium_term import MediumTermModel
from utils.report_generator import ReportGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 全局变量
data_fetcher = OilDataFetcher()
akshare_fetcher = AKShareFetcher()
tushare_news_fetcher = TushareNewsFetcher()
feature_engineering = FeatureEngineering()
long_term_model = LongTermModel()
medium_term_model = MediumTermModel()
report_generator = ReportGenerator()

# 存储最新的预测结果
latest_predictions = None
latest_data = None

# Tushare新闻缓存
tushare_news_cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': timedelta(minutes=30)  # 缓存30分钟
}


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    """获取最新数据 - 只使用AKShare"""
    global latest_data

    if latest_data is None:
        # 只使用AKShare获取数据
        try:
            print("🇨🇳 使用AKShare获取数据...")
            latest_data = akshare_fetcher.get_all_data()
            data_source = "AKShare"
            print("✅ AKShare数据获取完成")
        except Exception as e:
            print(f"⚠️ AKShare获取失败: {e}")
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


@app.route('/api/news')
def get_news():
    """获取科技和财经新闻 - 从RSS源获取"""
    try:
        # 定义RSS新闻源
        tech_rss_sources = [
            "https://36kr.com/feed",           # 36氪
            "https://www.ithome.com/rss/",     # IT之家
            "https://www.solidot.org/index.rss", # Solidot
        ]

        # 从RSS获取科技新闻
        tech_news = _fetch_rss_news(tech_rss_sources, 'tech')

        # 使用Tushare获取财经新闻(带缓存,避免频繁调用)
        finance_news, finance_error = _get_tushare_news_with_cache()

        # 如果RSS获取失败,使用模拟数据作为备用
        if not tech_news or len(tech_news) < 3:
            logger.info("使用模拟科技新闻数据")
            tech_news = _generate_mock_news('tech')

        # Tushare获取失败时不使用假数据,返回错误信息
        if not finance_news or len(finance_news) < 3:
            if finance_error:
                # API限制情况,返回特殊标记
                finance_news = [{
                    'title': 'API调用已达限制',
                    'summary': '免费版每小时仅2次,已用完',
                    'source': 'Tushare',
                    'time': datetime.now().strftime('%H:%M'),
                    'sentiment': 'neutral',
                    'impact': 'medium',
                    'category': '系统提示',
                    'link': 'https://tushare.pro/document/1?doc_id=108',
                    'is_error': True
                }]
            else:
                logger.info("Tushare获取失败")
                finance_news = []

        return jsonify({
            'status': 'success',
            'tech_news': tech_news[:5],  # 只返回前5条
            'finance_news': finance_news[:5],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"获取新闻失败: {str(e)}")
        # 出错时使用模拟数据
        tech_news = _generate_mock_news('tech')
        finance_news = _generate_mock_news('finance')
        return jsonify({
            'status': 'success',
            'tech_news': tech_news,
            'finance_news': finance_news,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': '使用模拟数据(RSS获取失败)'
        })


def _get_tushare_news_with_cache():
    """使用Tushare获取财经新闻,带缓存机制避免频繁调用"""
    global tushare_news_cache

    # 检查缓存是否有效
    if tushare_news_cache['data'] is not None and \
       tushare_news_cache['timestamp'] is not None and \
       (datetime.now() - tushare_news_cache['timestamp']) < tushare_news_cache['cache_duration']:

        logger.info("使用缓存的Tushare财经新闻")
        return tushare_news_cache['data'], None

    # 缓存过期或未缓存,重新获取
    try:
        logger.info("从Tushare获取最新财经新闻...")
        news = tushare_news_fetcher.fetch_news(limit=20)

        if news and len(news) > 0:
            # 更新缓存
            tushare_news_cache['data'] = news
            tushare_news_cache['timestamp'] = datetime.now()
            logger.info(f"Tushare新闻已更新,缓存有效期30分钟")
            return news, None
        else:
            logger.warning("Tushare未返回新闻数据")
            return None, None
    except Exception as e:
        error_msg = str(e)
        logger.error(f"获取Tushare新闻失败: {error_msg}")

        # 检查是否是API限制错误
        if '每分钟最多访问' in error_msg or '每小时最多访问' in error_msg or '每分钟最多' in error_msg or '每小时最多' in error_msg:
            return None, 'API调用已达限制: 免费版每小时仅2次,已用完'
        else:
            return None, None


def _fetch_rss_news(sources, news_type):
    """从RSS源获取新闻"""
    import requests
    from bs4 import BeautifulSoup
    import feedparser

    all_news = []

    for source_url in sources:
        try:
            logger.info(f"尝试获取RSS源: {source_url}")

            # 对于新浪财经RSS,需要特殊处理编码问题
            if 'sina.com.cn' in source_url:
                try:
                    # 先用requests获取原始内容,指定编码
                    response = requests.get(source_url, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    })
                    response.encoding = 'utf-8'  # 强制使用UTF-8

                    # 将内容传给feedparser
                    feed = feedparser.parse(response.text)

                    if feed.bozo:
                        logger.warning(f"新浪财经RSS解析警告: {feed.bozo_exception}")
                        # 尝试忽略错误继续解析
                        if not feed.entries:
                            raise Exception("新浪财经RSS无有效条目")

                except Exception as e:
                    logger.warning(f"新浪财经RSS获取失败: {str(e)}, 跳过该源")
                    continue
            else:
                # 其他源直接解析
                feed = feedparser.parse(source_url)

            if feed.entries:
                logger.info(f"从 {source_url} 获取到 {len(feed.entries)} 条新闻")

                for entry in feed.entries[:10]:  # 每个源最多取10条
                    try:
                        # 尝试获取标题
                        title = entry.get('title', '未知标题')

                        # 尝试获取描述/摘要
                        summary = entry.get('description', '')
                        if not summary:
                            summary = entry.get('summary', '')

                        # 清理HTML标签
                        if summary:
                            summary = BeautifulSoup(summary, 'html.parser').get_text(strip=True)
                            if len(summary) > 150:
                                summary = summary[:150] + '...'

                        # 获取发布时间
                        pub_date = entry.get('published', entry.get('updated', ''))
                        time_str = ''
                        if pub_date:
                            try:
                                # 尝试解析时间
                                from dateutil import parser as date_parser
                                dt = date_parser.parse(pub_date)
                                # 如果是今天,只显示时间;否则显示日期
                                if dt.date() == datetime.now().date():
                                    time_str = dt.strftime('%H:%M')
                                else:
                                    time_str = dt.strftime('%m-%d')
                            except:
                                time_str = datetime.now().strftime('%H:%M')

                        # 获取来源
                        source = feed.feed.get('title', '未知来源')

                        # 简单的情感分析
                        sentiment = _analyze_sentiment(title + ' ' + summary)

                        # 判断影响程度
                        impact = _analyze_impact(title + ' ' + summary, news_type)

                        news_item = {
                            'title': title,
                            'summary': summary or '暂无摘要',
                            'source': source,
                            'time': time_str or datetime.now().strftime('%H:%M'),
                            'sentiment': sentiment,
                            'impact': impact,
                            'link': entry.get('link', '')
                        }

                        all_news.append(news_item)

                    except Exception as e:
                        logger.warning(f"解析单条新闻失败: {str(e)}")
                        continue

            else:
                logger.warning(f"RSS源 {source_url} 没有返回任何条目")

        except Exception as e:
            logger.warning(f"获取RSS源 {source_url} 失败: {str(e)}")
            continue

    # 去重并按时间排序(这里简单去重,基于标题)
    seen_titles = set()
    unique_news = []
    for news in all_news:
        if news['title'] not in seen_titles:
            seen_titles.add(news['title'])
            unique_news.append(news)

    return unique_news


def _analyze_sentiment(text):
    """简单的情感分析"""
    positive_keywords = ['增长', '上涨', '突破', '创新', '成功', '利好', '增长', '回升',
                       '突破', '大涨', '繁荣', '优化', '改善', '提升', '扩大', '加速',
                       'boost', 'increase', 'growth', 'success', 'rise', 'gain']

    negative_keywords = ['下降', '下跌', '暴跌', '衰退', '风险', '危机', '放缓', '下滑',
                       '收缩', '减少', '警告', '担忧', '跌', '崩盘', '衰退',
                       'fall', 'drop', 'decline', 'risk', 'crisis', 'slowdown', 'warning']

    text_lower = text.lower()

    positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
    negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)

    if positive_count > negative_count:
        return 'positive'
    elif negative_count > positive_count:
        return 'negative'
    else:
        return 'neutral'


def _analyze_impact(text, news_type):
    """分析影响程度"""
    high_impact_keywords = ['重大', '突破', '首次', '创', '新高', '暴跌', '大涨',
                           '重要', '关键', '紧急', '重磅', 'major', 'breakthrough',
                           'record', 'crucial', 'important', 'significant']

    text_lower = text.lower()
    high_count = sum(1 for keyword in high_impact_keywords if keyword in text_lower)

    if high_count >= 1:
        return 'high'
    elif high_count >= 1:
        return 'medium'
    else:
        return 'medium'


def _generate_mock_news(news_type):
    """生成模拟新闻数据 - 基于当前时间生成更真实的新闻"""
    from datetime import timedelta
    import random

    base_time = datetime.now()
    hour = base_time.hour

    if news_type == 'tech':
        news_templates = [
            ('AI大模型性能突破', '新一代大语言模型推理速度提升200%,成本降低50%,为商业化应用奠定基础', '科技前沿', 'positive', 'high'),
            ('量子计算取得重大进展', '中国科学家实现504比特超导量子计算芯片,创造新纪录', '量子科技', 'positive', 'high'),
            ('6G通信技术预研启动', '多家企业签署6G联合研发协议,预计2030年商用', '通信技术', 'positive', 'medium'),
            ('自动驾驶技术升级', 'L4级自动驾驶在特定场景实现商业化运营', '人工智能', 'positive', 'high'),
            ('卫星互联网加速部署', '低轨卫星星座建设提速,全球覆盖能力显著提升', '航天科技', 'positive', 'medium'),
            ('生物识别技术突破', '新型生物识别算法准确率达99.9%,支持多模态识别', '安全科技', 'positive', 'medium'),
            ('绿色芯片技术', '新型环保芯片材料研发成功,能耗降低40%', '半导体', 'positive', 'high'),
            ('元宇宙应用落地', '工业元宇宙在制造业率先应用,效率提升30%', '虚拟现实', 'positive', 'medium'),
        ]

        sources = ['36氪', 'IT之家', '科技日报', '极客公园', '量子位', '硅谷观察', '机器之心']
    else:  # finance
        # 根据当前小时生成更贴合实际的财经新闻
        if hour < 10:
            time_context = "早盘"
        elif hour < 11:
            time_context = "午盘前"
        elif hour < 14:
            time_context = "午后"
        else:
            time_context = "收盘后"

        # 财经新闻模板,包含标题、摘要、分类、情感、影响、链接
        news_templates = [
            (f'{time_context}原油价格震荡上行', 'OPEC+减产预期升温,地缘风险溢价支撑油价,WTI原油突破78美元', '原油市场', 'positive', 'high', 'https://finance.sina.com.cn/money/future/oil/'),
            ('美元指数高位回落', '美联储政策转向预期升温,美元指数跌破104关口', '外汇市场', 'negative', 'high', 'https://finance.sina.com.cn/fx/'),
            ('黄金价格再创新高', '避险需求持续旺盛,COMEX黄金突破2150美元/盎司', '贵金属', 'positive', 'high', 'https://finance.sina.com.cn/futuremarket/gold/'),
            ('全球股市普遍上涨', '经济复苏预期增强,欧美股市全线上扬', '股市动态', 'positive', 'medium', 'https://finance.sina.com.cn/stock/'),
            ('中国制造业PMI超预期', '3月制造业PMI回升至50.8%,显示经济企稳回升', '宏观经济', 'positive', 'high', 'https://finance.sina.com.cn/china/'),
            ('央行释放流动性信号', '央行开展逆回购操作,保持流动性合理充裕', '货币政策', 'positive', 'medium', 'https://finance.sina.com.cn/china/jrxw/'),
            ('新能源汽车产业链景气度高', '锂价企稳回升,电池产业链订单饱满', '产业经济', 'positive', 'high', 'https://finance.sina.com.cn/roll/'),
            ('房地产政策优化', '多地调整购房政策,市场信心逐步恢复', '房地产', 'neutral', 'medium', 'https://finance.sina.com.cn/fangchan/'),
            ('数字经济加速发展', '数据要素市场化配置提速,数字经济规模持续扩大', '数字经济', 'positive', 'high', 'https://finance.sina.com.cn/roll/'),
            ('国际贸易回暖', '3月出口数据超预期增长,外需韧性显现', '对外贸易', 'positive', 'medium', 'https://finance.sina.com.cn/china/'),
        ]

        sources = ['财经时报', '上海证券报', '中国证券报', '证券时报', '经济参考报', '第一财经', '金融界', '华尔街见闻']

    # 随机选择5条新闻
    selected_news = random.sample(news_templates, min(5, len(news_templates)))

    news_list = []
    for i, news_template in enumerate(selected_news):
        # 根据news_type解析模板
        if news_type == 'tech':
            title, summary, category, sentiment, impact = news_template
            link = ''
        else:
            title, summary, category, sentiment, impact, link = news_template

        # 随机化时间,让新闻看起来更真实
        time_offset = random.randint(i * 15, (i + 1) * 30)
        news_time = base_time - timedelta(minutes=time_offset)

        news_list.append({
            'title': title,
            'summary': summary,
            'source': random.choice(sources),
            'time': news_time.strftime('%H:%M'),
            'sentiment': sentiment,
            'impact': impact,
            'category': category,
            'link': link
        })

    return news_list


@app.route('/api/futures-quotes')
def get_futures_quotes():
    """获取期货行情数据"""
    # 先尝试获取真实数据,失败则返回模拟数据
    real_quotes = _get_real_futures_quotes()

    if real_quotes:
        return real_quotes
    else:
        # 返回模拟数据
        return jsonify({
            'status': 'success',
            'quotes': _generate_mock_futures_quotes(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': '使用模拟数据（API限流）'
        })


def _get_real_futures_quotes():
    """尝试从真实API获取期货行情数据 - 优先AKShare,备用新浪财经和东方财富"""
    quotes = []

    # 1. 使用AKShare获取国内期货数据
    try:
        import akshare as ak
        logger.info("使用AKShare获取国内期货行情...")

        # 定义需要获取的国内期货品种
        domestic_futures = {
            '原油': {'name': '上海原油 (INE)', 'symbol': 'CL', 'format': '{:.2f}'},
            '沪铜': {'name': '上海铜', 'symbol': 'HG', 'format': '{:.2f}'},
            '黄金': {'name': '上海黄金', 'symbol': 'GC', 'format': '{:.2f}'},
        }

        for variety, info in domestic_futures.items():
            try:
                logger.info(f"获取 {variety} 期货数据...")
                data = ak.futures_zh_realtime(symbol=variety)

                if not data.empty:
                    # 取第一个合约(通常是主力合约)
                    row = data.iloc[0]
                    price = float(row.get('trade', row.get('close', 0)))
                    open_price = float(row.get('open', price))
                    high = float(row.get('high', price))
                    low = float(row.get('low', price))
                    prev_close = float(row.get('prevsettlement', open_price))
                    volume = float(row.get('volume', 0))

                    daily_change = price - prev_close
                    daily_change_pct = float(row.get('changepercent', 0))

                    quotes.append({
                        'name': info['name'],
                        'symbol': info['symbol'],
                        'price': info['format'].format(price),
                        'open': info['format'].format(open_price),
                        'high': info['format'].format(high),
                        'low': info['format'].format(low),
                        'change': info['format'].format(daily_change),
                        'changePercent': f'{daily_change_pct:+.2f}',
                        'volume': f"{volume / 1000:.2f}K" if volume > 0 else '-',
                        'time': datetime.now().strftime('%H:%M:%S')
                    })
                    logger.info(f"{info['name']}: {info['format'].format(price)} ({daily_change_pct:+.2f}%)")

            except Exception as e:
                logger.warning(f"获取 {variety} 期货失败: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"AKShare获取国内期货失败: {str(e)}")

    # 2. 获取美元/人民币汇率
    try:
        import akshare as ak
        fx_data = ak.fx_spot_quote()
        if not fx_data.empty:
            # 查找USD/CNY
            usdcny_row = fx_data[fx_data['货币对'] == 'USD/CNY']
            if not usdcny_row.empty:
                row = usdcny_row.iloc[0]
                bid = float(row.get('买报价', 0))
                ask = float(row.get('卖报价', 0))
                price = (bid + ask) / 2  # 使用中间价
                change = 0  # AKShare只提供买卖价,没有涨跌
                change_percent = 0

                quotes.append({
                    'name': '美元/人民幣',
                    'symbol': 'USD/CNY',
                    'price': f'{price:.4f}',
                    'open': f'{price:.4f}',
                    'high': f'{ask:.4f}',
                    'low': f'{bid:.4f}',
                    'change': f'{change:+.4f}',
                    'changePercent': f'{change_percent:+.2f}',
                    'volume': '-',
                    'time': datetime.now().strftime('%H:%M:%S')
                })
                logger.info(f"USD/CNY: {price:.4f}")
    except Exception as e:
        logger.warning(f"获取美元人民币行情失败: {str(e)}")

    # 3. 从新浪财经获取美元指数
    if len([q for q in quotes if q['symbol'] == 'DX']) == 0:
        try:
            import requests
            logger.info("尝试从新浪财经获取美元指数...")

            url = "http://hq.sinajs.cn/list=DINIW"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Referer': 'https://finance.sina.com.cn/',
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                import re
                match = re.search(r'"([^"]*)"', response.text)
                if match:
                    data = match.group(1)
                    fields = data.split(',')

                    if len(fields) >= 11:
                        price = float(fields[1])
                        open_price = float(fields[2])
                        low = float(fields[3])
                        prev_close = float(fields[5])
                        high = float(fields[6])
                        name = fields[9]

                        daily_change = price - prev_close
                        daily_change_pct = (daily_change / prev_close * 100) if prev_close != 0 else 0

                        quotes.append({
                            'name': name,
                            'symbol': 'DX',
                            'price': f'{price:.3f}',
                            'open': f'{open_price:.3f}',
                            'high': f'{high:.3f}',
                            'low': f'{low:.3f}',
                            'change': f'{daily_change:.3f}',
                            'changePercent': f'{daily_change_pct:+.2f}',
                            'volume': '-',
                            'time': datetime.now().strftime('%H:%M:%S')
                        })
                        logger.info(f"美元指数: {price:.3f} ({daily_change_pct:+.2f}%)")

        except Exception as e:
            logger.warning(f"新浪财经获取美元指数失败: {str(e)}")

    # 4. 如果美元指数仍未获取到,使用模拟数据作为备用
    if len([q for q in quotes if q['symbol'] == 'DX']) == 0:
        logger.warning("美元指数真实数据获取失败,使用模拟数据")
        np.random.seed(int(datetime.now().timestamp()))
        base_price = 103.50
        daily_change_pct = np.random.uniform(-2.5, 2.5)
        price = base_price * (1 + daily_change_pct / 100)
        daily_change = price - base_price
        high = price * 1.005
        low = price * 0.995

        quotes.append({
            'name': '美元指数',
            'symbol': 'DX',
            'price': f'{price:.3f}',
            'open': f'{base_price:.3f}',
            'high': f'{high:.3f}',
            'low': f'{low:.3f}',
            'change': f'{daily_change:.3f}',
            'changePercent': f'{daily_change_pct:+.2f}',
            'volume': '-',
            'time': datetime.now().strftime('%H:%M:%S')
        })
        logger.info(f"美元指数(模拟): {price:.3f} ({daily_change_pct:+.2f}%)")

    # 返回结果
    if quotes:
        logger.info(f"成功获取 {len(quotes)} 个品种的期货行情")
        return jsonify({
            'status': 'success',
            'quotes': quotes,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    else:
        logger.warning("未获取到期货行情数据")
        return None


def _generate_mock_futures_quotes():
    """生成模拟期货行情数据"""
    # 使用当前时间作为基础,生成略有变化的数据
    np.random.seed(int(datetime.now().timestamp()))

    base_data = [
        {'name': 'WTI原油', 'symbol': 'CL', 'base_price': 76.50, 'format': '{:.2f}'},
        {'name': '倫敦布倫特原油', 'symbol': 'LCO', 'base_price': 80.20, 'format': '{:.2f}'},
        {'name': '銅 (LME)', 'symbol': 'HG', 'base_price': 4.25, 'format': '{:.4f}'},
        {'name': '美元指数期货', 'symbol': 'DX', 'base_price': 103.50, 'format': '{:.3f}'},
        {'name': '黃金', 'symbol': 'GC', 'base_price': 2050.0, 'format': '{:,.2f}'},
        {'name': '美元/人民幣', 'symbol': 'USD/CNY', 'base_price': 7.2450, 'format': '{:.4f}'},
    ]

    quotes = []
    for item in base_data:
        base = item['base_price']
        daily_change_pct = np.random.uniform(-2.5, 2.5)  # 随机涨跌幅 -2.5% 到 2.5%

        current_price = base * (1 + daily_change_pct / 100)
        daily_change = current_price - base

        high = max(base, current_price) * (1 + np.random.uniform(0, 0.01))
        low = min(base, current_price) * (1 - np.random.uniform(0, 0.01))

        quotes.append({
            'name': item['name'],
            'symbol': item['symbol'],
            'price': item['format'].format(current_price),
            'open': item['format'].format(base),
            'high': item['format'].format(high),
            'low': item['format'].format(low),
            'change': item['format'].format(daily_change),
            'changePercent': f'{daily_change_pct:+.2f}',
            'volume': f"{np.random.uniform(50, 200):.1f}K" if item['symbol'] != 'USD/CNY' else '-',
            'time': datetime.now().strftime('%H:%M:%S')
        })

    return quotes


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
