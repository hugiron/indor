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


class IMAGE(Structure):
    _fields_ = [("w", c_int),
                ("h", c_int),
                ("c", c_int),
                ("data", POINTER(c_float))]


class METADATA(Structure):
    _fields_ = [("classes", c_int),
                ("names", POINTER(c_char_p))]


class Detector(object):
    __slots__ = ['lib', 'make_boxes', 'free_ptrs', 'num_boxes', 'make_probs', 'load_net', 'free_image', 'load_meta',
                 'load_image', 'network_detect', 'network', 'meta']

    __install_script__ = ['wget https://github.com/pjreddie/darknet/archive/master.zip',
                          'unzip master && rm master.zip',
                          'mv darknet-master ~/.darknet',
                          'cd ~/.darknet',
                          'make',
                          'wget https://pjreddie.com/media/files/yolov3.weights']

    def __init__(self):
        if not os.path.exists('~/.darknet'):
            os.system(' && '.join(self.__install_script__))
        yolo_config = '~/.darknet/cfg/yolov3.cfg'
        coco_config = '~/.darknet/cfg/coco.data'
        weights = '~/.darknet/yolov3.weights'
        libdarknet = '~/.darknet/libdarknet.so'

        self.lib = CDLL(libdarknet, RTLD_GLOBAL)
        self.lib.network_width.argtypes = [c_void_p]
        self.lib.network_width.restype = c_int
        self.lib.network_height.argtypes = [c_void_p]
        self.lib.network_height.restype = c_int

        self.make_boxes = self.lib.make_boxes
        self.make_boxes.argtypes = [c_void_p]
        self.make_boxes.restype = POINTER(BOX)

        self.free_ptrs = self.lib.free_ptrs
        self.free_ptrs.argtypes = [POINTER(c_void_p), c_int]

        self.num_boxes = self.lib.num_boxes
        self.num_boxes.argtypes = [c_void_p]
        self.num_boxes.restype = c_int

        self.make_probs = self.lib.make_probs
        self.make_probs.argtypes = [c_void_p]
        self.make_probs.restype = POINTER(POINTER(c_float))

        self.load_net = self.lib.load_network
        self.load_net.argtypes = [c_char_p, c_char_p, c_int]
        self.load_net.restype = c_void_p

        self.free_image = self.lib.free_image
        self.free_image.argtypes = [IMAGE]

        self.load_meta = self.lib.get_metadata
        self.lib.get_metadata.argtypes = [c_char_p]
        self.lib.get_metadata.restype = METADATA

        self.load_image = self.lib.load_image_color
        self.load_image.argtypes = [c_char_p, c_int, c_int]
        self.load_image.restype = IMAGE

        self.network_detect = self.lib.network_detect
        self.network_detect.argtypes = [c_void_p, IMAGE, c_float, c_float, c_float, POINTER(BOX),
                                        POINTER(POINTER(c_float))]

        self.network = self.load_net(yolo_config.encode('utf-8'), weights.encode('utf-8'), 0)
        self.meta = self.load_meta(coco_config.encode('utf-8'))

    def __call__(self, image, thresh=.5, hier_thresh=.5, nms=.45):
        im = self.load_image(image.encode('utf-8'), 0, 0)
        boxes = self.make_boxes(self.network)
        probs = self.make_probs(self.network)
        num = self.num_boxes(self.network)
        self.network_detect(self.network, im, thresh, hier_thresh, nms, boxes, probs)
        result = []
        for j in range(num):
            for i in range(self.meta.classes):
                if probs[j][i] > 0:
                    result.append(Object(label=self.meta.names[i].decode('utf-8'),
                                         accuracy=probs[j][i],
                                         x=int(boxes[j].x),
                                         y=int(boxes[j].y),
                                         width=int(boxes[j].w),
                                         height=int(boxes[j].h)))
        self.free_image(im)
        self.free_ptrs(cast(probs, POINTER(c_void_p)), num)
        return result
