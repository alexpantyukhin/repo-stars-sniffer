from datetime import datetime
from testcontainers.redis import RedisContainer
import notification


def test_docker_run_redis_with_password():
    config = RedisContainer()
    with config as redis:
        client = redis.get_client(decode_responses=True)

        client.set("hello", "world")
        print(client.get("hello"))
        assert client.get("hello") == "world"


def batch(items, page_size):
    iterator = iter(items)

    buffer = []
    result = []
    while True:
        value = next(iterator, None)
        if value is None:
            break

        buffer.append(value)
        if len(buffer) == page_size:
            result.append(buffer)
            buffer = []

    if len(buffer) > 0:
        result.append(buffer)

    return result


def test_notification_get_repo_stars_diff():
    config = RedisContainer()
    with config as redis:
        client = redis.get_client(decode_responses=True)
        items = []
        for i in range(1, 11):
            items.append({
                'starred_at': datetime(2022, 1, i),
                'login': 'login' + str(i)
            })

        repo_name = 'https://api.github.com/repos/alexpantyukhin/go-pattern-match/stargazers'
        serializaed_items = list(map(lambda x: notification.StarItem.from_dict(x).to_json() , items))
        client.rpush(f'stars_{repo_name}', *serializaed_items)

        githib_items = items.copy()
        del githib_items[5]
        githib_items.append({
            'starred_at': datetime(2022, 1, 20),
            'login': 'login' + str(20)
        })
        page_size = 3
        github_paged_items = batch(githib_items, page_size)


        n = notification.Notification(
            client,
            get_repo_stars_count=lambda _: len(githib_items),
            get_repo_stargazers_page = lambda _, x: github_paged_items[x - 1],
            page_size=page_size)

        result = n.get_repo_stars_diff(repo_name)

        assert len(result[0]) == 1
        assert len(result[1]) == 1


test_notification_get_repo_stars_diff()
