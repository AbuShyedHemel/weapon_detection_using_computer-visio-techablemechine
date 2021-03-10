import serial
import time

gsm = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)

def main():
    gsm.write(b"AT\r\n")
    time.sleep(2)
    gsm.write(b"AT+CMGF=1\r\n")
    time.sleep(2)
    gsm.write(b"AT+CNMI=1,2,0,0,0\r\n")
    time.sleep(5)
    print('GSM STARTED.')
    
def sendSMS(number, msg):
    gsm.write(b'AT+CMGF=1\r\n')
    print('Text Mode Enabled.')
    time.sleep(3)
    gsm.write(b'AT+CMGS="' + number.encode() + b'"\r\n')
    print('sending message…')
    time.sleep(3)
    gsm.reset_output_buffer()
    time.sleep(1)
    gsm.write(str.encode(msg+chr(26)))
    time.sleep(5)
    print('message sent.')
    call(number)
    
def call(number):
    gsm.write(b"ATD%s;\r\n"%(number.encode()))
    print("Call to: %s."%(number))
    

if __name__ == "__main__":
    main()
    
    #call("01303147918")
    #sendSMS("01303147918", "Testing SMS from Python.")
    