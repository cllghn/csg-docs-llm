import streamlit as st
from openai import OpenAI
from llama_cloud_services import LlamaCloudIndex

AVAILABLE_INDEXES = {
    'csg-docs': 'General Purpose Index (default)',
    'csg-docs-2': 'JRI Documents Index', 
    'csg-adc-reports': 'Corrections Reports Index (coming soon!)'
}

# Initialize the LlamaCloud index
@st.cache_resource
def initialize_index(index_name: str):
    try:
        index = LlamaCloudIndex(
            name=index_name,
            project_name="Default",
            organization_id="f76af4a9-a7d3-4e76-8171-9d45e587eac1",
            api_key=st.secrets["LLAMA_CLOUD_API_KEY"]
        )
        return index

    except Exception as e:
        st.error(f"Error initializing LlamaCloud index: {e}")
        st.stop()

@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=st.secrets['openai_key'])

def retrieve_trusted_content(index: LlamaCloudIndex, query: str, top_k: int, 
                             min_similarity: float = 0.6):
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)
    filtered_nodes = [node for node in nodes if node.score >= min_similarity]
    print(filtered_nodes)

    if not filtered_nodes:
        return ["<no_relevant_content>No sufficiently relevant content found.</no_relevant_content>"]
    print(filtered_nodes)
    return [f"<excerpt confidence=\"{node.score:.2f}\" source=\"{node.metadata.get('id', '')}\" page=\"{node.metadata.get('page_label', '')}\">{node.text}</excerpt>"  
            for node in filtered_nodes]

def chat_with_retrieval(query: str, conversation_history: list, index_name: str, 
                        retrieve_n: int):
    # Get trusted content first
    index = initialize_index(index_name=index_name)
    excerpts = retrieve_trusted_content(index=index, query=query, 
                                        top_k=retrieve_n)
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
    - Always tell me the name of the report that you pulled the excerpts from and if information is coming from multiple reports note it. Include those sources at the bottom of the response.
    - Tell me what pages the information is coming from in the response.
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
        model="gpt-5",
        messages=messages,
        temperature=1,  # Default is 1 for gpt-5
        stream=True
    )
    
    return response

def main():
    # App configuration ========================================================
    st.set_page_config(page_title="CSG Justice Center GAMBLER", page_icon="🦙", 
                       layout="centered",
                       initial_sidebar_state="expanded",
                       menu_items={
                           'Report a bug': 'https://github.com/cllghn/csg-docs-llm/issues'
                           }
                        )

    # Sidebar ==================================================================
    # Inject custom CSS to set the width of the sidebar
    # https://discuss.streamlit.io/t/specify-sidebar-width/45866/5
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                min-width: 350px !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Hide the collapse button of the sidebar
    st.markdown(
        """
        <style>
        [data-testid="stSidebarCollapseButton"] {
            display: none
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.header("GAMBLER Configuration")

    # Set up a dropdown to select the document index ---------------------------
    # Initialize selected index in session state if not present
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = list(AVAILABLE_INDEXES.keys())[0]

    # Create selectbox for index selection
    selected_index = st.sidebar.selectbox(
        "Select Document Index:",
        options=list(AVAILABLE_INDEXES.keys()),
        format_func=lambda x: AVAILABLE_INDEXES[x],
        index=list(AVAILABLE_INDEXES.keys()).index(st.session_state.selected_index),
        help="Choose which document index to search. Different indexes may contain different sets of documents curated for different purposes."
    )
    
    # If index changed, clear conversation history
    if selected_index != st.session_state.selected_index:
        st.session_state.selected_index = selected_index
        st.session_state.messages = []
        st.rerun()

    # Set up a slider to change the top value of retrieved excerpts ------------
    if "top_n" not in st.session_state:
        st.session_state.top_n = 5
    
    top_n = st.sidebar.slider(
        "Number of Retrieved Excerpts for Summary:",
        min_value=3,
        max_value=15,
        value=st.session_state.top_n,
        help="Number of top relevant excerpts to retrieve from the index. More documents may provide better context but can also introduce noise."
    )

    # Set up a slider to change the minimum similarity threshold ---------------
    if "min_similarity" not in st.session_state:
        st.session_state.min_similarity = 0.65

    min_similarity = st.sidebar.slider(
        "Minimum Similarity Threshold:",
        min_value=0.5,
        max_value=1.0,
        value=st.session_state.min_similarity,
        step=0.1,
        help="Minimum similarity threshold for retrieved excerpts, between 0.5 and 1.0. Lower values will yield less relevant results."
    )

    # Check if selected index is coming soon
    is_coming_soon = "(coming soon!)" in AVAILABLE_INDEXES[selected_index].lower()
    if is_coming_soon:
        st.sidebar.warning("This index is coming soon! Please check back later.", icon="🚧")
    else:
        st.sidebar.info(f"You would be currently retrieving **up to {top_n} excerpts** for summary **from the {AVAILABLE_INDEXES[selected_index]} index**.", icon="ℹ️")


    # Contact info -------------------------------------------------------------
    st.markdown(
        """
        <div style="
            position: fixed;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.95);
            padding: 8px 16px;
            font-size: 14px;
            text-align: center;
            border-top: 1px solid #eee;
            z-index: 9999;
        ">
            Developed with ❤️ and <a href="https://github.com/cllghn/csg-docs-llm" target="_blank">version control</a> by <a href="mailto:ccallaghan@csg.org">Chris Callaghan</a>. 
            Report bugs or request features on <a href="https://github.com/cllghn/csg-docs-llm/issues" target="_blank">GitHub</a>.
        </div>

        <!-- spacer to prevent the fixed footer from overlapping page content -->
        <div style="height:48px;"></div>
        """,
        unsafe_allow_html=True,
    )

    # Main app =================================================================
    st.markdown("# CSG Justice Center: *G*uided *A*ggregation of *M*aterials and *B*riefs using *L*arge-Language Models and *E*nhanced *R*ules (GAMBLER)🦙")
    
    st.warning('This application is an **experiment**, please use it accordingly and verify any critical information.', icon="⚠️")

    # # Initialize the index and OpenAI client
    # index = initialize_index()
    
    
    st.markdown("Enter your query to search the CSG Justice Center documents index. " \
                "The system will retrieve relevant content from the index. That content is then summarized by the LLM. You will then be presented with a response. " \
                "Keep in mind that index is **very** limited in scope, so the answers might be incomplete, out of date, or worse.")
   
    client = get_openai_client()
    
    # Check if 'messages' exists in session state; otherwise; initialize it
    if "messages" in st.session_state:
        messages = st.session_state.messages
    else:
        messages = []
        st.session_state.messages = messages

    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Check if selected index is coming soon
    is_coming_soon = "(coming soon!)" in AVAILABLE_INDEXES[selected_index].lower()
    if is_coming_soon:
        st.chat_input("Ask me about CSG Justice Center documents in the selected index...", 
                      disabled=True)

    elif prompt := st.chat_input("Ask me about CSG Justice Center documents in the selected index..."):
        # Add user message to chat history
        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and stream assistant response
        with st.chat_message("assistant"):
            try:
                # Show a spinner and progress bar while retrieving and streaming the response
                with st.spinner("Retrieving trusted content and generating response..."):
                    response_stream = chat_with_retrieval(prompt, messages[:-1], 
                                                          index_name=selected_index, 
                                                          retrieve_n=top_n) 

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
