import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function SignupPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="w-full max-w-md rounded-2xl border bg-card p-6">
        <h1 className="text-xl font-semibold">注册</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          当前版本保留登录主流程，注册功能可后续按你的业务规则接入。
        </p>
        <div className="mt-6 flex gap-2">
          <Button asChild>
            <Link href="/login">返回登录</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/forgot-password">忘记密码</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
