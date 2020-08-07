""" 消除视频最后右下角的残留水印
    问题出现在ffmpeg在根据时长delogo的过程中因为精度问题而导致的水印有残留。
    解决方案：在时长处理那部分额外的加0.2s的时长，超过视频时长总长度也没有关系，会自动delogo到视频最后
"""

import os
import cv2
import glob
import subprocess

ori_video_dir = "video/ori"
new_video_dir = "video/new"
test_video_dir = "video/test"

def secure_remove(path, dst):
    if(path != dst and os.path.exists(path)):
        os.remove(path)

def get_info(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_num = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_num - 1))
    ret, _ = cap.read()
    cap.release()
    print("width:{},  height:{},  fps:{},  frame:{}".format(w, h, fps, frame_num))
    return [w, h, fps, frame_num, ret]


def clip_tail(input_path, output_path, segments_set, info):
    _, _, fps, frame_num, _ = info
    # clip tail segments
    min_pos = frame_num
    for tag, segments in segments_set.items():
        for segment in segments:
            if (segment[3] == 'tail'):
                min_pos = segment[4]
        assert (min_pos < frame_num)

        if (min_pos != frame_num - 1):
            cmd_line = "ffmpeg -i %s -ss 0 -t %.3f -async 1 -c:a aac -max_muxing_queue_size 4096 %s" % (
            input_path, min_pos / fps, output_path)
            subprocess.call(cmd_line, shell=True)
            return True
        else:
            return False


def remove(video_path, segments, output_path, tail_cut=True):
    info = get_info(video_path)
    w, h, fps, frame_num, format_valid = info
    input_path = video_path

    if len(segments.keys()) == 0:
        return 1, segments

    clip_path = output_path + "_clip.mp4"
    to_fps_path = output_path + '_fps.mp4'
    # clip the tail part
    to_delogo_path = input_path
    if (tail_cut and 'tail' in [segment[3] for k in segments.keys() for segment in segments[k]]):
        if (clip_tail(input_path, clip_path, segments, info)):
            to_delogo_path = clip_path

    # ffmpeg remove logo
    print("Delogo doing...")
    delogo_strs = []
    for key, segment_list in segments.items():
        for segment in segment_list:
            bbox, _, wm_type, tail_type, start, end = segment
            if (tail_type != 'inner'):
                continue
            top, bottom, left, right = bbox
            # FFmpeg will delogo by time, but the timestamp we calculated by frame position and fps may be not accurate.
            # So enlarge the time window by one second.
            start = max(0, start - fps)
            # end = min(frame_num, end + fps)

            left = max(1, left)
            top = max(1, top)
            right = min(w - 1, right)
            bottom = min(h - 1, bottom)
            delogo_str = "delogo=x=%d:y=%d:w=%d:h=%d:enable='between(t,%.2f,%.2f)'" % (
            left, top, right - left, bottom - top, float(start) / fps, float(end) / fps+0.2)
            delogo_strs.append(delogo_str)

    # print delogo_strs
    if (len(delogo_strs) > 0):
        cmd_line = 'ffmpeg -i %s -vf "%s,pad=ceil(iw/2)*2:ceil(ih/2)*2" -c:a aac -max_muxing_queue_size 4096 %s' % (
        to_delogo_path, ', '.join(delogo_strs), to_fps_path)

        print(cmd_line)
        subprocess.call(cmd_line, shell=True)
    else:
        to_fps_path = to_delogo_path
    print("Delogo done")
    print("Fps modify doing")
    # modify fps
    cmd_line = "ffmpeg -y -i %s -codec:v copy -codec:a aac -r %f -max_muxing_queue_size 4096 %s" % (
    to_fps_path, fps, output_path)
    subprocess.call(cmd_line, shell=True)
    print("Fps modify done")

    secure_remove(input_path, video_path)
    secure_remove(clip_path, video_path)
    secure_remove(to_delogo_path, video_path)
    secure_remove(to_fps_path, video_path)
    print("remove %s done" % video_path)
    return 0, segments


def delogo(video_name,segments):
    # ori_video_path = os.path.join(ori_video_dir,video_name)
    test_video_path = video_name
    # new_video_path = os.path.join(new_video_dir,video_name)
    new_video_path = os.path.splitext(test_video_path)[0]+"_new"+os.path.splitext(test_video_path)[1]
    print(test_video_path,new_video_path)
    remove(test_video_path, segments, new_video_path,True)


def capture_key_frame(video_path,frame_id):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_num = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    print("{}---{}".format(frame_num, frame_num/fps))


    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    time = frame_id/fps
    ret,frame = cap.read()
    print(time)
    # print(frame)
    cv2.imwrite("key_frame.jpg",frame)
    print("save done")

if __name__ == "__main__":

    # ori_video_list = os.listdir(test_video_dir)
    test_video= glob.glob(os.path.join(test_video_dir,'*.mp4'))[0]
    print(test_video)
    segments = {'snack': [[[0, 53, 0, 184], u'saackuiceo', 'snack', 'inner', 0, 767.475],
                          [[280, 335, 491, 639], u'saackdieeo', 'snack', 'inner', 0, 767.475],
                          [None, None, None, 'tail', 767.475, 846]]}

    capture_key_frame(test_video, 765)
    delogo(test_video, segments)

