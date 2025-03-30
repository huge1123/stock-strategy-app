
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import akshare as ak
import sqlite3
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=".")

def init_db():
    conn = sqlite3.connect("stock.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS stock_selection (
            stock_code TEXT,
            selection_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def fetch_stock_data(code):
    try:
        df = ak.stock_zh_a_spot()
        info = df[df['代码'] == code].iloc[0]
        price = round(float(info['最新价']), 2)
        change = round(float(info['涨跌幅']), 2)
        volume = info['成交量']
        status = "买入" if change > 2 else "观望" if change > 0 else "空仓"
        return {
            "code": code,
            "price": price,
            "change": change,
            "volume": volume,
            "status": status
        }
    except:
        return None

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    conn = sqlite3.connect("stock.db")
    c = conn.cursor()
    c.execute("SELECT stock_code FROM stock_selection")
    stock_codes = [row[0] for row in c.fetchall()]
    conn.close()

    stock_data = []
    up, down, neutral = 0, 0, 0
    for code in stock_codes:
        data = fetch_stock_data(code)
        if data:
            stock_data.append(data)
            if data['status'] == "买入":
                up += 1
            elif data['status'] == "空仓":
                down += 1
            else:
                neutral += 1

    strategy = "建议买入" if up > down else "建议空仓" if down > up else "建议观望"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "stock_codes": stock_codes,
        "stock_data": stock_data,
        "strategy": strategy,
        "up_count": up,
        "down_count": down,
        "neutral_count": neutral
    })

@app.post("/add_stock")
def add_stock(code: str = Form(...)):
    conn = sqlite3.connect("stock.db")
    c = conn.cursor()
    today = datetime.today().strftime("%Y-%m-%d")
    c.execute("INSERT INTO stock_selection VALUES (?, ?)", (code, today))
    conn.commit()
    conn.close()
    return RedirectResponse("/", status_code=302)
