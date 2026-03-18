# 后端选择与参考图策略

## 目录

- 三种后端能力对比
- 后端选择决策树
- 自动选择逻辑
- 人物参考图两条路径
- 路径 A：Kling Omni（角色一致性优先）
- 路径 B：Kling + Gemini 首帧（场景精确度优先）
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

**核心权衡：人物一致性 vs 场景精确度**

```
镜头是否包含人物？
├── 是 → 是否有注册的人物参考图？
│        ├── 是 → 哪个优先级更高？
│        │        ├── 人物一致性优先 → kling-omni + image_list
│        │        └── 场景精确度优先 → kling + Gemini 生首帧
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
| 有人物参考图，要保持一致 | **kling-omni** | `--image-list ref.jpg` |
| 需要精确首帧画面 | **kling** | `--image first_frame.png` |
| 需要首尾帧动画 | **kling** | `--image first.png --tail-image last.png` |
| 多镜头剧情 + 角色一致 | **kling-omni** | `--image-list ref.jpg --multi-shot` |
| 简单无人场景 / 快速原型 | **kling**（默认）或 vidu | 无需特殊参数 |

---

## 自动选择逻辑

未指定 `--backend` 时默认使用 **kling**。特殊参数会强制切换后端：
- 提供 `--image-list` → 自动切换到 kling-omni（唯一支持）
- 提供 `--tail-image` → 保持 kling（唯一支持）
- 需要快速兜底 → 手动指定 `--backend vidu`

---

## 人物参考图两条路径

**仅当已注册人物参考图时考虑。**

| | Kling Omni 路径 | Kling + Gemini 路径 |
|---|---|---|
| **流程** | 参考图 → Kling Omni `--image-list` | 参考图 → Gemini 生分镜图 → Kling img2video |
| **优势** | 路径简单，无需中间步骤 | 画面质感好，场景精确可控 |
| **一致性** | 同一参考图多镜头自动一致 | 多镜头间一致性难保证 |
| **适用** | 人物一致性优先的剧情视频 | 需要精确构图/场景控制 |

**选择建议**：人物一致性优先 → **Kling Omni**（推荐）；场景精确度优先 → **Kling + Gemini**

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

## 路径 B：Kling + Gemini 首帧

⚠️ **核心原则**：参考图是**样貌参考图**，只取面部/体态特征，**不能直接做 img2video 首帧**。参考图中的场景、服饰、姿态都是干扰。

```
人物参考图 → Gemini 生成分镜图（指定场景/服饰/姿态）→ img2video
```

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
