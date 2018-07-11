import asyncio
import aioredis
import argparse
import random
import gino
import uvloop
import string
from sqlalchemy.engine.url import URL
import config
from models import db
from models.account import Account


def parse_args():
    parser = argparse.ArgumentParser()
    # TODO: Add helpers!!!
    parser.add_argument('--token_size', type=int, default=32, help='')
    subparsers = parser.add_subparsers(dest='cmd')
    create_parser = subparsers.add_parser('create')
    create_parser.add_argument('--name', type=str, required=True, help='')
    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('--token', type=str, required=True, help='')
    add_parser.add_argument('--username', type=str, required=True, help='')
    refresh_parser = subparsers.add_parser('refresh')
    refresh_parser.add_argument('--token', type=str, required=True, help='')
    delete_parser = subparsers.add_parser('delete')
    delete_parser.add_argument('--token', type=str, required=True, help='')
    return parser.parse_args()


async def init_connections():
    postgres_url = URL(
        drivername=config.postgres_driver,
        host=config.postgres_host,
        port=config.postgres_port,
        username=config.postgres_username,
        password=config.postgres_password,
        database=config.postgres_database)
    engine = await gino.create_engine(postgres_url)
    await db.set_bind(engine)
    connections = dict()
    connections['redis'] = await aioredis.create_redis(address=config.redis_address,
                                                       db=config.redis_database,
                                                       password=config.redis_password)
    return connections


async def close_connections(connections):
    await db.pop_bind().close()
    connections['redis'].close()
    await connections['redis'].wait_closed()


def generate_token():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(args.token_size))


async def create_account(connections):
    account = await Account.create(name=args.name)
    access_token = generate_token()
    await Account.redis_set_id(redis=connections['redis'], access_token=access_token, id=account.id)
    await Account.redis_set_username(redis=connections['redis'], access_token=access_token, username='Administrator')
    print('Account %s [#%d] was created with access token: %s' % (account.name, account.id, access_token))


async def add_account(connections):
    username = await Account.redis_get_username(redis=connections['redis'], access_token=args.token)
    if username == 'Administrator':
        account_id = await Account.redis_get_id(redis=connections['redis'], access_token=args.token)
        access_token = generate_token()
        await Account.redis_set_id(redis=connections['redis'], access_token=access_token, id=account_id)
        await Account.redis_set_username(redis=connections['redis'], access_token=access_token, username=args.username)
        print('User %s was added into account %d with access token: %s' % (args.username, account_id, access_token))
    elif username is None:
        print('Invalid access token')
    else:
        print('Current user is not administrator')


async def refresh_account(connections):
    account_id = await Account.redis_get_id(redis=connections['redis'], access_token=args.token)
    if account_id is not None:
        username = await Account.redis_get_username(redis=connections['redis'], access_token=args.token)
        access_token = generate_token()
        await Account.redis_set_id(redis=connections['redis'], access_token=access_token, id=account_id)
        await Account.redis_set_username(redis=connections['redis'], access_token=access_token, username=username)
        await Account.redis_delete(redis=connections['redis'], access_token=args.token)
        print('New access token: %s' % access_token)
    else:
        print('Invalid access token')


async def delete_account(connections):
    username = await Account.redis_get_username(redis=connections['redis'], access_token=args.token)
    if username != 'Administrator':
        await Account.redis_delete(redis=connections['redis'], access_token=args.token)
        print('User %s was deleted' % username)
    elif username is None:
        print('Invalid access token')
    else:
        print('Current user is administrator')


async def main():
    connections = await init_connections()
    try:
        if args.cmd == 'create':
            await create_account(connections=connections)
        elif args.cmd == 'add':
            await add_account(connections=connections)
        elif args.cmd == 'refresh':
            await refresh_account(connections=connections)
        elif args.cmd == 'delete':
            await delete_account(connections=connections)
    except Exception as msg:
        print(msg)
    finally:
        await close_connections(connections=connections)


if __name__ == '__main__':
    args = parse_args()
    # Использование UVLoop в качестве цикла событий по-умолчанию
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.get_event_loop().run_until_complete(main())
