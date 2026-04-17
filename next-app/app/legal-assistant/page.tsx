"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDownIcon,
  MessageSquare,
  PanelLeftIcon,
  Plus,
  Send,
  Sparkles,
  User,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { getApiUrl } from "@/lib/api-url";
import { cn } from "@/lib/utils";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
};

const suggestions = [
  "请总结《民法典》中合同无效的核心判断要点。",
  "请给出侵权责任纠纷的法律分析提纲。",
  "请比较保证责任与抵押担保的关键差异。",
  "请列出探望权纠纷中常见的裁判思路。",
];

const historySeeds = [
  "租赁纠纷责任分析",
  "保证合同效力核查清单",
  "探望权裁判要点框架",
  "侵权赔偿范围速查笔记",
];

function extractTextFromUnknownPayload(payload: unknown): string {
  if (typeof payload === "string") {
    return payload;
  }

  if (!payload || typeof payload !== "object") {
    return "";
  }

  const record = payload as Record<string, unknown>;

  if (typeof record.answer === "string") {
    return record.answer;
  }

  if (typeof record.delta === "string") {
    return record.delta;
  }

  if (typeof record.text === "string") {
    return record.text;
  }

  if (typeof record.content === "string") {
    return record.content;
  }

  if (record.message) {
    const nested = extractTextFromUnknownPayload(record.message);
    if (nested) {
      return nested;
    }
  }

  if (record.data) {
    const nested = extractTextFromUnknownPayload(record.data);
    if (nested) {
      return nested;
    }
  }

  if (Array.isArray(record.parts)) {
    return record.parts
      .map((part) => {
        if (part && typeof part === "object") {
          const p = part as Record<string, unknown>;
          if (p.type === "text" && typeof p.text === "string") {
            return p.text;
          }
          if (typeof p.delta === "string") {
            return p.delta;
          }
        }
        return "";
      })
      .join("");
  }

  return "";
}

async function readAssistantText(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("text/event-stream")) {
    if (!response.body) {
      return "";
    }

    const decoder = new TextDecoder();
    const reader = response.body.getReader();
    let buffer = "";
    let assistantText = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line.startsWith("data:")) {
          continue;
        }

        const data = line.slice(5).trim();
        if (!data || data === "[DONE]") {
          continue;
        }

        try {
          const parsed = JSON.parse(data);
          assistantText += extractTextFromUnknownPayload(parsed);
        } catch {
          assistantText += data;
        }
      }
    }

    return assistantText.trim();
  }

  if (contentType.includes("application/json")) {
    const json = await response.json();
    const text = extractTextFromUnknownPayload(json).trim();

    if (text) {
      return text;
    }

    if (
      json &&
      typeof json === "object" &&
      "answer" in json &&
      typeof (json as { answer?: unknown }).answer === "string"
    ) {
      return ((json as { answer: string }).answer ?? "").trim();
    }

    return "";
  }

  return (await response.text()).trim();
}

export default function LegalAssistantPage() {
  const router = useRouter();
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sessionValue = sessionStorage.getItem("legal_auth_session");
    const localValue = localStorage.getItem("legal_auth_session");
    if (!sessionValue && !localValue) {
      router.replace("/login");
    }
  }, [router]);

  useEffect(() => {
    const panel = messagesRef.current;
    if (!panel) return;
    panel.scrollTo({ top: panel.scrollHeight, behavior: "smooth" });
  }, [messages, isSending]);

  const canSend = input.trim().length > 0 && !isSending;

  const stats = useMemo(() => {
    const userCount = messages.filter((item) => item.role === "user").length;
    const assistantCount = messages.filter((item) => item.role === "assistant").length;
    return { userCount, assistantCount };
  }, [messages]);

  const addUserMessage = async (question: string) => {
    const text = question.trim();
    if (!text) return;

    if (isSending) {
      return;
    }

    const userMessageId = `u-${Date.now()}`;

    setMessages((previous) => [
      ...previous,
      {
        id: userMessageId,
        role: "user",
        content: text,
      },
    ]);
    setInput("");
    setIsSending(true);

    try {
      const response = await fetch(getApiUrl("/api/chat"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          query: text,
          history: messages.map((message) => ({
            role: message.role,
            content: message.content,
          })),
          top_n: 5,
          n_results: 15,
          threshold: -2,
          force_search: true,
        }),
      });

      if (!response.ok) {
        let errorMessage = `请求失败（${response.status}）`;
        try {
          const errorJson = await response.json();
          errorMessage =
            (errorJson?.message as string | undefined) ||
            (errorJson?.error as string | undefined) ||
            errorMessage;
        } catch {
          // ignore json parse failure
        }
        throw new Error(errorMessage);
      }

      const assistantReply = await readAssistantText(response);

      setMessages((previous) => [
        ...previous,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          content: assistantReply || "后端已响应，但未返回可展示文本。",
        },
      ]);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "请求后端失败，请检查 API 地址和登录状态。";

      setMessages((previous) => [
        ...previous,
        {
          id: `a-error-${Date.now()}`,
          role: "assistant",
          content: `请求后端失败：${message}`,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const resetChat = () => {
    setMessages([]);
    setInput("");
  };

  const logout = () => {
    localStorage.removeItem("legal_auth_session");
    sessionStorage.removeItem("legal_auth_session");
    router.replace("/login");
  };

  return (
    <div className="flex h-dvh w-full flex-row overflow-hidden bg-sidebar">
      <aside
        className={cn(
          "border-r border-border/50 bg-sidebar transition-all duration-300",
          showSidebar ? "w-[268px]" : "w-0 overflow-hidden",
        )}
      >
        <div className="flex h-14 items-center justify-between px-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Sparkles className="size-4" />
            法律助手
          </div>
          <Button variant="ghost" size="icon" onClick={() => setShowSidebar(false)}>
            <PanelLeftIcon className="size-4" />
          </Button>
        </div>

        <div className="px-3 pb-3">
          <Button className="w-full justify-start rounded-lg" variant="secondary" onClick={resetChat}>
            <Plus className="size-4" />
            新建对话
          </Button>
        </div>

        <div className="space-y-1 px-2">
          {historySeeds.map((item) => (
            <button
              key={item}
              type="button"
              className="w-full rounded-lg px-3 py-2 text-left text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              onClick={() => addUserMessage(item)}
            >
              {item}
            </button>
          ))}
        </div>

        <div className="absolute bottom-0 w-[268px] border-t border-border/50 bg-sidebar p-3">
          <Button variant="outline" className="w-full" onClick={logout}>
            返回登录页
          </Button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col bg-background md:rounded-tl-[12px] md:border-l md:border-t md:border-border/40">
        <header className="flex h-14 items-center gap-2 border-b border-border/20 px-3">
          {!showSidebar ? (
            <Button variant="ghost" size="icon" onClick={() => setShowSidebar(true)}>
              <PanelLeftIcon className="size-4" />
            </Button>
          ) : null}
          <div className="flex size-5 items-center justify-center rounded bg-muted/60 ring-1 ring-border/50">
            <Sparkles className="size-3" />
          </div>
          <span className="text-[13px] text-muted-foreground">智能法律问答</span>
          <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
            <span>用户: {stats.userCount}</span>
            <span>助手: {stats.assistantCount}</span>
            <Link href="/login" className="underline-offset-4 hover:underline">
              切换账号
            </Link>
          </div>
        </header>

        <div ref={messagesRef} className="relative flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-8 px-8">
              <div className="text-center">
                <h2 className="text-xl font-semibold tracking-tight">我可以帮你处理什么法律问题？</h2>
                <p className="mt-1.5 text-sm text-muted-foreground">
                  你可以提问、整理法律思路，或生成分析框架。
                </p>
              </div>

              <div className="grid w-full max-w-2xl grid-cols-1 gap-2 md:grid-cols-2">
                {suggestions.map((suggestion) => (
                  <button
                    className="rounded-xl border border-border/30 bg-card/20 px-3 py-2.5 text-left text-[12px] leading-relaxed text-muted-foreground/70 transition-all duration-200 hover:border-border/60 hover:bg-card/40 hover:text-muted-foreground"
                    key={suggestion}
                    onClick={() => {
                      void addUserMessage(suggestion);
                    }}
                    type="button"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col gap-5 px-2 py-6 md:gap-7 md:px-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex w-full",
                    message.role === "user" ? "justify-end" : "justify-start",
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[88%] rounded-2xl border px-4 py-3 text-sm leading-7",
                      message.role === "user"
                        ? "border-border bg-foreground text-background"
                        : "border-border/50 bg-card text-card-foreground",
                    )}
                  >
                    <div className="mb-1 flex items-center gap-1 text-xs opacity-75">
                      {message.role === "user" ? <User className="size-3.5" /> : <MessageSquare className="size-3.5" />}
                      <span>{message.role === "user" ? "你" : "助手"}</span>
                    </div>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              ))}

              {isSending ? (
                <div className="flex justify-start">
                  <div className="rounded-2xl border border-border/50 bg-card px-4 py-3 text-sm text-muted-foreground">
                    助手正在思考...
                  </div>
                </div>
              ) : null}

              <div className="sticky bottom-0 z-10 flex justify-center pb-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="rounded-full"
                  onClick={() => {
                    const panel = messagesRef.current;
                    if (!panel) return;
                    panel.scrollTo({ top: panel.scrollHeight, behavior: "smooth" });
                  }}
                >
                  <ArrowDownIcon className="size-3" />
                </Button>
              </div>
            </div>
          )}
        </div>

        <div className="mx-auto w-full max-w-4xl px-2 pb-3 md:px-4 md:pb-4">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void addUserMessage(input);
            }}
            className="rounded-2xl border border-border/40 bg-card/70 p-2"
          >
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();

                    if (!canSend) {
                      return;
                    }

                    void addUserMessage(input);
                  }
                }}
                placeholder="请输入你的法律问题..."
                className="min-h-[54px] max-h-44 flex-1 resize-none rounded-xl border border-border/30 bg-background px-3 py-3 text-sm outline-none"
              />
              <Button type="submit" size="icon" className="size-10 rounded-xl" disabled={!canSend}>
                <Send className="size-4" />
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
