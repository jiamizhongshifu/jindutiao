# GaiYa 快速开发指南

## 🚀 打包脚本(已优化)

项目现在只保留**三个优化的打包脚本**,旧脚本已移至 `.old_build_scripts/` 备份。

### 📦 推荐使用顺序

```
日常开发: build-fast.bat ⭐
    ↓ (如果失败)
遇到问题: build-clean.bat
    ↓ (如果还失败)
带验证的: build-smart.bat
```

---

## 🎯 核心原则

1. **日常开发**: 使用 `build-fast.bat` (自动检测,极速打包)
2. **遇到问题**: 使用 `build-clean.bat` (完全清理)
3. **打包卡死**: 使用 `build-smart.bat` (带重试机制)
4. **速度提升**: 使用缓存时可提升 **70-87%** 🎉

详细说明请查看 [BUILD_GUIDE.md](BUILD_GUIDE.md)

**祝开发顺利!** 🚀
