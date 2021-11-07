import json
import sys

sys.path.append('..')
import liked_tweets
import pandas as pd
import numpy as np
import sentence_vectorizer
import functools
import demoji
from ja_sentence_segmenter.common.pipeline import make_pipeline
from ja_sentence_segmenter.concatenate.simple_concatenator import concatenate_matching
from ja_sentence_segmenter.normalize.neologd_normalizer import normalize
from ja_sentence_segmenter.split.simple_splitter import split_newline, split_punctuation

pd.set_option('display.max_columns', 50)


# 特定のキーワードを含むツイートを100件取得
with open('search_tweet.json', 'r', encoding='utf-8') as json_file:
    tweets = json.load(json_file)


def return_tweets(tweets):
    """いいねの多いツイート10件を返す
    """
    df_tweets = pd.json_normalize(tweets['data'])
    df_tweets = df_tweets.sort_values(['public_metrics.like_count'], ascending=False)

    return df_tweets[['public_metrics.like_count', 'text']][:10].reset_index(drop=True)

# GET
df_tweets = get_search_tweet(tweets)


# 関心のあるツイートを選択し、ターゲットツイートとして保存する
target_tweet = df_tweets.iloc[2]



# 特定のツイートにいいねしたユーザー取得
with open('liking_users.json', 'r', encoding='utf-8') as json_file:
    users = json.load(json_file)

# 入れ子の辞書をデータフレームに変換
df_users = pd.json_normalize(users['data'])


# いいねしたユーザーのツイートを100件ずつ取得
with open('liked_tweets.json', 'r', encoding='utf-8') as json_file:
    dic_liked_tweets = json.load(json_file)

df_liked_tweets = pd.concat({k: pd.DataFrame(v['data']) for k, v in dic_liked_tweets.items()},axis=0).unstack(0).swaplevel(1,0, axis=1).sort_index(axis=1)


# ターゲットツイートの前処理
target_tweet['text']

split_punc2 = functools.partial(split_punctuation, punctuations=r"。!?")
concat_tail_no = functools.partial(concatenate_matching, former_matching_rule=r"^(?P<result>.+)(の)$", remove_former_matched=False)
segmenter = make_pipeline(normalize, split_newline, concat_tail_no, split_punc2)

# 文単位に分割する
target_texts = pd.DataFrame(segmenter(target_tweet['text']), columns=['text'])
target_texts

# ベクトル表現を生成する
BSV = sentence_vectorizer.BertSequenceVectorizer()
target_texts['vector'] = target_texts['text'].map(lambda x: BSV.vectorize(x))
target_texts['vector']


# いいねしたツイート文の前処理
user_names = df_liked_tweets.columns.get_level_values(0).unique()
tweets_text_list = []

for user in user_names:
    user_texts = df_liked_tweets[user]['text'].copy()
    # いいねしたツイート文にターゲットツイート文が含まれていたらNANに置換する
    user_texts.replace(target_tweet['text'], np.nan, inplace=True)
    tweets_text_list.append(user_texts)

df_tweets_text = pd.DataFrame(tweets_text_list, index=user_names)

# いいねしたテキストのデータフレームの転置を用意する
df_tweets_text_t =  df_tweets_text.T


# ターゲットキーワードを含むツイート文以外はNANに置換する
keyword = 'Kaggle'
for col in df_tweets_text_t.columns:
    flag = df_tweets_text_t[col].str.contains(keyword, na=False)
    df_tweets_text_t.loc[~flag, col] = np.nan

# NAN以外の値を持つユーザーIDを特定する（POSTする候補）
exist_flag = df_tweets_text_t.count() != 0
user_name = df_tweets_text[exist_flag].index


# POSTするユーザー候補ごとに関連ツイート文を全て結合
candidate_users = df_tweets_text_t[user_name].T
# 後で文を区切る区切りのためツイート文の文末に'。'を追加
candidate_users += '。'
# ツイート文を結合
candidate_users['all'] = candidate_users.iloc[:,0].str.cat([candidate_users.iloc[:,col] for col in candidate_users.columns[1:]], na_rep='')

split_punc2 = functools.partial(split_punctuation, punctuations=r"。!?")
concat_tail_no = functools.partial(concatenate_matching, former_matching_rule=r"^(?P<result>.+)(の)$", remove_former_matched=False)
segmenter = make_pipeline(normalize, split_newline, concat_tail_no, split_punc2)

# 結合したツイート文を文単位で分割する
df_list = []
for idx, text in enumerate(candidate_users['all']):
    df_list.append(list(segmenter(text)))

candidate_users['text'] = df_list

# '。'だけの文字と絵文字を削除
for i in range(len(candidate_users)):
    candidate_users['text'][i] = [demoji.replace(string=seg, repl='') for seg in candidate_users['segments'][i] if '。' != seg]

# ベクトル表現を生成する
BSV = sentence_vectorizer.BertSequenceVectorizer()
vectors_list = [pd.Series(text).map(lambda x: BSV.vectorize(x)) for text in candidate_users['text']]


sr_vectors = pd.Series(vectors_list, index=candidate_users['text'].index, name='vector')
candidate_users_features = pd.concat([candidate_users['text'], sr_vectors], axis=1)


# 識別しやすいようにターゲットツイートのインデックスにプレフィックスをつける

target_texts.rename(index=lambda s: 'target_' + str(s), inplace=True)


# コサイン類似度の高いユーザーを算出
dic_degree = {}
dic_index = {}

for vec in candidate_users_features['vector']:
    join = target_texts['vector'].append(vec)
    for idx in range(len(target_texts)):
        mask = np.ones(len(join), dtype=bool)
        mask[idx] = False
        matrix = sentence_vectorizer.cos_sim_matrix(np.stack( join[mask]))
        print(np.sort(matrix[0])[::-1])
        degree = np.sort(matrix[0])[::-1][1]
        index = np.argsort(matrix[0])[::-1][1]
        dic_degree.setdefault(idx, []).append(degree)
        dic_index.setdefault(idx, []).append(index)

