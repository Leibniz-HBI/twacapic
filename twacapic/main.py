import os

from twacapic.auth import read_credentials, save_credentials
from TwitterAPI import TwitterAPI


def run():
    print("Hello friend …")

    if not os.path.isfile('twitter_keys.yaml'):
        print("Please enter your API key:")
        consumer_key = input()
        print("Please enter your API secret:")
        consumer_secret = input()

        save_credentials('twitter_keys.yaml', consumer_key, consumer_secret)

    keys = read_credentials('twitter_keys.yaml')

    api = TwitterAPI(keys['consumer_key'], keys['consumer_secret'], auth_type='oAuth2', api_version='2')

    r = api.request('tweets/search/all', {'query': 'from:flxvctr'})

    print(r.text)


if __name__ == '__main__':
    run()
