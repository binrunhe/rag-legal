from data_process import *
from inject import *

# 需修改的参数
docx_name='中华人民共和国民法典_20200528.docx'
json_name='civil_code_1260.json'
English_name='Civil_code'

# 无需修改的参数
file_path=f'法律原文/{docx_name}'
output_json=f'code_json/{json_name}'
json_path=output_json
db_path = "./legal_vector_db"  # 向量库存放地址
collection_name = "china_law_library"  # 向量库中的集合名称 都用一个集合,一起搜
model_name = "Qwen/Qwen3-Embedding-0.6B"

if __name__ == "__main__":
    parse_code_perfect(file_path, output_json, English_name)
    run_ingestion(json_path,db_path,collection_name,model_name)