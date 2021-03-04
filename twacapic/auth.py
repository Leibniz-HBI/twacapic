import yaml
from TwitterAPI import TwitterAPI


def save_credentials(path, consumer_key=None, consumer_secret=None, bearer_token=None):

    content = {
        'search_tweets_v2':
            {
                'endpoint': 'https://api.twitter.com/2/tweets/search/all',
                'consumer_key': consumer_key,
                'consumer_secret': consumer_secret,
                'bearer_token': bearer_token
            }
    }

    with open(path, 'w') as file:
        yaml.dump(content, file)


def read_credentials(path):
    with open(path, 'r') as file:

        content = yaml.safe_load(file)

        return content['search_tweets_v2']


def get_api(path):

    credentials = read_credentials(path)
    consumer_key = credentials['consumer_key']
    consumer_secret = credentials['consumer_secret']

    return TwitterAPI(consumer_key, consumer_secret,
                      auth_type='oAuth2', api_version='2')
