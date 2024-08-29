import cv2
import time
import torch
import numpy as np
from statistics import mean
from skimage.feature import hog
from scipy.stats import skew, kurtosis

from bitstream_decode import NAL_unit
from bitstream_decode import sps_unit
from bitstream_decode import pps_unit

import joblib
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

class blur_detector():
    def __init__(self):
        self.blur_detect_model = joblib.load('Demo_code/saved_model/blur_linear_svm_model.joblib')

    def predict_res(self, x_features):
        print('start blur detect!!!!!!!!!!!!!!!!!!!!!!!!!!')

        blur_pred = self.blur_detect_model.predict(x_features)
        return blur_pred

class noise_detector():
    def __init__(self):
        self.noise_detect_model = joblib.load('Demo_code/saved_model/noise_linear_svm_model.joblib')

    def predict_res(self, x_features):
        print('start noise detect!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        noise_pred = self.noise_detect_model.predict(x_features)
        return noise_pred

def occlusion_detect(previous_RL_mean, RL_mean_list, threshold = 0.015):
    RL_mean = np.mean(RL_mean_list)
    change_rate = (previous_RL_mean - RL_mean) / previous_RL_mean
    if abs(change_rate) > threshold:
        return True, RL_mean
    return False, RL_mean

def badlight_detect(RL):
    threshold = 0.32
    if RL > 0.32:
        return False
    else:
        return True

def getRL(image):
    img = cv2.resize(image, (64,64))
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

def getFeatures(image):
    image_features_blur = {}
    image_features_noise = {}
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    _, threshold_image = cv2.threshold(image, 5, 255, cv2.THRESH_BINARY_INV)

    black_area = np.sum(threshold_image == 255)
    total_area = image.shape[0] * image.shape[1]
    black_area_ratio = black_area / total_area

    start_time = time.time()
    # Calculate the gradients
    grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)  # Gradient in x direction
    grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)  # Gradient in y direction
    print('time for calculating gradients:', time.time() - start_time)
    start_time = time.time()

    # Calculate the gradient magnitude and direction
    magnitude = cv2.magnitude(grad_x, grad_y)
    direction = cv2.phase(grad_x, grad_y, angleInDegrees=True)
    print('time for calculating magnitude and direction:', time.time() - start_time)
    start_time = time.time()

    meanGmag = np.mean(magnitude)
    stdGmag = np.std(magnitude)
    meanGdir = np.mean(direction)
    stdGdir = np.std(direction)
    print('time for calculating magnitude and direction features:', time.time() - start_time)
    
    start_time = time.time()

    image_contrast = np.std(image)

    image_features_blur['meanGmag'] = meanGmag
    image_features_blur['stdGmag'] = stdGmag 
    image_features_blur['meanGdir'] = meanGdir
    image_features_blur['stdGdir'] = stdGdir 

    image_features_noise['stdGmag'] = stdGmag 
    image_features_noise['stdGdir'] = stdGdir 
    image_features_noise['image_contrast'] = image_contrast

    return image_features_blur, image_features_noise, black_area_ratio

def RTP_loss(seq_num_list, interval):
    # print('interval: ', interval)
    seq_num_list.sort()
    target_rec_packet = max(seq_num_list) - min(seq_num_list) + interval
    # print('target_rec_packet: ', target_rec_packet)
    packet_loss = target_rec_packet - len(seq_num_list)
    # print('packet_loss: ', packet_loss)
    return packet_loss/target_rec_packet

def P_slice_qp_value_extract(nalu):
    previous_time = time.time()
    pic_init_qp_minus26 = -10000
    nal_unit_obj = NAL_unit(nalu)
    nal_unit_obj.nal_unit()
    # print('decode nalu head: ', time.time() - previous_time)
    # print('nalu type: ', nal_unit_obj.nal_unit_type)
    if nal_unit_obj.nal_unit_type == 7:
        sps_u = sps_unit(nal_unit_obj.rbsp_byte)
        # print(sps_u.seq_parameter_set_id)
        # print(type(sps_u.seq_parameter_set_id))
        # sps_dic[sps_u.seq_parameter_set_id] = sps_u
        # print('Sequence parameter set decode finished!')
    elif nal_unit_obj.nal_unit_type == 8:
        pps_u = pps_unit(nal_unit_obj.rbsp_byte)
        # pps_dic[pps_u.pic_parameter_set_id] = pps_u
        # print('Picture parameter set decode finised!')
        pic_init_qp_minus26 = pps_u.pic_init_qp_minus26
    return pic_init_qp_minus26, nal_unit_obj.nal_unit_type

def alert_detect(frame):
    res = ''
    return res