import os

from TwitterAPI import TwitterAPI


def run():
    print("Hello friend …")

    if not os.path.isfile('twacapic_credentials.py'):
        print("Please enter your API key:")
        consumer_key = input()
        print("Please enter your API secret:")
        consumer_secret = input()

        with open('twacapic_credentials.py', 'a') as keyfile:
            keyfile.writelines([
                f'consumer_key = "{consumer_key}"\n',
                f'consumer_secret = "{consumer_secret}"\n'
            ])

    import twacapic.twacapic_credentials as keys

    api = TwitterAPI(keys.consumer_key, keys.consumer_secret, auth_type='oAuth2', api_version='2')

    r = api.request('tweets/search/all', {'query': 'from:flxvctr'})

    print(r.text)


if __name__ == '__main__':
    run()
