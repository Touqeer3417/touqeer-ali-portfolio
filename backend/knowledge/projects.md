# Projects – Touqeer Ali


# 1. Corrective RAG – 

## Project Overview

Corrective RAG is an AI-powered document question-answering system designed to retrieve relevant information from a knowledge base and generate answers using retrieved context.

The project uses a corrective retrieval approach to improve answer quality. It combines traditional keyword-based retrieval with dense vector search and uses an agentic workflow to support more reliable retrieval and answer generation.

## Problem It Solves

Traditional RAG systems can sometimes retrieve irrelevant or incomplete information. When retrieval quality is poor, the language model may generate an inaccurate or insufficient answer.

Corrective RAG aims to address this problem by combining multiple retrieval techniques and introducing a correction-oriented workflow.

## Key Features

- Document-based question answering.
- Hybrid retrieval using BM25 and dense vector search.
- Semantic search for finding contextually relevant information.
- LangGraph-based agentic workflow.
- Retrieval correction and evaluation-oriented processing.
- Qdrant vector database integration.
- LLM-powered answer generation using Groq.
- Web search fallback when document evidence is insufficient.
- FastAPI backend.
- React and TypeScript frontend.

## Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Frontend | React, TypeScript |
| AI Frameworks | LangChain, LangGraph |
| Retrieval | BM25, Dense Vector Search, Hybrid Search |
| Vector Database | Qdrant |
| LLM Integration | Groq |
| Deployment / Infrastructure | Docker, Render |

## Technical Implementation

The system combines keyword-based retrieval and semantic vector retrieval.

- BM25 helps retrieve documents based on keyword relevance.
- Dense vector search finds semantically related content.
- Hybrid retrieval combines the strengths of both approaches.
- LangGraph manages the agentic workflow.
- Qdrant stores and retrieves vector embeddings.
- Groq provides LLM inference.
- External web search can be used when the available document evidence is insufficient.

## Why This Project Matters

This project demonstrates practical knowledge of advanced RAG architecture, hybrid retrieval, agentic workflows, vector databases and evidence-based answer generation.

## Repository and Demo

- GitHub Repository: https://github.com/Touqeer3417/corrective-rag-
- Live Demo: https://corrective-rag-plum.vercel.app/

---

# 2. Document Search RAG – End-to-End Document Search System

## Project Overview

Document Search RAG is an end-to-end Retrieval-Augmented Generation application that allows users to ask questions about their documents and receive AI-generated answers based on retrieved document content.

Instead of relying only on the language model's general knowledge, the system retrieves relevant information from the document collection and uses it as context for generating answers.if the answers is not in document it do the web search 

## Problem It Solves

Reading and searching large documents manually can be time-consuming.

This project provides a conversational way to explore document information, locate relevant content and ask questions using natural language.

## Key Features

- Document-based question answering.
- Retrieval-Augmented Generation pipeline.
- Document processing and text retrieval.
- Semantic vector search.
- ChromaDB vector database integration.
- OpenAI embeddings.
- Groq LLM integration.
- LLaMA 3.3 70B model integration.
- Streamlit-based user interface.
- Tavily web search fallback.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| User Interface | Streamlit |
| RAG Framework | LangChain |
| Vector Database | ChromaDB |
| Embeddings | OpenAI Embeddings |
| LLM | Groq – LLaMA 3.3 70B |
| Web Search | Tavily |

## Technical Implementation

The application follows a typical RAG workflow:

1. Documents are processed and converted into text.
2. Text is divided into smaller chunks.
3. OpenAI embeddings convert text chunks into vector representations.
4. ChromaDB stores the embeddings.
5. A user submits a natural-language question.
6. The retriever searches for relevant document chunks.
7. Retrieved context is passed to the language model.
8. The model generates an answer using the available context.

Tavily is integrated as a web-search fallback for cases where additional external information is needed.

The project initially used Qdrant and was later adapted to use local ChromaDB.

## Why This Project Matters

This project demonstrates practical understanding of the complete RAG pipeline, including document processing, chunking, embeddings, vector storage, retrieval, LLM integration and conversational question answering.

## Repository

- GitHub Repository: https://github.com/Touqeer3417/End-to-End-Rag-Docuemnt-Search-Project

---

# 3. LifeOps AI – AI-Powered Personal Productivity Assistant

## Project Overview

LifeOps AI is an AI-powered productivity assistant designed to bring personal productivity and daily workflow management into one application.

The project combines an interactive frontend, backend services, authentication, database storage and AI-related capabilities.

## Problem It Addresses

People often use multiple applications to manage daily tasks, information and schedules.

LifeOps AI aims to provide a more integrated experience by connecting productivity-related functionality with an AI-powered application.

## Technology Stack

| Category | Technologies |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| Vector Search | pgvector |
| Authentication | Auth0 |
| Integrations | Google Calendar OAuth, Gmail |

## Main Technical Components

- React-based user interface.
- FastAPI backend for application services.
- PostgreSQL for structured data storage.
- pgvector for vector-related functionality.
- Auth0 authentication integration.
- Google Calendar OAuth integration.
- Gmail integration.

## Project Architecture

The application uses a frontend-backend architecture.

- React and Vite provide the frontend.
- FastAPI handles backend operations.
- PostgreSQL manages application data.
- pgvector supports vector storage and similarity-search functionality.
- Auth0 handles authentication.
- Google Calendar and Gmail integrations connect external productivity services.

## Why This Project Matters

LifeOps AI demonstrates the integration of modern web technologies, backend development, authentication, database systems and external services in an AI-oriented productivity application.

Note: This description documents the known architecture and integrations. It does not claim that every planned feature is fully implemented or publicly deployed.

---

# 4. Portfolio AI Assistant – Personal Knowledge-Based RAG Chatbot

## Project Overview

The Portfolio AI Assistant is an AI-powered chatbot integrated into Touqeer Ali's personal portfolio website.

Its purpose is to help potential clients, recruiters and visitors learn about Touqeer through natural-language conversations.

Instead of manually browsing multiple portfolio pages, visitors can ask questions and receive answers based on Touqeer's personal and professional knowledge base.

## Problem It Solves

Visitors may want to quickly understand:

- Who Touqeer is.
- What technologies he works with.
- Which projects he has developed.
- What services he is interested in offering.
- How to contact him.
- Whether his technical experience matches their requirements.

The chatbot provides a conversational interface for accessing this information.

## Knowledge Base Structure

The assistant uses separate Markdown knowledge files:

- about.md – Personal introduction, education and background.
- skills.md – Technical skills, tools and technologies.
- projects.md – Project descriptions, features and technology stacks.
- services.md – AI and software development services.
- contact.md – Contact details and professional links.

## Main Capabilities

- Answer questions about Touqeer's background.
- Explain his technical skills.
- Describe his AI and RAG projects.
- Provide information about his development interests and services.
- Share available contact information.
- Respond to questions in English.
- Support Roman Urdu conversations.

## RAG Architecture

The assistant follows a knowledge-base-driven retrieval approach.

1. Markdown knowledge files provide the source information.
2. The backend processes the knowledge-base content.
3. Relevant information is retrieved based on the visitor's question.
4. Retrieved context is provided to the language model.
5. The model generates a response grounded in the available information.

## Why This Project Matters

This project demonstrates how RAG can be applied to a real-world portfolio use case.

It also shows how a knowledge assistant can help visitors access professional information through natural-language interaction.

## Portfolio

- Website: https://touqeerali.dev/
- GitHub: https://github.com/Touqeer3417/touqeer-ali-portfolio

---
