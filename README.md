# DocumentBot Agent

<p align="center">
  <h3 align="center">Next.js + FastAPI Documentation Agent</h3>
</p>

<p align="center">AIを活用したドキュメンテーションアシスタント。Next.js 14とFastAPIを使用したモダンなウェブアプリケーション。</p>

<br/>

## 概要

このプロジェクトは、OpenAIのAPIを活用してドキュメンテーションの作成・管理を支援するAIアシスタントです。フロントエンドにNext.js 14、バックエンドにFastAPIを採用し、モダンで使いやすいインターフェースを提供します。

## 主な機能

- 💬 AIを活用したドキュメント作成支援
- 🎯 コンテキストを考慮した的確な応答
- 🌐 モダンなウェブインターフェース
- ⚡ 高速なレスポンス

## 技術スタック

- フロントエンド: Next.js 14, TailwindCSS
- バックエンド: FastAPI, LangChain
- AI: OpenAI API

## 開発環境のセットアップ

1. 環境変数の設定:

```bash
# .envファイルを作成
cp .env.sample .env
# OpenAI APIキーを設定
```

2. Python仮想環境の作成と有効化:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. 依存関係のインストール:

```bash
# フロントエンド
npm install

# バックエンド
pip install -e .
```

4. 開発サーバーの起動:

```bash
npm run dev
```

アプリケーションは以下のURLで起動します：
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000

## APIエンドポイント

- `POST /api/chat`: チャットメッセージの送受信
- `GET /health`: ヘルスチェック

## 環境変数

- `OPENAI_API_KEY`: OpenAI APIキー（必須）
- `PORT`: バックエンドサーバーのポート番号（デフォルト: 8000）

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
