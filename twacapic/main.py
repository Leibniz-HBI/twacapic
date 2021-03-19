import argparse
import os

from twacapic.auth import save_credentials
from twacapic.collect import UserGroup


def run():

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--userlist',
                        help='path to list of user IDs, one per line. \
                        Required for first run only. Can be used to add users to a group')
    parser.add_argument('-g', '--groupname',
                        help='name of the group to collect.\
                        Results will be saved in folder `results/GROUPNAME/`.\
                        Can be used to poll for new tweets of a group.\
                        Default: "users"',
                        default='users')
    parser.add_argument(
        '-c', '--group_config',
        help='path to a custom group config file to define tweet data to be retrieved, \
        e.g. retweets, mentioned users, attachments. \
        A template named `group_config.yaml` can be found in any already created group folder.'
    )
    args = parser.parse_args()

    print("Hello friend …")

    if not os.path.isfile('twitter_keys.yaml'):
        print("Please enter your API key:")
        consumer_key = input()
        print("Please enter your API secret:")
        consumer_secret = input()

        save_credentials('twitter_keys.yaml', consumer_key, consumer_secret)

    try:
        path = args.userlist
    except IndexError:
        path = None

    user_group = UserGroup(path=path, name=args.groupname)
    user_group.collect()

    print("Finished")


if __name__ == '__main__':

    run()
