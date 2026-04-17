import torch

class Config:
    # 数据库配置
    DB_PATH = "./legal_vector_db"
    COLLECTION_NAME = "china_law_library"

    # 模型配置
    SEARCH_MODEL = "Qwen/Qwen3-Embedding-0.6B"
    RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
    RAG_MODEL = "Lusizo/qwen2.5-7b-instruct-1m:latest"

    # 运行配置
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    # 默认算法参数 (后续可以被前端传参覆盖)
    DEFAULT_N_RESULTS = 15
    DEFAULT_TOP_N = 5
    DEFAULT_THRESHOLD = -2
    DEFAULT_MAX_LENGTH = 512