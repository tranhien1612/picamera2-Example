import time, os, socket, threading, datetime, pytz
from pathlib import Path

import libcamera
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
from libcamera import controls


class MyCameraPi:
    isRecording = False;
    picam2 = None;
    encoder = H264Encoder(10000000)
    size = 0;
    full_res = 0;
    
    def __init__(self):
        self.picam2 = Picamera2();
        video_config = self.picam2.create_video_configuration(main={"size": (1920, 1080)}, lores={"size": (1920, 1080)});
        self.picam2.configure(video_config);
        self.picam2.start();
        self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        
    def __init__(self, host, port):
        self.picam2 = Picamera2();
        video_config = self.picam2.create_video_configuration(main={"size": (1920, 1080)}, lores={"size": (1920, 1080)});
        self.picam2.configure(video_config);
        self.picam2.start();
        self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

        self.start_stream_udp(host, port);
    
    def take_photo(self):
        filename = "data/"+ self.getTime() + ".jpg";
        if(self.isRecording == False):
            self.picam2.start()
            self.picam2.capture_file(filename)
        else:
            request = self.picam2.capture_request()
            request.save("main", filename)
            request.release() 
    
    def start_record_video(self):
        if(self.isRecording == False):
            self.isRecording = True;
            filename = "data/"+ self.getTime() + ".mp4";
            output = FfmpegOutput(filename)
            self.picam2.start_encoder(self.encoder, output, name="main") 
        
    def stop_record_video(self):
        if(self.isRecording == True):
            self.isRecording = False;
            self.picam2.stop_encoder(self.encoder)
    
    def getTime(self):
        VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')
        current_datetime = datetime.datetime.now().astimezone(VN_TZ)
        current_date = current_datetime.strftime("%Y-%m-%d-%H-%M-%S")
        return current_date;
        
    #UDP Stream
    def start_stream_udp(self, host, port):
        url = "-f rtp udp://{}:{}".format(host, port);
        print(f"Start UDP Stream started on {host}:{port}\n")
        self.picam2.start_recording(H264Encoder(), output=FfmpegOutput(url));
    
    #TCP Server
    def start_tcp_server(self, host, port):
        server_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_tcp.bind((host, port))
        server_tcp.listen(5)
        print(f"TCP server started on {host}:{port}")
        while True:
            print("Waiting for connection...")
            client_socket, client_addr = server_tcp.accept()
            tcpThread = threading.Thread(target=self.handle_client, args=(client_socket, client_addr))
            tcpThread.start()

    def handle_client(self, client_socket, client_addr):
        global myCamera;
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
        print(f"msg: {msg}")
        #arr = msg.split(" ")
        
        header = msg[0:8];
        cmdId = msg[9:14];
        status = msg[24:26];
        
        num = int(msg[15:17], 16)
                
        if(len(msg) >= 26):
            if(header == "fe 55 00" and cmdId == "02 24" and status == "01"):
                print("Start Video")
                self.start_record_video();
                data = [0xfe, 0x55, 0x01, 0x02, 0x24, num + 1, 0x02, 0x00, 0x00, 0x25]
                client_socket.sendall(bytes(data))
            elif(header == "fe 55 00" and cmdId == "02 24" and status == "02"):
                print("Stop Video")
                self.stop_record_video();
                data = [0xfe, 0x55, 0x02, 0x02, 0x24, num + 1, 0x02, 0x00, 0x00, 0x25]
                client_socket.sendall(bytes(data))
            elif(header == "fe 55 00" and cmdId == "01 24" and status == "00"):  
                print("Take Photo");
                self.take_photo();
                data = [0xfe, 0x55, 0x02, 0x01, 0x24, num + 1, 0x02, 0x00, 0x00, 0x25] #3header, 2cmd, 1 num, 1 len, data, crc
                client_socket.sendall(bytes(data))
                
            
#####################################################################################################################
#####################################################################################################################
                  
if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
        
    myCamera = MyCameraPi("192.168.1.27", 10001);
    myCamera.start_tcp_server('0.0.0.0', 5765);
