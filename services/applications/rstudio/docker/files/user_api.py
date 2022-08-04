#!/usr/bin/env python3

from fastapi import FastAPI, Form
import os
import subprocess
import pwd
import uvicorn
import shutil
import json
from os.path import join, exists, basename

home_dir = "/home"
user_info_json_path = join(home_dir,"user_info.json")
app = FastAPI(title="RStudio User API",root_path=os.getenv('APPLICATION_ROOT', '/rst-api'))

def add_user(username,password):
     print(f"Creating user: {username}")
     try:
        if exists(user_info_json_path):
            with open(user_info_json_path) as f:
                user_info_dict = json.load(f)
        else:
            user_info_dict={}

        user_home_dir = join(home_dir,f"{username}")
        print(f"{user_home_dir=}")
        print("useradd ...")
        output = subprocess.run(["useradd", "-p", password, username ])
        print("setpass ...")
        os.system(f"yes {password} | passwd {username}")
        print("check home-dir ...")
        if not os.path.exists(user_home_dir):
            os.makedirs(user_home_dir)
            with open(join(user_home_dir,"welcome.txt"), "w") as file:
                file.write(f"Welcome {username} to the RACOON R data-analysis!")
            uid, gid =  pwd.getpwnam(username).pw_uid, pwd.getpwnam(username).pw_uid
            shutil.copyfile("/src/test.R", join(user_home_dir,"test.R"))
            os.chown(user_home_dir, uid, gid)
            print("User home-dir created.")
        else:
            print("User home-dir already exists.")
        
        user_info_dict[username]={
            "username": username,
            "password": password
        }               
        print("write user-info...")
        with open(user_info_json_path, 'w') as out_file:
            json.dump(user_info_dict, out_file, sort_keys = False, indent = 4, ensure_ascii = False)
        
        print(f"user: {username} created.")      
        return True
     
     except Exception as e:
        print(f"Could not create user: {username}")
        print(e)                     
        return False

@app.get("/")
async def root():
    return {"message": "Hello World!"}

@app.post("/user")
async def create_user(username: str = Form(), password: str = Form()):
    if add_user(username=username,password=password):
        return {
            "username": username,
            "created": True
            }
    else:
        return {
            "username": username,
            "created": False
            }

@app.on_event("startup")
def startup_event():
    print("Init Users from home-dir ...")
    user_directories=[d for d in os.listdir(home_dir) if os.path.isdir(join(home_dir, d))]
    if len(user_directories) > 0:
        print("Found existing users ...")
        assert exists(user_info_json_path)
        with open(user_info_json_path) as f:
            user_info_dict = json.load(f)

        for user_id in user_directories:
            print(f"Init user: {user_id} ...")
            assert user_id in user_info_dict

            user_info = user_info_dict[user_id]
            assert "username" in user_info and "password" in user_info
            add_user(username=user_info["username"],password=user_info["password"])
    else:
        print("No existing users found ...")


if __name__ == "__main__":
    uvicorn.run("user_api:app", host="127.0.0.1", port=5000, log_level="info",reload=False)