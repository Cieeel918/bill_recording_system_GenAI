from flask import Flask, render_template,request,redirect
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import openai
from dash import Dash,dcc, html, Input, Output
import plotly.express as px
from functions import *
from datetime import datetime
import os
import dash
import logging
logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)

# 定义 CSV 存储路径
CSV_PATH = "/mnt/data/user_history.csv"

# 确保 CSV 文件存在，并加载数据
if os.path.exists(CSV_PATH):
    user_history = pd.read_csv(CSV_PATH)
else:
    user_history = pd.DataFrame(columns=['timestamp', 'income_or_spending', 'type', 'amount'])

@app.route('/', methods=["GET", "POST"])
def home():
    global user_history
    
    if request.method == "POST":
        # 获取用户输入
        income_or_spending = int(request.form['income_or_spending'])
        transaction_type = request.form['type']
        amount = float(request.form['amount'])
        timestamp = datetime.now().strftime('%Y-%m-%d')

        # 生成新数据
        new_entry = pd.DataFrame({
            'timestamp': [timestamp],
            'income_or_spending': [income_or_spending],
            'type': [transaction_type],
            'amount': [amount]
        })

        # 追加到全局 DataFrame
        user_history = pd.concat([user_history, new_entry], ignore_index=True)

        # **将数据存储到 CSV（追加模式）**
        user_history.to_csv(CSV_PATH, index=False)

    return render_template('home.html')



dash_app = Dash(__name__, server=app, routes_pathname_prefix='/dash/', requests_pathname_prefix='/dash/')



df = load_data(CSV_PATH)

# 计算月度收入和支出
def get_monthly_summary(df):
    if df.empty:
        return pd.DataFrame(columns=['month', 'income', 'spending'])
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.month

    summary = df.groupby('month').agg(
        income=('amount', lambda x: x[df['income_or_spending'] == 1].sum()),
        spending=('amount', lambda x: x[df['income_or_spending'] == 0].sum())
    ).reset_index()
    
    return summary

monthly_summary = get_monthly_summary(df)

# 设置 Dash 页面
dash_app.layout = html.Div([
    html.H1("Annual Bill Analysis", style={'textAlign': 'center'}),

    # 月度柱状图
    dcc.Graph(
        id='monthly-bar',
        figure=px.bar(
            monthly_summary,
            x='month',
            y=['income', 'spending'],
            title="Monthly Income vs Spending",
            labels={'value': 'Amount', 'variable': 'Category'},
            barmode='group'
        )
    ),

    html.Hr(),

    # 选择月份和类别
    html.Div([
        dcc.Dropdown(
            id='month-selector',
            options=[{'label': f'Month {m}', 'value': m} for m in range(1, 13)],
            value=1,
            style={'width': '200px'}
        ),
        dcc.RadioItems(
            id='category-selector',
            options=[
                {'label': 'Income', 'value': 1},
                {'label': 'Spending', 'value': 0}
            ],
            value=0,
            inline=True
        ),
        dcc.Graph(id='type-pie')
    ])
])

# Dash 交互逻辑
@dash_app.callback(
    dash.dependencies.Output('type-pie', 'figure'),
    [dash.dependencies.Input('month-selector', 'value'),
     dash.dependencies.Input('category-selector', 'value')]
)
def update_pie_chart(selected_month, selected_category,CSV_PATH):
    df = load_data(CSV_PATH)
    if df.empty:
        return {}

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.month

    filtered_df = df[(df['month'] == selected_month) & (df['income_or_spending'] == selected_category)]
    
    if filtered_df.empty:
        return {}

    fig = px.pie(filtered_df, names='type', values='amount', title="Spending by Category")
    return fig

@app.route('/analysis')
def analysis():
    return redirect('/dash/')


@app.route('/suggestion',methods=["GET","POST"])
def suggestion():
    user_history = load_data()
    generated_text = None
    a = ""
    if request.method == "POST":
        a = request.form.get('user_prompt', '')
        if not a:
            return render_template('suggestion.html', message="Please enter a requirment.")
        
        prompt = prepare_prompt(a,user_history)
        generated_text = chat_with_gpt(prompt)
    
    return render_template('suggestion.html', user_prompt=a, generated_text=generated_text)





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

