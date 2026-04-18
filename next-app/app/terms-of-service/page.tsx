import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function TermsOfServicePage() {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-6 px-4 py-8 md:px-6">
      <div className="rounded-2xl border border-border/50 bg-background p-6 shadow-sm md:p-8">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold">服务条款</h1>
          <p className="text-sm text-muted-foreground">最近更新：2026-04-17</p>
        </div>

        <div className="mt-6 space-y-5 text-sm leading-7 text-muted-foreground">
          <p>
            欢迎使用“法律顾问”服务。你在访问或使用本网站时，应当阅读并遵守本服务条款。继续使用即视为你已阅读、理解并同意受本条款约束。
          </p>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">1. 服务说明</h2>
            <p>1. 本服务提供法律信息检索、要点整理与通用问答辅助。</p>
            <p>2. 本服务内容仅供参考，不构成正式法律意见或律师执业建议。</p>
            <p>3. 对于需专业判断的事项，请咨询持证律师并结合具体案情处理。</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">2. 账号与访问</h2>
            <p>1. 你应妥善保管账号及登录凭据，对账号下行为负责。</p>
            <p>2. 你可使用访客模式体验，但部分功能可能受限。</p>
            <p>3. 若发现账号异常或安全风险，应及时通知我们。</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">3. 用户行为规范</h2>
            <p>你不得利用本服务从事任何违法违规活动，包括但不限于：</p>
            <p>1. 发布、传播违法信息，侵害他人合法权益。</p>
            <p>2. 进行恶意攻击、逆向工程、干扰系统正常运行。</p>
            <p>3. 未经授权抓取、复制、出售平台数据或内容。</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">4. 知识产权</h2>
            <p>
              本服务所包含的界面设计、文本、标识、代码与相关内容受知识产权法律保护。未经许可，你不得擅自复制、修改、传播或商业化使用。
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">5. 免责声明</h2>
            <p>1. 本服务按“现状”提供，不保证对所有场景均完全准确、完整或实时。</p>
            <p>2. 因你基于本服务内容直接作出决策而产生的风险，由你自行承担。</p>
            <p>3. 在法律允许范围内，我们不对间接损失、附带损失承担责任。</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">6. 服务变更、中断与终止</h2>
            <p>
              我们有权在必要时对功能进行升级、维护、限制或停止；对于违反本条款的账号，有权采取警告、限制功能或终止服务等措施。
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">7. 法律适用与争议解决</h2>
            <p>
              本条款的订立、生效、解释与争议解决，适用中华人民共和国法律。因本条款产生的争议，应先友好协商；协商不成的，提交有管辖权的人民法院解决。
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground">8. 条款更新</h2>
            <p>
              我们可根据法律法规、监管要求或业务发展调整本条款。更新后将通过页面公告等方式提示，继续使用服务即视为你同意更新条款。
            </p>
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
