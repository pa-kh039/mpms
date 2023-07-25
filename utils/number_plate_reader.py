import cv2
import easyocr
from IPython.display import Image





# img_roi=None
def read(checkpoint):
    harcascade = "D:/Django/MLP/mlp2/utils/model/haarcascade_russian_plate_number.xml"
    min_area = 500
    count = 0
    cap = cv2.VideoCapture(0)
    cap.set(3, 640) # width
    cap.set(4, 480) #height
    while True:

        success, img = cap.read()

        plate_cascade = cv2.CascadeClassifier(harcascade)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        plates = plate_cascade.detectMultiScale(img_gray, 1.1, 4)
        
        # print(0)
        for (x,y,w,h) in plates:
            area = w * h
            # print(1)
            if area > min_area:
                # print(2)
                cv2.rectangle(img, (x,y), (x+w, y+h), (0,255,0), 2)
                cv2.putText(img, "Number Plate", (x,y-5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 0, 255), 2)

                img_roi = img[y: y+h, x:x+w]
                
                cv2.imshow("ROI", img_roi) 


        

        if cv2.waitKey(1) & 0xFF == ord('s'):
            try:
                cv2.imwrite("D:/Django/MLP/mlp2/utils/images/scanned_img"+str(checkpoint)+".jpg", img_roi)
                # cv2.imwrite("images/scaned_img_" + str(count) + ".jpg", img_roi)
                # cv2.rectangle(img, (0,200), (640,300), (0,255,0), cv2.FILLED)
                # cv2.putText(img, "Plate Saved", (150, 265), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (0, 0, 255), 2)
                # cv2.imshow("Saved",img)
                cv2.waitKey(500)
                Image("D:/Django/MLP/mlp2/utils/images/scanned_img"+str(checkpoint)+".jpg")
                reader = easyocr.Reader(['en'])
                output = reader.readtext('D:/Django/MLP/mlp2/utils/images/scanned_img'+str(checkpoint)+'.jpg')
                tmp_ans=((output[0][-2]).lower())
                tmp_ans=((output[0][-2]).lower())
                ans=""
                for ch in tmp_ans:
                    if ch!=" ":
                        ans+=ch
                return (ans)
                # count += 1
            except Exception as e:
                print(e)
                print("no new car detected")

        cv2.imshow("Press 's' to record the highlighted image", img)
