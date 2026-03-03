# 🚀 快速开始指南

## 安装

```bash
# 克隆项目
cd /Users/ydy/CodeBuddy/20260303110910-oil-price-prediction

# 安装依赖
pip install -r requirements.txt
```

## 运行预测

```bash
# 运行完整预测（推荐）
python main.py

# 仅运行长期趋势模型
python main.py --model long-term

# 仅运行中期波动模型
python main.py --model medium-term
```

## 查看结果

预测完成后，结果将保存在 `outputs/reports/` 目录：
- 文本报告: `oil_prediction_report_YYYYMMDD_HHMMSS.txt`
- HTML报告: `oil_prediction_report_YYYYMMDD_HHMMSS.html`

## 项目结构

```
oil-price-prediction/
├── data/                   # 数据目录
├── models/                 # 模型目录
│   ├── long_term.py       # 长期趋势模型
│   └── medium_term.py     # 中期波动模型
├── utils/                  # 工具目录
│   ├── data_fetcher.py    # 数据获取
│   ├── feature_engineering.py  # 特征工程
│   └── report_generator.py     # 报告生成
├── outputs/                # 输出目录
├── main.py                 # 主程序
├── config.py              # 配置文件
└── requirements.txt       # 依赖列表
```

## 核心功能

### 1. 数据获取
- 原油价格数据（WTI、Brent）
- 库存数据（EIA）
- 产量数据（OPEC、美国页岩油）
- 需求数据（PMI、进口量、炼厂开工率）
- 金融数据（美元指数、VIX、CFTC持仓）

### 2. 特征工程
- 技术指标（MA、RSI、MACD、布林带）
- 基本面因子（供需、库存、价差）
- 宏观因子（滞后、差分、滚动统计）
- 日历特征（季节性、周期性）

### 3. 模型预测
- **长期趋势模型**（6-12个月）：基于基本面因子
- **中期波动模型**（1-3个月）：基于宏观流动性
- **集成预测**：加权融合多模型结果

### 4. 情景分析
- 基准情景（50%概率）
- 上行风险（25%概率）
- 下行风险（25%概率）

## 示例输出

```
【当前市场价格】
  WTI原油价格: $75.50/桶

【长期趋势模型（6-12个月）】
  预测价格: $82.30/桶 (+8.99%)
  置信区间: [$78.50, $86.10]
  关键驱动因素: Geopolitical_Risk, Global_PMI, Inventory_Deviation

【中期波动模型（1-3个月）】
  预测价格: $77.80/桶 (+3.05%)
  置信区间: [$75.20, $80.40]
  关键驱动因素: Dollar_Index, VIX_Index, OPEC_Production_Change

【集成预测】
  预测价格: $80.05/桶 (+6.02%)
  置信区间: [$76.85, $83.25]
```

## 常见问题

### Q: 数据从哪里获取？
A: 目前使用模拟数据，实际应用中需要接入EIA、IEA、OPEC等官方API。

### Q: 如何提高预测准确性？
A: 可以通过以下方式改进：
1. 接入真实的高质量数据
2. 增加模型训练数据量
3. 调整模型参数
4. 增加更多相关特征
5. 使用更先进的模型（如LSTM、Transformer）

### Q: 如何定制模型？
A: 修改 `config.py` 中的配置参数：
- 调整模型权重
- 添加新的特征
- 修改预测周期
- 自定义情景分析

## 技术支持

如有问题，请查看：
- README.md：详细说明文档
- config.py：配置参数说明
- docs/：更多文档

---

**🛢️ 理性分析，稳健预测！**
