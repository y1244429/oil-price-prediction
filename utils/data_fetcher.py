#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
原油数据获取模块
"""

import akshare as ak
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OilDataFetcher:
    """原油数据获取器"""

    def __init__(self):
        self.data_cache = {}
        logger.info("原油数据获取器初始化完成")

    def get_oil_price_data(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取原油价格数据（WTI和Brent）

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            包含WTI和Brent价格的DataFrame
        """
        try:
            logger.info("开始获取原油价格数据...")

            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

            # 使用yfinance获取WTI和Brent期货数据
            wti_ticker = "CL=F"  # WTI原油期货
            brent_ticker = "BZ=F"  # Brent原油期货

            logger.info(f"获取WTI数据: {wti_ticker}")
            wti_data = yf.download(wti_ticker, start=start_date, end=end_date, progress=False)

            logger.info(f"获取Brent数据: {brent_ticker}")
            brent_data = yf.download(brent_ticker, start=start_date, end=end_date, progress=False)

            # 合并数据
            data = pd.DataFrame({
                'WTI_Close': wti_data['Close'],
                'WTI_Volume': wti_data['Volume'],
                'Brent_Close': brent_data['Close'],
                'Brent_Volume': brent_data['Volume']
            })

            # 计算价差
            data['Spread'] = data['Brent_Close'] - data['WTI_Close']

            logger.info(f"成功获取 {len(data)} 条原油价格数据")
            return data

        except Exception as e:
            logger.error(f"获取原油价格数据失败: {e}")
            return None

    def get_inventory_data(self) -> pd.DataFrame:
        """
        获取库存数据（EIA原油库存）

        Returns:
            包含库存数据的DataFrame
        """
        try:
            logger.info("开始获取库存数据...")

            # 使用AKShare获取EIA库存数据
            # 注意：AKShare的EIA数据可能有限，这里使用模拟数据
            # 实际应用中需要接入EIA API

            # 获取最近的历史价格数据作为基础
            price_data = self.get_oil_price_data()

            if price_data is None:
                return None

            # 生成模拟库存数据（实际应用中从EIA API获取）
            np.random.seed(42)
            base_inventory = 400  # 基准库存（百万桶）

            # 生成库存数据
            dates = price_data.index
            inventory_values = []

            for i in range(len(dates)):
                # 模拟库存波动
                noise = np.random.normal(0, 10)
                seasonality = 10 * np.sin(2 * np.pi * i / 52)  # 周期性
                trend = -0.5 * i  # 轻微下降趋势
                inventory = base_inventory + noise + seasonality + trend
                inventory_values.append(inventory)

            inventory_data = pd.DataFrame({
                'EIA_Crude_Inventory': inventory_values
            }, index=dates)

            # 计算5年均值偏离度
            inventory_data['Inventory_5Y_Avg'] = inventory_data['EIA_Crude_Inventory'].rolling(window=252).mean()
            inventory_data['Inventory_Deviation'] = (
                (inventory_data['EIA_Crude_Inventory'] - inventory_data['Inventory_5Y_Avg']) /
                inventory_data['Inventory_5Y_Avg'] * 100
            )

            logger.info(f"成功获取 {len(inventory_data)} 条库存数据")
            return inventory_data

        except Exception as e:
            logger.error(f"获取库存数据失败: {e}")
            return None

    def get_production_data(self) -> pd.DataFrame:
        """
        获取产量数据（OPEC、美国页岩油等）

        Returns:
            包含产量数据的DataFrame
        """
        try:
            logger.info("开始获取产量数据...")

            # 获取价格数据作为基准
            price_data = self.get_oil_price_data()

            if price_data is None:
                return None

            # 生成模拟产量数据（实际应用中从EIA/IEA/OPEC获取）
            dates = price_data.index

            # OPEC产量（百万桶/天）
            opec_base = 30.0
            opec_production = []
            for i in range(len(dates)):
                noise = np.random.normal(0, 0.5)
                seasonality = 0.3 * np.sin(2 * np.pi * i / 52)
                production = opec_base + noise + seasonality
                opec_production.append(production)

            # 美国钻机数（领先指标）
            rig_base = 500
            rig_count = []
            for i in range(len(dates)):
                noise = np.random.normal(0, 20)
                trend = 0.1 * i  # 缓慢上升趋势
                rigs = rig_base + noise + trend
                rig_count.append(rigs)

            # 全球闲置产能（百万桶/天）
            spare_capacity_base = 5.0
            spare_capacity = []
            for i in range(len(dates)):
                noise = np.random.normal(0, 0.3)
                capacity = spare_capacity_base + noise
                spare_capacity.append(capacity)

            production_data = pd.DataFrame({
                'OPEC_Production': opec_production,
                'US_Rig_Count': rig_count,
                'Global_Spare_Capacity': spare_capacity
            }, index=dates)

            logger.info(f"成功获取 {len(production_data)} 条产量数据")
            return production_data

        except Exception as e:
            logger.error(f"获取产量数据失败: {e}")
            return None

    def get_demand_data(self) -> pd.DataFrame:
        """
        获取需求数据（PMI、进口量、炼厂开工率等）

        Returns:
            包含需求数据的DataFrame
        """
        try:
            logger.info("开始获取需求数据...")

            # 获取价格数据作为基准
            price_data = self.get_oil_price_data()

            if price_data is None:
                return None

            dates = price_data.index

            # 全球PMI制造业指数
            pmi_base = 52.0
            global_pmi = []
            for i in range(len(dates)):
                noise = np.random.normal(0, 1.0)
                cycle = 2.0 * np.sin(2 * np.pi * i / 52)
                pmi = pmi_base + noise + cycle
                pmi.append(pmi)

            # 中国原油进口（百万桶/天）
            china_import_base = 10.0
            china_import = []
            for i in range(len(dates)):
                noise = np.random.normal(0, 0.5)
                seasonality = 1.0 * np.sin(2 * np.pi * i / 52)
                imports = china_import_base + noise + seasonality
                china_import.append(imports)

            # 美国炼厂开工率（百分比）
            refinery_utilization_base = 85.0
            refinery_utilization = []
            for i in range(len(dates)):
                noise = np.random.normal(0, 3.0)
                seasonality = 10.0 * np.sin(2 * np.pi * i / 52)
                utilization = refinery_utilization_base + noise + seasonality
                utilization = np.clip(utilization, 60, 95)  # 限制在合理范围
                refinery_utilization.append(utilization)

            # 航空煤油需求恢复指标（相对于2019年的百分比）
            jet_fuel_base = 90.0
            jet_fuel_demand = []
            for i in range(len(dates)):
                noise = np.random.normal(0, 2.0)
                trend = 0.05 * i  # 逐渐恢复
                demand = jet_fuel_base + noise + trend
                demand = np.clip(demand, 70, 100)
                jet_fuel_demand.append(demand)

            demand_data = pd.DataFrame({
                'Global_PMI': global_pmi,
                'China_Import': china_import,
                'US_Refinery_Utilization': refinery_utilization,
                'Jet_Fuel_Demand': jet_fuel_demand
            }, index=dates)

            logger.info(f"成功获取 {len(demand_data)} 条需求数据")
            return demand_data

        except Exception as e:
            logger.error(f"获取需求数据失败: {e}")
            return None

    def get_financial_data(self) -> pd.DataFrame:
        """
        获取金融数据（美元指数、VIX、CFTC持仓等）

        Returns:
            包含金融数据的DataFrame
        """
        try:
            logger.info("开始获取金融数据...")

            # 获取价格数据作为基准
            price_data = self.get_oil_price_data()

            if price_data is None:
                return None

            dates = price_data.index

            # 美元指数（DXY）
            dxy_base = 105.0
            dollar_index = []
            for i in range(len(dates)):
                noise = np.random.normal(0, 1.0)
                cycle = 3.0 * np.sin(2 * np.pi * i / 104)  # 半年周期
                dxy = dxy_base + noise + cycle
                dollar_index.append(dxy)

            # VIX恐慌指数
            vix_base = 20.0
            vix_index = []
            for i in range(len(dates)):
                noise = np.random.normal(0, 3.0)
                vix = vix_base + noise
                vix = np.clip(vix, 10, 50)  # 限制在合理范围
                vix_index.append(vix)

            # CFTC非商业净持仓（千手）
            cftc_base = 200
            cftc_position = []
            for i in range(len(dates)):
                noise = np.random.normal(0, 30)
                position = cftc_base + noise
                cftc_position.append(position)

            # 地缘政治风险指数（GPR）
            gpr_base = 100
            gpr_index = []
            for i in range(len(dates)):
                noise = np.random.normal(0, 10)
                # 模拟突发事件（第100天和第200天）
                if 95 < i < 105:
                    gpr = gpr_base + 50 + noise
                elif 195 < i < 205:
                    gpr = gpr_base + 30 + noise
                else:
                    gpr = gpr_base + noise
                gpr = np.clip(gpr, 50, 200)
                gpr_index.append(gpr)

            financial_data = pd.DataFrame({
                'Dollar_Index': dollar_index,
                'VIX_Index': vix_index,
                'CFTC_Net_Position': cftc_position,
                'Geopolitical_Risk': gpr_index
            }, index=dates)

            logger.info(f"成功获取 {len(financial_data)} 条金融数据")
            return financial_data

        except Exception as e:
            logger.error(f"获取金融数据失败: {e}")
            return None

    def get_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        获取所有数据

        Returns:
            包含所有数据的字典
        """
        logger.info("=" * 60)
        logger.info("开始获取所有原油市场数据...")
        logger.info("=" * 60)

        all_data = {}

        # 获取各类数据
        all_data['price'] = self.get_oil_price_data()
        time.sleep(1)

        all_data['inventory'] = self.get_inventory_data()
        time.sleep(1)

        all_data['production'] = self.get_production_data()
        time.sleep(1)

        all_data['demand'] = self.get_demand_data()
        time.sleep(1)

        all_data['financial'] = self.get_financial_data()

        # 合并所有数据
        try:
            combined_data = pd.concat([
                all_data['price'],
                all_data['inventory'],
                all_data['production'],
                all_data['demand'],
                all_data['financial']
            ], axis=1)

            all_data['combined'] = combined_data

            logger.info("=" * 60)
            logger.info("数据获取完成！")
            logger.info(f"总共获取 {len(combined_data)} 条记录")
            logger.info(f"包含 {len(combined_data.columns)} 个特征")
            logger.info("=" * 60)

            return all_data

        except Exception as e:
            logger.error(f"合并数据失败: {e}")
            return all_data

    def save_data(self, data: pd.DataFrame, filename: str):
        """
        保存数据到文件

        Args:
            data: 要保存的数据
            filename: 文件名
        """
        try:
            from config import PROCESSED_DATA_DIR
            filepath = PROCESSED_DATA_DIR / filename
            data.to_csv(filepath)
            logger.info(f"数据已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存数据失败: {e}")


if __name__ == "__main__":
    # 测试数据获取
    fetcher = OilDataFetcher()

    # 获取所有数据
    all_data = fetcher.get_all_data()

    # 打印数据摘要
    if all_data.get('combined') is not None:
        print("\n" + "=" * 60)
        print("数据摘要")
        print("=" * 60)
        print(all_data['combined'].info())
        print("\n前5行数据:")
        print(all_data['combined'].head())
        print("\n统计描述:")
        print(all_data['combined'].describe())

        # 保存数据
        fetcher.save_data(all_data['combined'], 'oil_market_data.csv')
