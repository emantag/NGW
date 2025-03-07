from flask import Flask, request, jsonify, send_file
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import yfinance as yf
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)
dash_app = dash.Dash(__name__, server=app, routes_pathname_prefix='/stocks/', suppress_callback_exceptions=True)

def fetch_stock_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")
    if hist.empty:
        return None, None
    hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
    return stock, hist

dash_app.layout = html.Div([
    html.H1("Stock Analysis Dashboard"),
    dcc.Input(id='ticker-input', type='text', value='AAPL', debounce=True, placeholder='Enter Ticker...'),
    html.Button('Submit', id='submit-button', n_clicks=0),
    dcc.Graph(id='stock-chart'),
    html.Br(),
    html.A("Download PDF Report", id='download-link', href='/generate_report/AAPL', target="_blank")
])

@dash_app.callback(
    [Output('stock-chart', 'figure'), Output('download-link', 'href')],
    [Input('submit-button', 'n_clicks')],
    [dash.dependencies.State('ticker-input', 'value')]
)
def update_chart(n_clicks, ticker):
    stock, hist = fetch_stock_data(ticker)
    if hist is None:
        return go.Figure(), f'/generate_report/AAPL'
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Close'))
    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_20'], mode='lines', name='SMA 20', line=dict(dash='dash')))
    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], mode='lines', name='SMA 50', line=dict(dash='dash')))
    fig.update_layout(title=f"{ticker} Stock Price", xaxis_title="Date", yaxis_title="Price")
    return fig, f'/generate_report/{ticker}'

@app.route('/generate_report/<ticker>')
def generate_pdf_report(ticker):
    stock, hist = fetch_stock_data(ticker)
    if hist is None:
        return "Error: No data available", 400
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.drawString(100, 800, f"Stock Report for {ticker}")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{ticker}_report.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
