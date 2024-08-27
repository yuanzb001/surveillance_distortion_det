import cv2
import time
from PIL import Image
import easyocr

def getTextfromFrame(frame_pic, detect_threshold = 0.5):
    start_time = time.time()
    gray = cv2.cvtColor(frame_pic, cv2.COLOR_BGR2GRAY)

    blurred_img_2 = cv2.GaussianBlur(gray, (5,5), 0)
    print('time for image blur: ', time.time() - start_time)
    start_time = time.time()
    # _2, binary_2 = cv2.threshold(blurred_img_2, thresh = 0, maxval = 255, type=cv2.THRESH_OTSU)

    reader = easyocr.Reader(['en'])
    print('time for easyocr Reader initial: ', time.time() - start_time)
    start_time = time.time()
    # image_PIL = Image.open('error_blackback.png')
    re_forCrop = reader.readtext(blurred_img_2)
    print(re_forCrop)
    print('time for text detect: ', time.time() - start_time)
    start_time = time.time()
    # start_pos_flag = False
    # x_start, y_start = 0, 0
    # x_end, y_end = 0, 0
    # for element in re_forCrop:
    #     pos_info = element[0]
    #     text = element[1]
    #     confidence = element[2]
    #     for pos in pos_info:
    #         if not start_pos_flag:
    #             x_start = x_end = pos[0]
    #             y_start = y_end = pos[1]
    #             start_pos_flag = True
    #         else:
    #             if pos[0] < x_start:
    #                 x_start = pos[0]
    #             elif pos[0] > x_end:
    #                 x_end = pos[0]
    #             if pos[1] < y_start:
    #                 y_start = pos[1]
    #             elif pos[1] > y_end:
    #                 y_end = pos[1]

    # print(y_start, y_end, x_start, x_end)

    # cropped_image = frame_pic[int(y_start):int(y_end), int(x_start):int(x_end)]
    # cropped_image_gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)

    # blurred_img_2 = cv2.GaussianBlur(cropped_image_gray, (3,3), 0)

    # _2, binary_2 = cv2.threshold(blurred_img_2, thresh = 0, maxval = 255, type=cv2.THRESH_OTSU)

    # img_pil = Image.fromarray(cv2.cvtColor(binary_2, cv2.COLOR_BGR2RGB))
    # re = reader.readtext(binary_2)
    # print(re)
    text_tmp_backup = []
    score_tmp_backup = []
    for element in re_forCrop:
        if element[2] > detect_threshold:
            text_tmp_backup.append(element[1])
            score_tmp_backup.append(element[2])
    print('time for result filter: ', time.time() - start_time)
    start_time = time.time()
    
    return text_tmp_backup, score_tmp_backup

def getHighestScore(text_list, score_list):
    # max_score = score_list[0]
    # best_text = text_list[0]
    # for index in range(len(score_list)):
    #     if score_list[index] > max_score:
    #         max_score = score_list[index]
    #         best_text = text_list[index]
    # return best_text, max_score
    best_text_list = text_list[0]
    max_score_list = score_list[0]
    for index in range(len(score_list)):
        for item_index in range(len(score_list[index])):
            if item_index >= len(best_text_list):
                best_text_list.append(text_list[index][item_index])
                max_score_list.append(score_list[index][item_index])
            else:
                if max_score_list[item_index] < score_list[index][item_index]:
                    best_text_list[item_index] = text_list[index][item_index]
                    max_score_list[item_index] = score_list[index][item_index]
    return best_text_list, max_score_list

# def getHighestfrequency(text_list, score_list):
#     for index in range(len(text_list)):


