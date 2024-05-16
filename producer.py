import asyncio
import time
import random
import os, signal

from pydantic import BaseModel, StringConstraints
from typing import Optional
from typing_extensions import Annotated

from fastapi import FastAPI
from config import get_config

class Message(BaseModel):
    id : int = 0
    number : Annotated[str, StringConstraints(min_length=10, max_length=10)] = "0123456789"
    content : Annotated[str, StringConstraints(max_length=100)] = "Content"
    success : Optional[bool] = None

config_dict = get_config()

total_msgs = config_dict["total_msgs"]
msgs_sent_success = 0
msgs_sent_failed = 0



q = asyncio.Queue()

async def generate(n):
    for i in range(n):
        await q.put(Message(id=i,
                            number="".join([chr(random.randint(ord("0"), ord("9"))) for _ in range(10)]),
                            content="".join([chr(random.randint(ord("0"), ord("Z"))) for _ in range(random.randint(5,100))])))
    return True


asyncio.run(generate(total_msgs))
start_time = time.time()
app = FastAPI()

"""
Issue with running things with run.sh is that there's no way to cntrl + C the fast API
and it turns out it's a knottier problem to have the app shut itself down than expected 
"""
@app.on_event('shutdown')
def shutdown_event():
    print('Shutting down...!')


@app.get("/kill")
def kill_signal():
   os.kill(os.getpid(), signal.SIGINT)
   return True


@app.get("/")
def running():
    return {"running":True}


# get messgages sent, rate, etc - compute here.
@app.get("/stats")
def return_stats() -> dict:
    global msgs_sent_success, msgs_sent_failed, total_msgs, start_time
    time_elapsed = (time.time() - start_time)
    msg_rate = (msgs_sent_failed + msgs_sent_success) / time_elapsed
    percent_done = (msgs_sent_failed + msgs_sent_success) / total_msgs * 100

    return {"msgs_sent": msgs_sent_success,
            "msgs_failed":msgs_sent_failed,
            "percent_done":percent_done,
            "msg_rate":msg_rate,
            "time_elapsed":time_elapsed,
            "total_msgs":total_msgs}

#get message
@app.get("/get")
async def get():
    if not q.empty():
        return await q.get()
    else:
        return None

#send message  +  succeed or fail
@app.post("/send")
def send(message: Message):
    global  msgs_sent_success, msgs_sent_failed
    success = message.success
    if success:
        msgs_sent_success+=1
    else:
        msgs_sent_failed+=1
    return "Success"




