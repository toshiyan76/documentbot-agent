import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from docubot_agent.main import DocumentationAgent
from langchain_openai import ChatOpenAI

# ロギングの設定
import sys
import json
from google.cloud import logging as cloud_logging

# Cloud Run環境でのCloud Loggingの設定
try:
    client = cloud_logging.Client()
    handler = cloud_logging.handlers.CloudLoggingHandler(client)
    cloud_logger = logging.getLogger('cloudLogger')
    cloud_logger.setLevel(logging.INFO)
    cloud_logger.addHandler(handler)
except Exception as e:
    print(f"Failed to initialize Cloud Logging: {e}")

# 通常のロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .envファイルを読み込む
load_dotenv()

# 環境変数の存在確認とログ出力
required_env_vars = [
    'OPENAI_API_KEY',
    'LANGCHAIN_API_KEY',
    'LANGCHAIN_PROJECT',
    'LANGCHAIN_ENDPOINT',
    'LANGCHAIN_TRACING_V2',
    'CORS_ORIGINS'
]

for var in required_env_vars:
    value = os.getenv(var)
    logger.info(f'Environment variable {var} is {"set" if value else "not set"}')

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Request processing error: {str(e)}")
            return Response("Internal Server Error", status_code=500)

app = FastAPI()

# タイムアウトミドルウェアを追加
app.add_middleware(TimeoutMiddleware)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # フロントエンドのオリジン
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# エージェント初期化
llm = ChatOpenAI(
    model_name="gpt-4o",
    temperature=0.7
)

try:
    logger.info("Initializing DocumentationAgent...")
    agent = DocumentationAgent(llm=llm)
    logger.info("DocumentationAgent initialized successfully")
    logger.info(f"Using model: {llm.model_name}")
except Exception as e:
    logger.error(f"Failed to initialize DocumentationAgent: {str(e)}")
    raise

@app.get("/api/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    サーバーの状態を確認するために使用
    """
    env_status = {}
    for var in required_env_vars:
        env_status[var] = bool(os.getenv(var))
    
    logger.info(f'Health check called, environment status: {env_status}')
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": env_status
    }

import asyncio
from fastapi import BackgroundTasks

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    チャットエンドポイント
    ユーザーからのメッセージを受け取り、AIエージェントの応答を返す
    """
    request_id = str(uuid.uuid4())
    try:
        # リクエスト情報のロギング
        logger.info(f"Request ID: {request_id} - Starting request processing")
        cloud_logger.info(f"Request ID: {request_id} - Starting request processing")

        # 環境変数のチェック
        required_env_vars = ['OPENAI_API_KEY', 'LANGCHAIN_API_KEY', 'LANGCHAIN_PROJECT']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(f"Request ID: {request_id} - {error_msg}")
            cloud_logger.error(f"Request ID: {request_id} - {error_msg}")
            raise ValueError(error_msg)

        # リクエストの検証
        if not request.message or not request.message.strip():
            error_msg = "Empty message received"
            logger.error(f"Request ID: {request_id} - {error_msg}")
            cloud_logger.error(f"Request ID: {request_id} - {error_msg}")
            raise ValueError(error_msg)

        # デバッグログ
        logger.info(f"Processing message: {request.message[:100]}...")
        
        # エージェント処理を呼び出し
        try:
            # エージェントの状態をログ
            logger.info("Agent state before processing:")
            logger.info(f"LLM model: {agent.llm.model_name}")
            
            response = agent.run(request.message)
            
            if not response:
                raise ValueError("Agent returned empty response")
                
            logger.info("Successfully generated response")
            return {"response": response}
            
        except Exception as agent_error:
            logger.error(f"Agent execution failed: {str(agent_error)}")
            logger.error(f"Agent error type: {type(agent_error).__name__}")
            
            # エージェントのエラーを詳細に記録
            if hasattr(agent_error, '__cause__') and agent_error.__cause__:
                logger.error(f"Caused by: {str(agent_error.__cause__)}")
            
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Agent Processing Error",
                    "message": str(agent_error),
                    "type": type(agent_error).__name__
                }
            )

    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation Error",
                "message": str(ve)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Unexpected error: {str(e)}\nTraceback: {error_trace}")
        
        error_detail = {
            "error": "Internal Server Error",
            "message": str(e),
            "type": type(e).__name__,
            "traceback": error_trace
        }
        raise HTTPException(status_code=500, detail=error_detail)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8081"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=True,
        timeout_keep_alive=300,  # Keep-Alive timeout
        workers=4,  # マルチワーカー
        limit_concurrency=10,  # 同時接続数の制限
        timeout_notify=300,  # 通知タイムアウト
        backlog=2048  # 接続キューサイズ
    )