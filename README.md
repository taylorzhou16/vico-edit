# Vico Edit - AI 视频剪辑 Skill

一个 Claude Code Skill，将 AI 视频剪辑能力带入你的对话中。

## 功能

- **素材分析**：自动识别图片/视频内容、场景、情感、色彩
- **创意生成**：交互式问题卡片，定制你的视频创意方案
- **分镜设计**：自动生成专业的分镜脚本和 Vidu Prompt
- **AI 视频生成**：支持首帧生图、参考生图、文生视频
- **AI 音乐生成**：Suno V4.5 背景音乐生成
- **统一剪辑**：转场、字幕、调色、变速、音频混合

## 安装

将 `SKILL.md` 复制到你的 Claude Code skills 目录：

```bash
mkdir -p ~/.claude/skills/vico-edit
cp SKILL.md ~/.claude/skills/vico-edit/
```

## 使用方法

```
/vico-edit <素材目录> [--duration <秒>] [--style <风格>]
```

### 示例

```bash
# 完整创作流程
/vico-edit ~/Videos/旅行素材/

# 指定时长和风格
/vico-edit ~/Photos/ --duration 30 --style travel_vlog

# 继续上次的项目
/vico-edit ~/vico-projects/trip_20260309/
```

## 工作流程

```
素材分析 → 创意生成 → 分镜设计 → 视频生成 → 音乐生成 → 剪辑输出
```

## API Key 配置

使用前需要准备：

| API | 用途 | 获取方式 |
|-----|------|----------|
| Vidu API Key | AI 视频生成 | [云雾 AI](https://yunwu.ai) |
| Suno API Key | AI 音乐生成 | [Suno](https://suno.ai) |

在运行时提供 API Key 即可，无需配置文件。

## 两种视频生成模式

| 模式 | 特点 | 适用场景 |
|------|------|----------|
| **首帧生图** | 图片就是第一帧，真实感强 | Vlog、旅行记录 |
| **参考生图** | 图片作为风格参考 | 创意视频、虚构内容 |

## 输出目录结构

```
~/vico-projects/{project_name}_{timestamp}/
├── state.json              # 项目状态
├── materials/              # 原始素材
├── analysis/analysis.json  # 素材分析结果
├── creative/creative_brief.json  # 创意方案
├── storyboard/storyboard.json     # 分镜脚本
├── generated/
│   ├── videos/             # AI 生成的视频
│   └── music/              # AI 生成的音乐
├── intermediate/           # 中间文件
└── output/
    └── {project_name}_final.mp4  # 最终视频
```

## 依赖

- FFmpeg 6.0+（视频处理）
- Python 3.9+（可选，用于节拍分析）

## License

MIT