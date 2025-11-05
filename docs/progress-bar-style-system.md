# GaiYa每日进度条 - 个性化样式系统设计

> **核心理念**: 让进度条不只是功能，更是艺术
> **商业模式**: Free基础样式 + Pro高级样式 + 样式商店生态
> **设计日期**: 2025-11-05

---

## 🎨 产品定位调整

### 原方向（已放弃）
- ❌ AI生成主题配色
- ❌ AI推荐主题
- ❌ 配额限制配色数量

### 新方向（推荐）✅
- ✅ **免费用户**：享受所有配色主题，无限制
- ✅ **Pro用户**：解锁高级进度条样式（动漫风、赛博风等）
- ✅ **样式商店**：用户可以购买/出售自己设计的样式
- ✅ **时间标记**：高级动图、特效标记（Pro专属）

**核心差异化**：
> 从"配色限制"变为"样式升级"，用户不是被迫付费解锁基础功能，而是主动升级获得更炫酷的视觉体验。

---

## 🎯 样式系统架构

### 1. 样式分类体系

```
进度条样式（ProgressBarStyle）
├── 基础样式（Free）- 内置
│   ├── 经典纯色（Solid）
│   ├── 渐变色（Gradient）
│   ├── 条纹（Striped）
│   └── 半透明（Translucent）
│
├── 高级样式（Pro）- 需订阅
│   ├── 动漫风格
│   │   ├── 二次元光效
│   │   ├── 樱花飘落
│   │   └── 霓虹描边
│   ├── 赛博朋克
│   │   ├── 像素扫描线
│   │   ├── 故障艺术（Glitch）
│   │   └── 全息投影
│   ├── 自然主题
│   │   ├── 水波纹
│   │   ├── 极光
│   │   └── 星空
│   └── 科技感
│       ├── 电路板
│       ├── 数据流
│       └── 粒子特效
│
└── 商店样式（付费/免费）- UGC内容
    ├── 设计师原创
    ├── 社区投稿
    └── 官方限定
```

### 2. 时间标记样式

```
时间标记（TimeMarker）
├── 基础标记（Free）
│   ├── 静态图片（PNG/JPG）
│   └── 简单形状（线条、箭头）
│
├── 高级标记（Pro）
│   ├── 动态图（GIF/WebP）
│   ├── 粒子特效
│   ├── 发光效果
│   └── 自定义动画
│
└── 商店标记（付费）
    ├── 节日主题（春节、圣诞）
    ├── 二次元角色
    ├── 品牌联名
    └── 用户创作
```

---

## 📂 数据结构设计

### 样式元数据（JSON Schema）

```json
{
  "style_id": "cyber-glitch-001",
  "name": "赛博故障艺术",
  "name_en": "Cyber Glitch",
  "category": "cyberpunk",
  "tier": "pro",
  "author": "official",
  "version": "1.0.0",

  "preview": {
    "thumbnail": "https://cdn.gaiya.com/styles/cyber-glitch-001/thumb.jpg",
    "video": "https://cdn.gaiya.com/styles/cyber-glitch-001/preview.mp4"
  },

  "files": {
    "main": "cyber-glitch-001.qml",
    "assets": [
      "assets/glitch-texture.png",
      "assets/scan-line.png"
    ]
  },

  "metadata": {
    "description": "赛博朋克风格，带有扫描线和故障艺术效果",
    "tags": ["赛博", "科技", "炫酷", "动态"],
    "compatible_versions": ["1.5.0+"],
    "performance": "medium"
  },

  "pricing": {
    "type": "pro_exclusive",
    "price": 0
  },

  "stats": {
    "downloads": 1234,
    "rating": 4.8,
    "favorites": 567
  }
}
```

---

## 🗄️ Supabase数据库表设计

### 1. progress_bar_styles表（进度条样式库）

```sql
CREATE TABLE progress_bar_styles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- 基本信息
  style_id TEXT UNIQUE NOT NULL,  -- 样式唯一标识（如cyber-glitch-001）
  name TEXT NOT NULL,  -- 样式名称
  name_en TEXT,
  description TEXT,

  -- 分类
  category TEXT NOT NULL CHECK (category IN (
    'basic', 'anime', 'cyberpunk', 'nature', 'tech', 'custom'
  )),

  -- 访问控制
  tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'shop')),
  author_id UUID REFERENCES users(id),  -- 作者（用户上传的样式）
  author_type TEXT DEFAULT 'official' CHECK (author_type IN ('official', 'user')),

  -- 文件信息
  preview_thumbnail TEXT,  -- 缩略图URL
  preview_video TEXT,  -- 预览视频URL
  files JSONB NOT NULL,  -- 样式文件列表（QML + assets）

  -- 版本和兼容性
  version TEXT DEFAULT '1.0.0',
  compatible_versions TEXT[] DEFAULT ARRAY['1.5.0'],

  -- 统计数据
  downloads INTEGER DEFAULT 0,
  rating DECIMAL(3,2) DEFAULT 0.0,
  favorites INTEGER DEFAULT 0,

  -- 定价（样式商店）
  price DECIMAL(10,2) DEFAULT 0.0,
  currency TEXT DEFAULT 'CNY',

  -- 状态
  status TEXT DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),
  featured BOOLEAN DEFAULT FALSE,  -- 是否精选

  -- 时间戳
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_styles_category ON progress_bar_styles(category);
CREATE INDEX idx_styles_tier ON progress_bar_styles(tier);
CREATE INDEX idx_styles_author ON progress_bar_styles(author_id);
CREATE INDEX idx_styles_status ON progress_bar_styles(status);

-- 更新时间戳触发器
CREATE TRIGGER update_styles_updated_at BEFORE UPDATE ON progress_bar_styles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 2. time_markers表（时间标记库）

```sql
CREATE TABLE time_markers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- 基本信息
  marker_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,

  -- 分类
  category TEXT NOT NULL CHECK (category IN (
    'basic', 'animated', 'holiday', 'anime', 'custom'
  )),

  -- 访问控制
  tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'shop')),
  author_id UUID REFERENCES users(id),

  -- 文件信息
  preview_image TEXT,
  file_url TEXT NOT NULL,  -- 标记文件URL（图片/动图）
  file_type TEXT CHECK (file_type IN ('png', 'jpg', 'gif', 'webp')),
  file_size INTEGER,  -- 文件大小（bytes）

  -- 统计和定价
  downloads INTEGER DEFAULT 0,
  rating DECIMAL(3,2) DEFAULT 0.0,
  price DECIMAL(10,2) DEFAULT 0.0,

  -- 状态
  status TEXT DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),

  -- 时间戳
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_markers_category ON time_markers(category);
CREATE INDEX idx_markers_tier ON time_markers(tier);
```

### 3. user_purchased_styles表（用户购买记录）

```sql
CREATE TABLE user_purchased_styles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,

  -- 购买的样式
  item_type TEXT NOT NULL CHECK (item_type IN ('style', 'marker')),
  item_id UUID,  -- 关联到progress_bar_styles或time_markers

  -- 购买信息
  price DECIMAL(10,2) NOT NULL,
  currency TEXT DEFAULT 'CNY',
  payment_id UUID REFERENCES payments(id),

  -- 时间戳
  purchased_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_purchased_user ON user_purchased_styles(user_id);
CREATE INDEX idx_purchased_item ON user_purchased_styles(item_id);

-- 唯一约束：同一用户不能重复购买同一样式
CREATE UNIQUE INDEX idx_purchased_unique
  ON user_purchased_styles(user_id, item_type, item_id);
```

### 4. user_favorites表（用户收藏）

```sql
CREATE TABLE user_favorites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,

  item_type TEXT NOT NULL CHECK (item_type IN ('style', 'marker')),
  item_id UUID,

  created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_favorites_user ON user_favorites(user_id);

-- 唯一约束
CREATE UNIQUE INDEX idx_favorites_unique
  ON user_favorites(user_id, item_type, item_id);
```

---

## 💎 Free vs Pro 功能对比

### Free用户（免费版）

**进度条样式**:
- ✅ 所有基础样式（4种）
  - 经典纯色
  - 渐变色
  - 条纹
  - 半透明
- ✅ 所有配色主题（无限制）
- ✅ 自定义颜色

**时间标记**:
- ✅ 静态图片标记
- ✅ 简单形状标记
- ✅ 上传自定义图片（PNG/JPG）

**AI功能**:
- ✅ 任务规划：3次/天
- ✅ 周报生成：1次/周
- ✅ 对话查询：10次/天

---

### Pro用户（专业版）

**进度条样式**:
- ✅ 所有Free样式
- 💎 **高级样式（12+种）**
  - 动漫风格系列（3种）
  - 赛博朋克系列（3种）
  - 自然主题系列（3种）
  - 科技感系列（3种）
- 💎 **每月新增样式**（持续更新）

**时间标记**:
- ✅ 所有Free标记
- 💎 **动态标记（GIF/WebP）**
- 💎 **粒子特效标记**
- 💎 **发光和动画效果**

**AI功能**:
- ♾️ 任务规划：**50次/天**
- ♾️ 周报生成：10次/周
- ♾️ 对话查询：100次/天
- 💎 AI时间分析报告（周报/月报）

**云端服务**:
- ☁️ 多设备数据同步
- 🔄 配置自动备份（30天）
- 📊 高级统计报告（趋势分析）

**样式商店**:
- 🎁 每月10积分（购买付费样式）
- 💰 出售自己的样式（70%分成）
- 🎨 专属设计师模板

---

## 🛒 样式商店生态设计

### 1. 内容来源

```
样式内容生态
│
├── 官方样式（Official）
│   ├── 免费精选（吸引用户）
│   ├── Pro专属（会员福利）
│   └── 节日限定（营销活动）
│
├── 设计师合作（Partner）
│   ├── 知名设计师（品质保证）
│   ├── 品牌联名（商业合作）
│   └── 主题包（成套销售）
│
└── 用户创作（UGC）
    ├── 社区投稿（审核后上架）
    ├── 排行榜（激励创作）
    └── 分成机制（70%给作者）
```

### 2. 定价策略

**免费样式**:
- 官方基础样式
- 社区优质投稿（官方买断）
- 节日活动赠送

**Pro专属样式**:
- 包含在订阅内
- 每月新增2-3个
- 无需额外付费

**付费样式**:
- 定价范围：¥1-¥5 /个
- 主题包：¥9-¥19 /套（5-10个样式）
- 限定款：¥19-¥29 /个

**积分系统**:
- Pro用户每月10积分
- 1积分 = ¥1
- 可用于购买样式商店内容

### 3. 创作者分成

**用户上传样式**:
- 提交样式文件（QML + Assets）
- 官方审核（质量、版权、安全性）
- 上架样式商店

**收益分配**:
- 作者：70%
- 平台：30%

**提现规则**:
- 最低提现额度：¥50
- 提现周期：每月15日
- 提现方式：支付宝/微信/银行卡

**激励计划**:
- 新人奖励：首个样式上架奖励3个月Pro
- 月度榜单：Top 10创作者额外奖励
- 粉丝系统：用户可以关注喜欢的设计师

---

## 🎨 样式开发指南（技术实现）

### 1. 样式文件格式（QML）

```qml
// cyber-glitch-001.qml
import QtQuick 2.15

Rectangle {
    id: progressBar
    width: parent.width
    height: 10

    // 基础背景
    color: "transparent"

    // 渐变填充
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#00ff9d" }
        GradientStop { position: 1.0; color: "#00b8ff" }
    }

    // 扫描线效果
    Image {
        source: "assets/scan-line.png"
        anchors.fill: parent
        fillMode: Image.Tile
        opacity: 0.3

        SequentialAnimation on y {
            loops: Animation.Infinite
            NumberAnimation { from: 0; to: -20; duration: 1000 }
        }
    }

    // 故障闪烁
    Rectangle {
        anchors.fill: parent
        color: "#ff0055"
        opacity: 0

        SequentialAnimation on opacity {
            loops: Animation.Infinite
            NumberAnimation { to: 0.8; duration: 50 }
            NumberAnimation { to: 0; duration: 50 }
            PauseAnimation { duration: 3000 }
        }
    }
}
```

### 2. 样式加载系统

```python
# gaiya/core/style_manager.py

class StyleManager:
    """样式管理器"""

    def __init__(self):
        self.styles_dir = Path.home() / ".gaiya" / "styles"
        self.styles_dir.mkdir(parents=True, exist_ok=True)

    def get_available_styles(self, user_tier: str) -> List[Dict]:
        """
        获取可用样式列表

        Args:
            user_tier: 用户等级

        Returns:
            样式列表
        """
        # 1. 获取内置基础样式
        basic_styles = self._get_basic_styles()

        # 2. 如果是Pro用户，加载高级样式
        if user_tier in ['pro', 'lifetime']:
            pro_styles = self._get_pro_styles()
            basic_styles.extend(pro_styles)

        # 3. 加载用户购买的样式
        purchased_styles = self._get_purchased_styles(user_id)
        basic_styles.extend(purchased_styles)

        return basic_styles

    def download_style(self, style_id: str, user_id: str) -> bool:
        """
        下载样式文件到本地

        Args:
            style_id: 样式ID
            user_id: 用户ID

        Returns:
            是否成功
        """
        # 1. 从样式商店API获取下载链接
        # 2. 下载QML文件和资源文件
        # 3. 解压到本地styles目录
        # 4. 验证文件完整性
        # 5. 记录下载统计
        pass

    def apply_style(self, style_id: str):
        """应用样式到进度条"""
        # 加载QML文件
        # 替换当前进度条组件
        pass
```

---

## 📅 开发时间表（调整后）

### v1.6.0 商业化功能（3个月）

#### 第一阶段：基础设施（3周）
- Week 1: 用户认证系统
- Week 2: 支付集成
- Week 3: 测试与优化

#### 第二阶段：Pro功能开发（4周）
- Week 4-5: **样式系统开发**
  - [ ] 创建样式管理器（StyleManager）
  - [ ] 实现基础样式（4种）
  - [ ] 实现高级样式（12种）
  - [ ] 样式切换UI

- Week 6-7: 云端同步
- Week 8: 高级分析功能

#### 第三阶段：样式商店（2周）
- Week 9: 样式商店基础
  - [ ] 样式浏览和搜索
  - [ ] 样式购买流程
  - [ ] 样式下载管理

- Week 10: 创作者功能
  - [ ] 样式上传
  - [ ] 收益管理
  - [ ] 审核流程

---

## 🎯 商业目标（修订）

### v1.6.0 目标（2026年3月）
- [ ] Pro付费用户：100+
- [ ] 官方高级样式：12+种
- [ ] 样式商店上架：50+款（含UGC）
- [ ] 月经常性收入（MRR）：≥ ¥1000

### v1.7.0 目标（2026年Q2）
- [ ] 样式商店GMV：≥ ¥5000/月
- [ ] 活跃创作者：20+人
- [ ] 用户自创样式：100+款
- [ ] 品牌联名合作：2+个

---

## 💡 未来展望

### 样式商店2.0（v2.0+）
- 🎬 动态样式（视频背景）
- 🎮 交互式样式（鼠标悬停特效）
- 🌈 季节性自动切换
- 🤝 社交分享（朋友圈/小红书）

### 生态建设
- 👥 设计师认证计划
- 🏆 月度样式大赛
- 📚 样式开发教程
- 🛠️ 可视化样式编辑器

---

**文档维护**:
- 制定日期：2025-11-05
- 最后更新：2025-11-05
- 负责人：产品团队

