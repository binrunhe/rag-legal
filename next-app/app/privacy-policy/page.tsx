import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function PrivacyPolicyPage() {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-6 px-4 py-8 md:px-6">
      <div className="rounded-2xl border border-border/50 bg-background p-6 shadow-sm md:p-8">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold">隐私政策</h1>
          <p className="text-sm text-muted-foreground">最近更新：2026-04-17</p>
        </div>

        <div className="mt-6 space-y-5 text-sm leading-7 text-muted-foreground">
          <p>
            本隐私政策适用于“法律顾问”网站及相关服务。我们重视并保护你的个人信息，将按照合法、正当、必要、诚信原则处理你的数据。
          </p>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">1. 我们收集的信息</h2>
            <p>1. 账号信息：如你主动登录或填写，可能包括邮箱、昵称等。</p>
            <p>2. 会话信息：包括提问内容、使用时间、页面交互行为，用于提供问答服务和体验优化。</p>
            <p>3. 设备与日志信息：如浏览器类型、IP、访问时间、错误日志，用于安全保障与故障排查。</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">2. 信息使用目的</h2>
            <p>1. 提供、维护和改进法律问答服务。</p>
            <p>2. 身份识别、登录状态维持、风控与防滥用。</p>
            <p>3. 统计分析、产品优化与服务质量评估。</p>
            <p>4. 依法履行法定义务或响应监管要求。</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">3. Cookies 与本地存储</h2>
            <p>
              为保障基本登录能力与页面功能，我们可能使用 Cookie 或浏览器本地存储（如 localStorage、sessionStorage）保存会话状态。你可在浏览器设置中清理相关数据，但可能影响部分功能正常使用。
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">4. 信息共享、转让与公开披露</h2>
            <p>除以下情形外，我们不会向第三方出售你的个人信息：</p>
            <p>1. 获得你的明确同意。</p>
            <p>2. 为实现服务必需，与受约束的合作方共享最小必要信息。</p>
            <p>3. 依据法律法规、司法机关或行政机关依法要求。</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">5. 数据安全与保存期限</h2>
            <p>
              我们采取合理的技术和管理措施保护数据安全，包括访问控制、最小权限、传输保护与日志审计。个人信息保存期限将以实现处理目的所必需的最短时间为限，法律另有规定的从其规定。
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">6. 你的权利</h2>
            <p>你有权依法访问、更正、删除你的个人信息，并可申请撤回同意、注销账号或获取相关处理说明。</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">7. 未成年人保护</h2>
            <p>
              若你是未成年人，请在监护人指导下使用本服务。对于需要监护人同意方可处理的个人信息，我们将在确认同意后再进行处理。
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">8. 政策更新</h2>
            <p>
              我们可能根据业务发展或法律要求更新本政策。重大变更将通过页面公告或其他合理方式提示，更新后继续使用服务即视为你已阅读并同意更新内容。
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">9. 联系我们</h2>
            <p>如对本政策有疑问，可通过产品内反馈渠道联系我们。</p>
          </section>

          <div className="flex flex-wrap gap-3 pt-2">
            <Button asChild>
              <Link href="/login">返回登录</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
