from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import datetime
import akshare as ak
import uvicorn
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
DB_PATH = os.path.join(BASE_DIR, 'stocks.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stock_selection (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT,
                    selection_date DATE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stock_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT,
                    stat_date DATE,
                    price_change REAL)''')
    conn.commit()
    conn.close()

def add_stock(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.date.today()
    c.execute("INSERT INTO stock_selection (stock_code, selection_date) VALUES (?, ?)", (code, today))
    conn.commit()
    conn.close()

def get_yesterday_stocks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    c.execute("SELECT stock_code FROM stock_selection WHERE selection_date = ?", (yesterday,))
    stocks = [row[0] for row in c.fetchall()]
    conn.close()
    return stocks

def get_realtime_change(stock_code):
    try:
        df = ak.stock_zh_a_spot()
        match = df[df['代码'] == stock_code]
        if not match.empty:
            return float(match['涨跌幅'].values[0])
    except:
        return None

def analyze():
    stocks = get_yesterday_stocks()
    result = []
    up = 0
    for code in stocks:
        change = get_realtime_change(code)
        if change is not None:
            result.append((code, change))
            if change > 0:
                up += 1
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO stock_stats (stock_code, stat_date, price_change) VALUES (?, ?, ?)",
                      (code, datetime.date.today(), change))
            conn.commit()
            conn.close()
    total = len(result)
    ratio = up / total if total else 0
    if ratio > 0.5:
        strategy = "买入"
    elif ratio >= 0.3:
        strategy = "观望"
    else:
        strategy = "空仓"
    return result, strategy

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    stocks, strategy = analyze()
    return templates.TemplateResponse("index.html", {"request": request, "stocks": stocks, "strategy": strategy})

@app.post("/submit")
async def submit(code: str = Form(...)):
    add_stock(code)
    return RedirectResponse(url="/", status_code=303)

if __name__ == '__main__':
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=10000)
