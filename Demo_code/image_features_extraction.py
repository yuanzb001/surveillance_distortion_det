import sys
import cv2
import time
import torch
import numpy as np
from skimage.feature import hog
from scipy.stats import skew, kurtosis

def get_image_RL(image):
    image = image.astype(np.float32) / 255.0
    
    B, G, R = image[:, :, 0], image[:, :, 1], image[:, :, 2]
    
    # 计算相对亮度
    luminance = 0.0722 * B + 0.7152 * G + 0.2126 * R
    
    return np.mean(luminance)

def get_image_magnitude(image):
    # # Calculate the gradients
    # grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)  # Gradient in x direction
    # grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)  # Gradient in y direction

    # # Calculate the gradient magnitude and direction
    # magnitude = cv2.magnitude(grad_x, grad_y)
    # direction = cv2.phase(grad_x, grad_y, angleInDegrees=True)
    
    
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # image_tensor = torch.tensor(image, dtype=torch.float32).to(device)

    # sobel_x = torch.tensor([[[[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]]], dtype=torch.float32).to(device)
    # sobel_y = torch.tensor([[[[-1, -2, -1], [0, 0, 0], [1, 2, 1]]]], dtype=torch.float32).to(device)
    
    # # 计算梯度
    # grad_x = torch.nn.functional.conv2d(image_tensor.view(1, 1, *image_tensor.shape), sobel_x)
    # grad_y = torch.nn.functional.conv2d(image_tensor.view(1, 1, *image_tensor.shape), sobel_y)
    
    # # 计算梯度幅度和方向
    # magnitude = torch.sqrt(grad_x ** 2 + grad_y ** 2).squeeze().cpu().detach().numpy()
    # direction = torch.atan2(grad_y, grad_x).squeeze().cpu().detach().numpy() * 180 / np.pi

    grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
    # magnitude = np.sqrt(grad_x**2 + grad_y**2)
    # direction = np.arctan2(grad_y, grad_x)
    # direction = np.degrees(direction)

    magnitude = cv2.magnitude(grad_x, grad_y)
    direction = cv2.phase(grad_x, grad_y, angleInDegrees=True)

    return magnitude, direction

def get_Features_for_blur(magnitude, direction):
    # Calculate the mean and standard deviation of gradient magnitude and direction
    meanGmag = np.mean(magnitude)
    stdGmag = np.std(magnitude)
    meanGdir = np.mean(direction)
    stdGdir = np.std(direction)

    magnitude_flat = magnitude.flatten()
    direction_flat = direction.flatten()

    # Calculate skewness and kurtosis
    skewGmag = skew(magnitude_flat)
    kurtGmag = kurtosis(magnitude_flat)
    skewGdir = skew(direction_flat)
    kurtGdir = kurtosis(direction_flat)

    image_features = {}
    image_features['meanGmag'] = meanGmag
    image_features['stdGmag'] = stdGmag 
    image_features['meanGdir'] = meanGdir
    image_features['stdGdir'] = stdGdir 
    image_features['skewGmag'] = skewGmag
    image_features['kurtGmag'] = kurtGmag
    image_features['skewGdir'] = skewGdir
    image_features['kurtGdir'] = kurtGdir

    return image_features

def get_Features_of_light(image):
    RL_average = get_image_RL(image)
    return RL_average


def get_Features_for_noise(image):
    image_contrast = np.std(image)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Parameters for HOG descriptor
    # cell_size = (8, 8)  # h x w in pixels
    # block_size = (2, 2)  # cells per block
    # nbins = 9  # number of orientation bins

    original_size = image.shape
    new_size = (original_size[1] // 2, original_size[0] // 2)  # 将图像缩小一半
    resized_image = cv2.resize(image, new_size)

    start_time = time.time()
    print(start_time)
    # resized_image = cv2.resize(image, (64, 128))
    # Calculate HOG features and the HOG image
    # hog_features, hog_image = hog(image,
    #                               orientations=nbins,
    #                               pixels_per_cell=cell_size,
    #                               cells_per_block=block_size,
    #                               block_norm='L2-Hys',
    #                               visualize=True,
    #                               feature_vector=True)

    # winSize = (64, 128)  # 窗口大小
    winSize = new_size
    blockSize = (16, 16)  # 块大小
    blockStride = (8, 8)  # 块步幅
    cellSize = (8, 8)  # 单元格大小
    nbins = 9  # 方向梯度直方图的箱子数量

    # 初始化HOG描述符
    hog = cv2.HOGDescriptor(winSize, blockSize, blockStride, cellSize, nbins)

    # 计算HOG特征
    hog_features = hog.compute(resized_image)

    print(f'calculate hog features time {time.time() - start_time}')
    # Reshape HOG features to blocks
    h, w = resized_image.shape
    print(h, w)
    n_cells = (h // cellSize[0], w // cellSize[1])  # number of cells in image
    n_blocks = (n_cells[0] - int(blockSize[0]/cellSize[0]) + 1, n_cells[1] - int(blockSize[1]/cellSize[1]) + 1)  # number of blocks in image

    # Compute the total number of blocks
    n_total_blocks = n_blocks[0] * n_blocks[1]

    # Reshape HOG features to blocks
    hog_features_reshaped = hog_features.reshape(n_blocks[0], n_blocks[1], int(blockSize[0]/cellSize[0]), int(blockSize[1]/cellSize[1]), nbins)

    # Compute the average frequency (Wm) of each block
    block_averages = np.mean(hog_features_reshaped, axis=(2, 3, 4))  # Averaging over cells and bins
    # Compute the standard deviation (Ws) of each block
    block_stds = np.std(hog_features_reshaped, axis=(2, 3, 4))  # Standard deviation over cells and bins


    hog_mm = np.mean(block_averages)  # Average of block averages
    hog_ms = np.std(block_averages)   # Standard deviation of block averages
    hog_sm = np.mean(block_stds)
    hog_ss = np.std(block_stds)

    image_features = {}
    image_features['hog_mm'] = hog_mm
    image_features['hog_ms'] = hog_ms
    image_features['hog_sm'] = hog_sm
    image_features['hog_ss'] = hog_ss
    image_features['image_contrast'] = image_contrast
    
    return image_features