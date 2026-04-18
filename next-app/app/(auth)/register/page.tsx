"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Eye, EyeOff, Loader2 } from "lucide-react";

import { toast } from "@/components/chat/toast";
import { AnimatedCharacters } from "@/components/ui/animated-characters";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { InteractiveHoverButton } from "@/components/ui/interactive-hover-button";
import { Label } from "@/components/ui/label";
import { AuthApiError, register, sendCode } from "@/lib/api/auth";

const validateEmail = (email: string): string => {
  if (!email.trim()) {
    return "请输入电子邮件";
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
    return "邮箱格式不正确";
  }

  return "";
};

const validateCode = (code: string): string => {
  if (!code.trim()) {
    return "请输入验证码";
  }

  if (!/^\d{6}$/.test(code.trim())) {
    return "验证码必须是 6 位数字";
  }

  return "";
};

const validatePassword = (password: string): string => {
  if (!password) {
    return "请输入密码";
  }

  if (password.length < 6) {
    return "密码至少需要 6 个字符";
  }

  return "";
};

export default function Page() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [emailError, setEmailError] = useState("");
  const [codeError, setCodeError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [duplicateAccountOpen, setDuplicateAccountOpen] = useState(false);
  const [registerSuccessOpen, setRegisterSuccessOpen] = useState(false);
  const [registerSuccessMessage, setRegisterSuccessMessage] = useState("注册成功，请登录");

  useEffect(() => {
    if (countdown <= 0) {
      return;
    }

    const timer = window.setTimeout(() => {
      setCountdown((previousValue) => Math.max(0, previousValue - 1));
    }, 1000);

    return () => window.clearTimeout(timer);
  }, [countdown]);

  const handleSendCode = async () => {
    if (isSendingCode || countdown > 0) {
      return;
    }

    const emailMessage = validateEmail(email);
    if (emailMessage) {
      setEmailError(emailMessage);
      toast({
        type: "error",
        description: emailMessage,
      });
      return;
    }

    setIsSendingCode(true);
    try {
      const response = await sendCode({ email: email.trim(), purpose: "register" });
      toast({
        type: "success",
        description: response.msg || "验证码已发送，请查收邮箱",
      });
      setCountdown(60);
      setCodeError("");
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

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitError("");


    if (isLoading) {
      return;
    }

    const emailMessage = validateEmail(email);
    const codeMessage = validateCode(code);
    const passwordMessage = validatePassword(password);

    if (emailMessage) {
      setEmailError(emailMessage);
      toast({
        type: "error",
        description: emailMessage,
      });
      return;
    }

    if (codeMessage) {
      setCodeError(codeMessage);
      toast({
        type: "error",
        description: codeMessage,
      });
      return;
    }

    if (passwordMessage) {
      toast({
        type: "error",
        description: passwordMessage,
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await register({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        code: code.trim(),
      });

      toast({
        type: "success",
        description: response.msg || "注册成功，请登录",
      });
      setRegisterSuccessMessage(response.msg || "注册成功，请登录");
      setRegisterSuccessOpen(true);
      window.setTimeout(() => {
        router.push("/login");
      }, 1200);
    } catch (error) {
      if (error instanceof AuthApiError && error.statusCode === 409) {
        setDuplicateAccountOpen(true);
        return;
      }

      const message = error instanceof Error ? error.message : "注册失败，请重试";
      setSubmitError(message);
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
    <div className="min-h-screen max-h-screen overflow-hidden grid lg:grid-cols-2">
      <div className="relative hidden lg:flex flex-col justify-between bg-gradient-to-br from-gray-400 via-gray-500 to-gray-600 dark:from-white/90 dark:via-white/80 dark:to-white/70 p-12 text-white dark:text-gray-900">
        <div className="relative z-20">
          <Link href="/" className="flex items-center gap-2 text-lg font-semibold">
            <Image
              src="https://i.postimg.cc/nLrDYrHW/icon.png"
              alt="法律顾问标识"
              width={32}
              height={32}
              className="bg-white/10 backdrop-blur-sm p-1 rounded-lg"
            />
            <span>法律顾问</span>
          </Link>
        </div>

        <div className="relative z-20 flex items-end justify-center h-[500px]">
          <AnimatedCharacters
            isTyping={isTyping}
            showPassword={showPassword}
            passwordLength={password.length}
          />
        </div>

        <div className="relative z-20 flex items-center gap-8 text-sm text-gray-600 dark:text-gray-700">
          <Link href="/privacy-policy" className="hover:text-gray-900 dark:hover:text-black transition-colors">
            隐私政策
          </Link>
          <Link href="/terms-of-service" className="hover:text-gray-900 dark:hover:text-black transition-colors">
            服务条款
          </Link>
        </div>

        <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px]" />
        <div className="absolute top-1/4 right-1/4 size-64 bg-gray-400/20 dark:bg-gray-300/30 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/4 size-96 bg-gray-300/20 dark:bg-gray-200/20 rounded-full blur-3xl" />
      </div>

      <div className="flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-[420px]">
          <div className="lg:hidden flex items-center justify-center gap-2 text-lg font-semibold mb-12">
            <Image
              src="https://i.postimg.cc/nLrDYrHW/icon.png"
              alt="法律顾问标识"
              width={32}
              height={32}
              className="dark:bg-white dark:p-1 dark:rounded-md"
            />
            <span>法律顾问</span>
          </div>

          <div className="text-center mb-10">
            <h1 className="text-3xl font-bold tracking-tight mb-2">创建一个账户</h1>
            <p className="text-muted-foreground text-sm">注册后将自动发送欢迎邮件</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="fullName" className="text-sm font-medium">
                全名
              </Label>
              <Input
                id="fullName"
                name="fullName"
                type="text"
                placeholder="请输入你的姓名"
                autoComplete="name"
                required
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                onFocus={() => setIsTyping(true)}
                onBlur={() => setIsTyping(false)}
                className="h-12 bg-background border-border/60 focus:border-primary"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">
                电子邮件
              </Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="you@example.com"
                autoComplete="off"
                required
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setEmailError("");
                }}
                onFocus={() => setIsTyping(true)}
                onBlur={() => setIsTyping(false)}
                className="h-12 bg-background border-border/60 focus:border-primary"
              />
              {emailError ? (
                <div className="flex items-center gap-2 text-sm text-destructive">
                  <Loader2 className="size-4 opacity-0" />
                  {emailError}
                </div>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="code" className="text-sm font-medium">
                验证码
              </Label>
              <div className="flex gap-3">
                <Input
                  id="code"
                  name="code"
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="请输入 6 位验证码"
                  autoComplete="one-time-code"
                  required
                  value={code}
                  onChange={(event) => {
                    const nextValue = event.target.value.replace(/\D/g, "").slice(0, 6);
                    setCode(nextValue);
                    setCodeError("");
                  }}
                  className="h-12 bg-background border-border/60 focus:border-primary tracking-[0.25em] text-center font-mono text-lg"
                />
                <button
                  type="button"
                  onClick={handleSendCode}
                  disabled={isSendingCode || countdown > 0}
                  className="h-12 min-w-[124px] rounded-md border border-border/60 bg-background px-4 text-sm font-medium hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isSendingCode ? (
                    <span className="inline-flex items-center justify-center gap-2">
                      <Loader2 className="size-4 animate-spin" />
                      发送中...
                    </span>
                  ) : (
                    countdownLabel
                  )}
                </button>
              </div>
              {codeError ? (
                <div className="flex items-center gap-2 text-sm text-destructive">
                  <Loader2 className="size-4 opacity-0" />
                  {codeError}
                </div>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">
                密码
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="h-12 pr-10 bg-background border-border/60 focus:border-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox id="privacy-terms" required />
              <Label htmlFor="privacy-terms" className="text-sm font-normal cursor-pointer">
                我同意
                <Link href="/privacy-policy" className="text-primary underline mx-1">
                  隐私政策
                </Link>
                和
                <Link href="/terms-of-service" className="text-primary underline mx-1">
                  服务条款
                </Link>
              </Label>
            </div>

            <InteractiveHoverButton
              type="submit"
              text={isLoading ? "创建中..." : "创建账户"}
              className="w-full h-12 text-base font-medium"
              disabled={isLoading}
            />

            {submitError ? (
              <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {submitError}
              </div>
            ) : null}
          </form>

          <div className="text-center text-sm text-muted-foreground mt-8">
            已有账号？{" "}
            <Link href="/login" className="text-foreground font-medium hover:underline">
              登录
            </Link>
          </div>
        </div>
      </div>

      <AlertDialog open={duplicateAccountOpen} onOpenChange={setDuplicateAccountOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>账号已存在</AlertDialogTitle>
            <AlertDialogDescription>
              这个邮箱已经注册过了，请直接登录，或者使用“忘记密码”重置密码。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDuplicateAccountOpen(false)}>
              继续注册
            </AlertDialogCancel>
            <AlertDialogAction onClick={() => router.push("/login")}>去登录</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={registerSuccessOpen} onOpenChange={setRegisterSuccessOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>创建成功</AlertDialogTitle>
            <AlertDialogDescription>{registerSuccessMessage}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => router.push("/login")}>去登录</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
