from fastapi import FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Currency(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cur: str = Field(index=True)
    value: float | None = Field(default=None, index=True)


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


def get_rates_dict() -> dict:
    with Session(engine) as session:
        currencies = session.exec(select(Currency)).all()
        return {c.cur: c.value for c in currencies}


@app.get("/convert")
def convert_currency(from_cur: str, to_cur: str, amount: float):
    rates = get_rates_dict()
    if from_cur == to_cur:
        return {"result": amount}

    try:
        if from_cur == "EUR":
            result = amount * rates[to_cur]
        elif to_cur == "EUR":
            result = amount / rates[from_cur]
        else:
            eur_amount = amount / rates[from_cur]
            result = eur_amount * rates[to_cur]
        return {
            "from": from_cur,
            "to": to_cur,
            "amount": amount,
            "result": round(result, 2),
            "path": [from_cur, "EUR", to_cur],
        }
    except KeyError as c:
        raise HTTPException(status_code=400, detail=f"Currency {c} not supported")


@app.post("/rates/")
def add_currency(currency: Currency):
    with Session(engine) as session:
        session.add(currency)
        session.commit()
        session.refresh(currency)
        return currency


@app.get("/rates/")
def read_rates():
    with Session(engine) as session:
        rates = session.exec(select(Currency)).all()
        return rates


@app.get("/rates/{rate_id}")
def read_rate(rate_id: int):
    with Session(engine) as session:
        rate = session.get(Currency, rate_id)
        if not rate:
            raise HTTPException(status_code=404, detail="Currency not found")
        return rate


@app.put("/rates/{rate_id}")
def update_rate(rate_id: int, rate_data: Currency):
    with Session(engine) as session:
        rate = session.get(Currency, rate_id)
        if not rate:
            raise HTTPException(status_code=404, detail="Currency not found")

        for field, value in rate_data.model_dump().items():
            setattr(rate, field, value)
        session.commit()
        session.refresh(rate)
        return rate


@app.delete("/rates/{rate_id}")
def delete_rate(rate_id: int):
    with Session(engine) as session:
        rate = session.get(Currency, rate_id)
        if not rate:
            raise HTTPException(status_code=404, detail="Currency not found")
        session.delete(rate)
        session.commit()
        return rate
