import os
import uvicorn
from typing import List, Optional
from groq import Groq
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.utilities.semanticscholar import SemanticScholarAPIWrapper
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Research Paper API",
    description="API for fetching and analyzing research papers",
    version="1.0.0"
)

# Set up the Groq client with your API key
client = Groq(api_key='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')

# Initialize the Semantic Scholar API wrapper
semantic_scholar = SemanticScholarAPIWrapper(top_k_results=10, load_max_docs=10)

class Query(BaseModel):
    text: str
    limit: Optional[int] = 10

class Paper(BaseModel):
    title: str
    abstract: str
    url: str
    year: Optional[int]
    authors: List[str]
    citationCount: Optional[int]
    summary: str
    insights: str

class PapersResponse(BaseModel):
    papers: List[Paper]

def generate_summary(abstract: str) -> str:
    """Generate a concise and informative summary of the all the paper's abstract."""
    try:
        prompt = """
        Provide a clear, concise summary of all the research paper {abstract} that the user prefers. 
        Focus on the main objectives, methodology, and key findings. 
        Keep the summary informative but brief:

        Abstract: {abstract}
        """.format(abstract=abstract)

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return "Summary generation failed"

def extract_key_insights(abstract: str) -> str:
    """Extract key insights and contributions from the paper's abstract."""
    try:
        prompt = """
        Analyze all the research paper {abstract} and extract 3-4 key insights or contributions. 
        Task is to extract insights from multiple research paper {abstract}.
        Format them as bullet points and focus on the most significant findings or implications:

        Abstract: {abstract}
        """.format(abstract=abstract)

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error extracting insights: {str(e)}")
        return "Insight extraction failed"

def process_papers(papers_data: List[dict]) -> List[Paper]:
    """Process and filter papers data with enhanced error handling."""
    processed_papers = []
    
    for paper in papers_data:
        try:
            # Skip non-dictionary papers
            if not isinstance(paper, dict):
                logger.warning(f"Skipping invalid paper format: {type(paper)}")
                continue
            
            # Extract required fields
            title = paper.get('title')
            abstract = paper.get('abstract')
            
            if not title or not abstract:
                logger.warning(f"Skipping paper missing title or abstract: {title}")
                continue
            
            # Generate URL
            url = paper.get('url', '')
            if not url and paper.get('paperId'):
                url = f"https://www.semanticscholar.org/paper/{paper['paperId']}"
            elif not url:
                url = "#"  # Fallback URL
            
            # Process authors
            authors = []
            if isinstance(paper.get('authors'), list):
                authors = [
                    author.get('name', '') if isinstance(author, dict) else str(author)
                    for author in paper.get('authors', [])
                    if author
                ]
            
            # Generate summary and insights
            summary = generate_summary(abstract)
            insights = extract_key_insights(abstract)
            
            # Create Paper object
            processed_paper = Paper(
                title=title,
                abstract=abstract,
                url=url,
                year=paper.get('year'),
                authors=authors,
                citationCount=paper.get('citationCount', 0),
                summary=summary,
                insights=insights
            )
            processed_papers.append(processed_paper)
            
        except Exception as e:
            logger.error(f"Error processing paper: {str(e)}")
            continue
    
    return processed_papers

def fetch_papers_from_semantic_scholar(query: str, limit: int = 10) -> List[dict]:
    """Fetch papers from Semantic Scholar API with improved error handling."""
    try:
        logger.info(f"Fetching papers for query: {query}")
        results = semantic_scholar.run(query)
        
        # Handle different response types
        if isinstance(results, str):
            logger.warning(f"Received string response: {results}")
            results = [{"title": "Error", "abstract": results}]
        elif not isinstance(results, list):
            logger.warning(f"Received unexpected response type: {type(results)}")
            results = []
        
        # Limit results
        papers_data = results[:limit] if len(results) > limit else results
        logger.info(f"Found {len(papers_data)} papers")
        
        return papers_data
        
    except Exception as e:
        logger.error(f"Error fetching papers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch papers: {str(e)}"
        )

@app.post("/fetch_papers/", response_model=PapersResponse)
async def fetch_papers(query: Query):
    """Endpoint to fetch and process research papers with comprehensive error handling."""
    try:
        # Validate query
        if not query.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Search query cannot be empty"
            )
        
        # Fetch papers
        papers_data = fetch_papers_from_semantic_scholar(query.text, query.limit)
        
        # Process papers
        processed_papers = process_papers(papers_data)
        
        if not processed_papers:
            raise HTTPException(
                status_code=404,
                detail="No papers found matching your query"
            )
        
        return {"papers": processed_papers}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
