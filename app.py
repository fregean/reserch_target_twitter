import os
from os.path import join, dirname
import json

from flask import Flask, request, redirect, render_template, flash, session, jsonify, url_for
from werkzeug.utils import secure_filename
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv
import numpy as np
import ndjson

import recent_search_v2
import processing


app = Flask(__name__)
app.secret_key = 'hogehoge'

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


@app.route('/', methods=['GET', 'POST'])
def certification_app():
    return render_template("index.html",answer="")

@app.route('/request_token',methods=['GET'])
def request_token():

    consumer_key = os.environ.get('API_KEY')
    consumer_secret = os.environ.get('API_SECRET')

    # Get authorization
    request_token_url = "https://api.twitter.com/oauth/request_token"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    try:
        oauth.fetch_request_token(request_token_url)
    except ValueError:
        print(
            "There may have been an issue with the consumer_key or consumer_secret you entered."
        )

    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    return redirect(authorization_url)

@app.route('/callback', methods=['GET'])
def callback():
    oauth_token = request.args.get('oauth_token')
    oauth_token_secret = request.args.get('oauth_token_secret')
    verifier= request.args.get('oauth_verifier')

    oauth = OAuth1Session(
            os.environ.get('API_KEY'),
            client_secret=os.environ.get('API_SECRET'),
            resource_owner_key=oauth_token,
            #resource_owner_secret=oauth_token_secret,
            verifier=verifier
        )
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    oauth_tokens = oauth.fetch_access_token(access_token_url)
    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]

    session['twitter_oauth_token'] = {'access_token':access_token,'access_token_secret':access_token_secret}
    #oauth = get_oauth()
    # URLルート
    return redirect(url_for('get_keyword'))

def get_oauth():
    access_token = session['twitter_oauth_token']['access_token']
    access_token_secret = session['twitter_oauth_token']['access_token_secret']
    oauth = OAuth1Session(
            os.environ.get('API_KEY'),
            client_secret=os.environ.get('API_SECRET'),
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )

    return oauth

@app.route('/get_keyword', methods=['GET'])
def get_keyword():
    return render_template('get_keyword.html', explanation='関心のあるキーワードを一つ入力してください')

@app.route('/post_tweets', methods=['GET', 'POST'])
def post_tweets():
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        mail_address = request.form.get('mail_address')
        name = request.form.get('name')
        json_response = recent_search_v2.search_tweet(keyword, get_oauth())
        if not 'data' in json_response:
            # エラーメッセージを受け取った場合
            return render_template('get_keyword.html', explanation='ツイートが存在しなかったのでもう一度キーワードを入力してください')
        tweets = processing.return_tweets(json_response)
        df_values = tweets.values.tolist()
        df_columns = tweets.columns.tolist()
        session['client'] = {'name': name, 'mail_address': mail_address , 'keyword': keyword, 'tweets': df_values}
    return render_template('post_tweets.html', df_values=df_values, df_columns=df_columns, title='いいね数の多いツイート上位10件',)

@app.route('/display_information', methods=['GET'])
def display_information():
    twitter_id = request.args.get('twitter_id')
    session['client']['twitter_id'] = twitter_id
    with open('data/db_tweets.ndjson', mode='a') as f:
        writer = ndjson.writer(f)
        writer.writerow(session['client'])
    return render_template('display_information.html')

@app.route('/display_exception', methods=['GET'])
def display_exception():
    return render_template('display_exception.html')

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host ='0.0.0.0',port = port, debug=True)


