import sys, os
import cv2
import numpy as np
import skvideo.io

def set_attempt(cap):
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

class FullCapture:
    __cap__ = None
    __is_pbvideo__ = False
    __frames__ = None
    __frame_num__ = None
    __current_pos__ = 0
    
    def __init__(self, video_path, buf_step=0.1):
        self.__cap__ = cv2.VideoCapture(video_path)
        frame_num = self.__cap__.get(cv2.CAP_PROP_FRAME_COUNT)
        self.__cap__.set(cv2.CAP_PROP_POS_FRAMES, frame_num-1)
        ret, _ = self.__cap__.read()

        if(not ret):
            try:
                self.__frames__ = skvideo.io.vread(video_path)
                self.__frame_num__ = self.__frames__.shape[0]
                self.__is_pbvideo__ = True
            except Exception, e:
                raise 
        else:
            self.__cap__.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
    def isOpened(self):
        return ( (self.__is_pbvideo__ and self.__frames__.shape[0] == self.__cap__.get(cv2.CAP_PROP_FRAME_COUNT)) \
                or (not self.__is_pbvideo__ and self.__cap__.isOpened()) )

    def get(self, prop_id):
        if(self.__is_pbvideo__ and prop_id == cv2.CAP_PROP_FRAME_COUNT):
                return self.__frame_num__
        else:
            return self.__cap__.get(prop_id)

    def read(self):
        if(self.__is_pbvideo__):
            if(self.__current_pos__ < 0 or self.__current_pos__ > self.__frame_num__-1):
                return False, None
            else:
                frame = self.__frames__[self.__current_pos__]
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.__current_pos__ += 1
                return True, frame
        else:
            return self.__cap__.read()

    def release(self):
        if(self.__cap__ is not None):
            self.__cap__.release()

class SecureCapture:
    __cap__ = None
    __pos__ = 0
    __is_pbvideo__ = False
    __frames__ = None
    __frame_num__ = None
    
    def __init__(self, video_path, buf_step=0.1):
        self.__cap__ = cv2.VideoCapture(video_path)
        frame_num = self.__cap__.get(cv2.CAP_PROP_FRAME_COUNT)
        self.__cap__.set(cv2.CAP_PROP_POS_FRAMES, frame_num-1)
        ret1, _ = self.__cap__.read()
        self.__cap__.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret2, _ = self.__cap__.read()

        if(not (ret1 and ret2)):
            #self.__frame_num__ = self.get_real_frame_num(self.__cap__)
            #if(self.__frame_num__ <= frame_num - 10):
            # SecureCapture reback to FullCapture
            try:
                print("SKVIDEO reading %s" % video_path)
                self.__frames__ = skvideo.io.vread(video_path)
                self.__frame_num__ = self.__frames__.shape[0]
                self.__is_pbvideo__ = True
            except Exception, e:
                raise 

        self.__cap__.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.__pos__ = 0
            
            
    def get_real_frame_num(self, cap):
        frame_num = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return self.find_fn(cap, 0, frame_num)

    def find_fn(self, cap, start, end):
        if(end - start < 2):
            return start
        pos = (start + end) >> 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, _ = cap.read()
        if(ret):
            return self.find_fn(cap, pos, end)
        else:
            return self.find_fn(cap, start, pos)

    def isOpened(self):
        return ( (self.__is_pbvideo__ and self.__frames__.shape[0] == self.__cap__.get(cv2.CAP_PROP_FRAME_COUNT)) \
                or (not self.__is_pbvideo__ and self.__cap__.isOpened()) )

    def get(self, prop_id):
        if(self.__is_pbvideo__ and prop_id == cv2.CAP_PROP_FRAME_COUNT):
                return self.__frame_num__
        else:
            return self.__cap__.get(prop_id)

    def set_and_read(self, prop_id, pos):
        if(not self.isOpened()):        
            return False, None

        assert(prop_id == cv2.CAP_PROP_POS_FRAMES)
        if(self.__is_pbvideo__):
            frame_id = pos
            assert(frame_id >= 0 and frame_id < self.__frames__.shape[0])
            frame = cv2.cvtColor(self.__frames__[frame_id], cv2.COLOR_BGR2RGB)
            return True, frame
        else:
            self.__cap__.set(cv2.CAP_PROP_POS_FRAMES, pos)
            return self.__cap__.read()

    def read(self):
        if(self.__is_pbvideo__):
            if(self.__pos__ < 0 or self.__pos__ >= self.__frames__.shape[0]):
                return False, None
            else:
                frame = cv2.cvtColor(self.__frames__[self.__pos__], cv2.COLOR_BGR2RGB)
                self.__pos__ += 1
                return True, frame
        else:
            return self.__cap__.read()

    def release(self):
        self.__cap__.release()

if __name__ == '__main__':
    data_dir = "../experiments/temp_video_dir"
    for vname in os.listdir(data_dir):
        if vname != "77312056_432376105.mp4":
            continue
        print vname
        vpath = os.path.join(data_dir, vname)
        cap = SecureCapture(vpath)
        frame_num = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, frame_num // 10)
        for pos in range(step//2, frame_num, step):
            ret, frame = cap.set_and_read(cv2.CAP_PROP_POS_FRAMES, pos)
            if(ret):
                image_dir = os.path.join("./", vname.split(".mp4")[0])
                if(not os.path.exists(image_dir)):
                    os.mkdir(image_dir)
                cv2.imwrite(os.path.join(image_dir, "%05d.png"%pos), frame)
        cap.release()
