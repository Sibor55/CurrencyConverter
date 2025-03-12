from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select
from main import app, Currency, engine

client = TestClient(app)


def setup_module():
    # Очистка базы перед тестами
    with Session(engine) as session:
        session.exec(delete(Currency))
        session.commit()
        session.add(Currency(cur="EUR", value=1.0))
        session.add(Currency(cur="USD", value=1.2))
        session.commit()


def test_get_all_rates():
    response = client.get("/rates/")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert any(c["cur"] == "EUR" for c in response.json())
    assert any(c["cur"] == "USD" for c in response.json())


def test_get_specific_rate():
    response = client.get("/rates/1")
    assert response.status_code == 200
    assert response.json()["cur"] == "EUR"
    assert response.json()["value"] == 1.0


def test_get_nonexistent_rate():
    response = client.get("/rates/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Currency not found"}


def test_add_currency_success():
    new_currency = {"cur": "JPY", "value": 0.8}
    response = client.post("/rates/", json=new_currency)
    assert response.status_code == 200
    assert response.json()["cur"] == "JPY"

    # Проверяем, что добавилось в БД
    with Session(engine) as session:
        currency = session.exec(select(Currency).where(Currency.cur == "JPY")).first()
        assert currency is not None


def test_add_existing_currency():
    response = client.post("/rates/", json={"cur": "EUR", "value": 1.0})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_convert_currency_valid():
    response = client.get("/convert/?from_cur=EUR&to_cur=USD&amount=100")
    assert response.status_code == 200
    assert response.json() == 120.0  # 100 * 1.2


def test_convert_invalid_currency():
    response = client.get("/convert/?from_cur=XYZ&to_cur=USD&amount=100")
    assert response.status_code == 400
    assert "Currency XYZ not found" in response.json()["detail"]


def test_convert_missing_parameters():
    response = client.get("/convert/?from_cur=EUR")
    assert response.status_code == 422  # Ошибка валидации
    assert "field required" in response.text.lower()


def test_update_currency():
    # Сначала создаем валюту для обновления
    client.post("/rates/", json={"cur": "GBP", "value": 0.9})

    update_data = {"cur": "GBP", "value": 0.85}
    response = client.put("/rates/4", json=update_data)
    assert response.status_code == 200
    assert response.json()["value"] == 0.85


def test_delete_currency():
    response = client.delete("/rates/2")  # USD
    assert response.status_code == 200
    assert response.json() == {"message": "Currency deleted successfully"}

    # Проверяем, что валюта удалена
    response = client.get("/rates/2")
    assert response.status_code == 404
