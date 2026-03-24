import docx
import re
import json

def parse_civil_code_perfect(file_path, output_json):
    doc = docx.Document(file_path)
    legal_records = []

    # 状态机：用于记忆当前法条属于哪个层级
    current_book = ""
    current_subbook = ""  # 新增：分编
    current_chapter = ""
    current_section = ""

    # 终极正则匹配（加入了“零”，并匹配各种全半角空格 \u3000）
    re_book = re.compile(r'^(第[一二三四五六七八九十百千零]+编)[\s\u3000]+(.+)$')
    re_subbook = re.compile(r'^(第[一二三四五六七八九十百千零]+分编)[\s\u3000]+(.+)$')
    re_chapter = re.compile(r'^(第[一二三四五六七八九十百千零]+章)[\s\u3000]+(.+)$')
    re_section = re.compile(r'^(第[一二三四五六七八九十百千零]+节)[\s\u3000]+(.+)$')
    re_article = re.compile(r'^(第[一二三四五六七八九十百千零]+条)[\s\u3000]+(.+)$')

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # 1. 匹配“编”
        if re_book.match(text):
            current_book = text
            current_subbook = "" # 层级重置
            current_chapter = ""
            current_section = ""
            continue

        # 2. 匹配“分编”
        if re_subbook.match(text):
            current_subbook = text
            current_chapter = ""
            current_section = ""
            continue

        # 3. 匹配“章”
        if re_chapter.match(text):
            current_chapter = text
            current_section = ""
            continue

        # 4. 匹配“节”
        if re_section.match(text):
            current_section = text
            continue

        # 5. 匹配“条”（核心提取）
        article_match = re_article.match(text)
        if article_match:
            article_num = article_match.group(1)
            content = article_match.group(2)

            record = {
                "id": f"Civil_Code_{article_num}",
                "article_number": article_num,
                "hierarchy": {
                    "book": current_book,
                    "subbook": current_subbook,
                    "chapter": current_chapter,
                    "section": current_section
                },
                "content": content,
                "source": "中华人民共和国民法典"
            }
            legal_records.append(record)
            continue

        # 6. 处理多款落（如某条法律有两段话）
        # 如果当前行不是标题，且 legal_records 不为空，说明这是上一条法条的补充段落
        if legal_records and current_book:
            legal_records[-1]["content"] += "\n" + text

    # 输出为 JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(legal_records, f, ensure_ascii=False, indent=4)

    print(f"解析完美结束！共提取 {len(legal_records)} 条法律。")

# 运行代码
parse_civil_code_perfect("法律原文/中华人民共和国民法典_20200528.docx", "civil_code_1260.json")