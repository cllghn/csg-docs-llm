import streamlit as st
from openai import OpenAI
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
import os
import dotenv

dotenv.load_dotenv()
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-ada-002",
    api_key=os.getenv("CHATGPT_API_KEY")
)

@st.cache_resource
def initialize_index():
    try:
        # Path to your local storage directory
        storage_dir = "./storage"  # Adjust this path as needed
        
        if not os.path.exists(storage_dir):
            st.error(f"Storage directory '{storage_dir}' not found. Please ensure your index is built and stored in this location.")
            st.stop()
        
        # Load the storage context
        storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
        
        # Load the index from storage
        index = load_index_from_storage(storage_context)
        
        return index

    except Exception as e:
        st.error(f"Error loading local index: {e}")
        st.stop()

@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=st.secrets['openai_key'])

def retrieve_trusted_content(index, query: str, top_k: int = 5, 
                             min_similarity: float = 0.6):
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)
    filtered_nodes = [node for node in nodes if node.score >= min_similarity]
    print(filtered_nodes)

    if not filtered_nodes:
        return ["<no_relevant_content>No sufficiently relevant content found.</no_relevant_content>"]
    
    return [f"<excerpt confidence=\"{node.score:.2f}\" source=\"{node.metadata.get('file_name', node.metadata.get('id', ''))}\">{node.text}</excerpt>" 
            for node in filtered_nodes]

def chat_with_retrieval(query: str, conversation_history: list):
    # Get trusted content first
    index = initialize_index()
    excerpts = retrieve_trusted_content(index=index, query=query)
    # print(excerpts)
    client = get_openai_client()
    
    # Create system message
    system_message = """
    You are a helpful, but terse, assistant.
    If you can't answer the question based on the trusted content, say so.

    STRICT RULES:
    - Only use information explicitly stated in the <excerpt> tags
    - If the excerpts don't contain enough information to answer the question, say "The provided content does not contain sufficient information to answer this question"
    - Always cite which excerpt(s) you're using by referencing the confidence scores
    - Never make assumptions or fill in gaps with outside knowledge
    - If confidence scores are lower (0.7 to 0.8), mention this uncertainty in your response
    - If the confidence scores are high (0.8+), you can be more definitive in your response
    - Always tell me the name of the document/file that you pulled the excerpts from and if information is coming from multiple documents note it. Include those sources at the bottom of the response. 
    """
    # Build conversation with retrieved content
    messages = [{"role": "system", "content": system_message}]

    # Add conversation history
    messages.extend(conversation_history)

    # Create user message with retrieved content
    user_message = f"""Question: {query}

    Trusted content:
    {chr(10).join(excerpts)}

    Please answer the question based only on the provided trusted content above."""

    messages.append({"role": "user", "content": user_message})

    # Make the API call
    response = client.chat.completions.create(
        model="gpt-4o",  # Changed from gpt-5 to gpt-4o (more commonly available)
        messages=messages,
        temperature=0.7,  # Slightly lower temperature for more consistent responses
        stream=True
    )
    
    return response

def main():
    st.set_page_config(page_title="Local Document Search", page_icon="🔍", layout="centered")
    st.markdown("# CSG Justice Center: Local *G*uided *A*ggregation of *M*aterials and *B*riefs using *L*arge-Language Models and *E*nhanced *R*ules (Local GAMBLER)🦙")
    
    st.warning('This application is an **experiment**, please use it accordingly and verify any critical information.', icon="⚠️")

    st.markdown("Enter your query to search your local document index. " \
                "The system will retrieve relevant content from your local storage. That content is then summarized by the LLM. " \
                "Keep in mind that the index scope depends on the documents you've indexed.")
   
    # Initialize the index and OpenAI client
    index = initialize_index()
    client = get_openai_client()
    
    # Check if 'messages' exists in session state; otherwise initialize it
    if "messages" in st.session_state:
        messages = st.session_state.messages
    else:
        messages = []
        st.session_state.messages = messages

    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    if prompt := st.chat_input("Ask me about your documents..."):
        # Add user message to chat history
        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and stream assistant response
        with st.chat_message("assistant"):
            try:
                # Show a spinner while retrieving and streaming the response
                with st.spinner("Retrieving trusted content and generating response..."):
                    response_stream = chat_with_retrieval(prompt, messages[:-1])  # Exclude current message

                    # Stream the response
                    response_placeholder = st.empty()
                    full_response = ""

                    for chunk in response_stream:
                        # Append streamed content when present
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            response_placeholder.markdown(full_response + "▌")

                    response_placeholder.markdown(full_response)

                    # Add assistant response to chat history
                    messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                error_msg = f"Error during search: {e}"
                st.error(error_msg)
                messages.append({"role": "assistant", "content": error_msg})

        # Update session state
        st.session_state.messages = messages

if __name__ == "__main__":
    main()