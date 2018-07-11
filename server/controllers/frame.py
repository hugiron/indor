import os
import time
import aiohttp.web
from models import db
from models.account import Account
from models.camera import Camera
from exception import *


class FrameController(object):
    async def get(self, request):
        try:
            camera_id = int(request.match_info['camera_id'])
            frame_path = os.path.join(request.app['config']['path_camera_captures'], 'capture_%d.jpg' % camera_id)
            if not os.path.exists(frame_path):
                raise InvalidParameter('camera_id')
            return aiohttp.web.FileResponse(frame_path)
        except APIException as api_exception:
            raise api_exception
        except:
            raise InternalServerError()

    async def post(self, request):
        try:
            request_data = await request.post()
            camera_id = int(request.match_info['camera_id'])
            access_token = request_data.get('access_token')
            if not access_token:
                raise MissingParameter('access_token')
            account_id = await Account.redis_get_id(request.app['redis'], access_token)
            if account_id is None:
                raise InvalidAccessToken()
            user_camera = await db.select([Camera.delay])\
                .where(db.and_(Camera.id == camera_id,
                               Camera.account_id == account_id))\
                .gino\
                .model(Camera)\
                .all()
            if not user_camera:
                raise InvalidParameter('camera_id')
            frame = request_data.get('frame')
            frame_path = os.path.join(request.app['config']['path_camera_captures'], 'capture_%d.jpg' % camera_id)
            if not frame:
                raise MissingParameter('frame')
            with open(frame_path, 'wb') as frame_file:
                frame_file.write(frame.file.read())
            await Camera.update \
                .values(is_complete=False, last_update=int(time.time())) \
                .where(Camera.id == camera_id) \
                .gino \
                .status()
            return aiohttp.web.json_response({'status': True, 'next_delay': user_camera[0].delay})
        except APIException as api_exception:
            raise api_exception
        except:
            raise InternalServerError()
