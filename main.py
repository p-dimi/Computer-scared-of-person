import cv2
import numpy as np

# FPS MEASUREMENTS STORAGE
fps_mem = []



import time
start_time = time.time()

from delta_measure import DeltaMeasure
DM = DeltaMeasure(memory_length = 11, recency = 3)

current_w_ratio = 0
# i want the "approach" ai to demand an increase of no more than X% every frame
screen_width = 720
last_average = 0
last_current = 0
approach_thresh = 0.09

fear_meter = 0.0
calming_rate_per_second = 0.05
fear_increase_rate = 0.10

# fear demonstrating screen
canvas = np.ones((512,512))

'''
def screen_ratio(val):
    global current_w_ratio
    if val != 0:
        current_w_ratio = val / screen_width
    else:
        # default ratio to be set at 10% minimum (that's how close the fear starts reacting)
        current_w_ratio = 0.1

def control_fear(val1, val2):
    if val2 == 0:
        # avoid division by zero
        val2 = 1
    if (val1 / val2) > (1 + (0.85 * approach_thresh) + ( (0.15 *approach_thresh) / current_w_ratio)):
        return True
    else:
        return False
'''

def control_fear(val):
    global current_w_ratio
    #print()
    #print((0.9 * approach_thresh) + ( (0.1 *approach_thresh) / current_w_ratio))
    ####
    # might want to implement also a dependency on how much bigger the change is than we want
    # like: dif = val - ((0.85 * approach_thresh) + ( (0.15 *approach_thresh) / current_w_ratio))
    ####
    if current_w_ratio <= 0.:
        current_w_ratio = 1.
    if val > (1 + (0.8 * approach_thresh) + ( (0.2 * approach_thresh) / current_w_ratio)):
        #print('TRUE')
        return True, (val - (1 + (0.8 * approach_thresh) + ( (0.2 *approach_thresh) / current_w_ratio)))
    else:
        return False, 0



    
def modulate_reaction(startled_bool, mod_val):
    global fear_meter
    # increase fear if need be
    if startled_bool == True:
        fear_meter += (0.85 * fear_increase_rate) + (0.15 * fear_increase_rate * current_w_ratio) + (fear_increase_rate * mod_val)
    # reduce fear naturally by reduction rate
    remainder = (10.0 - ((time.time() - start_time) % 10.0))
    #print(remainder)
    
    fear_meter -= (1 - (remainder / 10)) * calming_rate_per_second
    if fear_meter < 0.0:
        fear_meter = 0.0
    elif fear_meter > 1.0:
        fear_meter = 1.0
        
scale_mod = 0.5
init_mod = 0.75

weights = 'yolov3.weights'
model = 'yolov3.cfg'

weights_tiny = 'yolov3_tiny.weights'
model_tiny = 'yolov3_tiny.cfg'

net = cv2.dnn.readNet(weights_tiny, model_tiny)

classes=[]
with open('coco_classes.txt','r') as f:
    classes = [line.strip() for line in f.readlines()]
    
layer_names = net.getLayerNames()

outputlayers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

colors = np.random.uniform(0,255,size=(len(classes),3))

face_color = (160,160,255)

#cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap = cv2.VideoCapture(0)


cap.set(cv2.CAP_PROP_FPS, 60)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

#frame_id = 0

font = cv2.FONT_HERSHEY_PLAIN

min_conf_score = 0.15

thresh = 0.5
non_max_suppress = 0.45


im_size = 320

def crop_frame(frame):
    dif = int((frame.shape[1] - frame.shape[0]) / 2)
    return frame[0:frame.shape[0], dif:frame.shape[1]-dif, :]

    
while True:
    # measure fps
    fps_measure_starttime = time.time()
    
    ret, frame = cap.read()
        
    frame = crop_frame(frame)
        
    #print(frame.shape)
    
    
    height,width,channels = frame.shape
    
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (im_size,im_size), (0,0,0), True, crop=False)
    
    net.setInput(blob)
    
    outs = net.forward(outputlayers)
    
    class_ids=[]
    confidences=[]
    boxes=[]
    
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            
            if confidence > min_conf_score:
                # obj detected
                center_x = int(detection[0]*width)
                center_y = int(detection[1]*height)
                
                w = int(detection[2]*width)
                h = int(detection[3]*height)
                
                ### ### ### ### ### ###
                growth, avg_w = DM.get_delta(w)
                current_w_ratio = avg_w / screen_width
                startled, approach_dif = control_fear(growth)                    
                modulate_reaction(startled, approach_dif)
                ### ### ### ### ### ###
                
                # rect coords
                x = int(center_x - w/2)
                y = int(center_y - h/2)
                
                # save all boxes / confidences / classes
                boxes.append([x,y,w,h])
                confidences.append(float(confidence))
                class_ids.append(class_id)
                
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, non_max_suppress, thresh)
    
    # draw boxes
    for i in range(len(boxes)):
        if i in indexes:
            x,y,w,h = boxes[i]
            confidence = confidences[i]
            color = colors[class_ids[i]]
            cv2.rectangle(frame, (x,y), (x+w, y+h), color, 2)
            
            label = str(classes[class_ids[i]])
            
            cv2.putText(frame, label+' '+str(round(confidence, 2)), (x,y+30), font, 1, (255,255,255), 2)
            
    cv2.imshow('display', frame)
    
    cv2.imshow('fear display', (canvas * fear_meter))
    
    key = cv2.waitKey(1)
    
    # measure fps
    fps_mem.append(1 / (time.time() - fps_measure_starttime))
        
    if key == 27:
        break
        
        
for fps in fps_mem:
    print(fps)

def count_average(mem_list):
    sum = 0.
    for mem in mem_list:
        sum += mem
    return sum / len(mem_list)

avg_fps = count_average(fps_mem)
print('\nAVG FPS:')
print(avg_fps)
        
cap.release()
cv2.destroyAllWindows()