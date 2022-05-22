'''The telegram bot module'''
import logging
from typing import List
from aiogram import Bot, Dispatcher, executor, types
import settings
from notification import Notification, SubscribeResult, UnsubscribeResut

logging.basicConfig(level=logging.INFO)

bot = Bot(token=settings.TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)

REPOS_COMMAND = 'repos'
UNSUBSCRIBE_COMMAND = 'unsubs'

unsubscribe_states_users_ids = set()

def get_message_lines(lines: List[str]) -> str:
    '''Join string list to string'''
    return '\n'.join(lines)

def clean_unsubscribe_states(message: types.Message):
    '''Clean unsubscribe state for user'''
    unsubscribe_states_users_ids.discard(message.from_user.id)

@dp.message_handler(commands=['start', 'help'])
async def welcome(message: types.Message):
    '''Send the info about commands'''
    clean_unsubscribe_states(message)

    await message.answer(get_message_lines([
        'The bot for tracking github starts.',
        '',
        f'See subscribed repos: /{REPOS_COMMAND}',
        'Subscribe repo: (repourl)',
        f'Unsubscribe repo: /{UNSUBSCRIBE_COMMAND}'
    ]))


@dp.message_handler(commands=[REPOS_COMMAND])
async def get_user_subscribed_repos(message: types.Message):
    '''Send subscribed repos'''
    user_id = message.from_user.id
    clean_unsubscribe_states(message)

    notification = Notification()
    user_repos = notification.get_user_repos(user_id)

    if len(user_repos) == 0:
        await message.answer('There are no subscribed repos for you.')
        return

    answer = ['Subscribed repos:', '']
    for repo in user_repos:
        answer.append(' - ' + repo.url)

    await message.answer(get_message_lines(answer), disable_web_page_preview=True)


@dp.message_handler(commands=[UNSUBSCRIBE_COMMAND])
async def unsubscribed_repo(message: types.Message):
    '''Send subscribed repos'''
    unsubscribe_states_users_ids.add(message.from_user.id)

    await message.answer('Put a link of the repo for unsubscribing.')

@dp.message_handler()
async def send_url(message: types.Message):
    '''User sends url. Subscribe/unsubscribe'''
    repo_url = message.text
    user_id = message.from_user.id

    unsubscribe = user_id in unsubscribe_states_users_ids
    print(unsubscribe_states_users_ids)
    clean_unsubscribe_states(message)

    notification = Notification()

    if unsubscribe:
        unsubscribe_result = notification.unsubscribe(user_id, repo_url)
        if unsubscribe_result == UnsubscribeResut.REPO_MISSING:
            await message.answer(f'You are not subscribed for the repo {repo_url}',
                                disable_web_page_preview=True)
            return

        await message.answer('Unsubscribed successfully.')
        return

    subscribe_result = notification.subscribe(user_id, repo_url)
    if subscribe_result == SubscribeResult.ALREADY_SUBSCRIBE:
        await message.answer(f'You are already subscribed to "{repo_url}" repo.',
                                disable_web_page_preview=True)
        return

    await message.answer('Subscribed successfully.')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
