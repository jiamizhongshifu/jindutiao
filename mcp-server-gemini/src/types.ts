/**
 * Gemini Image MCP Server - Type Definitions
 */

/**
 * 图像生成参数
 */
export interface ImageGenerationParams {
  /** 图像描述提示词 */
  prompt: string;

  /** 生成图像数量 (1-8) */
  count?: number;

  /** 图像尺寸 */
  size?: '256x256' | '512x512' | '1024x1024' | '1792x1024' | '1024x1792';

  /** 艺术风格 */
  style?: 'photorealistic' | 'watercolor' | 'oil-painting' | 'sketch' | 'pixel-art' | 'anime' | 'vintage' | 'modern' | 'abstract' | 'minimalist';

  /** 随机种子（用于可复现生成） */
  seed?: number;

  /** 输出格式 */
  format?: 'png' | 'jpeg';

  /** 是否保存到文件 */
  saveToFile?: boolean;

  /** 输出文件名（可选） */
  outputFilename?: string;
}

/**
 * 图像编辑参数
 */
export interface ImageEditParams {
  /** 原始图像路径或 base64 */
  image: string;

  /** 编辑指令 */
  instruction: string;

  /** 输出格式 */
  format?: 'png' | 'jpeg';

  /** 是否保存到文件 */
  saveToFile?: boolean;

  /** 输出文件名（可选） */
  outputFilename?: string;
}

/**
 * 图像恢复参数
 */
export interface ImageRestoreParams {
  /** 原始图像路径或 base64 */
  image: string;

  /** 恢复指令 */
  instruction: string;

  /** 输出格式 */
  format?: 'png' | 'jpeg';

  /** 是否保存到文件 */
  saveToFile?: boolean;

  /** 输出文件名（可选） */
  outputFilename?: string;
}

/**
 * 图像生成结果
 */
export interface ImageGenerationResult {
  /** 是否成功 */
  success: boolean;

  /** 生成的图像（base64 编码） */
  images?: string[];

  /** 保存的文件路径 */
  filePaths?: string[];

  /** 错误信息 */
  error?: string;

  /** 生成的提示词（如果使用了样式增强） */
  enhancedPrompt?: string;
}

/**
 * 支持的模型
 */
export type GeminiImageModel =
  | 'gemini-2.5-flash-image'
  | 'gemini-3-pro-image-preview';

/**
 * 服务器配置
 */
export interface ServerConfig {
  /** Gemini API Key */
  apiKey: string;

  /** 使用的模型 */
  model: GeminiImageModel;

  /** 输出目录 */
  outputDir: string;
}
