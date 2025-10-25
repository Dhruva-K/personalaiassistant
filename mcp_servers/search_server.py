#!/usr/bin/env python3
"""
MCP Server for Internet Search
Handles web searching for real-time information
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SearchServer")


@mcp.tool()
def search_web(query: str, num_results: int = 5) -> str:
    """
    Search the web for information.
    
    Args:
        query: Search query
        num_results: Number of results to return (default: 5)
    
    Returns:
        Search results with titles, URLs, and snippets
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num={num_results}"
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = []
        
        for g in soup.find_all('div', class_='g')[:num_results]:
            title_elem = g.find('h3')
            link_elem = g.find('a')
            snippet_elem = g.find('div', class_=['VwiC3b', 'yXK7lf'])
            
            if title_elem and link_elem:
                title = title_elem.get_text()
                link = link_elem.get('href')
                snippet = snippet_elem.get_text() if snippet_elem else "No description available"
                
                search_results.append({
                    'title': title,
                    'url': link,
                    'snippet': snippet
                })
        
        if not search_results:
            return f"No results found for: {query}"
        
        result_text = f"Search results for '{query}':\n\n"
        for i, result in enumerate(search_results, 1):
            result_text += f"{i}. {result['title']}\n"
            result_text += f"   URL: {result['url']}\n"
            result_text += f"   {result['snippet']}\n\n"
        
        return result_text
    
    except Exception as e:
        return f"Error performing search: {str(e)}"


@mcp.tool()
def get_webpage_content(url: str) -> str:
    """
    Fetch and extract text content from a webpage.
    
    Args:
        url: URL of the webpage to fetch
    
    Returns:
        Extracted text content
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text[:2000] + "..." if len(text) > 2000 else text
    
    except Exception as e:
        return f"Error fetching webpage: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
