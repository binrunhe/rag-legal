from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import uvicorn
import torch

# 导入咱们自己写的核心模块
from config import Config
from search import run_search
from rerank import rerank_context
from RAG import rewrite_query, call_ollama_rag

# 初始化 FastAPI 应用
app = FastAPI(
    title="法律大模型智能体 API",
    description="提供给前端调用的标准 RESTful 接口，支持自定义检索参数。",
    version="1.0.0",
    servers=[ # 不加这段会认为网页在哪,api在哪 会去手机的8000端口
        {"url": "https://api.hehe051104.me", "description": "公网生产环境"},
        {"url": "http://127.0.0.1:8000", "description": "本地开发环境"}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有前端域名访问（开发阶段极其方便）
    allow_credentials=True,
    allow_methods=["*"],  # 允许 POST, GET 等所有请求
    allow_headers=["*"],  # 允许所有请求头
)

# ==========================================
# 定义前端传过来的数据格式 (数据校验层)
# ==========================================
class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]  # 仅允许 user / assistant
    content: str                           # 对应当前消息文本


class ChatRequest(BaseModel):
    query: str                                  # 用户当前的问题
    # 历史对话格式固定为:
    # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    history: List[HistoryMessage] = Field(default_factory=list)

    # 开放给前端的“大厂级”配置开关 (带默认值)
    top_n: Optional[int] = Config.DEFAULT_TOP_N                 # 决定最后引用几条法条
    n_results: Optional[int] = Config.DEFAULT_N_RESULTS         # 决定向量海选捞多少条
    threshold: Optional[float] = Config.DEFAULT_THRESHOLD       # 决定过滤掉多少低分法条
    force_search: Optional[bool] = True                         # 是否强制开启检索（应对闲聊）

# ==========================================
# 核心对话接口
# ==========================================
@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        print("\n" + "="*50)
        print(f"📥 [API接收请求] 用户提问: {req.query}")
        print(f"⚙️  [前端配置] top_n={req.top_n}, n_results={req.n_results}, 历史对话轮数={len(req.history)}")

        # 1. 意图重写
        search_query = rewrite_query(req.query, req.history, Config.RAG_MODEL)

        # 2. 意图预判 (继承你 main.py 里的逻辑)
        skip_words = ["总结", "记忆", "之前", "聊了什么", "你是谁"]
        should_skip_search = any(word in search_query for word in skip_words)

        # 如果前端强制关掉了检索，或者触发了闲聊词
        if not req.force_search or should_skip_search:
            print("🔀 [流转] 判定为闲聊或前端关闭检索，直接进入大模型回复。")
            answer = call_ollama_rag(req.query, [], req.history, Config.RAG_MODEL)
            return {
                "answer": answer,
                "references": [],  # 没有检索，溯源卡片为空
                "status": "success_no_search"
            }

        # 3. 混合检索
        raw_docs = run_search(search_query, Config.DB_PATH, Config.COLLECTION_NAME, Config.SEARCH_MODEL, req.n_results)

        final_docs = []
        if raw_docs:
            # 4. 动态重排 (传入前端指定的 top_n 和 threshold)
            final_docs = rerank_context(search_query, raw_docs, Config.RERANK_MODEL, Config.DEFAULT_MAX_LENGTH, req.top_n, req.threshold)

        # 5. 生成回答
        answer = call_ollama_rag(req.query, final_docs, req.history, Config.RAG_MODEL)

        # 清理显存碎片 (继承自你原本的 main.py)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # 6. 组装发给前端的 JSON 数据
        # 格式化 references 方便前端直接渲染“溯源卡片”
        formatted_references = []
        for doc in final_docs:
            formatted_references.append({
                "source": doc['metadata'].get('source', '未知'),
                "article": doc['metadata'].get('article_number', '未知'),
                "content": doc['content'],
                "score": doc.get('rerank_score', 0)
            })

        print("📤 [API返回响应] 成功生成回答并附带溯源信息。")
        print("="*50 + "\n")

        return {
            "answer": answer,
            "references": formatted_references,
            "status": "success"
        }

    except Exception as e:
        print(f"❌ [API运行错误]: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 启动服务器，对外暴露 8000 端口
    print("🚀 法律智能体 API 服务已启动！")
    print("👉 请在浏览器中打开调试台: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)