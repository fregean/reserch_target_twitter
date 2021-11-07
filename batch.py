import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
import config

sendAddress = config.MAIL_ADDRESS
password = config.MAIL_PASSWORD

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