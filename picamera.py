import time, os, socket, threading, datetime, pytz
from pathlib import Path

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, MJPEGEncoder
from picamera2.outputs import FfmpegOutput

from libcamera import controls

#(1280, 720), (1920, 1080), (2048, 1536), (4608, 2592) (3280, 2464)

class MyCameraPi:
    udpPort = 5600;
    isRecording = False;
    picam2 = None;
    encoder = H264Encoder(17000000) #10000000
    host = None;
    max_size = (4608, 2592)
    min_size = (1920, 1080)
    mode = False; #False: photo, True: video
    
    def __init__(self):
        self.picam2 = Picamera2();
        video_config = self.picam2.create_video_configuration(
                    main   ={"size": (1920, 1080)}, 
                    lores  ={"size": (1280, 720)}, 
                    raw    ={"size": (4608, 2592)}, 
                    controls = {"FrameRate": 10.0},
                    buffer_count = 3
                ); 
        self.picam2.configure(video_config);
        self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        self.picam2.start();
        
    def switch_mode(self, mode):
        if(mode == False and self.mode != mode): #photo
            print("Switch Mode: Photo")
            self.picam2.stop();
            video_config = self.picam2.create_video_configuration(
                    main   ={"size": (1920, 1080)}, 
                    lores  ={"size": (1280, 720)}, 
                    raw    ={"size": (4608, 2592)}, 
                    controls = {"FrameRate": 10.0},
                    buffer_count = 3
                ); 
            self.picam2.configure(video_config);
            self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
            self.picam2.start();
        elif(mode == True and self.mode != mode): #video
            print("Switch Mode: Video")
            self.picam2.stop();
            video_config = self.picam2.create_video_configuration(
                    main   ={"size": (1920, 1080)}, 
                    lores  ={"size": (1280, 720)}, 
                    raw    ={"size": (1920, 1080)}, 
                    controls = {"FrameRate": 50.0},
                    buffer_count = 3
                ); 
            self.picam2.configure(video_config);
            self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
            self.picam2.start();
        
        self.mode = mode;
          
    def take_photo(self):
        self.switch_mode(False);
        filename = "data/"+ self.getTime()# + ".jpg";
        if(self.isRecording == False):
            #self.picam2.start()
            self.picam2.capture_file(filename, name="raw")
            #os.rename(filename + ".dng", filename + ".jpg")
        else:
            request = self.picam2.capture_request()
            request.save("main", filename)
            request.release() 
    
    def start_record_video(self):
        if(self.isRecording == False):
            self.switch_mode(True);
            self.isRecording = True;
            filename = "data/"+ self.getTime() + ".mp4";
            output = FfmpegOutput(filename)
            self.picam2.start_encoder(self.encoder, output, name="main")
        
    def stop_record_video(self):
        if(self.isRecording == True):
            self.isRecording = False;
            self.picam2.stop_encoder(self.encoder)
            
    def change_brightness(self, brightness):
        self.picam2.set_controls({"Brightness": (brightness*2.0)/100 - 1.0})
        
    def change_saturation(self, saturation):
        self.picam2.set_controls({"Saturation": (saturation*32.0)/100})
        
    def change_contrast(self, contrast):
        self.picam2.set_controls({"Contrast": (contrast*32.0)/100})
          
    def zoom(self, cnt):
        max_size = self.picam2.camera_properties['PixelArraySize']
        size = self.picam2.capture_metadata()['ScalerCrop'][2:]
        crop = (max_size[0], max_size[1], max_size[0], max_size[1])
        
        for i in range(cnt):
          size = [int(s * 0.7) for s in size]
          offset = [(r - s) for r, s in zip(max_size, size)]
          print(f"cnt: {cnt}, size: {size}, offset: {offset}")
          crop = (offset[0], offset[1], size[0], size[1])

        self.picam2.set_controls({"ScalerCrop": crop})

        
    def getTime(self):
        VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')
        current_datetime = datetime.datetime.now().astimezone(VN_TZ)
        current_date = current_datetime.strftime("%Y-%m-%d-%H-%M-%S")
        return current_date;
        
    #UDP Stream
    def start_stream_udp(self, host, port):
        url = "-f rtp udp://{}:{}".format(host, port);
        print(f"Start UDP Stream started on {host}:{port}\n")
        self.picam2.start_recording(H264Encoder(), output=FfmpegOutput(url), name="lores"); #H264Encoder(bitrate=10000000)
    
    #TCP Server
    def start_tcp_server(self, host, port):
        server_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_tcp.bind((host, port))
        server_tcp.listen(5)
        print(f"TCP server started on {host}:{port}")
        while True:
            print("Waiting for connection...")
            client_socket, client_addr = server_tcp.accept()
            host, _ = client_addr;
            if(host != self.host):
                self.host = host;
                self.start_stream_udp(self.host, self.udpPort);

            tcpThread = threading.Thread(target=self.handle_client, args=(client_socket, client_addr))
            tcpThread.start()

    def handle_client(self, client_socket, client_addr):
        if(self.isRecording == True):
            data = [0xfe, 0x55, 0x02, 0x02, 0x24, 0x10, 0x02, 0x00, 0x01, 0x25]
            client_socket.sendall(bytes(data))
        elif(self.isRecording == False):
            data = [0xfe, 0x55, 0x02, 0x02, 0x24, 0x10, 0x02, 0x00, 0x00, 0x25]
            client_socket.sendall(bytes(data))
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break;
                
                dataHexa = data.hex(" ");
                self.handle_messgae(client_socket, dataHexa);
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            client_socket.close()
            print(f"Connection with {client_addr} closed")
    
    def handle_messgae(self, client_socket, msg):
        #print(f"msg: {msg}")
        #arr = msg.split(" ")
        
        if(len(msg) >= 26 and msg[0:8] == "fe 55 00"):
            #header = msg[0:8];
            cmdId = msg[9:14];
            status = msg[24:26];
            num = int(msg[15:17], 16)
            print(f"msg: {msg}")
            
            if(cmdId == "02 24" and status == "01"):
                print("Start Video")
                self.start_record_video();
                data = [0xfe, 0x55, 0x02, 0x02, 0x24, num, 0x02, 0x00, 0x01, 0x25]
                client_socket.sendall(bytes(data))
            elif(cmdId == "02 24" and status == "02"):
                print("Stop Video")
                self.stop_record_video();
                data = [0xfe, 0x55, 0x02, 0x02, 0x24, num, 0x02, 0x00, 0x00, 0x25]
                client_socket.sendall(bytes(data))
            elif(cmdId == "01 24" and status == "00"):  
                print("Take Photo");
                self.take_photo();
                data = [0xfe, 0x55, 0x01, 0x01, 0x24, num, 0x02, 0x00, 0x00, 0x25]
                client_socket.sendall(bytes(data))
            elif(cmdId == "04 24"):
                print("Erase TFCard");
                os.system("rm -rf /home/raspi/camera/data/*");
            elif(cmdId == "02 22"):
                zoomLevel = int(msg[21:23], 16)
                self.zoom(zoomLevel);
            
            
#####################################################################################################################
#####################################################################################################################
                  
if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
        
    myCamera = MyCameraPi();
    myCamera.start_tcp_server('0.0.0.0', 5765);
