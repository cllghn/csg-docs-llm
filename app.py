import streamlit as st
from openai import OpenAI
from llama_cloud_services import LlamaCloudIndex

# Initialize the LlamaCloud index
@st.cache_resource
def initialize_index():
    try:
        index = LlamaCloudIndex(
            name="csg-docs-2",
            project_name="Default",
            organization_id="f76af4a9-a7d3-4e76-8171-9d45e587eac1",
            api_key=st.secrets["LLAMA_CLOUD_API_KEY"],
        )
        return index

    except Exception as e:
        st.error(f"Error initializing LlamaCloud index: {e}")
        st.stop()

@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=st.secrets['openai_key'])

def retrieve_trusted_content(index: LlamaCloudIndex, query: str, top_k: int = 5, min_similarity: float = 0.1):
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)
    filtered_nodes = [node for node in nodes if node.score >= min_similarity]
    
    if not filtered_nodes:
        return ["<no_relevant_content>No sufficiently relevant content found.</no_relevant_content>"]
    
    return [f"<excerpt confidence=\"{node.score:.2f}\">{node.text}</excerpt>" 
            for node in filtered_nodes]

def chat_with_retrieval(query: str):
    # Get trusted content first
    index = initialize_index()
    excerpts = retrieve_trusted_content(index=index, query=query)
    print(excerpts)
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
    st.set_page_config(page_title="CSG Justice Center GAMBLER", page_icon="🦙", layout="centered")
    st.markdown("# CSG Justice Center: *G*uided *A*ggregation of *M*aterials and *B*riefs using *L*arge-Language Models and *E*nhanced *R*ules (GAMBLER)🦙")
    
    st.warning('This application is an **experiment**, please use it accordingly and verify any critical information.', icon="⚠️")

    st.markdown("Enter your query to search the CSG Justice documents index. " \
                "The system will retrieve relevant content. That content is then summarized by the LLM. You will then be presented with a response based on that generative process. " \
                "Keep in mind that index is **very** limited in scope and that the team is continuously working to expand it.")
   
    # Initialize the index and OpenAI client
    index = initialize_index()
    client = get_openai_client()
    
    st.divider()

    # Query input
    query = st.text_input("Enter your query below:", 
                          placeholder="What would you like to know? For example, 'What is Justice Reinvestment?'",
                          help="Type your question here and click Search.")
   
    if st.button("Search") and query:
        with st.spinner("Searching..."):
            try:
                # Get response from query engine
                response = chat_with_retrieval(query)
               
                st.subheader("Response:")
                st.write(response)
                
            except Exception as e:
                st.error(f"Error during search: {e}")

if __name__ == "__main__":
    main()