# 混元球 v1.01（本地翻译 API + WebUI）

这是一个在 Windows 10/11 上本地运行的翻译服务：
- 后端：`llama-server`（OpenAI 兼容 API）
- 前端：内置 WebUI（浏览器访问）
- 模型：腾讯Hunyuan-MT-1.5-1.8B GGUF（纯 CPU 可跑）

适用场景：
- 给「沉浸式翻译」提供本地翻译 API
- 翻译网页全文、油管字幕等
- 不占显存，不依赖显卡（CPU 模式）

---

## 运行环境

- Windows 10 / Windows 11（64 位）
- **首次运行建议安装**：Microsoft Visual C++ Redistributable 2015–2022（x64）  
  官方下载：https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## 目录结构（发布包）

```

混元球/
├─ launcher.exe          # 主程序（托盘）
├─ _internal/            # 运行时依赖（不要删除）
├─ config.json           # 配置文件（可修改）
├─ llama/                # llama-server.exe + DLL
├─ webui/                # WebUI 静态页面
├─ models/               # 放 GGUF 模型文件（用户自己拷）
└─ logs/                 # 日志输出

````

---

## 快速开始

1. 把模型文件（`.gguf`）放到 `models/` 目录  
   例如：`models/HY-MT1.5-1.8B-Q4_K_M.gguf`

2. 双击运行 `launcher.exe`  
   程序会在右下角托盘出现图标。

3. 如果开启了 WebUI，本地浏览器访问（默认）：
   - 自带翻译界面：`程序文件夹/webui/index.html`
   - 标准OpenAI 格式 API地址：`http://127.0.0.1:58088/`

4. 在托盘菜单可以：
   - 开启/关闭 API（载入/卸载模型）
   - 打开 WebUI
   - 打开 logs 日志目录
## 🛠️ 接入沉浸式翻译 (Immersive Translate)

请按照以下步骤，将本地服务接入沉浸式翻译插件：

### 1. 开启自定义服务

打开沉浸式翻译插件的 **设置** -> 点击左侧边栏的 **“翻译服务”** -> 找到底部 **“添加自定义翻译服务”**选择 **“OpenAI”**。

### 2. 配置 OpenAI 接口

在弹出菜单中选择 **"OpenAI"**，并参照下方表格填写参数：

| 配置项目 | 填写内容 |
| --- | --- |
| **自定义名称** | `混元球 (HunyuanBall)` |
| **API KEY** | `hunyuan` |
| **自定义接口地址** | `http://127.0.0.1:58088/v1/chat/completions` |
| **每秒最大请求数** | `3` (若配置较高可调整至 4-8) |
| **每次请求最大长度** | `600` (若显存充裕可调整至 800-1200) |
| **每次请求最大段落** | `3` (若显存充裕可调整至 5-8) |

> [!TIP]
> * 如果你修改了程序的默认端口，请确保 **接口地址** 中的端口号同步更新。
> * 其他选项建议保持默认状态，以获得最稳定的翻译效果。
> 
> 

---

### 给用户的提示：

如果配置后无法正常翻译，请检查：

1. 本地服务程序是否已启动并正常运行。
2. 之前的 **Visual C++ 运行库** 是否已按要求安装完成（否则服务可能无法加载）。
3. 端口 `58088` 是否被其他程序占用。

---

## OpenAI 兼容 API 示例（测试连通性）

### Chat Completions
请求：
```bash
curl http://127.0.0.1:58088/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"local\",\"messages\":[{\"role\":\"user\",\"content\":\"把这句话翻译成英文：今天天气真好\"}],\"temperature\":0.2,\"max_tokens\":256}"
````

---

## 配置文件说明：config.json

推荐配置 `config.json` 示例：
在AMD 3600/3700X 上接入“沉浸式翻译”进行网页全屏翻译基本能达到1-3秒内出结果。
```json
{
  "model_path": "models\\HY-MT1.5-1.8B-Q4_K_M.gguf",
  "host": "127.0.0.1",
  "port": 58088,
  "threads": 2,
  "threads_batch": 2,
  "ctx": 1024,
  "batch": 256,
  "extra_args": ["--no-webui"],
  "autostart": true,
  "open_webui_on_ready": true,
  "show_tips": true
}
```

> 注意：Windows 路径可以用 `\\`（双反斜杠）或 `/` 都可以。
> 例如 `models/HY-MT1.5-1.8B-Q4_K_M.gguf` 也是 OK 的。

---

### 1) model_path（模型路径）

* 类型：字符串
* 作用：指定 GGUF 模型文件位置
* 支持：相对路径 / 绝对路径

  * 相对路径以 `launcher.exe` 所在目录为基准

示例：

```json
"model_path": "models\\HY-MT1.5-1.8B-Q4_K_M.gguf"
```

常见错误：

* 文件不存在 → 启动失败（请确认模型确实放在 `models/`）

---

### 2) host / port（API 监听地址与端口）

* 类型：字符串 / 数字
* 作用：决定 OpenAI 兼容 API 服务监听在哪里

推荐：

* 本机使用：`127.0.0.1`
* 局域网访问：可改成 `0.0.0.0`（允许同网段其它设备访问）
  ⚠️ 注意安全：局域网其它设备也能访问你的本地翻译服务。

示例：

```json
"host": "127.0.0.1",
"port": 58088
```

端口冲突：

* 如果 58088 被占用，改成其它未占用端口（例如 58100）

---

### 3) threads（推理线程数，对应 llama-server 的 -t）

* 类型：数字
* 对应参数：`-t`
* 作用：模型推理使用的 CPU 线程数（影响速度、也影响 CPU 占用）

建议值：

* 纯翻译场景，且你不想卡电脑：`1 ~ 4`
* Ryzen 3700X（8C16T）：

  * “舒服不卡”：`threads=1~2`
  * “追求速度”：`threads=4~8`（CPU 占用会明显增加）

示例：

```json
"threads": 2
```

---

### 4) threads_batch（批处理线程数，对应 llama-server 的 -tb）

* 类型：数字
* 对应参数：`-tb`
* 作用：主要影响“prompt 预处理/批量处理”的并行度

建议：

* 一般与 `threads` 相同即可
* 单核运行（想省资源）：两者都设 1

示例：

```json
"threads_batch": 2
```

---

### 5) ctx（上下文长度，对应 llama-server 的 -c）

* 类型：数字
* 对应参数：`-c`
* 作用：最大上下文窗口（越大越吃内存，也会更慢）

典型建议：

* 翻译网页/字幕：`1024 ~ 2048`
* 如果出现 “Context size has been exceeded”：说明请求太长
  解决思路：

  1. 降低沉浸式翻译“每次请求最大文本长度/段落数”
  2. 或适当提高 `ctx`（代价：更吃内存更慢）

示例：

```json
"ctx": 2048
```

---

### 6) batch（批大小，对应 llama-server 的 -b）

* 类型：数字
* 对应参数：`-b`
* 作用：影响吞吐/速度/内存占用

经验值（CPU 翻译场景）：

* 更稳、更省内存：`128 ~ 256`
* 追求吞吐：`256 ~ 512`
* 太大可能导致内存涨、甚至变慢（看 CPU/内存情况）

示例：

```json
"batch": 512
```

---

### 7) extra_args（额外传给 llama-server 的参数列表）

* 类型：数组（字符串列表）
* 作用：把你想额外传给 `llama-server.exe` 的命令行参数写这里

示例：

```json
"extra_args": ["--no-webui"]
```

说明：

* `--no-webui`：禁用 llama-server 自带 WebUI（推荐，使用我们自己的 WebUI）
* 你也可以加入其它 llama-server 参数，例如：

  * `--verbose`（输出更多日志，调试用）
  * 其它参数按你本机编译的 llama-server 支持项为准

---

### 8) autostart（启动程序后自动开启 API）

* 类型：布尔（true/false）
* 作用：运行 `launcher.exe` 后自动载入模型并开始提供 API 服务

示例：

```json
"autostart": true
```

推荐：

* 日常使用建议 `true`
* 调试/开发阶段也可以先设 `false`，手动从托盘菜单启动

---

### 9) open_webui_on_ready（模型就绪后自动打开 WebUI）

* 类型：布尔
* 作用：当模型加载完成并且 API 可用时，自动打开 WebUI 页面

示例：

```json
"open_webui_on_ready": true
```

说明：

* 如果你设置为 true，但浏览器没有弹出，通常是系统/浏览器策略导致前台窗口被抑制。
* 建议使用本项目的本地 WebUI URL（HTTP）方式以提高弹窗成功率。

---

### 10) show_tips（是否显示托盘气泡提示）

* 类型：布尔
* 作用：控制托盘提示气泡（启动中/已就绪/停止等提示）

示例：

```json
"show_tips": true
```

---

## 性能建议（翻译场景优先）

如果你主要用「沉浸式翻译」翻译网页全文：

* `threads=1~2`：基本够用且很稳
* `ctx=1024~2048`：网页段落一般足够
* `batch=256`：多数机器更均衡
* 沉浸式翻译里：

  * 每秒最大请求数：建议 1
  * 每次请求最大文本长度：600 左右更稳
  * 每次请求最大段落数：1（速度最快，也最稳定）

---

## 常见问题

### 1）启动后提示找不到模型

检查：

* `models/` 目录下是否真的有 `.gguf`
* `model_path` 是否写对（注意路径）

### 2）翻译网页很慢

通常原因：

* 同时并发请求太多（段落数太大、QPS 太高）
* 上下文太大（ctx 太大）
* batch 太大导致内存压力

建议：

* 沉浸式翻译：QPS=1、段落数=1、长度=600
* `threads=1~2`、`batch=256`

### 3）日志在哪里？

* `logs/launcher.log`：托盘程序日志
* `logs/llama-server.log`：模型服务日志

---

## 免责声明

本项目为本地工具，用户需自行确保模型与使用方式符合相关许可与法律法规。

```

---

如果你愿意，我还可以顺手帮你把 README 再加两块更“产品化”的内容：

1) **沉浸式翻译的具体填写截图/字段示例**（URL、模型名、temperature、max_tokens 之类）  
2) **配置推荐模板**（比如低资源模式/高性能模式/局域网共享模式三套 config）
::contentReference[oaicite:0]{index=0}
```
