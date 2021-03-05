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


def test_user_in_group_has_meta_file(user_group_with_tweets):

    folders = glob(f'{user_group_with_tweets.path}/*')

    for folder in folders:

        meta_file_path = f'{folder}/meta.yaml'

        with open(meta_file_path, 'r') as metafile:
            meta_data = yaml.safe_load(metafile)

        files = glob(f'{folder}/*.json')
        with open(files[0], 'r') as tweetfile:
            tweet_data = json.load(tweetfile)

        assert tweet_data['meta']['newest_id'] == meta_data['newest_id']
        assert tweet_data['meta']['oldest_id'] == meta_data['oldest_id']
