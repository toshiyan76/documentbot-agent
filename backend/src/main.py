import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from docubot_agent.main import DocumentationAgent
from langchain_openai import ChatOpenAI

# ロギングの設定
logging.basicConfig(level=logging.INFO)
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

app = FastAPI()

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
    model_name="gpt-4o"
)
agent = DocumentationAgent(llm=llm)

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

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    チャットエンドポイント
    ユーザーからのメッセージを受け取り、AIエージェントの応答を返す
    """
    try:
        # デバッグログ
        print(f"Received message: {request.message}")
        print(f"OPENAI_API_KEY is set: {bool(os.getenv('OPENAI_API_KEY'))}")
        
        # エージェント処理を呼び出し
        response = agent.run(request.message)
        return {"response": response}
    except Exception as e:
        import traceback
        error_detail = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print("Error occurred:", error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8081"))
    uvicorn.run(app, host="0.0.0.0", port=port, debug=True)