import aiohttp.web
from models import db
from models.account import Account
from models.camera import Camera
from models.place import Place
from exception import *


class PlaceController(object):
    async def get(self, request):
        try:
            camera_id = int(request.match_info['camera_id'])
            access_token = request.rel_url.query.get('access_token')
            if not access_token:
                raise MissingParameter('access_token')
            account_id = await Account.redis_get_id(request.app['redis'], access_token)
            if account_id is None:
                raise InvalidAccessToken()
            places = await Place.join(Camera, db.and_(Camera.id == Place.camera_id,
                                                      Camera.account_id == account_id))\
                .select()\
                .where(Place.camera_id == camera_id)\
                .gino\
                .model(Place)\
                .all()
            place_json = [{'id': place.id, 'label': place.label, 'status': place.status, 'x': place.x, 'y': place.y}
                          for place in places]
            return aiohttp.web.json_response({'place': place_json})
        except APIException as api_exception:
            raise api_exception
        except:
            raise InternalServerError()

    async def post(self, request):
        try:
            request_data = await request.post()
            camera_id = int(request.match_info['camera_id'])
            access_token = request_data.get('access_token')
            label = request_data.get('label')
            x = request_data.get('x')
            y = request_data.get('y')
            if not access_token:
                raise MissingParameter('access_token')
            if not label:
                raise MissingParameter('label')
            if not x:
                raise MissingParameter('x')
            if not y:
                raise MissingParameter('y')
            if not x.isdigit():
                raise InvalidParameter('x')
            if not y.isdigit():
                raise InvalidParameter('y')
            account_id = await Account.redis_get_id(request.app['redis'], access_token)
            if account_id is None:
                raise InvalidAccessToken()
            user_camera = await db.select([Camera.id])\
                .where(db.and_(Camera.id == camera_id,
                               Camera.account_id == account_id))\
                .gino\
                .model(Camera)\
                .all()
            if not user_camera:
                raise InvalidParameter('camera_id')
            status, result = await Place.update\
                .values(x=int(x), y=int(y))\
                .where(db.and_(Place.camera_id == camera_id,
                               Place.label == label))\
                .gino\
                .status()
            if status == 'UPDATE 0':
                place = await Place.create(camera_id=camera_id, label=label, x=int(x), y=int(y))
            else:
                place = await db.select([Place.id])\
                    .where(db.and_(Place.camera_id == camera_id,
                                   Place.label == label))\
                    .gino\
                    .model(Place)\
                    .first()
            return aiohttp.web.json_response({'status': True, 'id': place.id})
        except APIException as api_exception:
            raise api_exception
        except:
            raise InternalServerError()

    async def delete_by_id(self, request):
        try:
            camera_id = int(request.match_info['camera_id'])
            place_id = int(request.match_info['place_id'])
            request_data = await request.post()
            access_token = request_data.get('access_token')
            if not access_token:
                raise MissingParameter('access_token')
            account_id = await Account.redis_get_id(request.app['redis'], access_token)
            if account_id is None:
                raise InvalidAccessToken()
            status, result = await Place.delete\
                .where(db.and_(Place.id == place_id,
                               Place.camera_id == camera_id,
                               Camera.id == Place.camera_id,
                               Camera.account_id == account_id))\
                .gino\
                .status()
            if status == 'DELETE 0':
                raise InvalidParameter('camera_id or place_id')
            return aiohttp.web.json_response({'status': True})
        except APIException as api_exception:
            raise api_exception
        except:
            raise InternalServerError()
