import cv2

class VideoPreprocessing():

    cap = None
    window_size = 8
    gray = False
    segments = []

    def __init__(self, video_path = None):

        if not video_path:
            raise Exception('ERR: No Video Path Specified.')
        else:
            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                raise Exception('ERR: Invalid Video Path.')

    def setGray(self, gray):

        self.gray = gray

    def getVideoSegments(self):

        segment = []
        count = 0

        while True:

            ret, frame = self.cap.read()
            count += 1

            if not ret:
                break
            
            if self.gray:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # if self.width and self.height:
            # scale_down_factor = 2
            # frame = cv2.resize(frame, None, fx= scale_down_factor, fy= scale_down_factor, interpolation= cv2.INTER_LINEAR)
            frame = cv2.resize(frame, (256, 256))

            segment.append(frame)

            if count % self.window_size == 0:
                self.segments.append(segment)
                segment = []

        return self.segments

