#input: frame.
#output: RelativeLuminance value for that frame.

import numpy as np
import cv2
from statistics import mean

THRESHOLD = 0.32


def relativeLuminance(img):
    img = cv2.resize(img, (64,64))
    B, G, R = cv2.split(img)
#     print(B.shape)
    c = 0
    tmp_list = []
    for b,g,r in zip(B,G,R):
        RL = 0
        RL = mean([(p*0.2125) for p in r])/255 + mean([(p*0.715) for p in g])/255 + mean([(p*0.072) for p in b])/255
#         RL = (mean(r)*0.2125 + mean(g)*0.715 + mean(b)*0.072) / 255 
        tmp_list.append(RL)
    return mean(tmp_list)


def detect_badlight(img_arr):
    res = []
    for i in img_arr:
        rl = relativeLuminance(i)
        # print(rl)
        if rl < THRESHOLD:
            res.append(1)
        else:
            res.append(0)
    return res