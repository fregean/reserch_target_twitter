import requests
import os
import json
from os.path import join, dirname

from dotenv import load_dotenv

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

bearer_token = os.environ.get('BEARER_TOKEN')
PATH = "/Users/yottan/Desktop/Aidemy/reserch_target_twitter/data/liking_users.json"

def create_url(target_ids):
    # User fields are adjustable, options include:
    # created_at, description, entities, id, location, name,
    # pinned_tweet_id, profile_image_url, protected,
    # public_metrics, url, username, verified, and withheld
    user_fields = "user.fields=created_at,description,location,public_metrics"
    # You can replace the ID given with the Tweet ID you wish to like.
    # You can find an ID by using the Tweet lookup endpoint
    id = target_ids
    # You can adjust ids to include a single Tweets.
    # Or you can add to up to 100 comma-separated IDs
    url = "https://api.twitter.com/2/tweets/{}/liking_users".format(id)
    return url, user_fields


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2LikingUsersPython"
    return r


def connect_to_endpoint(url, user_fields):
    response = requests.request("GET", url, auth=bearer_oauth, params=user_fields)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()


def get_users(target_id):
    url, tweet_fields = create_url(target_id)
    json_response = connect_to_endpoint(url, tweet_fields)
    with open(PATH, 'w') as file:
        json.dump(json_response, file)
    #print(json.dumps(json_response, indent=4, sort_keys=True))
    return json_response