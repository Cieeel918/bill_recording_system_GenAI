from flask import Flask, render_template,request
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

app = Flask(__name__)
dashapp = Dash(__name__, server=app, url_base_pathname="/analysis/", suppress_callback_exceptions=True)

user_history = pd.DataFrame(columns=['timestamp','income_or_spending', 'type', 'amount'])
# existed_data = pd.read_csv("user_annual_bill_data.csv")
# user_history = pd.concat([user_history,existed_data],axis=0)

@app.route('/',methods=["GET","POST"])
def home():
    """
    允许用户输入信息，保存到user_history这个dataframe里面
    允许多次输入信息
    允许跳转另外两个页面
    """
    global user_history
    if request.method == "POST":
    
        income_or_spending = int(request.form['income_or_spending'])
        transaction_type = request.form['type']
        amount = float(request.form['amount'])
        timestamp = datetime.now().strftime('%Y/%m/%d')

        
        new_entry = pd.DataFrame({
            'timestamp': [timestamp],
            'income_or_spending': [income_or_spending],
            'type': [transaction_type],
            'amount': [amount]
        })

        user_history = pd.concat([user_history,new_entry],ignore_index = True)
        #print(user_history)

    return render_template('home.html')

df = load_data()
# df = user_history
monthly_summary = get_monthly_summary(df)

dashapp.layout = html.Div([
    html.H1("Annual Bill Analysis", style={'textAlign': 'center'}),
    
    # 图表1：静态月度柱状图
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
    
    # 图表2：动态饼图
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

@dashapp.callback(
    Output('type-pie', 'figure'),
    [Input('month-selector', 'value'),
    Input('category-selector', 'value')]
)
def update_pie(month, category):
    data = get_month_type_data(df, month, category)
    title = f'{"Income" if category else "Spending"} Types - Month {month}'
    return px.pie(data, values='amount', names='type', title=title)

@app.route('/analysis/',methods=["GET","POST"])
def analysis():
    return render_template('analysis.html')


@app.route('/suggestion',methods=["GET","POST"])
def suggestion():
    user_history = create_sample_data()
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
    app.run(debug=True, host='0.0.0.0')

