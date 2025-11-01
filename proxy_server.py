# -*- coding: utf-8 -*-
"""
PyDayBar API代理服务器
部署在Railway或其他免费平台上，保护API密钥安全
"""
import os
import sys
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime
from typing import Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# API配置（从环境变量读取）
TUZI_API_KEY = os.getenv("TUZI_API_KEY")
TUZI_BASE_URL = os.getenv("TUZI_BASE_URL", "https://api.tu-zi.com/v1")

if not TUZI_API_KEY:
    logger.error("未找到TUZI_API_KEY环境变量，请设置环境变量")
    # 生产环境应该退出，但这里允许继续运行（用于测试）

# 简单的请求限流（内存存储，生产环境应使用Redis）
request_counts = {}
MAX_REQUESTS_PER_HOUR = 100  # 每小时最大请求数


def check_rate_limit(ip: str) -> bool:
    """检查请求频率限制"""
    current_hour = datetime.now().strftime("%Y-%m-%d-%H")
    key = f"{ip}:{current_hour}"
    
    if key not in request_counts:
        request_counts[key] = 0
    
    request_counts[key] += 1
    
    if request_counts[key] > MAX_REQUESTS_PER_HOUR:
        logger.warning(f"IP {ip} 超过请求限制: {request_counts[key]}")
        return False
    
    return True


@app.route('/health', methods=['GET'])
def health():
    """健康检查端点"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "PyDayBar API Proxy"
    })


@app.route('/api/plan-tasks', methods=['POST'])
def proxy_plan_tasks():
    """代理任务规划请求"""
    if not TUZI_API_KEY:
        return jsonify({"error": "API密钥未配置"}), 500
    
    # 检查请求频率
    client_ip = request.remote_addr
    if not check_rate_limit(client_ip):
        return jsonify({
            "error": "请求过于频繁，请稍后再试"
        }), 429
    
    try:
        # 获取用户请求数据
        user_data = request.json
        if not user_data:
            return jsonify({"error": "请求数据为空"}), 400
        
        logger.info(f"收到任务规划请求，IP: {client_ip}")
        
        # 构造API请求 - 使用OpenAI格式
        api_url = f"{TUZI_BASE_URL}/chat/completions"
        
        # 构造请求体（OpenAI格式）
        api_request_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个任务规划助手，帮助用户将自然语言描述转换为结构化的任务列表。"
                },
                {
                    "role": "user",
                    "content": user_data.get("input", "")
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        # 转发请求到真实API
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {TUZI_API_KEY}",
                "Content-Type": "application/json"
            },
            json=api_request_body,
            timeout=60  # AI请求可能需要较长时间
        )
        
        # 记录响应状态
        logger.info(f"API响应状态: {response.status_code}")
        
        if response.status_code == 200:
            # 解析响应并转换为PyDayBar格式
            api_response = response.json()
            # 这里需要根据实际API响应格式进行解析
            # 简化处理：返回原始响应
            return jsonify({
                "success": True,
                "tasks": [],  # 实际应该解析AI响应
                "quota_info": {
                    "remaining": {"daily_plan": 2},
                    "user_tier": user_data.get("user_tier", "free")
                }
            }), 200
        else:
            logger.error(f"API请求失败: {response.status_code}, {response.text}")
            return jsonify({
                "error": "API请求失败",
                "details": response.text[:200]
            }), response.status_code
            
    except requests.exceptions.Timeout:
        logger.error("API请求超时")
        return jsonify({"error": "请求超时，请稍后再试"}), 504
    except Exception as e:
        logger.error(f"代理请求失败: {e}", exc_info=True)
        return jsonify({
            "error": "服务器内部错误",
            "details": str(e)
        }), 500


@app.route('/api/generate-weekly-report', methods=['POST'])
def proxy_generate_weekly_report():
    """代理周报生成请求"""
    if not TUZI_API_KEY:
        return jsonify({"error": "API密钥未配置"}), 500
    
    # 检查请求频率
    client_ip = request.remote_addr
    if not check_rate_limit(client_ip):
        return jsonify({
            "error": "请求过于频繁，请稍后再试"
        }), 429
    
    try:
        user_data = request.json
        if not user_data:
            return jsonify({"error": "请求数据为空"}), 400
        
        logger.info(f"收到周报生成请求，IP: {client_ip}")
        
        # 构造API请求
        api_url = f"{TUZI_BASE_URL}/chat/completions"
        
        # 构造请求体
        statistics = user_data.get("statistics", {})
        prompt = f"根据以下统计数据生成周报：\n{statistics}"
        
        api_request_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的周报生成助手，帮助用户生成清晰、专业的周报。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        # 转发请求到真实API
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {TUZI_API_KEY}",
                "Content-Type": "application/json"
            },
            json=api_request_body,
            timeout=60
        )
        
        if response.status_code == 200:
            api_response = response.json()
            # 解析响应并提取报告内容
            # 简化处理：返回原始响应
            return jsonify({
                "report": "周报生成功能待实现",
                "quota_info": {
                    "remaining": {"weekly_report": 0},
                    "user_tier": user_data.get("user_tier", "free")
                }
            }), 200
        else:
            logger.error(f"API请求失败: {response.status_code}, {response.text}")
            return jsonify({
                "error": "API请求失败",
                "details": response.text[:200]
            }), response.status_code
            
    except Exception as e:
        logger.error(f"代理请求失败: {e}", exc_info=True)
        return jsonify({
            "error": "服务器内部错误",
            "details": str(e)
        }), 500


@app.route('/api/chat-query', methods=['POST'])
def proxy_chat_query():
    """代理对话查询请求"""
    if not TUZI_API_KEY:
        return jsonify({"error": "API密钥未配置"}), 500
    
    # 检查请求频率
    client_ip = request.remote_addr
    if not check_rate_limit(client_ip):
        return jsonify({
            "error": "请求过于频繁，请稍后再试"
        }), 429
    
    try:
        user_data = request.json
        if not user_data:
            return jsonify({"error": "请求数据为空"}), 400
        
        logger.info(f"收到对话查询请求，IP: {client_ip}")
        
        # 构造API请求
        api_url = f"{TUZI_BASE_URL}/chat/completions"
        
        query = user_data.get("query", "")
        context = user_data.get("context", {})
        
        api_request_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个智能助手，帮助用户解答问题。"
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # 转发请求到真实API
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {TUZI_API_KEY}",
                "Content-Type": "application/json"
            },
            json=api_request_body,
            timeout=60
        )
        
        if response.status_code == 200:
            api_response = response.json()
            # 解析响应并提取回答
            # 简化处理：返回原始响应
            return jsonify({
                "response": "对话查询功能待实现",
                "quota_info": {
                    "remaining": {"chat": 9},
                    "user_tier": user_data.get("user_tier", "free")
                }
            }), 200
        else:
            logger.error(f"API请求失败: {response.status_code}, {response.text}")
            return jsonify({
                "error": "API请求失败",
                "details": response.text[:200]
            }), response.status_code
            
    except Exception as e:
        logger.error(f"代理请求失败: {e}", exc_info=True)
        return jsonify({
            "error": "服务器内部错误",
            "details": str(e)
        }), 500


@app.route('/api/quota-status', methods=['GET'])
def proxy_quota_status():
    """代理配额查询请求（简化版，返回固定配额）"""
    # 简化实现：返回固定配额
    # 生产环境应该从数据库查询真实配额
    user_tier = request.args.get('user_tier', 'free')
    
    # 根据用户等级返回不同配额
    if user_tier == 'pro':
        return jsonify({
            "remaining": {
                "daily_plan": 50,
                "weekly_report": 10,
                "chat": 100,
                "theme_recommend": 50,
                "theme_generate": 50
            },
            "user_tier": "pro"
        }), 200
    else:
        return jsonify({
            "remaining": {
                "daily_plan": 3,
                "weekly_report": 1,
                "chat": 10,
                "theme_recommend": 5,
                "theme_generate": 3
            },
            "user_tier": "free"
        }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info("=" * 60)
    logger.info("PyDayBar API代理服务器启动")
    logger.info(f"端口: {port}")
    logger.info(f"调试模式: {debug}")
    logger.info(f"API密钥已配置: {'是' if TUZI_API_KEY else '否'}")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
