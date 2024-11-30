import os
import json
import logging
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(
    base_url="https://api.novita.ai/v3/openai",
    api_key="d63ccf43-a0e1-4011-b5cc-19d204794b29"
)

class AnalyzeRequest(BaseModel):
    code: str
    stream: bool = False

class SaveAnalysisRequest(BaseModel):
    path: str
    content: str

@app.get("/")
async def root():
    """Serve the root HTML file."""
    logger.info("Serving root HTML file")
    return FileResponse("code_viewer.html")

@app.get("/code_viewer.js")
async def serve_js():
    """Serve the JavaScript file."""
    logger.info("Serving code_viewer.js")
    return FileResponse("code_viewer.js")

@app.get("/api/files")
async def get_files(path: str):
    """Get directory contents."""
    try:
        logger.info(f"Getting files from path: {path}")
        files = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            is_dir = os.path.isdir(item_path)
            files.append({
                "name": item,
                "path": item_path,
                "isDirectory": is_dir
            })
        return files
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content")
async def get_content(path: str):
    """Get file contents."""
    try:
        logger.info(f"Getting content from file: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        logger.error(f"Error getting file content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/load_analysis")
async def load_analysis(path: str):
    """Load AI analysis from file if it exists."""
    try:
        analysis_path = path + '.ai'
        if os.path.exists(analysis_path):
            logger.info(f"Loading analysis from: {analysis_path}")
            with open(analysis_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"content": content}
        else:
            raise HTTPException(status_code=404, detail="Analysis file not found")
    except Exception as e:
        logger.error(f"Error loading analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save_analysis")
async def save_analysis(request: SaveAnalysisRequest):
    """Save AI analysis to file."""
    try:
        analysis_path = request.path + '.ai'
        logger.info(f"Saving analysis to: {analysis_path}")
        with open(analysis_path, 'w', encoding='utf-8') as f:
            f.write(request.content)
        return {"message": "Analysis saved successfully"}
    except Exception as e:
        logger.error(f"Error saving analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_code(request: AnalyzeRequest):
    """Analyze code using Novita AI API."""
    try:
        completion_res = client.completions.create(
            model="qwen/qwen-2-72b-instruct",
            prompt = "You are a benevolent programming expert, adept at deciphering code from the perspective of a beginner. The emphasis is on elucidating the functionality and operational mechanisms of the code in accessible and understandable language. Please start by summarizing the overall function of the code, then provide functional annotations for the provided code to help beginners quickly grasp the project and get started. The explanations should be given in Chinese.Code: "+request.code,
            temperature=0.8,
            stream=False,
            max_tokens=5000,
            timeout=100
        )
        content = completion_res.choices[0].text
        return {"content": content}

    except Exception as e:
        logger.error(f"Error in code analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting server...")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
