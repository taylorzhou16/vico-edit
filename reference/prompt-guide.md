# Prompt 编写与一致性规范

## 目录

- 图片生成 Prompt（Gemini）
- 视频生成 Prompt（Kling/Vidu）
- 比例约束规范
- 人物一致性规范
- 物料/道具一致性规范
- 台词设计规范

---

## 图片生成 Prompt（Gemini）

必须包含五要素：

1. **场景描述**：时间、地点、环境
2. **主体描述**：人物外貌、服饰、姿态
3. **光影效果**：光线方向、色温、氛围
4. **画面风格**：cinematic / realistic / anime 等
5. **画面比例（强制）**：竖屏/横屏/正方形，具体比例

**示例**：

```
一位25岁的亚洲女性，黑色长发披肩，穿着米色针织衫，坐在窗边的木质椅子上，
下午三点的阳光从左侧窗户斜射进来，在墙面形成斑驳光影，温暖柔和的氛围，
电影感色调，浅景深虚化背景，竖屏构图，9:16画面比例，人物位于画面上三分之一下方
```

---

## 视频生成 Prompt（Kling/Vidu）

**必须使用中文编写**，包含以下要素：

1. **运镜描述**：推/拉/摇/移/跟/升降
2. **运动节奏**：缓慢/平稳/快速/急促
3. **画面稳定性**：保持稳定/轻微晃动/手持感
4. **比例保护（强制）**：明确说明"保持XX比例构图，不破坏画面比例"
5. **台词信息（如有）**：什么角色、说什么、什么情绪、什么语速

**示例**：

```
镜头缓慢推近，画面保持稳定，从远景慢慢推到女主角的中景。
女主角面向镜头说话，表情自然微笑，说着："这是我最喜欢的地方。"
声音温柔清澈，带着怀念的情绪，语速适中偏慢。
保持竖屏9:16构图，人物始终位于画面中央，不破坏画面比例。
```

---

## 比例约束规范（强制执行）

### 文生图 Prompt

- 9:16 → 必须包含："竖屏构图，9:16画面比例，人物/主体位于画面中央"
- 16:9 → 必须包含："横屏构图，16:9画面比例"
- 1:1 → 必须包含："正方形构图，1:1画面比例，主体居中"

### 图生视频 / 文生视频 Prompt

- 所有 video_prompt 必须确保运镜不破坏原始画面比例
- 9:16 竖屏：避免会导致画面变横的运镜描述
- text2video 必须同时设置正确的 `aspect_ratio` 参数

---

## 人物一致性规范

**每个包含人物的镜头，prompt 必须包含**：

### 1. 人物身份标识

使用统一的名字（如"小美"），在 prompt 中明确提及。

### 2. 外貌特征详细描述（每次都要写）

- 性别、年龄、ethnicity
- 发型（长度、颜色、造型）
- 面部特征（脸型、眼睛、鼻子、嘴巴）
- 体型（高矮胖瘦）
- 标志性特征（眼镜、痣、纹身等）

### 3. 服饰描述

衣服款式、颜色、材质、配饰等。

### Prompt 模板

```
{人物名字}，{性别}，{年龄}岁，{ethnicity}，
{发型详细描述}，{面部特征详细描述}，{体型描述}，
穿着{服饰详细描述}，
{场景描述}，{光影描述}，{比例信息}
```

### 跨镜头示例

镜头1：
```
小美，年轻亚洲女性，25岁左右，黑色长直发及腰，瓜子脸，大眼睛，高鼻梁，
身材苗条，穿着白色连衣裙，站在海边，日落时分的金色光线从侧面照射，
电影感色调，竖屏9:16构图
```

镜头3（小美再次出现）：
```
小美（与镜头1为同一人），年轻亚洲女性，25岁左右，黑色长直发及腰，瓜子脸，大眼睛，高鼻梁，
身材苗条，这次穿着白色连衣裙外面套了一件米色针织开衫，
坐在咖啡厅窗边，下午柔和的自然光，温暖舒适的氛围，
电影感色调，竖屏9:16构图
```

---

## 物料/道具一致性规范

跨镜头重复出现的重要道具，需要：

1. **建立物料清单**（在 storyboard 的 `props` 字段中）
2. **每个相关镜头的 prompt 包含完整描述**
3. **关键道具类型**：品牌 Logo、产品外观、剧情关键物品、场景标志性元素

---

## 台词设计规范

### 台词语言标注

每个含台词镜头必须标注 `dialogue_language`：中文/英文/日文等。

### 同期声 vs TTS

| 类型 | 生成方式 | 适用场景 |
|------|---------|---------|
| 同期声 | 视频生成模型（`audio: true`） | 角色对话、角色独白 |
| TTS 旁白 | TTS 后期配音 | 片头/片尾解说、场景描述、情感烘托 |

**核心原则**：能收同期声的镜头，不要用 TTS！

---

## V3-Omni Prompt 规范（三层结构）

针对 Kling V3-Omni 的**分镜图 + 视频**两阶段生成，需要分别编写 Image Prompt 和 Video Prompt。

### Image Prompt 规范（分镜图生成）

**用途**：控制整体视觉（场景、画风、灯光、氛围、色彩、妆造）

**结构**：
```
Cinematic realistic start frame.

[角色参考]
Referencing the facial features, face shape, skin tone, and clothing details of:
- image_1: {角色1外貌描述}
- image_2: {角色2外貌描述}

[场景描述]
Scene: {具体场景描述}
Location details: {环境细节}

[角色姿态]
{角色1}: {姿态}, {表情}
{角色2}: {姿态}, {表情}

[技术参数]
Shot scale: {wide/medium/close-up}
Camera angle: {eye-level/high/low}
Lighting: {灯光描述}
Color grade: {色调}

[风格定义]
Style: {cinematic realistic/film grain/etc.}
```

**示例**：

```
Cinematic realistic start frame.

Referencing the facial features, face shape, skin tone, and clothing details of:
- image_1: Chuyue, young Asian woman, long black hair, delicate features, wearing light grey blazer with ID badge
- image_2: Jiazhi, mature man, short hair, deep eyes, wearing black shirt with rolled sleeves
- image_3: Tianyu, young man, short hair, wearing light professional shirt

Scene: A wide three-person shot inside the men's restroom at the doorway transition zone
Location details: white tiles, sink and mirror visible in mid-ground, door frame as composition divider

Chuyue: stands in doorway, body half-outside, hands raised in flustered waving gesture, forced apologetic smile
Jiazhi: stands in background, upright and composed, neutral expression with hint of cool amusement
Tianyu: side-turned, ears visibly red, arms loose

Shot scale: Wide/Full shot
Camera angle: Eye-level, frontal
Lighting: Cold white fluorescent overhead lighting
Color grade: Cool blue-white

Style: Cinematic realistic, film grain, shallow depth of field, 16:9 aspect ratio
```

### Video Prompt 规范（视频生成）

**用途**：引用分镜图构图，叠加动作、对白、镜头运动

**结构**：
```
Referencing the {frame_name} composition.

[角色确认]
{角色1}'s appearance and positioning from {frame_name}.
{角色2}'s appearance and positioning from {frame_name}.

[整体动作]
Overall: {整体动作描述}

[分段动作]
Motion sequence ({duration}s):
{time_range_1}: {character} {action}{, with lip-synced dialogue}
{time_range_2}: {action}
...

[对白同步]
Dialogue exchange:
- {speaker} ({emotion}): "{line}"
- {speaker} ({emotion}): "{line}"

[技术参数]
Camera movement: {static/pan/tracking/etc.}
Sound effects: {声音设计}

Style: Cinematic realistic style. No music, no subtitles.
```

**示例**：

```
Referencing the Shot_Chuyue_Retreat_frame composition.

Element_Chuyue's appearance and positioning from Shot_Chuyue_Retreat_frame.
Element_Jiazhi's appearance and positioning from Shot_Chuyue_Retreat_frame.
Element_Tianyu's appearance and positioning from Shot_Chuyue_Retreat_frame.

Overall: Chuyue fumbles backward out the doorway while delivering awkward running apology, sparking three-way exchange that ends with deflecting compliment

Motion sequence (7s):
0-2s: Element_Chuyue steps back past threshold in clumsy hurried motion, both hands raised chest-high in frantic waving gesture, fingers spread, palms partially outward, face showing forced manic apologetic smile
2-5s: three-way dialogue exchange, Chuyue speaks rapidly then Tianyu cuts back, with lip-synced dialogue
5-7s: Element_Chuyue catches herself, voice softening into barely-held laugh, finishing line, with lip-synced dialogue

Dialogue exchange:
- Chuyue (尴尬赔笑): "可以，我承认，today is on me。我职业素养很高的，绝不乱说。"
- Tianyu (flat, cutting back): "那你别一脸见鬼。"
- Chuyue (voice softening into barely-held laugh): "不是见鬼，是见……见真爱。"

Camera movement: static wide shot, eye-level frontal — all three characters in frame throughout
Sound effects: shuffling footsteps on tile, ambient restroom hum

Cinematic realistic style. No music, no subtitles.
```

### 关键要点

**Image Prompt**：
- 必须包含角色参考（image_1, image_2...）
- 必须包含画面比例（16:9 / 9:16）
- 场景、灯光、相机参数要详细

**Video Prompt**：
- 必须引用分镜图（Referencing XXX_frame composition）
- 动作必须分段描述（0-2s, 2-5s...）
- 对白必须标注情绪和 lip-sync
- 声音设计单独列出
