# 密码重置功能 - 完整部署指南

## 📋 功能概述

本指南涵盖从 CareerCompass 迁移到 RAG-Legal 的完整密码重置功能。包含：

- ✅ **前端页面** - 优化的找回密码页面（2步流程）
- ✅ **后端API** - 完整的验证码生成、存储和重置逻辑
- ✅ **邮件服务** - QQ邮箱SMTP集成
- ✅ **安全机制** - HMAC-SHA256验证码哈希、Bcrypt密码加密、TTL控制

---

## 🔧 后端配置

### 1. 环境变量配置 (.env)

```env
# SMTP 邮箱配置
SMTP_USER=1433809622@qq.com
SMTP_PASSWORD=ppuaphrjcvcmifgi        # QQ邮箱授权码
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_FROM=1433809622@qq.com           # 发件人邮箱
SMTP_USE_SSL=true                     # QQ邮箱使用SSL
SMTP_USE_TLS=false

# 验证码配置
RESET_CODE_SECRET=your-secret-key-change-me  # 用于HMAC签名
RESET_CODE_EXPIRE_MINUTES=5           # 验证码有效期（分钟）
RESET_CODE_RESEND_INTERVAL_SECONDS=60 # 重发冷却时间（秒）

# Redis 配置（可选）
REDIS_URL=redis://localhost:6379/0    # 如果使用Redis存储验证码

# JWT 配置
JWT_SECRET=your-jwt-secret-change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120
```

### 2. 数据库验证 (models.py)

确保 `User` 模型包含以下字段：

```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    provider: Mapped[str] = mapped_column(String(50), default="local")
    role: Mapped[str] = mapped_column(String(50), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 3. 后端API路由 (routers/auth.py)

已实现的端点：

#### POST /api/auth/send-code
**请求：**
```json
{
  "email": "user@example.com"
}
```

**响应 (成功)：**
```json
{
  "status": "success",
  "data": null,
  "msg": "验证码已发送"
}
```

**响应 (错误)：**
```json
{
  "status": "error",
  "data": null,
  "msg": "邮箱未注册"  // 404
}
```

**错误码：**
- `404` - 邮箱未注册
- `429` - 请稍后再获取（冷却时间未满）
- `502` - 邮件发送失败

#### POST /api/auth/reset-password
**请求：**
```json
{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "newPassword123"
}
```

**响应 (成功)：**
```json
{
  "status": "success",
  "data": null,
  "msg": "密码已重置"
}
```

**响应 (错误)：**
```json
{
  "status": "error",
  "data": null,
  "msg": "验证码错误"  // 400
}
```

**错误码：**
- `400` - 验证码无效、过期或验证码错误
- `404` - 邮箱未注册
- `502` - 密码更新失败

---

## 🎨 前端页面

### 页面位置
`next-app/app/(auth)/forgot-password/page.tsx`

### 主要特性

1. **2步流程**
   - 第1步：输入邮箱 → 获取验证码
   - 第2步：输入验证码、新密码、确认密码 → 重置密码

2. **实时验证**
   - 邮箱格式检查
   - 验证码6位纯数字
   - 密码长度≥6字符
   - 密码一致性校验

3. **用户体验**
   - 60秒倒计时（防止滥用）
   - 实时错误提示
   - 加载状态指示
   - 成功后自动跳转登录

4. **响应式设计**
   - 桌面端：左侧装饰区 + 右侧表单
   - 手机端：单列表单（隐藏装饰区）

### 集成API客户端

前端使用 `@/lib/api/auth.ts` 中的函数：

```typescript
// 发送验证码
const response = await sendCode({ email: "user@example.com" });

// 重置密码
const response = await resetPassword({
  email: "user@example.com",
  code: "123456",
  new_password: "newPassword123"
});
```

---

## 🛡️ 安全机制

### 验证码安全

1. **生成**
   - 6位随机数字 (0-999999)
   - 使用 `secrets.randbelow(1_000_000)`

2. **存储**
   - 使用 HMAC-SHA256 哈希（不存储明文）
   - Redis 优先，内存TTL备选
   - 自动过期（5分钟可配置）

3. **验证**
   - 恒定时间比较 (`hmac.compare_digest`)
   - 防止时序攻击

### 密码安全

1. **存储**
   - Bcrypt 哈希 (cost=12)
   - `passlib[bcrypt]` 库

2. **重置流程**
   - 需要有效的验证码
   - 验证码一次性使用
   - 成功后立即删除验证码

### 速率限制

1. **发送冷却**
   - 60秒内最多发送一次
   - Redis 或内存缓存追踪
   - 返回 429 Too Many Requests

2. **验证尝试**
   - 无限尝试（受验证码过期限制）
   - 建议添加账户级别的限制

---

## 📧 邮件服务

### QQ邮箱配置步骤

1. **获取授权码**
   - 登录 QQ邮箱网页版
   - 设置 → 账户 → POP3/SMTP服务
   - 点击"生成授权码"
   - 使用授权码作为 `SMTP_PASSWORD`

2. **SMTP参数**
   ```
   Host: smtp.qq.com
   Port: 465 (SSL) 或 587 (TLS)
   User: 1433809622@qq.com
   Password: [授权码]
   ```

3. **邮件模板**
   - 验证码模板：HTML + 纯文本
   - 包含验证码、有效期、安全提示
   - 可自定义（见 `utils.py` 中的 `send_verification_email`）

### 测试邮件发送

```bash
python test_email.py
# 输入测试邮箱地址，检查收件箱
```

---

## 🔄 完整流程示例

### 用户重置密码流程

```
1. 用户访问 /forgot-password
   ↓
2. 输入邮箱 → 点击"获取验证码"
   ↓
3. 后端验证邮箱 → 生成6位验证码
   ↓
4. 哈希验证码 → 存储到Redis/内存（5分钟有效期）
   ↓
5. 发送验证码邮件
   ↓
6. 用户收到邮件 → 输入验证码和新密码
   ↓
7. 前端验证表单 → 调用 /reset-password
   ↓
8. 后端验证验证码 → 对比HMAC哈希
   ↓
9. 验证成功 → 用Bcrypt哈希新密码
   ↓
10. 更新数据库 → 删除已用验证码
    ↓
11. 返回成功 → 前端跳转 /login
```

### API调用顺序

```typescript
// 第1步：发送验证码
POST /api/auth/send-code
{
  "email": "user@example.com"
}
→ 响应: { "status": "success", "msg": "验证码已发送", "data": null }

// 第2步：重置密码
POST /api/auth/reset-password
{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "newPassword123"
}
→ 响应: { "status": "success", "msg": "密码已重置", "data": null }

// 第3步：重新登录
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "newPassword123"
}
→ 响应: { "status": "success", "data": { "token": {...}, "user": {...} } }
```

---

## 🚀 部署检查清单

- [ ] `.env` 文件已配置所有必要的SMTP和验证码参数
- [ ] QQ邮箱授权码已设置
- [ ] Redis已安装（可选）或使用内存缓存
- [ ] 数据库User表包含所有必要字段
- [ ] 后端依赖已安装：`pip install -r requirements.txt`
- [ ] 前端依赖已安装：`npm install` 或 `pnpm install`
- [ ] 已通过 `python test_email.py` 测试邮件发送
- [ ] 已测试完整的密码重置流程
- [ ] CORS配置包含前端URL（如 localhost:3001）
- [ ] JWT_SECRET和RESET_CODE_SECRET已设置为强密钥

---

## 📝 自定义

### 修改验证码有效期

编辑 `.env`：
```env
RESET_CODE_EXPIRE_MINUTES=10  # 改为10分钟
```

### 修改重发冷却时间

编辑 `.env`：
```env
RESET_CODE_RESEND_INTERVAL_SECONDS=30  # 改为30秒
```

### 修改邮件模板

编辑 `utils.py` 中的 `send_verification_email()` 函数：
```python
async def send_verification_email(to_email: str, code: str) -> None:
    subject = "【您的应用】邮箱验证码"
    plain_body = f"验证码：{code}"
    html_body = f"<h1>验证码：{code}</h1>"
    # ...
```

### 修改前端验证规则

编辑 `forgot-password/page.tsx` 中的验证函数：
```typescript
const validatePassword = (password: string) => {
  // 自定义密码强度要求
  if (password.length < 8) {  // 改为8字符
    return { valid: false, error: "密码至少需要8个字符" };
  }
  // 可添加大小写、数字、特殊字符要求
  return { valid: true };
};
```

---

## 🐛 故障排查

### 问题：验证码发送失败 (502)

**原因：**
- SMTP配置不正确
- QQ邮箱授权码过期
- 网络连接问题

**解决：**
1. 运行 `python test_email.py` 测试
2. 检查 `.env` 中的SMTP参数
3. 重新生成QQ邮箱授权码

### 问题：验证码始终提示"无效或已过期"

**原因：**
- Redis未启动或配置错误
- 验证码已过期（5分钟）
- HMAC签名不匹配

**解决：**
1. 检查 `REDIS_URL` 是否配置
2. 确认 `RESET_CODE_SECRET` 一致
3. 在5分钟内使用验证码

### 问题：密码重置后无法登录

**原因：**
- 新密码未正确哈希
- 数据库未保存

**解决：**
1. 检查 `hash_password()` 函数
2. 验证数据库commit是否成功
3. 检查密码字段长度限制

---

## 📚 参考文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 异步文档](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Passlib Bcrypt 文档](https://passlib.readthedocs.io/)
- [Next.js 官方文档](https://nextjs.org/docs)
- [QQ邮箱SMTP设置](https://service.mail.qq.com/)

---

## 💡 最佳实践

1. **定期更换密钥**
   - 每3-6个月更换 JWT_SECRET 和 RESET_CODE_SECRET

2. **监控邮件发送**
   - 记录失败的发送尝试
   - 设置告警机制

3. **用户通知**
   - 密码重置后发送确认邮件
   - 登录异常时发送警告

4. **数据清理**
   - 定期清理过期的验证码
   - 归档日志文件

5. **安全审计**
   - 记录所有密码重置操作
   - 定期审查异常活动

---

**最后更新：2026-04-18**
**版本：1.0 (生产就绪)**
