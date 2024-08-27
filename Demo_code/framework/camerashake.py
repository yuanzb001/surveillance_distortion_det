import numpy as np
import matplotlib.pyplot as plt
import math
import os
from statistics import mean
import random 

from scipy.spatial.distance import cosine
import cv2


def get_corner_blocks(matrix):
    """
    This function takes a square matrix and returns a list of smaller square matrices
    representing its corner blocks.
    """
    size = len(matrix)
    block_size = size // 2
    blocks = []
    
    # Upper left block
    blocks.append(matrix[:block_size, :block_size])
    
    # Upper right block
    blocks.append(matrix[:block_size, block_size:])
    
    # Lower left block
    blocks.append(matrix[block_size:, :block_size])
    
    # Lower right block
    blocks.append(matrix[block_size:, block_size:])
    
    return blocks

def get_keypoints_and_descriptors(img):
    
    sift = cv2.SIFT_create()
    keypoints, descriptors = sift.detectAndCompute(img,None)
    
    return (keypoints, descriptors)

def get_matches(descriptors_1, descriptors_2):

    matches = None
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(descriptors_1, descriptors_2, k=2)

    # Apply ratio test
    good = None
    if matches is not None and len(matches[0]) > 1:
        good = []
        for m,n in matches:
            if m.distance < 0.75*n.distance:
                good.append(m)
        gmatches = sorted(good, key = lambda x:x.distance)
    else:
        gmatches = good
    
    # print(good[0])
    # print(gmatches[0])
    return gmatches


def get_reference_point(curr_frame, next_frame):
    
    curr_frame_blocks = get_corner_blocks(curr_frame)
    next_frame_blocks = get_corner_blocks(next_frame)

    cfd = []
    reference_points = []
    for corner1, corner2 in zip(curr_frame_blocks, next_frame_blocks):
        matches = None
        curr_keypoints = None
        next_keypoints = None
        curr_descriptors = None
        next_descriptors = None
        curr_keypoints, curr_descriptors = get_keypoints_and_descriptors(corner1)
        next_keypoints, next_descriptors = get_keypoints_and_descriptors(corner2)
#         print(curr_keypoints, next_descriptors)
#         print('-----------------')
#         if curr_keypoints is not None and next_keypoints is not None:
        if curr_descriptors is not None and next_descriptors is not None:
            if curr_keypoints is not None and next_keypoints is not None:
#                 print('kp and desc are there in corner')
                matches = get_matches(curr_descriptors, next_descriptors)
#         print('kp not there.')
                if matches is not None and len(matches) >= 1:
                    if len(matches) == 1:
#                         print('single match')
                        match = matches[0]
                    if len(matches) > 1:
#                         print('multiple matches')
                        # seed_constant = 27
                        # random.seed(seed_constant)
                        match = matches[0]
                    p1 = curr_keypoints[match.queryIdx].pt
                    p2 = next_keypoints[match.trainIdx].pt
                    p1 = (round(p1[0]), round(p1[1]))
                    p2 = (round(p2[0]), round(p2[1]))
                    reference_points.append((p1, p2))
                else:
                    p1 = (-1, -1)
                    p2 = (-1, -1)
                    reference_points.append((p1, p2))
#                     print('no matches')
                    pass
            else:
#                 print('no kps')
                pass
        else:
#             print('no desc')
            pass
    return reference_points


def get_direction(points_list):
    if len(points_list) == 4:
        first_corner = points_list[0]
        sec_corner = points_list[1]
        third_corner = points_list[2]
        fourth_corner = points_list[3]


        if first_corner[0][0] == first_corner[1][0] and sec_corner[0][0] == sec_corner[1][0] and third_corner[0][0] == third_corner[1][0] and fourth_corner[0][0] == fourth_corner[1][0]:
            return 'no_shake'
        elif first_corner[0][1] < first_corner[1][1] and sec_corner[0][1] == sec_corner[1][1] and third_corner[0][1] == third_corner[1][1] and fourth_corner[0][1] == fourth_corner[1][1]:
            return 'shake'      
        elif first_corner[0][0] < first_corner[1][0] and sec_corner[0][0] < sec_corner[1][0] and third_corner[0][0] < third_corner[1][0] and fourth_corner[0][0] < fourth_corner[1][0]:
            return 'left'
        elif first_corner[0][0] > first_corner[1][0] and sec_corner[0][0] > sec_corner[1][0] and third_corner[0][0] > third_corner[1][0] and fourth_corner[0][0] > fourth_corner[1][0]:
            return 'right'
        elif first_corner[0][1] < first_corner[1][1] and sec_corner[0][1] < sec_corner[1][1] and third_corner[0][1] < third_corner[1][1] and fourth_corner[0][1] < fourth_corner[1][1]:
            return 'up'
        elif first_corner[0][1] > first_corner[1][1] and sec_corner[0][1] > sec_corner[1][1] and third_corner[0][1] > third_corner[1][1] and fourth_corner[0][1] > fourth_corner[1][1]:
            return 'down'
        else:
            return 'shake'
    else:
#         print('no enough pts.')
        return 'shake'
    
def detect_camerashake(images):
    images = [cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) for image in images]
    # images = [cv2.resize(img, (64,64)) for img in images]
    # print(len(images))
    medianFrame = np.median(images, axis=0).astype(dtype=np.uint8) 
    res = []
    for i in range(0, len(images)-4):
    #     print(i)
        ps = get_reference_point(images[i], images[i+1])
        ps1 = get_reference_point(images[i+2], images[i+3])
        # ps = get_reference_point(images[i], medianFrame)
        # ps1 = get_reference_point(images[i+1], medianFrame)
    #     print(ps, ps1)
    #     print('-----------------------')
        r1 = get_direction(ps)
        r2 = get_direction(ps1)
        if (r1 == r2) and (r1 != 'shake' or r2 != 'shake'):
            res.append(0)
        elif r1 == 'no_shake' or r2 == 'no_shake':
            res.append(0)
        else:
            res.append(1)

    return res