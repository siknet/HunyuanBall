# 混元球（HyBall） V2.0.1
## 因为Github限制，请直接下载右侧发行包。 
一个基于 `llama.cpp` + `Vulkan` 的腾讯混元翻译大模型本地服务端，特性：

* 支持沉浸式翻译
* OpenAI 兼容 API
* 本地离线翻译
* 低资源占用
* 显卡加速

默认内置腾讯混元官方翻译模型：

`Hy-MT2-1.8B-Q4_K_M.gguf`

支持 AMD / NVIDIA 显卡 Vulkan 加速，同时兼容纯 CPU 模式。

---

# 项目特点

* 基于最新腾讯混元翻译模型 `Hy-MT2`
* OpenAI Compatible API
* 支持沉浸式翻译等插件接入
* Vulkan 显卡加速（支持 A 卡 / N 卡）
* 低资源占用
* 本地离线运行
* 自带简易 WebUI
* 无需 CUDA 环境
* 默认开箱即用

---

# 模型说明

本项目默认使用：

`Hy-MT2-1.8B-GGUF`

官方说明：

> Hy-MT2 是一款面向真实复杂场景的“快思考”多语言翻译模型家族，涵盖 1.8B、7B 和 30B-A3B（MoE）三种体量，支持 33 种语言互译并具备强大的多语言指令遵循能力。
>
> 在端侧部署上，得益于 AngelSlim 1.25-bit 极端量化，其 1.8B 模型仅需 440MB 存储空间，推理速度显著提升 1.5 倍。
>
> 多维度评测表明，Hy-MT2 在通用、真实业务、专业领域及指令遵循等翻译任务中表现卓越。

---

# 测试环境

硬件环境：

* CPU：AMD Ryzen 7 3700X
* GPU：RTX 3070 8GB
* 内存：32GB

测试结果：

| 模式        | 推理速度          |
| --------- | ------------- |
| CPU 模式    | ~20 token/s   |
| Vulkan 模式 | ~200 token/s  |
| CUDA 模式   | 与 Vulkan 基本一致 |

由于 Vulkan 模式性能与 CUDA 接近，同时具备更好的兼容性，因此程序默认仅提供：

* Vulkan 模式
* CPU 模式

默认使用 Vulkan 模式。

---

# Vulkan 模式说明

Vulkan 模式支持：

* NVIDIA 显卡
* AMD 显卡
* Intel 显卡（部分）

无需安装 CUDA Toolkit。

程序默认优先使用 Vulkan 显卡加速。

---

# WebUI 模式

程序内置一个简易 WebUI，调用办法：右键点击桌面右下角系统托盘图标，点击“启动WebUI”菜单。提供简单的服务：

* 临时测试
* API 调试
* 简单翻译

但更推荐搭配如下插件或客户端使用：

* 沉浸式翻译
* Cherry Studio
* OpenAI Compatible 客户端



---

# 沉浸式翻译接入教程

## 1. 启动程序

打开主程序后：

点击：

`启动`

等待下方：

`API 状态`

显示运行成功。

默认 API 地址通常为：

```text
http://127.0.0.1:58088/v1
```

---

## 2. 打开沉浸式翻译设置

进入：

`翻译服务`

右击右上角：

`添加自定义翻译服务`

选择：

`OpenAI`

---

## 3. 填写参数

### API Key

```text
123
```

（可随意填写）

---

### 自定义翻译服务名称

例如：

```text
混元球
```

---

### 自定义 API 接口地址

在程序主窗口中点击 API 地址复制。

最终填写：

```text
http://127.0.0.1:58088/v1/chat/completions
```

如果修改了端口，请对应修改。

---

## 4. 测试服务

点击：

`点此测试服务`

如果出现绿色勾选，则说明模型工作正常。

---

## 5. 设置默认翻译服务

在左侧服务列表中找到：

`混元球`

点击：

`设为默认`

即可开始使用。

---

# 模型切换

程序默认内置：

`Hy-MT2-1.8B-Q4_K_M.gguf`

如果需要更高翻译精度，可自行下载更高量化版本。

下载后：

在程序设置面板：

`GGUF 模型路径`

中指定新的模型文件即可。

---

# 推荐模型下载

建议使用迅雷下载。

## Q6 精度版本（推荐）

```text
Hy-MT2-1.8B-Q6_K
```

[https://huggingface.co/tencent/Hy-MT2-1.8B-GGUF/blob/main/Hy-MT2-1.8B-Q6_K.gguf](https://huggingface.co/tencent/Hy-MT2-1.8B-GGUF/blob/main/Hy-MT2-1.8B-Q6_K.gguf)

---

## Q8 高精度版本

```text
Hy-MT2-1.8B-Q8_0
```

[https://huggingface.co/tencent/Hy-MT2-1.8B-GGUF/blob/main/Hy-MT2-1.8B-Q8_0.gguf](https://huggingface.co/tencent/Hy-MT2-1.8B-GGUF/blob/main/Hy-MT2-1.8B-Q8_0.gguf)

---

# 模型精度说明

翻译质量：

```text
Q8 > Q6 > Q4
```

对应：

| 量化 | 特点         |
| -- | ---------- |
| Q4 | 体积最小、速度最快  |
| Q6 | 推荐，精度与速度平衡 |
| Q8 | 精度最高，占用更大  |

---

# 默认参数

程序默认使用：

| 参数          | 默认值    |
| ----------- | ------ |
| Backend     | Vulkan |
| Context     | 4096   |
| Batch Size  | 512    |
| GPU Layers  | 99     |
| Temperature | 0.1    |
| Top-p       | 0.7    |
| CPU threads      | 2   |
这些参数已经针对翻译任务进行了优化。

---

# OpenAI Compatible API

程序兼容 OpenAI API 格式。

默认接口：

```text
http://127.0.0.1:58088/v1/chat/completions
```

可接入：

* 沉浸式翻译
* Cherry Studio
* Open WebUI
* SillyTavern
* AnythingLLM
* 其他 OpenAI Compatible 工具

---

# 注意事项

* 首次启动可能需要数秒载入模型
* 若端口被占用，请修改 API 端口
* CPU 模式速度较慢，仅建议无独显环境使用
* Vulkan 模式推荐显卡显存 ≥ 4GB
* 若模型翻译质量不够理想，可尝试切换更高精度量化版本

---

# 致谢

* llama.cpp
* 腾讯混元
* Vulkan
* 沉浸式翻译
* Deepseek 
* Reasonix
