# 法律助手项目说明

相关数据库已建立完成，只需要进行环境配置并启动服务。

## 1. 环境准备

先安装 Python 依赖：

```bash
pip install -r requirements.txt
```

## 2. 安装与启动模型

1. 安装 Ollama。
2. 在 cmd 中运行以下命令拉取并启动模型：

```bash
ollama run Lusizo/qwen2.5-7b-instruct-1m
```

3. 打开项目并运行 api_server.py，启动后端咨询服务。

## 3. 法律数据扩充

如需新增法律文本：

1. 前往 https://flk.npc.gov.cn/index 下载原文。
2. 将文件放入“法律原文”文件夹。
3. 在 process+injest(一键批量完成).py 中配置参数后运行。

司法解释的处理流程同上。

## 4. 法律助手前端（可选 Web UI）

这是 RAG-Legal 项目的可选 Next.js 前端。

### 快速开始

```bash
需要node-js环境，请自己安装
cd next-app
npm install -g pnpm
pnpm dev 代替 npm run dev
cloudflare中用pnpm run build 代替 npm run build   pnpm中run可省略
```

启动后访问：http://localhost:3000

### 技术栈

- Next.js 15 (App Router)
- React Server Components
- shadcn/ui + Tailwind CSS
- Auth.js（认证）
- Drizzle ORM

