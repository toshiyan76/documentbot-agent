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
