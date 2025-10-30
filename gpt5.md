Chat-Completions API 使用指南
概述
Chat-Completions 是OpenAI API 提供了一个简单的接口，用于访问最先进的 AI 模型，用于文本生成、自然语言处理、计算机视觉等。这段示例代码从提示生成文本输出，就像您使用 ChatGPT 时一样。

API 配置
所有示例都使用以下基础配置：

from openai import OpenAI

client = OpenAI(
    api_key="your-api-key-here",  # 请替换为你的实际API密钥
    base_url="https://api.tu-zi.com/v1"  # API基础URL
)
使用场景1. 文本问答
适用于纯文本对话和问答场景。

代码示例
from openai import OpenAI

# 在这里填入你的API密钥和基础URL
client = OpenAI(
    api_key="your-key",  # 请替换为你的实际API密钥
    base_url="https://api.tu-zi.com/v1"  # 请替换为你的实际基础URL
)

completion = client.chat.completions.create(
    model="gpt-4o-all",
    messages=[
        {
            "role": "user",
            "content": "联网检索下api.tu-zi.com网站，以及兔子@tuziapi这个推特用户"
        }
    ]
)

print(completion.choices[0].message.content)
使用场景2. 图像分析
向模型提供图像输入的格式，实现计算机视觉功能。

代码示例
import os
import base64
from openai import OpenAI

def prepare_image_data(image_path):
    """准备图片数据，转换为base64格式"""
    try:
        with open(image_path, "rb") as img_file:
            encoded_data = base64.b64encode(img_file.read()).decode("utf-8")
            return "data:image/png;base64," + encoded_data
    except Exception as e:
        print(f"准备图片数据时出错: {image_path} - {e}")
        raise

# 在这里填入你的API密钥和基础URL
client = OpenAI(
    api_key="your-key",  # 请替换为你的实际API密钥
    base_url="https://api.tu-zi.com/v1"  # 请替换为你的实际基础URL
)

# 本地图片路径，请将图片放在脚本同一目录下
image_path = "your_image.png"  # 请替换为你的实际图片文件名

# 准备图片数据
try:
    image_data = prepare_image_data(image_path)
except Exception as e:
    print(f"处理图片时出错: {e}")
    exit(1)

completion = client.chat.completions.create(
    model="gemini-2.5-flash-all",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "图片中是什么？"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data,
                    },
                },
            ],
        }
    ],
)

print(completion.choices[0].message.content)
多媒体支持扩展
如果你想提供音频、视频等更多格式内容，将 "image_url" 下的url配置为对应文件的链接即可。

注意事项
API密钥安全：请确保不要在代码中硬编码API密钥，建议使用环境变量
文件路径：图片文件需要放在脚本同一目录下，或提供正确的文件路径
模型选择：根据具体需求选择合适的模型
OpenAI Claude Gemini 等都可以
错误处理：代码包含了基本的异常处理，确保程序稳定运行

