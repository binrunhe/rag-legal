import torch
import chromadb
from sentence_transformers import SentenceTransformer

# db_path = "./legal_vector_db"
# collection_name = "china_civil_code"
# model_name = "Qwen/Qwen3-Embedding-0.6B"

_embedding_model_instance = None
_chroma_client = None

# 优化,解决一次加载常驻内存 无需重复加载
def get_resources(db_path, model_name):
    """内部函数：确保数据库客户端和模型只加载一次"""
    global _embedding_model_instance, _chroma_client

    #  加载数据库客户端
    if _chroma_client is None:
        print(f" [首次加载] 正在连接数据库: {db_path}")
        _chroma_client = chromadb.PersistentClient(path=db_path)

    #  加载 Embedding 模型
    if _embedding_model_instance is None:
        print(f" [首次加载] 正在加载 Embedding 模型: {model_name}")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f'当前使用设备为: {device}')
        _embedding_model_instance = SentenceTransformer(
            model_name,
            device=device,
            model_kwargs={"torch_dtype": torch.float16}
        )

    return _chroma_client, _embedding_model_instance

def run_search(query_text,db_path,collection_name,model_name,n_results):
    client, model = get_resources(db_path, model_name)

    collection = client.get_collection(name=collection_name)


    print(f"\n用户咨询: {query_text}")
    print("正在检索法律依据\n")

    # 核心：使用 query 专门的 Prompt 进行编码
    # 先把要查询句子句子转成向量
    query_embedding = model.encode(
        [query_text],
        prompt_name="query",
        convert_to_numpy=True
    ).tolist()

    #  执行检索 (取前 n_results 条最相关的)
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        # where={"book": "第二编　物　　权"}  # 筛选条件
    )

    #  打印结果
    # results包含documents,metadatas,ids,distances  embeddings 默认是不返回的
    # [0]的原因是支持一下多查询,可能里面会有多个数据
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        score = results['distances'][0][i] # 距离越小越相关

        levels = [
            meta.get("book", ""),
            meta.get("subbook", ""),
            meta.get("chapter", ""),
            meta.get("section", "")
        ]
        full_path = " > ".join([lvl for lvl in levels if lvl])

        print(f"【匹配条文 {i+1}】")
        print(f"来源：{meta['source']}")
        print(f"法条编号：{meta['article_number']}")
        print(f"法律层级：{full_path}")
        print(f"法律原文：{doc}")
        print(f"语义距离：{score:.4f}")
        print("-" * 60)

    return results

""" 
results结构
{
    "documents": [ 
        ["法条A", "法条B", "法条C"] , [                   ] // 这是第一个问题的搜索结果 (索引 0)
    ],
    "metadatas": [
        [{"src": "民法典"}, {"src": "刑法"}, {"src": "担保解释"}] , [                   ] 
    ],
    "distances": [
        [0.12, 0.45, 0.88] , [                   ] 
    ]
}
"""