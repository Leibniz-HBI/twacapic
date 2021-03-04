import json
import os
import shutil
from glob import glob

import pytest
import yaml
from twacapic import __version__
from twacapic.auth import read_credentials, save_credentials
from twacapic.collect import UserGroup


def test_version():
    assert __version__ == '0.1.4.0'


def test_can_create_credential_yaml(tmp_path):

    tmp_yaml_path = tmp_path.joinpath('twitter_keys.yaml')

    save_credentials(tmp_yaml_path, '<CONSUMER_KEY>', '<CONSUMER_SECRET>')

    with open(tmp_yaml_path, 'r') as created_yaml:
        with open('tests/mock_files/mock_credentials.yaml') as test_yaml:
            expected = yaml.safe_load(test_yaml)
            actual = yaml.safe_load(created_yaml)

            assert expected == actual


def test_can_read_credentials():

    credentials = read_credentials('tests/mock_files/mock_credentials.yaml')

    assert credentials['consumer_key'] == '<CONSUMER_KEY>'
    assert credentials['consumer_secret'] == '<CONSUMER_SECRET>'


@pytest.fixture
def user_group():

    user_group = UserGroup('tests/mock_files/users.csv', name='test_users')

    yield user_group

    shutil.rmtree('results/test_users')


def test_user_group_creates_directories(user_group):

    with open('tests/mock_files/users.csv') as file:
        for line in file:
            path = f'results/test_users/{line.strip()}'
            assert os.path.isdir(path), f"Could not find directory for user in {path}"


@pytest.fixture(scope='module')
def user_group_with_tweets():

    user_group = UserGroup('tests/mock_files/users.csv', name='test_users_with_tweets')

    user_group.collect()

    yield user_group

    shutil.rmtree(user_group.path)


def test_can_retrieve_tweets_from_user_timeline(user_group_with_tweets):

    folders = glob(f'{user_group_with_tweets.path}/*')

    for folder in folders:
        files = os.listdir(folder)

        assert len(files) >= 1, f'No tweets in user folder {folder}'

        with open(f'{folder}/{files[0]}', 'r') as file:
            tweets = json.load(file)
            assert len(tweets['data']) > 90, 'not retrieving maximum of tweets per request'


@pytest.fixture
def group_without_latest_tweet(user_group_with_tweets):

    group_path = 'results/group_without_latest_tweet'
    shutil.copytree(user_group_with_tweets.path, group_path)

    group = UserGroup(name='group_without_latest_tweet')

    for user_id in group.user_ids:
        latest_file = glob(f'{group.path}/{user_id}/*')[0]

        with open(latest_file, 'r+') as f:
            tweets = json.load(f)
            tweets['data'].pop(0)
            json.dump(tweets, f)

    yield group

    shutil.rmtree(group_path)


def test_can_retrieve_only_new_tweets_from_user(group_without_latest_tweet):

    group_without_latest_tweet.collect()

    for user_id in group_without_latest_tweet.user_ids:
        user_folder = f'{group_without_latest_tweet.path}/{user_id}'
        file_list = os.listdir(user_folder)

        assert len(file_list) == 2, "no new tweets collected"

        file_list.sort(reverse=True)
        print(f'\nfiles in user_folder {user_id}: ', file_list)
        latest_file = file_list[0]
        file_before = file_list[1]
        tweet_before = file_before.split('_')[0]
        print('latest file: ', latest_file)
        print('latest_tweet_before: ', tweet_before)

        with open(f'{user_folder}/{latest_file}', 'r') as f:
            tweets = json.load(f)['data']
            assert len(tweets) < 10, 'too many tweets collected'
            assert tweets['meta']['oldest_id'] > tweet_before
