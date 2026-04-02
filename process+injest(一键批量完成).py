import json
import os
from data_process import parse_code_perfect, parse_interpretation_perfect
from injest import run_ingestion  # 确保你之前的 run_ingestion 已经改成了单例加载模型

# 固定参数
db_path = "./legal_vector_db"
collection_name = "china_law_library"
model_name = "Qwen/Qwen3-Embedding-0.6B"

def start_batch_work():
    # 加载注册表
    if not os.path.exists("registry.json"):
        print(" 错误：找不到 registry.json，请先运行 create_registry.py")
        return

    with open("registry.json", "r", encoding="utf-8") as f:
        tasks = json.load(f)

    print(f"所有待处理文件信息加载成功，共 {len(tasks)} 项任务准备就绪...\n")

    #  循环执行：解析 + 入库
    for i, task in enumerate(tasks):
        docx_name = task['docx_name']
        full_path = task['full_path']
        task_type = task['type']
        output_json = task['output_json']

        print(f" [任务 {i+1}/{len(tasks)}] 正在处理: {docx_name}")

        try:
            # 解析过程
            # 法律原文或是司法解释 用不同解析函数
            if task_type == 'code':
                parse_code_perfect(full_path, output_json)
            else:
                parse_interpretation_perfect(full_path, output_json)

            # 入库过程
            run_ingestion(
                json_path=output_json,
                db_path=db_path,
                collection_name=collection_name,
                model_name=model_name,
            )

            print(f"{docx_name} 处理并入库成功！")

        except Exception as e:
            print(f" 任务 {i+1} 出错: {docx_name}")
            print(f" 原因: {str(e)}")
            continue

    print("\n" + "="*50)
    print("一键处理全部任务完成.")
    print("-"*50)

if __name__ == "__main__":
    start_batch_work()