from sentence_transformers import CrossEncoder

# 把search找到的results再塞进rerank,找到更相近的
def rerank_context(query, raw_docs, model_name ,max_length,top_n=3, threshold=-5):

    rerank_model = CrossEncoder(model_name, max_length=max_length)

    if not raw_docs:
        return []

    # 构造交叉编码器的输入对：[[问题, 法条1], [问题, 法条2], ...]
    # 注意：search_results 里面包含 content 和 metadata   不能只有content,不然做完之后就不知道这个东西来自哪里了
    # search函数的结果results是字典. (results[documents][0]才能得到所有的content),要与metadatas一对一,转成列表
    # 拿出results[0]里的每一项的content(或documents)和metadata构成raw_docs [{"content": d, "metadata": m}......]方便rerank函数求值与排序
    input_pairs = [[query, doc['content']] for doc in raw_docs]

    # 模型打分
    scores = rerank_model.predict(input_pairs)

    # 将分数写回结果中并排序
    for i in range(len(raw_docs)):
        raw_docs[i]['rerank_score'] = float(scores[i])

    # 按 Rerank 分数从高到低排序
    sorted_results = sorted(raw_docs, key=lambda x: x['rerank_score'], reverse=True)

    # 阈值过滤：只保留真正相关的
    final_results = [res for res in sorted_results if res['rerank_score'] >= threshold]
    final_results=final_results[:top_n]

    for i, res in enumerate(final_results):
        score = res.get('rerank_score', 0)
        source = res['metadata'].get('source', '未知来源')
        article = res['metadata'].get('article_number', '未知编号')
        content = res['content'].replace('\n', ' ') # 压缩一下换行，方便预览

        print(f"【排名 {i+1}】  Rerank得分: {score:.4f}")
        print(f" 来源: {source} | 编号: {article}")
        print(f" 内容: {content}...")
        print("-" * 60)

    return final_results