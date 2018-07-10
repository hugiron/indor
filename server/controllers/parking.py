import aiohttp.web
from models import db
from models.account import Account
from exception import *


class ParkingController(object):
    async def get(self, request):
        try:
            all_accounts = await db.select([Account.id, Account.name])\
                .gino\
                .model(Account)\
                .all()
            json_parking = [{'id': parking.id, 'name': parking.name} for parking in all_accounts]
            return aiohttp.web.json_response({'parking': json_parking})
        except:
            raise InternalServerError()

    async def get_by_id(self, request):
        try:
            parking_id = int(request.match_info['parking_id'])
            account_by_id = await db.select([Account.places])\
                .where(Account.id == parking_id)\
                .gino\
                .model(Account)\
                .all()
            if not account_by_id:
                raise InvalidParameter('parking_id')
            json_place = account_by_id[0].places
            return aiohttp.web.json_response({'place': json_place})
        except APIException as api_exception:
            raise api_exception
        except:
            raise InternalServerError()
