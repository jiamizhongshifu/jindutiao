# Tests 目录说明

本目录包含PyDayBar项目的所有测试文件。

## 目录结构

```
tests/
├── unit/               # 单元测试（待添加）
├── integration/        # 集成测试（待添加）
├── fixtures/           # 测试数据和资源（待添加）
├── test_*.py           # 旧版本测试脚本（待整理）
└── README.md           # 本文件
```

## 当前测试文件

以下是从根目录移动过来的旧测试脚本，需要进一步整理：

### API测试
- `test_backend_api.py` - 后端API集成测试
- `test_vercel_api.py` - Vercel云服务API测试
- `test_quota.py` - 配额系统测试
- `test_quota_simple.py` - 配额系统简化测试
- `test_tuzi_connection.py` - 兔子API连接测试

### 性能测试
- `test_performance.py` - 性能基准测试
- `test_fps.py` - 帧率测试
- `test_loop.py` - 循环性能测试

### 功能测试
- `test_v1.4.py` - v1.4版本功能测试

## 后续改进计划

### 第二阶段（1个月内）
- [ ] 为工具模块编写单元测试（目标覆盖率>90%）
- [ ] 为核心业务逻辑编写单元测试（目标覆盖率>60%）
- [ ] 整理现有测试脚本，分类到unit/integration目录

### 第三阶段（3个月内）
- [ ] 集成pytest框架
- [ ] 添加测试覆盖率报告
- [ ] 集成到CI/CD流程（GitHub Actions）
- [ ] 添加性能回归测试

## 运行测试

### 手动运行
```bash
# 运行所有测试（使用pytest）
pytest tests/

# 运行特定测试文件
python tests/test_backend_api.py

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/
```

### 测试覆盖率
```bash
# 安装pytest-cov
pip install pytest-cov

# 生成覆盖率报告
pytest --cov=pydaybar --cov-report=html tests/
```

## 贡献指南

编写测试时请遵循以下规范：

1. **命名规范**
   - 测试文件：`test_<module_name>.py`
   - 测试类：`Test<ClassName>`
   - 测试函数：`test_<function_name>_<scenario>`

2. **目录分类**
   - `unit/` - 单元测试，测试单个函数或类
   - `integration/` - 集成测试，测试多个模块协作
   - `fixtures/` - 测试数据、配置文件、mock对象

3. **断言风格**
   - 使用pytest的`assert`语句
   - 避免使用unittest的`self.assertEqual()`等

4. **测试隔离**
   - 每个测试应该独立运行
   - 使用`@pytest.fixture`管理测试依赖
   - 避免测试之间的数据污染

## 参考资料

- [pytest官方文档](https://docs.pytest.org/)
- [测试最佳实践](https://docs.python-guide.org/writing/tests/)
- [项目测试规范](../docs/testing-guide.md)（待创建）
