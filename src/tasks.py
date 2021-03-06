'''The module with celery tasks'''
import asyncio
from aiogram import Bot
import celery
from celery.utils.log import get_task_logger
from notification import Notification
from common import generate_notification_message
import settings

app = celery.Celery('github-notification')

app.conf.update(broker_url=settings.CELERY_BROKER_URL,
                result_backend=settings.CELERY_RESULT_BACKEND)


bot = Bot(token=settings.TELEGRAM_API_TOKEN)

app.conf.beat_schedule = {
    'add-every-2-seconds': {
        'task': 'tasks.handle_urls',
        'schedule': settings.SECONDS_UPDATE,
    },
}

logger = get_task_logger(__name__)

class Sender:
    '''Sender'''

    def __init__(self, user, message) -> None:
        self.user = user
        self.message = message

    async def send(self):
        '''send message to user'''
        await bot.send_message(self.user, self.message, disable_web_page_preview=True)


@app.task
def handle_repo(repo_id: int):
    '''Handle repo by id'''
    logger.info('Handle repo with id %s is started.', repo_id)
    notification = Notification()
    diff_result = notification.update_repo_stars(repo_id)

    if diff_result.need_to_handle():
        repo = notification.get_repo_by_id(repo_id)
        message = generate_notification_message(repo.url,
                                                diff_result.added_stars,
                                                diff_result.removed_stars)

        for user in diff_result.teleg_subscribed_users:
            asyncio.run(Sender(user, message).send())

    logger.info('Handle repo with id %s is finished.', repo_id)


@app.task
def handle_urls():
    '''Handle all urls from the DB'''

    repos = Notification().get_all_repos()
    for repo in repos:
        handle_repo.delay(repo.id)


app.conf.timezone = 'UTC'
