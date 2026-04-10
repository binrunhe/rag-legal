import requests
import json
import os

# --- 新增：读取本地已有法律清单的函数 ---
def get_available_laws():
    """从 registry.json 中提取所有已入库的法律和解释名称"""
    try:
        if not os.path.exists("registry.json"):
            return "暂无清单，请按常识推断。"

        with open("registry.json", "r", encoding="utf-8") as f:
            tasks = json.load(f)

        # 提取文件名并去掉 .docx 后缀
        law_names = [task['docx_name'].replace('.docx', '') for task in tasks]

        # 拼接成带序号的文本
        return "\n".join([f"- {name}" for name in law_names])
    except Exception as e:
        print(f"读取清单失败: {e}")
        return "暂无清单，请按常识推断。"

def rewrite_query(user_query, history, model_name):
    print("\n正在分析用户意图并重写查询...")

    if not history:
        history_str = "无"
    else:
        history_str = "\n".join([f"用户: {h['user']}\n助手: {h['bot']}" for h in history[-2:]])

    # 动态获取菜单
    available_laws_list = get_available_laws()

    # --- 核心改动：把清单加入 Prompt，并强约束它的输出 ---
    prompt = f"""你是一个专业的法律咨询意图解析器。请结合【对话历史】，将用户的【最新提问】改写为一个独立的搜索语句。

    【核心任务要求】：
    1. 提取法条标签：如果用户提到了具体的法律名称和条文编号，请务必在输出最前面用标签标出，格式为：【法律名-第xxx条】。
       - ⚠️警告：必须严格提取用户提问中的条文数字，绝对不许自己瞎编数字！如果用户说“第一条”，就写“第一条”。
       - 注意：数字必须转换为中文大写。
    
    2. 严格遵循可用清单（禁止瞎编）：
       如果用户提到了法律、规定或司法解释的简称（如“侵权解释”、“婚姻法解释”），你【必须】从下方的【本地可用法律清单】中，找出最匹配的全称填入标签。
       绝不允许自己编造清单中没有的法律名字！如果清单里没有对应的，就填【未知】。
       
    3. 语义重写：在标签之后，去除口语化废话，提炼出专业的法律搜索关键词。

    【本地可用法律清单】：
    {available_laws_list}

    【对话历史】：
    {history_str}

    【最新提问】：
    {user_query}

    请直接输出改写后的结果："""

    payload = {"model": model_name, "prompt": prompt, "stream": False}
    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload)
        return response.json().get("response", user_query).strip()
    except Exception as e:
        print(f"大模型请求失败: {e}")
        return user_query

def call_ollama_rag(query_text, retrieved_docs,history,model_name):
    context = ""
    for i, item in enumerate(retrieved_docs):
        meta = item['metadata']
        content = item['content']
        source = meta.get('source', '未知来源')
        levels = [meta.get("book", ""), meta.get("subbook", ""),
                  meta.get("chapter", ""), meta.get("section", "")]
        path = f'{source} >' + " > ".join([l for l in levels if l])

        context += f"【{i+1}】来源：{path} > {meta['article_number']}\n原文：{content}\n\n"

    history_context = "\n".join([f"用户: {h['user']}\n助手: {h['bot']}" for h in history[-3:]])
    prompt = f"""你是一名专业的法律顾问。请根据以下提供的【法律依据】回答用户的【咨询问题】。

【对话历史】：
{history_context}

【法律依据】：
{context}

【咨询问题】：
{query_text}

【回答要求】：
1. 如果用户在询问之前聊过的话题，请直接根据【对话历史】回答，不要强行套用【法律依据】。
2. 如果用户在咨询新法律问题，请优先使用【法律依据】。
3. 保持专业、连贯的对话风格。
4. 必须优先根据法律依据回答。
5. 引用法条时请注明具体的“条”和“编/章”路径。
6. 如果法律依据不足以回答问题，请如实告知。
7.如果给定的原文中没有相关依据，请诚实回答不知道，严禁私自编造法律条文
"""

    # 调用 Ollama
    print(f" 正在链接本地 大语言模型: {model_name}")
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": 4096,  # kv限制，防止 1M 模型吞掉所有显存
            "temperature": 0.3 # 法律咨询建议设低一点，更严谨
        }
    }

    try:
        response = requests.post(url, json=payload)
        return response.json().get("response", "模型响应出错")
    except Exception as e:
        return f"连接 Ollama 失败: {str(e)}"