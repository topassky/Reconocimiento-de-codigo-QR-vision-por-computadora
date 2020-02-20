# USAGE
# python webstreaming.py --ip 0.0.0.0 --port 8000

# import the necessary packages
from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import datetime
import imutils
import time
import cv2
from os import scandir, getcwd,system
import os
#import psycopg2
#import zbar
from pyzbar import pyzbar
#import MySQLdb
import csv 


outputFrame = None
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__)

vs = cv2.VideoCapture(0)
time.sleep(2.0)

@app.route("/")
def index():
	# return the rendered template
	return render_template("index.html")

def detect_motion(frameCount):

	global vs, outputFrame, lock, cur, conn


	contador = 1
	barcodeold = " 1 "
	lista_Barcode = [[]]

	while True:

		(grabbed, frame) = vs.read()
		status = "No QR"
		
		if not grabbed:
			break    
        
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		blurred = cv2.GaussianBlur(gray, (7, 7), 0)
		edged = cv2.Canny(blurred, 50, 150)
		cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)
		
		for c in cnts:
			peri = cv2.arcLength(c, True)
			approx = cv2.approxPolyDP(c, 0.01 * peri, True)
			if len(approx) >= 4 and len(approx) <= 6:
				(x, y, w, h) = cv2.boundingRect(approx)
				aspectRatio = w / float(h)
				area = cv2.contourArea(c)
				hullArea = cv2.contourArea(cv2.convexHull(c))
				solidity = area / float(hullArea)
				
				keepDims = w > 25 and h > 25
				keepSolidity = solidity > 0.9
				keepAspectRatio = aspectRatio >= 0.8 and aspectRatio <= 1.2
				
				if keepDims and keepSolidity and keepAspectRatio:
					cv2.drawContours(frame, [approx], -1, (0, 0, 255), 2)
					contador += 1
					roi = frame[y:y + h, x:x + w]
					cv2.imwrite(getcwd()+'/basura/image'+str(contador)+'.png',roi)
					
					if contador == 10:
						ruta = getcwd()+"/basura/"
						directorio = [arch.name for arch in scandir(ruta) if arch.is_file()]
						for image in directorio:
							image = cv2.imread(getcwd()+"/basura/"+image) 
							barcodes = pyzbar.decode(image)
							for barcode in barcodes:
								(x, y, w, h) = barcode.rect
								cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
								barcodeData = barcode.data.decode("utf-8")
								barcodeType = barcode.type
								status = "{} ({})".format(barcodeData, barcodeType)
								if (status == "No QR"):
									continue
								else:
									status = "{} ({})".format(barcodeData, barcodeType)
									#print("El codigo QR contiene {} ".format(status))
									if (barcodeold != str(barcodeData)):
										lista_Barcode[0].append (str(barcodeData))
										
										print(lista_Barcode)
										with open ('/home/felipe/Escritorio/Django/paginaProyectoQR/ejemplo/AwsDemo/services/codigoQR.csv', 'w', newline='')as file:
											writer = csv.writer(file)
											writer.writerows(lista_Barcode)
										print('lo hice')
										barcodeold=str(barcodeData)
										lista_Barcode[0][:]=[]
										
									else:
										continue

						contador = 0
						
		# grab the current timestamp and draw it on the frame
		timestamp = datetime.datetime.now()
		cv2.putText(frame, timestamp.strftime(
			"%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
			cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        
        

		with lock:
			outputFrame = frame.copy()
		
def generate():
	# grab global references to the output frame and lock variables
	global outputFrame, lock

	# loop over frames from the output stream
	while True:
		# wait until the lock is acquired
		with lock:
			# check if the output frame is available, otherwise skip
			# the iteration of the loop
			if outputFrame is None:
				continue

			# encode the frame in JPEG format
			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

			# ensure the frame was successfully encoded
			if not flag:
				continue

		# yield the output frame in the byte format
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
	# return the response generated along with the specific media
	# type (mime type)
	return Response(generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")

# check to see if this is the main thread of execution
if __name__ == '__main__':
	# construct the argument parser and parse command line arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--ip", type=str, required=True,
		help="ip address of the device")
	ap.add_argument("-o", "--port", type=int, required=True,
		help="ephemeral port number of the server (1024 to 65535)")
	ap.add_argument("-f", "--frame-count", type=int, default=32,
		help="# of frames used to construct the background model")
	args = vars(ap.parse_args())

	# start a thread that will perform motion detection
	t = threading.Thread(target=detect_motion, args=(
		args["frame_count"],))
	t.daemon = True
	t.start()

	# start the flask app
	app.run(host=args["ip"], port=args["port"], debug=True,
		threaded=True, use_reloader=False)

# release the video stream pointer
cur.close()
conn.close()
vs.stop()
