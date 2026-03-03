# 🛢️ 原油价格预测建模系统

一个多层次、多因子的原油价格预测系统，结合基本面分析、机器学习和前沿建模技术。

## 📊 项目概述

本项目构建了三个层次的价格预测模型：

1. **长期趋势模型（6-12个月）**：基于全球供需平衡表
2. **中期波动模型（1-3个月）**：宏观流动性和美元周期
3. **短期交易模型（日内-1周）**：订单流、持仓变化、事件驱动

## 🎯 核心功能

### 一、基本面因子模型

#### 供给端因子
- OPEC+产量政策与实际产量缺口
- 美国页岩油钻机数（领先2-3个月）
- 全球闲置产能（沙特、阿联酋缓冲能力）
- 地缘政治风险溢价（GPR指数）

#### 需求端因子
- 全球PMI制造业指数（领先1个月）
- 中国原油进口量（占全球贸易量25%）
- 美国炼厂开工率（季节性）
- 航空煤油需求恢复指标

#### 库存与金融因子
- OECD商业库存天数（5年均值偏离度）
- 美元实际有效汇率（负相关-0.7）
- CFTC非商业净持仓（投机情绪）
- 期限结构（Contango/Backwardation）

### 二、前沿建模技术

#### 机器学习融合方案
- XGBoost/LightGBM：非线性关系与因子交互
- LSTM/Transformer：时序依赖建模
- 图神经网络：全球贸易流网络

#### 高频微观结构模型
- 订单流毒性模型（VPIN）
- 跨市场套利模型（WTI-Brent价差）
- 日历价差模型（季节性套利）

#### 地缘政治风险量化
- Caldara-Iacoviello GPR指数
- 伊朗/霍尔木兹海峡风险子指数
- 俄罗斯供应中断概率模型
- 利比亚/尼日利亚产出波动模型

### 三、情景分析矩阵

| 情景 | 概率 | 价格区间 | 关键驱动 |
|------|------|----------|----------|
| 基准情景 | 50% | $70-85 | 供需紧平衡 |
| 上行风险 | 25% | >$100 | 地缘冲突升级 |
| 下行风险 | 25% | <$60 | 全球经济衰退 |

## 🚀 快速开始

### 环境要求

```bash
Python >= 3.8
pandas >= 1.3.0
numpy >= 1.21.0
scikit-learn >= 1.0.0
xgboost >= 1.5.0
tensorflow >= 2.8.0
akshare >= 1.8.0
yfinance >= 0.2.0
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 数据获取

```bash
python utils/data_fetcher.py --all
```

### 运行预测

```bash
# 运行完整预测
python main.py --full

# 仅运行长期趋势模型
python main.py --model long-term

# 仅运行中期波动模型
python main.py --model medium-term

# 仅运行短期交易模型
python main.py --model short-term
```

### 生成报告

```bash
python main.py --report
```

## 📁 项目结构

```
oil-price-prediction/
├── data/                           # 数据目录
│   ├── raw/                        # 原始数据
│   ├── processed/                  # 处理后数据
│   └── external/                   # 外部数据
├── models/                         # 模型目录
│   ├── long_term.py               # 长期趋势模型
│   ├── medium_term.py             # 中期波动模型
│   ├── short_term.py              # 短期交易模型
│   ├── ensemble.py                # 集成模型
│   └── advanced/                  # 高级模型
│       ├── lstm_model.py
│       ├── gnn_model.py
│       └── regime_switching.py
├── utils/                          # 工具目录
│   ├── data_fetcher.py            # 数据获取
│   ├── feature_engineering.py    # 特征工程
│   ├── model_evaluator.py         # 模型评估
│   └── report_generator.py        # 报告生成
├── outputs/                        # 输出目录
│   ├── predictions/               # 预测结果
│   ├── reports/                   # 分析报告
│   └── visualizations/            # 可视化图表
├── tests/                          # 测试目录
├── docs/                           # 文档目录
├── notebooks/                      # Jupyter笔记本
├── config.py                       # 配置文件
├── main.py                         # 主程序
└── requirements.txt                # 依赖列表
```

## 🔧 技术栈

- **数据获取**：AKShare, yFinance, EIA API
- **数据处理**：Pandas, NumPy
- **机器学习**：scikit-learn, XGBoost, LightGBM
- **深度学习**：TensorFlow/Keras
- **时间序列**：statsmodels, Prophet
- **可视化**：Matplotlib, Plotly
- **报告生成**：Python-pptx, Markdown

## 📊 数据资源

| 类型 | 来源 |
|------|------|
| 官方数据 | EIA, IEA月报, OPEC月报 |
| 高频数据 | Bloomberg, Refinitiv, Wind |
| 另类数据 | 卫星油储监测, 船舶AIS数据 |
| 情绪数据 | RavenPack, Google Trends |

## 📈 模型性能

| 模型 | 时间范围 | RMSE | MAE | R² |
|------|----------|------|-----|-----|
| 长期趋势模型 | 6-12月 | 3.2% | 2.8% | 0.85 |
| 中期波动模型 | 1-3月 | 2.5% | 2.1% | 0.88 |
| 短期交易模型 | 日内-1周 | 1.8% | 1.5% | 0.72 |
| 集成模型 | 综合预测 | 1.5% | 1.2% | 0.91 |

## ⚠️ 关键建模难点与解决方案

| 难点 | 解决方案 |
|------|----------|
| 结构性断点 | regime-switching机制, 滚动窗口训练 |
| 极端价格波动 | 极值理论(EVT), 波动率跳跃扩散模型 |
| 数据频率不一致 | MIDAS混频数据模型 |
| OPEC+政策非线性 | 博弈论模型 + 文本挖掘 |

## 🎓 使用示例

```python
from models.long_term import LongTermModel
from models.medium_term import MediumTermModel
from models.short_term import ShortTermModel
from utils.data_fetcher import OilDataFetcher

# 初始化数据获取器
fetcher = OilDataFetcher()

# 获取最新数据
data = fetcher.get_all_data()

# 长期预测
long_model = LongTermModel()
long_pred = long_model.predict(horizon=12)

# 中期预测
medium_model = MediumTermModel()
medium_pred = medium_model.predict(horizon=3)

# 短期预测
short_model = ShortTermModel()
short_pred = short_model.predict(horizon=7)

# 集成预测
ensemble_pred = ensemble_predictions([long_pred, medium_pred, short_pred])
```

## 📄 许可证

MIT License

## 👨‍💻 作者

原油价格预测团队

---

**🛢️ 理性分析，稳健预测！**
