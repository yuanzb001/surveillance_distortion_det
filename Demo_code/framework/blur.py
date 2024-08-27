#input: frame
#output: RobertsEdgeMeasure for that frame.

import cv2
import numpy as np

THRESHOLD = 1.5

def roberts_cross_edge(img):
    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    # gray = cv2.GaussianBlur(gray, (7, 7), 0)

    # Compute the Roberts Cross edge map
    Gx = np.array([[1, 0], [0, -1]], dtype=np.float32)
    Gy = np.array([[0, 1], [-1, 0]], dtype=np.float32)
    edge_x = cv2.filter2D(gray, -1, Gx)
    edge_y = cv2.filter2D(gray, -1, Gy)
    edge_map = np.sqrt(np.square(edge_x) + np.square(edge_y))

    # Compute the average edge strength
    avg_edge = np.average(edge_map)

    print(avg_edge)

    return avg_edge


def detect_blur(img):
    edge_measure = roberts_cross_edge(img)
    if edge_measure < THRESHOLD:
        return
    


# import cv2
# import numpy

# THRESHOLD = 150.0 


# def fix_image_size(image: numpy.array, expected_pixels: float = 2E6):
#     ratio = numpy.sqrt(expected_pixels / (image.shape[0] * image.shape[1]))
#     return cv2.resize(image, (0, 0), fx=ratio, fy=ratio)


# def detect_blur(images):
#     res = []
#     for image in images:
#         if image.ndim == 3:
#             image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#         blur_map = cv2.Laplacian(image, cv2.CV_64F)
#         score = numpy.var(blur_map)
#         # print(score)
#         if score < THRESHOLD:
#             res.append(1)
#         else:
#             res.append(0)
#     return res


# def pretty_blur_map(blur_map: numpy.array, sigma: int = 5, min_abs: float = 0.5):
#     abs_image = numpy.abs(blur_map).astype(numpy.float32)
#     abs_image[abs_image < min_abs] = min_abs

#     abs_image = numpy.log(abs_image)
#     cv2.blur(abs_image, (sigma, sigma))
#     return cv2.medianBlur(abs_image, sigma)

