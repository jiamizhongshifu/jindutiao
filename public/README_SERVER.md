# 如何在本地测试官网

由于浏览器安全限制,不能直接双击打开 `index.html` 文件测试。
必须通过 HTTP 服务器访问才能正常加载翻译文件。

## 方法1: 使用 Python 内置服务器(最简单)

```bash
# 进入 public 目录
cd c:\Users\Sats\Downloads\jindutiao\public

# 启动服务器(Python 3)
python -m http.server 8000

# 或者 Python 2
python -m SimpleHTTPServer 8000
```

然后在浏览器中访问: `http://localhost:8000`

## 方法2: 使用 Node.js http-server

```bash
# 安装 http-server(仅需一次)
npm install -g http-server

# 进入 public 目录
cd c:\Users\Sats\Downloads\jindutiao\public

# 启动服务器
http-server -p 8000
```

然后在浏览器中访问: `http://localhost:8000`

## 方法3: 使用 VS Code Live Server 插件

1. 在 VS Code 中安装 "Live Server" 插件
2. 右键点击 `index.html`
3. 选择 "Open with Live Server"

## 正式部署

正式部署到生产环境时,请确保:

1. **Nginx 配置示例**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/public;
    index index.html;

    # 确保 JSON 文件正确的 MIME 类型
    location ~* \.json$ {
        add_header Content-Type application/json;
    }

    # SPA 路由支持(如果需要)
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

2. **Apache 配置示例**:
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    DocumentRoot /path/to/public

    <Directory /path/to/public>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    # 确保 JSON 文件正确的 MIME 类型
    AddType application/json .json
</VirtualHost>
```

## 常见问题

### Q: 为什么不能直接双击打开 HTML 文件?
A: 现代浏览器出于安全考虑,限制了 `file://` 协议下的跨文件访问。
   JavaScript 无法加载同目录下的 JSON 文件。

### Q: 我该用哪个方法?
A:
- **开发测试**: Python 内置服务器(最简单,无需安装)
- **频繁开发**: VS Code Live Server(自动刷新很方便)
- **正式部署**: Nginx 或 Apache(性能更好)
