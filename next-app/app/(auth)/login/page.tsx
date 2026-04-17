"use client";

import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Eye, EyeOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { AnimatedCharacters } from "@/components/ui/animated-characters";
import { InteractiveHoverButton } from "@/components/ui/interactive-hover-button";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");

  const validEmail = process.env.NEXT_PUBLIC_LOGIN_EMAIL ?? "demo@falvguwen.ai";
  const validPassword = process.env.NEXT_PUBLIC_LOGIN_PASSWORD ?? "123456";
  const redirectPath = "/legal-assistant";

  const persistSession = (userEmail: string, provider: "password" | "google" | "guest") => {
    const payload = JSON.stringify({
      userEmail,
      provider,
      signedInAt: new Date().toISOString(),
    });

    if (remember) {
      localStorage.setItem("legal_auth_session", payload);
      sessionStorage.removeItem("legal_auth_session");
      return;
    }

    sessionStorage.setItem("legal_auth_session", payload);
    localStorage.removeItem("legal_auth_session");
  };

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    window.setTimeout(() => {
      const isValidUser = email.trim().toLowerCase() === validEmail.toLowerCase();
      const isValidPassword = password === validPassword;

      if (!isValidUser || !isValidPassword) {
        setError("邮箱或密码不正确，请重试。");
        setIsLoading(false);
        return;
      }

      persistSession(email.trim().toLowerCase(), "password");
      setIsLoading(false);
      router.push(redirectPath);
    }, 380);
  };

  const handleGoogleSignIn = () => {
    setIsLoading(true);
    setError("");

    window.setTimeout(() => {
      persistSession("demo.google@falvguwen.ai", "google");
      setIsLoading(false);
      router.push(redirectPath);
    }, 260);
  };

  const handleGuestLogin = () => {
    setIsLoading(true);
    setError("");

    window.setTimeout(() => {
      persistSession("guest@falvguwen.local", "guest");
      setIsLoading(false);
      router.push(redirectPath);
    }, 260);
  };

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
          <Link
            href="/privacy-policy"
            className="hover:text-gray-900 dark:hover:text-black transition-colors"
          >
            隐私政策
          </Link>
          <Link
            href="/terms-of-service"
            className="hover:text-gray-900 dark:hover:text-black transition-colors"
          >
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
            <h1 className="text-3xl font-bold tracking-tight mb-2">欢迎回来</h1>
            <p className="text-muted-foreground text-sm">请输入你的登录信息</p>
          </div>

          <form onSubmit={onSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">
                邮箱
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                autoComplete="off"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                onFocus={() => setIsTyping(true)}
                onBlur={() => setIsTyping(false)}
                className="h-12 bg-background border-border/60 focus:border-primary"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">
                密码
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
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

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="remember"
                  checked={remember}
                  onCheckedChange={(checked) => setRemember(checked === true)}
                />
                <Label htmlFor="remember" className="text-sm font-normal cursor-pointer">
                  30 天内记住我
                </Label>
              </div>
              <Link href="/login" className="text-sm text-primary hover:underline font-medium">
                忘记密码
              </Link>
            </div>

            {error ? (
              <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/30 rounded-lg">
                {error}
              </div>
            ) : null}

            <InteractiveHoverButton
              type="submit"
              text={isLoading ? "登录中..." : "登录"}
              className="w-full h-12 text-base font-medium"
              disabled={isLoading}
            />
          </form>

          <div className="mt-6 space-y-3">
            <InteractiveHoverButton
              type="button"
              text="使用 Google 登录"
              className="w-full h-12 border-border/60"
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              icon={
                <svg
                  className="h-5 w-5"
                  aria-hidden="true"
                  focusable="false"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 488 512"
                >
                  <path
                    fill="currentColor"
                    d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 126 23.4 172.9 61.9l-76.2 76.2C322.3 113.2 289.4 96 248 96c-88.8 0-160.1 71.9-160.1 160.1s71.3 160.1 160.1 160.1c98.2 0 135-70.4 140.8-106.9H248v-85.3h236.1c2.3 12.7 3.9 26.9 3.9 41.4z"
                  />
                </svg>
              }
            />

            <Button
              type="button"
              variant="secondary"
              className="h-12 w-full text-base"
              onClick={handleGuestLogin}
              disabled={isLoading}
            >
              访客登录
            </Button>
          </div>

          <div className="text-center text-sm text-muted-foreground mt-8">
            还没有账号？{" "}
            <Link href="/login" className="text-foreground font-medium hover:underline">
              先体验访客登录
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
