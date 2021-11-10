import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate
from os.path import join, dirname
import time
import functools

msg = MIMEMultipart()

import pandas as pd
import numpy as np
import ndjson
from dotenv import load_dotenv
import sentence_vectorizer
import demoji
from ja_sentence_segmenter.common.pipeline import make_pipeline
from ja_sentence_segmenter.concatenate.simple_concatenator import concatenate_matching
from ja_sentence_segmenter.normalize.neologd_normalizer import normalize
from ja_sentence_segmenter.split.simple_splitter import split_newline, split_punctuation

import liking_users
import liked_tweets
import sentence_vectorizer

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

DIR = 'data/db_tweets.json'


def get_liking_users(target_tweet_id):
    """ターゲットツイートにいいねしたユーザー情報をデータフレームで返す
    """
    # ターゲットツイートIDからいいねしたユーザーを検索
    json_response = liking_users.get_users(target_tweet_id)
    # いいねしたユーザー情報のデータフレーム
    return pd.json_normalize(json_response['data'])

def get_liking_users_liked_tweets(df_users, target_tweet):
    """ユーザーデータフレームからユーザーがいいねしたツイートのデータフレームを返す
    """
    # ユーザーIDからいいねしたツイートを検索
    dic_liked_tweets = liked_tweets.get_liked_tweets(df_users['id'])
    # ユーザーごとの辞書データを結合したマルチカラムデータフレームを作成
    df_liked_tweets = pd.concat({k: pd.DataFrame(v['data']) for k, v in dic_liked_tweets.items()}, \
        axis=0).unstack(0).swaplevel(1,0, axis=1).sort_index(axis=1)
    # ユーザーIDを抽出
    user_ids = df_liked_tweets.columns.get_level_values(0).unique()

    tweets_text_list = []
    for ids in user_ids:
        user_texts = df_liked_tweets[ids]['text'].copy()
        # いいねしたツイートにターゲットツイートが含まれていたらNANに置換する
        user_texts.replace(target_tweet, np.nan, inplace=True)
        tweets_text_list.append(user_texts)
        # いいねしたツイートのデータフレーム
    df_tweets_text = pd.DataFrame(tweets_text_list, index=user_ids)
    return df_tweets_text.T

# ユーザーのいいねツイートへの前処理用

def select_tweets(keyword, df_liked_tweets):
    """ツイートのデータフレームからキーワードを含む文章をもつユーザーシリーズを作成
    """
    for col in df_liked_tweets.columns:
        flag = df_liked_tweets[col].str.contains(keyword, na=False)
        df_liked_tweets.loc[~flag, col] = np.nan

    # NAN以外の値を持つユーザーIDを特定する（POSTする候補）
    exist_flag = df_liked_tweets.count() != 0
    user_name = df_liked_tweets.T[exist_flag].index

    # POSTするユーザー候補ごとに関連ツイート文を全て結合
    candidate_users = df_liked_tweets[user_name].T
    # 後で文を区切る区切りのためツイート文の文末に'。'を追加
    candidate_users += '。'
    # ツイート文を結合
    return candidate_users.iloc[:,0].str.cat([candidate_users.iloc[:,col] for col in candidate_users.columns[1:]], na_rep='')

def segment_tweet(candidate_users):
    """ツイートを文単位でセパレートしたユーザーシリーズを返す
    """
    split_punc2 = functools.partial(split_punctuation, punctuations=r"。!?")
    concat_tail_no = functools.partial(concatenate_matching, former_matching_rule=r"^(?P<result>.+)(の)$", remove_former_matched=False)
    segmenter = make_pipeline(normalize, split_newline, concat_tail_no, split_punc2)

    sentence_list = []
    for text in candidate_users:
        sentence_list.append(list(segmenter(text)))

    candidate_users_segments = pd.Series(sentence_list, index=candidate_users.index, name='text')

    for i in range(len(candidate_users_segments)):
        candidate_users_segments[i] = [demoji.replace(string=seg, repl='') for seg in candidate_users_segments[i] if '。' != seg]

    return candidate_users_segments

def vectorize_candidate_segments(candidate_users_segments):
    """ユーザーシリーズに文単位のベクトルを追加したデータフレームを返す
    """
    # ベクトル表現を生成する
    BSV = sentence_vectorizer.BertSequenceVectorizer()
    vectors_list = [pd.Series(text).map(lambda x: BSV.vectorize(x)) for text in candidate_users_segments]
    sr_vectors = pd.Series(vectors_list, index=candidate_users_segments.index, name='vector')
    return pd.concat([candidate_users_segments, sr_vectors], axis=1)

# ターゲットツイートへの前処理

def segment_target_tweet(target_tweet):
    """ターゲットツイートを文単位でセパレートしたデータフレームを返す
    """
    split_punc2 = functools.partial(split_punctuation, punctuations=r"。!?")
    concat_tail_no = functools.partial(concatenate_matching, former_matching_rule=r"^(?P<result>.+)(の)$", remove_former_matched=False)
    segmenter = make_pipeline(normalize, split_newline, concat_tail_no, split_punc2)

    return pd.DataFrame(segmenter(target_tweet), columns=['text'])

def vectorize_target_segments(df_target_segments):
    """文単位のターゲットツイートデータフレームにベクトルを追加
    """
    BSV = sentence_vectorizer.BertSequenceVectorizer()
    df_target_segments['vector'] = df_target_segments['text'].map(lambda x: BSV.vectorize(x))
    return df_target_segments

def calculate_cosine_similarity(df_target_segments, df_candidate_users):
    """ターゲットツイートとターゲットユーザーツイートの類似度を計算
    """

    # コサイン類似度の高いユーザーを算出
    dic_degree = {}
    dic_index = {}

    for vec in df_candidate_users['vector']:

        join = df_target_segments['vector'].append(vec)
        for idx in range(len(df_target_segments)):
            # ターゲットツイートセグメントのインデックスを選択するマスク
            mask = np.ones(len(join), dtype=bool)
            mask[:len(df_target_segments)+1] = False
            mask[idx] = True
            # 類似度行列
            matrix = sentence_vectorizer.cos_sim_matrix(np.stack(join[mask]))
            #print(np.sort(matrix[0])[::-1])
            # ユーザーごとに最大の類似度とそのターゲットユーザーツイートのセグメントインデックスを取得
            degree = np.sort(matrix[0])[::-1][1]
            index = np.argsort(matrix[0])[::-1][1]

            dic_degree.setdefault(idx, []).append(degree)
            dic_index.setdefault(idx, []).append(index)

    return dic_degree, dic_index

def derived_result(client, df_target_segments, df_candidate_users, df_users, df_liked_tweets):
    """メール送信するユーザー名、ユーザーがいいねした関連度の高いツイート、関連スコア（0〜1）を返す
    """
    dic_degree, dic_index = calculate_cosine_similarity(df_target_segments, df_candidate_users)
    for degree_lst, index_lst in zip(dic_degree.values(), dic_index.values()):
        # 最大の関連度スコア
        client.degree.append(max(degree_lst))
        max_idx = degree_lst.index(max(degree_lst))
        target_user_id = df_candidate_users.iloc[max_idx].name
        # ターゲットユーザー名
        client.target_user.append(df_users['username'][df_users['id']==target_user_id].values)
        segment_index = index_lst[max_idx]
        # ツイート断片を抽出
        segment = df_candidate_users.loc[target_user_id,'text'][segment_index]
        # ツイート断片を含むツイート本文を抽出
        df_mask = df_liked_tweets[target_user_id].str.contains(segment)
        target_row = df_mask.first_valid_index()
        client.liked_tweet.append(df_liked_tweets.loc[target_row, target_user_id])


class Client():

    DIR = 'data/mail_body.txt'

    def __init__(self, client_data):

        self.client_data = client_data
        self.execution_time = 0
        self.target_user = []
        self.liked_tweet = []
        self.degree = []

    def extract_data(self):
        """クライアントの辞書から値をそれぞれ抽出
        """
        # 送信先を抽出
        self.mail_address = self.client_data['mail_address']
        # 宛名を抽出
        self.name = self.client_data['name']
        # キーワードを抽出
        self.keyword = self.client_data['keyword']
        # ツイッターIDを抽出
        self.target_tweet_id = self.client_data['twitter_id']
        # ツイッター本文を抽出
        df_tweets = pd.DataFrame(self.client_data['tweets'])
        self.target_tweet = df_tweets.iloc[:,1][df_tweets.iloc[:,2]==self.target_tweet_id].values[0]

    def send_email(self):
        """クライアント宛にメール送信
        """
        send_address = os.environ.get('MAIL_ADDRESS')
        password = os.environ.get('MAIL_PASSWORD')

        DIR = 'data/mail_body.txt'

        with open(DIR, encoding = "utf-8") as f:
            body_temp = f.read()

        subject = 'Twitter分析結果'
        from_address = send_address
        to_address = self.mail_address

        # SMTPサーバに接続
        smtpobj = smtplib.SMTP('smtp.gmail.com', 587)
        smtpobj.starttls()
        smtpobj.login(send_address, password)

        # メール作成
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = from_address
        msg['To'] = to_address
        msg['Date'] = formatdate()

        # メール本文
        # 一番大きい類似度のインデックス
        max_idx = self.degree.index(max(self.degree))

        body_text = body_temp.format(name=self.name,\
            keyword=self.keyword, target_tweet=self.target_tweet,\
            target_user=self.target_user[max_idx][0], liked_tweet=self.liked_tweet[max_idx],\
            degree=round(max(self.degree), 2), execution_time=round(self.execution_time, 2))
        body = MIMEText(body_text)
        msg.attach(body)

        # 作成したメールを送信
        smtpobj.send_message(msg)
        smtpobj.close()


def main(dir):
    """メイン
    """
    client_data_list = []

    # with open(dir, 'r+') as json_file:
    #     # 現在DBにあるクライアント情報を取得
    #     json_client_data = ndjson.load(json_file)
    #     print(f'DB情報：{json_client_data}')

    with open(dir, 'r+') as json_file:
        # DBの内容を空にする
        #json_file.truncate(0)
        for data in json_file:
            try:
            # 開始時間
                start_time = time.perf_counter()
                data = json.loads(data)
                print(data)
                # クライアントクラスの初期化
                client = Client(data)
                # クライアントデータ準備
                client.extract_data()

                df_target_segments = segment_target_tweet(client.target_tweet)
                df_target_segments = vectorize_target_segments(df_target_segments)

                df_users = get_liking_users(client.target_tweet_id)
                df_liked_tweets = get_liking_users_liked_tweets(df_users, client.target_tweet)
                candidate_users = select_tweets(client.keyword, df_liked_tweets)
                candidate_users_segments = segment_tweet(candidate_users)
                df_candidate_users = vectorize_candidate_segments(candidate_users_segments)
                derived_result(client, df_target_segments, df_candidate_users, df_users, df_liked_tweets)

                # 終了時間
                execution_time = time.perf_counter() - start_time
                client.execution_time = execution_time

                client.send_email()
            except Exception as e:
                print(e)

            print('送信成功しました')


if __name__ == "__main__":

    DIR = 'db_tweets.ndjson'
    main(DIR)