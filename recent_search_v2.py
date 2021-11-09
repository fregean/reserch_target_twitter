import requests
import os
import json
from os.path import join, dirname

from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv

search_url = "https://api.twitter.com/2/tweets/search/recent"
PATH = "/Users/yottan/Desktop/Aidemy/reserch_target_twitter/data/search_tweet.json"

# Optional params: start_time,end_time,since_id,until_id,max_results,next_token,
# expansions,tweet.fields,media.fields,poll.fields,place.fields,user.fields

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

def connect_to_endpoint(url, params, oauth):
    response = oauth.get(url, params=params)
    #response = requests.get(url, auth=bearer_oauth, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def search_tweet(keyword, oauth):
    print(f'キーワード：{keyword}')
    query_params = {'query': f'({keyword} -is:retweet lang:ja)','expansions': 'author_id', 'tweet.fields': 'public_metrics','max_results':100}
    json_response = connect_to_endpoint(search_url, query_params, oauth)
    #jsonfile = json.dumps(json_response, sort_keys=True, ensure_ascii=False)
    with open(PATH, 'w') as file:
        json.dump(json_response, file)
    return json_response

if __name__ == "__main__":
    search_tweet()