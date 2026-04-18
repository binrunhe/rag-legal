"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Eye, EyeOff, Mail, ShieldCheck, Loader2, CheckCircle2, AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { toast } from "@/components/chat/toast";
import { resetPassword, sendCode } from "@/lib/api/auth";

// ============================================
// 验证函数
// ============================================

const validateEmail = (email: string): { valid: boolean; error?: string } => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email) {
    return { valid: false, error: "请输入邮箱地址" };
  }
  if (!emailRegex.test(email)) {
    return { valid: false, error: "邮箱格式不正确" };
  }
  return { valid: true };
};

const validateCode = (code: string): { valid: boolean; error?: string } => {
  if (!code) {
    return { valid: false, error: "请输入验证码" };
  }
  if (code.length !== 6) {
    return { valid: false, error: "验证码必须是6位数字" };
  }
  if (!/^\d{6}$/.test(code)) {
    return { valid: false, error: "验证码只能包含数字" };
  }
  return { valid: true };
};

const validatePassword = (password: string): { valid: boolean; error?: string } => {
  if (!password) {
    return { valid: false, error: "请输入新密码" };
  }
  if (password.length < 6) {
    return { valid: false, error: "密码至少需要6个字符" };
  }
  return { valid: true };
};

// ============================================
// 主页面组件
// ============================================

export default function ForgotPasswordPage() {
  const router = useRouter();

  // 表单状态
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // UI状态
  const [step, setStep] = useState<"email" | "reset">("email");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // 加载和计时器状态
  const [isLoading, setIsLoading] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [countdown, setCountdown] = useState(0);

  // 验证错误
  const [emailError, setEmailError] = useState<string>("");
  const [codeError, setCodeError] = useState<string>("");
  const [passwordError, setPasswordError] = useState<string>("");

  // 倒计时逻辑
  useEffect(() => {
    if (countdown <= 0) return;

    const timer = setTimeout(() => {
      setCountdown((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearTimeout(timer);
  }, [countdown]);

  // ============================================
  // 事件处理器
  // ============================================

  const handleEmailChange = (value: string) => {
    setEmail(value);
    setEmailError("");
  };

  const handleCodeChange = (value: string) => {
    const numericValue = value.replace(/\D/g, "").slice(0, 6);
    setCode(numericValue);
    setCodeError("");
  };

  const handlePasswordChange = (value: string) => {
    setNewPassword(value);
    setPasswordError("");
  };

  const requestCode = async () => {
    if (isSendingCode || countdown > 0) return;

    // 验证邮箱
    const emailValidation = validateEmail(email);
    if (!emailValidation.valid) {
      setEmailError(emailValidation.error || "邮箱格式不正确");
      toast({
        type: "error",
        description: emailValidation.error || "邮箱格式不正确",
      });
      return;
    }

    setIsSendingCode(true);
    try {
      const response = await sendCode({ email: email.trim() });
      toast({
        type: "success",
        description: response.msg || "验证码已发送，请查收邮箱",
      });
      setStep("reset");
      setCountdown(60);
      setEmailError("");
    } catch (error) {
      const message = error instanceof Error ? error.message : "验证码发送失败，请重试";
      setEmailError(message);
      toast({
        type: "error",
        description: message,
      });
    } finally {
      setIsSendingCode(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isLoading) return;

    // 表单验证
    const codeValidation = validateCode(code);
    const passwordValidation = validatePassword(newPassword);

    if (!codeValidation.valid) {
      setCodeError(codeValidation.error || "验证码无效");
      toast({
        type: "error",
        description: codeValidation.error || "验证码无效",
      });
      return;
    }

    if (!passwordValidation.valid) {
      setPasswordError(passwordValidation.error || "密码不符合要求");
      toast({
        type: "error",
        description: passwordValidation.error || "密码不符合要求",
      });
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("两次输入的密码不一致");
      toast({
        type: "error",
        description: "两次输入的密码不一致",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await resetPassword({
        email: email.trim(),
        code: code.trim(),
        new_password: newPassword,
      });

      toast({
        type: "success",
        description: response.msg || "密码已重置，请重新登录",
      });

      // 延迟跳转，让用户看到成功提示
      setTimeout(() => {
        router.push("/login");
      }, 1500);
    } catch (error) {
      const message = error instanceof Error ? error.message : "重置密码失败，请重试";
      setPasswordError(message);
      toast({
        type: "error",
        description: message,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const countdownLabel = countdown > 0 ? `重新发送 (${countdown}s)` : "获取验证码";

  return (
    <div className="min-h-screen max-h-screen overflow-hidden grid lg:grid-cols-2 bg-black">
      {/* 左侧装饰区域 */}
      <div className="relative hidden lg:flex flex-col justify-between bg-black px-12 py-10 text-white overflow-hidden">
        <div className="relative z-20">
          <Link href="/" className="flex items-center gap-2 text-lg font-semibold">
            <Image
              src="https://i.postimg.cc/nLrDYrHW/icon.png"
              alt="法律智能体"
              width={32}
              height={32}
              className="bg-white/10 backdrop-blur-sm p-1 rounded-lg"
            />
            <span>法律智能体</span>
          </Link>
        </div>

        <div className="relative z-20 flex flex-col justify-center gap-8 h-[500px]">
          <div>
            <Badge variant="outline" className="mb-4 border-white/15 bg-white/5 text-white/80">
              安全找回
            </Badge>
            <h2 className="text-4xl font-bold tracking-tight mb-4">找回密码</h2>
            <p className="max-w-md text-sm text-white/70 leading-relaxed">
              输入注册邮箱获取6位验证码，验证码5分钟内有效，用于安全地重置您的账户密码。
            </p>
          </div>

          {/* 功能卡片 */}
          <div className="space-y-3">
            <div className="rounded-2xl border border-white/20 bg-white/5 p-4 backdrop-blur-md hover:bg-white/10 transition-colors">
              <div className="flex items-center gap-3 text-sm">
                <Mail className="size-5 text-white/80" />
                <div>
                  <div className="font-medium text-white">邮箱验证</div>
                  <div className="text-xs text-white/50">输入您的注册邮箱</div>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-white/20 bg-white/5 p-4 backdrop-blur-md hover:bg-white/10 transition-colors">
              <div className="flex items-center gap-3 text-sm">
                <ShieldCheck className="size-5 text-white/80" />
                <div>
                  <div className="font-medium text-white">验证码确认</div>
                  <div className="text-xs text-white/50">输入收到的6位验证码</div>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-white/20 bg-white/5 p-4 backdrop-blur-md hover:bg-white/10 transition-colors">
              <div className="flex items-center gap-3 text-sm">
                <CheckCircle2 className="size-5 text-white/80" />
                <div>
                  <div className="font-medium text-white">密码重置</div>
                  <div className="text-xs text-white/50">设置您的新密码</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="relative z-20 flex items-center gap-8 text-sm text-white/60">
          <Link href="/privacy-policy" className="hover:text-white transition-colors">
            隐私政策
          </Link>
          <Link href="/terms-of-service" className="hover:text-white transition-colors">
            服务条款
          </Link>
        </div>

        {/* 背景装饰 */}
        <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:20px_20px]" />
        <div className="absolute top-1/4 right-1/4 size-64 bg-white/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/4 size-96 bg-white/3 rounded-full blur-3xl" />
      </div>

      {/* 右侧表单区域 */}
      <div className="flex items-center justify-center p-6 md:p-8 bg-black">
        <div className="w-full max-w-[460px] rounded-3xl border border-white/10 bg-white/[0.04] p-6 md:p-8 shadow-[0_30px_120px_rgba(0,0,0,0.45)] backdrop-blur-xl">
          {/* 手机端Logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 text-lg font-semibold mb-12 text-white">
            <Image
              src="https://i.postimg.cc/nLrDYrHW/icon.png"
              alt="法律智能体"
              width={32}
              height={32}
              className="bg-white/10 p-1 rounded-md"
            />
            <span>法律智能体</span>
          </div>

          {/* 标题区域 */}
          <div className="text-center mb-10">
            <Badge variant="outline" className="mb-3 border-white/15 bg-white/5 text-white/75">
              验证码找回
            </Badge>
            <h1 className="text-3xl font-bold tracking-tight mb-2 text-white">重置密码</h1>
            <p className="text-white/70 text-sm">
              {step === "email" ? "输入注册邮箱以获取验证码" : "输入验证码和新密码完成重置"}
            </p>
          </div>

          <Separator className="my-6 bg-white/10" />

          {/* 表单 */}
          <form onSubmit={step === "reset" ? handleResetPassword : (e) => { e.preventDefault(); requestCode(); }} className="space-y-5">
            {/* 邮箱输入 */}
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium text-white">
                电子邮件
              </Label>
              <div className="relative">
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  disabled={step === "reset" || isSendingCode}
                  value={email}
                  onChange={(e) => handleEmailChange(e.target.value)}
                  className="h-12 rounded-xl border-white/15 bg-white/10 text-white placeholder:text-white/40 shadow-none focus:border-white/40 focus:bg-white/15 disabled:cursor-not-allowed disabled:opacity-60"
                />
              </div>
              {emailError && (
                <div className="flex items-center gap-2 text-sm text-red-400">
                  <AlertCircle className="size-4" />
                  {emailError}
                </div>
              )}
            </div>

            {/* 验证码和密码 - 仅在第二步显示 */}
            {step === "reset" && (
              <>
                {/* 验证码输入 */}
                <div className="space-y-2">
                  <Label htmlFor="code" className="text-sm font-medium text-white">
                    验证码
                  </Label>
                  <Input
                    id="code"
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    placeholder="请输入 6 位数字验证码"
                    autoComplete="one-time-code"
                    value={code}
                    onChange={(e) => handleCodeChange(e.target.value)}
                    className="h-12 rounded-xl border-white/15 bg-white/10 text-white placeholder:text-white/40 shadow-none focus:border-white/40 focus:bg-white/15 tracking-[0.25em] text-center font-mono text-lg"
                  />
                  {codeError && (
                    <div className="flex items-center gap-2 text-sm text-red-400">
                      <AlertCircle className="size-4" />
                      {codeError}
                    </div>
                  )}
                </div>

                {/* 新密码输入 */}
                <div className="space-y-2">
                  <Label htmlFor="newPassword" className="text-sm font-medium text-white">
                    新密码
                  </Label>
                  <div className="relative">
                    <Input
                      id="newPassword"
                      type={showPassword ? "text" : "password"}
                      placeholder="至少 6 个字符"
                      value={newPassword}
                      onChange={(e) => handlePasswordChange(e.target.value)}
                      className="h-12 rounded-xl pr-10 border-white/15 bg-white/10 text-white placeholder:text-white/40 shadow-none focus:border-white/40 focus:bg-white/15"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition-colors"
                    >
                      {showPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                    </button>
                  </div>
                </div>

                {/* 确认密码输入 */}
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-sm font-medium text-white">
                    确认密码
                  </Label>
                  <div className="relative">
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="再次输入新密码"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="h-12 rounded-xl pr-10 border-white/15 bg-white/10 text-white placeholder:text-white/40 shadow-none focus:border-white/40 focus:bg-white/15"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition-colors"
                    >
                      {showConfirmPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                    </button>
                  </div>
                  {passwordError && (
                    <div className="flex items-center gap-2 text-sm text-red-400">
                      <AlertCircle className="size-4" />
                      {passwordError}
                    </div>
                  )}
                </div>
              </>
            )}

            {/* 提交按钮 */}
            <Button
              type="submit"
              disabled={isLoading || isSendingCode || (step === "reset" && !code)}
              className="w-full h-12 rounded-xl text-base font-medium bg-white text-black shadow-sm hover:bg-white/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading || isSendingCode ? (
                <>
                  <Loader2 className="mr-2 size-4 animate-spin" />
                  {step === "email" ? "发送中..." : "重置中..."}
                </>
              ) : (
                <>{step === "email" ? "获取验证码" : "重置密码"}</>
              )}
            </Button>

            {/* 重新发送按钮 - 仅在第二步显示 */}
            {step === "reset" && (
              <Button
                type="button"
                variant="ghost"
                onClick={requestCode}
                disabled={countdown > 0 || isSendingCode}
                className="w-full h-11 rounded-xl text-sm text-white border border-white/15 bg-white/5 hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSendingCode ? (
                  <>
                    <Loader2 className="mr-2 size-4 animate-spin" />
                    发送中...
                  </>
                ) : (
                  countdownLabel
                )}
              </Button>
            )}
          </form>

          {/* 底部链接 */}
          <div className="mt-8 flex items-center justify-between text-sm text-white/60">
            <Link href="/login" className="text-white font-medium hover:text-white/80 transition-colors">
              返回登录
            </Link>
            <Link href="/register" className="text-white font-medium hover:text-white/80 transition-colors">
              去注册
            </Link>
          </div>

          {/* 安全提示 */}
          <div className="mt-6 rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-white/70 flex gap-2">
            <ShieldCheck className="size-4 mt-0.5 flex-shrink-0" />
            <span>
              您的账户信息已安全加密。验证码仅用于密码重置，请勿与他人分享。
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
