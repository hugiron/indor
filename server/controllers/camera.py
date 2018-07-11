import aiohttp.web
from models import db
from models.account import Account
from models.camera import Camera
from exception import *


class CameraController(object):
    async def get(self, request):
        try:
            access_token = request.rel_url.query.get('access_token')
            if not access_token:
                raise MissingParameter('access_token')
            account_id = await Account.redis_get_id(request.app['redis'], access_token)
            if account_id is None:
                raise InvalidAccessToken()
            user_cameras = await db.select([Camera.id, Camera.name])\
                .where(Camera.account_id == account_id)\
                .gino\
                .model(Camera)\
                .all()
            json_cameras = [{'id': camera.id, 'name': camera.name} for camera in user_cameras]
            return aiohttp.web.json_response({'camera': json_cameras})
        except APIException as api_exception:
            raise api_exception
        except:
            raise InternalServerError()

    async def post(self, request):
        try:
            request_data = await request.post()
            access_token = request_data.get('access_token')
            name = request_data.get('name')
            if not access_token:
                raise MissingParameter('access_token')
            if not name:
                raise MissingParameter('name')
            account_id = await Account.redis_get_id(request.app['redis'], access_token)
            if account_id is None:
                raise InvalidAccessToken()
            camera = await db.select([Camera.id])\
                .where(db.and_(Camera.account_id == account_id,
                               Camera.name == name))\
                .gino\
                .model(Camera)\
                .all()
            if camera:
                camera = camera[0]
            else:
                camera = await Camera.create(account_id=account_id, name=name)
            return aiohttp.web.json_response({"id": camera.id})
        except APIException as api_exception:
            raise api_exception
        except:
            raise InternalServerError()
