# 分镜设计完整规范

## 目录

- Storyboard 结构（Scene / Shot）
- 分镜设计原则与时长限制
- shot_id 命名规则
- T2V/I2V 选择规则
- 首尾帧生成策略
- 台词融入 video_prompt
- Storyboard JSON 格式
- 多镜头模式（Kling / Kling Omni）
- Review 检查机制
- 展示给用户确认

---

## Storyboard 结构

采用 **场景-分镜两层结构**：`scenes[] → shots[]`

- **场景 (Scene)**：语义+视觉+时空相对稳定的叙事单元，时长通常 10-30 秒
- **分镜 (Shot)**：最小视频生成单元，时长 2-5 秒

### 场景字段（Scene）

- `scene_id`：场景编号（如 "scene_1"）
- `scene_name`：场景名称
- `duration`：场景总时长 = 下属所有分镜时长之和
- `narrative_goal`：主叙事目标
- `spatial_setting`：空间设定
- `time_state`：时间状态
- `visual_style`：视觉母风格
- `shots[]`：分镜列表

### 分镜字段（Shot）

- `shot_id`：分镜编号（格式见下文命名规则）
- `duration`：时长（2-5秒）
- `shot_type`：establishing / dialogue / action / closeup / multi_shot
- `description`：简要描述
- `generation_mode`：text2video / img2video / omni-video
- `multi_shot`：true / false
- `generation_backend`：kling / kling-omni / vidu
- `video_prompt`：视频生成提示词
- `image_prompt`：图片生成提示词（img2video 时使用）
- `frame_strategy`：none / first_frame_only / first_and_last_frame
- `reference_images`：参考图路径列表（kling-omni 专用）
- `dialogue`：台词信息（结构化）
- `transition`：转场效果
- `audio`：是否生成音频

---

## 分镜设计原则

1. **时长分配**：总时长 = 目标时长（±2秒）
2. **节奏变化**：避免所有镜头时长相同
3. **景别变化**：连续镜头应有景别差异
4. **转场选择**：根据情绪选择合适转场
5. **单一动作原则**：同一分镜内最多 1 个动作
6. **空间不变原则**：禁止在 shot 内发生空间环境变化
7. **描述具体原则**：禁止抽象动作描述，用具体动作替代

### 时长限制

- 普通镜头：2-3 秒
- 复杂运动镜头：≤2 秒
- 静态情绪镜头：≤5 秒

---

## shot_id 命名规则

格式：`scene{场景号}_shot{分镜号}`

| 类型 | 示例 | 说明 |
|------|------|------|
| 单分镜 | `scene1_shot1`、`scene2_shot1` | 标准命名 |
| 多镜头模式 | `scene1_shot2to4_multi` | 合并分镜，带 `_multi` 后缀 |

---

## T2V/I2V 选择规则

**决策树**：

```
镜头是否包含人物？
├── 是 → 是否有注册的人物参考图？
│        ├── 是 → img2video（或 omni-video）
│        └── 否 → 是否需要精确控制表情/动作？
│                 ├── 是 → img2video
│                 └── 否 → text2video
└── 否 → 是否是复杂场景/重要镜头？
         ├── 是 → img2video
         └── 否 → text2video
```

| 镜头类型 | 生成模式 | 首尾帧策略 |
|---------|---------|-----------|
| 场景建立镜头（无人物） | text2video | none |
| 人物介绍/对话/动作（简单） | img2video | first_frame_only |
| 人物动作（复杂） | img2video | first_and_last_frame |
| 风景/物品特写 | text2video 或 img2video | none 或 first_frame_only |

---

## 首尾帧生成策略

| frame_strategy | 说明 | 执行方式 |
|---|------|---------|
| `none` | 无需首尾帧 | 直接调用文生视频 API |
| `first_frame_only` | 仅首帧 | 生成首帧图 → image2video API |
| `first_and_last_frame` | 首尾帧 | 生成首帧和尾帧 → Kling API（`image_tail` 参数） |

首尾帧字段扩展（`first_and_last_frame` 时）：

```json
{
  "frame_strategy": "first_and_last_frame",
  "image_prompt": "首帧描述",
  "last_frame_prompt": "尾帧描述"
}
```

---

## 台词融入 video_prompt

当镜头包含台词时，**必须在 video_prompt 中完整描述**：角色（含外貌）、台词内容（引号包裹）、表情/情绪、声音特质和语速。

```json
{
  "shot_id": "scene1_shot5",
  "video_prompt": "小美（25岁亚洲女性，黑色长直发）抬头看向服务生，温柔微笑着说：'这里真的很安静，我很喜欢。' 声音清脆悦耳，语速适中偏慢。保持竖屏9:16构图。",
  "dialogue": {
    "speaker": "小美",
    "content": "这里真的很安静，我很喜欢。",
    "emotion": "温柔、愉悦",
    "voice_type": "清脆女声"
  },
  "audio": true
}
```

`dialogue` 字段用途：TTS 生成、字幕提取、用户快速查看。

**TTS 旁白仅用于**：片头/片尾解说、不需要角色开口的场景描述、情感烘托旁白。**能收同期声的镜头不要用 TTS！**

---

## Storyboard JSON 格式

```json
{
  "project_name": "项目名称",
  "target_duration": 60,
  "aspect_ratio": "9:16",
  "scenes": [
    {
      "scene_id": "scene_1",
      "scene_name": "开场 - 咖啡馆相遇",
      "duration": 18,
      "narrative_goal": "展示女主角在咖啡馆的日常",
      "spatial_setting": "温馨的城市咖啡馆",
      "time_state": "下午3点",
      "visual_style": "温暖色调，电影感",
      "shots": [
        {
          "shot_id": "scene1_shot1",
          "duration": 3,
          "shot_type": "establishing",
          "description": "咖啡馆全景",
          "generation_mode": "text2video",
          "generation_backend": "kling",
          "video_prompt": "温馨的城市咖啡馆内部全景，午后阳光透过落地窗洒进来，镜头缓慢推近。保持竖屏9:16构图。",
          "frame_strategy": "none",
          "multi_shot": false,
          "dialogue": null,
          "transition": "fade_in",
          "audio": false
        }
      ]
    }
  ],
  "personas": [],
  "props": [],
  "decision_log": {}
}
```

### Kling Omni 模式示例

```json
{
  "shot_id": "scene2_shot1",
  "generation_mode": "omni-video",
  "generation_backend": "kling-omni",
  "video_prompt": "小美（<<<image_1>>>）戴着耳机，在赛车模拟器前全神贯注。竖屏9:16构图。",
  "reference_images": ["/path/to/xiaomei_ref.jpg"],
  "multi_shot": false,
  "audio": true
}
```

---

## V3-Omni 三层结构（推荐）

针对 Kling V3-Omni 的**分镜图 + 视频**两阶段生成流程，推荐采用三层结构：

### 设计理念

**分镜图（Storyboard Frame）**：不只是首帧控制，还控制整体视觉（场景、画风、灯光、氛围、色彩、妆造）

**视频生成**：引用分镜图构图，叠加动作和人物参考

### Schema 结构

```json
{
  "shot_id": "scene1_shot1",
  "duration": 7,
  "workflow_version": "v3_omni_v1",

  "storyboard": {
    "chinese_description": "连续动作与对话 (约7s)全景。初月手忙脚乱退到门外...",
    "shot_scale": "全景",
    "location": "男洗手间门口过渡区",
    "dialogue_segments": [
      {"time": "0-2s", "speaker": "初月", "line": "可以，我承认...", "emotion": "尴尬赔笑"},
      {"time": "2-4s", "speaker": "天宇", "line": "那你别一脸见鬼。", "emotion": "flat"}
    ],
    "transition": "cut"
  },

  "frame_generation": {
    "output_key": "scene1_shot1_frame",
    "prompt": "Cinematic realistic start frame...",
    "character_refs": ["Element_Chuyue", "Element_Jiazhi", "Element_Tianyu"],
    "scene": "男洗手间门口，白色瓷砖...",
    "lighting": "冷白色荧光灯",
    "camera": {"shot_scale": "wide", "angle": "eye-level"},
    "style": "cinematic realistic, cool blue-white"
  },

  "video_generation": {
    "backend": "kling_v3_omni",
    "frame_reference": "scene1_shot1_frame",
    "prompt": "Referencing scene1_shot1_frame composition...",
    "motion_overall": "Chuyue fumbles backward...",
    "motion_segments": [
      {"time": "0-2s", "action": "steps back past threshold...", "character": "Element_Chuyue"},
      {"time": "2-5s", "action": "three-way dialogue exchange", "lip_sync": true}
    ],
    "camera_movement": "static wide shot",
    "sound_effects": "shuffling footsteps on tile"
  }
}
```

### 字段说明

**storyboard 层**（中文，给人看）
- `chinese_description`: 剧情描述
- `shot_scale`: 景别（全景/中景/特写等）
- `location`: 场景位置
- `dialogue_segments`: 对白时间轴
- `transition`: 转场效果

**frame_generation 层**（生成分镜图）
- `output_key`: 输出文件名
- `prompt`: 完整的 Image Prompt
- `character_refs`: 引用的角色元素
- `scene`: 场景描述
- `lighting`: 灯光描述
- `camera`: 相机参数（shot_scale, angle, lens）
- `style`: 视觉风格

**video_generation 层**（生成视频）
- `frame_reference`: 引用的分镜图 output_key
- `prompt`: 完整的 Video Prompt
- `motion_overall`: 整体动作描述
- `motion_segments`: 分段动作（带时间轴）
- `camera_movement`: 镜头运动
- `sound_effects`: 声音设计

---

## 多镜头模式（Kling / Kling Omni）

Kling 和 Kling Omni 均支持多镜头一镜到底。

### 配置字段

```json
{
  "shot_id": "scene1_shot2to4_multi",
  "duration": 10,
  "multi_shot": true,
  "multi_shot_config": {
    "mode": "customize",
    "shots": [
      {"shot_id": "scene1_shot2", "duration": 3, "prompt": "镜头1描述"},
      {"shot_id": "scene1_shot3", "duration": 4, "prompt": "镜头2描述"},
      {"shot_id": "scene1_shot4", "duration": 3, "prompt": "镜头3描述"}
    ]
  }
}
```

### 两种模式

- **intelligence**：AI 自动分镜，适合简单叙事
- **customize**（推荐）：精确控制每个镜头内容和时长

### 多镜头规则

- 总时长 3-15s，每个镜头至少 1s
- 所有镜头时长之和 = 视频总时长

| 场景 | 推荐模式 |
|------|---------|
| 剧情视频（故事、广告） | multi_shot + customize |
| 简单叙事 | multi_shot + intelligence |
| 素材混剪（vlog、展示） | 单镜头逐个生成 |
| 简单短视频（<10s） | 单镜头 text2video |

---

## Review 检查机制

生成 storyboard 后，必须检查以下项目：

**1. 结构完整性**
- 总时长匹配目标时长（±2秒）
- 场景时长 = 下属分镜时长之和

**2. 分镜规则**
- 每个分镜时长 2-5 秒
- 无多动作分镜、无分镜内空间变化

**3. Prompt 规范**
- 所有 video_prompt 包含比例信息
- 台词已融入 video_prompt
- 无抽象动作描述

**4. 技术选择**
- T2V/I2V 选择合理
- 后端选择匹配需求
- 首尾帧策略正确

---

## 展示给用户确认（强制步骤）

**必须在用户明确确认后，才能进入 Phase 4！**

确认时展示每个镜头的：场景信息、生成模式、后端、video_prompt、image_prompt（如有）、台词、转场、时长。

用户可选择：确认并执行 / 修改分镜 / 调整时长 / 更换转场 / 取消。
