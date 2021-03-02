import yaml


def save_credentials(path, consumer_key, consumer_secret):

    content = {
        'search_tweets_v2':
            {
                'endpoint': 'https://api.twitter.com/2/tweets/search/all',
                'consumer_key': f'{consumer_key}',
                'consumer_secret': f'{consumer_secret}',
            }
    }

    with open(path, 'w') as file:
        yaml.dump(content, file)


def read_credentials(path):
    with open(path, 'r') as file:

        content = yaml.safe_load(file)

        return content['search_tweets_v2']
