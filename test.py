import os
from huggingface_hub import scan_cache_dir

print(f"环境变量 HF_HOME: {os.environ.get('HF_HOME')}")

try:
    cache_info = scan_cache_dir()
    print(f"模型实际存储根目录: {cache_info.cached_dir}")
    for repo in cache_info.repos:
        print(f"已识别模型: {repo.repo_id}")
except Exception as e:
    print(f"扫描失败，请检查路径。错误: {e}")