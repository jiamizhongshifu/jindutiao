# GaiYa性能测试指南

本目录包含GaiYa项目的性能测试套件，用于验证系统在高负载下的表现。

## 📁 文件结构

```
tests/performance/
├── __init__.py                  # Python包标记
├── README.md                    # 本文档
├── locustfile.py                # Locust压力测试脚本
└── test_api_performance.py      # pytest性能基准测试
```

---

## 🛠️ 环境准备

### 1. 安装依赖

```bash
# 安装Locust（压力测试工具）
pip install locust

# 安装pytest-benchmark（性能基准测试）
pip install pytest-benchmark

# 安装requests（API测试）
pip install requests
```

### 2. 验证安装

```bash
# 检查Locust版本
locust --version

# 检查pytest-benchmark是否可用
pytest --benchmark-help
```

---

## 🚀 运行测试

### 方案1: Locust压力测试 (推荐用于实际部署验证)

#### 1.1 Web UI模式（交互式）

```bash
# 启动Locust Web UI
locust -f tests/performance/locustfile.py --host=https://jindutiao.vercel.app

# 访问 http://localhost:8089
# 在Web界面设置:
# - Number of users: 100
# - Spawn rate: 10 users/second
# - Host: https://jindutiao.vercel.app
```

**Web UI功能**:
- 实时查看请求统计（RPS, 响应时间, 失败率）
- 动态调整并发用户数
- 查看响应时间分布图
- 下载CSV/HTML报告

#### 1.2 Headless模式（适合CI/CD）

```bash
# 无UI模式运行，生成HTML报告
locust -f tests/performance/locustfile.py \
       --host=https://jindutiao.vercel.app \
       --users 50 \
       --spawn-rate 5 \
       --run-time 3m \
       --headless \
       --html=reports/performance_report.html \
       --csv=reports/performance_stats
```

**参数说明**:
- `--users 50`: 模拟50个并发用户
- `--spawn-rate 5`: 每秒增加5个用户
- `--run-time 3m`: 运行3分钟
- `--headless`: 无Web UI模式
- `--html`: 生成HTML报告
- `--csv`: 生成CSV统计数据

#### 1.3 性能基准验证（验证100 QPS目标）

```bash
# 高负载压力测试
locust -f tests/performance/locustfile.py \
       --host=https://jindutiao.vercel.app \
       --users 200 \
       --spawn-rate 20 \
       --run-time 10m \
       --headless \
       --html=reports/benchmark_report.html
```

**验收标准**:
- ✅ 支持100+ QPS (每秒请求数)
- ✅ P95响应时间 < 500ms (配额/订阅查询)
- ✅ P95响应时间 < 5s (AI任务规划)
- ✅ 错误率 < 1%

---

### 方案2: pytest-benchmark本地性能测试

#### 2.1 运行所有性能测试

```bash
# 运行所有性能基准测试
pytest tests/performance/test_api_performance.py -v --benchmark-only
```

#### 2.2 保存基准数据（用于对比）

```bash
# 第一次运行：保存基准数据
pytest tests/performance/test_api_performance.py \
       --benchmark-save=baseline \
       --benchmark-only

# 修改代码后运行：对比性能变化
pytest tests/performance/test_api_performance.py \
       --benchmark-compare=baseline \
       --benchmark-only
```

**输出示例**:
```
-------------------- benchmark 'test_quota_manager_performance' ---------------------
Name (time in ms)              Min      Max     Mean    StdDev  Median     Ops
--------------------------------------------------------------------------------------
test_quota_manager[baseline]  12.34   15.67   13.45    0.89    13.23    74.35
test_quota_manager[current]   11.89   14.23   12.78    0.67    12.56    78.25
--------------------------------------------------------------------------------------
```

#### 2.3 生成详细报告

```bash
# 生成JSON报告
pytest tests/performance/test_api_performance.py \
       --benchmark-only \
       --benchmark-json=reports/benchmark.json

# 查看详细统计列
pytest tests/performance/test_api_performance.py \
       --benchmark-only \
       --benchmark-columns=min,max,mean,stddev,median,ops,outliers
```

---

## 📊 测试场景说明

### Locust测试场景

| 任务 | 权重 | API端点 | 预期性能 | 说明 |
|------|------|---------|----------|------|
| 配额查询 | 5 (最高) | `/api/quota-status` | P95 < 500ms | 用户最常用功能 |
| 任务规划 | 3 (中) | `/api/plan-tasks` | P95 < 5s | AI生成，允许较慢 |
| 订阅查询 | 2 (低) | `/api/subscription-status` | P95 < 500ms | 偶尔查询 |
| 健康检查 | 1 (偶尔) | `/api/health` | P95 < 200ms | 监控端点 |

### pytest-benchmark测试场景

| 测试用例 | 目标组件 | 验收标准 | 说明 |
|----------|----------|----------|------|
| `test_quota_manager_performance` | QuotaManager.get_quota_status | 平均 < 50ms, P95 < 100ms | 纯逻辑性能 |
| `test_quota_manager_use_quota_performance` | QuotaManager.use_quota | 平均 < 100ms, P95 < 200ms | 包含写操作 |
| `test_subscription_manager_get_subscription_performance` | SubscriptionManager.get_user_subscription | 平均 < 50ms, P95 < 100ms | 读取订阅 |
| `test_quota_status_endpoint_response_time` | `/api/quota-status` | P95 < 500ms | E2E测试 |
| `test_health_endpoint_response_time` | `/api/health` | P95 < 200ms | E2E测试 |

---

## 📈 性能指标解释

### 关键指标

- **RPS (Requests Per Second)**: 每秒请求数，反映系统吞吐量
- **P50 (Median)**: 50%的请求响应时间低于此值
- **P95**: 95%的请求响应时间低于此值（重要指标）
- **P99**: 99%的请求响应时间低于此值
- **Min/Max**: 最小/最大响应时间
- **Mean**: 平均响应时间
- **StdDev**: 标准差，反映响应时间的波动性
- **Failure Rate**: 请求失败率

### 性能基准目标

```
✅ 优秀: P95 < 200ms, RPS > 200, 失败率 < 0.1%
✅ 良好: P95 < 500ms, RPS > 100, 失败率 < 1%
⚠️ 可接受: P95 < 1s, RPS > 50, 失败率 < 5%
❌ 需优化: P95 > 1s 或 RPS < 50 或 失败率 > 5%
```

---

## 🔍 问题排查

### 问题1: Locust无法连接到API

**症状**: `Connection refused` 或 `404 Not Found`

**解决方案**:
```bash
# 1. 检查API是否部署
curl https://jindutiao.vercel.app/api/health

# 2. 检查host参数是否正确
locust -f tests/performance/locustfile.py --host=https://jindutiao.vercel.app

# 3. 检查防火墙/网络设置
```

### 问题2: pytest-benchmark测试失败

**症状**: `ModuleNotFoundError: No module named 'pytest_benchmark'`

**解决方案**:
```bash
# 重新安装pytest-benchmark
pip install --upgrade pytest-benchmark

# 验证安装
pip show pytest-benchmark
```

### 问题3: 性能结果不稳定

**症状**: 每次运行结果差异很大

**解决方案**:
```bash
# 增加迭代次数以获得更稳定的结果
pytest tests/performance/test_api_performance.py \
       --benchmark-only \
       --benchmark-min-rounds=10

# 预热阶段（跳过前几次测量）
pytest tests/performance/test_api_performance.py \
       --benchmark-only \
       --benchmark-warmup=on
```

---

## 📝 CI/CD集成

### GitHub Actions示例

```yaml
name: Performance Tests

on:
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点运行
  workflow_dispatch:  # 手动触发

jobs:
  performance-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install locust pytest-benchmark requests

      - name: Run Locust performance test
        run: |
          mkdir -p reports
          locust -f tests/performance/locustfile.py \
                 --host=${{ secrets.API_BASE_URL }} \
                 --users 50 \
                 --spawn-rate 5 \
                 --run-time 3m \
                 --headless \
                 --html=reports/locust_report.html

      - name: Run pytest-benchmark
        run: |
          pytest tests/performance/test_api_performance.py \
                 --benchmark-only \
                 --benchmark-json=reports/benchmark.json

      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: performance-reports
          path: reports/
```

---

## 🎯 验收检查清单

在Phase 3完成后，确认以下检查项:

- [ ] Locust脚本能成功运行并生成报告
- [ ] pytest-benchmark测试全部通过
- [ ] P95响应时间满足基准要求
- [ ] 系统能稳定支持100+ QPS
- [ ] 错误率 < 1%
- [ ] 性能测试文档完整且易懂
- [ ] CI/CD集成性能测试（可选）

---

## 📚 参考资料

- [Locust官方文档](https://docs.locust.io/)
- [pytest-benchmark文档](https://pytest-benchmark.readthedocs.io/)
- [Vercel性能最佳实践](https://vercel.com/docs/concepts/limits/overview)
- [Supabase性能优化](https://supabase.com/docs/guides/platform/performance)

---

**最后更新**: 2025-01-19
**维护者**: Claude AI Assistant
