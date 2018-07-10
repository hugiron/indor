import asyncio
import aiohttp
import argparse
import gino
import time
import random
import logging
import uvloop
import urllib.parse
from sqlalchemy.engine.url import URL
import config
from detectors.darknet import Detector
from models import db
from models.camera import Camera
from models.place import Place


def parse_args():
    parser = argparse.ArgumentParser()
    # TODO: Add helpers!!!
    parser.add_argument('--yolo_config', type=str, default='darknet/cfg/yolov3.cfg', help='')
    parser.add_argument('--coco_config', type=str, default='darknet/cfg/coco.data', help='')
    parser.add_argument('--weights', type=str, default='darknet/yolo.weights', help='')
    parser.add_argument('--libdarknet', type=str, default='darknet/libdarknet.so', help='')
    parser.add_argument('--host', type=str, default='http://localhost:9000', help='Base endpoint for API')
    parser.add_argument('--delay', type=int, default=1, help='Delay in the absence of new frames in the database')
    parser.add_argument('--filename', type=str, default='current_frame.jpg', help='Name of file to save frame')
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


async def get_camera_id(detector_id):
    camera_id_query = db.select([Camera.id]) \
        .order_by(Camera.last_update.asc()) \
        .where(db.and_(Camera.detector_id == 0,
                       Camera.status == True,
                       Camera.is_complete == False)) \
        .limit(1)
    status, result = await Camera.update \
        .values(detector_id=detector_id) \
        .where(Camera.id == camera_id_query) \
        .gino \
        .status()
    if status == 'UPDATE 0':
        return None
    camera = await db.select([Camera.id])\
        .where(db.and_(Camera.detector_id == detector_id,
                       Camera.is_complete == False))\
        .gino\
        .model(Camera)\
        .first()
    return camera.id


async def get_places(camera_id):
    places = await db.select([Place])\
        .where(Place.camera_id == camera_id)\
        .gino\
        .model(Place)\
        .all()
    return places


async def download_frame(camera_id):
    url = urllib.parse.urljoin(args.host, '/api/camera/%d/frame' % camera_id)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if 'application/json' in response.headers.get('content-type'):
                json = await response.json()
                raise Exception('API Exception [%d]: %s' % (json['error']['error_code'],
                                                            json['error']['error_message']))
            elif 'image/jpeg' in response.headers.get('content-type'):
                with open(args.filename, 'wb') as frame_file:
                    frame_content = await response.content.read()
                    frame_file.write(frame_content)
            else:
                raise Exception('An unknown content-type is received')


async def main():
    await init_connections()
    detector_id = random.randint(1, 2 ** 24)
    detector = Detector(yolo_config=args.yolo_config,
                        coco_config=args.coco_config,
                        weights=args.weights,
                        libdarknet=args.libdarknet)
    logging.basicConfig(level=logging.ERROR, filename='%s::%d.log' % (__main__.__file__[:-3], detector_id),
                        format=u'%(filename)s[LINE:%(lineno)d] #%(levelname)s [%(asctime)s] %(message)s')

    while True:
        try:
            camera_id = await get_camera_id(detector_id=detector_id)
            if camera_id is None:
                await asyncio.sleep(args.delay)
                continue
            places = await get_places(camera_id=camera_id)
            await download_frame(camera_id=camera_id)
            objects = detector(image=args.filename)
            dist = [((obj.x - place.x) ** 2 + (obj.y - place.y) ** 2, obj, place)
                    for obj in objects for place in places]
            dist.sort(key=lambda x: x[0])
            used = set()
            values = dict()
            for place in places:
                values[place.id] = False
            for d, obj, place in dist:
                if (obj.x, obj.y) in used:
                    continue
                if (obj.x - obj.width // 2) <= place.x <= (obj.x + obj.width // 2) and \
                        (obj.y - obj.height // 2) <= place.y <= (obj.y + obj.height // 2):
                    used.add((obj.x, obj.y))
                    values[place.id] = True
            async with db.transaction() as tx:
                for place in places:
                    if place.status != values[place.id]:
                        await Place.update \
                            .values(status=values[place.id]) \
                            .where(Place.id == place.id) \
                            .gino \
                            .status()
                await Camera.update\
                    .values(is_complete=True, detector_id=0, last_update=int(time.time()))\
                    .where(Camera.id == camera_id)\
                    .gino\
                    .status()
        except Exception as msg:
            logging.error(str(msg))


if __name__ == '__main__':
    args = parse_args()
    # Использование UVLoop в качестве цикла событий по-умолчанию
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.get_event_loop().run_until_complete(main())
