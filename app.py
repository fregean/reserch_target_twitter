import os

from flask import Flask, request, redirect, render_template, flash, session, jsonify, url_for
from werkzeug.utils import secure_filename
from requests_oauthlib import OAuth1Session
import numpy as np

import config
import recent_search_v2
import processing




classes = ["0","1","2","3","4","5","6","7","8","9"]
image_size = 28

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.secret_key = 'hogehoge'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

model = load_model('./model.h5')#学習済みモデルをロード


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('ファイルがありません')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('ファイルがありません')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            #受け取った画像を読み込み、np形式に変換
            img = image.load_img(filepath, grayscale=True, target_size=(image_size,image_size))
            img = image.img_to_array(img)
            data = np.array([img])
            #変換したデータをモデルに渡して予測する
            result = model.predict(data)[0]
            predicted = result.argmax()
            pred_answer = "これは " + classes[predicted] + " です"

            return render_template("index.html",answer=pred_answer)

    return render_template("index.html",answer="")


@app.route('/request_token',methods=['GET'])
def request_token():

    consumer_key = config.API_KEY
    consumer_secret = config.API_SECRET

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
            config.API_KEY,
            client_secret=config.API_SECRET,
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
            config.API_KEY,
            client_secret=config.API_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )

    return oauth

@app.route('/get_keyword', methods=['GET'])
def get_keyword():
    return render_template("get_keyword.html")

@app.route('/post_tweets', methods=['GET', 'POST'])
def post_tweets():
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        json_response = recent_search_v2.search_tweet(keyword, get_oauth())
        tweets = processing.return_tweets(json_response)
        df_values = tweets.values.tolist()
        df_columns = tweets.columns.tolist()
    return render_template('post_tweets.html', df_values=df_values, df_columns=df_columns, title='いいね数の多いツイート上位10件',)

@app.route('/keep_waiting', methods=['GET'])
def keep_waiting():
    twitter_id = request.args.get('twitter_id')
    return render_template("keep_waiting.html")





if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host ='0.0.0.0',port = port, debug=True)


