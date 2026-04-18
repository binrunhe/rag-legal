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

## 5. 认证接口联调

Python 认证接口现在统一返回：

```json
{
	"status": "success | error",
	"data": {},
	"msg": "自定义提示消息"
}
```

Swagger 示例可直接打开后端 `/docs` 查看，接口包括：

- `POST /api/auth/send-code`
- `POST /api/auth/register`
- `POST /api/auth/reset-password`
- `POST /api/auth/login`
- `POST /api/auth/token/verify`

前端调用封装已放在 `next-app/lib/api/auth.ts`，可以直接在 Next.js 中导入使用。

### 需要配置的环境变量

- `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM`
- `SMTP_USE_SSL` / `SMTP_USE_TLS`
- `ADMIN_EMAILS` 或 `ADMIN_INVITE_CODE`
- `CORS_ORIGINS`
- `JWT_SECRET` / `JWT_ALGORITHM` / `JWT_EXPIRE_MINUTES`
- `REDIS_URL`（可选，验证码缓存优先使用 Redis）
- `RESET_CODE_SECRET`（可选，验证码摘要密钥；不配则回退到 `JWT_SECRET`）
- `RESET_CODE_EXPIRE_MINUTES`（默认 5）
- `RESET_CODE_RESEND_INTERVAL_SECONDS`（默认 60）

### 认证规则

- 新用户默认是 `user`。
- `ADMIN_EMAILS` 里的邮箱注册时会自动分配 `admin`。
- `ADMIN_INVITE_CODE` 匹配时也会分配 `admin`。
- 找回密码验证码为 6 位，默认 5 分钟有效。
- 验证码默认存入 Redis；如果未配置 `REDIS_URL`，则回退到内存 TTL 缓存。
- 同一邮箱默认 60 秒内只能重新获取一次验证码。
- 注册成功后会发送欢迎邮件，找回密码会发送验证码邮件。

### 联调样例（curl）

以下示例假设后端地址为 `http://127.0.0.1:8000`。

1) 注册

```bash
curl -X POST "http://127.0.0.1:8000/api/auth/register" \
	-H "Content-Type: application/json" \
	-d '{
		"email": "demo@example.com",
		"password": "Test123456",
		"full_name": "Demo User",
		"invite_code": ""
	}'
```

2) 登录

```bash
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
	-H "Content-Type: application/json" \
	-d '{
		"email": "demo@example.com",
		"password": "Test123456"
	}'
```

3) 发送找回验证码

```bash
curl -X POST "http://127.0.0.1:8000/api/auth/send-code" \
	-H "Content-Type: application/json" \
	-d '{
		"email": "demo@example.com"
	}'
```

4) 重置密码（将 123456 替换为真实验证码）

```bash
curl -X POST "http://127.0.0.1:8000/api/auth/reset-password" \
	-H "Content-Type: application/json" \
	-d '{
		"email": "demo@example.com",
		"code": "123456",
		"new_password": "NewPass123456"
	}'
```

5) 校验 JWT（将 TOKEN 替换为登录接口返回的 access_token）

```bash
curl -X POST "http://127.0.0.1:8000/api/auth/token/verify" \
	-H "Content-Type: application/json" \
	-d '{
		"token": "TOKEN"
	}'
```

### 联调样例（PowerShell）

```powershell
$base = "http://127.0.0.1:8000"

# 注册
$registerBody = @{
	email = "demo@example.com"
	password = "Test123456"
	full_name = "Demo User"
	invite_code = ""
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/api/auth/register" -ContentType "application/json" -Body $registerBody

# 登录并提取 token
$loginBody = @{
	email = "demo@example.com"
	password = "Test123456"
} | ConvertTo-Json
$loginResp = Invoke-RestMethod -Method Post -Uri "$base/api/auth/login" -ContentType "application/json" -Body $loginBody
$token = $loginResp.data.token.access_token

# 发送验证码
$sendCodeBody = @{ email = "demo@example.com" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/api/auth/send-code" -ContentType "application/json" -Body $sendCodeBody

# 重置密码（先把 123456 改成邮箱收到的验证码）
$resetBody = @{
	email = "demo@example.com"
	code = "123456"
	new_password = "NewPass123456"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/api/auth/reset-password" -ContentType "application/json" -Body $resetBody

# 校验 token
$verifyBody = @{ token = $token } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/api/auth/token/verify" -ContentType "application/json" -Body $verifyBody
```

