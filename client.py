from threading import *
import time
from app import App
import pandas as pd
from queue import Queue
from extsockets import *


# hostname = socket.gethostname()
# HOST = socket.gethostbyname(hostname)
HOST = "52.91.161.11"
PORT = 2012

pending, _open, closed = "pending", "open", "closed"
xonetypes = {pending, _open, closed}

add_subscription, sub_response = "add subscription", "subscription response"
xones = "xones"  # subscriptions
spawn, spawn_response = "spawn", "spawn_response"

client, server, meta, data = "client", "server", "meta", "data"

request_template = {"to": server, "from": client, meta: "", data: ""}


class GridClient(App):
    def __init__(self, host=HOST, port=PORT):
        super().__init__()
        self.q = Queue()
        self.spawn.set_spawning_q(self.q)
        self.update_needed = Event()
        self.client_manager = ClientManager(host=host, port=port, call_on_message=self.message_handler,
                                            call_on_close=self.close_handler)
        message = request_template.copy()
        message[meta] = add_subscription
        message[data] = xones
        self.client_manager.send_message(message)
        self.updater = Thread(target=self.update, daemon=True)
        self.updater.start()
        self.mainloop()

    def message_handler(self, message):
        global meta, data
        rcvd_meta = message[meta]
        rcvd_data = message[data]
        if rcvd_meta == sub_response:
            self.raven.post_message(rcvd_data)
        if rcvd_meta == xones:
            self.xones.refresh(rcvd_data)

    def close_handler(self):
        self.client_manager.close()

    def update(self):
        while True:
            ordervals = self.q.get()
            place_order(**ordervals)


def place_order(symbol, entry, stoploss, target=""):
    response = None
    received = Event()

    def response_handler(message):
        global response
        rcvd_meta = message[meta]
        rcvd_data = message[data]
        if rcvd_meta == spawn_response:
            response = rcvd_data
            print(f"Response: {response}")
            received.set()

    def close_handler():
        received.set()

    vals = {
        'symbol': symbol,
        'entry': entry,
        'stoploss': stoploss,
        'target': target
    }
    message = request_template.copy()
    message[meta] = spawn
    message[data] = vals
    tc = ClientManager(HOST, PORT, call_on_message=response_handler, call_on_close=close_handler)
    tc.send_message(message)
    while received.wait():
        received.clear()
        tc.close()
        return response


if __name__ == '__main__':
    gc = GridClient(HOST, PORT)
