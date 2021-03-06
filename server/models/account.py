from gino.dialects.asyncpg import JSONB
from models import db


class Account(db.Model):
    __tablename__ = 'account'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False)
    places = db.Column(JSONB(), nullable=False, server_default='{}')

    @staticmethod
    async def redis_get_id(redis, access_token):
        id = await redis.get('%s_id' % access_token)
        return int(id) if id is not None else id

    @staticmethod
    async def redis_set_id(redis, access_token, id):
        await redis.set('%s_id' % access_token, str(id))

    @staticmethod
    async def redis_get_username(redis, access_token):
        username = await redis.get('%s_username' % access_token)
        return username.decode('utf-8') if username is not None else username

    @staticmethod
    async def redis_set_username(redis, access_token, username):
        await redis.set('%s_username' % access_token, username)

    @staticmethod
    async def redis_delete(redis, access_token):
        await redis.delete('%s_id' % access_token)
        await redis.delete('%s_username' % access_token)
