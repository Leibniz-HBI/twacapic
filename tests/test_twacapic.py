import json
import os
import shutil
from glob import glob
from unittest.mock import Mock, patch

import pytest
import twacapic
import yaml
from requests.exceptions import ConnectionError
from twacapic import __version__
from twacapic.auth import read_credentials, save_credentials
from twacapic.collect import UserGroup
from TwitterAPI import TwitterResponse
from TwitterAPI.TwitterError import TwitterConnectionError


def test_version():
    assert __version__ == '0.1.4.5'


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
        files = glob(f'{folder}/*.json')

        assert len(files) >= 1, f'No tweets in user folder {folder}'

        with open(files[0], 'r') as file:
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


@pytest.fixture
def user_group_with_old_meta_file(user_group_with_tweets):

    shutil.copytree(user_group_with_tweets.path, 'results/users_with_meta')

    user_group = UserGroup(name='users_with_meta')

    for user_id in user_group.user_ids:
        meta_file_path = f'{user_group.path}/{user_id}/meta.yaml'

        with open(meta_file_path, 'r') as f:
            metadata = yaml.safe_load(f)

        metadata['newest_id'] = str(int(metadata['newest_id']) - 1)

        with open(meta_file_path, 'w') as f:
            yaml.dump(metadata, f)

    yield user_group

    shutil.rmtree(user_group.path)


def test_collect_only_new_tweets(user_group_with_old_meta_file):

    user_group_with_old_meta_file.collect()

    for user_id in user_group_with_old_meta_file.user_ids:
        files = glob(f'{user_group_with_old_meta_file.path}/{user_id}/*.json')

        assert len(files) == 2

        files.sort(reverse=True)

        with open(files[0], 'r') as f:
            oldest_collected_id = json.load(f)['meta']['oldest_id']

        with open(f'{user_group_with_old_meta_file.path}/{user_id}/meta.yaml') as f:
            oldest_meta_id = yaml.safe_load(f)['oldest_id']

        assert oldest_collected_id > oldest_meta_id


def test_no_new_tweets(user_group_with_tweets):

    user_group_with_tweets.collect()

    for user_id in user_group_with_tweets.user_ids:

        assert len(user_group_with_tweets.tweet_files[user_id]) == 1


@pytest.fixture
def user_group_with_very_old_tweets(user_group_with_tweets, user_group):

    for user_id in user_group_with_tweets.user_ids:
        metadata = user_group_with_tweets.meta[user_id]
        metadata['newest_id'] = metadata['oldest_id']

        with open(f'{user_group.path}/{user_id}/meta.yaml', 'w') as f:
            yaml.dump(metadata, f)

    yield user_group


def test_pagination_of_old_tweets(user_group_with_very_old_tweets):

    meta_old = user_group_with_very_old_tweets.meta

    user_group_with_very_old_tweets.collect(max_results_per_call=50)

    for user_id in user_group_with_very_old_tweets.user_ids:

        meta_new = user_group_with_very_old_tweets.meta
        tweet_files = user_group_with_very_old_tweets.tweet_files[user_id]
        tweet_files.sort(reverse=True)
        latest_tweet_id = tweet_files[0].split('/')[-1].split('_')[0]

        assert len(tweet_files) == 2
        assert meta_new[user_id]['newest_id'] == latest_tweet_id
        assert meta_new[user_id]['oldest_id'] == meta_old[user_id]['oldest_id']


@pytest.fixture(scope='module')
def successful_response_mock(user_group_with_tweets):
    tweet_file = glob(f'{user_group_with_tweets.path}/*/*.json')[0]

    mock_response = Mock()
    options = Mock()
    mock_response.status_code = 200
    with open(tweet_file, 'r') as tweets:
        mock_response.text = tweets.read()

    yield TwitterResponse(mock_response, options)


@pytest.fixture(scope='module')
def failed_response_mock(user_group_with_tweets):

    mock_response = Mock()
    options = Mock()
    mock_response.status_code = 42

    mock_response.text = 'The answer to life the universe & everything.'

    yield TwitterResponse(mock_response, options)


def test_twitter_connection_error(user_group, successful_response_mock):

    side_effects = [
        successful_response_mock,  # success user 1
        TwitterConnectionError(ConnectionError()),  # failure user 2
        successful_response_mock  # success user 2
    ]

    with patch.object(twacapic.auth.TwitterAPI, 'request', autospec=True,
                      side_effect=side_effects) as mocked_request_method:

        user_group.collect()
        assert mocked_request_method.call_count == 3


def test_twitter_request_error(user_group, successful_response_mock, failed_response_mock):

    side_effects = [
            successful_response_mock,  # success user 1
            failed_response_mock,  # failure user 2
            successful_response_mock  # success user 2
    ]

    with patch.object(twacapic.auth.TwitterAPI, 'request', autospec=True,
                      side_effect=side_effects) as mocked_request_method:

        user_group.collect()
        assert mocked_request_method.call_count == 3


def test_stops_after_10_request_errors(user_group, failed_response_mock):

    side_effects = [failed_response_mock] * 11

    with patch.object(twacapic.auth.TwitterAPI, 'request', autospec=True,
                      side_effect=side_effects) as mocked_request_method:
        with patch.object(twacapic.collect.time, 'sleep'):

            with pytest.raises(AssertionError):
                user_group.collect()

            assert mocked_request_method.call_count == 11


def test_stops_after_10_connection_errors(user_group, failed_response_mock):

    side_effects = [TwitterConnectionError(ConnectionError())] * 11

    with patch.object(twacapic.auth.TwitterAPI, 'request', autospec=True,
                      side_effect=side_effects) as mocked_request_method:
        with patch.object(twacapic.collect.time, 'sleep'):

            with pytest.raises(TwitterConnectionError):
                user_group.collect()

            assert mocked_request_method.call_count == 11
