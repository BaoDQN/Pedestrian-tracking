import cv2
import numpy as np
import os


def convert_img_to_vid(source, out_dir):
    img_array = []
    for i in range(1, len(os.listdir(source))+1):
        if i < 10:
            file = f'00000{i}.jpg'
        elif i < 100:
            file = f'0000{i}.jpg'
        elif i < 1000:
            file = f'000{i}.jpg'
        elif i < 10000:
            file = f'00{i}.jpg'
        img = cv2.imread(os.path.join(source, file))
        height, width, channels = img.shape
        size = (width, height)
        img_array.append(img)
    out = cv2.VideoWriter(os.path.join(out_dir, 'video.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 30, size)
    for i in range(len(img_array)):
        out.write(img_array[i])
    out.release()


convert_img_to_vid('data/results/ByteTrack/MOT17-13-FRCNN/img1', 'data/results/ByteTrack/MOT17-13-FRCNN')
