import requests
import json
import os
from typing import Any, Dict, List

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


def _normalize_history_messages(history: List[Any]) -> List[Dict[str, str]]:
    """
    将 history 统一转换为 role/content 格式：
    [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

    兼容输入：
    1) 新格式：{"role": "user|assistant", "content": "..."}
    2) 旧格式：{"user": "...", "bot": "..."}
    3) Pydantic 对象（如 HistoryMessage）
    """
    normalized: List[Dict[str, str]] = []

    if not history:
        return normalized

    for item in history:
        # 兼容 Pydantic v2 对象
        if hasattr(item, "model_dump"):
            item = item.model_dump()

        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        # 新格式: {role, content}
        if role in ("user", "assistant") and isinstance(content, str):
            text = content.strip()
            if text:
                normalized.append({"role": role, "content": text})
            continue

        # 旧格式: {user, bot}
        user_text = item.get("user")
        bot_text = item.get("bot")

        if isinstance(user_text, str) and user_text.strip():
            normalized.append({"role": "user", "content": user_text.strip()})
        if isinstance(bot_text, str) and bot_text.strip():
            normalized.append({"role": "assistant", "content": bot_text.strip()})

    return normalized


def _history_to_prompt_text(history: List[Any], max_messages: int) -> str:
    messages = _normalize_history_messages(history)

    if not messages:
        return "无"

    recent_messages = messages[-max_messages:]
    return "\n".join(
        [
            f"{'用户' if msg['role'] == 'user' else '助手'}: {msg['content']}"
            for msg in recent_messages
        ]
    )

def rewrite_query(user_query, history, model_name):
    print("\n正在分析用户意图并重写查询...")

    # 保持原有“最近两轮上下文”的语义，按消息数约等于最近 4 条
    history_str = _history_to_prompt_text(history, max_messages=4)

    # 动态获取菜单
    available_laws_list = get_available_laws()

    # --- 核心改动：把清单加入 Prompt，并强约束它的输出 ---
    prompt = f"""你是一个顶级的法律咨询意图解析器。请结合【对话历史】，将用户的【最新提问】改写为一个独立的搜索语句。

【系统内部通讯唯一合法暗号（必须严格遵守）】
你输出的法条标签必须严格使用：
【法律名-第xxx条】

严禁输出以下任何非法格式：
- 【法律名 第xxx条】
- 【法律名第xxx条】
- 法律名:第xxx条
- 其他不带中括号或不带横杠的写法

只要你判断出了法律名和条号，就必须使用带横杠的标准格式输出。

【红线规则（绝对优先，违反即判错）】
1) 数字神圣不可侵犯：
    - 如果用户提问中包含明确条号数字（如“第二条”“第10条”“第十条”），你输出标签时必须且只能使用该数字对应的条号。
    - 严禁以任何理由改写、放大、缩小或替换数字（例如把“第二条”改成“第二百三十二条”）。

2) 禁止过度联想：
    - 当用户提问非常简洁（如“刑法第二条”）时，只提取该条目的核心法律含义关键词。
    - 在用户没有明确提及“杀人”“抢劫”等行为时，严禁自行脑补具体罪名。

3) 指令优先级：
    - 用户输入中的显式数字优先级最高，高于任何示例、经验规则和上下文推断。
    - 若示例与用户显式数字冲突，必须以用户输入数字为准。

【Few-Shot 少样本示例（用于格式演示，不得覆盖用户显式数字）】
示例1：
输入：刑法第二条
输出：【中华人民共和国刑法-第二条】刑法适用范围、法律适用、基本原则

示例2：
输入：我高空抛物了
输出：【中华人民共和国民法典-第一千二百五十四条】高空抛物、侵权责任、过错认定、损害赔偿、举证责任

示例3：
输入：我杀人了
输出：【中华人民共和国刑法-第二百三十二条】故意杀人、刑事责任、量刑标准、主观故意、从重从轻情节

【任务一：格式化法条标签（精准检索专用）】
1. 格式严格为：【法律名-第xxx条】。
2. 提取准则：必须严格提取【最新提问】中的数字并转为中文大写，不得改写为其他条号。
3. 法律名判定：
   - ⚠️ **话题漂移判定**：先判断【最新提问】是否开启了与【对话历史】完全不同的法律领域（如从民事转为刑事）。
   - 如果发生领域大跨度跳转，请果断放弃沿用，将法律名写为“未知”。
   - 只有在逻辑高度连贯（如都在聊离婚或都在聊合同）时，才允许沿用法律名。

【任务二：语义重写（向量搜索专用）】
在标签后增加 3-5 个关键词，必须遵循以下“法学专家”原则：
1. **领域分诊**：先在内心判断这是刑事、民事还是行政。
2. **动词优先**：必须保留用户行为的核心动词（如：杀害、抢劫、自首、坠落、违约）。**严禁将刑事动作（杀人）弱化为民事权利（生命权）。**
3. **术语转化**：将口语（我不小心弄坏了）转化为术语（财产损害、过失侵权）。

【本地可用法律清单】：
{available_laws_list}

【对话历史】：
{history_str}

【最新提问】：
{user_query}

请直接输出改写后的结果（标签 + 关键词）："""

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

    # 保持原有“最近三轮上下文”的语义，按消息数约等于最近 6 条
    history_context = _history_to_prompt_text(history, max_messages=6)
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