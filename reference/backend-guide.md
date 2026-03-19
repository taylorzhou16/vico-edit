# 后端选择与参考图策略

## 目录

- 三种后端能力对比
- 后端选择决策树
- 自动选择逻辑
- 人物参考图三条路径
- 路径 A：Kling Omni（角色一致性优先）
- 路径 B：Kling + Gemini 首帧（场景精确度优先）
- **路径 C：Kling V3-Omni（推荐）**
- Gemini Prompt 注意事项

---

## 三种后端能力对比

| 能力 | Vidu | Kling | Kling Omni |
|------|------|-------|------------|
| **后端名** | `vidu` | `kling` | `kling-omni` |
| **文生视频** | 5-10s | 3-15s | 3-15s |
| **图生视频** | 单图 | 首帧图（精确控制） | 用 image_list 代替 |
| **image_list 多参考图** | -- | -- | `<<<image_1>>>` 引用 |
| **multi_shot 多镜头** | -- | intelligence / customize | intelligence / customize |
| **首尾帧控制** | -- | `--image` + `--tail-image` | -- |
| **音画同出** | -- | `--audio` | `--audio` |
| **最佳场景** | 简单快速、兜底 | 首帧精确控制、场景一致 | 角色一致性、多人物 |

**重要区别**：
- Kling `--image` 是**首帧图**（视频从此图开始）
- Kling Omni `--image-list` 是**参考图**（人物保持一致，但首帧不确定）

---

## 后端选择决策树

**核心权衡：人物一致性 vs 场景精确度 vs 两者兼顾**

```
镜头是否包含人物？
├── 是 → 是否有注册的人物参考图？
│        ├── 是 → 需要场景精确控制吗？
│        │        ├── 是 → 需要角色一致性吗？
│        │        │        ├── 两者都要 → kling-omni V3 + 分镜图 (Path C)
│        │        │        └── 场景优先，角色可接受波动 → kling + Gemini 首帧 (Path B)
│        │        └── 否 → kling-omni --image-list (Path A)
│        └── 否 → 是否需要精确控制首帧画面？
│                 ├── 是 → kling + image（Gemini 生首帧）
│                 └── 否 → kling text2video
└── 否 → 是否需要 multi_shot？
         ├── 是 → kling
         └── 否 → kling（默认）
```

### 场景速查

| 场景 | 后端 | 关键参数 |
|------|------|---------|
| **剧情视频，场景+角色都要** | **kling-omni V3** | `--image frame.png --image-list ref.jpg` |
| 有人物参考图，要保持一致 | kling-omni | `--image-list ref.jpg` |
| 需要精确首帧画面 | kling | `--image first_frame.png` |
| 需要首尾帧动画 | kling | `--image first.png --tail-image last.png` |
| 多镜头剧情 + 角色一致 | kling-omni | `--image-list ref.jpg --multi-shot` |
| 简单无人场景 / 快速原型 | kling（默认）或 vidu | 无需特殊参数 |

---

## 自动选择逻辑

未指定 `--backend` 时默认使用 **kling**。特殊参数会强制切换后端：
- 提供 `--image-list` → 自动切换到 kling-omni（唯一支持）
- 提供 `--tail-image` → 保持 kling（唯一支持）
- 需要快速兜底 → 手动指定 `--backend vidu`

---

## 人物参考图三条路径

**仅当已注册人物参考图时考虑。**

| | Path A: Kling Omni | Path B: Kling + Gemini | **Path C: V3-Omni（推荐）** |
|---|---|---|---|
| **流程** | 参考图 → Kling Omni `--image-list` | 参考图 → Gemini 生分镜图 → Kling img2video | **分镜图 → V3-Omni + image_list** |
| **优势** | 路径简单，无需中间步骤 | 场景精确可控 | **两者兼顾：场景可控 + 角色一致** |
| **一致性** | 同一参考图多镜头自动一致 | 多镜头间一致性难保证 | **分镜图+参考图双重保障** |
| **场景控制力** | 弱（纯prompt控制） | 强（分镜图定义） | **强（分镜图定义）** |
| **适用** | 快速原型、人物一致性优先 | 场景精确度优先 | **剧情视频（推荐）** |

**选择建议**：
- 快速原型、人物一致性优先 → **Path A: Kling Omni**
- 场景精确度优先、可接受角色波动 → **Path B: Kling + Gemini**
- **剧情视频、两者都要 → Path C: V3-Omni（推荐）**

---

## 路径 A：Kling Omni（推荐）

```
人物参考图 → Kling Omni（--image-list，prompt 用 <<<image_1>>> 引用）→ 视频
```

- 无需 Gemini 生成分镜图
- 同一参考图可在多个镜头中重复使用
- multi_shot 模式下同一人自动保持一致

```bash
python vico_tools.py video \
  --backend kling-omni \
  --prompt "人物 <<<image_1>>> 在咖啡馆窗边坐下，微笑着看向窗外" \
  --image-list /path/to/person_ref.jpg \
  --audio --output output.mp4
```

### Omni 多参考图 + multi_shot

```bash
python vico_tools.py video --backend kling-omni \
  --prompt "故事" \
  --image-list ref1.jpg ref2.jpg \
  --multi-shot --shot-type customize \
  --multi-prompt '[{"index":1,"prompt":"<<<image_1>>> 镜头1","duration":"3"},{"index":2,"prompt":"<<<image_2>>> 镜头2","duration":"4"}]' \
  --duration 7
```

### Omni 模式 Storyboard 标注

```json
{
  "shot_id": "scene1_shot2",
  "generation_mode": "omni-video",
  "generation_backend": "kling-omni",
  "video_prompt": "小美（<<<image_1>>>）抬头看向服务生，温柔微笑...",
  "reference_images": ["/path/to/xiaomei_ref.jpg"]
}
```

---

## 路径 C：Kling V3-Omni（推荐）

**V3-Omni 双阶段生成流程**——结合分镜图视觉控制与角色参考一致性。

```
阶段1: 角色参考图 + Image Prompt → Gemini 生成分镜图（控制场景/画风/灯光/氛围/色彩/妆造）
         ↓
阶段2: 分镜图 + 角色参考图 + Video Prompt → Kling V3-Omni 生成视频
```

**关键认知**：
- **分镜图**不只是首帧控制，还控制整体视觉（场景、画风、灯光、氛围、色彩、妆造）
- **角色参考图**保证角色面貌/身材一致性
- 两者结合：分镜图提供整体视觉定义，人物参考保证角色不崩

### 与 Path A/B 的区别

| 路径 | 一致性来源 | 场景控制力 | 适用场景 |
|------|-----------|-----------|---------|
| Path A (Omni) | image_list 参考图 | 弱（prompt控制） | 快速生成、人物一致性优先 |
| Path B (Gemini→Kling) | 分镜图 | 强 | 场景精确控制，但角色可能崩 |
| **Path C (V3-Omni)** | **分镜图 + image_list** | **强** | **两者兼顾（推荐）** |

### Stage 1: 生成分镜图

```bash
python vico_tools.py image \
  --prompt "Cinematic realistic start frame.\nReferencing...\nScene: ...\nLighting: ...\nStyle: ..." \
  --reference <角色参考图> \
  --output generated/frames/{shot_id}_frame.png
```

**Image Prompt 结构**：
```
Cinematic realistic start frame.

Referencing the facial features, face shape, skin tone, and clothing details of:
- image_1: {角色1外貌描述}
- image_2: {角色2外貌描述}

Scene: {具体场景描述}
Location details: {环境细节}

{角色1}: {姿态}, {表情}
{角色2}: {姿态}, {表情}

Shot scale: {wide/medium/close-up}
Camera angle: {eye-level/high/low}
Lighting: {灯光描述}
Color grade: {色调}

Style: {cinematic realistic/film grain/etc.}
```

### Stage 2: V3-Omni 生成视频

```bash
python vico_tools.py video \
  --backend kling-omni \
  --image generated/frames/{shot_id}_frame.png \
  --image-list <角色参考图> \
  --prompt "Referencing {shot_id}_frame composition...\nMotion sequence...\nDialogue..." \
  --audio --output output.mp4
```

**Video Prompt 结构**：
```
Referencing the {frame_name} composition.

{角色1}'s appearance and positioning from {frame_name}.
{角色2}'s appearance and positioning from {frame_name}.

Overall: {整体动作描述}

Motion sequence ({duration}s):
{time_range_1}: {character} {action}{, with lip-synced dialogue}
{time_range_2}: {action}
...

Dialogue exchange:
- {speaker} ({emotion}): "{line}"
- {speaker} ({emotion}): "{line}"

Camera movement: {static/pan/tracking/etc.}
Sound effects: {声音设计}

Style: Cinematic realistic style. No music, no subtitles.
```

### V3-Omni Storyboard 标注

```json
{
  "shot_id": "scene1_shot1",
  "duration": 7,
  "workflow_version": "v3_omni_v1",
  "storyboard": {
    "chinese_description": "连续动作与对话...",
    "shot_scale": "全景",
    "location": "男洗手间门口过渡区",
    "dialogue_segments": [
      {"time": "0-2s", "speaker": "初月", "line": "可以，我承认...", "emotion": "尴尬赔笑"}
    ],
    "transition": "cut"
  },
  "frame_generation": {
    "output_key": "scene1_shot1_frame",
    "prompt": "Cinematic realistic start frame...",
    "character_refs": ["Element_Chuyue", "Element_Jiazhi"],
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
      {"time": "0-2s", "action": "steps back...", "character": "Element_Chuyue"},
      {"time": "2-5s", "action": "three-way dialogue", "lip_sync": true}
    ],
    "camera_movement": "static wide shot",
    "sound_effects": "shuffling footsteps on tile"
  }
}
```

---

## 路径 B：Kling + Gemini 首帧（传统）

⚠️ **核心原则**：参考图是**样貌参考图**，只取面部/体态特征，**不能直接做 img2video 首帧**。参考图中的场景、服饰、姿态都是干扰。

```
人物参考图 → Gemini 生成分镜图（指定场景/服饰/姿态）→ img2video（Kling普通版）
```

**注意**：此路径生成的首帧作为普通 Kling img2video 的输入，**不使用** Omni 的 image_list 功能。角色一致性不如 Path C。

### 单人镜头

**Step 1**：Gemini 基于参考图生成分镜图

```bash
python vico_tools.py image \
  --prompt "小美（25岁亚洲女性，黑色长直发，瓜子脸）坐在咖啡馆窗边，抬头微笑，下午阳光，电影感，竖屏9:16构图" \
  --reference <参考图路径> \
  --output generated/storyboard/scene1_shot2_frame.png
```

**Step 2**：分镜图做 img2video

```bash
python vico_tools.py video \
  --image generated/storyboard/scene1_shot2_frame.png \
  --prompt "小美抬头看向服务生，温柔微笑着说：'这里真的很安静，我很喜欢。'" \
  --backend kling --audio \
  --output generated/videos/scene1_shot2.mp4
```

### 双人/多人镜头

**Step 1**：Gemini 多参考图合成一张分镜图（**参考图顺序很重要，重要人物放后面**）

```bash
python vico_tools.py image \
  --prompt "小美和小明并肩走在街道上，温暖的金色光线，竖屏9:16构图" \
  --reference <次要人物参考图> <主要人物参考图> \
  --output generated/storyboard/scene2_shot1_frame.png
```

**Step 2**：合成图做 img2video

### Kling 路径 Storyboard 标注

```json
{
  "shot_id": "scene1_shot2",
  "generation_mode": "img2video",
  "generation_backend": "kling",
  "frame_strategy": "first_frame_only",
  "image_prompt": "小美坐在咖啡馆窗边，抬头微笑，竖屏9:16构图",
  "video_prompt": "小美抬头看向服务生，温柔微笑...",
  "reference_personas": ["小美"]
}
```

---

## Gemini Prompt 注意事项

必须包含：
- 人物身份标识 + 外貌特征（与参考图对应）
- 场景描述（当前分镜的场景，非参考图场景）
- 服饰描述（可能与参考图不同）
- 光影氛围
- **画面比例**（竖屏9:16构图）

**示例**：
```
Reference for 小美: MUST preserve exact appearance - 25岁亚洲女性，黑色长直发，瓜子脸
小美坐在温馨的咖啡馆窗边，穿着米色针织衫，下午阳光透过窗户洒进来，
电影感色调，浅景深虚化背景，竖屏构图，9:16画面比例，人物位于画面中央
```
