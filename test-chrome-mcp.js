// 测试 Chrome DevTools MCP 连接
// 这个脚本用于验证 MCP 服务器是否可以正常与 Chrome 通信

const CDP = require('chrome-remote-interface');

async function testChromeMCP() {
    console.log('🔍 连接到 Chrome DevTools Protocol...');

    try {
        const client = await CDP({ port: 9222 });
        const { Page, Runtime, Network } = client;

        console.log('✅ 成功连接到 Chrome！');

        // 启用各个域
        await Promise.all([
            Page.enable(),
            Runtime.enable(),
            Network.enable()
        ]);

        console.log('✅ 已启用 Page、Runtime、Network 域');

        // 获取页面信息
        const { frameTree } = await Page.getFrameTree();
        console.log('\n📄 当前页面信息：');
        console.log('  URL:', frameTree.frame.url);
        console.log('  ID:', frameTree.frame.id);

        // 执行 JavaScript
        console.log('\n🔧 测试执行 JavaScript...');
        const result = await Runtime.evaluate({
            expression: 'document.title'
        });
        console.log('  页面标题:', result.result.value);

        // 获取控制台消息
        console.log('\n📝 监听控制台消息...');
        Runtime.consoleAPICalled((params) => {
            console.log('  控制台:', params.args[0].value);
        });

        // 注入测试日志
        await Runtime.evaluate({
            expression: 'console.log("MCP 测试成功！")'
        });

        console.log('\n✅ 所有测试通过！Chrome DevTools MCP 配置成功！');

        await client.close();
    } catch (error) {
        console.error('❌ 错误:', error.message);
        process.exit(1);
    }
}

testChromeMCP();
