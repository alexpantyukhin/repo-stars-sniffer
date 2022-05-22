from datetime import datetime
from enum import Enum
from typing import List
import math
from urllib.parse import urlparse
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
import redis
from marshmallow import fields
from sqlalchemy.orm import sessionmaker
import settings
import github_api
from models import session_factory, User, Repo, get_or_create


class SubscribeResult(Enum):
    '''Subscibe result enum'''
    OK = 1
    ALREADY_SUBSCRIBE = 2
    INCORRECT_REPO = 3


class UnsubscribeResut(Enum):
    '''Unsubscribe result enum'''
    OK = 1
    REPO_MISSING = 2


@dataclass_json
@dataclass
class StarItem:
    login: str
    starred_at: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))

@dataclass
class UpdateRepoStarsResult:
    initiated: bool
    removed_stars: List[str]
    added_stars: List[str]
    teleg_subscribed_users: List[str]


REPOS_COLLECTION = 'repos'

class Notification:
    '''The class represent the '''
    def __init__(
                    self,
                    redis_connection=None,
                    get_repo_stars_count = None,
                    get_repo_stargazers_page = None,
                    page_size = 100
                ) -> None:
        self.redis_connection = redis_connection or \
                                redis.Redis(
                                    host=settings.REDIS_HOST,
                                    port=settings.REDIS_PORT,
                                    db=0)
        self.get_repo_stars_count = get_repo_stars_count or github_api.get_repo_stars_count
        self.get_repo_stargazers_page = get_repo_stargazers_page or \
                                        github_api.get_repo_stargazers_page

        self.page_size = page_size


    def subscribe(self, teleg_user_id: int, repository_url: str) -> SubscribeResult:
        '''Subscribe to watch for the repo'''

        #TODO : check for valid url
        # if True:
        #     pass

        with session_factory() as session:
            user_repo_query = session.query(Repo)\
                            .join(User, Repo.users)\
                            .filter(Repo.url == repository_url,
                                    User.teleg_user_id == teleg_user_id)\
                            .exists()

            repo_is_binded = session.query(user_repo_query).scalar()

            if repo_is_binded:
                return SubscribeResult.ALREADY_SUBSCRIBE

            user = get_or_create(session, User, teleg_user_id = teleg_user_id)
            repo = get_or_create(session, Repo, url = repository_url)

            user.repos.append(repo)
            session.commit()

        return SubscribeResult.OK


    def unsubscribe(self, teleg_user_id: str, repository_url: str) -> UnsubscribeResut:
        '''Unsubscribe to watch for the repo'''

        with session_factory() as session:
            user = session.query(User)\
                            .filter(User.teleg_user_id == teleg_user_id)\
                            .one_or_none()

            if user is None:
                return UnsubscribeResut.REPO_MISSING

            user_repo = None
            for repo in user.repos:
                if repo.url == repository_url:
                    user_repo = repo
                    break

            if user_repo is None:
                return UnsubscribeResut.REPO_MISSING

            user.repos.remove(user_repo)
            session.commit()

        return UnsubscribeResut.OK


    def get_user_repos(self, teleg_user_id: int) -> List[str]:
        '''Get subscribed repos for user'''

        with session_factory() as session:
            repos = session\
                .query(Repo)\
                .join(User, Repo.users)\
                .filter(User.teleg_user_id == teleg_user_id)\
                .all()

            return [repo.url for repo in repos]


    def update_repo_stars(self, repo_id: int) -> UpdateRepoStarsResult:
        '''Get repo starts for repo by id'''

        with session_factory() as session:
            repo = session.query(Repo).filter(Repo.id == repo_id).one()
            return self.__update_repo_stars(repo, session)


    def __get_all_github_starts(self, repo: Repo) -> List[StarItem]:
        parsed_url = urlparse(repo.url)

        api_repo_url = f'https://api.github.com/repos{parsed_url.path}'
        api_repo_stars_url = f'https://api.github.com/repos{parsed_url.path}/stargazers'

        repo_stars_count = self.get_repo_stars_count(api_repo_url)

        pages_number = math.ceil(repo_stars_count / self.page_size)

        github_stars = []

        for page_number in range(1, pages_number + 1):
            github_page = list(map(
                                    StarItem.from_dict,
                                    self.get_repo_stargazers_page(
                                        api_repo_stars_url,
                                        page=page_number,
                                        size=self.page_size
                                    )
                                ))

            for page_item in github_page:
                github_stars.append(page_item)

        return github_stars


    def __update_repo_stars(self, repo: Repo, session: sessionmaker) -> UpdateRepoStarsResult:
        '''Get diff for stars locally and from the github.'''
        is_repo_initiated = repo.last_updated_time is not None

        if is_repo_initiated\
            and (repo.last_updated_time - datetime.utcnow).minutes < settings.MINUTES_UPDATE:

            return UpdateRepoStarsResult(initiated=is_repo_initiated,
                                            removed_stars=[],
                                            added_stars=[])


        github_stars = self.__get_all_github_starts(repo)

        repo_redis_key = 'stars_repo_' + str(repo.id)
        stars_from_db = list(map(
                                    StarItem.from_json,
                                    self.redis_connection.lrange(repo_redis_key, 0, -1)
                                ))

        stars_from_db_updated_set = set(map(lambda x: x.login, stars_from_db))
        github_stargazers_set = set(map(lambda x: x.login, github_stars))

        removed_stars = list(github_stargazers_set.difference(stars_from_db_updated_set))
        added_stars = list(stars_from_db_updated_set.difference(github_stargazers_set))

        repo.last_updated_time = datetime.utcnow()
        session.commit()

        self.redis_connection.delete(repo_redis_key)
        self.redis_connection.lpush(repo_redis_key, *list(map(StarItem.to_json , github_stars)))

        users = [u.teleg_user_id for u in repo.users]

        return UpdateRepoStarsResult(initiated=is_repo_initiated,
                                     removed_stars=removed_stars,
                                     added_stars=added_stars,
                                     teleg_subscribed_users=users)
