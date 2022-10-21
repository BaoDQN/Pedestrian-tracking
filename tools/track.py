import argparse
import os
import sys
import os.path as osp
import pandas as pd

import torch

ROOT = os.getcwd()
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from yolov6.utils.events import LOGGER
from yolov6.core.tracker import Tracker


def get_args_parser(add_help=True):
    parser = argparse.ArgumentParser(description='YOLOv6 PyTorch Inference.', add_help=add_help)
    parser.add_argument('--weights', type=str, default='weights/yolov6n.pt', help='model path(s) for inference.')
    parser.add_argument('--source', type=str, default='data/images', help='the source path, e.g. image-file/dir.')
    parser.add_argument('--yaml', type=str, default='data/coco.yaml', help='data yaml file.')
    parser.add_argument('--img-size', nargs='+', type=int, default=[640, 640], help='the image-size(h,w) in inference size.')
    parser.add_argument('--conf-thres', type=float, default=0.4, help='confidence threshold for inference.')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold for inference.')
    parser.add_argument('--max-det', type=int, default=1000, help='maximal inferences per image.')
    parser.add_argument('--device', default='cpu', help='device to run our model i.e. 0 or 0,1,2,3 or cpu.')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt.')
    parser.add_argument('--save-img', action='store_false', help='save visuallized inference results.')
    parser.add_argument('--save-dir', type=str, help='directory to save predictions in. See --save-txt.')
    parser.add_argument('--view-img', action='store_true', help='show inference results')
    parser.add_argument('--classes', nargs='+', default=0, type=int, help='filter by classes, e.g. --classes 0, or --classes 0 2 3.')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS.')
    parser.add_argument('--project', default='runs/inference', help='save inference results to project/name.')
    parser.add_argument('--name', default='exp', help='save inference results to project/name.')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels.')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences.')
    parser.add_argument('--half', action='store_true', help='whether to use FP16 half-precision inference.')
    parser.add_argument('--track-method', type=str, default='SORT', help='method for tracking, default is SORT')
    parser.add_argument('--evaluation', type=bool, default=False, help='run evaluation or not')
    parser.add_argument("--track_thresh", type=float, default=0.4, help="threshold of detection to be tracked")
    parser.add_argument("--track_buffer", type=int, default=30, help="the frames for keep lost tracks for ByteTrack")
    parser.add_argument("--match_thresh", type=float, default=0.8, help="matching threshold for tracking for ByteTrack")
    parser.add_argument("--mot20", dest="mot20", default=False, action="store_true", help="test mot20.")

    args = parser.parse_args()
    LOGGER.info(args)
    return args


@torch.no_grad()
def run(weights='weights/yolov6n.pt',
        source=osp.join(ROOT, 'data/images'),
        yaml=None,
        img_size=640,
        conf_thres=0.4,
        iou_thres=0.45,
        max_det=1000,
        device='cpu',
        save_txt=False,
        save_img=True,
        save_dir=None,
        view_img=True,
        classes=None,
        agnostic_nms=False,
        project=osp.join(ROOT, 'runs/tracking'),
        name='exp',
        hide_labels=False,
        hide_conf=False,
        half=False,
        track_method='SORT',
        evaluation=False,
        track_thresh=0.5,
        track_buffer=30,
        match_thresh=0.8,
        mot20=False,
        ):
    """ Inference process, supporting inference on one image file or directory which containing images.
    Args:
        weights: The path of model.pt, e.g. yolov6n.pt
        source: Source path, supporting image files or dirs containing images.
        yaml: Data yaml file, .
        img_size: Inference image-size, e.g. 640
        conf_thres: Confidence threshold in inference, e.g. 0.25
        iou_thres: NMS IOU threshold in inference, e.g. 0.45
        max_det: Maximal detections per image, e.g. 1000
        device: Cuda device, e.e. 0, or 0,1,2,3 or cpu
        save_txt: Save results to *.txt
        save_img: Save visualized inference results
        classes: Filter by class: --class 0, or --class 0 2 3
        agnostic_nms: Class-agnostic NMS
        project: Save results to project/name
        name: Save results to project/name, e.g. 'exp'
        line_thickness: Bounding box thickness (pixels), e.g. 3
        hide_labels: Hide labels, e.g. False
        hide_conf: Hide confidences
        half: Use FP16 half-precision inference, e.g. False
    """
    # create save dir
    if save_dir is None:
        save_dir = osp.join(project, name)
        save_txt_path = osp.join(save_dir, 'labels')
    else:
        save_txt_path = save_dir
    if (save_img or save_txt) and not osp.exists(save_dir):
        os.makedirs(save_dir)
    else:
        LOGGER.warning('Save directory already existed')
    if save_txt:
        save_txt_path = osp.join(save_dir, 'labels')
        if not osp.exists(save_txt_path):
            os.makedirs(save_txt_path)

    # # Inference
    # inferer = Inferer(source, weights, device, yaml, img_size, half)
    # inferer.infer(conf_thres, iou_thres, classes, agnostic_nms, max_det, save_dir, save_txt, save_img, hide_labels, hide_conf, view_img)

    # Tracking
    tracker = Tracker(source, weights, device, yaml, img_size, half, evaluation)
    if evaluation:
        summary, fps = tracker.track(conf_thres, iou_thres, classes, agnostic_nms, max_det, track_method, save_dir, save_txt, save_img, hide_labels,
              hide_conf, view_img, track_thresh, track_buffer, match_thresh, mot20)
        # write to file
        summary['fps'] = fps
        summary['idf1'] *= 100
        summary['idp'] *= 100
        summary['idr'] *= 100
        summary['recall'] *= 100
        summary['precision'] *= 100
        summary['mota'] *= 100
        summary['motp'] = (1 - summary['motp'])*100
        summary.to_csv(os.path.join(save_dir, f'{source.split("/")[-1]}_performance.csv'))
    else:
        tracker.track(conf_thres, iou_thres, classes, agnostic_nms, max_det, track_method, save_dir, save_txt, save_img,
                      hide_labels, hide_conf, view_img, track_thresh, track_buffer, match_thresh, mot20)

    if save_txt or save_img:
        LOGGER.info(f"Results saved to {save_dir}")


def main(args):
    run(**vars(args))


if __name__ == "__main__":
    args = get_args_parser()
    main(args)
