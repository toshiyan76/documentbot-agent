This file is a merged representation of the entire codebase, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded

## Additional Info

# Directory Structure
```
backend/
  src/
    docubot_agent/
      main.py
    main.py
    requirements.txt
  Dockerfile
  README.md
frontend/
  src/
    app/
      chat/
        ChatUI.tsx
        page.tsx
      globals.css
      layout.tsx
      page.tsx
    public/
      next.svg
      vercel.svg
    .eslintrc.json
    next.config.js
    package.json
    postcss.config.js
    tailwind.config.js
    tsconfig.json
  Dockerfile
.dockerignore
.env_sample
.gitignore
.windsurfrules
cloudbuild.yaml
docker-compose.yaml
README.md
```

# Files

## File: backend/src/docubot_agent/main.py
````python
import operator
from typing import Annotated, Any, Optional
import os
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

# .envファイルから環境変数を読み込む
load_dotenv()


# ペルソナを表すデータモデル
class Persona(BaseModel):
    name: str = Field(..., description="ペルソナの名前")
    background: str = Field(..., description="ペルソナの持つ背景")


# ペルソナのリストを表すデータモデル
class Personas(BaseModel):
    personas: list[Persona] = Field(
        default_factory=list, description="ペルソナのリスト"
    )


# インタビュー内容を表すデータモデル
class Interview(BaseModel):
    persona: Persona = Field(..., description="インタビュー対象のペルソナ")
    question: str = Field(..., description="インタビューでの質問")
    answer: str = Field(..., description="インタビューでの回答")


# インタビュー結果のリストを表すデータモデル
class InterviewResult(BaseModel):
    interviews: list[Interview] = Field(
        default_factory=list, description="インタビュー結果のリスト"
    )


# 評価の結果を表すデータモデル
class EvaluationResult(BaseModel):
    reason: str = Field(..., description="判断の理由")
    is_sufficient: bool = Field(..., description="情報が十分かどうか")


# 要件定義生成AIエージェントのステート
class InterviewState(BaseModel):
    user_request: str = Field(..., description="ユーザーからのリクエスト")
    personas: Annotated[list[Persona], operator.add] = Field(
        default_factory=list, description="生成されたペルソナのリスト"
    )
    interviews: Annotated[list[Interview], operator.add] = Field(
        default_factory=list, description="実施されたインタビューのリスト"
    )
    requirements_doc: str = Field(default="", description="生成された要件定義")
    iteration: int = Field(
        default=0, description="ペルソナ生成とインタビューの反復回数"
    )
    is_information_sufficient: bool = Field(
        default=False, description="情報が十分かどうか"
    )


# ペルソナを生成するクラス
class PersonaGenerator:
    def __init__(self, llm: ChatOpenAI, k: int = 5):
        self.llm = llm.with_structured_output(Personas)
        self.k = k

    def run(self, user_request: str) -> Personas:
        # プロンプトテンプレートを定義
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "あなたはユーザーインタビュー用の多様なペルソナを作成する専門家です。",
                ),
                (
                    "human",
                    f"以下のユーザーリクエストに関するインタビュー用に、{self.k}人の多様なペルソナを生成してください。\n\n"
                    "ユーザーリクエスト: {user_request}\n\n"
                    "各ペルソナには名前と簡単な背景を含めてください。年齢、性別、職業、技術的専門知識において多様性を確保してください。",
                ),
            ]
        )
        # ペルソナ生成のためのチェーンを作成
        chain = prompt | self.llm
        # ペルソナを生成
        return chain.invoke({"user_request": user_request})


# インタビューを実施するクラス
class InterviewConductor:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def run(self, user_request: str, personas: list[Persona]) -> InterviewResult:
        # 質問を生成
        questions: list[str] = self._generate_questions(
            user_request=user_request, personas=personas
        )
        # 回答を生成
        answers: list[str] = self._generate_answers(
            personas=personas, questions=questions
        )
        # 質問と回答の組み合わせからインタビューリストを作成
        interviews: list[Interview] = self._create_interviews(
            personas=personas, questions=questions, answers=answers
        )
        # インタビュー結果を返す
        return InterviewResult(interviews=interviews)

    def _generate_questions(
        self, user_request: str, personas: list[Persona]
    ) -> list[str]:
        # 質問生成のためのプロンプトを定義
        question_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "あなたはユーザー要件に基づいて適切な質問を生成する専門家です。",
                ),
                (
                    "human",
                    "以下のペルソナに関連するユーザーリクエストについて、1つの質問を生成してください。\n\n"
                    "ユーザーリクエスト: {user_request}\n"
                    "ペルソナ: {persona_name} - {persona_background}\n\n"
                    "質問は具体的で、このペルソナの視点から重要な情報を引き出すように設計してください。",
                ),
            ]
        )
        # 質問生成のためのチェーンを作成
        question_chain = question_prompt | self.llm | StrOutputParser()

        # 各ペルソナに対する質問クエリを作成
        question_queries = [
            {
                "user_request": user_request,
                "persona_name": persona.name,
                "persona_background": persona.background,
            }
            for persona in personas
        ]
        # 質問をバッチ処理で生成
        return question_chain.batch(question_queries)

    def _generate_answers(
        self, personas: list[Persona], questions: list[str]
    ) -> list[str]:
        # 回答生成のためのプロンプトを定義
        answer_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "あなたは以下のペルソナとして回答しています: {persona_name} - {persona_background}",
                ),
                ("human", "質問: {question}"),
            ]
        )
        # 回答生成のためのチェーンを作成
        answer_chain = answer_prompt | self.llm | StrOutputParser()

        # 各ペルソナに対する回答クエリを作成
        answer_queries = [
            {
                "persona_name": persona.name,
                "persona_background": persona.background,
                "question": question,
            }
            for persona, question in zip(personas, questions)
        ]
        # 回答をバッチ処理で生成
        return answer_chain.batch(answer_queries)

    def _create_interviews(
        self, personas: list[Persona], questions: list[str], answers: list[str]
    ) -> list[Interview]:
        # ペルソナ毎に質問と回答の組み合わせからインタビューオブジェクトを作成
        return [
            Interview(persona=persona, question=question, answer=answer)
            for persona, question, answer in zip(personas, questions, answers)
        ]


# 情報の十分性を評価するクラス
class InformationEvaluator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm.with_structured_output(EvaluationResult)

    # ユーザーリクエストとインタビュー結果を基に情報の十分性を評価
    def run(self, user_request: str, interviews: list[Interview]) -> EvaluationResult:
        # プロンプトを定義
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "あなたは包括的な要件文書を作成するための情報の十分性を評価する専門家です。",
                ),
                (
                    "human",
                    "以下のユーザーリクエストとインタビュー結果に基づいて、包括的な要件文書を作成するのに十分な情報が集まったかどうかを判断してください。\n\n"
                    "ユーザーリクエスト: {user_request}\n\n"
                    "インタビュー結果:\n{interview_results}",
                ),
            ]
        )
        # 情報の十分性を評価するチェーンを作成
        chain = prompt | self.llm
        # 評価結果を返す
        return chain.invoke(
            {
                "user_request": user_request,
                "interview_results": "\n".join(
                    f"ペルソナ: {i.persona.name} - {i.persona.background}\n"
                    f"質問: {i.question}\n回答: {i.answer}\n"
                    for i in interviews
                ),
            }
        )


# 要件定義書を生成するクラス
class RequirementsDocumentGenerator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def run(self, user_request: str, interviews: list[Interview]) -> str:
        # プロンプトを定義
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "あなたは収集した情報に基づいて要件文書を作成する専門家です。",
                ),
                (
                    "human",
                    "以下のユーザーリクエストと複数のペルソナからのインタビュー結果に基づいて、要件文書を作成してください。\n\n"
                    "ユーザーリクエスト: {user_request}\n\n"
                    "インタビュー結果:\n{interview_results}\n"
                    "要件文書には以下のセクションを含めてください:\n"
                    "1. プロジェクト概要\n"
                    "2. 主要機能\n"
                    "3. 非機能要件\n"
                    "4. 制約条件\n"
                    "5. ターゲットユーザー\n"
                    "6. 優先順位\n"
                    "7. リスクと軽減策\n\n"
                    "出力は必ず日本語でお願いします。\n\n要件文書:",
                ),
            ]
        )
        # 要件定義書を生成するチェーンを作成
        chain = prompt | self.llm | StrOutputParser()
        # 要件定義書を生成
        return chain.invoke(
            {
                "user_request": user_request,
                "interview_results": "\n".join(
                    f"ペルソナ: {i.persona.name} - {i.persona.background}\n"
                    f"質問: {i.question}\n回答: {i.answer}\n"
                    for i in interviews
                ),
            }
        )


# 要件定義書生成AIエージェントのクラス
class AgentError(Exception):
    """DocumentationAgentの基本エラークラス"""
    pass

class PersonaGenerationError(AgentError):
    """ペルソナ生成時のエラー"""
    pass

class InterviewError(AgentError):
    """インタビュー実施時のエラー"""
    pass

class EvaluationError(AgentError):
    """情報評価時のエラー"""
    pass

class DocumentGenerationError(AgentError):
    """要件定義書生成時のエラー"""
    pass

class DocumentationAgent:
    def __init__(self, llm: ChatOpenAI, k: Optional[int] = None):
        if not isinstance(llm, ChatOpenAI):
            raise ValueError("llm must be an instance of ChatOpenAI")

        try:
            # LLMの保存
            self.llm = llm

            # 各種ジェネレータの初期化
            self.persona_generator = PersonaGenerator(llm=self.llm, k=k)
            self.interview_conductor = InterviewConductor(llm=self.llm)
            self.information_evaluator = InformationEvaluator(llm=self.llm)
            self.requirements_generator = RequirementsDocumentGenerator(llm=self.llm)

            # グラフの作成
            self.graph = self._create_graph()
        except Exception as e:
            raise AgentError(f"Failed to initialize DocumentationAgent: {str(e)}") from e

    def _create_graph(self) -> StateGraph:
        # グラフの初期化
        workflow = StateGraph(InterviewState)

        # 各ノードの追加
        workflow.add_node("generate_personas", self._generate_personas)
        workflow.add_node("conduct_interviews", self._conduct_interviews)
        workflow.add_node("evaluate_information", self._evaluate_information)
        workflow.add_node("generate_requirements", self._generate_requirements)

        # エントリーポイントの設定
        workflow.set_entry_point("generate_personas")

        # ノード間のエッジの追加
        workflow.add_edge("generate_personas", "conduct_interviews")
        workflow.add_edge("conduct_interviews", "evaluate_information")

        # 条件付きエッジの追加
        workflow.add_conditional_edges(
            "evaluate_information",
            lambda state: not state.is_information_sufficient and state.iteration < 5,
            {True: "generate_personas", False: "generate_requirements"},
        )
        workflow.add_edge("generate_requirements", END)

        # グラフのコンパイル
        return workflow.compile()

    def _generate_personas(self, state: InterviewState) -> dict[str, Any]:
        # ペルソナの生成
        new_personas: Personas = self.persona_generator.run(state.user_request)
        return {
            "personas": new_personas.personas,
            "iteration": state.iteration + 1,
        }

    def _conduct_interviews(self, state: InterviewState) -> dict[str, Any]:
        # インタビューの実施
        new_interviews: InterviewResult = self.interview_conductor.run(
            state.user_request, state.personas[-5:]
        )
        return {"interviews": new_interviews.interviews}

    def _evaluate_information(self, state: InterviewState) -> dict[str, Any]:
        # 情報の評価
        evaluation_result: EvaluationResult = self.information_evaluator.run(
            state.user_request, state.interviews
        )
        return {
            "is_information_sufficient": evaluation_result.is_sufficient,
            "evaluation_reason": evaluation_result.reason,
        }

    def _generate_requirements(self, state: InterviewState) -> dict[str, Any]:
        # 要件定義書の生成
        requirements_doc: str = self.requirements_generator.run(
            state.user_request, state.interviews
        )
        return {"requirements_doc": requirements_doc}

    def run(self, user_request: str) -> str:
        # 初期状態の設定
        initial_state = InterviewState(user_request=user_request)
        # グラフの実行
        final_state = self.graph.invoke(initial_state)
        # 最終的な要件定義書の取得
        return final_state["requirements_doc"]


# 実行方法:
# poetry run python -m documentation_agent.main --task "ユーザーリクエストをここに入力してください"
# 実行例）
# poetry run python -m documentation_agent.main --task "スマートフォン向けの健康管理アプリを開発したい"
def main():
    import argparse

    # コマンドライン引数のパーサーを作成
    parser = argparse.ArgumentParser(
        description="ユーザー要求に基づいて要件定義を生成します"
    )
    # "task"引数を追加
    parser.add_argument(
        "--task",
        type=str,
        help="作成したいアプリケーションについて記載してください",
    )
    # "k"引数を追加
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="生成するペルソナの人数を設定してください（デフォルト:5）",
    )
    # コマンドライン引数を解析
    args = parser.parse_args()

    # ChatOpenAIモデルを初期化（deepseek-chatを使用）
    llm = ChatOpenAI(
        model="gpt-4o",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
    # 要件定義書生成AIエージェントを初期化
    agent = DocumentationAgent(llm=llm, k=args.k)
    # エージェントを実行して最終的な出力を取得
    final_output = agent.run(user_request=args.task)

    # 最終的な出力を表示
    print(final_output)


if __name__ == "__main__":
    main()
````

## File: backend/src/main.py
````python
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
````

## File: backend/src/requirements.txt
````
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6
langchain-core==0.3.0
langchain-openai==0.2.0
langgraph==0.2.22
python-dotenv==1.0.1
pydantic==2.5.3
pydantic-settings==2.1.0
````

## File: backend/Dockerfile
````
ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim AS base
RUN apt-get update && \
    apt-get install -y \
    git gcc musl-dev && \
    rm -rf /var/lib/apt/lists/*

FROM base AS init
WORKDIR /app

FROM base AS dev
WORKDIR /app
COPY src/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PYTHONPATH=/app/src
ENV FASTAPI_ENV="development"

FROM base AS builder
ARG API_PORT
WORKDIR /app

COPY src/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
ENV FASTAPI_ENV="production"

FROM python:${PYTHON_VERSION}-slim AS runner
WORKDIR /app
ENV PYTHONPATH=/app/src
ENV FASTAPI_ENV="production"

COPY src/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=builder /app/src .
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

EXPOSE 8081
ENV PORT 8081

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]
````

## File: backend/README.md
````markdown
# バックエンドテスト手順書

このドキュメントでは、DocuBotのバックエンドAPIをテストする手順を説明します。

## 1. Docker環境でのテスト（推奨）

### 1.1 Dockerコンテナの起動

1. プロジェクトのルートディレクトリに移動
   ```bash
   cd /path/to/docubot-agent
   ```

2. 環境変数の設定
   ```bash
   cp .env.sample .env
   # .envファイルを編集してOpenAI APIキーを設定
   ```

3. Dockerコンテナのビルドと起動
   ```bash
   docker-compose up --build backend
   ```

### 1.2 APIの動作確認

1. ヘルスチェック
   ```bash
   curl http://localhost:8000/health
   ```
   期待される応答：
   ```json
   {
     "status": "healthy",
     "version": "1.0.0",
     "openai_api_key": true
   }
   ```

2. チャットエンドポイントのテスト
   ```bash
   curl -X POST "http://localhost:8000/chat" \
   -H "Content-Type: application/json" \
   -d '{"message": "新しいECサイトの要件を定義したい"}'
   ```

3. Swagger UIの確認
   ブラウザで以下のURLにアクセス：
   ```
   http://localhost:8000/docs
   ```

### 1.3 コンテナログの確認
```bash
docker-compose logs -f backend
```

### 1.4 トラブルシューティング

1. コンテナの状態確認
   ```bash
   docker-compose ps
   ```

2. コンテナの再起動
   ```bash
   docker-compose restart backend
   ```

3. コンテナの再ビルド
   ```bash
   docker-compose build --no-cache backend
   ```

4. 依存関係の更新
   ```bash
   # コンテナ内で実行
   docker-compose exec backend uv sync
   ```

## 2. 手動テスト（基本）

### 2.1 開発サーバーの起動

1. バックエンドディレクトリに移動
   ```bash
   cd backend
   ```

2. 依存関係のインストール
   ```bash
   uv pip install --system
   # 開発時は
   uv pip install --system -G dev
   ```

3. 開発サーバーの起動
   ```bash
   uvicorn main:app --reload
   ```

### 2.2 APIドキュメントの確認

1. ブラウザで以下のURLにアクセス：
   ```
   http://localhost:8000/docs
   ```
   Swaggerドキュメントが表示され、利用可能なAPIエンドポイントが確認できます。

### 2.3 基本的なAPIテスト

1. curlを使用したテスト
   ```bash
   # チャットエンドポイントのテスト
   curl -X POST "http://localhost:8000/chat" \
   -H "Content-Type: application/json" \
   -d '{"message": "新しいECサイトの要件を定義したい"}'
   ```

2. HTTPieを使用したテスト（より読みやすい）
   ```bash
   # HTTPieのインストール
   pip install httpie

   # テストの実行
   http POST http://localhost:8000/chat message="新しいECサイトの要件を定義したい"
   ```

## 3. 自動テストの実行（発展）

### 3.1 テスト環境のセットアップ

1. テスト用パッケージのインストール
   ```bash
   pip install pytest pytest-asyncio httpx
   ```

2. テストファイルの作成
   ```bash
   mkdir tests
   touch tests/__init__.py
   touch tests/test_main.py
   ```

3. `tests/test_main.py`に以下のテストコードを追加：
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from main import app

   client = TestClient(app)

   def test_chat_endpoint():
       response = client.post(
           "/chat",
           json={"message": "新しいECサイトの要件を定義したい"}
       )
       assert response.status_code == 200
       assert "response" in response.json()
   ```

4. テストの実行
   ```bash
   pytest
   ```

## 4. よくあるエラーと解決方法

### 4.1 サーバー起動時のエラー

1. ポートが使用中の場合
   ```bash
   # 別のポートを指定して起動
   uvicorn main:app --reload --port 8001
   ```

2. モジュールが見つからない場合
   ```bash
   # 依存関係を再インストール
   pip install -r requirements.txt
   ```

### 4.2 API呼び出し時のエラー

1. CORS関連のエラー
   - フロントエンドからのアクセスがブロックされる場合は、`main.py`のCORS設定を確認

2. OpenAI APIキーのエラー
   - `.env`ファイルにAPIキーが正しく設定されているか確認
   - 環境変数が読み込まれているか確認
   ```bash
   echo $OPENAI_API_KEY
   ```

## 5. パフォーマンステスト（オプション）

### 5.1 負荷テストの実行

1. locustのインストール
   ```bash
   pip install locust
   ```

2. `locustfile.py`の作成
   ```python
   from locust import HttpUser, task, between

   class APIUser(HttpUser):
       wait_time = between(1, 2)

       @task
       def test_chat(self):
           self.client.post("/chat", json={
               "message": "新しいECサイトの要件を定義したい"
           })
   ```

3. 負荷テストの実行
   ```bash
   locust -f locustfile.py
   ```

4. ブラウザで`http://localhost:8089`にアクセスし、テストを設定・実行

## 6. テスト結果の解釈

### 6.1 期待される結果

1. APIエンドポイント（/chat）
   - ステータスコード: 200
   - レスポンス形式: JSON
   - 必須フィールド: "response"

2. エラーレスポンス
   - 不正なリクエスト: 400
   - サーバーエラー: 500
   - エラーメッセージを含むJSON応答

### 6.2 パフォーマンス指標

- レスポンス時間: 通常2-5秒以内
- エラー率: 1%未満
- 同時接続数: 最大10接続まで安定動作

## 7. トラブルシューティング

問題が発生した場合は、以下の手順で対応してください：

1. ログの確認
   ```bash
   uvicorn main:app --reload --log-level debug
   ```

2. 環境変数の確認
   ```bash
   python -c "import os; print(os.environ.get('OPENAI_API_KEY'))"
   ```

3. ネットワーク接続の確認
   ```bash
   curl -v http://localhost:8000/health
   ```

4. 仮想環境の再作成
   ```bash
   deactivate
   rm -rf .venv
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
````

## File: frontend/src/app/chat/ChatUI.tsx
````typescript
'use client'
import { useState, useEffect, useRef } from 'react'

export default function ChatUI() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([])
  const [isLoading, setIsLoading] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)
  const retryCountRef = useRef(0)
  const MAX_RETRIES = 3

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  // タイムアウト付きのfetch関数
  const fetchWithTimeout = async (
    url: string, 
    options: RequestInit & { timeoutMs?: number }
  ): Promise<Response> => {
    const { timeoutMs = 600000, ...fetchOptions } = options // デフォルト10分
    abortControllerRef.current = new AbortController()

    try {
      const fetchPromise = fetch(url, {
        ...fetchOptions,
        signal: abortControllerRef.current.signal,
      })

      const timeoutPromise = new Promise<Response>((_, reject) => {
        setTimeout(() => {
          if (abortControllerRef.current) {
            abortControllerRef.current.abort()
          }
          reject(new Error('Request timed out'))
        }, timeoutMs)
      })

      return await Promise.race([fetchPromise, timeoutPromise])
    } catch (error) {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      throw error
    }
  }

  const handleSubmit = async () => {
    if (!input || isLoading) return
    
    try {
      setIsLoading(true)
      const userMessage = { role: 'user', content: input }
      setMessages(prev => [...prev, userMessage])
      
      const response = await fetchWithTimeout('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
        timeoutMs: 600000, // 10分
      })

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('Response body is null')

      let assistantMessage = { role: 'assistant', content: '' }
      setMessages(prev => [...prev, assistantMessage])

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = new TextDecoder().decode(value)
        try {
          const parsedChunk = JSON.parse(chunk)
          assistantMessage.content = parsedChunk.response || parsedChunk
          setMessages(prev => 
            prev.map((msg, i) => 
              i === prev.length - 1 ? assistantMessage : msg
            )
          )
        } catch (e) {
          console.warn('Failed to parse chunk:', e)
          assistantMessage.content += chunk
          setMessages(prev => 
            prev.map((msg, i) => 
              i === prev.length - 1 ? assistantMessage : msg
            )
          )
        }
      }

      retryCountRef.current = 0
      
    } catch (error) {
      console.error('Error:', error)
      
      if (retryCountRef.current < MAX_RETRIES && 
          error instanceof Error && 
          (error.name === 'AbortError' || error.message.includes('socket') || error.message.includes('timeout'))) {
        retryCountRef.current++
        console.log(`Retrying... (${retryCountRef.current}/${MAX_RETRIES})`)
        setTimeout(() => handleSubmit(), 1000 * Math.pow(2, retryCountRef.current))
        return
      }

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'エラーが発生しました。もう一度お試しください。'
      }])
    } finally {
      setInput('')
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="border rounded-lg p-4 mb-4 h-[600px] overflow-y-auto bg-gray-50">
        {messages.map((msg, i) => (
          <div key={i} className={`mb-3 ${msg.role === 'user' ? 'text-right' : ''}`}>
            <div className={`inline-block p-3 rounded-lg max-w-[80%] whitespace-pre-wrap ${
              msg.role === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-white text-gray-800 border'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit()}
          className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="プロジェクトの要件を入力してください..."
          disabled={isLoading}
        />
        <button
          onClick={handleSubmit}
          className={`px-6 py-2 rounded-lg text-white ${
            isLoading ? 'bg-gray-400' : 'bg-blue-500 hover:bg-blue-600'
          }`}
          disabled={isLoading}
        >
          {isLoading ? '生成中...' : '送信'}
        </button>
      </div>
    </div>
  )
}
````

## File: frontend/src/app/chat/page.tsx
````typescript
import ChatUI from './ChatUI'

export default function ChatPage() {
  return (
    <div className="min-h-screen bg-gray-100 py-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
          要件定義生成チャット
        </h1>
        <ChatUI />
      </div>
    </div>
  )
}
````

## File: frontend/src/app/globals.css
````css
@tailwind base;
@tailwind components;
@tailwind utilities;
````

## File: frontend/src/app/layout.tsx
````typescript
import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'DocuBot',
  description: 'Documentation Generator',
  icons: {
    icon: '/favicon.ico'
  }
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  )
}
````

## File: frontend/src/app/page.tsx
````typescript
import { redirect } from 'next/navigation'

export default function Home() {
  redirect('/chat')
  return null
}
````

## File: frontend/src/public/next.svg
````
<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 394 80"><path fill="#000" d="M262 0h68.5v12.7h-27.2v66.6h-13.6V12.7H262V0ZM149 0v12.7H94v20.4h44.3v12.6H94v21h55v12.6H80.5V0h68.7zm34.3 0h-17.8l63.8 79.4h17.9l-32-39.7 32-39.6h-17.9l-23 28.6-23-28.6zm18.3 56.7-9-11-27.1 33.7h17.8l18.3-22.7z"/><path fill="#000" d="M81 79.3 17 0H0v79.3h13.6V17l50.2 62.3H81Zm252.6-.4c-1 0-1.8-.4-2.5-1s-1.1-1.6-1.1-2.6.3-1.8 1-2.5 1.6-1 2.6-1 1.8.3 2.5 1a3.4 3.4 0 0 1 .6 4.3 3.7 3.7 0 0 1-3 1.8zm23.2-33.5h6v23.3c0 2.1-.4 4-1.3 5.5a9.1 9.1 0 0 1-3.8 3.5c-1.6.8-3.5 1.3-5.7 1.3-2 0-3.7-.4-5.3-1s-2.8-1.8-3.7-3.2c-.9-1.3-1.4-3-1.4-5h6c.1.8.3 1.6.7 2.2s1 1.2 1.6 1.5c.7.4 1.5.5 2.4.5 1 0 1.8-.2 2.4-.6a4 4 0 0 0 1.6-1.8c.3-.8.5-1.8.5-3V45.5zm30.9 9.1a4.4 4.4 0 0 0-2-3.3 7.5 7.5 0 0 0-4.3-1.1c-1.3 0-2.4.2-3.3.5-.9.4-1.6 1-2 1.6a3.5 3.5 0 0 0-.3 4c.3.5.7.9 1.3 1.2l1.8 1 2 .5 3.2.8c1.3.3 2.5.7 3.7 1.2a13 13 0 0 1 3.2 1.8 8.1 8.1 0 0 1 3 6.5c0 2-.5 3.7-1.5 5.1a10 10 0 0 1-4.4 3.5c-1.8.8-4.1 1.2-6.8 1.2-2.6 0-4.9-.4-6.8-1.2-2-.8-3.4-2-4.5-3.5a10 10 0 0 1-1.7-5.6h6a5 5 0 0 0 3.5 4.6c1 .4 2.2.6 3.4.6 1.3 0 2.5-.2 3.5-.6 1-.4 1.8-1 2.4-1.7a4 4 0 0 0 .8-2.4c0-.9-.2-1.6-.7-2.2a11 11 0 0 0-2.1-1.4l-3.2-1-3.8-1c-2.8-.7-5-1.7-6.6-3.2a7.2 7.2 0 0 1-2.4-5.7 8 8 0 0 1 1.7-5 10 10 0 0 1 4.3-3.5c2-.8 4-1.2 6.4-1.2 2.3 0 4.4.4 6.2 1.2 1.8.8 3.2 2 4.3 3.4 1 1.4 1.5 3 1.5 5h-5.8z"/></svg>
````

## File: frontend/src/public/vercel.svg
````
<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 283 64"><path fill="black" d="M141 16c-11 0-19 7-19 18s9 18 20 18c7 0 13-3 16-7l-7-5c-2 3-6 4-9 4-5 0-9-3-10-7h28v-3c0-11-8-18-19-18zm-9 15c1-4 4-7 9-7s8 3 9 7h-18zm117-15c-11 0-19 7-19 18s9 18 20 18c6 0 12-3 16-7l-8-5c-2 3-5 4-8 4-5 0-9-3-11-7h28l1-3c0-11-8-18-19-18zm-10 15c2-4 5-7 10-7s8 3 9 7h-19zm-39 3c0 6 4 10 10 10 4 0 7-2 9-5l8 5c-3 5-9 8-17 8-11 0-19-7-19-18s8-18 19-18c8 0 14 3 17 8l-8 5c-2-3-5-5-9-5-6 0-10 4-10 10zm83-29v46h-9V5h9zM37 0l37 64H0L37 0zm92 5-27 48L74 5h10l18 30 17-30h10zm59 12v10l-3-1c-6 0-10 4-10 10v15h-9V17h9v9c0-5 6-9 13-9z"/></svg>
````

## File: frontend/src/.eslintrc.json
````json
{
  "extends": "next/core-web-vitals"
}
````

## File: frontend/src/next.config.js
````javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    serverMinification: true,
    serverTimeout: 600000, // 10分
  },
  httpAgentOptions: {
    keepAlive: true,
    timeout: 600000, // 10分
    scheduling: 'fifo',
    maxSockets: 100,
    maxFreeSockets: 10,
    socketTimeout: 610000, // timeout + 10秒
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "Connection",
            value: "keep-alive",
          },
          {
            key: "Keep-Alive",
            value: "timeout=600",
          },
        ],
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://backend:8081/api/:path*",
        has: [
          {
            type: 'header',
            key: 'connection',
            value: '(.*?)',
          },
        ],
      },
    ];
  },
  serverOptions: {
    maxHeaderSize: 65536, // 64KB
    keepAliveTimeout: 600000, // 10分
    headersTimeout: 610000, // keepAliveTimeout + 10秒
    maxRequestsPerSocket: 0, // 無制限
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        minSize: 20000,
        maxSize: 244000,
        minChunks: 1,
        maxAsyncRequests: 30,
        maxInitialRequests: 30,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
````

## File: frontend/src/package.json
````json
{
  "name": "nextjs-fastapi",
  "version": "0.2.0",
  "private": true,
  "scripts": {
    "dev": "node server.js",
    "build": "next build",
    "start": "node server.js",
    "lint": "next lint"
  },
  "dependencies": {
    "@types/node": "22.5.5",
    "@types/react": "18.3.8",
    "@types/react-dom": "18.3.0",
    "autoprefixer": "^10.4.20",
    "concurrently": "^9.0.1",
    "eslint": "8.41.0",
    "eslint-config-next": "13.4.4",
    "next": "^14.2.13",
    "postcss": "^8.4.35",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "tailwindcss": "3.4.12",
    "typescript": "5.6.2"
  },
  "devDependencies": {
    "@babel/core": "^7.26.7",
    "@babel/preset-env": "^7.26.7"
  }
}
````

## File: frontend/src/postcss.config.js
````javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
````

## File: frontend/src/tailwind.config.js
````javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    '!./node_modules/**/*'
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}
````

## File: frontend/src/tsconfig.json
````json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
````

## File: frontend/Dockerfile
````
ARG IMG_VER="20.11.0"

### base ####
FROM node:${IMG_VER} AS base
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    libvips42 \
    && rm -rf /var/lib/apt/lists/*

# npmは20.11.0に付属のものを使用するため、追加インストール不要
RUN corepack disable

FROM base AS init
WORKDIR /app/src

FROM base AS dev
WORKDIR /app/src

FROM base AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
COPY src/package*.json ./
RUN npm install --production
ENV NODE_ENV=production
COPY src/ ./
RUN npm run build

FROM node:${IMG_VER} AS runner
WORKDIR /app

# 環境変数の設定
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NODE_OPTIONS="--max-old-space-size=512 --max-http-header-size=16384"

# タイムアウト設定
ENV SERVER_TIMEOUT=60000
ENV KEEP_ALIVE_TIMEOUT=65000

# Next.js固有の設定
ENV NEXT_TELEMETRY_DISABLED=1

# デバッグ用の環境変数
ENV DEBUG="*"

# Next.js固有の設定
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_SHARP_PATH=/usr/local/lib/node_modules/sharp

# スタンドアロンビルドの結果をコピー
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000


CMD ["node", "server.js"]
````

## File: .dockerignore
````
# Version control
.git
.gitignore
.github/*

# Environment variables
.env
.env_sample
**/.env
**/.env.*

# Dependencies
**/node_modules
**/__pycache__
**/*.pyc
**/.pytest_cache

# Documentation
README.md
*.md

# Development tools
Makefile
terraform/*

# IDE and editor files
.idea
.vscode
*.swp
*.swo

# Build outputs
**/dist
**/.next
**/build
**/*.egg-info
````

## File: .env_sample
````
# Application Settings
APP_ENV=development                 # development, staging, production
APP_DEBUG=true                      # true/false for debug mode

# Server Ports
FRONTEND_PORT=3000                  # Next.js application port
BACKEND_PORT=8080                   # FastAPI application port

# API Configuration
API_PREFIX=/api/v1                  # API route prefix
API_TIMEOUT=30                      # API timeout in seconds

# Google Cloud Platform Settings
PROJECT_ID=your-project-id          # GCP project ID
REGION=asia-northeast1              # GCP region
ARTIFACT_REPO=your-artifact-repo    # Artifact Registry repository name

# Service Accounts
BUILD_ACCOUNT=your-build-account@your-project.iam.gserviceaccount.com        # Build service account
OPERATION_ACCOUNT=your-operation-account@your-project.iam.gserviceaccount.com # Operation service account

# Workload Identity
WORKLOAD_IDENTITY_PROVIDER=projects/123456789/locations/global/workloadIdentityPools/my-pool/providers/my-provider

# OpenAI Configuration
OPENAI_API_KEY=your-api-key         # OpenAI API key
OPENAI_MODEL=gpt-4                  # OpenAI model to use
OPENAI_MAX_TOKENS=2000              # Maximum tokens per request

# Security
JWT_SECRET_KEY=your-jwt-secret      # JWT signing key
JWT_ALGORITHM=HS256                 # JWT algorithm
JWT_EXPIRATION=3600                 # JWT expiration in seconds

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080  # Comma-separated list of allowed origins

# Database (if needed)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=documentbot
DB_USER=postgres
DB_PASSWORD=postgres

# Redis (if needed)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Logging
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR, CRITICAL
````

## File: .gitignore
````
# Dependencies
node_modules/
.pnp/
.pnp.js
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.env.*
!.env_sample
.venv/
venv/
ENV/
env/

# Testing and Coverage
coverage/
.coverage
.coverage.*
.pytest_cache/
htmlcov/
.tox/
nosetests.xml
coverage.xml
*.cover

# Build and Output
.next/
out/
build/
dist/
*.tsbuildinfo

# IDE and Editor
.idea/
.vscode/
*.swp
*.swo
*.swn
*.bak
*.orig
*~

# Logs and Debug
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
debug.log

# OS
.DS_Store
Thumbs.db
*.pem

# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
!*.tfvars_sample
.terraformrc
terraform.rc

# Docker
.docker/

# Temporary files
*.tmp
*.temp
.cache/

# Next.js
.vercel
next-env.d.ts

# Custom
/app/.next/
/app/node_modules/
````

## File: .windsurfrules
````
あなたは高度な問題解決能力を持つAIアシスタント、Windsurf Cascadeです。以下の指示に従って、効率的かつ正確にタスクを遂行してください。

# 基本動作原則

1. **指示の受信と理解**
   - ユーザーからの指示を注意深く読み取り
   - 不明点がある場合は、具体的な質問を行う
   - 技術的な制約や要件を明確に把握

2. **深い分析とプランニング**
   ```markdown
   ## タスク分析
   - 目的：[タスクの最終目標]
   - 技術要件：[必要な技術要素]
   - 実装手順：[具体的なステップ]
   - リスク：[潜在的な問題点]
   - 品質基準：[満たすべき基準]
   ```

3. **実装計画の策定**
   ```markdown
   ## 実装計画
   1. [具体的なステップ1]
      - 詳細な実装内容
      - 予想される課題と対策
   2. [具体的なステップ2]
      ...
   ```

4. **段階的な実装と検証**
   - 各ステップの完了後に検証
   - 問題発生時の即時対応
   - 品質基準との照合

5. **継続的なフィードバック**
   - 実装の進捗状況を定期的に報告
   - 重要な判断ポイントでの確認
   - 問題発生時の迅速な報告

---

# 品質管理プロトコル

## 1. コード品質
- 言語・フレームワークの標準規約準拠
- コーディング規約の一貫性維持
- 適切なコメント・ドキュメント化

## 2. パフォーマンス
- リソース使用の最適化
- 処理速度の効率化
- スケーラビリティの考慮

## 3. セキュリティ
- 入力値の厳格なバリデーション
- 適切なエラーハンドリング
- 機密情報の安全な管理

## 4. 保守性
- コードの可読性維持
- モジュール化の推進
- テストの容易性確保

---

# 実装プロセス

## 1. 初期分析フェーズ
```markdown
### 要件分析
- 機能要件の特定
- 技術的制約の確認
- 既存コードとの整合性確認

### リスク評価
- 潜在的な技術的課題
- パフォーマンスへの影響
- セキュリティリスク
```

## 2. 実装フェーズ
- 段階的な実装
- 各段階での検証
- コード品質の維持

## 3. 検証フェーズ
- 単体テスト
- 統合テスト
- パフォーマンステスト

## 4. 最終確認
- 要件との整合性
- コード品質
- ドキュメント完成度

---

# エラー対応プロトコル

1. **問題の特定**
   - エラーメッセージの解析
   - 影響範囲の特定
   - 原因の切り分け

2. **解決策の策定**
   - 複数の対応案の検討
   - リスク評価
   - 最適解の選択

3. **実装と検証**
   - 解決策の実装
   - テストによる検証
   - 副作用の確認

4. **文書化**
   - 問題と解決策の記録
   - 再発防止策の提案
   - 学習点の共有

---

# バージョン管理プロトコル

1. **バージョン管理の基本原則**
   - 変更履歴の明確な記録
   - 依存関係の整合性維持
   - バージョン番号の適切な更新

2. **変更管理プロセス**
   - 変更の影響範囲の評価
   - 互換性の確認
   - 段階的な更新の実施

3. **リリース管理**
   - リリースノートの作成
   - 変更点の明確な文書化
   - ロールバック手順の準備

---

以上の指示に従い、確実で質の高い実装を行います。不明点や重要な判断が必要な場合は、必ず確認を取ります。
````

## File: cloudbuild.yaml
````yaml
options:
  logging: CLOUD_LOGGING_ONLY
  dynamicSubstitutions: true

steps:
  # Configure docker auth
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['auth', 'configure-docker', 'us-central1-docker.pkg.dev']

  # Build the backend container image
  - name: 'gcr.io/cloud-builders/docker'
    dir: 'backend'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/docubot-repo/backend'
      - '.'

  # Build the frontend container image
  - name: 'gcr.io/cloud-builders/docker'
    dir: 'frontend'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/docubot-repo/frontend'
      - '--build-arg'
      - 'NEXT_PUBLIC_API_URL=/api'
      - '.'

  # Push the backend container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/docubot-repo/backend']

  # Push the frontend container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/docubot-repo/frontend']

    # service.yamlを生成（テンプレートとして）
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: bash
    args:
      - -c
      - |
         cat > service.yaml <<'EOF'
         apiVersion: serving.knative.dev/v1
         kind: Service
         metadata:
           annotations:
           name: docubot-service
         spec:
           template:
             spec:
               containers:
                 - name: frontend
                   image: us-central1-docker.pkg.dev/$PROJECT_ID/docubot-repo/frontend
                   ports:
                     - containerPort: 3000
                   env:
                     - name: NEXT_PUBLIC_API_URL
                       value: "/api"
                 - name: backend
                   image: us-central1-docker.pkg.dev/$PROJECT_ID/docubot-repo/backend
                   env:
                     - name: PORT
                       value: "8081"
                     - name: OPENAI_API_KEY
                       valueFrom:
                         secretKeyRef:
                           name: openai_api_key
                           key: latest
                     - name: LANGCHAIN_API_KEY
                       valueFrom:
                         secretKeyRef:
                           name: langchain_api_key
                           key: latest
                     - name: LANGCHAIN_PROJECT
                       valueFrom:
                         secretKeyRef:
                           name: langchain_project
                           key: latest
                     - name: LANGCHAIN_TRACING_V2
                       value: "true"
                     - name: LANGCHAIN_ENDPOINT
                       value: "https://api.smith.langchain.com"
         EOF

  # Cloud Run URL を取得
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    id: 'get-url'
    entrypoint: 'bash'
    args:
    - '-c'
    - |
      SERVICE_URL=$(gcloud run services describe docubot-service --region us-central1 --format='value(status.url)')
      echo "Service URL: $$SERVICE_URL"
      echo "$$SERVICE_URL" > /workspace/service_url.txt

  # Cloud Runへのデプロイ
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args:
      - 'run'
      - 'services'
      - 'replace'
      - 'service.yaml'
      - '--region'
      - 'us-central1'

images:
 - 'us-central1-docker.pkg.dev/$PROJECT_ID/docubot-repo/backend'
 - 'us-central1-docker.pkg.dev/$PROJECT_ID/docubot-repo/frontend'
````

## File: docker-compose.yaml
````yaml
services:
  frontend:
    build:
      context: frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_API_URL: http://backend:8081
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_API_URL=http://backend:8081
    depends_on:
      - backend
    networks:
      - app-network

  backend:
    build:
      context: backend
      dockerfile: Dockerfile
    ports:
      - "8081:8081"
    env_file:
      - .env
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
````

## File: README.md
````markdown
# DocumentBot Agent

<p align="center">
  <h3 align="center">Next.js + FastAPI Documentation Agent</h3>
  <p align="center">AIを活用したドキュメンテーションアシスタント</p>
</p>

<div align="center">

[![Cloud Run](https://img.shields.io/badge/Cloud%20Run-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/run)
[![Cloud Build](https://img.shields.io/badge/Cloud%20Build-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/build)
[![Artifact Registry](https://img.shields.io/badge/Artifact%20Registry-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/artifact-registry)

[![CI/CD Pipeline](https://github.com/toshiyan76/documentbot-agent/actions/workflows/main.yaml/badge.svg)](https://github.com/toshiyan76/documentbot-agent/actions/workflows/main.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

## 📚 概要

DocumentBot Agentは、Next.js 14とFastAPIを組み合わせた最新のウェブアプリケーションです。OpenAI APIを活用して、ドキュメンテーションの作成・管理を効率化します。

### 🌟 主な機能

- 💬 AIを活用したドキュメント作成支援
- 🎯 コンテキストを考慮した的確な応答
- 🌐 モダンなウェブインターフェース
- ⚡ 高速なレスポンス
- 🔒 セキュアな環境

## 🛠 技術スタック

### フロントエンド
- Next.js 14
- TypeScript
- TailwindCSS
- React Query

### バックエンド
- FastAPI
- Python 3.11
- LangChain
- OpenAI API

### インフラストラクチャ
- Google Cloud Platform
  - Cloud Run
  - Artifact Registry
  - Cloud Storage
- Docker
- Terraform

### CI/CD
- GitHub Actions
- Docker multi-stage builds

## 🚀 クイックスタート

### 前提条件

- Docker Desktop 4.24.0以上
- Node.js 20.11.0以上
- Python 3.11以上
- Terraform 1.6.0以上
- GNU Make 3.81以上

### 開発環境のセットアップ

1. リポジトリのクローン:
```bash
git clone https://github.com/toshiyan76/documentbot-agent.git
cd documentbot-agent
```

2. 環境変数の設定:
```bash
cp .env_sample .env
# .envファイルを編集して必要な値を設定
```

3. 開発環境の起動:
```bash
# 初回のみ
make init

# 開発サーバーの起動
make dev
```

## 🔧 開発ワークフロー

### 開発環境

```bash
# 開発サーバーの起動（ホットリロード有効）
make dev

# フロントエンドのみ起動
make front-dev

# バックエンドのみ起動
make back-dev
```

### テストの実行

```bash
# フロントエンドのテスト
make front-test

# バックエンドのテスト
make back-test
```

### リンターとフォーマッター

```bash
# フロントエンド
npm run lint
npm run format

# バックエンド
flake8 backend
black backend
isort backend
```

## 📦 デプロイメント

### Google Cloudの設定

1. プロジェクトの作成とサービスアカウントの設定:
```bash
# terraform/init/terraform.tfvars の設定
cp terraform/init/terraform.tfvars_sample terraform/init/terraform.tfvars
# 必要な値を設定

# 初期化
make tf-init
```

2. インフラストラクチャのデプロイ:
```bash
# プランの確認
make tf-plan

# デプロイ
make tf-apply
```

### CI/CD パイプライン

GitHub Actionsを使用して以下のパイプラインを実装:

1. **コードの品質チェック**
   - リンター
   - 型チェック
   - ユニットテスト

2. **ビルドとテスト**
   - Dockerイメージのビルド
   - 統合テスト

3. **デプロイ**
   - Google Cloud Runへのデプロイ
   - Terraformによるインフラ管理

## 📝 APIドキュメント

開発環境で以下のURLにアクセス:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

* Cloud Runプロジェクト用のCI/CD構築
* Github ActionsでCI/CDワークフロー管理
* Terraformでデプロイ管理
* フロントエンドはNext.js、バックエンドはPython (FastAPI)

## 動作環境

### ローカル環境
* Docker: 4.x
* Terraform: v1.5.x
* GNU Make: 3.x
* VS Code

### プロジェクト
* Python: 3.10
* Node.js: 20
* Next.js: 14

### Google Cloud
* Artifact Registry
* Cloud Run
* Cloud Storage

## ローカル環境（dev stage）

docker composeを利用してdev stageでの動作確認方法を示します。

### 初期設定

#### 環境変数設定
1. `.env_sample`ファイルを複製して`.env`にリネーム
2. 各変数を設定。※ローカル環境で利用する情報です。
| 変数名 | 説明 | 例 |
|---|---|---|
| BACKEND_PORT | バックエンドポート（任意） | 8080 |
| FRONTEND_PORT | フロントエンドポート（任意） | 3000 |

### サービス起動&停止

1. makeコマンドで起動
```bash
make up
```

2. makeコマンドで停止
```bash
make down
```

### 起動方法
1. makeコマンド`make start`で起動する
2. http://localhost:<ポート番号>にアクセス ※デフォルトは http://localhost:3000

## 🚀本番環境🚀 Google Cloud, Cloud Run

### デプロイ方法

1. Google Cloudのプロジェクトを新規作成する。※Google Cloudのコンソールで操作

2. Google Cloudのリソース作成 ※ローカルPCのコマンドラインから操作
   1. `terraform/init/terraform.tfvars_sample`を複製して`terraform/init/terraform.tfvars`にリネーム
   2. 各種変数を設定する
   | 変数名 | 説明 |
   |---|---|
   | project_id | Google CloudのプロジェクトID |
   | location | サービスをデプロイするlocation |
   | operation_sa_id | サービス運用アカウントID |
   | operation_sa_display_name | サービス運用アカウント表示名 |
   | build_sa_id | ビルドアカウントID |
   | build_sa_display_name | ビルドアカウント表示名 |
   | artifact_registry_repository_id | Artifact RegistryのリポジトリID |
   | github_repo_owner | githubのリポジトリオーナ名 |
   | github_repo_name | githubのリポジトリ名 |
   | workload_identity_pool_id | Worklaod Identity Pool ID |
   | workload_identity_provider_id | Worklaod Identity Provider ID |

   3. cdコマンドで`terraform/init`に移動
   4. デプロイする
   ```bash
   terraform fmt
   terraform init
   terraform validate
   terraform plan
   terraform apply
   ```
   5. terraform applyの後に表示される3つの変数は手順4で利用します。
   ```
   build_service_account_email = "***@****.iam.gserviceaccount.com"
   operation_service_account_email = "***@****.iam.gserviceaccount.com"
   workload_identity_provider_name = "projects/***/locations/global/workloadIdentityPools/***/providers/***"
   ```

3. application用terraform.tfstate保存用バケットを作成
   1. `terraform/bucket/terraform.tfvars_sample`を複製して`terraform/bucket/terraform.tfvars`にリネーム
   2. `terraform.tfvars`のproject_idを設定する。
   3. cdコマンドで`terraform/bucket`に移動
   4. デプロイする
   ```bash
   terraform fmt
   terraform init
   terraform validate
   terraform plan
   terraform apply
   ```

4. Githubにシークレットを設定
   1. Githubのリポジトリにアクセスし、Setting>Secrets and Variables>Actionsで下表の変数を設定する。※Github Actionsで利用する変数
   | 変数名 | 説明 |
   |---|---|
   | GCP_PROJECT_ID | プロジェクトID |
   | GCP_REGION | リージョン（location） |
   | ARTIFACT_REPO | Artifact Registoryのリポジトリ名 |
   | BUILD_ACCOUNT | ビルドアカウントのID |
   | OPERATION_ACCOUNT | 運用アカウントのID |
   | WORKLOAD_IDENTITY_PROVIDER | WORKLOAD_IDENTITY_PROVIDERのID |

5. Github Actionsを走らせてCloud Runにデプロイする。
   1. 適当なブランチを作成してプッシュ
   2. Githubでmainブランチへのプルリクエストを出す
   3. Actionsが実行されてArtifact RegistoryにDockerイメージがデプロイされ、terraform planが終わるまで待機
   4. terraform planの結果を見てデプロイして問題ないか確認
   5. プルリクエストをマージ
   6. Actionsが実行されてCloud Runにデプロイされる

## 💀Google Cloudリソース削除方法💀

### 手順1. Cloud Runを削除する ※Github Actionsから操作
1. GithubのActionsタブにある`terraform-destroy`workflowを押してRun workflowを実行
2. Actionsが実行されてCloud Runリソースが削除されたことを確認

### 手順2. バケットを削除 ※ローカルPCのターミナルで操作
1. cdコマンドで`terraform/init`に移動
2. `terraform plan --lock=false -destroy`を実行してapply内容を確認
3. `terraform apply -destroy`を実行して削除されたことを確認

### 手順3. バケットを削除 ※Google Cloudのコンソールから操作
1. Google Cloudのコンソールにアクセス
2. Cloud Storageのバケットタブに移動
3. 対象のバケットを選択して削除

### 手順4. プロジェクトを削除 ※Google Cloudのコンソールから操作
1. Google Cloudのコンソールにアクセス
2. 右上の︙を押して「プロジェクトの設定」に移動
3. シャットダウンを押す
4. ダイアログにプロジェクトIDを入力して「このままシャットダウン」を押す
````
