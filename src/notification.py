from datetime import datetime
from enum import Enum
from tkinter import W
from typing import List, Tuple
import math
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
import redis
from marshmallow import fields
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
class HandleNotificationResult:
    initiated: bool
    removed_stars: List[str]
    added_stars: List[str]


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


    def get_repos(self, teleg_user_id: int) -> List[str]:
        '''Get subscribed repos for user'''

        with session_factory() as session:
            return session\
                            .query(Repo)\
                            .join(User, Repo.users)\
                            .filter(User.teleg_user_id == teleg_user_id)\
                            .all()


    def get_repo_stars_diff(self, repo_id: int) -> Tuple[List[str], List[str]]:
        '''Get repo starts for repo by id'''

        with session_factory() as session:
            repo = session.query(Repo).filter(Repo.id == repo_id).one()
            return self.__get_repo_stars_diff(repo)


    def __get_repo_stars_diff(self, repo: Repo) -> HandleNotificationResult:
        '''Get diff for stars locally and from the github.'''
        is_repo_initiated = repo.last_updated_time is None

        repo_url = repo.url
        repo_stars_count = self.get_repo_stars_count(repo_url)
        pages_number = math.ceil(repo_stars_count / self.page_size)

        github_stargazers_pages = []

        repo_redis_key = 'stars_repo_' + str(repo.id)
        stars_from_db = list(map(
                                    StarItem.from_json,
                                    self.redis_connection.lrange(repo_redis_key, 0, -1)
                                ))

        for page_number in range(pages_number, 0, -1):
            github_page = list(map(
                                    StarItem.from_dict,
                                    self.get_repo_stargazers_page(repo_url, page_number)
                                ))
            github_stargazers_pages.append(github_page)

            prev_items_number = (page_number - 1) * self.page_size
            if prev_items_number == 0 or \
                (len(stars_from_db) > prev_items_number and \
                stars_from_db[prev_items_number].starred_at == github_page[0].starred_at):

                break

        prev_items_number = (page_number - 1) * self.page_size

        github_stargazers_pages.reverse()
        stars_from_db_updated = stars_from_db[prev_items_number:]
        github_stargazers = []
        for page in github_stargazers_pages:
            for row in page:
                github_stargazers.append(row)

        stars_from_db_updated_set = set(map(lambda x: x.login, stars_from_db_updated))
        github_stargazers_set = set(map(lambda x: x.login, github_stargazers))

        removed_stars = list(github_stargazers_set.difference(stars_from_db_updated_set))
        added_stars = list(stars_from_db_updated_set.difference(github_stargazers_set))

        return HandleNotificationResult(initiated=is_repo_initiated,
                                        removed_stars=removed_stars,
                                        added_stars=added_stars)
