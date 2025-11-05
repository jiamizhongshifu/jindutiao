-- GaiYa每日进度条 - 初始数据Seed脚本
-- 创建日期: 2025-11-05
-- 描述: 插入基础样式、示例用户等初始数据

-- ============================================================
-- 1. 插入基础进度条样式（Free用户可用）
-- ============================================================

-- 经典纯色样式
INSERT INTO progress_bar_styles (
  style_id, name, name_en, description, category, tier, author_type,
  preview_thumbnail, files, version, status, featured
) VALUES (
  'basic-solid',
  '经典纯色',
  'Solid Color',
  '简洁的纯色进度条,适合专注工作',
  'basic',
  'free',
  'official',
  'https://cdn.gaiya.com/styles/basic-solid/thumb.jpg',
  '{
    "main": "basic-solid.qml",
    "assets": []
  }'::jsonb,
  '1.0.0',
  'published',
  true
);

-- 渐变色样式
INSERT INTO progress_bar_styles (
  style_id, name, name_en, description, category, tier, author_type,
  preview_thumbnail, files, version, status, featured
) VALUES (
  'basic-gradient',
  '渐变色',
  'Gradient',
  '柔和的渐变色进度条,视觉更丰富',
  'basic',
  'free',
  'official',
  'https://cdn.gaiya.com/styles/basic-gradient/thumb.jpg',
  '{
    "main": "basic-gradient.qml",
    "assets": []
  }'::jsonb,
  '1.0.0',
  'published',
  true
);

-- 条纹样式
INSERT INTO progress_bar_styles (
  style_id, name, name_en, description, category, tier, author_type,
  preview_thumbnail, files, version, status, featured
) VALUES (
  'basic-striped',
  '条纹',
  'Striped',
  '经典条纹进度条,动态感十足',
  'basic',
  'free',
  'official',
  'https://cdn.gaiya.com/styles/basic-striped/thumb.jpg',
  '{
    "main": "basic-striped.qml",
    "assets": ["assets/stripe-pattern.png"]
  }'::jsonb,
  '1.0.0',
  'published',
  true
);

-- 半透明样式
INSERT INTO progress_bar_styles (
  style_id, name, name_en, description, category, tier, author_type,
  preview_thumbnail, files, version, status, featured
) VALUES (
  'basic-translucent',
  '半透明',
  'Translucent',
  '优雅的半透明进度条,融入桌面背景',
  'basic',
  'free',
  'official',
  'https://cdn.gaiya.com/styles/basic-translucent/thumb.jpg',
  '{
    "main": "basic-translucent.qml",
    "assets": []
  }'::jsonb,
  '1.0.0',
  'published',
  true
);

-- ============================================================
-- 2. 插入高级进度条样式（Pro用户专属）
-- ============================================================

-- 动漫风格系列
INSERT INTO progress_bar_styles (
  style_id, name, name_en, description, category, tier, author_type,
  preview_thumbnail, preview_video, files, version, status, featured
) VALUES
(
  'anime-neon-outline',
  '霓虹描边',
  'Neon Outline',
  '二次元风格霓虹光效描边',
  'anime',
  'pro',
  'official',
  'https://cdn.gaiya.com/styles/anime-neon-outline/thumb.jpg',
  'https://cdn.gaiya.com/styles/anime-neon-outline/preview.mp4',
  '{
    "main": "anime-neon-outline.qml",
    "assets": ["assets/neon-glow.png"]
  }'::jsonb,
  '1.0.0',
  'published',
  true
),
(
  'anime-sakura-fall',
  '樱花飘落',
  'Sakura Fall',
  '樱花飘落动画效果进度条',
  'anime',
  'pro',
  'official',
  'https://cdn.gaiya.com/styles/anime-sakura-fall/thumb.jpg',
  'https://cdn.gaiya.com/styles/anime-sakura-fall/preview.mp4',
  '{
    "main": "anime-sakura-fall.qml",
    "assets": ["assets/sakura-petal.png"]
  }'::jsonb,
  '1.0.0',
  'published',
  true
),
(
  'anime-sparkle',
  '二次元光效',
  'Anime Sparkle',
  '闪光粒子特效进度条',
  'anime',
  'pro',
  'official',
  'https://cdn.gaiya.com/styles/anime-sparkle/thumb.jpg',
  'https://cdn.gaiya.com/styles/anime-sparkle/preview.mp4',
  '{
    "main": "anime-sparkle.qml",
    "assets": ["assets/sparkle-particle.png"]
  }'::jsonb,
  '1.0.0',
  'published',
  true
);

-- 赛博朋克系列
INSERT INTO progress_bar_styles (
  style_id, name, name_en, description, category, tier, author_type,
  preview_thumbnail, preview_video, files, version, status, featured
) VALUES
(
  'cyber-glitch',
  '故障艺术',
  'Glitch Effect',
  '赛博朋克故障艺术效果',
  'cyberpunk',
  'pro',
  'official',
  'https://cdn.gaiya.com/styles/cyber-glitch/thumb.jpg',
  'https://cdn.gaiya.com/styles/cyber-glitch/preview.mp4',
  '{
    "main": "cyber-glitch.qml",
    "assets": ["assets/glitch-texture.png"]
  }'::jsonb,
  '1.0.0',
  'published',
  true
),
(
  'cyber-scanline',
  '像素扫描线',
  'Pixel Scanline',
  '复古像素扫描线效果',
  'cyberpunk',
  'pro',
  'official',
  'https://cdn.gaiya.com/styles/cyber-scanline/thumb.jpg',
  'https://cdn.gaiya.com/styles/cyber-scanline/preview.mp4',
  '{
    "main": "cyber-scanline.qml",
    "assets": ["assets/scan-line.png"]
  }'::jsonb,
  '1.0.0',
  'published',
  true
),
(
  'cyber-hologram',
  '全息投影',
  'Hologram',
  '未来科技全息投影风格',
  'cyberpunk',
  'pro',
  'official',
  'https://cdn.gaiya.com/styles/cyber-hologram/thumb.jpg',
  'https://cdn.gaiya.com/styles/cyber-hologram/preview.mp4',
  '{
    "main": "cyber-hologram.qml",
    "assets": ["assets/hologram-effect.png"]
  }'::jsonb,
  '1.0.0',
  'published',
  true
);

-- 自然主题系列
INSERT INTO progress_bar_styles (
  style_id, name, name_en, description, category, tier, author_type,
  preview_thumbnail, preview_video, files, version, status, featured
) VALUES
(
  'nature-water-ripple',
  '水波纹',
  'Water Ripple',
  '柔和的水波纹动画效果',
  'nature',
  'pro',
  'official',
  'https://cdn.gaiya.com/styles/nature-water-ripple/thumb.jpg',
  'https://cdn.gaiya.com/styles/nature-water-ripple/preview.mp4',
  '{
    "main": "nature-water-ripple.qml",
    "assets": ["assets/water-texture.png"]
  }'::jsonb,
  '1.0.0',
  'published',
  true
),
(
  'nature-aurora',
  '极光',
  'Aurora',
  '绚丽的极光流动效果',
  'nature',
  'pro',
  'official',
  'https://cdn.gaiya.com/styles/nature-aurora/thumb.jpg',
  'https://cdn.gaiya.com/styles/nature-aurora/preview.mp4',
  '{
    "main": "nature-aurora.qml",
    "assets": []
  }'::jsonb,
  '1.0.0',
  'published',
  true
),
(
  'nature-starry-sky',
  '星空',
  'Starry Sky',
  '璀璨星空粒子效果',
  'nature',
  'pro',
  'official',
  'https://cdn.gaiya.com/styles/nature-starry-sky/thumb.jpg',
  'https://cdn.gaiya.com/styles/nature-starry-sky/preview.mp4',
  '{
    "main": "nature-starry-sky.qml",
    "assets": ["assets/star-particle.png"]
  }'::jsonb,
  '1.0.0',
  'published',
  true
);

-- 科技感系列
INSERT INTO progress_bar_styles (
  style_id, name, name_en, description, category, tier, author_type,
  preview_thumbnail, preview_video, files, version, status, featured
) VALUES
(
  'tech-circuit',
  '电路板',
  'Circuit Board',
  '科技感电路板动画',
  'tech',
  'pro',
  'official',
  'https://cdn.gaiya.com/styles/tech-circuit/thumb.jpg',
  'https://cdn.gaiya.com/styles/tech-circuit/preview.mp4',
  '{
    "main": "tech-circuit.qml",
    "assets": ["assets/circuit-pattern.png"]
  }'::jsonb,
  '1.0.0',
  'published',
  true
),
(
  'tech-data-stream',
  '数据流',
  'Data Stream',
  '矩阵式数据流动效果',
  'tech',
  'pro',
  'official',
  'https://cdn.gaiya.com/styles/tech-data-stream/thumb.jpg',
  'https://cdn.gaiya.com/styles/tech-data-stream/preview.mp4',
  '{
    "main": "tech-data-stream.qml",
    "assets": []
  }'::jsonb,
  '1.0.0',
  'published',
  true
),
(
  'tech-particle-flow',
  '粒子特效',
  'Particle Flow',
  '炫酷粒子流动特效',
  'tech',
  'pro',
  'official',
  'https://cdn.gaiya.com/styles/tech-particle-flow/thumb.jpg',
  'https://cdn.gaiya.com/styles/tech-particle-flow/preview.mp4',
  '{
    "main": "tech-particle-flow.qml",
    "assets": ["assets/particle-dot.png"]
  }'::jsonb,
  '1.0.0',
  'published',
  true
);

-- ============================================================
-- 3. 插入基础时间标记（Free用户可用）
-- ============================================================

INSERT INTO time_markers (
  marker_id, name, description, category, tier,
  preview_image, file_url, file_type, file_size, status
) VALUES
(
  'basic-arrow',
  '箭头标记',
  '简单的箭头形状标记',
  'basic',
  'free',
  'https://cdn.gaiya.com/markers/basic-arrow/preview.png',
  'https://cdn.gaiya.com/markers/basic-arrow/marker.png',
  'png',
  2048,
  'published'
),
(
  'basic-line',
  '线条标记',
  '简洁的竖线标记',
  'basic',
  'free',
  'https://cdn.gaiya.com/markers/basic-line/preview.png',
  'https://cdn.gaiya.com/markers/basic-line/marker.png',
  'png',
  1024,
  'published'
),
(
  'basic-dot',
  '圆点标记',
  '简单的圆点标记',
  'basic',
  'free',
  'https://cdn.gaiya.com/markers/basic-dot/preview.png',
  'https://cdn.gaiya.com/markers/basic-dot/marker.png',
  'png',
  1536,
  'published'
);

-- ============================================================
-- 4. 插入高级时间标记（Pro用户专属）
-- ============================================================

INSERT INTO time_markers (
  marker_id, name, description, category, tier,
  preview_image, file_url, file_type, file_size, status
) VALUES
(
  'animated-kun',
  '小坤跳舞',
  '经典kun跳舞动图标记',
  'animated',
  'pro',
  'https://cdn.gaiya.com/markers/animated-kun/preview.jpg',
  'https://cdn.gaiya.com/markers/animated-kun/marker.webp',
  'webp',
  512000,
  'published'
),
(
  'animated-sparkle',
  '闪光特效',
  '闪闪发光的粒子特效',
  'animated',
  'pro',
  'https://cdn.gaiya.com/markers/animated-sparkle/preview.jpg',
  'https://cdn.gaiya.com/markers/animated-sparkle/marker.gif',
  'gif',
  128000,
  'published'
),
(
  'holiday-christmas',
  '圣诞老人',
  '节日限定圣诞主题标记',
  'holiday',
  'pro',
  'https://cdn.gaiya.com/markers/holiday-christmas/preview.jpg',
  'https://cdn.gaiya.com/markers/holiday-christmas/marker.webp',
  'webp',
  256000,
  'published'
);

-- ============================================================
-- 5. 插入示例测试用户（开发环境使用）
-- ============================================================

-- 免费用户
INSERT INTO users (
  email, username, display_name, user_tier, email_verified, status
) VALUES (
  'free_user@example.com',
  'free_user',
  '免费用户测试',
  'free',
  true,
  'active'
);

-- Pro用户
INSERT INTO users (
  email, username, display_name, user_tier, email_verified, status
) VALUES (
  'pro_user@example.com',
  'pro_user',
  'Pro用户测试',
  'pro',
  true,
  'active'
);

-- 终身会员
INSERT INTO users (
  email, username, display_name, user_tier, email_verified, status
) VALUES (
  'lifetime_user@example.com',
  'lifetime_user',
  '终身会员测试',
  'lifetime',
  true,
  'active'
);

-- ============================================================
-- 完成标记
-- ============================================================
-- 初始数据插入完成
-- 基础样式：4个（Free）
-- 高级样式：12个（Pro）
-- 基础标记：3个（Free）
-- 高级标记：3个（Pro）
-- 测试用户：3个
