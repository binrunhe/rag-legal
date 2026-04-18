# 密码重置功能 - 快速验证清单

## ✅ 快速部署验证（5分钟）

### 步骤1：验证环境变量（1分钟）

```bash
cd d:\办公室\RAG-Legal

# 检查.env文件是否包含：
grep -E "SMTP_USER|SMTP_PASSWORD|RESET_CODE_SECRET|JWT_SECRET" .env

# 预期输出：
# SMTP_USER=1433809622@qq.com
# SMTP_PASSWORD=ppuaphrjcvcmifgi
# RESET_CODE_SECRET=...
# JWT_SECRET=...
```

### 步骤2：验证后端依赖（1分钟）

```bash
# 检查依赖是否安装
python -c "import fastapi; import sqlalchemy; import passlib; print('✅ All dependencies installed')"

# 或查看requirements.txt中的关键包
cat requirements.txt | grep -E "fastapi|sqlalchemy|passlib|aiosqlite|python-jose|python-dotenv"
```

### 步骤3：测试邮件发送（2分钟）

```bash
# 运行测试脚本
python test_email.py

# 输入一个邮箱地址（如：your-email@qq.com）
# 等待邮件送达
# 验证：✅ 邮件发送成功！
```

### 步骤4：启动后端（1分钟）

```bash
# 启动API服务器
python api_server.py

# 预期输出：
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 步骤5：前端验证（可选，需要Node.js）

```bash
# 在另一个终端
cd next-app
npm install
npm run dev

# 访问：http://localhost:3000/forgot-password
```

---

## 🧪 端到端测试场景

### 场景1：成功的密码重置

**操作步骤：**
1. 访问 `http://localhost:8000/docs` (Swagger文档)
2. 找到 `POST /api/auth/send-code`
3. 输入已注册的邮箱
4. 获取响应：`{"status": "success", "data": null, "msg": "验证码已发送"}`
5. 查收邮件，复制验证码
6. 调用 `POST /api/auth/reset-password`
7. 输入：邮箱、验证码、新密码
8. 获取响应：`{"status": "success", "data": null, "msg": "密码已重置"}`
9. 使用新密码调用 `POST /api/auth/login` 验证成功

**预期结果：**
- ✅ 验证码邮件收到
- ✅ 密码重置成功
- ✅ 使用新密码登录成功

### 场景2：冷却时间限制

**操作步骤：**
1. 调用 `send-code` - 成功
2. 立即再次调用 `send-code`
3. 获取响应：`{"status": "error", "data": null, "msg": "请 59 秒后再获取验证码"}`
4. 等待60秒后再试

**预期结果：**
- ✅ 第一次成功
- ✅ 第二次返回429 Too Many Requests
- ✅ 倒计时正确显示

### 场景3：验证码过期

**操作步骤：**
1. 调用 `send-code` - 获得验证码
2. 等待5分01秒
3. 调用 `reset-password` 使用该验证码
4. 获取响应：`{"status": "error", "data": null, "msg": "验证码无效或已过期"}`

**预期结果：**
- ✅ 5分钟后验证码自动失效

### 场景4：无效验证码

**操作步骤：**
1. 调用 `send-code` - 获得验证码（假设为123456）
2. 调用 `reset-password` 使用错误验证码（如999999）
3. 获取响应：`{"status": "error", "data": null, "msg": "验证码错误"}`

**预期结果：**
- ✅ 验证码验证失败，返回400

### 场景5：未注册邮箱

**操作步骤：**
1. 调用 `send-code`，使用从未注册过的邮箱
2. 获取响应：`{"status": "error", "data": null, "msg": "邮箱未注册"}`

**预期结果：**
- ✅ 返回404，提示邮箱未注册

---

## 📊 API响应验证

### 成功响应格式

```json
{
  "status": "success",
  "data": null,
  "msg": "验证码已发送"
}
```

**检查点：**
- ✅ `status` 字段为 "success" 或 "error"
- ✅ `data` 字段为 `null`（对于send-code和reset-password）
- ✅ `msg` 字段为中文说明文本
- ✅ HTTP状态码为 200

### 错误响应格式

```json
{
  "status": "error",
  "data": null,
  "msg": "邮箱未注册"
}
```

**检查点：**
- ✅ `status` 字段为 "error"
- ✅ `data` 字段为 `null`
- ✅ `msg` 字段说明错误原因
- ✅ HTTP状态码为 400、404、429 或 502

---

## 🔍 前端集成验证

### 验证API调用

在前端查看浏览器开发者工具 (F12 → Network 标签)

**send-code 请求：**
```
POST http://localhost:8000/api/auth/send-code
Content-Type: application/json

{"email": "user@example.com"}
```

**reset-password 请求：**
```
POST http://localhost:8000/api/auth/reset-password
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "newPassword123"
}
```

### 验证页面功能

**第1步（邮箱输入）**
- [ ] 邮箱输入框可见
- [ ] "获取验证码"按钮可点击
- [ ] 输入无效邮箱时显示错误
- [ ] 倒计时显示正确

**第2步（密码重置）**
- [ ] 验证码输入框自动聚焦
- [ ] 输入非数字时自动过滤
- [ ] 超过6位时自动截断
- [ ] 密码显示/隐藏切换正常
- [ ] 两次密码一致性校验
- [ ] 所有字段有实时验证

**通用**
- [ ] 错误消息清晰可见
- [ ] 加载状态显示
- [ ] Toast通知正常弹出
- [ ] 成功后跳转到登录页

---

## 🔐 安全验证

### 密码哈希验证

```bash
# 登录后端容器或本地环境
python -c "
from utils import hash_password, verify_password

# 测试密码哈希
pwd = 'testPassword123'
hashed = hash_password(pwd)
print(f'Original: {pwd}')
print(f'Hashed: {hashed}')
print(f'Verified: {verify_password(pwd, hashed)}')

# 预期输出：
# Original: testPassword123
# Hashed: \$2b\$12\$...(60字符的bcrypt哈希)
# Verified: True
"
```

### 验证码哈希验证

```bash
python -c "
from utils import generate_6_digit_code, _hash_reset_code, verify_reset_code

# 生成验证码
code = generate_6_digit_code()
digest = _hash_reset_code(code)

print(f'Code: {code}')
print(f'Digest: {digest}')
print(f'Verified: {verify_reset_code(code, digest)}')

# 预期输出：
# Code: 123456 (6位数字)
# Digest: abc123...(64字符的SHA256哈希)
# Verified: True
"
```

---

## 📈 性能检查

### 响应时间目标

| 操作 | 目标 | 检查方法 |
|------|------|--------|
| send-code | < 3秒 | F12 → Network → 查看请求时间 |
| reset-password | < 2秒 | F12 → Network → 查看请求时间 |
| 验证码生成 | < 100ms | 后端日志 |
| 验证码验证 | < 50ms | 后端日志 |

### 数据库查询验证

```bash
# 后端日志应显示查询语句，例如：
# SELECT users.id, users.email ... WHERE users.email = %s

# 确保没有 N+1 查询问题
# 正常应该只有1-2个查询
```

---

## 🔧 故障排查快速参考

| 问题 | 症状 | 解决方案 |
|------|------|--------|
| 邮件未发送 | 502 错误 | 检查SMTP参数和QQ授权码 |
| 验证码始终过期 | 立即显示过期 | 检查Redis连接或系统时间 |
| 密码不能登录 | 验证失败 | 确认Bcrypt配置一致 |
| CORS错误 | 跨域请求失败 | 更新api_server.py中的CORS_ORIGINS |
| 验证码丢失 | 找不到验证码 | 进程重启后丢失？配置Redis或增加TTL |

---

## 📋 最终检查清单

**后端检查：**
- [ ] `utils.py` 包含所有验证码和邮件函数
- [ ] `routers/auth.py` 包含send-code和reset-password端点
- [ ] `.env` 文件包含所有必需的环境变量
- [ ] 运行 `python test_email.py` 成功
- [ ] 后端在 `http://localhost:8000` 正常运行
- [ ] Swagger文档在 `http://localhost:8000/docs` 可访问

**前端检查：**
- [ ] `next-app/app/(auth)/forgot-password/page.tsx` 已更新
- [ ] `next-app/lib/api/auth.ts` 包含API调用函数
- [ ] 前端在 `http://localhost:3000` 正常运行
- [ ] `/forgot-password` 页面可访问

**集成检查：**
- [ ] 前端可以调用后端API
- [ ] send-code返回成功响应
- [ ] 邮件成功送达
- [ ] reset-password返回成功响应
- [ ] 使用新密码可以登录

**功能检查：**
- [ ] 2步流程正常工作
- [ ] 60秒倒计时正确
- [ ] 5分钟验证码过期
- [ ] 所有错误都有友好提示
- [ ] 成功后跳转到登录页

**安全检查：**
- [ ] 验证码使用HMAC-SHA256哈希存储
- [ ] 密码使用Bcrypt哈希存储
- [ ] 验证使用恒定时间比较
- [ ] 敏感信息不泄露到前端
- [ ] API响应使用正确的HTTP状态码

---

## 🚀 一键验证脚本

```bash
#!/bin/bash

echo "========== 密码重置功能验证 =========="
echo ""

# 1. 检查后端
echo "[1/5] 检查后端启动..."
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ 后端运行正常"
else
    echo "❌ 后端未启动，请运行: python api_server.py"
    exit 1
fi

# 2. 检查前端
echo "[2/5] 检查前端启动..."
if curl -s http://localhost:3000/forgot-password > /dev/null; then
    echo "✅ 前端运行正常"
else
    echo "⚠️  前端可能未启动，可选启动: npm run dev"
fi

# 3. 测试send-code
echo "[3/5] 测试 send-code 端点..."
SEND_CODE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}')

if echo "$SEND_CODE_RESPONSE" | grep -q "success"; then
    echo "✅ send-code 端点正常"
elif echo "$SEND_CODE_RESPONSE" | grep -q "error"; then
    echo "⚠️  send-code 返回错误（可能是邮箱未注册）"
else
    echo "❌ send-code 端点异常"
fi

# 4. 检查数据库
echo "[4/5] 检查数据库..."
if python -c "from models import User; print('✅ 数据库模型正常')" 2>/dev/null; then
    echo "✅ 数据库模型正常"
else
    echo "❌ 数据库模型错误"
fi

# 5. 验证依赖
echo "[5/5] 验证依赖..."
if python -c "import fastapi, sqlalchemy, passlib, dotenv; print('✅ 所有依赖正常')" 2>/dev/null; then
    echo "✅ 所有依赖正常"
else
    echo "❌ 部分依赖缺失，请运行: pip install -r requirements.txt"
fi

echo ""
echo "========== 验证完成 =========="
```

运行脚本：
```bash
bash verify.sh
```

---

## 📞 支持和反馈

如遇到问题，请检查：
1. 完整部署指南：`PASSWORD_RESET_GUIDE.md`
2. 实现总结：`IMPLEMENTATION_SUMMARY.md`
3. 此验证清单

---

**最后更新**：2026-04-18  
**版本**：1.0
