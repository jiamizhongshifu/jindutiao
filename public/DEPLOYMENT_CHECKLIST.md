# 🚀 GaiYa 官网部署检查清单

当语言切换功能不工作时,按以下步骤排查:

## ✅ 步骤 1: 确认文件已上传

SSH 登录到服务器,检查文件是否存在:

```bash
# 进入网站目录
cd /var/www/gaiya.cloud/public  # 根据实际路径调整

# 检查 locales 目录
ls -la locales/

# 应该看到:
# -rw-r--r-- 1 www-data www-data 18316 ... zh_CN.json
# -rw-r--r-- 1 www-data www-data 19140 ... en_US.json
```

**如果文件不存在**: 上传 `public/locales/` 目录到服务器

## ✅ 步骤 2: 检查文件权限

```bash
# 确保 Web 服务器有读取权限
chmod 644 locales/*.json
chown www-data:www-data locales/*.json  # Ubuntu/Debian
# 或
chown nginx:nginx locales/*.json        # CentOS/RHEL
```

## ✅ 步骤 3: 测试文件是否可访问

在浏览器中直接访问:

- https://gaiya.cloud/locales/zh_CN.json
- https://gaiya.cloud/locales/en_US.json

**预期结果**: 应该看到 JSON 内容,而不是 404 错误

**如果还是 404**: 继续下一步

## ✅ 步骤 4: 检查 Web 服务器配置

### 如果使用 Nginx:

```bash
# 检查 Nginx 配置
nginx -t

# 查看当前站点配置
cat /etc/nginx/sites-available/gaiya.cloud

# 应该包含类似配置:
# location /locales/ {
#     try_files $uri =404;
#     add_header Content-Type application/json;
# }
```

如果没有上述配置,参考 `nginx.conf.example` 添加配置,然后:

```bash
# 重新加载 Nginx
sudo systemctl reload nginx
```

### 如果使用 Apache:

```bash
# 检查 .htaccess 文件是否上传
ls -la /var/www/gaiya.cloud/public/.htaccess

# 确保 Apache 允许 .htaccess 覆盖
# 检查 /etc/apache2/sites-available/gaiya.cloud.conf
# 应该包含: AllowOverride All
```

如果没有 `.htaccess`,参考 `.htaccess.example` 创建文件,然后:

```bash
# 重新加载 Apache
sudo systemctl reload apache2
```

## ✅ 步骤 5: 浏览器缓存清除

有时浏览器会缓存 404 响应:

1. 打开浏览器开发者工具 (F12)
2. 右键点击刷新按钮
3. 选择 "清空缓存并硬性重新加载"

或者使用隐私模式/无痕模式重新访问

## ✅ 步骤 6: 检查 CDN 缓存(如果使用)

如果你的网站使用了 CDN(如 Cloudflare、阿里云 CDN):

1. 登录 CDN 控制台
2. 清除 `/locales/*.json` 的缓存
3. 等待 5-10 分钟后重试

## ✅ 步骤 7: 查看服务器错误日志

```bash
# Nginx 错误日志
tail -f /var/log/nginx/error.log

# Apache 错误日志
tail -f /var/log/apache2/error.log

# 然后在浏览器中访问网站,查看日志输出
```

## 🎯 快速验证方法

在浏览器控制台执行以下命令:

```javascript
// 测试翻译文件是否可加载
fetch('/locales/zh_CN.json')
  .then(r => r.json())
  .then(d => console.log('✅ 中文翻译加载成功:', d))
  .catch(e => console.error('❌ 中文翻译加载失败:', e))

fetch('/locales/en_US.json')
  .then(r => r.json())
  .then(d => console.log('✅ 英文翻译加载成功:', d))
  .catch(e => console.error('❌ 英文翻译加载失败:', e))
```

## 📞 仍然无法解决?

如果以上步骤都完成了还是不行,请提供以下信息:

1. Web 服务器类型和版本 (Nginx/Apache/其他)
2. 操作系统版本
3. 网站目录结构截图
4. Nginx/Apache 配置文件内容
5. 浏览器控制台完整错误信息
6. 服务器错误日志

---

## 🎉 成功标志

当一切正常时,你应该看到:

1. **浏览器控制台**:
   ```
   [i18n] Loaded translations for zh_CN
   [i18n] Initialized with locale: zh_CN
   ```

2. **Network 标签**:
   - `/locales/zh_CN.json` - 状态码 200
   - `/locales/en_US.json` - 状态码 200

3. **语言切换**:
   - 点击语言按钮后页面自动刷新
   - 所有文本切换到对应语言
   - 没有 "Missing translation" 警告
