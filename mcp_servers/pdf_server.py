#!/usr/bin/env python3
"""
MCP Server for PDF Processing
Handles PDF reading and question answering with local LLM for privacy
"""
import os
from pathlib import Path
from typing import List
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import ChatOllama
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("PDFServer")

# Global state for loaded PDFs
pdf_store = None
loaded_files = []


@mcp.tool()
def load_pdf(file_path: str) -> str:
    """
    Load a PDF file for processing. Uses local embeddings for privacy.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        Status message
    """
    global pdf_store, loaded_files
    
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"
        
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_text(text)
        
        embeddings = OllamaEmbeddings(model="llama2")
        
        if pdf_store is None:
            pdf_store = Chroma.from_texts(
                chunks,
                embeddings,
                metadatas=[{"source": file_path}] * len(chunks)
            )
        else:
            pdf_store.add_texts(
                chunks,
                metadatas=[{"source": file_path}] * len(chunks)
            )
        
        loaded_files.append(file_path)
        return f"Successfully loaded PDF: {file_path} ({len(reader.pages)} pages, {len(chunks)} chunks)"
    
    except Exception as e:
        return f"Error loading PDF: {str(e)}"


@mcp.tool()
def ask_pdf_question(question: str) -> str:
    """
    Ask a question about loaded PDF files. Uses local LLM for privacy.
    
    Args:
        question: Question about the PDF content
    
    Returns:
        Answer based on PDF content
    """
    global pdf_store, loaded_files
    
    try:
        if pdf_store is None or not loaded_files:
            return "No PDF files loaded. Please load a PDF first using load_pdf()."
        
        relevant_docs = pdf_store.similarity_search(question, k=3)
        
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        sources = set([doc.metadata["source"] for doc in relevant_docs])
        
        llm = ChatOllama(model="mistral", temperature=0.3)
        
        prompt = f"""Based on the following PDF content, answer the question.
If the answer is not in the provided content, say so.

Context:
{context}

Question: {question}

Answer:"""
        
        response = llm.invoke(prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        return f"{answer}\n\nSources: {', '.join(sources)}"
    
    except Exception as e:
        return f"Error answering question: {str(e)}"


@mcp.tool()
def list_loaded_pdfs() -> str:
    """
    List all currently loaded PDF files.
    
    Returns:
        List of loaded PDF files
    """
    global loaded_files
    
    if not loaded_files:
        return "No PDF files currently loaded."
    
    return "Loaded PDF files:\n" + "\n".join([f"- {f}" for f in loaded_files])


if __name__ == "__main__":
    mcp.run(transport="stdio")
