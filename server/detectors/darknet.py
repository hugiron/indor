import os
from ctypes import *


class Object(object):
    __slots__ = ['label', 'accuracy', 'x', 'y', 'width', 'height']

    def __init__(self, label: str, accuracy: float, x: int, y: int, width: int, height: int):
        self.label = label
        self.accuracy = accuracy
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class BOX(Structure):
    _fields_ = [("x", c_float),
                ("y", c_float),
                ("w", c_float),
                ("h", c_float)]


class DETECTION(Structure):
    _fields_ = [("bbox", BOX),
                ("classes", c_int),
                ("prob", POINTER(c_float)),
                ("mask", POINTER(c_float)),
                ("objectness", c_float),
                ("sort_class", c_int)]


class IMAGE(Structure):
    _fields_ = [("w", c_int),
                ("h", c_int),
                ("c", c_int),
                ("data", POINTER(c_float))]


class METADATA(Structure):
    _fields_ = [("classes", c_int),
                ("names", POINTER(c_char_p))]


# TODO: Fix bug with paths in coco.data
class Detector(object):
    __slots__ = ['lib', 'predict', 'set_gpu', 'make_image', 'get_network_boxes', 'free_detections', 'free_ptrs',
                 'network_predict', 'reset_rnn', 'load_net', 'do_nms_obj', 'do_nms_sort', 'free_image',
                 'letterbox_image', 'make_network_boxes', 'load_meta', 'load_image', 'rgbgr_image', 'predict_image',
                 'network', 'meta']

    __install_script__ = ['wget https://github.com/pjreddie/darknet/archive/master.zip',
                          'unzip master && rm master.zip',
                          'mv darknet-master ~/.darknet',
                          'cd ~/.darknet',
                          'make',
                          'wget https://pjreddie.com/media/files/yolov3.weights']

    def __init__(self):
        if not os.path.exists(os.path.expanduser('~/.darknet')):
            os.system(' && '.join(self.__install_script__))
        yolo_config = os.path.expanduser('~/.darknet/cfg/yolov3.cfg')
        coco_config = os.path.expanduser('~/.darknet/cfg/coco.data')
        weights = os.path.expanduser('~/.darknet/yolov3.weights')
        libdarknet = os.path.expanduser('~/.darknet/libdarknet.so')

        self.lib = CDLL(libdarknet, RTLD_GLOBAL)
        self.lib.network_width.argtypes = [c_void_p]
        self.lib.network_width.restype = c_int
        self.lib.network_height.argtypes = [c_void_p]
        self.lib.network_height.restype = c_int

        self.predict = self.lib.network_predict
        self.predict.argtypes = [c_void_p, POINTER(c_float)]
        self.predict.restype = POINTER(c_float)

        self.set_gpu = self.lib.cuda_set_device
        self.set_gpu.argtypes = [c_int]

        self.make_image = self.lib.make_image
        self.make_image.argtypes = [c_int, c_int, c_int]
        self.make_image.restype = IMAGE

        self.get_network_boxes = self.lib.get_network_boxes
        self.get_network_boxes.argtypes = [c_void_p, c_int, c_int, c_float, c_float, POINTER(c_int), c_int, POINTER(c_int)]
        self.get_network_boxes.restype = POINTER(DETECTION)

        self.make_network_boxes = self.lib.make_network_boxes
        self.make_network_boxes.argtypes = [c_void_p]
        self.make_network_boxes.restype = POINTER(DETECTION)

        self.free_detections = self.lib.free_detections
        self.free_detections.argtypes = [POINTER(DETECTION), c_int]

        self.free_ptrs = self.lib.free_ptrs
        self.free_ptrs.argtypes = [POINTER(c_void_p), c_int]

        self.network_predict = self.lib.network_predict
        self.network_predict.argtypes = [c_void_p, POINTER(c_float)]

        self.reset_rnn = self.lib.reset_rnn
        self.reset_rnn.argtypes = [c_void_p]

        self.load_net = self.lib.load_network
        self.load_net.argtypes = [c_char_p, c_char_p, c_int]
        self.load_net.restype = c_void_p

        self.do_nms_obj = self.lib.do_nms_obj
        self.do_nms_obj.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

        self.do_nms_sort = self.lib.do_nms_sort
        self.do_nms_sort.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

        self.free_image = self.lib.free_image
        self.free_image.argtypes = [IMAGE]

        self.letterbox_image = self.lib.letterbox_image
        self.letterbox_image.argtypes = [IMAGE, c_int, c_int]
        self.letterbox_image.restype = IMAGE

        self.load_meta = self.lib.get_metadata
        self.lib.get_metadata.argtypes = [c_char_p]
        self.lib.get_metadata.restype = METADATA

        self.load_image = self.lib.load_image_color
        self.load_image.argtypes = [c_char_p, c_int, c_int]
        self.load_image.restype = IMAGE

        self.rgbgr_image = self.lib.rgbgr_image
        self.rgbgr_image.argtypes = [IMAGE]

        self.predict_image = self.lib.network_predict_image
        self.predict_image.argtypes = [c_void_p, IMAGE]
        self.predict_image.restype = POINTER(c_float)

        self.network = self.load_net(yolo_config.encode('utf-8'), weights.encode('utf-8'), 0)
        self.meta = self.load_meta(coco_config.encode('utf-8'))

    def __call__(self, image, thresh=.5, hier_thresh=.5, nms=.45):
        im = self.load_image(image.encode('utf-8'), 0, 0)
        num = c_int(0)
        pnum = pointer(num)
        self.predict_image(self.network, im)
        dets = self.get_network_boxes(self.network, im.w, im.h, thresh, hier_thresh, None, 0, pnum)
        num = pnum[0]
        self.do_nms_obj(dets, num, self.meta.classes, nms)
        result = []
        for j in range(num):
            for i in range(self.meta.classes):
                if dets[j].prob[i] > 0:
                    box = dets[j].bbox
                    result.append(Object(label=self.meta.names[i].decode('utf-8'),
                                         accuracy=dets[j].prob[i],
                                         x=int(box.x),
                                         y=int(box.y),
                                         width=int(box.w),
                                         height=int(box.h)))
        self.free_image(im)
        self.free_detections(dets, num)
        return result
