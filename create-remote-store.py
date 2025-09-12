from llama_cloud_services import LlamaCloudIndex
import dotenv
import os 

dotenv.load_dotenv()

index = LlamaCloudIndex.create_index(
    name="csg-docs-2",
    project_name="Default",
    organization_id="f76af4a9-a7d3-4e76-8171-9d45e587eac1",
    api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
    # embedding_config={
    #     "type": "OPENAI_EMBEDDING",
    #     "model_name": "text-embedding-3-small",
    #     "api_key": os.getenv("CHATGPT_API_KEY")
    # },
    transform_config={
        "chunk_size": 512,
        "chunk_overlap": 50
        }
)

files = os.listdir("downloads")

for file in files:
    if file.endswith(".pdf"):
        print(f"Adding {file} to index...")
        index.upload_file(file_path=os.path.join("downloads", file), 
                          wait_for_ingestion=True)
