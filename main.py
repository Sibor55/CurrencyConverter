from fastapi import FastAPI, HTTPException, Request
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="template")
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


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, from_cur: str = None, to_cur: str = None, amount: float = None):
    rates = get_rates_dict()
    currencies = list(rates.keys())
    result = error = None
    
    if all([from_cur, to_cur, amount is not None]):
        try:
            if from_cur not in currencies or to_cur not in currencies:
                raise ValueError("Invalid currency selected")
                
            from_rate = rates.get(from_cur)
            to_rate = rates.get(to_cur)
            
            if from_rate == 0:
                raise ValueError("Zero rate conversion not allowed")
            
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
        except (KeyError, ValueError, TypeError) as e:
            error = f"Conversion error: {str(e)}"
        except Exception as e:
            error = f"Unexpected error: {str(e)}"
    
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "currencies": currencies,
            "result": result,
            "error": error,
            "from_cur": from_cur,
            "to_cur": to_cur,
            "amount": amount
        }
    )

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
