# import the necessary packages
import argparse
import imutils
import cv2
from os import scandir, getcwd
import zbar
from pyzbar import pyzbar
# import the necessary packages
#import argparse
#import imutils
#import cv2
 
# construct the argument parse and parse the arguments
#ap = argparse.ArgumentParser()
#ap.add_argument("-v", "--video", help="path to the video file")
#args = vars(ap.parse_args())
 
# load the video
#camera = cv2.VideoCapture(args["video"])
camera = cv2.VideoCapture(0)
contador = 1
while True:
	# grab the current frame and initialize the status text
	(grabbed, frame) = camera.read()
	status = "No QR"
 
	# check to see if we have reached the end of the
	# video
	if not grabbed:
		break
 
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


	blurred = cv2.GaussianBlur(gray, (7, 7), 0)
	edged = cv2.Canny(blurred, 50, 150)

    # find contours in the edge map
	cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)

    # loop over the contours
	for c in cnts:
    # approximate the contour
		peri = cv2.arcLength(c, True)
		approx = cv2.approxPolyDP(c, 0.01 * peri, True)
    
        # ensure that the approximated contour is "roughly" rectangular
		if len(approx) >= 4 and len(approx) <= 6:
            # compute the bounding box of the approximated contour and
            # use the bounding box to compute the aspect ratio
			(x, y, w, h) = cv2.boundingRect(approx)
			aspectRatio = w / float(h)
    
            # compute the solidity of the original contour
			area = cv2.contourArea(c)
			hullArea = cv2.contourArea(cv2.convexHull(c))
			solidity = area / float(hullArea)
    
            # compute whether or not the width and height, solidity, and
            # aspect ratio of the contour falls within appropriate bounds
			keepDims = w > 25 and h > 25
			keepSolidity = solidity > 0.9
			keepAspectRatio = aspectRatio >= 0.8 and aspectRatio <= 1.2
    
            # ensure that the contour passes all our tests
			if keepDims and keepSolidity and keepAspectRatio:
                # draw an outline around the target and update the status
                # text
                
				cv2.drawContours(frame, [approx], -1, (0, 0, 255), 2)
				#image = frame[y:y + h, x:x + w]
				#status = "QR"
				contador += 1
    
				roi = frame[y:y + h, x:x + w]
				cv2.imwrite(getcwd()+'/basura/image'+str(contador)+'.png',roi)

				
				if contador == 10:
					ruta = getcwd()+"/basura/"
					directorio = [arch.name for arch in scandir(ruta) if arch.is_file()]
					#print(directorio)
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
								print("El codigo QR contiene {} ".format(status))

					contador = 0

	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF
 
	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break
 
# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()


