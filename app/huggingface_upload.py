from huggingface_hub import HfApi
import os

REPO_ID = "soy8itte/gliner2-system-diagram"

# ✅ adapter_config.json 이 들어있는 폴더
FOLDER_PATH = os.path.join("app", "models", "output9_r_16", "best")

api = HfApi()

# 1) 모델 repo 생성 (이미 있으면 유지)
api.create_repo(
    repo_id=REPO_ID,
    repo_type="model",
    private=True,
    exist_ok=True,
)

# 2) LoRA adapter 폴더 업로드
api.upload_folder(
    repo_id=REPO_ID,
    repo_type="model",
    folder_path=FOLDER_PATH,
)

print(f"✅ Hugging Face adapter upload completed: {REPO_ID}")
