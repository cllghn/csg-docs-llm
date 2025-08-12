from openai import OpenAI
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
import dotenv
import os
import sys

dotenv.load_dotenv()

# Configure embedding model (same as used when creating the index)
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-ada-002",
    api_key=os.getenv("CHATGPT_API_KEY")
)

storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context)

def retrieve_trusted_content(query: str, top_k: int = 5, min_similarity: float = 0.7):
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)
    filtered_nodes = [node for node in nodes if node.score >= min_similarity]
    
    if not filtered_nodes:
        return ["<no_relevant_content>No sufficiently relevant content found.</no_relevant_content>"]
    
    return [f"<excerpt confidence=\"{node.score:.2f}\">{node.text}</excerpt>" 
            for node in filtered_nodes]

client = OpenAI(api_key=os.getenv("CHATGPT_API_KEY"))

def chat_with_retrieval(query: str):
    # Get trusted content first
    excerpts = retrieve_trusted_content(query)
    
    # Create system message
    system_message = """
    You are a helpful, but terse, assistant.
    If you can't answer the question based on the trusted content, say so.

    STRICT RULES:
    - Only use information explicitly stated in the <excerpt> tags
    - If the excerpts don't contain enough information to answer the question, say "The provided content does not contain sufficient information to answer this question"
    - Always cite which excerpt(s) you're using by referencing the confidence scores
    - Never make assumptions or fill in gaps with outside knowledge
    - If confidence scores are low (<0.7), mention this uncertainty in your response
    - Always tell me the name of the report that you pulled the excerpts from and if information is coming from multiple reports note it.
    """

    # Create user message with retrieved content
    user_message = f"""Question: {query}

    Trusted content:
    {chr(10).join(excerpts)}

    Please answer the question based only on the provided trusted content above."""

    # Make the API call
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        temperature=1  # Defaul is 1 for gpt-5
    )
    
    return response.choices[0].message.content


def main():
    # Check if question was provided as command line argument
    if len(sys.argv) < 2:
        print("Please provide a question as a command line argument.")
        print("Usage: python script.py \"Your question here\"")
        print("Example: python script.py \"What have we written about the strategies for reducing recidivism among young adults in the justice system?\"")
        sys.exit(1)
   
    # Join all arguments after the script name to handle multi-word questions
    query = " ".join(sys.argv[1:])
   
    print(f"Question: {query}")
    print("-" * 50)
    print("⚠️  DISCLAIMER: This response is AI-generated based on document retrieval.")
    print("Please verify important information with original sources.")
    print("-" * 50)
   
    try:
        answer = chat_with_retrieval(query)
        print(answer)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    try:
        answer = chat_with_retrieval(query)
        print(answer)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()