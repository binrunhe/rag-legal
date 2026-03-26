from search import *
from RAG import *

def main():
    history = [] # 历史记录
    # 设定一个语义距离门槛，Qwen3-Embedding 在 1.0 以上通常相关性就很低了
    distance_threshold = 1.05

    while True:
        user_input = input("\n请输入您的问题:...(q,quit,exit退出.. )\n")
        if user_input.lower() in ['q', 'quit', 'exit']: break

        #  重写请求：将模糊的“上面聊了什么”转为“总结对话” 不然bug会是搜索'上面聊了什么'
        search_query = rewrite_query(user_input, history)

        # 意图预判：如果是询问记忆或闲聊，直接跳过检索
        # 简单判断重写后的词是否包含特定关键词
        skip_words = ["总结", "记忆", "之前", "聊了什么", "你是谁"]
        should_skip_search = any(word in search_query for word in skip_words)

        formatted_docs = []

        if not should_skip_search:
            # 检索
            results = run_search(search_query)

            # 距离太远，则不传给模型
            if results and 'distances' in results and results['distances'][0][0] < distance_threshold:   # 第一个最小的都不行那就都不做了
                for i in range(len(results['documents'][0])):
                    if results['distances'][0][i] < 1.1:
                        formatted_docs.append({
                            "content": results['documents'][0][i],
                            "metadata": results['metadatas'][0][i]
                        })
            else:
                print("本地法律库未匹配到高相关条文，将由模型尝试回答。")
        else:
            print("识别为对话回顾请求，跳过数据库检索。")

        # 生成回答：传入过滤后的文档和历史记录
        # 如果 formatted_docs 为空，Qwen 就会根据 Prompt 里的要求，只看 history 回答
        answer = call_ollama_rag(user_input, formatted_docs, history)

        print("\n" + "="*30 + " 律师建议 " + "="*30)
        print(answer)
        print("="*68)

        # 更新历史
        history.append({"user": user_input, "bot": answer})

if __name__ == "__main__":
    main()