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
