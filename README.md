# Academic Live Translator

[简体中文](./README.md) | [English](./README.en.md)

**beta01 · WebUI · 默认便携模式**

Academic Live Translator 是一个本地优先的 WebUI，用于实时语音转录、翻译与学术场景记录。它面向课堂、研讨会、学术会议、日常会议、访谈以及已有音视频材料等使用场景。

> 本项目目前处于 Beta 阶段。预发布版本统一使用 `betaXX` 作为版本标识；首个稳定版本发布后再开始使用正式的语义化版本号。

## 主要功能

- 实时双语转录工作区
- WebUI 默认中文，可在 Settings 中切换中文 / English
- 支持浏览器麦克风、浏览器标签页/屏幕音频、Windows WASAPI 系统音频回环以及音视频文件输入
- 学术术语表 Profile 与自定义术语
- Important / Question / Idea / Reference / Follow-up / Note 等学术标记
- 课程 PPT / 屏幕截图记录
- 支持全文搜索与删除的 Session Library
- 支持导出 TXT、Markdown、SRT 与 JSON
- 默认使用本地 Faster-Whisper 进行 ASR
- 首次使用可选择无需 API Key 的 Bing Free 翻译（实验性）
- 支持 Microsoft Translator 与通用 OpenAI-compatible Provider
- llama.cpp、vLLM、LM Studio、LocalAI 等服务均可通过 OpenAI-compatible 接口接入

## 默认 Portable 存储

应用自身的运行数据默认**不会写入 AppData**。Academic Live Translator 创建或下载的内容会集中保存在项目目录中：

```text
academic-live-translator/
├─ .venv/              # Python 虚拟环境
├─ data/
│  ├─ config.json
│  ├─ sessions/
│  └─ assets/          # 录音与截图
├─ models/
│  └─ faster-whisper/  # 自动下载的本地 ASR 模型
├─ cache/
│  ├─ huggingface/
│  ├─ pip/
│  └─ temp/
├─ logs/
├─ app/
├─ static/
└─ start_webui.ps1
```

这些运行时目录都已加入 `.gitignore`，因此个人转录记录、录音、截图、模型文件以及缓存不会被意外提交到 Git 仓库。

如果需要自定义存储位置，可以使用 `ALT_DATA_DIR`、`ALT_MODELS_DIR`、`ALT_CACHE_DIR` 或 `ALT_LOGS_DIR` 环境变量覆盖默认路径。

## 前置条件

- Python 3.11–3.13
- 如需原生 WASAPI 系统音频捕获，需要 Windows 10/11
- 浏览器音频捕获推荐使用 Chrome / Edge
- 推荐安装 FFmpeg，用于媒体格式转换与 FLAC 录音
- GPU 不是必需条件。默认的 Faster-Whisper `base` 模型可以直接使用 CPU 运行

## Windows 快速开始

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start_webui.ps1
```

启动脚本会自动：

1. 在项目目录中创建 `.venv/`；
2. 使用项目内的 pip 缓存安装依赖；
3. 首次运行时将默认 Faster-Whisper 模型下载到 `models/faster-whisper/`；
4. 启动 WebUI：`http://127.0.0.1:8765`。

只要 PowerShell 中能够执行 `python`，启动脚本即可同时兼容普通 Python 安装和 Conda 环境。

## Linux / macOS 快速开始

```bash
chmod +x start_webui.sh
./start_webui.sh
```

Linux/macOS 暂不支持 Windows 原生 WASAPI 系统音频捕获，但浏览器麦克风、标签页/屏幕音频捕获以及 Media 文件处理功能仍然可以使用。

## 默认 Provider

### ASR：Local Faster-Whisper

默认模型为 `base`，首次启动时自动下载。之后可以在 Settings 中切换为 `tiny`、`small`、`medium` 或 `large-v3-turbo`。

### 翻译：Bing Free（实验性）

该选项不需要 API Key，主要用于降低首次部署和测试门槛。它依赖非官方 Web 接口，因此如果 Bing 调整前端接口，功能可能暂时失效。

如果需要长期、稳定使用，建议切换到 Microsoft Translator 或 OpenAI-compatible 翻译服务。

## OpenAI-compatible Provider

ASR 与翻译都可以使用兼容 OpenAI Chat Completions 的服务。例如，当 llama.cpp Router 同时托管多个模型时，ASR 和翻译可以共用同一个 Base URL：

```text
ASR
Base URL: http://127.0.0.1:8080/v1
Model: <ASR model id>
Mode: OpenAI Chat Completions

Translation
Base URL: http://127.0.0.1:8080/v1
Model: <translation model id>
Mode: OpenAI Chat Completions
```

远程 ASR 通过 Chat Completions 的 `input_audio` 发送音频。因此所接入的 OpenAI-compatible 服务需要支持多模态音频输入。

## 实时音频输入

当前支持：

- 浏览器麦克风
- 浏览器标签页 / 屏幕音频
- 浏览器系统音频 + 麦克风混合
- Windows WASAPI 系统音频回环
- Windows 原生麦克风
- 音频 / 视频文件

对于 Windows 上通过 Chrome、Zoom、Teams、VLC 等播放的在线课程，通常推荐使用 WASAPI loopback。它直接捕获系统数字音频流，即使使用耳机也无需让麦克风重新录制扬声器声音。

## 语言

WebUI 默认使用中文，可在 `Settings → 界面 → 语言` 中切换为 English，设置会自动保存。

目标翻译语言目前提供中文、English、日本語、한국어、Français、Deutsch、Español 与 العربية。Malay 仍可作为源语言使用，但不再列为默认目标语言。

## 学术工作流

在实时 Session 中，你可以：

- 同时查看原始转录与翻译；
- 使用学术术语 Profile 或自定义术语；
- 将内容标记为 Important、Question、Idea、Reference、Follow-up 或 Note；
- 截取当前屏幕并作为课程/PPT快照保存；
- 保存 Session 音频；
- 将完整 Session 导出为 Markdown、TXT、SRT 或 JSON。

## 从旧版迁移

`beta01` **不会自动复用** v0.1 / v0.2 / v0.3 曾经位于 AppData 中的数据目录。这样可以避免不同版本之间意外共享 Session，同时避免应用数据隐藏占用系统盘。

现有 beta01 中使用旧 ASR 模式名称的配置会自动迁移到统一的 `OpenAI Chat Completions` 模式；旧的 Malay 目标语言会回退为中文。

## 开发

```bash
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements-dev.txt
# Linux/macOS: .venv/bin/python -m pip install -r requirements-dev.txt
pytest
```

CI 同时执行 Python 测试与 `node --check static/app.js`，用于拦截 WebUI JavaScript 语法错误。

## License

本项目采用 MIT License，详见 [LICENSE](LICENSE)。
