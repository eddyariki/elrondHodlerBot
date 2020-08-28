from cryptography.fernet import Fernet
import base64
class Encryption:
    def __init__(self, location):
        self.location = location



    def generate_key(self):
        try:
            key = Fernet.generate_key()
            return key
        except Exception as e:
            print(e)
    
    def encrypt(self, text):
        try:
            #get key
            key = self.generate_key()
            

            #encode text
            encoded=text.encode()

            #encrypt text
            f = Fernet(key)
            encrypted = f.encrypt(encoded)

            #return as string
            return encrypted.decode(), key.decode()

        except Exception as e:
            print(e)
    
    def decrypt(self,encrypted,key):
        try:
            #get key
            # if(key==None):
            #     with open(self.location+'key.key', 'rb') as file:
            #         key = file.read()
            

            #turn to bytes
            encoded = base64.b64decode(encrypted).decode('utf-8')
            encoded = encoded.encode()
             
            #turn to bytes
            # encoded = base64.b64decode(encrypted).decode('utf-8')
            # encoded = encrypted.encode()
            #decrypt
            f = Fernet(key)
            decrypted = f.decrypt(encoded)

            #decode bytes
            decoded = decrypted.decode()
            return decoded

        except Exception as e:
            print(e)


