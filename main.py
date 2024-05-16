"""

paradigm - producer is a fastapi
senders are just loops
this is a streamlit

"""
import time
import sys
import streamlit as st
import requests
from config import get_config

config_dict = get_config()
producer_url = config_dict["producer_url"]
refresh_time = config_dict["frontend_refresh_time"]

placeholder = st.empty()

def run_app_loop(refresh_time):
    running = False
    while not running:
        try:
            running = requests.get(producer_url + "/").json()['running']
        except Exception as E:
            running = False

    while running:
        time.sleep(refresh_time)
        try:
            stats_d = requests.get(producer_url + "/stats").json()
        except:
            break
        msgs_sent = stats_d["msgs_sent"]
        msgs_failed = stats_d["msgs_failed"]
        percent_done = stats_d["percent_done"]
        msg_rate = stats_d["msg_rate"]
        time_elapsed = stats_d["time_elapsed"]

        with placeholder.container():
            #timedelta objct doesn't allow strftime
            t_str = "{:02}:{:02}:{:02}".format(time_elapsed//3600, (time_elapsed%3600)//60, time_elapsed%60//1)
            st.write(f"[{t_str}] : SENT: {msgs_sent} / FAILED: {msgs_failed} / TOTAL {percent_done} / RATE {msg_rate:.2f}")
            st.progress(percent_done/100)

    sys.exit(0)

run_app_loop(refresh_time)