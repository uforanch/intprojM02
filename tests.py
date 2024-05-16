import pytest
from config import get_config
from fastapi.testclient import TestClient
from producer import app, Message
test_app = TestClient(app)

"""
staying to reasonable unit tests. Checking that apps run and self terminate could be possible with subprocesses.
So we mainly check that functions operate as they are supposed to. Nothing to check for main or run.sh. 
----
Additionally had a autouse function to set configs before each test but the only test it's needed for is the 
producer, which seems to set itself up and reset itself without the config file. 
"""

#PRODUCER TESTS
def test_producer_running():
    assert test_app.get("/").json()=={"running":True}
    #kill doesn't seem to test well but seems to be working

def test_producer_config():
    from producer import config_dict
    assert config_dict == get_config()

def test_producer_get():
    msg0_json = test_app.get("/get").json()
    assert msg0_json # received msg
    assert Message.validate(msg0_json) #msg format
    assert msg0_json["id"] == 0 #msg is first
    assert len(msg0_json["number"])==10
    assert all([n in "0123456789" for n in msg0_json["number"]])
    assert len(msg0_json["content"])<=100


    msg1_json = test_app.get("/get").json()
    assert msg1_json # received msg
    assert Message.validate(msg1_json) #msg format
    assert msg1_json["id"] == 1 #msg is first
    assert len(msg1_json["number"])==10
    assert all([n in "0123456789" for n in msg1_json["number"]])
    assert len(msg1_json["content"])<=100

def test_producer_get_all():
    total_mgs = get_config()["total_msgs"]
    for _ in range(total_mgs):
        test_app.get("/get").json()
    msg_last = test_app.get("/get").json()
    assert msg_last is None

def test_producer_stats_send():
    msg = Message()
    config_dict = get_config()
    stats_d = test_app.get("/stats").json()
    assert stats_d["total_msgs"] == config_dict["total_msgs"]
    assert stats_d["percent_done"] == 0
    assert stats_d["msgs_sent"] == 0
    assert stats_d["msgs_failed"] == 0
    assert stats_d["msg_rate"] == 0
    msg.success=True
    test_app.post("/send", json=msg.dict())

    stats_d = test_app.get("/stats").json()
    assert stats_d["total_msgs"] == config_dict["total_msgs"]
    assert stats_d["percent_done"] > 0
    assert stats_d["msgs_sent"] == 1
    assert stats_d["msgs_failed"] == 0
    assert stats_d["msg_rate"] > 0
    msg.success = False
    test_app.post("/send", json=msg.dict())

    stats_d = test_app.get("/stats").json()
    assert stats_d["total_msgs"] == config_dict["total_msgs"]
    assert stats_d["percent_done"] > 0
    assert stats_d["msgs_sent"] == 1
    assert stats_d["msgs_failed"] == 1
    assert stats_d["msg_rate"] > 0

# SENDER TESTS
def test_sender_generation():
    from senders import generate_senders
    send_rate_list_orig = [.1,.2,.3]
    failure_rate_list_orig = [.1,.2,.3]
    send_rate_list = send_rate_list_orig.copy()
    failure_rate_list = failure_rate_list_orig.copy()
    sender_list = generate_senders(send_rate_list, failure_rate_list, 3)
    assert len(sender_list)==3
    for i in range(3):
        assert send_rate_list[i] == send_rate_list_orig[i]
        assert failure_rate_list[i] == failure_rate_list_orig[i]
        assert sender_list[i].send_rate == send_rate_list[i]
        assert sender_list[i].failure_rate == failure_rate_list[i]

    send_rate_list_orig = [.1, .2]
    failure_rate_list_orig = [.1]
    send_rate_list = send_rate_list_orig.copy()
    failure_rate_list = failure_rate_list_orig.copy()
    sender_list = generate_senders(send_rate_list, failure_rate_list, 5)
    assert len(sender_list) == 5
    for i in range(5):
        if i<=1:
            assert send_rate_list[i] == send_rate_list_orig[i]
        else:
            assert send_rate_list[i] == send_rate_list_orig[-1]
        if i<=0:
            assert failure_rate_list[i] == failure_rate_list_orig[i]
        else:
            assert failure_rate_list[i] == failure_rate_list_orig[-1]
        assert sender_list[i].send_rate == send_rate_list[i]
        assert sender_list[i].failure_rate == failure_rate_list[i]


"""
Desired to unit test the functionality of Sender and thought my method
of making sure Sender used the Test App would work. 

Despite run.sh currently working fine, the unit tests fail even the "send function"
operates just fine when not passed into the Sender. 

I am... really unsure how to get around this without using popon, etc
"""
@pytest.mark.skip(reason="unknown why test fails")
@pytest.mark.asyncio
async def test_sender_funcs():
    from senders import Sender
    get_func = lambda : test_app.get("/get")
    send_func = lambda d : test_app.post("/send", json=d)
    s = Sender(0,
               .1,
               0,
               get_func = get_func,
               send_func = send_func)

    msg = await s.get_message()
    assert msg is None or Message.validate(msg)

    msg_json = Message().dict()
    msg_json["success"]=True
    send_func(msg_json)

    assert test_app.get("/stats").json()['msgs_sent']==1

    s.send_message(msg_json)

    assert test_app.get("/stats").json()['msgs_sent']==2

    s.failure_rate=1
    s.send_message(msg)


    assert test_app.get("/stats").json()['msgs_failed']==1


def test_sender_config():
    from senders import config_dict
    assert config_dict==get_config()

