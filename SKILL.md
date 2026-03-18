---
name: vico-edit
description: AI视频剪辑工具。分析素材、生成创意、设计分镜、执行剪辑。支持Vidu/Kling/Kling Omni视频生成、Suno音乐生成、TTS配音、FFmpeg剪辑。当用户要求制作视频、剪辑视频、生成视频、创建短片、或提供素材目录要求生成作品时触发。
argument-hint: <素材目录或视频文件>
---

# Vico-Edit 使用指南

**角色**：Director Agent — 理解创作意图、协调所有资源、交付视频作品。

**语言要求**：所有回复必须使用中文。

---

## 推荐配置

**建议使用多模态模型**（如 Claude Opus/Sonnet/Kimi-K2.5）以获得最佳体验。

非多模态模型会自动调用视觉模型进行图片分析，在 `config.json` 中配置 `VISION_BASE_URL`、`VISION_MODEL`、`VISION_API_KEY`。

---

## 核心理念

- **工具文件**：vico_tools.py（API 调用）和 vico_editor.py（FFmpeg 剪辑）是命令行工具
- **灵活规划，稳健执行**：规划阶段产出结构化制品，执行阶段由分镜方案驱动
- **优雅降级**：遇到问题时主动寻求用户帮助，而不是卡住流程

### 后端选择概览

| 后端 | 核心优势 | 推荐场景 |
|------|---------|---------|
| **Kling** (`kling`, 默认) | 首帧精确控制、画面质感好 | 大多数场景的首选 |
| **Kling Omni** (`kling-omni`) | image_list 多参考图、角色一致性最佳 | 有人物的剧情视频 |
| **Vidu** (`vidu`) | 稳定、快速 | 兜底、快速原型 |

详细后端对比和参考图策略：See [reference/backend-guide.md](reference/backend-guide.md)

---

## 快速启动流程

```
环境检查 → 素材收集 → 创意确认 → 分镜设计 → 执行生成 → 剪辑输出
   5秒        交互       交互        交互        自动        自动
```

### 工作流进度清单

```
Task Progress:
- [ ] Phase 0: 环境检查（python vico_tools.py check）
- [ ] Phase 1: 素材收集（扫描 + 视觉分析 + 人物识别）
- [ ] Phase 2: 创意确认（问题卡片交互）
- [ ] Phase 3: 分镜设计（生成 storyboard.json + 用户确认）
- [ ] Phase 4: 执行生成（API 调用 + 进度跟踪）
- [ ] Phase 5: 剪辑输出（拼接 + 转场 + 调色 + 配乐）
```

---

## Phase 0: 环境检查

```bash
python ~/.claude/skills/vico-edit/vico_tools.py check
```

- 基础依赖（FFmpeg/Python/httpx）不通过 → 停止并告知安装方法
- API key 未配置 → 记录状态，后续按需询问

---

## Phase 1: 素材收集

### 素材来源识别

- **目录路径** → 扫描目录中的图片/视频文件
- **视频文件** → 直接分析该视频
- **无参数** → 纯创意模式（无素材）

### 视觉分析流程（三级 fallback）

**Step 1**：使用 Read 工具读取图片。记录场景描述、主体内容、情感基调、颜色风格。

**Step 2**：Read 失败 → 调用内置 VisionClient：

```python
from vico_tools import VisionClient
client = VisionClient()
results = await client.analyze_batch(image_paths, "分析这些素材：场景、主体、颜色、氛围")
```

**Step 3**：VisionClient 也失败 → 主动询问用户描述每张素材内容。

### 人物识别（条件性）

**仅当用户提供了人物肖像图时触发**（不确定时询问用户）。

执行步骤：
1. 读取图片内容（不看文件名），识别所有人物
2. 询问用户确认每个人物的身份
3. 使用 PersonaManager 分别注册：

```python
from vico_tools import PersonaManager
manager = PersonaManager(project_dir)
manager.register("小美", "female", "path/to/ref.jpg", "长发、瓜子脸")
```

### 产出文件

创建项目目录 `~/vico-projects/{project_name}_{timestamp}/`，产出 `state.json`、`analysis/analysis.json`、`personas.json`（如有人物）。

---

## Phase 2: 创意确认

**使用问题卡片与用户交互**，一次性收集关键信息：

### 问题卡片设计

**问题 1: 视频风格**
- 选项：电影感 | Vlog风格 | 广告片 | 纪录片 | 艺术/实验
- 说明：决定调色、转场、配乐的整体基调

**问题 2: 目标时长**
- 选项：15秒（短视频）| 30秒（标准）| 60秒（长视频）| 自定义
- 说明：影响分镜数量和节奏

**问题 3: 画面比例**
- 选项：9:16（抖音/小红书）| 16:9（B站/YouTube）| 1:1（Instagram）
- 说明：根据发布平台选择

**问题 4: 配乐需求**
- 选项：AI生成BGM | 不需要配乐 | 我已有音乐
- 说明：是否需要 Suno 生成背景音乐

**问题 5: 旁白/字幕**

区分两种音频生成方式：

**A. 角色台词（同期声）**
- 由视频生成模型直接生成
- 需要在分镜的 video_prompt 中明确描述：角色、台词、情绪、语速、声音特质
- 视频生成时设置 `audio: true`

**B. 旁白/解说（后期配音）**
- 由 TTS 生成
- 用于场景解说、背景介绍、情感烘托
- 选项：不需要 | AI生成旁白 | 我已有文案

**重要原则**：能收同期声的镜头，都不要用后期 TTS 配音！

产出：`creative/creative.json`

---

## Phase 3: 分镜设计

根据素材和创意方案生成分镜脚本。

### 核心结构

Storyboard 采用 `scenes[] → shots[]` 两层结构。每个 scene 包含叙事目标、空间设定、视觉风格；每个 shot 包含生成模式、prompt、时长、转场等。

**完整分镜规范**：See [reference/storyboard-spec.md](reference/storyboard-spec.md)
**Prompt 编写与一致性规范**：See [reference/prompt-guide.md](reference/prompt-guide.md)
**后端选择与参考图策略**：See [reference/backend-guide.md](reference/backend-guide.md)

### 关键设计原则

1. 总时长 = 目标时长（±2秒），单镜头 2-5 秒
2. 同一分镜内最多 1 个动作，禁止空间变化
3. 所有 video_prompt 必须包含比例信息
4. 台词必须融入 video_prompt（角色 + 内容 + 情绪 + 声音）
5. 人物镜头每次都要写完整外貌描述

### 展示给用户确认（强制步骤）

**必须在用户明确确认后才能进入 Phase 4！** 展示每个镜头的生成模式、prompt、时长、转场等，提供确认/修改/取消选项。

产出：`storyboard/storyboard.json`

---

## Phase 4: 执行生成

### API Key 管理

首次调用时检查并请求 API key，用户提供后通过 `export` 设置。

### 执行规则

1. **首次 API 调用单独执行**，确认成功后再并发
2. **并发不超过 3 个** API 生成调用
3. **实时更新 state.json** 记录进度
4. **失败时重试** 最多 2 次，然后询问用户

### 生成模式强制执行

必须严格按照 storyboard.json 中的 `generation_mode` 执行，禁止擅自更改。

**工具调用详细参数**：See [reference/api-reference.md](reference/api-reference.md)

---

## Phase 5: 剪辑输出

### 视频参数校验

拼接前自动检查分辨率/编码/帧率，不一致时自动归一化（1080x1920 / H.264 / 24fps）。

```bash
python ~/.claude/skills/vico-edit/vico_editor.py concat --inputs video1.mp4 video2.mp4 --output final.mp4
```

### 合成流程

1. **拼接** → 按分镜顺序连接（自动归一化）
2. **转场** → 添加镜头间转场效果
3. **调色** → 应用整体调色风格
4. **配乐** → 混合背景音乐
5. **输出** → 生成最终视频

---

## 工具调用速查

```bash
# 环境检查
python ~/.claude/skills/vico-edit/vico_tools.py check

# 视频生成（自动选择后端）
python ~/.claude/skills/vico-edit/vico_tools.py video --prompt <描述> --output <输出>

# 音乐 / TTS / 图片
python ~/.claude/skills/vico-edit/vico_tools.py music --prompt <描述> --output <输出>
python ~/.claude/skills/vico-edit/vico_tools.py tts --text <文本> --output <输出>
python ~/.claude/skills/vico-edit/vico_tools.py image --prompt <描述> --output <输出>

# 剪辑
python ~/.claude/skills/vico-edit/vico_editor.py concat --inputs <视频列表> --output <输出>
python ~/.claude/skills/vico-edit/vico_editor.py mix --video <视频> --bgm <音乐> --output <输出>
python ~/.claude/skills/vico-edit/vico_editor.py transition --inputs <v1> <v2> --type <类型> --output <输出>
python ~/.claude/skills/vico-edit/vico_editor.py color --video <视频> --preset <预设> --output <输出>
```

**完整 CLI 参数和环境变量**：See [reference/api-reference.md](reference/api-reference.md)

---

## 文件结构

```
~/vico-projects/{project_name}_{timestamp}/
├── state.json           # 项目状态
├── materials/           # 原始素材
├── analysis/
│   └── analysis.json    # 素材分析
├── creative/
│   └── creative.json    # 创意方案
├── storyboard/
│   └── storyboard.json  # 分镜脚本
├── generated/
│   ├── videos/          # 生成的视频
│   └── music/           # 生成的音乐
└── output/
    └── final.mp4        # 最终视频
```

---

## 错误处理

| 问题 | 处理方式 |
|------|---------|
| 视觉分析失败 | VisionClient fallback → 询问用户 |
| API key 未配置 | 首次调用时询问 |
| API 调用失败 | 重试 2 次 → 询问用户 |
| 视频生成失败 | 尝试其他模式或用原始素材 |
| 音乐生成失败 | 生成静音视频并告知 |

---

## 依赖

- FFmpeg 6.0+
- Python 3.9+
- httpx
