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

def return_tweets(tweets):
    """いいねの多いツイート10件を返す
    """
    df_tweets = pd.json_normalize(tweets['data'])
    df_tweets = df_tweets.sort_values(['public_metrics.like_count'], ascending=False)

    return df_tweets[['public_metrics.like_count', 'text', 'id']][:10].reset_index(drop=True).\
rename(columns={'public_metrics.like_count': 'いいね数', 'text': 'ツイート本文', 'id': 'ID'})


