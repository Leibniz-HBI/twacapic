# twacapic

Twitter Academic API Client

In development. Expect breaking changes and bugs when updating to the latest version.

Tested on Linux (Ubuntu 20.10, Python 3.8) and MacOS 11 (Python 3.9). Please [raise an issue](https://github.com/Leibniz-HBI/twacapic/issues) if you need to install it with another Python version or encounter issues with other operating systems.


## Installation

Install via pip:

`pip install twacapic`


## Usage

```txt
usage: twacapic [-h] [-u USERLIST] [-g GROUPNAME] [-c GROUP_CONFIG] [-l LOG_LEVEL] [-lf LOG_FILE]
                [-s SCHEDULE] [-n NOTIFY]

optional arguments:
  -h, --help            show this help message and exit
  -u USERLIST, --userlist USERLIST
                        Path to list of user IDs, one per line. Required for first run only. Can be
                        used to add users to a group.
  -g GROUPNAME, --groupname GROUPNAME
                        Name of the group to collect. Results will be saved in folder
                        `results/GROUPNAME/`. Can be used to poll for new tweets of a group. Default:
                        "users"
  -c GROUP_CONFIG, --group_config GROUP_CONFIG
                        Path to a custom group config file to define tweet data to be retrieved, e.g.
                        retweets, mentioned users, attachments. A template named `group_config.yaml`
                        can be found in any already created group folder.
  -l LOG_LEVEL, --log_level LOG_LEVEL
                        Level of output detail (DEBUG, INFO, WARNING, ERROR). Warnings and Errors are
                        always logged in respective log-files `errors.log` and `warnings.log`.
                        Default: ERROR
  -lf LOG_FILE, --log_file LOG_FILE
                        Path to logfile. Defaults to standard output.
  -s SCHEDULE, --schedule SCHEDULE
                        If given, repeat every SCHEDULE minutes.
  -n NOTIFY, --notify NOTIFY
                        If given, notify email address in case of unexpected errors. Needs further
                        setup. See README.
```

At the moment twacapic can only collect the latest 100 tweets of a list of users and then poll for new tweets afterwards if called again with the same group name or if the `-s` argument is given.

Email notifications with the `-n` argument use the OAuth2 procedure of yagmail and necessitate an OAuth2 procedure to give access to a Gmail account as described in  its [README](https://github.com/kootenpv/yagmail#oauth2)

### Authorisation with the Twitter API

At first use, it will prompt you for your API credentials, which you find [here](https://developer.twitter.com/en/portal/projects-and-apps). These credentials will be stored in a file in the working directory, so make sure that the directory is readable by you and authorised users only.

For non-interactive use, e.g. when automatically deploying twacapic to a server, this file can be used as a template and should always be placed in the working directory of twacapic.

### Example

`twacapic -g USER_GROUP_NAME -u PATH_TO_USER_CSV`

`USER_GROUP_NAME` should be the name of the results folder that is meant to be created and will contain raw json responses from Twitter.

`PATH_TO_USER_CSV` should be a path to a list of Twitter user IDs, without header, one line per user ID.

Afterwards you can poll for new tweets of a user group by running simply:

`twacapic -g USER_GROUP_NAME`

Enjoy!


### Config Template

The group config is a yaml file in the following form:

```yaml
fields:
  attachments: No
  author_id: Yes
  context_annotations: No
  conversation_id: No
  created_at: No
  entities: No
  geo: No
  in_reply_to_user_id: No
  lang: No
  non_public_metrics: No
  organic_metrics: No
  possibly_sensitive: No
  promoted_metrics: No
  public_metrics: No
  referenced_tweets: No
  reply_settings: No
  source: No
  withheld: No
expansions:
  author_id: Yes
  referenced_tweets.id: No
  in_reply_to_user_id: No
  attachments.media_keys: No
  attachments.poll_ids: No
  geo.place_id: No
  entities.mentions.username: No
  referenced_tweets.id.author_id: No
```

An explanation of the fields and expansions can be found in Twitter's API docs:

  - [Fields](https://developer.twitter.com/en/docs/twitter-api/fields)
  - [Expansions](https://developer.twitter.com/en/docs/twitter-api/expansions)


## Dev Install

1. Install [poetry](https://python-poetry.org/docs/#installation)
2. Clone repository
3. In the directory run `poetry install`
4. Run `poetry shell` to start development virtualenv
5. Run `twacapic` to enter API keys. Ignore the IndexError.
6. Run `pytest` to run all tests
