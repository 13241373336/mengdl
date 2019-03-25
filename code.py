import qrcode 
import time
from pystrich.code128 import Code128Encoder
import random




def create_barcode(code):
    # code=random.randint(1000000000,999999999)
    path='barcode/'+str(code)+'.jpg'
    encoder=Code128Encoder(str(code))
    encoder.save(path)

def create_qrcode(code):
    # code=random.randint(1000000000,999999999)
    path='qrcode/'+str(code)+'.jpg'
    qr = qrcode.QRCode(     
        version=1,     
        error_correction=qrcode.constants.ERROR_CORRECT_L,     
        box_size=10,     
        border=0, 
    ) 
    qr.add_data(code) 
    qr.make(fit=True)  
    img = qr.make_image()
    img.save(path)

def create_codes(code):
    create_barcode(code)
    create_qrcode(code)




# code=int(str(int(time.time()/10000))+str(random.randint(1000,9999)))
# path='qrcode/'+str(code)+'.jpg'
# print(path)
# # create_qrcode('qrcode/'+str(int(time.time()))+str(random.randint(1000,9999)),int(str(int(time.time()/1000))+str(random.randint(1000,9999))))
# create_qrcode(path,code)