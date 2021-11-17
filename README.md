# Finding Twitter Targeting_Users Application

Twitterのターゲットユーザーを提案してくれるアプリです。

## 何ができる？

Twitterで自社製品を広告したいとき、どんなユーザーにツイートを届ければよいでしょうか？
あるキーワードを含むツイートに「いいね」したユーザーが他によく似たツイートに「いいね」していれば、そのユーザーは、そのキーワードに強い関心を持っていると仮定してよいのではないでしょうか。
そこで以下のようなレポートを返すアプリを作ってみました。

```　
=======================================
〇〇様が入力されたキーワードと、選択されたツイートはこちらです。

■ キーワード：udemy

■ ツイート：
「udemy今日だけセールやってる！JSの基礎から学び直したい！ #駆け出しエンジニアと繋がりたい」

---------------------------------------

上記ツイートに「いいね」したターゲットユーザー候補を表示します。

■ ユーザー：@hogehoge

■ 上記ユーザーがいいねした類似度の高いツイート：
「GAS入門講座終了！ひと月かかったけどようやく仕事で使えそう。#udemy #JavaScript」

■ 類似度スコア（0〜1）：0.87
=======================================
処理時間は38.34秒でした。
```

いい感じのターゲットユーザーが見つかれば、あとはフォローするなり、そのユーザーの属性から類似する層に向けてツイッター広告を打つなり、ツイートの文面を研究するなり、アクションが取れそうです。
類似したユーザーは「興味関心、行動、エンゲージメントが既存の顧客と似ている」ため、広告キャンペーンのターゲットとして有効と言われています。
あなたが上司にTwitter広告のターゲティングを頼まれたら、ぜひ使ってみてください。


## アプリの設計

アプリの処理は大きく分けて二つのパートに分かれます。
一つはflaskによるwebアプリケーションの処理で、もう一つは、pythonによるバッチ処理です。バッチ処理において、機械学習モデル（BertJapaneseTokenizer）を利用します。

以下の文章中の①〜⑰は、flaskのディレクトリごとの処理を表示しています。⑱〜㉛はpythonのバッチ処理を示しています。
※文中の丸数字は画像中の丸数字に対応しています。

- ルートディレクトリ（トップページ）
    - ①トップページ表示
    - ②クライアントが「Start App」ボタンが押す
        - ③Twitterに開発者のapi_key、api_key_secretを送る
        - ④Twitterからリクエストトークンを受け取る
        - ⑤Twitter連携アプリ認証URL表示

-  request_tokenディレクトリ（連携アプリ認証ページ）
    -  ⑥クライアントがログイン入力&「Authorize App」ボタンが押す
        - ⑦Twitterにリクエストトークンを渡す
        - ⑧Twitterからaccess_token、認証コード（verifier）を受け取る

- callbackディレクトリ
    - access_token、認証コードでOAuth認証を行う

![アプリ設計図 (13)](https://user-images.githubusercontent.com/31781305/141421466-d071d184-8027-4037-8bb9-19b0979841ba.png)

- get_keywordディレクトリ（キーワード入力ページ）
    - ⑨キーワード入力ページ表示

- post_tweetsディレクトリ（検索結果ページ）
    - ⑩クライアントがキーワード、アドレス、名前を入力して「Send」ボタンを押す
        - キーワード、アドレス、名前をsessionに保存
    - ⑪Twitterにキーワードでツイート検索をかける
    - ⑫ツイートデータを受け取る
    - ⑬データ整形
    - ⑭検索結果ページ表示

![アプリ設計図 (9)](https://user-images.githubusercontent.com/31781305/141421402-25f32b2a-9c8b-44b3-abc3-3018503b9f5c.png)

- display_informationディレクトリ
    - ⑮クライアントがツイートを選択する
        - ツイートIDを保存
    - ⑯ファイルにクライアントの入力情報とツイート情報を書込み（※Twitterログイン情報は含みません）
    - ⑰お知らせページ表示

![アプリ設計図 (10)](https://user-images.githubusercontent.com/31781305/141421405-ec3a8cf1-e5ff-4f40-9292-fc90374da050.png)

flaskの処理はここまでで終了です。ここからはpythonのバッチ処理になります。

- バッチ処理
    - ⑱データ読取り（※スケジューラ設定がある場合は定期実行）
    - ⑲読取り後にファイルをクリア
    - ⑳クライアントごとにオブジェクトを作成
        - データ保存
    - ㉑TwitterにツイートIDで検索をかける
    - ㉒ツイートに「いいねしたユーザー」の情報を取得
    - ㉓TwitterにユーザーIDで検索をかける
    - ㉔ユーザーごとに「いいねしたツイート」100件を取得

![アプリ設計図 (11)](https://user-images.githubusercontent.com/31781305/141421406-81517453-9fe5-4b76-9c4e-4aae019ea38e.png)

- ㉕ツイートを選定
        - キーワードを含むもの
    - ㉖ツイートを文単位でセパレート
    - ㉗モデルに文を渡す
        - transformersのBertJapaneseTokenizerを使用
    - ㉘ベクトル表現を取得
    - ㉙ベクトル間の類似度を計算
        - クライアントの選んだツイートとそれに関連するツイート間の類似度
    - ㉚計算結果をGmailで送信
    - ㉛クライアントにメールが届く

![アプリ設計図 (12)](https://user-images.githubusercontent.com/31781305/141421408-693d7ebe-5e6e-45e7-b356-28c1a113bbe0.png)

## 使用方法

### 準備

- Twitter開発者アカウントの申請
   - Twitterにログインした状態で以下のサイトのステップ１に従って、開発者アカウントの申請を行います。
      - [新しいTwitterAPIv2への最初のリクエストを行うためのステップバイステップガイド](https://developer.twitter.com/en/docs/tutorials/step-by-step-guide-to-making-your-first-request-to-the-twitter-api-v2)
      - 日本語の参考ブログ：[2021年度版 Twitter API利用申請の例文からAPIキーの取得まで詳しく解説](https://www.itti.jp/web-direction/how-to-apply-for-twitter-api/)

- Twitterのキーおよびトークンの発行
   - Twitter開発者アカウント申請が承認されたら、以下のサイトのステップ2：プロジェクトを作成し、アプリを接続します。
      - [新しいTwitterAPIv2への最初のリクエストを行うためのステップバイステップガイド](https://developer.twitter.com/en/docs/tutorials/step-by-step-guide-to-making-your-first-request-to-the-twitter-api-v2)
   - アプリが作成できたら、「API Key」「API Secret」「Bearer Token」の3つを発行します。
   - TwitterのキーとトークンはOAuth認証（アクセストークンの要求と応答）という手続きで必要になります。
      
- GmailアドレスとGmailのアプリパスワードの用意
   - 以下のサイトからアプリパスワードを発行する
      - [アプリ パスワードを作成、使用する](https://support.google.com/mail/answer/185833?hl=ja)
   - このGmailアドレスは、アプリの処理結果の送信用アドレスになります。

- .envファイルの準備
   - 以下の形式を記述したファイルを.envと名付けて作成します。
   - 上で準備した「API Key」「API Secret」「Bearer Token」「Gmailアドレス」「アプリパスワード」を以下の形式中の「""」内に貼り付ければファイルの完成です。
   - .envファイルは、app.pyと同じディレクトリに配置します。

```
API_KEY = ""
API_SECRET = ""
BEARER_TOKEN = ""
MAIL_ADDRESS = ""
MAIL_PASSWORD = ""
```

- Twitter Callback URLの用意
   - 以下の開発者ポータルのダッシュボードにアクセスし、上で作成したアプリ名を左のメニューから見つけて、Setting（歯車マーク）を開き、「3-legged OAuth」を有効にします。
   - [Developer Portal Dashboard](https://developer.twitter.com/en/portal/dashboard)
   - 以下の形式で「Callback URLs」を記述します。
      - http://ローカルIPアドレス/callback
      - `python app.py`を実行して、flaskサーバーを起動したときに表示されるローカルIPアドレスを使ってください。
      - (例) 環境によって異なりますが、以下のようなローカルIPアドレスが表示されます。
         - `Running on http://192.168.10.101:8000/ (Press CTRL+C to quit)`
         - 上の場合は、「Callback URLs」を`http://192.168.10.101:8000/callback`とします。
   - 「Callback URLs」を書いたら、他は書かずにsaveします。  

### 実行

- リポジトリをクローンします。

```
git clone https://github.com/fregean/reserch_target_twitter.git
```

- 移動して、app.pyを実行します。
```
cd reserch_target_twitter
python app.py
```
- コマンドラインに表示された `Running on` 以下のIPアドレスにアクセスすると、ブラウザに以下のページが表示されるので、ページの指示に従ってボタン押&入力を進めてください。
 

<img width="716" alt="スクリーンショット 2021-11-17 18 05 00" src="https://user-images.githubusercontent.com/31781305/142170246-be4db564-10d0-4b44-91e7-b71411091332.png">
<img width="500" alt="スクリーンショット 2021-11-12 14 40 51" src="https://user-images.githubusercontent.com/31781305/141416308-44ed6808-6ca2-4de8-9627-98610d8ddf37.png">
<img width="500" alt="スクリーンショット 2021-11-12 15 24 55" src="https://user-images.githubusercontent.com/31781305/141420381-1617f889-1695-42d6-8ca7-020db00280ed.png">
<img width="500" alt="スクリーンショット 2021-11-12 15 25 27" src="https://user-images.githubusercontent.com/31781305/141420431-020f6865-da0a-4c3a-87d3-1e9f396c1bc7.png">
<img width="500" alt="スクリーンショット 2021-11-12 15 25 55" src="https://user-images.githubusercontent.com/31781305/141420475-59bec8ee-8fcb-4cce-b415-311c9fdf9ad3.png">

- 最後の画像のページが表示されたら、batch.pyを実行します。

```
python batch.py
```
※「15分ほどで結果をメールに送信します」と表示されているのは、元々スケジューラで10分ごとにバッチ処理をする設計だったためです。
batch.pyを実行すると、アプリを利用した一人のクライアントにつき1〜2分でメールのレポートが届きます。
batch.pyを実行するまでは、アプリを利用したクライアントの入力履歴は保持され、実行されると入力履歴が削除されます。（クライアントのTwitterアカウント情報は保持しません）

- 1〜2分すると、メールが届きます。



