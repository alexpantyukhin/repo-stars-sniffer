from typing import Dict, List
import json
import requests

def _get_request_content(base_url, page=None, size=None):
    url = base_url
    params = []
    if page is not None:
        params.append(f'page={str(page)}')

    if size is not None:
        params.append(f'size={str(size)}')

    params_str = '&'.join(params)
    if len(params) > 0:
        url += '?' + params_str

    contents = requests.get(url).text
    return json.loads(contents)


def get_repo_stars_count(repo_url: str) -> int:
    content = _get_request_content(repo_url)
    return content['stargazers_count']


def get_repo_stargazers_page(repo_url: str, page: int) -> List[Dict[str, str]]:
    content = _get_request_content(repo_url, page=page)
    return map(lambda x: x['name'] + ' (fork)' if x['fork'] else x['name'], content)

def get_user_repos(user: str) -> List[str]:
    user_url = f'https://api.github.com/users/{user}/repos'
    repos = _get_request_content(user_url)

    return map(lambda x: x, repos)
    # return map(lambda x: x['name'] + ' (fork)' if x['fork'] else x['name'], repos)

# def get_user_repo_stargazers(user, repo):
#     stargazers_url = f'https://api.github.com/repos/{user}/{repo}/stargazers'
#     stargazers = _get_request_content(stargazers_url)

#     return map(lambda x: x['login'], stargazers)

def get_user_repo_stargazers(repo_url: str):
    stargazers_url = repo_url
    stargazers = _get_request_content(stargazers_url)

    return map(lambda x: x['login'], stargazers)


#for repo in gh.get_user().get_repos():
#    print(repo)
#    stargazers_url = repo.stargazers_url 
