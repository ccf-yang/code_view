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
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from zhipuai import ZhipuAI
import sys
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read API keys from JSON file
def load_api_keys():
    try:
        with open("D:\\api_key\\llmapi.json", "r", encoding="utf-8") as f:
            keys = json.load(f)
            
        glm_key = None
        novita_key = None
        ppinfra_key = None
        modelscope_key = None
        
        # Find GLM and NOVITA keys
        for key_name, value in keys.items():
            if key_name.startswith("GLM"):
                glm_key = value
            elif "NOVITA" in key_name:
                novita_key = value
            elif "PPINFRA" in key_name:
                ppinfra_key = value
            elif "MODELSCOPE" in key_name:
                modelscope_key = value
        
        if not glm_key or not novita_key or not ppinfra_key or not modelscope_key:
            logger.error("Required API keys not found in llmkey.json")
            raise ValueError("Missing required API keys")
            
        return glm_key, novita_key, ppinfra_key, modelscope_key
    except Exception as e:
        logger.error(f"Error loading API keys: {str(e)}")
        raise

# Load API keys
try:
    ZHIPU_API_KEY, NOVITA_API_KEY, PPINFRA_API_KEY, MODELSCOPE_API_KEY = load_api_keys()
    logger.info("API keys loaded successfully")
    logger.info("zhipu api key: " + ZHIPU_API_KEY)
    logger.info("novita api key: " + NOVITA_API_KEY)
    logger.info("ppinfra api key: " + PPINFRA_API_KEY)
    logger.info("modelscope api key: " + MODELSCOPE_API_KEY)
except Exception as e:
    logger.error(f"Failed to load API keys: {str(e)}")
    ZHIPU_API_KEY = ""
    NOVITA_API_KEY = ""
    PPINFRA_API_KEY = ""
    MODELSCOPE_API_KEY = ""

app = FastAPI()

# Get the application's base directory
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle (packaged with PyInstaller)
    base_dir = sys._MEIPASS
else:
    # If the application is run from a Python interpreter
    base_dir = os.path.dirname(os.path.abspath(__file__))

# 添加静态文件支持
public_dir = os.path.join(base_dir, "public")
app.mount("/public", StaticFiles(directory=public_dir), name="public")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AIClientSingleton:
    """AI客户端单例模式管理类"""
    _zhipu_instance = None
    _novita_instance = None
    _ppinfra_instance = None
    _modelscope_instance = None
    _lock = threading.Lock()

    @classmethod
    def get_zhipu_client(cls) -> ZhipuAI:
        """获取智谱AI客户端单例"""
        if cls._zhipu_instance is None:
            with cls._lock:
                if cls._zhipu_instance is None:
                    logger.info("Creating new ZhipuAI client instance")
                    cls._zhipu_instance = ZhipuAI(api_key=ZHIPU_API_KEY)
        return cls._zhipu_instance

    @classmethod
    def get_novita_client(cls) -> OpenAI:
        """获取Novita客户端单例"""
        if cls._novita_instance is None:
            with cls._lock:
                if cls._novita_instance is None:
                    logger.info("Creating new Novita client instance")
                    cls._novita_instance = OpenAI(
                        base_url="https://api.novita.ai/v3/openai",
                        api_key=NOVITA_API_KEY
                    )
        return cls._novita_instance

    @classmethod
    def get_ppinfra_client(cls) -> OpenAI:
        """获取PPInfra客户端单例"""
        if cls._ppinfra_instance is None:
            with cls._lock:
                if cls._ppinfra_instance is None:
                    logger.info("Creating new PPInfra client instance")
                    cls._ppinfra_instance = OpenAI(
                        base_url="https://api.ppinfra.com/v3/openai",
                        api_key=PPINFRA_API_KEY
                    )
        return cls._ppinfra_instance

    @classmethod
    def get_modelscope_client(cls) -> OpenAI:
        """获取ModelScope客户端单例"""
        if cls._modelscope_instance is None:
            with cls._lock:
                if cls._modelscope_instance is None:
                    logger.info("Creating new ModelScope client instance")
                    cls._modelscope_instance = OpenAI(
                        api_key=MODELSCOPE_API_KEY,
                        base_url="https://api-inference.modelscope.cn/v1/"
                    )
        return cls._modelscope_instance

    @classmethod
    def reset_clients(cls):
        """重置客户端实例（在需要重新创建时使用）"""
        with cls._lock:
            cls._zhipu_instance = None
            cls._novita_instance = None
            cls._ppinfra_instance = None
            cls._modelscope_instance = None
            cls._mota_instance = None
            logger.info("Reset all AI client instances")

async def analyze_with_zhipu(code: str) -> str:
    """使用智谱AI分析代码"""
    try:
        client = AIClientSingleton.get_zhipu_client()
        response = client.chat.completions.create(
            timeout=200,
            model="GLM-4-Flash",  # free
            # model="glm-4-plus",  # 0.05 元 / 千tokens
            messages=[
                {"role": "system", "content": "You are a benevolent programming expert, adept at deciphering code from the perspective of a beginner. The emphasis is on elucidating the functionality and operational mechanisms of the code in accessible and understandable language. Please start by summarizing the overall function of the code, then provide functional annotations for the provided code to help beginners quickly grasp the project and get started. For each function, it is imperative to elucidate its purpose, detailing what it takes as input, what it outputs, and the specific functionality it accomplishes.The explanations should be given in Chinese."},
                {"role": "user", "content": code}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error with Zhipu AI: {str(e)}")
        # 如果发生错误，重置客户端实例
        AIClientSingleton.reset_clients()
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_with_openai_compatible(code: str, model: str, client_type: str) -> str:
    """使用OpenAI兼容接口的服务分析代码"""
    try:
        if client_type == "novita":
            client = AIClientSingleton.get_novita_client()
        elif client_type == "ppinfra":
            client = AIClientSingleton.get_ppinfra_client()
        elif client_type == "modelscope":
            client = AIClientSingleton.get_modelscope_client()

            
        system_content = "You are a benevolent programming expert, adept at deciphering code from the perspective of a beginner. The emphasis is on elucidating the functionality and operational mechanisms of the code in accessible and understandable language. Please start by summarizing the overall function of the code, then provide functional annotations for the provided code to help beginners quickly grasp the project and get started. For each function, it is imperative to elucidate its purpose, detailing what it takes as input, what it outputs, and the specific functionality it accomplishes.The explanations should be given in Chinese."
        
        completion_res = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": code}
            ],
            temperature=0.8,
            stream=False,
            max_tokens=8192,
            timeout=60
        )
        return completion_res.choices[0].message.content
    except Exception as e:
        logger.error(f"Error with {client_type} AI: {str(e)}")
        AIClientSingleton.reset_clients()
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/api/analyze")
async def analyze_code(request: AnalyzeRequest):
    """Analyze code using selected AI model."""
    try:
        print(request.model)
        if request.model == "glm-4-plus":
            logger.info("Using Zhipu AI for code analysis")
            content = await analyze_with_zhipu(request.code)
        elif request.model == "ppinfra":
            logger.info("Using PPInfra for code analysis")
            content = await analyze_with_openai_compatible(request.code, "qwen/qwen-2-72b-instruct", "ppinfra")
        elif request.model == "modelscope":
            logger.info("Using ModelScope for code analysis")
            content = await analyze_with_openai_compatible(request.code, "Qwen/Qwen2.5-Coder-32B-Instruct", "modelscope")
        else:
            logger.info(f"Using Novita AI model {request.model} for code analysis")
            content = await analyze_with_openai_compatible(request.code, request.model, "novita")

        return {"content": content}
    except Exception as e:
        logger.error(f"Error in code analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting server...")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
