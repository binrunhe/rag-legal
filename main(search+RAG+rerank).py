from search import *
from RAG import *
from rerank import *

db_path = "./legal_vector_db"
collection_name = "china_law_library"

search_model_name = "Qwen/Qwen3-Embedding-0.6B"
n_results=10 # search一下子找出多少条数据给rerank

rag_model_name='Lusizo/qwen2.5-7b-instruct-1m:latest'
# distance_threshold = 1.05  优化后retrieve后接rerank,不需要这个阈值了

rerank_model_name=('BAAI/bge-reranker-v2-m3')
max_length=512  # [query,content] 拼接起来塞进模型的最大长度
top_n=3  # 最后取分数最高的前几
threshold=-2  # 阈值,低于的认为不相关

def main():
    history = [] # 历史记录

    while True:
        user_input = input("\n请输入您的问题:...(q,quit,exit退出.. )\n")
        if user_input.lower() in ['q', 'quit', 'exit']: break

        # 重写请求：将模糊的“上面聊了什么”转为“总结对话” 不然bug会是搜索'上面聊了什么'
        search_query = rewrite_query(user_input, history,rag_model_name)

        # 意图预判：如果是询问记忆或闲聊，直接跳过检索
        # 简单判断重写后的词是否包含特定关键词
        skip_words = ["总结", "记忆", "之前", "聊了什么", "你是谁"]
        should_skip_search = any(word in search_query for word in skip_words)

        formatted_docs = []

        if not should_skip_search:
            # 检索 (现在返回的是现成的列表格式)
            raw_docs = run_search(search_query, db_path, collection_name, search_model_name, n_results)

            if raw_docs:
                # 直接喂给重排序函数
                final_results = rerank_context(search_query, raw_docs, rerank_model_name, max_length, top_n, threshold)

                print("\n" + " [透明测试] 最终塞给大模型的法律条文 " )
                if not final_results:
                    print(" 警告：重排后所有法条均被低分过滤，大模型将仅靠自身记忆回答。")
                else:
                    for i, doc in enumerate(final_results):
                        print(f"  条文 {i+1}: {doc['metadata']['source']} - {doc['metadata']['article_number']}")
                print("="*68 + "\n")

                formatted_docs = final_results
            else:
                print("本地法律库未匹配到相关条文，将由模型尝试回答。")

        # 生成回答：传入过滤后的文档和历史记录
        # 如果 formatted_docs 为空，Qwen 就会根据 Prompt 里的要求，只看 history 回答
        answer = call_ollama_rag(user_input, formatted_docs, history,rag_model_name)

        print("\n" + "="*30 + " 律师建议 " + "="*30)
        print(answer)
        print("="*68)

        # 更新历史
        history.append({"user": user_input, "bot": answer})

        # 清理一下碎片,怕显存炸
        torch.cuda.empty_cache()

if __name__ == "__main__":
    main()