from video_preprocessing import VideoPreprocessing
from multiple_distortions_detection import MultipleDistortionsDetection
from tqdm import tqdm, trange
import time
import cv2
import datetime
import pandas as pd


if __name__ == '__main__':

    gt_14 = {'blur': 1.41, 'badlight': 2.08, 'occlusion': 2.05, 'camerashake': 1.40}
    gt_3 = {'blur': 4.31, 'badlight': 2.16, 'occlusion': 1.35, 'camerashake': 0.8}
    gt_17 = {'blur': 2.15, 'badlight': 2.16, 'occlusion': 1.36, 'camerashake': 2.0}
    gt_2 = {'blur': 0.85, 'badlight': 2.22, 'occlusion': 2.15, 'camerashake': 1.12}
    gt_15 = {'blur': 1.43, 'badlight': 3.08, 'occlusion': 2.30, 'camerashake': 1.12}
    gt_24 = {'blur': 2.13, 'badlight': 5.01, 'occlusion': 1.0, 'camerashake': 1.45}

    predicted_df = pd.DataFrame()
    actual_df = pd.DataFrame()

    vid_path = r"D:\data\framework\framework_data\a16_24_360p_24.mp4"
    data = cv2.VideoCapture(vid_path)
    
    # count the number of frames
    frames = data.get(cv2.CAP_PROP_FRAME_COUNT)
    # print(frames)
    frames = frames - (frames % 8)

    # print(frames)
    fps = data.get(cv2.CAP_PROP_FPS)
    fps = round(fps)
    # calculate duration of the video
    seconds = round(frames / fps, 2)
    # print(seconds)
    video_time = datetime.timedelta(seconds=seconds)
    # print(f"duration in seconds: {seconds}")
    # print(f"video time: {video_time}")

    vp_obj = VideoPreprocessing(vid_path)
    # vp_obj.setGray(True)
    segs = vp_obj.getVideoSegments()
    count = 0

    mdd = MultipleDistortionsDetection(segs, seconds, frames, vid_path)
    predicted = mdd.getOverallResult()

    tmp_pre = {'blur': predicted['blur'], 
               'badlight': predicted['badlight'], 
               'occlusion': predicted['occlusion'],
               'camerashake': predicted['camerashake']}
    
    tmp_act = {'blur': gt_24['blur']*fps, 
               'badlight': gt_24['badlight']*fps, 
               'occlusion': gt_24['occlusion']*fps,
               'camerashake': gt_24['camerashake']*fps}
    

    predicted_df = pd.concat([predicted_df, pd.DataFrame([tmp_pre])], ignore_index=True)
    actual_df = pd.concat([actual_df, pd.DataFrame([tmp_act])], ignore_index=True)

    print(vid_path)
    print(predicted_df)
    print(actual_df)
