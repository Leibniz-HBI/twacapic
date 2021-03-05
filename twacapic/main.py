import os
from sys import argv

from twacapic.auth import save_credentials
from twacapic.collect import UserGroup


def run():
    print("Hello friend …")

    if not os.path.isfile('twitter_keys.yaml'):
        print("Please enter your API key:")
        consumer_key = input()
        print("Please enter your API secret:")
        consumer_secret = input()

        save_credentials('twitter_keys.yaml', consumer_key, consumer_secret)

    try:
        path = argv[2]
    except IndexError:
        path = None

    user_group = UserGroup(path=path, name=argv[1])
    user_group.collect()

    print("Finished")


if __name__ == '__main__':
    run()
