# AKShare数据集成指南

## 📊 什么是AKShare？

AKShare是一个开源、免费的财经数据接口库，提供中国金融市场数据，包括股票、期货、基金、外汇等多种数据类型。

## ✅ 已集成的功能

### 1. 能源期货数据
- **WTI原油期货**：通过新浪期货接口获取
- **Brent原油期货**：通过新浪期货接口获取
- 数据包括：开盘价、最高价、最低价、收盘价、成交量等

### 2. 宏观经济数据
- **PMI数据**：中国制造业采购经理指数（217条历史数据）
- **VIX指数**：波动率指数（当前使用模拟数据）
- **美元指数**：美元/人民币汇率（当前使用模拟数据）

### 3. 其他数据源
由于AKShare主要提供中国金融市场数据，部分国际数据仍使用模拟数据：
- EIA原油库存（模拟）
- OPEC产量数据（模拟）
- 美国钻机数（模拟）

## 🔧 技术实现

### 数据获取流程

```python
# 1. 初始化AKShare获取器
from utils.akshare_fetcher import AKShareFetcher
akshare_fetcher = AKShareFetcher()

# 2. 获取所有数据
data = akshare_fetcher.get_all_data()

# 3. 返回的数据包含：
# - wti: WTI原油期货数据
# - brent: Brent原油期货数据
# - pmi: PMI数据
# - vix: VIX指数（模拟）
# - eia_inventory: 库存数据（模拟）
# - opec_production: OPEC产量（模拟）
# - rig_count: 钻机数（模拟）
# - combined: 合并后的所有数据
```

### 数据合并策略

```python
def _merge_data(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    合并所有数据到统一的时间序列

    策略：
    1. 找到日期范围最大的数据集作为主数据
    2. 按日期左连接其他数据
    3. 保持原始时间序列完整性
    """
```

## 📈 数据质量

### 真实数据
- ✅ WTI/Brent原油期货价格（真实）
- ✅ PMI数据（真实，217条记录）
- ✅ 成交量数据（真实）

### 模拟数据
- ⚠️ EIA库存（模拟）
- ⚠️ OPEC产量（模拟）
- ⚠️ 美国钻机数（模拟）
- ⚠️ VIX指数（模拟）
- ⚠️ 美元指数（模拟）

## 🚀 性能优化

### 1. 数据缓存
```python
# 全局变量缓存
latest_data = None

# 只在首次加载时获取数据
if latest_data is None:
    latest_data = akshare_fetcher.get_all_data()
```

### 2. 异常处理
```python
try:
    # 尝试使用AKShare获取真实数据
    latest_data = akshare_fetcher.get_all_data()
except Exception as e:
    # 失败时使用模拟数据
    latest_data = generate_mock_data()
```

### 3. 数据限流
AKShare没有严格的API限流，但建议：
- 避免频繁调用（每分钟不超过10次）
- 使用全局变量缓存数据
- 定期更新（建议每天1-2次）

## 🔄 数据更新策略

### 自动更新
```python
# 在Flask应用中
@app.route('/api/refresh_data')
def refresh_data():
    """手动刷新数据"""
    global latest_data
    latest_data = akshare_fetcher.get_all_data()
    return jsonify({'status': 'success', 'message': '数据已刷新'})
```

### 定时任务
```python
# 可以使用APScheduler添加定时任务
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    refresh_data,
    'interval',
    hours=24,  # 每24小时刷新一次
    id='data_refresh'
)
scheduler.start()
```

## 📊 数据验证

### 测试AKShare数据获取
```bash
cd /Users/ydy/CodeBuddy/20260303110910-oil-price-prediction
python utils/akshare_fetcher.py
```

### 测试API端点
```bash
# 测试数据获取
curl http://localhost:5003/api/data | python -m json.tool

# 测试预测
curl -X POST http://localhost:5003/api/predict | python -m json.tool
```

## 🌐 与其他数据源对比

| 数据源 | 免费程度 | 覆盖范围 | 限流情况 | 推荐 |
|--------|---------|---------|---------|------|
| AKShare | ✅ 完全免费 | 中国市场为主 | 轻度 | ⭐⭐⭐⭐ |
| yfinance | ✅ 免费 | 全球市场 | 严格 | ⭐⭐ |
| Wind | ❌ 付费 | 全面 | 无 | ⭐⭐⭐⭐⭐ |
| Bloomberg | ❌ 付费 | 全面 | 无 | ⭐⭐⭐⭐⭐ |

## 💡 使用建议

### 1. 优势
- ✅ 完全免费
- ✅ 无需API密钥
- ✅ 覆盖中国主要期货市场
- ✅ 数据更新及时
- ✅ 社区活跃，文档完善

### 2. 局限
- ⚠️ 国际数据覆盖有限
- ⚠️ 部分数据需要模拟
- ⚠️ 需要网络连接
- ⚠️ 数据质量依赖数据源

### 3. 适用场景
- 📈 中国市场原油期货分析
- 📊 PMI等宏观数据分析
- 🎯 中短期价格预测
- 💰 投资决策参考

## 🔍 高级用法

### 1. 自定义数据获取
```python
from utils.akshare_fetcher import AKShareFetcher

fetcher = AKShareFetcher()

# 单独获取某个数据
wti_data = fetcher.get_energy_futures()
pmi_data = fetcher.get_macro_data()
```

### 2. 数据预处理
```python
# 过滤特定日期范围
start_date = '2025-01-01'
end_date = '2025-12-31'
filtered_data = data[
    (data['date'] >= start_date) &
    (data['date'] <= end_date)
]

# 计算技术指标
data['MA5'] = data['close'].rolling(5).mean()
data['MA20'] = data['close'].rolling(20).mean()
```

### 3. 数据导出
```python
# 导出为CSV
data.to_csv('oil_data.csv', index=False)

# 导出为Excel
data.to_excel('oil_data.xlsx', index=False)
```

## 🐛 常见问题

### Q1: AKShare获取数据失败怎么办？
A:
1. 检查网络连接
2. 查看错误日志
3. 系统会自动降级使用模拟数据

### Q2: 数据更新频率如何？
A:
- 期货数据：实时更新（交易时间内）
- PMI数据：月度更新
- 其他数据：按各自频率更新

### Q3: 如何切换到其他数据源？
A:
修改 `app.py` 中的数据获取逻辑：
```python
# 使用yfinance
latest_data = data_fetcher.get_all_data()

# 使用AKShare
latest_data = akshare_fetcher.get_all_data()

# 使用模拟数据
latest_data = generate_mock_data()
```

### Q4: 能否同时使用多个数据源？
A: 可以，需要自定义合并逻辑：
```python
# 获取多个数据源
yf_data = data_fetcher.get_all_data()
aks_data = akshare_fetcher.get_all_data()

# 合并数据
merged_data = merge_data_sources(yf_data, aks_data)
```

## 📚 参考资料

- AKShare官方文档: https://akshare.akfamily.xyz/
- AKShare GitHub: https://github.com/akfamily/akshare
- 新浪期货API文档: http://finance.sina.com.cn/futuremarket/

## 🎯 总结

AKShare为原油价格预测系统提供了：
1. ✅ 免费的期货价格数据
2. ✅ 真实的PMI宏观数据
3. ✅ 稳定的数据获取方式
4. ✅ 完善的异常处理
5. ✅ 良好的性能表现

系统现在使用AKShare作为主要数据源，提供更准确的数据支持！
