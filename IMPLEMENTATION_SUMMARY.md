# 密码重置功能 - 代码迁移整合总结

## 🎯 项目目标

✅ **已完成**：从 CareerCompass 迁移完整的密码重置功能到 RAG-Legal

---

## 📦 核心文件清单

### 前端文件

| 文件路径 | 状态 | 说明 |
|---------|------|------|
| `next-app/app/(auth)/forgot-password/page.tsx` | ✅ 重写 | 2步密码重置表单，包含验证码倒计时、表单验证、错误处理 |
| `next-app/lib/api/auth.ts` | ✅ 已有 | TypeScript API客户端，定义了所有认证相关的类型和函数 |
| `next-app/lib/api-url.ts` | ✅ 已有 | API URL配置 |
| `next-app/hooks/use-toast.ts` | ✅ 已有 | Toast通知钩子 |

### 后端文件

| 文件路径 | 状态 | 说明 |
|---------|------|------|
| `routers/auth.py` | ✅ 已有 | 认证路由，包含send-code和reset-password端点 |
| `utils.py` | ✅ 已有 | 工具函数，包含验证码生成、存储、验证和邮件发送 |
| `models.py` | ✅ 已有 | 数据库模型定义 |
| `database.py` | ✅ 已有 | 数据库配置和会话管理 |
| `api_server.py` | ✅ 已有 | FastAPI应用配置和全局错误处理 |

### 配置文件

| 文件路径 | 状态 | 说明 |
|---------|------|------|
| `.env` | ✅ 更新 | 新增SMTP_FROM, SMTP_USE_SSL, SMTP_USE_TLS |
| `requirements.txt` | ✅ 已有 | 包含所有必要的依赖 |
| `PASSWORD_RESET_GUIDE.md` | ✅ 新建 | 完整的部署和配置指南 |

---

## 🔑 关键技术决策

### 1. 验证码存储方案

**选择：Redis优先 + 内存TTL备选**

```python
# utils.py 中的实现
async def _get_redis_client() -> Any | None:
    # 尝试连接Redis
    # 失败则使用内存字典

_memory_reset_code_cache: dict[str, dict[str, Any]] = {}
```

**优势：**
- ✅ 无需数据库表
- ✅ 自动过期管理
- ✅ 高性能读写
- ✅ Redis和内存双重支持

### 2. 验证码安全机制

**选择：HMAC-SHA256 + Bcrypt**

```python
# 验证码不存储明文，只存储哈希摘要
code_digest = hmac.new(
    RESET_CODE_SECRET.encode(),
    code.encode(),
    hashlib.sha256,
).hexdigest()

# 使用恒定时间比较防止时序攻击
hmac.compare_digest(expected_digest, _hash_reset_code(code))
```

**优势：**
- ✅ 验证码泄露不会暴露真实值
- ✅ 防止时序攻击
- ✅ 与登录密码相同的Bcrypt哈希方案

### 3. 倒计时和速率限制

**选择：客户端倒计时 + 服务端验证**

```python
# 后端
can_send, remaining_seconds = await can_send_reset_code(email)
if not can_send:
    raise AuthError(f"请 {remaining_seconds} 秒后再获取验证码", status_code=429)

# 前端
const [countdown, setCountdown] = useState(0);
// 用户看到倒计时，防止重复点击
```

**优势：**
- ✅ 用户体验友好
- ✅ 防止滥用
- ✅ 双重验证确保安全

### 4. 邮件服务

**选择：QQ SMTP + 异步发送**

```python
# 在线程池中执行阻塞的SMTP操作
await asyncio.to_thread(_send_email_blocking, to_email, subject, plain_body, html_body)
```

**优势：**
- ✅ 不阻塞API响应
- ✅ QQ邮箱免费可靠
- ✅ 同时支持SSL/TLS

---

## 📋 API契约

### 发送验证码

```http
POST /api/auth/send-code
Content-Type: application/json

{
  "email": "user@example.com"
}

HTTP/1.1 200 OK
{
  "status": "success",
  "data": null,
  "msg": "验证码已发送"
}
```

**约束：**
- 邮箱必须已注册
- 60秒内最多发送1次（返回429）
- 验证码有效期5分钟

### 重置密码

```http
POST /api/auth/reset-password
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "newPassword123"
}

HTTP/1.1 200 OK
{
  "status": "success",
  "data": null,
  "msg": "密码已重置"
}
```

**约束：**
- 验证码必须有效且未过期
- 验证码一次性使用
- 新密码至少6字符
- 成功后验证码自动删除

---

## 🔐 数据安全性

### 传输安全

- ✅ HTTPS（生产环境）
- ✅ 验证码仅通过邮件传输
- ✅ API响应中不包含验证码

### 存储安全

- ✅ 验证码使用HMAC-SHA256哈希
- ✅ 密码使用Bcrypt哈希
- ✅ 自动过期（TTL）
- ✅ 一次性使用

### 操作安全

- ✅ 恒定时间比较（防时序攻击）
- ✅ 速率限制（防暴力破解）
- ✅ 验证码格式验证
- ✅ 邮箱存在性检查

---

## 🎨 前端关键特性

### 表单验证

```typescript
// 邮箱格式验证
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// 验证码格式（6位数字）
if (!/^\d{6}$/.test(code)) { /* error */ }

// 密码强度（≥6字符）
if (password.length < 6) { /* error */ }

// 密码一致性
if (newPassword !== confirmPassword) { /* error */ }
```

### 状态管理

```typescript
// 表单状态
const [email, setEmail] = useState("");
const [code, setCode] = useState("");
const [newPassword, setNewPassword] = useState("");
const [confirmPassword, setConfirmPassword] = useState("");

// UI状态
const [step, setStep] = useState<"email" | "reset">("email");
const [showPassword, setShowPassword] = useState(false);

// 加载和计时
const [isLoading, setIsLoading] = useState(false);
const [isSendingCode, setIsSendingCode] = useState(false);
const [countdown, setCountdown] = useState(0);

// 错误消息
const [emailError, setEmailError] = useState("");
const [codeError, setCodeError] = useState("");
const [passwordError, setPasswordError] = useState("");
```

### 用户交互流

1. **第1步（邮箱验证）**
   - 输入邮箱 → 验证格式
   - 点击"获取验证码" → API调用
   - 成功 → 开始倒计时，进入第2步

2. **第2步（密码重置）**
   - 输入验证码 → 实时格式检查
   - 输入新密码 → 显示/隐藏选项
   - 确认密码 → 一致性检查
   - 点击"重置密码" → API调用
   - 成功 → Toast通知，延迟跳转到登录页

---

## 📊 后端数据流

```
请求 (send-code)
  ↓
验证邮箱格式
  ↓
检查邮箱是否已注册
  ↓
检查冷却时间（60秒）
  ↓
生成6位随机验证码
  ↓
HMAC-SHA256哈希验证码
  ↓
存储到Redis或内存（TTL=5分钟）
  ↓
发送邮件
  ↓
更新最后发送时间
  ↓
返回成功响应


请求 (reset-password)
  ↓
验证邮箱格式
  ↓
检查邮箱是否已注册
  ↓
检索验证码记录
  ↓
验证是否过期
  ↓
恒定时间比较验证码
  ↓
Bcrypt哈希新密码
  ↓
更新数据库
  ↓
删除已用验证码
  ↓
返回成功响应
```

---

## 🧪 测试清单

### 单元测试（后端）

```python
# utils.py 中的函数测试
- test_generate_6_digit_code()  # 验证生成的码是否为6位数字
- test_hash_reset_code()         # 验证HMAC哈希
- test_verify_reset_code()       # 验证恒定时间比较
- test_store_reset_code()        # 验证码存储
- test_get_reset_code_record()   # 验证码检索
- test_can_send_reset_code()     # 冷却时间检查
```

### 集成测试（API）

```bash
# 1. 发送验证码
curl -X POST http://localhost:8000/api/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# 2. 重置密码
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "code": "123456", "new_password": "newpass123"}'

# 3. 重新登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "newpass123"}'
```

### 端到端测试（前端）

1. 访问 `/forgot-password`
2. 输入有效邮箱 → 获取验证码
3. 查收邮件，复制验证码
4. 输入验证码和新密码
5. 点击重置 → 验证成功
6. 使用新密码登录 → 验证成功

### 测试脚本

```bash
# 测试邮件发送
python test_email.py

# 输入测试邮箱，检查是否收到验证码
```

---

## 🚀 部署步骤

### 1. 本地开发环境

```bash
# 后端
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
python api_server.py

# 前端
cd next-app
npm install  # 或 pnpm install
npm run dev
```

### 2. 配置文件

```bash
# 复制.env模板
cp .env.example .env

# 编辑.env，配置：
# - SMTP_USER/PASSWORD
# - JWT_SECRET
# - RESET_CODE_SECRET
# - 可选的REDIS_URL
```

### 3. 测试

```bash
# 测试邮件发送
python test_email.py

# 运行前后端
# 访问 http://localhost:3000/forgot-password
```

### 4. 生产部署

```bash
# 后端（Gunicorn）
gunicorn api_server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# 前端（Next.js）
npm run build
npm run start

# 使用Nginx反向代理
# - /api/* → http://localhost:8000
# - /* → http://localhost:3000
```

---

## 🔄 与CareerCompass的差异

| 功能 | CareerCompass | RAG-Legal | 说明 |
|------|--------------|---------|------|
| 认证方式 | Firebase Auth | JWT | 自建认证系统 |
| 邮件服务 | Brevo | QQ SMTP | 本地配置更简单 |
| 验证码存储 | Firestore | Redis/内存 | 分布式系统的选择 |
| UI框架 | Radix UI | 自定义UI | 项目特定样式 |
| 验证码格式 | 不明确 | 6位数字 | 更安全的格式 |
| 密码哈希 | Firebase管理 | Bcrypt | 同步登录系统 |

---

## 📝 环境变量完整清单

```env
# SMTP配置（必需）
SMTP_USER=1433809622@qq.com
SMTP_PASSWORD=ppuaphrjcvcmifgi
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_FROM=1433809622@qq.com
SMTP_USE_SSL=true
SMTP_USE_TLS=false

# 验证码配置（必需）
RESET_CODE_SECRET=your-secret-key
RESET_CODE_EXPIRE_MINUTES=5
RESET_CODE_RESEND_INTERVAL_SECONDS=60

# JWT配置（必需）
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0

# 管理员配置（可选）
ADMIN_EMAILS=admin@example.com,another@example.com
ADMIN_INVITE_CODE=your-invite-code

# Google OAuth（如需使用）
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Gemini API（如需使用）
GEMINI_API_KEY=your-gemini-api-key
```

---

## 💾 数据库检查

### 确认User表包含以下字段

```sql
SELECT * FROM users LIMIT 1;

-- 必需字段：
-- id (VARCHAR, PRIMARY KEY)
-- email (VARCHAR, UNIQUE)
-- password_hash (VARCHAR)
-- full_name (VARCHAR)
-- is_verified (BOOLEAN)
-- provider (VARCHAR)
-- role (VARCHAR)
-- created_at (DATETIME)
-- updated_at (DATETIME)
```

---

## 🎓 学习资源

### 核心概念

1. **HMAC和密码哈希**
   - [HMAC维基百科](https://en.wikipedia.org/wiki/HMAC)
   - [Bcrypt解释](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

2. **验证码安全**
   - [OWASP密码重置指南](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)

3. **异步Python**
   - [FastAPI异步](https://fastapi.tiangolo.com/async/)
   - [asyncio文档](https://docs.python.org/3/library/asyncio.html)

### 项目特定

- `utils.py` - 验证码和邮件逻辑
- `routers/auth.py` - API端点
- `forgot-password/page.tsx` - 前端UI逻辑

---

## 🐛 已知问题和解决方案

### 问题：内存缓存在进程重启后丢失

**解决**：部署时配置Redis
```env
REDIS_URL=redis://localhost:6379/0
```

### 问题：验证码邮件延迟

**原因**：网络或SMTP服务器繁忙  
**解决**：
1. 使用异步邮件队列（Celery）
2. 添加重试机制
3. 监控SMTP连接

### 问题：CORS错误

**解决**：确保 `api_server.py` 中的CORS配置包含前端URL
```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://yourdomain.com",
]
```

---

## ✅ 验收标准

项目完成的标志：

- ✅ 用户可在 `/forgot-password` 输入邮箱并接收验证码
- ✅ 用户可输入验证码和新密码完成重置
- ✅ 重置成功后跳转到登录页
- ✅ 新密码可成功登录
- ✅ 60秒内无法重复发送验证码
- ✅ 5分钟后验证码过期
- ✅ 所有错误都显示友好的中文消息
- ✅ 页面在手机和桌面上都能正常显示
- ✅ 邮件发送和密码哈希与登录系统一致

---

**实现完成日期**：2026-04-18  
**状态**：✅ 生产就绪  
**测试状态**：✅ 所有功能已验证
