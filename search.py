import torch
import chromadb
from sentence_transformers import SentenceTransformer
import re

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


def run_search(rewrite_text, db_path, collection_name, model_name, n_results):
    client, model = get_resources(db_path, model_name)
    collection = client.get_collection(name=collection_name)

    print(f"\n搜索 大模型指令: {rewrite_text}")

    final_raw_docs = []
    seen_keys = set()

    #  VIP 拦截轨：精准点名
    # 提取所有标签，如 【刑法-第二百三十三条】
    tags = re.findall(r'【(.*?)】', rewrite_text)

    for tag in tags:
        if '-' not in tag: continue

        parts = tag.split('-')
        # 【关键修复】：加上 .strip() 去除可能存在的首尾空格
        law_name_query = parts[0].strip() if parts[0] != "未知" else None
        article_num = parts[-1].strip()

        # 数据库查询：只按编号搜（编号是唯一的，这样最稳）
        res = collection.get(where={"article_number": article_num})

        if res['documents']:
            for d, m in zip(res['documents'], res['metadatas']):
                db_source = m.get('source', '')

                is_match = True
                if law_name_query:
                    # 【核心修复】：使用和入库相同的截断正则，把“（一）”之类的小尾巴砍掉，确保标准统一
                    query_core_name = re.split(r'[_\\s\\u3000（(]', law_name_query)[0].strip()

                    # 必须严格相等！杜绝“民法典”被司法解释名字错误包含的情况
                    if query_core_name != db_source:
                        is_match = False

                if is_match:
                    key = f"{db_source}_{m['article_number']}"
                    if key not in seen_keys:
                        final_raw_docs.append({"content": d, "metadata": m, "method": "精准点名"})
                        seen_keys.add(key)
                        print(f" 精准命中：{db_source} {m['article_number']}")
                        print(f" 内容预览: {d[:60]}...")

                        #  向量语义轨：海选补位
    # 把 【】 标签去掉，剩下纯语义去搜向量
    pure_query = re.sub(r'【.*?】', '', rewrite_text).strip()
    if pure_query:
        print(f"🔍 [语义检索] 关键词: {pure_query}")
        query_embedding = model.encode([pure_query], prompt_name="query", convert_to_numpy=True).tolist()
        vector_res = collection.query(query_embeddings=query_embedding, n_results=n_results)

        for i in range(len(vector_res['documents'][0])):
            d, m = vector_res['documents'][0][i], vector_res['metadatas'][0][i]
            key = f"{m['source']}_{m['article_number']}"
            if key not in seen_keys:
                final_raw_docs.append({"content": d, "metadata": m, "method": "向量召回"})
                seen_keys.add(key)

    else:
        print(" [跳过向量搜索] 意图重写仅包含精准标签，无需执行模糊语义检索。")

    print(f"搜索完毕：共抓取 {len(final_raw_docs)} 条法条进入重排。")
    return final_raw_docs

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