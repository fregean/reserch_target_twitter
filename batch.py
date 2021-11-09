import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate
from os.path import join, dirname
import time

msg = MIMEMultipart()

import pandas as pd
import numpy as np
import ndjson
from dotenv import load_dotenv
import sentence_vectorizer
import functools
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

def read_tweet(dir):
    json.load()










def send_email():
    sendAddress = os.environ.get('MAIL_ADDRESS')
    password = os.environ.get('MAIL_PASSWORD')

    subject = 'ごきげんいかがですか'
    bodyText = 'いつもおつかれさまです'
    fromAddress = sendAddress
    toAddress = 'yuki_fujisawa@wywy.jp'

    # SMTPサーバに接続
    smtpobj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpobj.starttls()
    smtpobj.login(sendAddress, password)

    # メール作成
    msg = MIMEText(bodyText)
    msg['Subject'] = subject
    msg['From'] = fromAddress
    msg['To'] = toAddress
    msg['Date'] = formatdate()

    # 作成したメールを送信
    smtpobj.send_message(msg)
    smtpobj.close()

if __name__ == "__main__":
    send_email()