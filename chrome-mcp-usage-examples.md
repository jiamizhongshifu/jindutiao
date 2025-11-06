# Chrome DevTools MCP 使用示例

## ✅ 配置状态

- **Chrome 版本**: 142.0.7444.59
- **调试端口**: 9222 (已启动)
- **MCP 服务器**: chrome-devtools (已连接)
- **当前页面**: https://www.example.com/

## 🚀 在 Claude Code 中使用

现在你可以直接对我说这些话，我会调用 MCP 工具来完成：

### 1. 导航和页面管理

```
"帮我打开 GitHub 主页"
→ 我会调用 navigate_page 工具

"列出所有打开的标签页"
→ 我会调用 list_pages 工具

"打开一个新标签页访问 https://google.com"
→ 我会调用 new_page 工具

"关闭当前标签页"
→ 我会调用 close_page 工具
```

### 2. 截图和调试

```
"给当前页面截个图"
→ 我会调用 take_screenshot 工具

"截取整个页面的长图"
→ 我会调用 take_screenshot (fullPage: true)

"查看页面的控制台消息"
→ 我会调用 list_console_messages 工具

"执行这段 JS: document.title"
→ 我会调用 evaluate_script 工具
```

### 3. 自动化操作

```
"点击页面上的'More information'链接"
→ 我会调用 click 工具

"在搜索框输入 'Hello World'"
→ 我会调用 fill 工具

"填写表单：用户名 admin，密码 123456"
→ 我会调用 fill_form 工具
```

### 4. 网络和性能分析

```
"查看这个页面的所有网络请求"
→ 我会调用 list_network_requests 工具

"开始性能追踪"
→ 我会调用 performance_start_trace 工具

"停止追踪并分析性能"
→ 我会调用 performance_stop_trace + performance_analyze_insight
```

### 5. 设备模拟

```
"模拟移动设备，调整页面大小为 375x667"
→ 我会调用 resize_page 工具

"模拟慢速 3G 网络"
→ 我会调用 emulate_network 工具

"模拟 CPU 降速 4 倍"
→ 我会调用 emulate_cpu 工具
```

## 📋 完整工具列表

### 导航工具 (7个)
1. `navigate_page` - 导航到指定 URL
2. `new_page` - 打开新标签页
3. `list_pages` - 列出所有打开的页面
4. `select_page` - 切换到指定页面
5. `close_page` - 关闭页面
6. `navigate_page_history` - 前进/后退
7. `wait_for` - 等待特定事件

### 输入自动化工具 (7个)
1. `click` - 点击元素
2. `drag` - 拖拽元素
3. `fill` - 填写输入框
4. `fill_form` - 填写表单
5. `handle_dialog` - 处理弹窗
6. `hover` - 鼠标悬停
7. `upload_file` - 上传文件

### 调试工具 (4个)
1. `evaluate_script` - 执行 JavaScript
2. `list_console_messages` - 查看控制台消息
3. `take_screenshot` - 截图
4. `take_snapshot` - 获取 DOM 快照

### 网络工具 (2个)
1. `list_network_requests` - 列出网络请求
2. `get_network_request` - 获取请求详情

### 性能工具 (3个)
1. `performance_start_trace` - 开始性能追踪
2. `performance_stop_trace` - 停止追踪
3. `performance_analyze_insight` - 分析性能洞察

### 模拟工具 (3个)
1. `emulate_cpu` - CPU 节流
2. `emulate_network` - 网络节流
3. `resize_page` - 调整页面大小

## 💡 实用场景示例

### 场景 1：网页调试
```
你："这个网页加载很慢，帮我分析一下"
我：
1. 使用 list_console_messages 检查控制台错误
2. 使用 list_network_requests 查看请求
3. 使用 performance_start_trace 分析性能
4. 给出优化建议
```

### 场景 2：自动化测试
```
你："帮我测试登录功能"
我：
1. 使用 navigate_page 打开登录页
2. 使用 fill_form 填写用户名密码
3. 使用 click 点击登录按钮
4. 使用 wait_for 等待跳转
5. 使用 take_screenshot 截图验证
```

### 场景 3：响应式测试
```
你："测试这个网站在移动设备上的表现"
我：
1. 使用 resize_page 切换到手机尺寸
2. 使用 take_screenshot 截图
3. 使用 evaluate_script 检查布局
4. 对比桌面版和移动版的差异
```

## 🎯 快速测试命令

试试对我说：

1. **"帮我截图���前页面"** - 测试截图功能
2. **"列出所有打开的标签页"** - 测试页面管理
3. **"执行 JS：document.title"** - 测试脚本执行
4. **"打开 https://github.com"** - 测试导航

## 📝 注意事项

1. **Chrome 必须保持运行** - 如果关闭 Chrome，需要重新以调试模式启动
2. **调试端口 9222** - 确保端口未被占用
3. **安全限制** - 某些网站可能有安全限制，无法完全自动化
4. **每次重启** - 重启 Chrome 后需要重新以调试模式启动

## 🔧 重新启动调试模式

如果 Chrome 被关闭了，运行：

```bash
# 方法 1：使用脚本
./start-chrome-debug.bat

# 方法 2：手动命令
taskkill /F /IM chrome.exe
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

验证是否启动成功：

```bash
curl http://localhost:9222/json/version
```

---

**配置完成时间**: $(date)
**Chrome 版本**: 142.0.7444.59
**状态**: ✅ 已就绪
