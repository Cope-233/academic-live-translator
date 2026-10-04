# Academic Live Translator

**简体中文** | [English](./README.en.md)

**beta 0.6 · WebUI · Portable 安装模式**

Academic Live Translator 是一个本地优先的实时语音转录、翻译与学术记录 WebUI，适用于课堂、研讨会、学术会议、日常会议、访谈以及已有音视频材料。

> Beta 阶段统一使用 `beta x.y` 作为版本标识；首个稳定版本发布后再开始使用正式语义化版本号。

## Windows 一键安装

### 最简单：双击

```text
install.bat
```

或者直接双击：

```text
start_webui.bat
```

如果 beta 0.6 尚未完成初始化，`start_webui.bat` 会自动执行完整安装，然后启动 WebUI。

安装脚本会自动：

1. 在项目目录创建 `.venv/`；
2. 安装 Python 依赖；
3. 下载全部五种 Faster-Whisper 模型：`tiny`、`base`、`small`、`medium`、`large-v3-turbo`；
4. 将模型保存在 `models/faster-whisper/<模型名>/`；
5. Windows 检测到 NVIDIA GPU 时，下载项目专用的 CUDA 12 cuBLAS / cuDNN Runtime；
6. 将 GPU Runtime 解压到 `runtime/cuda12/bin/`，不会修改系统级 CUDA 安装；
7. 运行 Whisper CPU / int8 的真实推理自检；
8. 如存在 NVIDIA Runtime，再运行 CUDA / float16 的真实推理自检。

> 完整安装包含五个 Whisper 模型以及可选 CUDA Runtime，需要数 GB 磁盘空间和下载流量。五个模型本身约 4 GB，完整项目建议预留至少 6 GB 可用空间。

Windows CUDA Runtime 使用 Faster-Whisper 官方文档所推荐的 Windows 本地库方案，来源为 [Purfview/whisper-standalone-win 的 cuBLAS/cuDNN bundle](https://github.com/Purfview/whisper-standalone-win/releases/tag/libs)。

## macOS 安装（Apple silicon）

在 M1、M2、M3 或 M4 Mac 上打开终端，进入项目目录后运行：

```bash
chmod +x start_webui.sh
./start_webui.sh
```

启动脚本会检测 Apple 芯片和 Python 架构，在项目目录创建 `.venv/`，并自动安装适配 arm64 的 MLX Whisper。首次启动会准备当前配置的默认模型（默认 `base`），并分别执行 Apple GPU / Metal 与 CPU 推理自检。首次下载后，模型保存在项目目录中。MLX 使用 [Apple 的 MLX Whisper 实现](https://github.com/ml-explore/mlx-examples/tree/main/whisper) 和 [MLX Community 转换的模型](https://huggingface.co/mlx-community/whisper-base-mlx)。

在 `设置 → ASR Provider → 设备` 中可以选择：

- **自动**：M 系列 Mac 使用 MLX / Metal；Windows 检测到 NVIDIA GPU 时使用 CUDA；其他情况使用 CPU。
- **CPU**：使用 Faster-Whisper / CTranslate2。
- **Apple silicon GPU（MLX / Metal）**：仅在 M 系列 Mac 上显示。

切换到其他 Whisper 型号时会自动下载对应平台的模型。Intel Mac 和 Linux 只显示自动与 CPU 选项。若 M 系列 Mac 提示 Python 架构不匹配，请安装 arm64 版本的 Python，删除项目内 `.venv/` 后重新运行启动脚本。

## 启动

完成安装后，推荐双击：

```text
start_webui.bat
```

也可以使用 PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start_webui.ps1
```

WebUI 默认地址：

```text
http://127.0.0.1:8765
```

## Portable 目录结构

应用自身产生或下载的运行数据默认集中在项目目录，不写入 AppData：

```text
academic-live-translator/
├─ .venv/                     # 项目 Python 环境
├─ data/
│  ├─ config.json
│  ├─ sessions/
│  └─ assets/                 # 录音与截图
├─ models/
│  └─ faster-whisper/
│     ├─ tiny/
│     ├─ base/
│     ├─ small/
│     ├─ medium/
│     └─ large-v3-turbo/
│  └─ mlx-whisper/           # Apple silicon 上使用的 MLX 模型
│     └─ base/
├─ runtime/
│  └─ cuda12/
│     └─ bin/                 # Windows NVIDIA 用户的本地 CUDA/cuDNN DLL
├─ cache/
│  ├─ huggingface/
│  ├─ pip/
│  ├─ downloads/
│  └─ temp/
├─ logs/
├─ app/
├─ static/
├─ install.bat
├─ install.ps1
├─ start_webui.bat
└─ start_webui.ps1
```

`.venv/`、`data/`、`models/`、`runtime/`、`cache/` 与 `logs/` 都不会提交到 Git。

## 主要功能

- 实时双语转录工作区
- 本地 Whisper：tiny / base / small / medium / large-v3-turbo（Apple silicon 使用 MLX；其他平台使用 Faster-Whisper）
- Bing Free、Microsoft Translator 与 OpenAI-compatible 翻译
- llama.cpp、vLLM、LM Studio、LocalAI 等 OpenAI-compatible 服务
- 浏览器麦克风、标签页/屏幕音频、系统音频 + 麦克风混合
- Windows WASAPI 系统回环与原生麦克风
- 音频 / 视频文件转录
- 原文 / 翻译双栏同步滚动与自动跟随
- 实验性 Document Picture-in-Picture 置顶悬浮字幕窗
- 学术术语表与自定义术语
- Important / Question / Idea / Reference / Follow-up / Note 标记
- 屏幕/PPT截图
- Session Library 搜索与删除
- TXT、Markdown、SRT、JSON 导出

## 默认 Provider

### ASR：本地 Whisper

默认模型为 `base`。Windows 完整安装会提前准备全部五个 Faster-Whisper 模型。macOS Apple silicon 会为当前选中型号准备 MLX 和 CPU 模型；其他型号在首次选择时下载到项目目录。

自动模式在 Apple silicon 上使用 MLX / Metal，在 Windows NVIDIA 设备上使用 CUDA，否则使用 CPU。CPU 模式不需要 CUDA。Windows NVIDIA 用户通过一键安装获得项目目录内的 CUDA Runtime，推荐使用启动脚本运行，以便把 `runtime/cuda12/bin` 只加入当前应用进程的 DLL 搜索路径。

### 翻译：Bing Free（实验性）

Bing Free 无需 API Key，适合首次使用与轻量场景。它依赖非官方 Web 接口，因此仍标记为 Experimental。需要长期稳定部署时，可使用 Microsoft Translator 或 OpenAI-compatible 翻译服务。

## OpenAI-compatible Provider

例如 llama.cpp Router：

```text
ASR
Mode: OpenAI Chat Completions
Base URL: http://127.0.0.1:8080/v1
Model: <ASR model id>

Translation
Mode: OpenAI Chat Completions
Base URL: http://127.0.0.1:8080/v1
Model: <translation model id>
```

远程 ASR 通过 Chat Completions 的 `input_audio` 发送 WAV 音频，因此服务端需要支持对应的多模态音频输入格式。

## 悬浮窗（Experimental）

在较新的桌面 Chrome / Edge 中，可以通过 Document Picture-in-Picture 把原文与翻译放到 Zoom、WebEx、PPT 或网页课程上方。悬浮窗支持调整大小、自动跟随最新 Segment，并与主 WebUI 共用实时 Session。

> 悬浮窗只是显示层，请保持主 WebUI 标签页打开。

## Linux / Intel Mac

仍可使用：

```bash
chmod +x start_webui.sh
./start_webui.sh
```

Linux 与 Intel Mac 使用 CPU Whisper。支持浏览器麦克风、标签页/屏幕音频以及媒体文件工作流；Windows WASAPI 捕获、Windows CUDA bundle 和 Apple MLX 加速不适用。

## 从旧版升级

beta 0.6 继续使用 Portable-by-default 存储。已有 `data/config.json` 与 Session 可以继续使用。Windows 的 `cuda` 配置会在 Apple silicon 上自动映射到 MLX / Metal。

首次运行 beta 0.6 时，启动脚本会检测 `data/.installed-beta-0.6`；如果不存在，会执行对应平台的安装与推理自检。已有模型、配置、Session 和缓存不会删除。

## 开发

```bash
python -m venv .venv
# Windows
.venv\Scripts\python -m pip install -r requirements-dev.txt
pytest
```

CI 同时检查 Python 测试与 WebUI JavaScript 语法。

## License

本项目采用 MIT License，详见 [LICENSE](LICENSE)。
