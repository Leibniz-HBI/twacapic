import os


class UserGroup:

    def __init__(self, path, name):
        with open(path, 'r') as file:
            for line in file:
                os.makedirs(f'results/{name}/{line.strip()}', exist_ok=True)
