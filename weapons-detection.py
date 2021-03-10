import numpy as np
import cv2
from PIL import Image
from tflite_runtime.interpreter import Interpreter
import sim800
import _thread
import datetime
from gpiozero import LED

SMS_freq = 10             # 30 seconds
detect_confidence = 0.70  # Greater than 70%
number   = "01676503632"  # SMS and Call Number
msg      = "Warning! Your property is in danger!! Please take immediate action!!!"

buzzer = LED(18)

_thread.start_new_thread(sim800.main, ())

def load_labels(path):
  with open(path, 'r') as f:
    return {i: line.strip() for i, line in enumerate(f.readlines())}


def set_input_tensor(interpreter, image):
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image


def classify_image(interpreter, image, top_k=1):
  set_input_tensor(interpreter, image)
  interpreter.invoke()
  output_details = interpreter.get_output_details()[0]
  output = np.squeeze(interpreter.get_tensor(output_details['index']))

  if output_details['dtype'] == np.uint8:
    scale, zero_point = output_details['quantization']
    output = scale * (output - zero_point)

  ordered = np.argpartition(-output, top_k)
  return [(i, output[i]) for i in ordered[:top_k]]


def main():
  smsFlag = 0
  global SMS_freq
  global detect_confidence
  now, hold = datetime.datetime.now(), datetime.datetime.now()
  labels = load_labels('labels.txt')
  interpreter = Interpreter('model.tflite')
  interpreter.allocate_tensors()
  _, height, width, _ = interpreter.get_input_details()[0]['shape']
  
  camera = cv2.VideoCapture(0)
  frameWidth = 320
  frameHeight = 240
  camera.set(cv2.CAP_PROP_FRAME_WIDTH, frameWidth)
  camera.set(cv2.CAP_PROP_FRAME_HEIGHT, frameHeight)
  camera.set(cv2.CAP_PROP_GAIN, 0)
  
  while True:
      ret, frame = camera.read()
      
      if ret == False:
          continue
      
      frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
      frame_resized = cv2.resize(frame_rgb, (width, height))
      image = np.expand_dims(frame_resized, axis=0)
      
      predictions = classify_image(interpreter, image)
      label_id, percent = predictions[0]
      
      if label_id != 5 and percent >= detect_confidence and smsFlag == 0:
          _thread.start_new_thread(sim800.sendSMS, (number, msg))
          smsFlag = 1
          buzzer.on()
          now = datetime.datetime.now()
          hold = now + datetime.timedelta(seconds = SMS_freq)
      
      if datetime.datetime.now() >= hold:
          smsFlag = 0
          buzzer.off()
      
      cv2.putText(
            img=frame,
            text=labels[label_id] + ' | Confidence: ' + str(int(percent * 100)) + '%',
            org=(10, 30),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.5,
            color=(255, 255, 255))

      cv2.imshow('Object detector', frame)
      
      if cv2.waitKey(1) == ord('q'):
          break

cv2.destroyAllWindows()

if __name__ == '__main__':
  main()
