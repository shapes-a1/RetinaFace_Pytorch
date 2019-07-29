import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import skimage
from skimage import io
from PIL import Image
import cv2
import torchvision
import eval_widerface
import model

def pad_to_square(img, pad_value):
    c, h, w = img.shape
    dim_diff = np.abs(h - w)
    # (upper / left) padding and (lower / right) padding
    pad1, pad2 = dim_diff // 2, dim_diff - dim_diff // 2
    # Determine padding
    pad = (0, 0, pad1, pad2) if h <= w else (pad1, pad2, 0, 0)
    # Add padding
    img = F.pad(img, pad, "constant", value=pad_value)

    return img, pad

def resize(image, size):
    image = F.interpolate(image.unsqueeze(0), size=size, mode="nearest").squeeze(0)
    return image

def get_args():
    parser = argparse.ArgumentParser(description="Detect program for retinaface.")
    parser.add_argument('--image_path', type=str, default='test.jpg', help='Path for image to detect')
    parser.add_argument('--model_path', type=str, help='Path for model')
    parser.add_argument('--save_path', type=str, default='./', help='Path for result image')
    parser.add_argument('--depth', help='Resnet depth, must be one of 18, 34, 50, 101, 152', type=int, default=50)
    args = parser.parse_args()

    return args

def main():
    args = get_args()

	# Create the model
    if args.depth == 18:
        RetinaFace = model.resnet18(num_classes=2, pretrained=True)
    elif args.depth == 34:
        RetinaFace = model.resnet34(num_classes=2, pretrained=True)
    elif args.depth == 50:
        RetinaFace = model.resnet50(num_classes=2, pretrained=True)
    elif args.depth == 101:
        RetinaFace = model.resnet101(num_classes=2, pretrained=True)
    elif args.depth == 152:
        RetinaFace = model.resnet152(num_classes=2, pretrained=True)
    else:
        raise ValueError('Unsupported model depth, must be one of 18, 34, 50, 101, 152')

    # Load trained model
    retina_dict = RetinaFace.state_dict()
    pre_state_dict = torch.load(args.model_path)
    pretrained_dict = {k[7:]: v for k, v in pre_state_dict.items() if k[7:] in retina_dict}
    RetinaFace.load_state_dict(pretrained_dict)

    RetinaFace = RetinaFace.cuda()

    # Read image
    img = skimage.io.imread(args.image_path)
    img = torch.from_numpy(img)
    img = img.permute(2,0,1)
    padded_img, _ = pad_to_square(img,0)
    #print('padded img:',padded_img)
    resized_img = resize(padded_img.float(),(640,640))
    input_img = resized_img.unsqueeze(0).cuda()
    picked_boxes, picked_landmarks = eval_widerface.get_detections(input_img, RetinaFace, score_threshold=0.05, iou_threshold=0.3)

    #np_img = resized_img.cpu().numpy()
    np_img = resized_img.cpu().permute(1,2,0).numpy()
    np_img.astype(int)
    img = cv2.cvtColor(np_img.astype(np.uint8),cv2.COLOR_BGR2RGB)

    for j, boxes in enumerate(picked_boxes):
        if boxes is not None:
            for box in boxes:
                cv2.rectangle(img,(box[0],box[1]),(box[2],box[3]),(0,0,255),thickness=2)

    cv2.imshow('test',img)
    cv2.waitKey()





if __name__=='__main__':
    main()