#!/usr/bin/env python3

from fastapi import FastAPI, Form
import os
import subprocess
import pwd
import uvicorn
import shutil
from os.path import join

def add_user(username,password):
     try:
        # executing useradd command using subprocess module
        home_dir = f"/home/{username}"
        output = subprocess.run(["useradd", "-p", password, username ])
        os.system(f"yes {password} | passwd {username}")
        if not os.path.exists(home_dir):
            os.makedirs(home_dir)
            with open(join(home_dir,"welcome.txt"), "w") as file:
                file.write(f"Welcome {username} to the RACOON R data-analysis!")
            uid, gid =  pwd.getpwnam(username).pw_uid, pwd.getpwnam(username).pw_uid
            shutil.copyfile("/src/test.R", join(home_dir,"test.R"))
            os.chown(home_dir, uid, gid)
        print(f"user: {username} created.")                     
        return True
     except:
        print(f"Could not create user: {username}")                     
        return False

app = FastAPI(title="RStudio User API",root_path=os.getenv('APPLICATION_ROOT', '/rst-api'))
    

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


# uvicorn user_api:app --reload

if __name__ == "__main__":
    uvicorn.run("user_api:app", host="127.0.0.1", port=5000, log_level="info",reload=False)