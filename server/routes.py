from aiohttp.web import route
from controllers import *


camera_controller = CameraController()
frame_controller = FrameController()
status_controller = StatusController()
place_controller = PlaceController()
parking_controller = ParkingController()

routes = [
    route('GET', r'/api/camera', camera_controller.get),
    route('POST', r'/api/camera', camera_controller.post),
    route('GET', r'/api/camera/{camera_id:\d+}/frame', frame_controller.get),
    route('POST', r'/api/camera/{camera_id:\d+}/frame', frame_controller.post),
    route('GET', r'/api/camera/{camera_id:\d+}/status', status_controller.get),
    route('POST', r'/api/camera/{camera_id:\d+}/status', status_controller.post),
    route('GET', r'/api/camera/{camera_id:\d+}/place', place_controller.get),
    route('POST', r'/api/camera/{camera_id:\d+}/place', place_controller.post),
    route('DELETE', r'/api/camera/{camera_id:\d+}/place/{place_id:\d+}', place_controller.delete_by_id),
    route('GET', r'/api/parking', parking_controller.get),
    route('GET', r'/api/parking/{parking_id:\d+}', parking_controller.get_by_id)
]
