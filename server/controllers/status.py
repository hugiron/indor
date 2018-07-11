import aiohttp.web
import distutils.util
from models import db
from models.account import Account
from models.camera import Camera
from exception import *


class StatusController(object):
    async def get(self, request):
        try:
            camera_id = int(request.match_info['camera_id'])
            access_token = request.rel_url.query.get('access_token')
            if not access_token:
                raise MissingParameter('access_token')
            account_id = await Account.redis_get_id(request.app['redis'], access_token)
            if account_id is None:
                raise InvalidAccessToken()
            camera = await db.select([Camera.status])\
                .where(db.and_(Camera.id == camera_id,
                               Camera.account_id == account_id))\
                .gino\
                .model(Camera)\
                .all()
            if not camera:
                raise InvalidParameter('camera_id')
            return aiohttp.web.json_response({'status': camera[0].status})
        except APIException as api_exception:
            raise api_exception
        except:
            raise InternalServerError()

    async def post(self, request):
        try:
            request_data = await request.post()
            camera_id = int(request.match_info['camera_id'])
            access_token = request_data.get('access_token')
            status = request_data.get('status')
            if not access_token:
                raise MissingParameter('access_token')
            if not status:
                raise MissingParameter('status')
            if status not in ['true', 'false']:
                raise InvalidParameter('status')
            account_id = await Account.redis_get_id(request.app['redis'], access_token)
            if account_id is None:
                raise InvalidAccessToken()
            status, result = await Camera.update\
                .values(status=bool(distutils.util.strtobool(status)))\
                .where(db.and_(Camera.id == camera_id,
                               Camera.account_id == account_id))\
                .gino\
                .status()
            if status == 'UPDATE 0':
                raise InvalidParameter('camera_id')
            return aiohttp.web.json_response({'status': True})
        except APIException as api_exception:
            raise api_exception
        except:
            raise InternalServerError()
