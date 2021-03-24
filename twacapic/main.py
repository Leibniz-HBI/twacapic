import argparse
import os
import sys

from loguru import logger
from twacapic.auth import save_credentials
from twacapic.collect import UserGroup

logger.remove()

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
    parser.add_argument(
        '-l', '--log_level',
        help='Level of output detail (DEBUG, INFO, WARNING, ERROR). Default: INFO',
        default='INFO'
    )
    parser.add_argument(
        '-lf', '--log_file',
        help='Path to logfile. Defaults to standard output.',
    )
    args = parser.parse_args()

    if args.log_file is None:
        logger.add(sys.stdout, level=args.log_level)
    else:
        logger.add(args.log_file, level=args.log_level, rotation="64 MB")
        logger.add(sys.stderr, level='ERROR')
    logger.add('errors.log', level='ERROR')
    logger.add('warnings.log', level='WARNING')

    print("Hello friend …")

    if not os.path.isfile('twitter_keys.yaml'):
        consumer_key = input("Please enter your API key:")
        consumer_secret = input("Please enter your API secret:")

        save_credentials('twitter_keys.yaml', consumer_key, consumer_secret)

    user_group = UserGroup(path=args.userlist, name=args.groupname, config=args.group_config)

    logger.info(f"Starting collection of {args.groupname}.")

    user_group.collect()

    logger.info(f"Finished collection of {args.groupname}.")

    print("Exciting time in the world right now … exciting time … ")


if __name__ == '__main__':

    run()
