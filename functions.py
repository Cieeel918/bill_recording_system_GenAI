import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from openai import OpenAI
from datetime import datetime
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import plotly.express as px
import os
from io import StringIO


def prepare_prompt(user_prompt,history_info):
    '''收入多少，各类型支出多少，'''
    df=history_info
    df['timestamp'] = df['timestamp'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d"))
    df["month"]=df["timestamp"].apply(lambda x:x.month)
    df_spend = df.groupby(["month","income_or_spending"],as_index=False).agg({"amount":"sum"}).query("""income_or_spending==0""")
    df_income= df.groupby(["month","income_or_spending"],as_index=False).agg({"amount":"sum"}).query("""income_or_spending==1""")
    
    text_all=""  #每月支出和收入
    for i in range(df_income.shape[0]):
        income=df_income.iloc[i,:]
        spend=df_spend.iloc[i,:]
        text_unit=f"In month {i+1}, the spending is {spend[-1]} and the income is {income[-1]}. "
        text_all += text_unit
    
    df_income_type = df.groupby(["income_or_spending","type"],as_index=False).agg({"amount":"sum"}).query("""income_or_spending==1""")
    df_spend_type = df.groupby(["income_or_spending","type"],as_index=False).agg({"amount":"sum"}).query("""income_or_spending==0""")

    income_type_info='' #不同收入类型
    for i in range(df_income_type.shape[0]):
        info=df_income_type.iloc[i,:]
        type=f'The income type is {info[-2]}, the amount is {info[-1]}.'
        income_type_info+=type

    spend_type_info='' #不同支出类型
    for i in range(df_spend_type.shape[0]):
        info=df_spend_type.iloc[i,:]
        type=f'The spending type is {info[-2]}, the amount is {info[-1]}.'
        spend_type_info+=type

    
    prompt = "here is my monthly income and spending information:" + "\n" + text_all + "\n" + "here is my income type information" + income_type_info + "here is my spend type information" + spend_type_info
    prompt = "here is my goal: " + user_prompt
    return prompt




def chat_with_gpt(user_input):
    
    '''
    description: 
        this function call openai api to make users able to interact with chatgpt within this website

    parameters:
        None
    
    output:
        print the response from chat-gpt

    '''
    client = OpenAI(
    api_key=os.getenv("api_key"),
    )
    conversation = [{"role": "system", "content": "You are a helpful assistant. And you need to give the user detailed financial plan to achieve his goal."}]
    try:
        conversation.append({"role": "user", "content": user_input})
        chat_completion = client.chat.completions.create(
            messages=conversation,
            model="gpt-4o-mini",
                    )
        assistant_reply = chat_completion.choices[0].message.content
        conversation.append({"role": "assistant", "content": assistant_reply})
        return assistant_reply

    except TimeoutError:
        print("error")


def load_data(CSV_PATH):
    try:
        if os.path.exists(CSV_PATH):
            return pd.read_csv(CSV_PATH)
        else:
            return pd.DataFrame(columns=['timestamp', 'income_or_spending', 'type', 'amount'])
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame(columns=['timestamp', 'income_or_spending', 'type', 'amount'])


def get_monthly_summary(df):
    income = df[df.income_or_spending == 1].groupby('month').amount.sum().rename('income')
    spending = df[df.income_or_spending == 0].groupby('month').amount.sum().rename('spending')
    return pd.concat([income, spending], axis=1).reset_index().fillna(0)

def get_month_type_data(df, month, category):
    filtered = df[(df.month == month) & (df.income_or_spending == category)]
    return filtered.groupby('type', as_index=False).amount.sum()