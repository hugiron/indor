import cv2
import time
import argparse
import logging
import requests
import urllib.parse
import imutils
import picamera
import __main__


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='http://localhost:9000', help='Base endpoint for API')
    parser.add_argument('--token', type=str, required=True, help='Client access token for API')
    parser.add_argument('--camera_name', type=str, required=True, help='Unique camera name')
    parser.add_argument('--angle', type=float, default=0, help='The angle of rotation of the frame (from -180 to 180)')
    parser.add_argument('--filename', type=str, default='current_frame.jpg', help='Name of file to save frame')
    return parser.parse_args()


def get_camera_id():
    global args
    url = urllib.parse.urljoin(args.host, '/api/camera')
    params = {
        'access_token': args.token,
        'name': args.camera_name
    }
    response = requests.post(url, data=params).json()
    if 'error' in response:
        raise Exception('API Exception [%d]: %s' % (response['error']['error_code'],
                                                    response['error']['error_message']))
    return response['id']


def send_frame(camera_id):
    global args
    url = urllib.parse.urljoin(args.host, '/api/camera/%d/frame' % camera_id)
    params = {
        'access_token': args.token
    }
    files = {
        'frame': open(args.filename, 'rb')
    }
    response = requests.post(url, data=params, files=files).json()
    if 'error' in response:
        raise Exception('API Exception [%d]: %s' % (response['error']['error_code'],
                                                    response['error']['error_message']))
    return response['next_delay']


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR, filename='%s.log' % __main__.__file__[:-3],
                        format=u'%(filename)s[LINE:%(lineno)d] #%(levelname)s [%(asctime)s] %(message)s')
    args = parse_args()
    camera_id = get_camera_id()

    camera = picamera.PiCamera()
    camera.start_preview()
    next_delay = 0
    while True:
        try:
            camera.capture(args.filename)
            image = imutils.rotate_bound(cv2.imread(args.filename), args.angle)
            cv2.imwrite(args.filename, image)
            next_delay = send_frame(camera_id)
        except Exception as msg:
            logging.error(str(msg))
        finally:
            time.sleep(next_delay)

    camera.stop_preview()