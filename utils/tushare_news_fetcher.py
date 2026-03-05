#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tushare财经新闻获取器
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class TushareNewsFetcher:
    """Tushare新闻获取器"""

    def __init__(self, token=None):
        """
        初始化Tushare新闻获取器

        Args:
            token: Tushare API token, 如果为None则从环境变量读取
        """
        self.token = token or os.getenv('TUSHARE_TOKEN', '')
        self.api = None

        if self.token:
            try:
                import tushare as ts
                ts.set_token(self.token)
                self.api = ts.pro_api()
                logger.info("Tushare API初始化成功")
            except Exception as e:
                logger.error(f"Tushare API初始化失败: {str(e)}")
                self.api = None
        else:
            logger.warning("未提供Tushare token,将使用模拟数据")

    def fetch_news(self, limit=20):
        """
        获取财经新闻

        Args:
            limit: 获取新闻数量

        Returns:
            list: 新闻列表,每条新闻包含标题、摘要、时间、来源等
        """
        if not self.api:
            logger.warning("Tushare API未初始化")
            return []

        try:
            # 获取当前时间和30天前的时间
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            # 调用Tushare新闻接口
            df = self.api.news(
                src='sina',  # 新浪财经
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d')
            )

            if df is None or df.empty:
                logger.warning("未获取到新闻数据")
                return []

            # 转换为标准格式
            news_list = []
            for idx, row in df.head(limit).iterrows():
                try:
                    # 解析时间
                    pub_time = pd.to_datetime(row.get('datetime', row.get('time', datetime.now())))
                    time_str = pub_time.strftime('%H:%M')

                    # 清理摘要
                    summary = row.get('content', row.get('summary', ''))
                    if isinstance(summary, str):
                        summary = summary[:150] + '...' if len(summary) > 150 else summary
                    else:
                        summary = '暂无摘要'

                    news_item = {
                        'title': row.get('title', '未知标题'),
                        'summary': summary,
                        'source': row.get('source', '新浪财经'),
                        'time': time_str,
                        'link': row.get('url', ''),
                        'sentiment': self._analyze_sentiment(row.get('title', '')),
                        'impact': self._analyze_impact(row.get('title', '')),
                        'category': self._categorize_news(row.get('title', '')),
                        'pub_date': pub_time.strftime('%Y-%m-%d %H:%M:%S')
                    }

                    news_list.append(news_item)
                except Exception as e:
                    logger.warning(f"解析单条新闻失败: {str(e)}")
                    continue

            logger.info(f"成功获取 {len(news_list)} 条财经新闻")
            return news_list

        except Exception as e:
            error_msg = str(e)
            logger.error(f"获取Tushare新闻失败: {error_msg}")

            # 如果是API限制错误,抛出异常让上层处理
            if '每分钟最多' in error_msg or '每小时最多' in error_msg:
                raise Exception(error_msg)
            else:
                return []

    def _analyze_sentiment(self, text):
        """简单的情感分析"""
        if not text:
            return 'neutral'

        positive_keywords = ['增长', '上涨', '突破', '创新', '成功', '利好', '回升',
                          '大涨', '繁荣', '优化', '改善', '提升', '扩大', '加速',
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

    def _analyze_impact(self, text):
        """分析影响程度"""
        if not text:
            return 'medium'

        high_impact_keywords = ['重大', '突破', '首次', '创', '新高', '暴跌', '大涨',
                               '重要', '关键', '紧急', '重磅', 'major', 'breakthrough',
                               'record', 'crucial', 'important', 'significant']

        text_lower = text.lower()
        high_count = sum(1 for keyword in high_impact_keywords if keyword in text_lower)

        if high_count >= 1:
            return 'high'
        else:
            return 'medium'

    def _categorize_news(self, title):
        """对新闻进行分类"""
        if not title:
            return '财经要闻'

        title_lower = title.lower()

        categories = {
            '原油市场': ['原油', '石油', 'opec', 'wti', '布伦特', 'brent', 'oil'],
            '外汇市场': ['美元', '欧元', '英镑', '日元', '汇率', '美元指数', '外汇', 'forex'],
            '贵金属': ['黄金', '白银', 'gold', 'silver', '贵金属', 'comex'],
            '股市动态': ['股市', '大盘', '沪指', '深成指', '创业板', '科创板', '上涨', '下跌'],
            '宏观经济': ['pmi', 'gdp', 'cpi', 'ppi', '制造业', '经济', '通胀', '通缩', '宏观数据'],
            '货币政策': ['央行', '降息', '加息', '利率', 'mlf', '逆回购', '政策', '货币'],
            '产业经济': ['新能源', '光伏', '风电', '汽车', '房地产', '基建', '投资'],
            '数字经济': ['数字', 'ai', '人工智能', '云计算', '大数据', '区块链', '元宇宙'],
            '对外贸易': ['出口', '进口', '贸易', '顺差', '逆差', '外贸'],
            '债券市场': ['债券', '国债', '地方债', '企业债', '收益率', 'bond']
        }

        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category

        return '财经要闻'


# 测试代码
if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(level=logging.INFO)

    # 注意: 需要先设置 TUSHARE_TOKEN 环境变量
    # 或者传入 token 参数
    token = os.getenv('TUSHARE_TOKEN', '')

    if not token:
        print("❌ 请先设置 TUSHARE_TOKEN 环境变量")
        print("   注册地址: https://tushare.pro/register")
        print("   设置方式: export TUSHARE_TOKEN=your_token_here")
        exit(1)

    fetcher = TushareNewsFetcher(token=token)
    news = fetcher.fetch_news(limit=10)

    print(f"\n获取到 {len(news)} 条新闻:\n")
    for i, item in enumerate(news, 1):
        print(f"{i}. [{item['category']}] {item['title']}")
        print(f"   来源: {item['source']}  时间: {item['time']}")
        print(f"   情感: {item['sentiment']}  影响: {item['impact']}")
        if item['link']:
            print(f"   链接: {item['link']}")
        print(f"   摘要: {item['summary'][:80]}...")
        print()
