# pylint: disable=W1514,W0621,C0116

import json
import os
import random
import shutil
import sys
import time
from glob import glob
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import twacapic
import twacapic.templates
import yaml
from loguru import logger
from requests.exceptions import ConnectionError
from twacapic import __version__
from twacapic.auth import read_credentials, save_credentials
from twacapic.collect import UserGroup
from twacapic.utils import get_date_from_tweet_id
from TwitterAPI import TwitterResponse
from TwitterAPI.TwitterError import TwitterConnectionError

logger.add(sys.stdout, level='INFO')


def test_version():
    assert __version__ == '0.8.0'


@pytest.fixture
def user_group():

    user_group = UserGroup('tests/mock_files/users.csv', name='test_users')

    yield user_group

    shutil.rmtree('results/test_users')


@pytest.fixture
def user_group_to_get_all_the_tweets():

    user_group = UserGroup('tests/mock_files/users.csv', name='test_users_get_all_the_tweets', get_all_the_tweets=True)

    yield user_group

    shutil.rmtree('results/test_users_get_all_the_tweets')


@pytest.fixture
def user_group_with_deleted_protected_accounts():

    user_group = UserGroup('tests/mock_files/protected_nonexistent_users.csv',
                           name='test_non_reachable_users')

    yield user_group

    shutil.rmtree(Path.cwd()/'results'/'test_non_reachable_users')
    # shutil.rmtree(Path.cwd()/'results'/'deleted_test_non_reachable_users')
    # shutil.rmtree(Path.cwd()/'results'/'protected_test_non_reachable_users')
    # shutil.rmtree(Path.cwd()/'results'/'suspended_test_non_reachable_users')


@pytest.fixture(scope='module')
def user_group_with_tweets():

    user_group = UserGroup('tests/mock_files/users.csv', name='test_users_with_tweets')

    user_group.collect()

    yield user_group

    shutil.rmtree(user_group.path)


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


@pytest.fixture
def user_group_with_very_old_tweets(user_group_with_tweets, user_group):

    shutil.copytree(user_group.path, 'results/users_with_very_old_tweets')

    user_group = UserGroup(name='users_with_very_old_tweets')

    for user_id in user_group_with_tweets.user_ids:
        metadata = user_group_with_tweets.meta[user_id]
        metadata['newest_id'] = metadata['oldest_id']

        with open(f'{user_group.path}/{user_id}/meta.yaml', 'w') as f:
            yaml.dump(metadata, f)

    yield user_group

    shutil.rmtree(user_group.path)


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
def successful_response_mock_with_next_token(user_group_with_tweets):

    tweet_file = glob(f'{user_group_with_tweets.path}/*/*.json')[0]

    mock_response = Mock()
    options = Mock()
    mock_response.status_code = 200
    with open(tweet_file, 'r') as tweets:
        mock_response.text = tweets.read()

    text = json.loads(mock_response.text)

    text['meta']['next_token'] = 'mock_tocken'

    mock_response.text = json.dumps(text)

    yield TwitterResponse(mock_response, options)


@pytest.fixture(scope='module')
def successful_empty_response_mock():

    mock_response = Mock()
    options = Mock()
    mock_response.status_code = 200

    mock_response.text = '''
        {
            "meta": {
                "result_count": 0
            }
        }
        '''

    yield TwitterResponse(mock_response, options)


@pytest.fixture(scope='module')
def failed_response_mock():

    mock_response = Mock()
    options = Mock()
    mock_response.status_code = 42

    mock_response.text = 'The answer to life the universe & everything.'

    yield TwitterResponse(mock_response, options)


@pytest.fixture
def minimal_config_path():
    path = 'minimal_config.yaml'
    min_config = {'expansions': {}, 'fields': {}, 'user.fields': {}}
    with open(path, 'w') as f:
        yaml.dump(min_config, f)

    yield path

    os.remove(path)


@pytest.fixture
def group_with_minimal_config(minimal_config_path):
    user_group = UserGroup(
        'tests/mock_files/users.csv',
        name='test_users_with_min_config',
        config=minimal_config_path
    )

    yield user_group

    shutil.rmtree(user_group.path)


@pytest.fixture
def backup_logs():

    logs = {'errors': False, 'warnings': False}
    for entry in logs:
        if os.path.isfile(f'{entry}.log'):
            os.rename(f'{entry}.log', f'{entry}.log.bk')
            logs[entry] = True

    yield logs

    for entry in logs:
        if entry:
            os.rename(f'{entry}.log.bk', f'{entry}.log')


def test_run(script_runner, backup_logs):

    ret = script_runner.run(
        'twacapic',
        '-g', 'test_run',
        '-u', 'tests/mock_files/users.csv',
        '-c', 'twacapic/templates/min_group_config.yaml',
        '-l', 'DEBUG'
    )

    assert ret.success
    assert ret.stderr == ''
    assert '36476777' in ret.stdout
    with open('results/test_run/group_config.yaml') as f:
        config = yaml.safe_load(f)
        assert not config['fields']['attachments']
    shutil.rmtree('results/test_run')


def test_run_2_lists(script_runner, backup_logs):

    ret = script_runner.run(
        'twacapic',
        '-g', 'test_run_2_lists', 'test_run_2_lists_2',
        '-u', 'tests/mock_files/users.csv', 'tests/mock_files/users2.csv',
        '-c', 'twacapic/templates/min_group_config.yaml',
        '-l', 'DEBUG'
    )

    assert ret.success
    assert ret.stderr == ''
    assert '36476777' in ret.stdout
    assert '1349149096909668363' in ret.stdout
    with open('results/test_run_2_lists/group_config.yaml') as f:
        config = yaml.safe_load(f)
        assert not config['fields']['attachments']
    with open('results/test_run_2_lists_2/group_config.yaml') as f:
        config = yaml.safe_load(f)
        assert not config['fields']['attachments']

    ret2 = script_runner.run(
        'twacapic',
        '-g', 'test_run_2_lists', 'test_run_2_lists_2',
        '-l', 'DEBUG'
    )

    assert ret2.success
    assert ret2.stderr == ''
    assert '36476777' in ret2.stdout
    assert '1349149096909668363' in ret2.stdout
    with open('results/test_run_2_lists/group_config.yaml') as f:
        config = yaml.safe_load(f)
        assert not config['fields']['attachments']
    with open('results/test_run_2_lists_2/group_config.yaml') as f:
        config = yaml.safe_load(f)
        assert not config['fields']['attachments']

    shutil.rmtree('results/test_run_2_lists')
    shutil.rmtree('results/test_run_2_lists_2')


def test_run_2_lists_not_enough_paths(script_runner, backup_logs):

    ret = script_runner.run(
        'twacapic',
        '-g', 'test_run_2_lists', 'test_run_2_lists_2',
        '-u', 'tests/mock_files/users2.csv',
        '-c', 'twacapic/templates/min_group_config.yaml',
        '-l', 'DEBUG'
    )

    assert not ret.success
    assert 'AssertionError' in ret.stderr


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


def test_user_group_creates_directories(user_group):

    with open('tests/mock_files/users.csv') as file:
        for line in file:
            path = f'results/test_users/{line.strip()}'
            assert os.path.isdir(path), f"Could not find directory for user in {path}"


def test_can_retrieve_tweets_from_user_timeline(user_group_with_tweets):

    folders = glob(f'{user_group_with_tweets.path}/*/')

    for folder in folders:
        files = glob(f'{folder}/*.json')

        assert len(files) >= 1, f'No tweets in user folder {folder}'

        with open(files[0], 'r') as file:
            tweets = json.load(file)
            assert len(tweets['data']) > 90, 'not retrieving maximum of tweets per request'


def test_user_in_group_has_meta_file(user_group_with_tweets):

    folders = glob(f'{user_group_with_tweets.path}/*/')

    for folder in folders:

        meta_file_path = f'{folder}/meta.yaml'

        with open(meta_file_path, 'r') as metafile:
            meta_data = yaml.safe_load(metafile)

        files = glob(f'{folder}/*.json')
        with open(files[0], 'r') as tweetfile:
            tweet_data = json.load(tweetfile)

        assert tweet_data['meta']['newest_id'] == meta_data['newest_id']
        assert tweet_data['meta']['oldest_id'] == meta_data['oldest_id']


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


def test_pagination_if_page_has_zero_results(user_group_with_old_meta_file,
                                             successful_response_mock_with_next_token,
                                             successful_empty_response_mock):

    number_of_users = len(user_group_with_old_meta_file.user_ids)

    side_effects = [
        successful_response_mock_with_next_token,  # success page 1
        successful_empty_response_mock,  # empty page 2
    ] * number_of_users

    with patch.object(twacapic.auth.TwitterAPI, 'request', autospec=True,
                      side_effect=side_effects) as mocked_request_method:

        user_group_with_old_meta_file.collect()
        assert mocked_request_method.call_count == 2 * number_of_users


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


def test_can_import_group_config():
    group_config = twacapic.templates.group_config

    assert 'expansions' in group_config
    assert 'fields' in group_config


def test_group_has_default_config(user_group):
    assert 'group_config.yaml' in os.listdir(user_group.path)


def test_can_use_custom_config(group_with_minimal_config):
    user_group = group_with_minimal_config

    with open(f'{user_group.path}/group_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

        assert config['expansions'] == {}
        assert config['fields'] == {}


def test_group_retains_config(group_with_minimal_config, successful_response_mock):

    side_effects = [
        successful_response_mock,  # success user 1
        successful_response_mock  # success user 2
    ]

    with patch.object(twacapic.auth.TwitterAPI, 'request',
                      autospec=True, side_effect=side_effects) as mocked_request_method:

        group_with_minimal_config.collect()
        assert mocked_request_method.call_count == 2

        with open(f'{group_with_minimal_config.path}/group_config.yaml', 'r') as f:
            config = yaml.safe_load(f)

            assert config['expansions'] == {}
            assert config['fields'] == {}


def test_fields_in_tweets(user_group_with_tweets):

    user_group = user_group_with_tweets

    for user_id in user_group.user_ids:
        for file in user_group.tweet_files[user_id]:
            with open(file, 'r') as f:
                tweets = json.load(f)
                for tweet in tweets['data']:
                    number_of_fields = 0
                    for field in user_group.config['fields']:
                        if user_group.config['fields'][field]:
                            if field in tweet:
                                number_of_fields += 1
                    assert number_of_fields > 2


def test_expansions_in_tweets(user_group_with_tweets):

    for user_id in user_group_with_tweets.user_ids:
        for file in user_group_with_tweets.tweet_files[user_id]:
            with open(file, 'r') as f:
                tweets = json.load(f)
                assert 'includes' in tweets
                assert 'users' in tweets['includes']
                assert 'tweets' in tweets['includes']

                for user in tweets['includes']['users']:
                    for key in ['public_metrics',
                                'created_at',
                                'description',
                                # 'location', can be empty
                                'verified']:
                        assert key in user.keys()


def test_non_reachable_users(user_group_with_deleted_protected_accounts):

    user_group_with_deleted_protected_accounts.collect()
    print(user_group_with_deleted_protected_accounts.user_ids)

    for item in os.listdir(user_group_with_deleted_protected_accounts.path):
        assert item in ['group_config.yaml', '2530965517', '557558765', '11']

    user_group_with_deleted_protected_accounts.collect()  # check second time for errors because of missing metadata etc.

    assert (Path.cwd()/'results'/'test_non_reachable_users').is_dir()
    assert not (Path.cwd()/'results'/'deleted_test_non_reachable_users').exists()
    assert not (Path.cwd()/'results'/'protected_test_non_reachable_users').exists()
    assert not (Path.cwd()/'results'/'suspended_test_non_reachable_users').exists()


def test_user_group_setup_for_getting_all_the_tweets(user_group_to_get_all_the_tweets):

    for user_id in user_group_to_get_all_the_tweets.user_ids:
        meta_file_path = f'{user_group_to_get_all_the_tweets.path}/{user_id}/meta.yaml'

        with open(meta_file_path, 'r') as f:
            metadata = yaml.safe_load(f)

        assert metadata['newest_id'] == metadata['oldest_id']
        assert metadata['newest_id'] == '0'


def test_collect_only_tweets_of_last_x_days(user_group_to_get_all_the_tweets):

    days = random.randint(1, 14)

    user_group_to_get_all_the_tweets.collect(days=days)

    for user_id in user_group_to_get_all_the_tweets.user_ids:
        tweet_files = user_group_to_get_all_the_tweets.tweet_files[user_id]
        if len(tweet_files) == 0:
            continue
        tweet_files.sort(reverse=False)
        oldest_tweet_id = tweet_files[0].split(
            '/')[-1].split('_')[1].split('.')[0]
        timestamp = get_date_from_tweet_id(oldest_tweet_id)['timestamp']
        seconds_diff = time.time() - timestamp/1000
        hours_diff = seconds_diff/3600
        days_diff = hours_diff/24

        assert days_diff <= days
