import torch
import chromadb
from sentence_transformers import SentenceTransformer
import re


# 兼容以下格式：
# 1) 【刑法-第十条】
# 2) 【刑法 第十条】
# 3) 【刑法第十条】
PRECISE_TAG_PATTERN = re.compile(
    r'^\s*(?P<law>.+?)(?:\s*[-－—–]\s*|\s+)?(?P<article>第[一二三四五六七八九十百千万零〇两\d]+条(?:之[一二三四五六七八九十百千万零〇两\d]+)?)\s*$'
)


def parse_precise_tag(tag_text):
    """从标签文本中提取法律名和条号，失败返回 None。"""
    if not tag_text:
        return None

    match = PRECISE_TAG_PATTERN.match(tag_text.strip())
    if not match:
        return None

    law_name = match.group('law').strip()
    article_num = match.group('article').strip()

    if not law_name or not article_num:
        return None

    return {
        'law_name': law_name,
        'article_number': article_num,
    }

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
    # 提取所有标签，如：
    # - 【刑法-第二百三十三条】
    # - 【刑法 第二百三十三条】
    # - 【刑法第二百三十三条】
    tags = re.findall(r'【(.*?)】', rewrite_text)

    for tag in tags:
        parsed = parse_precise_tag(tag)
        if not parsed:
            continue

        law_name_query = parsed['law_name'] if parsed['law_name'] != "未知" else None
        article_num = parsed['article_number']

        # 数据库查询：只按编号搜（编号是唯一的，这样最稳）
        res = collection.get(where={"article_number": article_num})

        if res['documents']:
            for d, m in zip(res['documents'], res['metadatas']):
                db_source = m.get('source', '')

                is_match = True
                if law_name_query:
                    # 1. 依然先砍掉“(一)”等后缀，拿到标准核心名
                    query_core = re.split(r'[_\\s\\u3000（(]', law_name_query)[0].strip()

                    # 2. 只有“互相包含”才有进一步谈的资格
                    if query_core in db_source or db_source in query_core:
                        # 3. 【核心修复】：身份必须完全对等
                        # 判断数据库里的和查询词里的，是否【都包含】或者【都不包含】“解释/规定”
                        db_is_interp = any(kw in db_source for kw in ["解释", "规定"])
                        query_is_interp = any(kw in query_core for kw in ["解释", "规定"])

                        # 如果一个是解释，另一个不是，直接判定为“跨界误触”，强制拦截！
                        if db_is_interp != query_is_interp:
                            is_match = False
                    else:
                        is_match = False # 完全不包含，直接拒绝

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