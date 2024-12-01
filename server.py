import os
import json
import logging
import subprocess
from urllib.parse import urlparse
from pathlib import Path
from typing import List
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from zhipuai import ZhipuAI

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

# 智谱AI配置
ZHIPU_API_KEY = "907cd4277f8a353cdc15dbcd2c287327.699fhMuv7NCKDyIS"  # 请填写您的智谱API密钥

class AnalyzeRequest(BaseModel):
    code: str
    model: str = "qwen/qwen-2-72b-instruct"  # 默认使用 Novita AI
    stream: bool = False

class GitRepoRequest(BaseModel):
    url: str

class SaveAnalysisRequest(BaseModel):
    path: str
    content: str

class HistoryRequest(BaseModel):
    path: str

class DeleteHistoryRequest(BaseModel):
    path: str

# Ensure data/gitcode directory exists
GITCODE_DIR = Path("data/gitcode")
GITCODE_DIR.mkdir(parents=True, exist_ok=True)

# History log file path
HISTORY_FILE = Path("history.log")

def get_repo_name(url: str) -> str:
    """Extract repository name from Git URL."""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    return path.split('/')[-1].replace('.git', '')

def get_existing_repo(url: str) -> str:
    """Check if repository already exists locally."""
    repo_name = get_repo_name(url)
    repo_path = GITCODE_DIR / repo_name
    if repo_path.exists():
        return str(repo_path)
    return None

def load_history() -> List[str]:
    """Load history from file."""
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading history: {e}")
        return []

def save_history(path: str, is_git: bool = False):
    """Save path to history if not exists."""
    try:
        history = load_history()
        # 如果是Git URL，直接保存URL
        path_to_save = path if is_git else str(Path(path).resolve())
        if path_to_save not in history:
            history.append(path_to_save)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving history: {e}")

def delete_history(path: str):
    """Delete path from history."""
    try:
        history = load_history()
        if path in history:
            history.remove(path)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting history: {e}")
        return False

@app.post("/api/clone-repo")
async def clone_repo(request: GitRepoRequest):
    """Clone a Git repository if it doesn't exist locally."""
    try:
        # Save Git URL to history
        save_history(request.url, is_git=True)
        
        # Check if repo already exists
        existing_path = get_existing_repo(request.url)
        if existing_path:
            logger.info(f"Repository already exists at {existing_path}")
            return {"path": existing_path}

        # Clone the repository
        repo_name = get_repo_name(request.url)
        repo_path = GITCODE_DIR / repo_name
        
        # Remove directory if it exists but is empty or incomplete
        if repo_path.exists():
            import shutil
            shutil.rmtree(repo_path)
            
        logger.info(f"Cloning repository: {request.url} to {repo_path}")
        result = subprocess.run(
            ["git", "clone", request.url, str(repo_path)],
            capture_output=True,
            text=True,
            check=False  # Don't raise exception immediately
        )
        
        if result.returncode != 0:
            logger.error(f"Git clone failed with error: {result.stderr}")
            raise HTTPException(status_code=400, detail=f"Git clone failed: {result.stderr}")
            
        if repo_path.exists():
            logger.info(f"Repository successfully cloned to {repo_path}")
            return {"path": str(repo_path)}
        else:
            logger.error("Repository path does not exist after clone")
            raise HTTPException(status_code=500, detail="Failed to clone repository: path does not exist after clone")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Git clone process error: {e.stderr}")
        raise HTTPException(status_code=400, detail=f"Git clone failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error during clone: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
async def get_files(path: str, should_save_history: bool = False):
    """Get directory contents."""
    try:
        # Only save path to history if explicitly requested
        if should_save_history:
            save_history(path, is_git=False)
        
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

@app.get("/api/history")
async def get_history():
    """Get path history."""
    try:
        history = load_history()
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history")
async def remove_history(request: DeleteHistoryRequest):
    """Remove path from history."""
    try:
        if delete_history(request.path):
            return {"success": True}
        raise HTTPException(status_code=404, detail="Path not found in history")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_with_zhipu(code: str) -> str:
    """使用智谱AI分析代码"""
    try:
        client = ZhipuAI(api_key=ZHIPU_API_KEY)
        response = client.chat.completions.create(
            model="glm-4-plus",
            messages=[
                {"role": "system", "content": "You are a benevolent programming expert, adept at deciphering code from the perspective of a beginner. The emphasis is on elucidating the functionality and operational mechanisms of the code in accessible and understandable language. Please start by summarizing the overall function of the code, then provide functional annotations for the provided code to help beginners quickly grasp the project and get started. The explanations should be given in Chinese."},
                {"role": "user", "content": code}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error with Zhipu AI: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_code(request: AnalyzeRequest):
    """Analyze code using selected AI model."""
    try:
        if request.model == "glm-4-plus":
            logger.info("Using Zhipu AI for code analysis")
            content = await analyze_with_zhipu(request.code)
        else:
            logger.info(f"Using Novita AI model {request.model} for code analysis")
            completion_res = client.completions.create(
                model=request.model,
                prompt="You are a benevolent programming expert, adept at deciphering code from the perspective of a beginner. The emphasis is on elucidating the functionality and operational mechanisms of the code in accessible and understandable language. Please start by summarizing the overall function of the code, then provide functional annotations for the provided code to help beginners quickly grasp the project and get started. The explanations should be given in Chinese.Code: " + request.code,
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
