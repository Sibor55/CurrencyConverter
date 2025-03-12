from fastapi import FastAPI, HTTPException, Request, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, UniqueConstraint
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import confloat
from typing import Optional

templates = Jinja2Templates(directory="template")

class CurrencyBase(SQLModel):
    cur: str = Field(index=True, max_length=3, regex="^[A-Z]{3}$")
    value: confloat(gt=0)  # Значение должно быть положительным

class Currency(CurrencyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    __table_args__ = (UniqueConstraint("cur"),)  # Уникальность валюты

class CurrencyCreate(CurrencyBase):
    pass

class CurrencyUpdate(CurrencyBase):
    pass

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

@app.get("/", response_class=HTMLResponse)
def read_root(
    request: Request,
    from_cur: Optional[str] = Query(None, min_length=3, max_length=3),
    to_cur: Optional[str] = Query(None, min_length=3, max_length=3),
    amount: Optional[confloat(gt=0)] = Query(None, description="Must be greater than 0")
):
    rates = get_rates_dict()
    currencies = list(rates.keys())
    result = error = None
    
    if all([from_cur, to_cur, amount]):
        try:
            # Валидация валют
            if from_cur not in currencies:
                raise ValueError(f"Currency {from_cur} not found")
            if to_cur not in currencies:
                raise ValueError(f"Currency {to_cur} not found")

            from_rate = rates[from_cur]
            to_rate = rates[to_cur]

            # Конвертация
            if from_cur == to_cur:
                result = amount
            elif from_cur == "EUR":
                result = amount * to_rate
            elif to_cur == "EUR":
                result = amount / from_rate
            else:
                eur_amount = amount / from_rate
                result = eur_amount * to_rate
            
            result = round(result, 2)
        except Exception as e:
            error = f"Error: {str(e)}"
    
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "currencies": sorted(currencies),
            "result": result,
            "error": error,
            "from_cur": from_cur,
            "to_cur": to_cur,
            "amount": amount
        }
    )

@app.post("/rates/", response_model=Currency)
def add_currency(currency: CurrencyCreate):
    with Session(engine) as session:
        # Проверка существующей валюты
        existing = session.exec(select(Currency).where(Currency.cur == currency.cur)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Currency already exists")
        
        new_currency = Currency(**currency.model_dump())
        session.add(new_currency)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")
        
        session.refresh(new_currency)
        return new_currency

@app.get("/rates/", response_model=list[Currency])
def read_rates():
    with Session(engine) as session:
        return session.exec(select(Currency)).all()

@app.get("/rates/{rate_id}", response_model=Currency)
def read_rate(rate_id: int):
    with Session(engine) as session:
        rate = session.get(Currency, rate_id)
        if not rate:
            raise HTTPException(status_code=404, detail="Currency not found")
        return rate

@app.put("/rates/{rate_id}", response_model=Currency)
def update_rate(rate_id: int, rate_data: CurrencyUpdate):
    with Session(engine) as session:
        rate = session.get(Currency, rate_id)
        if not rate:
            raise HTTPException(status_code=404, detail="Currency not found")

        # Проверка на уникальность при обновлении
        if rate_data.cur != rate.cur:
            existing = session.exec(select(Currency).where(Currency.cur == rate_data.cur)).first()
            if existing:
                raise HTTPException(status_code=400, detail="Currency already exists")

        for key, value in rate_data.model_dump().items():
            setattr(rate, key, value)
        
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")
        
        session.refresh(rate)
        return rate

@app.delete("/rates/{rate_id}")
def delete_rate(rate_id: int):
    with Session(engine) as session:
        rate = session.get(Currency, rate_id)
        if not rate:
            raise HTTPException(status_code=404, detail="Currency not found")
        
        session.delete(rate)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")
        
        return {"message": "Currency deleted successfully"}