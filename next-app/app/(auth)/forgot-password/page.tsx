import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function ForgotPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="w-full max-w-md rounded-2xl border bg-card p-6">
        <h1 className="text-xl font-semibold">忘记密码</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          当前为演示环境，请返回登录页使用默认账号密码或访客模式。
        </p>
        <div className="mt-6 flex gap-2">
          <Button asChild>
            <Link href="/login">返回登录</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/signup">去注册</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
