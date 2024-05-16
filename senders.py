from producer import Message
import requests
import asyncio
import random, logging
from config import get_config

config_dict = get_config()

LOGGING_ON = True


logger = logging.getLogger(__name__)

if LOGGING_ON:
    format_log = "%(asctime)s: %(levelname)s : %(message)s"

    logging.basicConfig(format=format_log,
                        datefmt="%H:%M:%S", level=logging.INFO)

    logger.info("Logger INFO level clear")
    logger.error("Logger ERROR level clear")



producer_url = config_dict["producer_url"]
senders = config_dict["senders"]
sender_rates = config_dict["sender_rates"]
failure_rates = config_dict["failure_rates"]


class Sender:
    def __init__(self, id, send_rate, failure_rate, get_func=None, send_func=None):
        self.id = id
        self.send_rate = send_rate
        self.failure_rate = failure_rate

        #mod for testing
        if get_func is None:
            self.get_func = lambda : requests.get(producer_url+"/get")
        else:
            self.get_func = get_func

        if send_func is None:
            self.send_func = lambda d : requests.post(producer_url+"/send", json=d)
        else:
            self.send_func = send_func
        logger.info("sender %d initialized: wait %1.1f, fail rate %1.2f", self.id, self.send_rate, self.failure_rate)
    async def get_message(self):
        msg_json = self.get_func().json()
        if msg_json is None:
            return msg_json
        msg = Message.validate(msg_json)
        return msg

    async def send_message(self, msg: Message):
        msg.success = random.random() >= self.failure_rate
        success = "Success" in self.send_func(msg.dict()).text
        return success

    async def run(self):
        logger.info(f"sender id {self.id} running")
        while True:
            #testing expovariate - mean value output is actually 1/parameter
            #desire send rate to give us an average rate of 1/send_rate
            #so pass in send_rate
            msg = await self.get_message()
            #slighly obscure
            if msg is None:
                break
            else:
                logger.info(f"sender id {self.id} recieves msg {msg.id}")
            await asyncio.sleep(random.expovariate(self.send_rate))
            await self.send_message(msg)
            logger.info(f"sender id {self.id} sends msg {msg.id} ({'Success' if msg.success else 'Failure'}) to {msg.number}")
        logger.info(f"sender id {self.id} terminated")
        return True

def kill_fastapi():
    requests.get(producer_url+"/kill")


def generate_senders(sender_rates, failure_rates, senders):
    senders_list = []
    if len(sender_rates) < senders:
        sender_rates += [sender_rates[-1]] * (senders - len(sender_rates))

    if len(failure_rates) < senders:
        failure_rates += [failure_rates[-1]] * (senders - len(failure_rates))
    for i in range(senders):
        senders_list.append(Sender(i, sender_rates[i], failure_rates[i]))
    return senders_list

async def run_senders(senders_list):
    await asyncio.gather(*[s.run() for s in senders_list])
    kill_fastapi()




if __name__=="__main__":
    running = False
    while not running:
        try:
            running = requests.get(producer_url + "/").json()['running']
        except Exception as E:
            running = False

    senders_list = generate_senders(sender_rates, failure_rates, senders)
    asyncio.run(run_senders(senders_list))
