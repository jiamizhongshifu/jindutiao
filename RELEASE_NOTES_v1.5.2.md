# GaiYa v1.5.2 - 会员合伙人计划升级 🎯

## 🎯 限量发售策略

**会员合伙人计划重磅升级！**

- 💎 **限量1000名** - ¥1200，一次购买，终身使用
- ✨ **深金色限量标签** - 强调稀缺性与高级定位
- 🤝 **共享价值** - 与我们一起成长，见证项目发展

## 💰 当前定价体系

| 套餐 | 价格 | 权益 |
|------|------|------|
| **月度会员** | ¥29/月 | 20次/天AI配额 |
| **年度会员** | ¥199/年 | 相当于16.6元/月，年省149元 |
| **会员合伙人** | ¥1200 | 限量1000名，九大专属权益 |

## 🤝 会员合伙人九大权益

1. ✅ 无限AI任务生成配额
2. ✅ 去除进度条水印
3. ✅ 完整数据统计报告
4. ✅ 专属会员合伙人社群
5. ✅ 33%引荐返现奖励
6. ✅ 优先体验新功能
7. ✅ 专属1v1咨询服务
8. ✅ 共同成长分享价值
9. ✅ 终身免费更新

## 🎨 UI 增强

- **限量标签实现** - 会员合伙人卡片添加"限量1000名"深金色标签
- **视觉优化** - 标题与标签居中对齐，突出稀缺性

## 🌐 开源准备

本版本完善了开源必备文档，为正式开源发布做好准备：

- ✅ 创建 CODE_OF_CONDUCT.md（贡献者公约行为准则）
- ✅ 添加 GitHub Issue 模板（Bug报告、功能请求）
- ✅ 添加 Pull Request 模板
- ✅ 创建 FUNDING.yml 赞助配置
- ✅ 增强 README.md（徽章、开源优势说明）
- ✅ 优化 .gitignore

## 📚 文档更新

- **README.md 全面升级**
  - 添加"为什么选择 GaiYa"部分
  - 添加"支持我们"部分
  - 增强徽章显示（Stars、Forks、Issues、PRs Welcome）
  - 更新会员系统价格说明

- **CHANGELOG.md 完善**
  - 详细记录 v1.5.2 所有变更
  - 清晰的分类和说明

## 🔧 技术改进

- **价格同步** - 前后端价格完全同步（4个文件）
  - config_gui.py（前端）
  - api/zpay_manager.py（支付管理）
  - api/subscription_manager.py（订阅管理）
  - api/validators.py（价格验证）

## 📥 下载说明

**Windows 用户**：
1. 下载 `GaiYa-v1.5.exe`（约62MB）
2. 双击运行即可

**从源码运行**：
```bash
git clone https://github.com/jiamizhongshifu/jindutiao.git
cd jindutiao
pip install -r requirements.txt
python main.py
```

## ⚠️ 重要提醒

- **杀毒软件可能误报**：这是 PyInstaller 打包应用的常见问题，请添加信任。详见 [SECURITY.md](https://github.com/jiamizhongshifu/jindutiao/blob/main/SECURITY.md)
- **完全开源**：所有代码公开审计，安全透明
- **数据本地**：配置文件存储在本地，隐私有保障

## 🔗 相关链接

- 📖 [完整文档](https://github.com/jiamizhongshifu/jindutiao#readme)
- 🐛 [报告问题](https://github.com/jiamizhongshifu/jindutiao/issues)
- 💬 [讨论区](https://github.com/jiamizhongshifu/jindutiao/discussions)
- 🤝 [贡献指南](https://github.com/jiamizhongshifu/jindutiao/blob/main/CONTRIBUTING.md)

---

⭐ **如果 GaiYa 对您有帮助，请给我们一个 Star！** ⭐
