import torch
import chromadb
from sentence_transformers import SentenceTransformer

db_path = "./legal_vector_db"
collection_name = "china_civil_code"
model_name = "Qwen/Qwen3-Embedding-0.6B"

def run_search():
    print("正在初始化检索引擎...")
    model = SentenceTransformer(
        model_name,
        device="cuda",
        model_kwargs={"torch_dtype": torch.float16}
    )

    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(name=collection_name)

    query_text = "我把车停在楼下，结果被楼上掉下来的花盆砸坏了，物业有责任吗？"

    print(f"\n用户咨询: {query_text}")
    print("正在检索法律依据...\n")

    # 核心：使用 query 专门的 Prompt 进行编码
    # 先把要查询句子句子转成向量
    query_embedding = model.encode(
        [query_text],
        prompt_name="query",
        convert_to_numpy=True
    ).tolist()

    #  执行检索 (取前 3 条最相关的)
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=3,
        # where={"book": "第二编　物　　权"}  # 筛选条件
    )

    #  打印结果
    # results包含documents,metadatas,distances
    # [0]的原因是支持一下多查询
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
        print(f"法条编号：{meta['article_number']}")
        print(f"法律层级：{full_path}")
        print(f"法律原文：{doc}")
        print(f"语义距离：{score:.4f}")
        print("-" * 60)

if __name__ == "__main__":
    run_search()