from cryptography.fernet import Fernet
import base64
class Encryption:
    def __init__(self, location):
        self.location = location



    def generate_key(self):
        try:
            key = Fernet.generate_key()
            with open('key.key', 'wb') as key_file:
                key_file.write(key)

        except Exception as e:
            print(e)
    
    def encrypt(self, text):
        try:
            #get key
            with open(self.location+'key.key', 'rb') as file:
                key = file.read()
            

            #encode text
            encoded=text.encode()

            #encrypt text
            f = Fernet(key)
            encrypted = f.encrypt(encoded)

            #return as string
            return encrypted.decode()

        except Exception as e:
            print(e)
    
    def decrypt(self,encrypted):
        try:

            with open(self.location+'key.key', 'rb') as file:
                key = file.read()
            
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

if __name__ == "__main__":
    fileloc = ""
    e = Encryption(fileloc)
    e.generate_key()

