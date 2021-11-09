import smtplib
import os
from email.mime.text import MIMEText
from email.utils import formatdate
from os.path import join, dirname

from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

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