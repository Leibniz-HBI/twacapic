import os

from TwitterAPI import TwitterAPI, TwitterOAuth


def run():
    print("Hello friend …")

    if not os.path.isfile('twacapic_credentials.txt'):
        print("Please enter your API key:")
        consumer_key = input()
        print("Please enter your API secret:")
        consumer_secret = input()

        with open('twacapic_credentials.txt', 'a') as keyfile:
            keyfile.writelines([
                f'consumer_key = {consumer_key}\n',
                f'consumer_secret = {consumer_secret}\n',
                'access_token_key = NOT_NECESSARY\n',
                'access_token_secret = NOT_NECESSARY\n'
            ])

    keys = TwitterOAuth.read_file('twacapic_credentials.txt')

    api = TwitterAPI(keys.consumer_key, keys.consumer_secret, auth_type='oAuth2', api_version='2')

    r = api.request('tweets/search/all', {'query': 'from:flxvctr'})

    print(r.text)


if __name__ == '__main__':
    run()
