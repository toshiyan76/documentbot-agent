import logging
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from docubot_agent.main import DocumentationAgent
from langchain_openai import ChatOpenAI
import json

# ロギングの設定
import sys

# 環境変数でCloud Run環境を判別
is_cloud_run = os.getenv('K_SERVICE') is not None

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    'LANGCHAIN_TRACING_V2',
    'CORS_ORIGINS'
]

for var in required_env_vars:
    value = os.getenv(var)
    logger.info(f'Environment variable {var} is {"set" if value else "not set"}')

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# タイムアウトミドルウェアを更新
import asyncio
from typing import Callable, Awaitable

class TimeoutMiddleware:
    def __init__(self, app, timeout: int = 600):
        self.app = app
        self.timeout = timeout

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # カスタムsend関数を作成してレスポンスを監視
        response_started = False
        original_messages = []

        async def custom_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            original_messages.append(message)
            await send(message)

        try:
            # タイムアウト付きで実行
            await asyncio.wait_for(
                self.app(scope, receive, custom_send),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.error("Request timed out")
            if not response_started:
                response = JSONResponse(
                    status_code=504,
                    content={"detail": "Request timed out"},
                )
                await response(scope, receive, send)
        except Exception as e:
            logger.error(f"Request failed: {e}")
            if not response_started:
                response = JSONResponse(
                    status_code=500,
                    content={"detail": "Internal server error"},
                )
                await response(scope, receive, send)

app = FastAPI()

# タイムアウトミドルウェアを追加（10分のタイムアウト）
app.add_middleware(TimeoutMiddleware, timeout=600)

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