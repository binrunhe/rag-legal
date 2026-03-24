import json
import os
import torch
import chromadb
from sentence_transformers import SentenceTransformer

json_path = "code_json/civil_code_1260.json"  # 选择要查看哪个法律的json文件
db_path = "./legal_vector_db"  # 向量库存放地址
collection_name = "china_civil_code"
model_name = "Qwen/Qwen3-Embedding-0.6B"

def run_ingestion():
    # --- 1. 加载 Qwen3-Embedding 模型 ---
    print(f"正在加载模型: {model_name} ...")

    #  half 精度适配 8GB 显存
    model = SentenceTransformer(
        model_name,
        device="cuda",
        model_kwargs={
            "torch_dtype": torch.float16,
            "device_map": "auto"
        },
        tokenizer_kwargs={"padding_side": "left"}  # 左填充,qwen规定
    )

    # --- 2. 初始化 ChromaDB ---
    # 如果数据库已存在，会直接加载
    client = chromadb.PersistentClient(path=db_path)  # # 在本地创建一个不会消失的客户端
    collection = client.get_or_create_collection(name=collection_name)  # 创建一个现在法律的表

    #  读取 JSON 数据
    if not os.path.exists(json_path):
        print(f"找不到文件: {json_path}，请检查路径。")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        law_data = json.load(f)  # 把json文件变成列表

    print(f"模型准备就绪，开始对 {len(law_data)} 条法条进行向量化...")

    #  准备数据
    documents = [item["content"] for item in law_data]  # 核心
    metadatas = []
    for item in law_data:
        h = item.get("hierarchy", {})

        meta = {
            "source": item["source"],
            "article_number": item["article_number"],
            "book": h.get("book", ""),
            "subbook": h.get("subbook", ""),  # 补全分编 有些数据没有这项 但是chromaDB要求值不为NONE
            "chapter": h.get("chapter", ""),
            "section": h.get("section", "")    # 补全节 有些数据没有这项
        }
        metadatas.append(meta)  #  辅助  筛选  query时用where
    ids = [item["id"] for item in law_data]  # id标识

    #  批量入库
    batch_size = 64
    for i in range(0, len(documents), batch_size):
        end_idx = i + batch_size
        batch_docs = documents[i:end_idx]

        # 编码文档（入库时不带 prompt_name）
        batch_embeddings = model.encode(
            batch_docs,
            batch_size=batch_size,
            convert_to_numpy=True,  # 转成numpy
            show_progress_bar=False
            # prompt_name="document"
        )

        # 存入数据库
        collection.add(
            embeddings=batch_embeddings.tolist(),
            documents=batch_docs,
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx]
        )
        print(f"进度: {min(end_idx, len(documents))}/{len(documents)}")

    print(f"✅ 成功！数据库已保存在: {os.path.abspath(db_path)}")

if __name__ == "__main__":
    run_ingestion()