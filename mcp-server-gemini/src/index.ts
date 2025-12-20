#!/usr/bin/env node

/**
 * Gemini Image MCP Server
 * 桥接 Gemini 图像生成 API 到 Claude Code
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { GeminiImageGenerator } from './imageGenerator.js';
import type {
  ImageGenerationParams,
  ImageEditParams,
  ImageRestoreParams,
  ServerConfig,
  GeminiImageModel
} from './types.js';
import * as path from 'path';
import * as os from 'os';

/**
 * 获取配置
 */
function getConfig(): ServerConfig {
  const apiKey =
    process.env.GEMINI_API_KEY ||
    process.env.GOOGLE_API_KEY ||
    process.env.NANOBANANA_GEMINI_API_KEY ||
    process.env.NANOBANANA_GOOGLE_API_KEY;

  if (!apiKey) {
    throw new Error(
      'Gemini API key not found. Please set one of: GEMINI_API_KEY, GOOGLE_API_KEY, NANOBANANA_GEMINI_API_KEY, or NANOBANANA_GOOGLE_API_KEY'
    );
  }

  const model = (process.env.GEMINI_IMAGE_MODEL || 'gemini-2.5-flash-image') as GeminiImageModel;
  const outputDir = process.env.GEMINI_OUTPUT_DIR || path.join(os.homedir(), 'gemini-images');

  return {
    apiKey,
    model,
    outputDir
  };
}

/**
 * 创建 MCP 服务器
 */
async function main() {
  console.error('[Gemini MCP Server] Starting...');

  // 获取配置
  const config = getConfig();
  console.error(`[Gemini MCP Server] Using model: ${config.model}`);
  console.error(`[Gemini MCP Server] Output directory: ${config.outputDir}`);

  // 创建图像生成器
  const imageGenerator = new GeminiImageGenerator(config);

  // 创建 MCP 服务器
  const server = new Server(
    {
      name: 'gemini-image-server',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  /**
   * 列出可用工具
   */
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: 'gemini_generate_image',
          description: 'Generate images using Gemini AI based on text prompts. Supports multiple styles, sizes, and variations.',
          inputSchema: {
            type: 'object',
            properties: {
              prompt: {
                type: 'string',
                description: 'The text prompt describing the image to generate'
              },
              count: {
                type: 'number',
                description: 'Number of images to generate (1-8)',
                minimum: 1,
                maximum: 8,
                default: 1
              },
              size: {
                type: 'string',
                description: 'Image size',
                enum: ['256x256', '512x512', '1024x1024', '1792x1024', '1024x1792'],
                default: '1024x1024'
              },
              style: {
                type: 'string',
                description: 'Artistic style for the image',
                enum: [
                  'photorealistic',
                  'watercolor',
                  'oil-painting',
                  'sketch',
                  'pixel-art',
                  'anime',
                  'vintage',
                  'modern',
                  'abstract',
                  'minimalist'
                ]
              },
              seed: {
                type: 'number',
                description: 'Random seed for reproducible generation'
              },
              format: {
                type: 'string',
                description: 'Output image format',
                enum: ['png', 'jpeg'],
                default: 'png'
              },
              saveToFile: {
                type: 'boolean',
                description: 'Whether to save images to files',
                default: true
              },
              outputFilename: {
                type: 'string',
                description: 'Custom output filename (optional)'
              }
            },
            required: ['prompt']
          }
        },
        {
          name: 'gemini_edit_image',
          description: 'Edit an existing image using Gemini AI based on natural language instructions.',
          inputSchema: {
            type: 'object',
            properties: {
              image: {
                type: 'string',
                description: 'Path to the image file or base64 encoded image data'
              },
              instruction: {
                type: 'string',
                description: 'The editing instruction (e.g., "add sunglasses to the person")'
              },
              format: {
                type: 'string',
                description: 'Output image format',
                enum: ['png', 'jpeg'],
                default: 'png'
              },
              saveToFile: {
                type: 'boolean',
                description: 'Whether to save the edited image to a file',
                default: true
              },
              outputFilename: {
                type: 'string',
                description: 'Custom output filename (optional)'
              }
            },
            required: ['image', 'instruction']
          }
        },
        {
          name: 'gemini_restore_image',
          description: 'Restore and enhance old or damaged images using Gemini AI.',
          inputSchema: {
            type: 'object',
            properties: {
              image: {
                type: 'string',
                description: 'Path to the image file or base64 encoded image data'
              },
              instruction: {
                type: 'string',
                description: 'Restoration instruction (e.g., "remove scratches and improve clarity")'
              },
              format: {
                type: 'string',
                description: 'Output image format',
                enum: ['png', 'jpeg'],
                default: 'png'
              },
              saveToFile: {
                type: 'boolean',
                description: 'Whether to save the restored image to a file',
                default: true
              },
              outputFilename: {
                type: 'string',
                description: 'Custom output filename (optional)'
              }
            },
            required: ['image', 'instruction']
          }
        }
      ]
    };
  });

  /**
   * 处理工具调用
   */
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      switch (name) {
        case 'gemini_generate_image': {
          const params = args as unknown as ImageGenerationParams;
          const result = await imageGenerator.generateImage(params);

          if (!result.success) {
            throw new Error(result.error);
          }

          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({
                  message: `Successfully generated ${result.images?.length || 0} image(s)`,
                  filePaths: result.filePaths,
                  enhancedPrompt: result.enhancedPrompt
                }, null, 2)
              }
            ]
          };
        }

        case 'gemini_edit_image': {
          const params = args as unknown as ImageEditParams;
          const result = await imageGenerator.editImage(params);

          if (!result.success) {
            throw new Error(result.error);
          }

          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({
                  message: 'Successfully edited image',
                  filePaths: result.filePaths
                }, null, 2)
              }
            ]
          };
        }

        case 'gemini_restore_image': {
          const params = args as unknown as ImageRestoreParams;
          const result = await imageGenerator.restoreImage(params);

          if (!result.success) {
            throw new Error(result.error);
          }

          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({
                  message: 'Successfully restored image',
                  filePaths: result.filePaths
                }, null, 2)
              }
            ]
          };
        }

        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      console.error(`[Gemini MCP Server] Error handling tool ${name}:`, error);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              error: error instanceof Error ? error.message : String(error)
            }, null, 2)
          }
        ],
        isError: true
      };
    }
  });

  /**
   * 启动服务器
   */
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('[Gemini MCP Server] Server started successfully');
}

// 启动服务器
main().catch((error) => {
  console.error('[Gemini MCP Server] Fatal error:', error);
  process.exit(1);
});
