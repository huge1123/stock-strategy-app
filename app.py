import sqlite3
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=".")

def get_yesterday_stocks():
    conn = sqlite3.connect("stock.db")
    c = conn.cursor()
    yesterday = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT stock_code FROM stock_selection WHERE selection_date = ?", (yesterday,))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def analyze():
    stocks = get_yesterday_stocks()
    strategy = "Buy and Hold"
    return stocks, strategy

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    stocks, strategy = analyze()
    return templates.TemplateResponse("index.html", {"request": request, "stocks": stocks, "strategy": strategy})
