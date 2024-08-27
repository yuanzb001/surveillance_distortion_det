from video_preprocessing import VideoPreprocessing
from badlight import detect_badlight
from blur import detect_blur
from camerashake import detect_camerashake
from occlusion import detect_occlusion
import random
from multiprocessing import Process
import pandas as pd
import time
import datetime
from tqdm import tqdm


class MultipleDistortionsDetection():

    def __init__(self, video_segments, duration, framesCount, path):
        self.video_segments = video_segments
        self.duration = duration
        self.framesCount = framesCount
        self.path = path
        self.result = ''


    def getSegmentResult(self, segment):

        st = time.time()
        bl_st = time.time()
        bl_res = detect_badlight(segment)
        bl_et = time.time()

        b_st = time.time()
        blur_res = detect_blur(segment)
        b_et = time.time()

        occ_st = time.time()
        occ_res = detect_occlusion(segment)
        occ_et = time.time()

        cs_st = time.time()
        cs_res = detect_camerashake(segment)
        cs_et = time.time()
        et = time.time()

        # p1 = Process(target=detect_badlight(segment))
        # bl_res = p1.start()
        # p2 = Process(target=detect_blur(segment))
        # blur_res = p2.start()
        # p3 = Process(target=detect_occlusion(segment))
        # occ_res = p3.start()
        # p4 = Process(target=detect_camerashake(segment))
        # cs_res = p4.start()
        
        # p1.join()
        # p2.join()
        # p3.join()
        # p4.join()
        bl_ct = bl_res.count(1)
        blur_ct = blur_res.count(1)
        cs_ct = cs_res.count(1)

        random.seed(23)
        n = random.uniform(0, 10)
        # cs_ct = [random.uniform(0, 5) for i in range(n)]
        t = round(max((b_et - b_st), (bl_et - bl_st), (occ_et - occ_st), (cs_et - cs_st)), 4)
        # Camera Shake: {(cs_ct/len(cs_res))*100.0} %

        if (blur_ct >= 4 and occ_res == 'Yes'):
            # or (bl_ct >= 4 and occ_res == 'Yes')
            occ_res = 'No'

        if (bl_ct == 8 and occ_res == 'Yes'):
            occ_res = 'No'

        res = f'''
        Blur: {(blur_ct/len(blur_res))*100.0 } % and Time Taken: {round(b_et - b_st, 2)} secs
        Bad Light: {(bl_ct/len(bl_res))*100.0} % and Time Taken: {round(bl_et - bl_st, 2)} secs
        Occlusion: {occ_res} and Time Taken: {round(occ_et - occ_st, 2)} secs
        Camera Shake: {(cs_ct/len(cs_res))*100.0} % and Time Taken: {round(cs_et - cs_st, 2)} secs
        Time Taken for this segment: {t} secs
        '''

        print(res)

        # print(et-st)

        return {'blur': blur_res, 'badlight': bl_res, 
                'occlusion': occ_res, 'camerashake': cs_res, 'timet': t}
    
    def getOverallResult(self):
        blur_res = []
        bl_res = []
        occ_res = []
        cs_res = []
        

        i = 1
        n = len(self.video_segments)
        pbar = tqdm(self.video_segments)

        ost = time.time()
        tt = 0
        for segment in pbar:
            pbar.set_description(f'Processing Segment - [ {i}/{n} ]')
            # st = time.time()
            op = self.getSegmentResult(segment)
            tt += op['timet']
            tst = i * ((8/self.framesCount) * self.duration)
            video_time = datetime.timedelta(seconds=tst)
            print(f'End time stamp at video for this segment: {video_time}')

            # print(self.duration, self.framesCount)
            # et = time.time()

            # print(f'time taken for Segment - [ {i}/{n} ]: {et-st}')
            # print(op)

            [blur_res.append(i) for i in op['blur']]
            [bl_res.append(i) for i in op['badlight']]
            occ_res.append(op['occlusion']) 
            [cs_res.append(i) for i in op['camerashake']]
            
            i += 1

        # print(occ_res)
        tmp = 0.0
        # print(len(blur_res), len(bl_res), len(occ_res), len(cs_res))

        bl_ct = bl_res.count(1)
        blur_ct = blur_res.count(1)
        occ_ct = occ_res.count('Yes')
        cs_ct = cs_res.count(1)
        

        # print(occ_ct)
        oet = time.time()
        res = f'''
        ########   Overall Result   ########
        Filename : {self.path}
        Total no.of  Frames: {self.framesCount}
        Video Length: {self.duration} secs
        Blur: {(blur_ct/len(blur_res))*100.0} % and Blurred Frames: {blur_ct}
        Bad Light: {(bl_ct/len(bl_res))*100.0} % and Bad Light Frames: {bl_ct}
        Occlusion: {(occ_ct/len(occ_res))*100.0} % and Occluded Frames: {occ_ct*8}
        Camera Shake: {(cs_ct/len(cs_res))*100.0} % and Camera Shake Frames: {cs_ct}
        Overall Time Taken: {tt} secs
        '''
        # print(et-st)
        print(res)
        outpt = {'filename' : self.path,
        'totalFrames': self.framesCount,
        'videoLength': self.duration,
        'blur': blur_ct,
        'badlight': bl_ct,
        'occlusion': occ_ct*8,
        'camerashake': cs_ct,
        'overallTime': tt}

        self.result = outpt

        return self.result
    

    # def writeLabelVideo(self):

    #     # Initialize the VideoCapture object to read from the video file.
    #     video_reader = cv2.VideoCapture(video_file_path)

    #     # Get the width and height of the video.
    #     original_video_width = int(video_reader.get(cv2.CAP_PROP_FRAME_WIDTH))
    #     original_video_height = int(video_reader.get(cv2.CAP_PROP_FRAME_HEIGHT))

    #     # Initialize the VideoWriter Object to store the output video in the disk.
    #     video_writer = cv2.VideoWriter(output_file_path, cv2.VideoWriter_fourcc('M', 'P', '4', 'V'), 
    #                                 video_reader.get(cv2.CAP_PROP_FPS), (original_video_width, original_video_height))

    #     # Declare a queue to store video frames.
    #     frames_queue = deque(maxlen = SEQUENCE_LENGTH)

    #     # Initialize a variable to store the predicted action being performed in the video.
    #     predicted_class_name = ''

    #     # Iterate until the video is accessed successfully.
    #     while video_reader.isOpened():

    #         # Read the frame.
    #         ok, frame = video_reader.read() 
            
    #         # Check if frame is not read properly then break the loop.
    #         if not ok:
    #             break

    #         # Resize the Frame to fixed Dimensions.
    #         resized_frame = cv2.resize(frame, (IMAGE_HEIGHT, IMAGE_WIDTH))
            
    #         # Normalize the resized frame by dividing it with 255 so that each pixel value then lies between 0 and 1.
    #         normalized_frame = resized_frame / 255

    #         # Appending the pre-processed frame into the frames list.
    #         frames_queue.append(normalized_frame)

    #         # Check if the number of frames in the queue are equal to the fixed sequence length.
    #         if len(frames_queue) == SEQUENCE_LENGTH:

    #             # Pass the normalized frames to the model and get the predicted probabilities.
    #             predicted_labels_probabilities = LRCN_model.predict(np.expand_dims(frames_queue, axis = 0))[0]

    #             # Get the index of class with highest probability.
    #             predicted_label = np.argmax(predicted_labels_probabilities)

    #             # Get the class name using the retrieved index.
    #             predicted_class_name = CLASSES_LIST[predicted_label]

    #         # Write predicted class name on top of the frame.
    #         cv2.putText(frame, predicted_class_name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    #         # Write The frame into the disk using the VideoWriter Object.
    #         video_writer.write(frame)
            
    #     # Release the VideoCapture and VideoWriter objects.
    #     video_reader.release()
    #     video_writer.release()


