# Local RAG (Retrieval-Augmented Generation) Test

## Overview
This project aims to implement a local RAG (Retrieval-Augmented Generation) system using the LlamaIndex and OpenAI APIs. Why you ask? Well so much of our knowledge is stored in archival document or on our website. The idea here is to leverage these technologies to can ingest all this database all this knowledge in a single location, making it easily accessible for retrieval through natural language prompts. 

## Process

```mermaid
flowchart TD
    A[Run pull-files.py] --> B[Collect content from published CSG Justice Center reports]
    B --> C[Run create-store.py]
    C --> D[Ingest and Index Documents]
    D --> E[Store Content in Vector Database]
    E --> F[Run retrieve-trusted.content.py]
    F --> G[Retrieve Relevant Documents for Query]
    G --> H[Generate Response with LlamaIndex & OpenAI]
    H --> I[Return Response to User]
```

After the information is retrieved using `pull-files.py`, the data is stored into a vector index. This process begins with `create-store.py`, this script builds a searchable document database by reading files from a "downloads" folder, breaking them into small chunks, and converting them into vector embeddings using OpenAI's embedding model. It creates an index that enables semantic search through the documents and saves everything to a "./storage" directory for future use - essentially setting up the foundation for a RAG system.

The next step involves running `retrieve-trusted.content.py`, this script completes the RAG system by loading the previously created vector index, performing semantic search to find relevant document chunks based on user queries, and then sending both the question and retrieved excerpts to the LLM (here GPT-5 🚀) with strict instructions to answer only based on the provided content. It operates as a command-line tool and at this point we have added prompt guardrails that ensure responses are somewhat grounded in the actual document collection rather than the AI's general knowledge. With this approach, we hope to improve the accuracy and confidence for transparency. Yet, hallucination are not unavoidable and a real possibility.

## TODO 

- [ ] Explore how to bring down 'projects' (e.g. JRI) rather that just 'documents' from the site
- [ ] Investigate how to curate this input list of documents to remove irrelevant content
- [ ] Add a GUI
- [ ] Investigate a vector database rather than an index

