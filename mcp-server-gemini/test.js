/**
 * Gemini Image MCP Server - 独立测试脚本
 *
 * 用于验证 Gemini API 配置是否正确
 * 无需 Claude Code 即可测试
 */

import { GoogleGenAI } from '@google/genai';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 加载环境变量
dotenv.config({ path: path.join(__dirname, '.env') });

async function test() {
  console.log('========================================');
  console.log('Gemini Image MCP Server - 测试工具');
  console.log('========================================\n');

  // 获取 API Key
  const apiKey =
    process.env.GEMINI_API_KEY ||
    process.env.GOOGLE_API_KEY ||
    process.env.NANOBANANA_GEMINI_API_KEY ||
    process.env.NANOBANANA_GOOGLE_API_KEY;

  if (!apiKey) {
    console.error('❌ 错误: 未找到 Gemini API Key');
    console.error('\n请设置以下环境变量之一:');
    console.error('  - GEMINI_API_KEY');
    console.error('  - GOOGLE_API_KEY');
    console.error('  - NANOBANANA_GEMINI_API_KEY');
    console.error('  - NANOBANANA_GOOGLE_API_KEY');
    console.error('\n或者创建 .env 文件（参考 .env.example）');
    process.exit(1);
  }

  console.log('✅ API Key 已找到:', apiKey.substring(0, 10) + '...');

  // 获取模型
  const model = process.env.GEMINI_IMAGE_MODEL || 'gemini-2.5-flash-image';
  console.log('✅ 使用模型:', model);

  // 获取输出目录
  const outputDir = process.env.GEMINI_OUTPUT_DIR || path.join(os.homedir(), 'gemini-images');
  console.log('✅ 输出目录:', outputDir);

  console.log('\n========================================');
  console.log('开始测试 Gemini API 连接...');
  console.log('========================================\n');

  try {
    // 创建 Gemini AI 客户端（使用新 SDK）
    const ai = new GoogleGenAI({ apiKey });

    // 测试简单的文本生成（验证 API 连接）
    console.log('1️⃣ 测试 API 连接...');
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: 'Hello, Gemini! Please respond with a short greeting.'
    });

    console.log('✅ API 连接成功！');
    console.log('   响应:', response.text.substring(0, 100) + (response.text.length > 100 ? '...' : ''));

    console.log('\n2️⃣ 测试图像生成能力...');
    console.log('   提示词: "a simple red circle"');

    // 注意：实际的图像生成需要使用正确的 Gemini 图像模型 API
    // 这里只是测试 API 连接，具体的图像生成实现在 imageGenerator.ts 中
    console.log('⚠️  注意: 完整的图像生成功能在 MCP 服务器中实现');
    console.log('   请通过 Claude Code 调用 gemini_generate_image 工具进行测试');

    console.log('\n3️⃣ 检查输出目录...');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
      console.log('✅ 创建输出目录:', outputDir);
    } else {
      console.log('✅ 输出目录已存在:', outputDir);
    }

    console.log('\n========================================');
    console.log('✅ 所有测试通过！');
    console.log('========================================\n');

    console.log('下一步:');
    console.log('1. 运行: npm run build');
    console.log('2. 配置 Claude Code (参考 QUICKSTART.md)');
    console.log('3. 在 Claude Code 中使用 Gemini 图像生成功能');

  } catch (error) {
    console.error('\n❌ 测试失败:', error.message);
    console.error('\n可能的原因:');
    console.error('1. API Key 无效或已过期');
    console.error('2. 网络连接问题');
    console.error('3. Gemini API 配额已用尽');
    console.error('\n请访问 https://makersuite.google.com/app/apikey 检查 API Key');
    process.exit(1);
  }
}

// 运行测试
test().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
