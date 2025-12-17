# GaiYa 成就系统图标设计方案

> 作为2025年最受欢迎的UI设计师，为GaiYa成就系统设计一套完整的SVG图标体系

---

## 一、设计理念

### 1.1 设计原则

| 原则 | 说明 |
|------|------|
| **简洁现代** | 扁平化设计，去除冗余装饰 |
| **一致性** | 统一的线条粗细、圆角、视觉重量 |
| **可识别性** | 每个图标都有独特的视觉特征 |
| **可扩展性** | 支持16px-128px多种尺寸 |
| **双状态** | 未解锁(灰色)/已解锁(彩色)两种状态 |

### 1.2 视觉规范

```
尺寸: 24x24 (基准), viewBox="0 0 24 24"
线条: stroke-width="2", stroke-linecap="round", stroke-linejoin="round"
圆角: rx="2" (矩形元素)
间距: 最小边距 2px
```

### 1.3 配色方案

| 分类 | 主色 | 辅色 | 用途 |
|------|------|------|------|
| 坚持之道 | #FF6B35 | #FFE0D3 | 火焰橙 |
| 效率大师 | #FFD700 | #FFF8DC | 金色 |
| 专注达人 | #4ECDC4 | #D4F5F3 | 青绿 |
| 功能探索 | #9B59B6 | #EDE7F6 | 紫色 |
| 特殊成就 | #E91E63 | #FCE4EC | 玫红 |
| 未解锁 | #9E9E9E | #F5F5F5 | 灰色 |

### 1.4 稀有度边框

| 稀有度 | 边框样式 | 颜色 |
|--------|----------|------|
| Common | 实线 1px | #BDBDBD |
| Rare | 实线 2px | #2196F3 |
| Epic | 渐变 2px | #9C27B0 → #E91E63 |
| Legendary | 渐变 3px + 光晕 | #FFD700 → #FF6B35 |

---

## 二、分类图标设计

### 2.1 坚持之道 - 火焰图标

```svg
<!-- 分类图标: 火焰 -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2c0 4-4 6-4 10a4 4 0 0 0 8 0c0-4-4-6-4-10z" fill="#FF6B35" stroke="#FF6B35"/>
  <path d="M12 8c0 2-2 3-2 5a2 2 0 0 0 4 0c0-2-2-3-2-5z" fill="#FFE0D3" stroke="none"/>
</svg>
```

### 2.2 效率大师 - 闪电图标

```svg
<!-- 分类图标: 闪电 -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="#FFD700" stroke="#FFD700"/>
</svg>
```

### 2.3 专注达人 - 靶心图标

```svg
<!-- 分类图标: 靶心 -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4ECDC4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <circle cx="12" cy="12" r="6"/>
  <circle cx="12" cy="12" r="2" fill="#4ECDC4"/>
</svg>
```

### 2.4 功能探索 - 指南针图标

```svg
<!-- 分类图标: 指南针 -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9B59B6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="#9B59B6"/>
</svg>
```

### 2.5 特殊成就 - 星星图标

```svg
<!-- 分类图标: 星星 -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E91E63" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" fill="#E91E63"/>
</svg>
```

---

## 三、成就图标设计

### 3.1 坚持之道系列

#### 初心者 (first_day)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FF6B35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <path d="M12 6v6l4 2"/>
</svg>
```

#### 周末战士 (consistency_7)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FF6B35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
  <line x1="16" y1="2" x2="16" y2="6"/>
  <line x1="8" y1="2" x2="8" y2="6"/>
  <line x1="3" y1="10" x2="21" y2="10"/>
  <path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01" stroke-width="3"/>
</svg>
```

#### 七日之约 (week_warrior)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FF6B35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
  <path d="M2 17l10 5 10-5"/>
  <path d="M2 12l10 5 10-5"/>
  <text x="12" y="16" text-anchor="middle" font-size="8" fill="#FF6B35" stroke="none">7</text>
</svg>
```

#### 习惯养成 (consistency_30)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FF6B35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2c0 4-4 6-4 10a4 4 0 0 0 8 0c0-4-4-6-4-10z" fill="#FF6B35"/>
  <text x="12" y="16" text-anchor="middle" font-size="7" fill="#FFF" stroke="none" font-weight="bold">30</text>
</svg>
```

#### 百日之约 (consistency_100)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FF6B35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2c0 4-4 6-4 10a4 4 0 0 0 8 0c0-4-4-6-4-10z" fill="#FF6B35"/>
  <path d="M8 18c0 2 2 4 4 4s4-2 4-4" fill="#FFE0D3" stroke="#FF6B35"/>
  <circle cx="12" cy="12" r="3" fill="#FFE0D3" stroke="none"/>
</svg>
```

#### 年度陪伴 (consistency_365)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
  <defs>
    <linearGradient id="legendary1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFD700"/>
      <stop offset="100%" style="stop-color:#FF6B35"/>
    </linearGradient>
  </defs>
  <path d="M12 2c0 4-4 6-4 10a4 4 0 0 0 8 0c0-4-4-6-4-10z" fill="url(#legendary1)" stroke="url(#legendary1)" stroke-width="2"/>
  <circle cx="12" cy="12" r="2" fill="#FFF"/>
  <path d="M6 20h12" stroke="#FFD700" stroke-width="2" stroke-linecap="round"/>
  <path d="M8 22h8" stroke="#FFD700" stroke-width="2" stroke-linecap="round"/>
</svg>
```

#### 早起鸟儿 (early_bird_7)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FF6B35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="6" r="4" fill="#FFE0D3"/>
  <path d="M12 10v2"/>
  <path d="M8 14c0 4 2 6 4 8 2-2 4-4 4-8"/>
  <path d="M6 14h12"/>
  <path d="M4 4l2 2M20 4l-2 2M12 0v2"/>
</svg>
```

#### 夜猫子 (night_owl_7)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FF6B35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="#FF6B35"/>
  <circle cx="9" cy="10" r="1.5" fill="#FFF"/>
  <circle cx="15" cy="10" r="1.5" fill="#FFF"/>
  <path d="M9 16c1.5 1 4.5 1 6 0" stroke="#FFF"/>
</svg>
```

### 3.2 效率大师系列

#### 任务新手 (task_10)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFD700" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M9 11l3 3L22 4"/>
  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
</svg>
```

#### 百任务达人 (task_100)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFD700" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M9 11l3 3L22 4"/>
  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
  <circle cx="17" cy="17" r="5" fill="#FFD700" stroke="#FFD700"/>
  <text x="17" y="20" text-anchor="middle" font-size="6" fill="#FFF" stroke="none" font-weight="bold">100</text>
</svg>
```

#### 任务狂人 (task_500)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFD700" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="#FFD700"/>
  <text x="12" y="15" text-anchor="middle" font-size="6" fill="#FFF" stroke="none" font-weight="bold">500</text>
</svg>
```

#### 完美一天 (perfect_day)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFD700" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10" fill="#FFD700"/>
  <path d="M8 14s1.5 2 4 2 4-2 4-2" stroke="#FFF" fill="none"/>
  <line x1="9" y1="9" x2="9.01" y2="9" stroke="#FFF" stroke-width="3"/>
  <line x1="15" y1="9" x2="15.01" y2="9" stroke="#FFF" stroke-width="3"/>
</svg>
```

#### 完美一周 (perfect_week)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
  <defs>
    <linearGradient id="epic1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#9C27B0"/>
      <stop offset="100%" style="stop-color:#FFD700"/>
    </linearGradient>
  </defs>
  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" fill="url(#epic1)" stroke="url(#epic1)" stroke-width="2"/>
  <text x="12" y="14" text-anchor="middle" font-size="6" fill="#FFF" stroke="none" font-weight="bold">7</text>
</svg>
```

#### 效率恶魔 (speed_demon)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFD700" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="#FFD700"/>
  <polygon points="15 6 10 12 13 12 12 17 17 11 14 11 15 6" fill="#FFF" stroke="none"/>
</svg>
```

#### 分类大师 (category_master)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFD700" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="3" width="7" height="7" fill="#FFD700"/>
  <rect x="14" y="3" width="7" height="7" fill="#FFE082"/>
  <rect x="14" y="14" width="7" height="7" fill="#FFD700"/>
  <rect x="3" y="14" width="7" height="7" fill="#FFE082"/>
</svg>
```

### 3.3 专注达人系列

#### 专注新星 (focus_10h)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4ECDC4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <circle cx="12" cy="12" r="3" fill="#4ECDC4"/>
</svg>
```

#### 专注达人 (focus_100h)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4ECDC4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <circle cx="12" cy="12" r="6"/>
  <circle cx="12" cy="12" r="2" fill="#4ECDC4"/>
  <path d="M12 2v2M12 20v2M2 12h2M20 12h2"/>
</svg>
```

#### 专注大师 (focus_500h)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
  <defs>
    <linearGradient id="focus_epic" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4ECDC4"/>
      <stop offset="100%" style="stop-color:#44A08D"/>
    </linearGradient>
  </defs>
  <circle cx="12" cy="12" r="10" fill="url(#focus_epic)" stroke="url(#focus_epic)" stroke-width="2"/>
  <circle cx="12" cy="12" r="6" fill="none" stroke="#FFF" stroke-width="2"/>
  <circle cx="12" cy="12" r="2" fill="#FFF"/>
  <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="#FFF" stroke-width="2"/>
</svg>
```

#### 深度工作 (deep_work)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4ECDC4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
  <circle cx="12" cy="12" r="5" fill="#4ECDC4"/>
  <text x="12" y="15" text-anchor="middle" font-size="7" fill="#FFF" stroke="none" font-weight="bold">2h</text>
</svg>
```

#### 代码战士 (code_warrior)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4ECDC4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="16 18 22 12 16 6"/>
  <polyline points="8 6 2 12 8 18"/>
  <line x1="12" y1="2" x2="12" y2="22" stroke-dasharray="2 2"/>
</svg>
```

#### 写作者 (writer)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4ECDC4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 19l7-7 3 3-7 7-3-3z"/>
  <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/>
  <path d="M2 2l7.586 7.586"/>
  <circle cx="11" cy="11" r="2" fill="#4ECDC4"/>
</svg>
```

### 3.4 功能探索系列

#### 场景设计师 (scene_creator)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9B59B6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
  <circle cx="8.5" cy="8.5" r="1.5" fill="#9B59B6"/>
  <polyline points="21 15 16 10 5 21"/>
</svg>
```

#### AI助手 (ai_user)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9B59B6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1a7 7 0 0 1-14 0H5a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" fill="#EDE7F6"/>
  <circle cx="9" cy="13" r="1" fill="#9B59B6"/>
  <circle cx="15" cy="13" r="1" fill="#9B59B6"/>
  <path d="M9 17h6" stroke="#9B59B6"/>
</svg>
```

#### 数据分析师 (stats_viewer)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9B59B6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <line x1="18" y1="20" x2="18" y2="10"/>
  <line x1="12" y1="20" x2="12" y2="4"/>
  <line x1="6" y1="20" x2="6" y2="14"/>
  <line x1="2" y1="20" x2="22" y2="20"/>
</svg>
```

#### 高级用户 (power_user)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9B59B6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" fill="#9B59B6"/>
  <circle cx="12" cy="12" r="3" fill="#EDE7F6" stroke="none"/>
  <path d="M12 10v4M10 12h4" stroke="#9B59B6" stroke-width="1.5"/>
</svg>
```

### 3.5 特殊成就系列

#### 新年新气象 (new_year)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
  <defs>
    <linearGradient id="newyear" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#E91E63"/>
      <stop offset="100%" style="stop-color:#FF5722"/>
    </linearGradient>
  </defs>
  <rect x="2" y="6" width="20" height="16" rx="2" fill="url(#newyear)" stroke="url(#newyear)" stroke-width="2"/>
  <path d="M8 2v4M16 2v4M2 10h20" stroke="#E91E63" stroke-width="2" stroke-linecap="round"/>
  <text x="12" y="18" text-anchor="middle" font-size="8" fill="#FFF" stroke="none" font-weight="bold">1.1</text>
</svg>
```

#### 周年纪念 (anniversary)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
  <defs>
    <linearGradient id="anniversary" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFD700"/>
      <stop offset="50%" style="stop-color:#E91E63"/>
      <stop offset="100%" style="stop-color:#9C27B0"/>
    </linearGradient>
  </defs>
  <circle cx="12" cy="12" r="10" fill="url(#anniversary)" stroke="url(#anniversary)" stroke-width="2"/>
  <text x="12" y="10" text-anchor="middle" font-size="5" fill="#FFF" stroke="none">365</text>
  <text x="12" y="16" text-anchor="middle" font-size="5" fill="#FFF" stroke="none">DAYS</text>
  <path d="M12 2l1 3-3-1 3 1-1 3 1-3 3 1-3-1 1-3" fill="#FFF" stroke="none"/>
</svg>
```

---

## 四、稀有度徽章框设计

### 4.1 Common (普通)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="30" fill="none" stroke="#BDBDBD" stroke-width="2"/>
  <!-- 内部放置成就图标 -->
</svg>
```

### 4.2 Rare (稀有)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="30" fill="none" stroke="#2196F3" stroke-width="3"/>
  <circle cx="32" cy="32" r="27" fill="none" stroke="#2196F3" stroke-width="1" stroke-dasharray="4 4"/>
  <!-- 内部放置成就图标 -->
</svg>
```

### 4.3 Epic (史诗)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="epic_border" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#9C27B0"/>
      <stop offset="100%" style="stop-color:#E91E63"/>
    </linearGradient>
  </defs>
  <circle cx="32" cy="32" r="30" fill="none" stroke="url(#epic_border)" stroke-width="3"/>
  <circle cx="32" cy="32" r="26" fill="none" stroke="url(#epic_border)" stroke-width="1"/>
  <!-- 内部放置成就图标 -->
</svg>
```

### 4.4 Legendary (传说)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="legendary_border" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFD700"/>
      <stop offset="50%" style="stop-color:#FF6B35"/>
      <stop offset="100%" style="stop-color:#FFD700"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <circle cx="32" cy="32" r="30" fill="none" stroke="url(#legendary_border)" stroke-width="4" filter="url(#glow)"/>
  <circle cx="32" cy="32" r="25" fill="none" stroke="url(#legendary_border)" stroke-width="1"/>
  <!-- 装饰星星 -->
  <polygon points="32,4 34,10 40,10 35,14 37,20 32,16 27,20 29,14 24,10 30,10" fill="#FFD700"/>
  <!-- 内部放置成就图标 -->
</svg>
```

---

## 五、未解锁状态设计

所有未解锁成就使用统一的灰度处理：

```svg
<!-- 未解锁状态示例 -->
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <defs>
    <filter id="grayscale">
      <feColorMatrix type="matrix" values="0.33 0.33 0.33 0 0
                                            0.33 0.33 0.33 0 0
                                            0.33 0.33 0.33 0 0
                                            0    0    0    0.5 0"/>
    </filter>
  </defs>
  <g filter="url(#grayscale)" opacity="0.6">
    <!-- 原图标内容 -->
  </g>
  <!-- 锁定图标叠加 -->
  <g transform="translate(44, 44)">
    <rect x="2" y="6" width="12" height="10" rx="2" fill="#9E9E9E"/>
    <path d="M5 6V4a3 3 0 0 1 6 0v2" fill="none" stroke="#9E9E9E" stroke-width="2"/>
  </g>
</svg>
```

---

## 六、实现指南

### 6.1 Python 集成方式

```python
# gaiya/ui/icons/achievement_icons.py

ACHIEVEMENT_ICONS = {
    "first_day": """<svg>...</svg>""",
    "week_warrior": """<svg>...</svg>""",
    # ... 更多图标
}

def get_achievement_icon(achievement_id: str, unlocked: bool = True) -> str:
    """获取成就图标SVG"""
    base_svg = ACHIEVEMENT_ICONS.get(achievement_id, ACHIEVEMENT_ICONS["default"])
    if not unlocked:
        return apply_grayscale_filter(base_svg)
    return base_svg
```

### 6.2 QSS 样式集成

```css
/* 成就图标容器 */
.achievement-icon {
    min-width: 48px;
    min-height: 48px;
    border-radius: 24px;
}

.achievement-icon.common { border: 2px solid #BDBDBD; }
.achievement-icon.rare { border: 3px solid #2196F3; }
.achievement-icon.epic { border: 3px solid qlineargradient(...); }
.achievement-icon.legendary { border: 4px solid #FFD700; }

.achievement-icon.locked {
    opacity: 0.5;
    filter: grayscale(100%);
}
```

---

## 七、资源文件结构

```
gaiya/
├── resources/
│   └── icons/
│       └── achievements/
│           ├── categories/
│           │   ├── consistency.svg
│           │   ├── productivity.svg
│           │   ├── focus.svg
│           │   ├── explorer.svg
│           │   └── special.svg
│           ├── badges/
│           │   ├── common_frame.svg
│           │   ├── rare_frame.svg
│           │   ├── epic_frame.svg
│           │   └── legendary_frame.svg
│           └── achievements/
│               ├── first_day.svg
│               ├── week_warrior.svg
│               ├── consistency_30.svg
│               └── ... (所有成就图标)
```

---

**设计版本**: v1.0
**设计日期**: 2024-12-16
**设计师**: AI UI Designer
