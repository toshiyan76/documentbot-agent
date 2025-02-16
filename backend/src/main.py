import logging
import uuid
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from docubot_agent.main import DocumentationAgent
from langchain_openai import ChatOpenAI
import json
import sys
import asyncio
from google.auth import default
from google.auth.transport.requests import Request as GoogleRequest

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # 標準出力にログを出力
)
logger = logging.getLogger(__name__)

# 起動時の環境情報をログに記録
logger.info("Application starting...")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"PYTHONPATH: {os.getenv('PYTHONPATH')}")
logger.info(f"PORT: {os.getenv('PORT')}")
logger.info(f"Files in current directory: {os.listdir('.')}")

# 環境変数でCloud Run環境を判別
is_cloud_run = os.getenv('K_SERVICE') is not None
logger.info(f"Running in Cloud Run: {is_cloud_run}")

# Cloud Run環境でのみ Cloud Loggingを設定
if is_cloud_run:
    try:
        from google.cloud import logging as cloud_logging
        client = cloud_logging.Client()
        handler = cloud_logging.handlers.CloudLoggingHandler(client)
        cloud_logger = logging.getLogger('cloudLogger')
        cloud_logger.setLevel(logging.INFO)
        cloud_logger.addHandler(handler)
        logger.info("Cloud Logging initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Cloud Logging: {e}")
        cloud_logger = logger  # フォールバックとして通常のロガーを使用

# .envファイルを読み込む
load_dotenv()

# 環境変数の存在確認とログ出力
required_env_vars = [
    'OPENAI_API_KEY',
    'LANGCHAIN_API_KEY',
    'LANGCHAIN_PROJECT',
    'LANGCHAIN_ENDPOINT',
    'LANGCHAIN_TRACING_V2'
]

# すべての環境変数の状態を確認
all_env_vars = os.environ.copy()
logger.info("Environment variables:")
for key, value in all_env_vars.items():
    if key in required_env_vars or key in ['PORT', 'PYTHONPATH', 'K_SERVICE']:
        # センシティブな情報は値を隠す
        is_sensitive = key in ['OPENAI_API_KEY', 'LANGCHAIN_API_KEY']
        shown_value = '***' if is_sensitive else value
        logger.info(f"{key}: {shown_value}")

missing_vars = []
for var in required_env_vars:
    value = os.getenv(var)
    if not value:
        missing_vars.append(var)
    logger.info(f'Required environment variable {var} is {"set" if value else "not set"}')

if missing_vars:
    error_msg = f"Required environment variables are missing: {', '.join(missing_vars)}"
    logger.error(error_msg)

app = FastAPI(
    title="Documentation Agent API",
    description="API for the Documentation Agent service",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS設定
origins = [
    'https://frontend-service-273148242685.us-central1.run.app',  # Cloud Run
    'http://localhost:3000',  # ローカル開発用
    'http://127.0.0.1:3000',  # ローカル開発用（代替URL）
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,  # 認証情報を使用しない
    allow_methods=["GET", "POST", "OPTIONS"],  # 許可するHTTPメソッド
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # プリフライトリクエストのキャッシュ時間（秒）
)

# リクエストロギングミドルウェア
@app.middleware('http')
async def log_request(request: Request, call_next):
    # プリフライトリクエストとヘルスチェックは認証をスキップ
    if request.method == "OPTIONS" or request.url.path == '/api/health':
        return await call_next(request)

    # ローカル環境では認証をスキップ
    if not is_cloud_run:
        logger.warning('Running in local environment - skipping token verification')
        return await call_next(request)

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JSONResponse(
            status_code=401,
            content={'detail': 'Missing or invalid authorization header'}
        )

    id_token = auth_header.split(' ')[1]
    try:
        # Cloud Run環境でのトークン検証
        from google.oauth2 import id_token
        credentials, project = default()
        auth_req = GoogleRequest()
        
        # トークンの検証
        try:
            # Cloud Run環境でのaudience
            audience = f"https://{os.getenv('K_SERVICE')}-{project}.{os.getenv('K_REGION')}.run.app"
            id_info = id_token.verify_oauth2_token(
                id_token,
                auth_req,
                audience=audience
            )
            
            # トークンの有効期限チェック
            if id_info.get('exp', 0) < int(time.time()):
                raise ValueError('Token has expired')
            
            # 発行者の検証
            if id_info.get('iss') not in [
                'https://accounts.google.com',
                'accounts.google.com'
            ]:
                raise ValueError('Invalid token issuer')
            
            logger.info(f"Token verified successfully for audience: {audience}")
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={'detail': f'Invalid token: {str(e)}'}
            )

        return await call_next(request)
    except Exception as e:
        logger.error(f'Token verification failed: {str(e)}')
        return JSONResponse(
            status_code=401,
            content={'detail': 'Invalid token'}
        )

class ChatRequest(BaseModel):
    message: str

@app.get("/api/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    サーバーの状態を確認するために使用
    """
    return {"status": "healthy"}

# APIキーの取得と検証
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    logger.error("OPENAI_API_KEY environment variable is not set")
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# エージェント初期化
try:
    llm = ChatOpenAI(
        api_key=api_key,
        model_name="gpt-4o",
        temperature=0.7
    )
    logger.info("ChatOpenAI initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ChatOpenAI: {str(e)}")
    raise

try:
    logger.info("Initializing DocumentationAgent...")
    agent = DocumentationAgent(llm=llm)
    logger.info("DocumentationAgent initialized successfully")
    logger.info(f"Using model: {llm.model_name}")
except Exception as e:
    logger.error(f"Failed to initialize DocumentationAgent: {str(e)}")
    raise

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    request_id = str(uuid.uuid4())
    logger.info(f"Request ID: {request_id} - Starting request processing")
    logger.info(f"Processing message: {request.message}")
    
    try:
        # ストリーミングレスポンスを作成
        async def generate_response():
            try:
                # エージェントの状態をログに記録
                logger.info("Agent state before processing:")
                logger.info(f"LLM model: {agent.llm.model_name}")
                
                try:
                    # 非同期でレスポンスを生成
                    response = await asyncio.to_thread(
                        agent.run,
                        request.message
                    )
                    
                    # レスポンスを文字列に変換してyieldする
                    if isinstance(response, (dict, list)):
                        yield json.dumps(response)
                    else:
                        yield str(response)
                        
                except Exception as e:
                    logger.error(f"Error in agent.run: {str(e)}")
                    yield json.dumps({
                        "error": "Failed to process request",
                        "details": str(e)
                    })
                    
            except Exception as e:
                logger.error(f"Error in generate_response: {e}")
                yield json.dumps({"error": str(e)})
        
        return StreamingResponse(
            generate_response(),
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting server on port {port}")
    try:
        uvicorn.run(
            "main:app",  # モジュール名を正しく指定
            host="0.0.0.0",
            port=port,
            log_level="info",
            reload=False
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise