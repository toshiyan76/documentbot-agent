from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """ヘルスチェックエンドポイントのテスト"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "openai_api_key" in data

def test_chat_endpoint():
    """チャットエンドポイントのテスト"""
    response = client.post(
        "/chat",
        json={"message": "新しいECサイトの要件を定義したい"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data

def test_chat_endpoint_invalid_request():
    """不正なリクエストのテスト"""
    response = client.post(
        "/chat",
        json={}  # messageフィールドが欠けている
    )
    assert response.status_code == 422  # バリデーションエラー 