
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import akshare as ak
import datetime
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

stock_file = "stock_codes.txt"

@app.get("/", response_class=HTMLResponse)
async def index():
    input_form = '''
    <html><body>
    <h2>输入股票代码（用逗号分隔）:</h2>
    <form action="/save" method="post">
        <input name="codes" type="text" style="width:300px;" placeholder="例如：000001,600519,002594"/>
        <input type="submit" value="保存"/>
    </form>
    </body></html>
    '''
    return input_form

@app.post("/save")
async def save_codes(codes: str = Form(...)):
    with open(stock_file, "w") as f:
        f.write(codes.strip())
    return HTMLResponse(f"<p>股票代码已保存：{codes}</p><a href='/analyze'>点击查看分析</a>")

@app.get("/analyze", response_class=HTMLResponse)
async def analyze():
    if not os.path.exists(stock_file):
        return HTMLResponse("<p>尚未输入股票代码</p>")

    with open(stock_file, "r") as f:
        codes = [code.strip() for code in f.read().split(",") if code.strip()]
    
    up_count = 0
    down_count = 0
    html = "<html><body><h2>实时涨跌分析</h2><table border='1'><tr><th>代码</th><th>名称</th><th>当前价格</th><th>涨跌幅</th></tr>"

    for code in codes:
        try:
            df = ak.stock_zh_a_spot()
            stock = df[df['代码'] == code].iloc[0]
            change = stock['涨跌幅']
            html += f"<tr><td>{code}</td><td>{stock['名称']}</td><td>{stock['最新价']}</td><td>{change:.2f}%</td></tr>"
            if change > 0:
                up_count += 1
            else:
                down_count += 1
        except:
            html += f"<tr><td>{code}</td><td colspan='3'>数据获取失败</td></tr>"

    total = len(codes)
    strategy = ""
    if up_count / total > 0.5:
        strategy = "建议：买入"
    elif up_count / total >= 0.3:
        strategy = "建议：观望"
    else:
        strategy = "建议：空仓"

    html += f"</table><p>{strategy}</p></body></html>"
    return HTMLResponse(html)
