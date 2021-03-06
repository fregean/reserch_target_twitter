import requests
import os
from os.path import join, dirname
import json
from time import sleep

from dotenv import load_dotenv

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

bearer_token = os.environ.get('BEARER_TOKEN')
#PATH = "/Users/yottan/Desktop/Aidemy/reserch_target_twitter/data/liked_tweets.json"



def create_url(user):
    # Tweet fields are adjustable.
    # Options include:
    # attachments, author_id, context_annotations,
    # conversation_id, created_at, entities, geo, id,
    # in_reply_to_user_id, lang, non_public_metrics, organic_metrics,
    # possibly_sensitive, promoted_metrics, public_metrics, referenced_tweets,
    # source, text, and withheld
    tweet_fields = "tweet.fields=lang,author_id"
    # Be sure to replace your-user-id with your own user ID or one of an authenticating user
    # You can find a user ID by using the user lookup endpoint
    id = user
    # You can adjust ids to include a single Tweets.
    # Or you can add to up to 100 comma-separated IDs
    url = "https://api.twitter.com/2/users/{}/liked_tweets".format(id)
    return url, tweet_fields


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2LikedTweetsPython"
    return r


def connect_to_endpoint(url, tweet_fields):
    response = requests.request(
        "GET", url, auth=bearer_oauth, params=tweet_fields)
    #print(response.status_code)
    if response.status_code != 200:
        print('リクエスト回数制限のため15min待機')
        sleep(15*60)
        # raise Exception(
        #     "Request returned an error: {} {}".format(
        #         response.status_code, response.text
        #     )
        # )
    return response.json()


def get_liked_tweets(user_series):
    tweet_dic = {}
    for user in user_series:
        url, tweet_fields = create_url(user)
        json_response = connect_to_endpoint(url, tweet_fields)
        tweet_dic[user] = json_response
    return tweet_dic


    # with open(PATH, 'w') as file:
    #     json.dump(tweet_dic, file)

    #print(json.dumps(json_response, indent=4, sort_keys=True))



# if __name__ == "__main__":
#     main()