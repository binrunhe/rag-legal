import docx
import re
import json
import os

def parse_code_perfect(file_path, output_json,English_name):
    doc = docx.Document(file_path)
    legal_records = []

    file_name = os.path.basename(file_path)  # 提取文件名 包含后缀
    file_name_without_ext = os.path.splitext(file_name)[0]  # 去掉文件后缀
    # 按第一个"_"分割，取前面的部分作为source；如果没有"_"，则用完整的文件名（去后缀）
    source_name = file_name_without_ext.split('_')[0] if '_' in file_name_without_ext else file_name_without_ext

    # 层级
    current_book = ""     # 编
    current_subbook = ""  # 分编
    current_chapter = ""  # 章
    current_section = ""  # 节

    # 正则
    re_book = re.compile(r'^(第[一二三四五六七八九十百千零]+编)[\s\u3000]+(.+)$')
    re_subbook = re.compile(r'^(第[一二三四五六七八九十百千零]+分编)[\s\u3000]+(.+)$')
    re_chapter = re.compile(r'^(第[一二三四五六七八九十百千零]+章)[\s\u3000]+(.+)$')
    re_section = re.compile(r'^(第[一二三四五六七八九十百千零]+节)[\s\u3000]+(.+)$')
    re_article = re.compile(r'^(第[一二三四五六七八九十百千零]+条)[\s\u3000]+(.+)$')
    re_appendix = re.compile(r'^附[\s\u3000]*则$')

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # 优先解决最后的附则
        if re_appendix.match(text):
            current_book = "附则"  # 把附则作为编
            current_subbook = ""
            current_chapter = ""
            current_section = ""
            continue
        # 匹配各级标题
        if re_book.match(text):
            current_book = text
            current_subbook = ""
            current_chapter = ""
            current_section = ""
            continue
        if re_subbook.match(text):
            current_subbook = text
            current_chapter = ""
            current_section = ""
            continue
        if re_chapter.match(text):
            current_chapter = text
            current_section = ""
            continue
        if re_section.match(text):
            current_section = text
            continue

        # 匹配“条”并构建记录 只有有条才会创建记录,略去了目录中的内容
        article_match = re_article.match(text)
        if article_match:
            article_num = article_match.group(1)
            content = article_match.group(2)
            record = {
                "id": f"{English_name}_{article_num}", # 后面想用其他法律这里要改前缀
                "article_number": article_num,
                "hierarchy": {
                    "book": current_book,
                    "subbook": current_subbook,
                    "chapter": current_chapter,
                    "section": current_section
                },
                "content": content,
                "source": source_name
            }
            legal_records.append(record)
            continue

        # 处理多款落补充内容
        if legal_records and current_book:
            legal_records[-1]["content"] += "\n" + text

    #  创建文件夹
    output_dir = os.path.dirname(output_json)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 写入文件
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(legal_records, f, ensure_ascii=False, indent=4)

    print(f"解析结束！共提取 {len(legal_records)} 条法律。")
    print(f"文件已保存至：{os.path.abspath(output_json)}")  # 输出绝对路径


# parse_code_perfect("法律原文/中华人民共和国刑法_20201226.docx", "code_json/criminal_law_452.json",'Criminal_law')