# ChatForest · 对话森林

> 每一次提示，都长出新的可能 · Every prompt grows a new branch

一个**多分支 AI 对话**工具。从任意一条消息岔出新的方向：换个问法、换个模型、换个思路——每条分支各自生长、互不干扰，让对话像森林一样分叉延展。

## 为什么是多分支？

传统 AI 对话是单线的：问 A、答 A、再问 B。想换个问法就得覆盖重来，旧的思路留不住。ChatForest 把对话变成一棵**树**：

- **一个问题，多个答案** — 让两个模型各答一遍，横向对比优劣
- **不满意就再长一条** — 从原问题岔出新分支，两种思路都保留，不必二选一
- **中途试探不伤主线** — 聊到一半想验证一个新想法？从那条消息岔出去，主线上下文不受影响
- **哪条聊得好走哪条** — 沿任意分支继续深入，其余分支随时可以回来

## 核心概念

| 概念 | 含义 |
|---|---|
| 消息卡片 | 每轮对话（你的提问 / AI 的回复）是树上的一个节点 |
| 分支 | 从任意一条消息发出新回复，长出新的对话支线 |
| 上下文链 | AI 回复时沿连线向上追溯本分支的全部历史，各分支上下文互不污染 |
| 对话树视图 | 整棵对话树自由缩放、拖动、分区查看，全貌一目了然 |

## 功能特性

- **多分支探索** — 从同一节点发出多条回复，形成树状对话结构
- **多模型对比** — 每张卡片可独立选择模型；内置阿里百炼、MiMo 预设渠道，支持自定义任意 OpenAI 兼容 API（OpenAI、DeepSeek、Ollama 等）
- **上下文继承** — 连线即继承关系，AI 沿连线向上追溯本分支历史
- **专注 / 总览双模式** — 专注模式沿当前分支线性追问，总览模式纵览整棵对话树
- **流式输出** — AI 回复实时流式显示
- **Markdown 渲染** — 标题、代码块、表格等完整格式
- **消息编辑** — 用户消息和 AI 回复均可直接修改
- **本地存储** — 所有数据以 JSON 文件保存在本地，不依赖任何云端服务

---

## 两种使用方式

| 方式 | 适合场景 | 入口 |
|---|---|---|
| 🖥️ **Windows 桌面版** | 个人使用，双击即开 | `build_exe.bat` 构建一次 → 双击 `ChatForest.exe` |
| 🌐 **Linux 服务器** | 局域网共享，多设备访问 | `bash service.sh start` |

### Windows 桌面版

在 Windows 电脑上构建一次（需 Python 3.10+ 和 Node.js 18+）：

```bat
conda activate chatforest
build_exe.bat
```

构建产物在 `dist\ChatForest\`，日常使用双击其中的 `ChatForest.exe`：自动启动服务并打开浏览器，关闭窗口即退出。对话数据保存在 exe 旁边的 `data\` 目录，整个文件夹拷到其他 Windows 电脑也能直接用。

### Linux 服务器

```bash
bash service.sh start     # 后台启动，关闭终端不影响
```

- 本机访问：http://localhost:9000
- 局域网访问：http://<服务器IP>:9000（局域网内其他设备浏览器直接打开）

管理命令：

```bash
bash service.sh status    # 查看运行状态和访问地址
bash service.sh logs      # 实时查看日志
bash service.sh restart   # 重启
bash service.sh stop      # 停止
```

---

## 快速开始（开发模式）

### 环境要求

- Python 3.10+
- Node.js 18+

### 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 配置模型

首次启动后，点击左下角「⚙ 模型配置」，进入「渠道与模型详细配置」，填入：

- **Base URL** — API 地址，例如阿里云百炼：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- **API Key** — 对应平台的密钥
- **模型列表** — 逗号分隔，例如 `qwen-plus,qwen-turbo,qwen-max`

支持任何 OpenAI 兼容格式的服务。

### 启动

```bash
# 后端
conda activate chatforest
cd backend
uvicorn main:app --host 0.0.0.0 --port 9000

# 前端（开发模式，新终端）
cd frontend
npm run dev   # http://localhost:5173
```

Windows 下一键启动（后端 + 前端热更新）：双击 `start.bat`。
Linux 下前台调试（强制重建前端）：`bash start.sh`。

---

## 使用说明

| 操作 | 方式 |
|---|---|
| 新建对话 | 点击左侧栏「🌱 新画布」，在底部输入框输入内容发送 |
| 分支上追问 | 点击选中一张卡片，在底部输入框输入并发送，新消息成为它的子节点 |
| 发送快捷键 | `Ctrl+Enter` 或 `Cmd+Enter` |
| 建立分支 | 从同一张卡片发出多条回复；或拖动卡片底部的连接点到目标卡片顶部，继承其上下文 |
| 删除连线 | 点击连线，确认删除 |
| 调整卡片大小 | 拖动卡片四边或四角的 resize 手柄 |
| 调整内容比例 | 拖动卡片内部的分隔条 |
| 复制卡片 | 点击卡片头部的 ⧉ 按钮，把内容复用到其他分支 |
| 删除卡片 | 点击卡片头部的 ✕ 按钮，或选中后按 `Delete` |
| 切换 Markdown 预览 | 点击 AI 区域标签旁的「编辑/预览」按钮 |

---

## 技术栈

| 层 | 技术 |
|---|---|
| 前端框架 | Vue 3 + TypeScript + Vite |
| 状态管理 | Pinia |
| 画布引擎 | Vue Flow |
| Markdown | marked + DOMPurify |
| 后端框架 | FastAPI + uvicorn |
| AI 接入 | OpenAI SDK（兼容任意 OpenAI 格式 API） |
| 存储 | 本地 JSON 文件 |

---

## 项目结构

```
.
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── run_local.py         # 桌面版启动器（双击 exe 的入口）
│   ├── requirements.txt
│   ├── api/                 # 画布 / 对话 / 模型配置接口
│   ├── core/                # 上下文链构建、AI 提供商适配
│   ├── storage/             # JSON 文件存储
│   └── data/                # 运行时数据（自动生成，不入库）
├── frontend/
│   └── src/
│       ├── App.vue
│       ├── api/             # 后端接口封装
│       ├── components/      # 画布、卡片、设置等组件
│       ├── stores/          # Pinia 状态
│       └── types/           # TypeScript 类型定义
├── ChatForest.spec          # PyInstaller 打包配置（Windows 桌面版）
├── build_exe.bat            # Windows 一键构建脚本
├── service.sh               # Linux 后台服务管理
└── start.sh / start.bat     # 开发模式启动脚本
```

---

## License

[MIT](LICENSE)
