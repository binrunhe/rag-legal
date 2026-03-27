from data_process import *
from injest import *

# 需修改的参数
docx_name='最高人民法院关于适用《中华人民共和国民法典》侵权责任编的解释（一）_20240925.docx'
json_name='tort_liability_interpretation_1_26.json'
English_name='Tort_Liability_Interpretation_1'
file_path=f'司法解释/中华人民共和国民法典/{docx_name}'   # 法律原文或司法解释下对应法律的目录
output_json=f'interpretation_json/{json_name}' # code_json或interpretation_json
# 测试
# docx_name='中华人民共和国民法典_20200528.docx'
# json_name='civil_code_1260.json'
# English_name='Civil_Code'
# file_path=f'法律原文/{docx_name}'   # 法律原文或司法解释下对应法律的目录
# output_json=f'code_json/{json_name}' # code_json或interpretation_json

# 无需修改的参数
json_path=output_json
db_path = "./legal_vector_db"  # 向量库存放地址
collection_name = "china_law_library"  # 向量库中的集合名称 都用一个集合,一起搜
model_name = "Qwen/Qwen3-Embedding-0.6B"

if __name__ == "__main__":
    if '关于' in docx_name or '解释' in docx_name:
        print(f"检测为 司法解释 ，使用对应解析器...")
        parse_interpretation_perfect(file_path, output_json)
    else:
        print(f"检测为 法律条文 ，使用对应解析器...")
        parse_code_perfect(file_path, output_json,)
    run_ingestion(json_path,db_path,collection_name,model_name)