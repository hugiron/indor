import aiohttp.web
from models import db
from models.account import Account
from exception import *


class AccountController(object):
    async def get(self, request):
        try:
            access_token = request.rel_url.query.get('access_token')
            if not access_token:
                raise MissingParameter('access_token')
            account_id = await Account.redis_get_id(request.app['redis'], access_token)
            if account_id is None:
                raise InvalidAccessToken()
            account = await db.select([Account])\
                .where(Account.id == account_id)\
                .gino\
                .model(Account)\
                .first()
            username = await Account.redis_get_username(request.app['redis'], access_token)
            json_account = {
                'name': account.name,
                'username': username
            }
            return aiohttp.web.json_response(json_account)
        except APIException as api_exception:
            raise api_exception
        except:
            raise InternalServerError()
