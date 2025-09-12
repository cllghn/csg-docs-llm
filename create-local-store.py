from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
import dotenv
import os 

dotenv.load_dotenv()

Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-ada-002",
    api_key=os.getenv("CHATGPT_API_KEY")
)

Settings.chunk_size = 512
Settings.chunk_overlap = 50

docs = SimpleDirectoryReader("downloads").load_data()
index = VectorStoreIndex.from_documents(docs)

index.storage_context.persist(persist_dir="./storage")