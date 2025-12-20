/**
 * Gemini Image Generator
 * 处理所有 Gemini API 图像生成相关的调用
 */

import { GoogleGenAI } from '@google/genai';
import * as fs from 'fs/promises';
import * as path from 'path';
import {
  ImageGenerationParams,
  ImageEditParams,
  ImageRestoreParams,
  ImageGenerationResult,
  ServerConfig
} from './types.js';

export class GeminiImageGenerator {
  private genAI: GoogleGenAI;
  private config: ServerConfig;

  constructor(config: ServerConfig) {
    this.config = config;
    this.genAI = new GoogleGenAI({ apiKey: config.apiKey });
  }

  /**
   * 生成图像
   */
  async generateImage(params: ImageGenerationParams): Promise<ImageGenerationResult> {
    try {
      const {
        prompt,
        count = 1,
        size = '1024x1024',
        style,
        seed,
        format = 'png',
        saveToFile = true,
        outputFilename
      } = params;

      // 构建增强的提示词
      const enhancedPrompt = this.buildEnhancedPrompt(prompt, style, size);

      console.error(`[Gemini Image] Generating ${count} image(s) with prompt: ${enhancedPrompt.substring(0, 100)}...`);

      // 调用 Gemini API 生成图像
      const images: string[] = [];
      const filePaths: string[] = [];

      for (let i = 0; i < count; i++) {
        // 添加随机种子到提示词（如果提供）
        const finalPrompt = seed ? `${enhancedPrompt} [seed: ${seed + i}]` : enhancedPrompt;

        // 生成图像（使用新 SDK）
        const response = await this.genAI.models.generateContent({
          model: this.config.model,
          contents: [{ role: 'user', parts: [{ text: finalPrompt }] }],
        });

        const imageData = this.extractImageData(response);

        if (imageData) {
          images.push(imageData);

          // 保存到文件
          if (saveToFile) {
            const filename = outputFilename
              ? `${path.parse(outputFilename).name}_${i + 1}.${format}`
              : this.generateFilename(prompt, i + 1, format);

            const filePath = await this.saveImage(imageData, filename);
            filePaths.push(filePath);
            console.error(`[Gemini Image] Saved: ${filePath}`);
          }
        }
      }

      return {
        success: true,
        images,
        filePaths: saveToFile ? filePaths : undefined,
        enhancedPrompt
      };
    } catch (error) {
      console.error('[Gemini Image] Generation error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * 编辑图像
   */
  async editImage(params: ImageEditParams): Promise<ImageGenerationResult> {
    try {
      const {
        image,
        instruction,
        format = 'png',
        saveToFile = true,
        outputFilename
      } = params;

      console.error(`[Gemini Image] Editing image with instruction: ${instruction}`);

      // 读取图像数据
      const imageData = await this.loadImageData(image);

      // 调用 Gemini API 编辑图像（使用新 SDK）
      const prompt = `Edit this image: ${instruction}. Maintain the original style and quality.`;

      const response = await this.genAI.models.generateContent({
        model: this.config.model,
        contents: [{
          role: 'user',
          parts: [
            { inlineData: { mimeType: 'image/png', data: imageData } },
            { text: prompt }
          ]
        }]
      });

      const editedImageData = this.extractImageData(response);

      if (!editedImageData) {
        throw new Error('Failed to extract edited image from response');
      }

      let filePath: string | undefined;
      if (saveToFile) {
        const filename = outputFilename || this.generateFilename(`edited_${instruction}`, 1, format);
        filePath = await this.saveImage(editedImageData, filename);
        console.error(`[Gemini Image] Saved edited image: ${filePath}`);
      }

      return {
        success: true,
        images: [editedImageData],
        filePaths: filePath ? [filePath] : undefined
      };
    } catch (error) {
      console.error('[Gemini Image] Edit error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * 恢复图像
   */
  async restoreImage(params: ImageRestoreParams): Promise<ImageGenerationResult> {
    try {
      const {
        image,
        instruction,
        format = 'png',
        saveToFile = true,
        outputFilename
      } = params;

      console.error(`[Gemini Image] Restoring image with instruction: ${instruction}`);

      // 读取图像数据
      const imageData = await this.loadImageData(image);

      // 调用 Gemini API 恢复图像（使用新 SDK）
      const prompt = `Restore and enhance this image: ${instruction}. Fix any damage, improve clarity, and enhance quality while preserving the original content and style.`;

      const response = await this.genAI.models.generateContent({
        model: this.config.model,
        contents: [{
          role: 'user',
          parts: [
            { inlineData: { mimeType: 'image/png', data: imageData } },
            { text: prompt }
          ]
        }]
      });

      const restoredImageData = this.extractImageData(response);

      if (!restoredImageData) {
        throw new Error('Failed to extract restored image from response');
      }

      let filePath: string | undefined;
      if (saveToFile) {
        const filename = outputFilename || this.generateFilename(`restored_${instruction}`, 1, format);
        filePath = await this.saveImage(restoredImageData, filename);
        console.error(`[Gemini Image] Saved restored image: ${filePath}`);
      }

      return {
        success: true,
        images: [restoredImageData],
        filePaths: filePath ? [filePath] : undefined
      };
    } catch (error) {
      console.error('[Gemini Image] Restore error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * 构建增强的提示词
   */
  private buildEnhancedPrompt(prompt: string, style?: string, size?: string): string {
    let enhanced = prompt;

    // 添加样式指令
    if (style) {
      const styleInstructions: Record<string, string> = {
        'photorealistic': 'photorealistic, high detail, professional photography',
        'watercolor': 'watercolor painting style, soft colors, artistic',
        'oil-painting': 'oil painting style, rich textures, classic art',
        'sketch': 'hand-drawn sketch, pencil art, artistic lines',
        'pixel-art': 'pixel art style, retro gaming aesthetic, 8-bit',
        'anime': 'anime art style, manga inspired, vibrant colors',
        'vintage': 'vintage aesthetic, retro style, aged look',
        'modern': 'modern contemporary style, clean design',
        'abstract': 'abstract art style, creative interpretation',
        'minimalist': 'minimalist design, clean, simple, elegant'
      };

      const styleInstruction = styleInstructions[style];
      if (styleInstruction) {
        enhanced = `${enhanced}, ${styleInstruction}`;
      }
    }

    // 添加尺寸指令
    if (size) {
      enhanced = `${enhanced}, image size: ${size}`;
    }

    // 添加通用质量指令
    enhanced = `${enhanced}, high quality, detailed, professional`;

    return enhanced;
  }

  /**
   * 从响应中提取图像数据
   */
  private extractImageData(response: any): string | null {
    try {
      // Gemini API 返回的图像数据格式可能不同，需要根据实际情况调整
      // 这里假设图像数据在 response 的某个字段中
      const candidates = response.candidates;
      if (candidates && candidates.length > 0) {
        const content = candidates[0].content;
        if (content && content.parts) {
          for (const part of content.parts) {
            if (part.inlineData && part.inlineData.data) {
              return part.inlineData.data;
            }
          }
        }
      }

      // 如果没有找到图像数据，返回 null
      console.error('[Gemini Image] No image data found in response');
      return null;
    } catch (error) {
      console.error('[Gemini Image] Error extracting image data:', error);
      return null;
    }
  }

  /**
   * 加载图像数据
   */
  private async loadImageData(imagePath: string): Promise<string> {
    // 如果已经是 base64，直接返回
    if (imagePath.startsWith('data:') || imagePath.length > 1000) {
      // 提取 base64 部分
      const base64Match = imagePath.match(/base64,(.+)/);
      return base64Match ? base64Match[1] : imagePath;
    }

    // 否则从文件读取
    const buffer = await fs.readFile(imagePath);
    return buffer.toString('base64');
  }

  /**
   * 保存图像到文件
   */
  private async saveImage(base64Data: string, filename: string): Promise<string> {
    // 确保输出目录存在
    await fs.mkdir(this.config.outputDir, { recursive: true });

    const filePath = path.join(this.config.outputDir, filename);
    const buffer = Buffer.from(base64Data, 'base64');

    await fs.writeFile(filePath, buffer);

    return filePath;
  }

  /**
   * 生成文件名
   */
  private generateFilename(prompt: string, index: number, format: string): string {
    // 清理提示词作为文件名
    const cleanPrompt = prompt
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, '')
      .replace(/\s+/g, '_')
      .substring(0, 50);

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];

    return `gemini_${cleanPrompt}_${timestamp}_${index}.${format}`;
  }
}
