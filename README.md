# twacapic

Twitter Academic API Client

In development. Expect breaking changes and destructive bugs when updating to the latest version.


## Installation

Install via pip:

`pip install twacapic`


## Usage

```
usage: twacapic [-h] [-u USERLIST] [-g GROUPNAME]

optional arguments:
  -h, --help            show this help message and exit
  -u USERLIST, --userlist USERLIST
                        path to list of user IDs, one per line. Required for
                        first run only. Can be used to add users to a group
  -g GROUPNAME, --groupname GROUPNAME
                        name of the group to collect. Results will be saved in
                        folder `results/GROUPNAME/`. Can be used to poll for
                        new tweets of a group. Default: "users"
```

### Example

At the moment twacapic can only collect the latest 100 tweets of a list of users and then poll for new tweets afterwards if called again with the same group name.

`twacapic -g USER_GROUP_NAME -u PATH_TO_USER_CSV`

`USER_GROUP_NAME` should be the name of the results folder that is meant to be created and will contain raw json responses from Twitter.

`PATH_TO_USER_CSV` should be a path to a list of Twitter user IDs, without header, one line per user ID.

Afterwards you can poll for new tweets of a user group by running simply:

`twacapic -g USER_GROUP_NAME`

Enjoy!


## Dev Install

1. Install [poetry](https://python-poetry.org/docs/#installation)
2. Clone repository
3. In the directory run `poetry install`
4. Run `poetry shell` to start development virtualenv
5. Run `twacapic` to enter API keys. Ignore the IndexError.
6. Run `pytest` to run all tests
