from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
from dotenv import load_dotenv
from api.docubot_agent.main import DocumentationAgent
from langchain_openai import ChatOpenAI

# .envファイルを読み込む
load_dotenv()

# docubot_agentモジュールをインポートできるようにパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="DocuBot API", version="1.0.0")

# CORS設定
origins = [
    "http://localhost:3000",
    "https://documentbot-agent.vercel.app",
    "https://documentbot-agent-git-main-toshiyan76.vercel.app",
    "https://documentbot-agent-toshiyan76.vercel.app"
]

# 環境変数からCORSの追加設定を取得
if additional_origins := os.getenv("CORS_ORIGINS"):
    origins.extend(additional_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# エージェント初期化
llm = ChatOpenAI()
agent = DocumentationAgent(llm=llm)

@app.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    サーバーの状態を確認するために使用
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "openai_api_key": bool(os.getenv("OPENAI_API_KEY"))
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
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port, debug=True)