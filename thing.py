import calendar
import sqlite3 as lite
import time
import json
import threading
import random

import main
import mob

clients = {}
clients_lock = threading.Lock()
things_connected_lock = threading.Lock()
things_connected = {}
things_time = {}

GROUPS = []
ITEMS = []
ITEMSComplete = []
PROFILES = []
PROFILESComplete = []
VERSION = {}
PROFILE_NUMBER = 0
TIMER_NUMBER = 0
relay_cnt = 0
relay_cnt1 = 0
relay_cnt2 = 0


class Thing:
    def __init__(self, server):

        # self.db_setting = db.Setting()
        self.result = {"set_relay_1": {}, "get_relay_1": None, "set_relay_2": {}, "get_relay_2": None,
                       "set_temperature": None, "get_temperature": None, "set_current": None, "get_current": None,
                       "info_switch_1": None, "info_switch_2": None, "set_relay_1_response": {},
                       "set_network_response": {}, "update_response": {},
                       "get_relay_1_response": None, "set_relay_2_response": {}, "get_relay_2_response": None,
                       "set_lock_1_response": {}, "set_lock_2_response": {},
                       "set_temperature_response": None, "get_temperature_response": None, "set_current_response": None,
                       "get_current_response": None, "info_switch_1_response": None, "info_switch_2_response": None}
        self.thing = "NA"
        self.type = "NA"
        self.changed = False
        self.relay_1 = -1
        self.relay_2 = -1
        self.lock_1 = -1
        self.lock_2 = -1
        self.temp = 0
        self.current = 0
        self.mem = ""
        self.mac = ""
        self.uptime = ""
        self.ip = ""
        self.name1 = "-259"
        self.image1 = 0
        self.name2 = "-259"
        self.image2 = 0
        self.version = ""
        self.send_ws_lock = threading.Lock()
        self.act_power = -1
        self.app_power = -1
        self.ac_voltage = -1
        self.server = server
        self.avg_list_actp = []
        self.avg_list_volt = []
        self.ws_cmd = {"current_state": "info_response", "set_relay_1": "setrelay1", "get_relay_1": "getrelay1",
                       "set_relay_2": "setrelay2", "get_relay_2": "getrelay2", "set_temperature": "settemperature",
                       "set_lock_1": "setlock1",  "set_lock_2": "setlock2",
                       "get_temperature": "gettemperature", "set_current": "setcurrent", "get_current": "getcurrent",
                       "info_switch_1": "infoswitch1", "info_switch_2": "infoswitch2", "update_request": "update"
                       }

        self.time_out = 3
        self.time_updated = 0

    def update_request_th(self):
        a = threading.Thread(name="db_setting", target=self.update_request)
        a.setDaemon(True)
        a.start()

        # print("\tIN UPDATE...", self.thing)

    def update_request(self):
        try:
            seq = str(random.randint(100000, 1000000))
            self.result["update_response"][seq] = None

            msg = {"seq": seq, "action": "update"}
            end = msg
            resp = json.dumps(end)

            # print ("send update command:", self.thing, resp)
            self.server.sendMessage(resp)

            time_end = calendar.timegm(time.gmtime())
            time_start = calendar.timegm(time.gmtime())

            while self.result["update_response"][seq] is None and (time_start - time_end) < self.time_out:
                time_start = calendar.timegm(time.gmtime())
                time.sleep(0.05)

            return self.result["update_response"][seq]
        except Exception as e:
            print(e)
            main.add_exception("update_request", str(e))

    def set_relay(self, state, thg):
        global relay_cnt, relay_cnt1

        relay_cnt += 1
        # print("************************COUNTER*****************", relay_cnt2, relay_cnt, relay_cnt1)

        if self.type == "SANA-102" or self.type == "SANA-102s":
            if thg[-2:] == "-1":
                return self.set_relay_1(state)
            elif thg[-2:] == "-2":
                return self.set_relay_2(state)
        else:
            return self.set_relay_1(state)

    def set_relay_1(self, data):
        global relay_cnt1
        try:
            # print "in set relay1 func", self.thing, data
            seq = str(random.randint(100000, 1000000))
            self.result["set_relay_1_response"][seq] = None

            msg = {"seq": seq, "action": "setrelay1", "value": data[0]}
            end = msg
            resp = json.dumps(end)

            with self.send_ws_lock:
                # print ("send command for relay 1:", resp)
                self.server.sendMessage(resp)

                time_end = calendar.timegm(time.gmtime())
                time_start = calendar.timegm(time.gmtime())

                # time.sleep(0.5)

                while self.result["set_relay_1_response"][seq] is None and (time_start - time_end) < self.time_out:
                    # print "wait for 111111", seq
                    time_start = calendar.timegm(time.gmtime())
                    time.sleep(0.05)

            print self.thing, self.result["set_relay_1_response"][seq]
            if self.result["set_relay_1_response"][seq] == 1:
                self.relay_1 = data[0]
            else:
                relay_cnt1 += 1

            print("************************COUNTER*****************", relay_cnt2, relay_cnt, relay_cnt1)

            return self.result["set_relay_1_response"][seq]
        except Exception as e:
            print(e)
            main.add_exception("set_relay1", str(e))

    def get_relay_1(self):
        return self.relay_1

    def set_relay_2(self, data):
        global relay_cnt1
        try:
            # print "in set relay2 func", self.thing, data
            seq = str(random.randint(100000, 1000000))
            self.result["set_relay_2_response"][seq] = None

            msg = {"seq": seq, "action": "setrelay2", "value": data[0]}
            end = msg
            resp = json.dumps(end)

            with self.send_ws_lock:
                # print ("send command for relay 2:", resp)
                self.server.sendMessage(resp)

                time_end = calendar.timegm(time.gmtime())
                time_start = calendar.timegm(time.gmtime())

                # time.sleep(0.5)

                while self.result["set_relay_2_response"][seq] is None and (time_start - time_end) < self.time_out:
                    # print "wait for 22222", seq
                    time_start = calendar.timegm(time.gmtime())
                    time.sleep(0.05)

            print self.thing, self.result["set_relay_2_response"][seq]
            if self.result["set_relay_2_response"][seq] == 1:
                self.relay_2 = data[0]
            else:
                relay_cnt1 += 1

            print("************************COUNTER*****************", relay_cnt2, relay_cnt, relay_cnt1)

            return self.result["set_relay_2_response"][seq]
        except Exception as e:
            print(e)
            main.add_exception("set_relay2", str(e))

    def get_relay_2(self):
        return self.relay_2

    def set_lock(self, state, thg):
        if self.type == "SANA-102" or self.type == "SANA-102s":
            if thg[-2:] == "-1":
                return self.set_lock_1(state)
            elif thg[-2:] == "-2":
                return self.set_lock_2(state)
        else:
            return self.set_lock_1(state)

    def set_lock_1(self, data):

        try:
            print "in set lock1 func", self.thing, data
            seq = str(random.randint(100000, 1000000))
            self.result["set_lock_1_response"][seq] = None

            msg = {"seq": seq, "action": "setlock1", "value": data[0]}
            end = msg
            resp = json.dumps(end)

            with self.send_ws_lock:
                print ("send command for lock 1:", resp)
                self.server.sendMessage(resp)

                time_end = calendar.timegm(time.gmtime())
                time_start = calendar.timegm(time.gmtime())

                while self.result["set_lock_1_response"][seq] is None and (time_start - time_end) < self.time_out:
                    # print "wait for 111111", seq
                    time_start = calendar.timegm(time.gmtime())
                    time.sleep(0.05)

            print ("response from chic1:", self.result["set_lock_1_response"][seq], data[0])
            if self.result["set_lock_1_response"][seq] == 1:
                self.lock_1 = data[0]

            return self.result["set_lock_1_response"][seq]
        except Exception as e:
            print(e)
            main.add_exception("set_lock1", str(e))

    def get_lock1(self):
        return self.lock_1

    def set_lock_2(self, data):
        try:
            print "in set lock2 func", self.thing, data
            seq = str(random.randint(100000, 1000000))
            self.result["set_lock_2_response"][seq] = None

            msg = {"seq": seq, "action": "setlock2", "value": data[0]}
            end = msg
            resp = json.dumps(end)

            with self.send_ws_lock:
                print ("send command for lock 2:", resp)
                self.server.sendMessage(resp)

                time_end = calendar.timegm(time.gmtime())
                time_start = calendar.timegm(time.gmtime())

                while self.result["set_lock_2_response"][seq] is None and (time_start - time_end) < self.time_out:
                    # print "wait for 22222", seq
                    time_start = calendar.timegm(time.gmtime())
                    time.sleep(0.05)

            print ("response from chic2:", self.result["set_lock_2_response"][seq], data[0])
            if self.result["set_lock_2_response"][seq] == 1:
                self.lock_2 = data[0]

            return self.result["set_lock_2_response"][seq]
        except Exception as e:
            print(e)
            main.add_exception("set_lock2", str(e))

    def get_lock_2(self):
        return self.lock_2

    def set_temperature(self, data):
        try:
            self.result["set_temperature_response"] = -1
            # print("sending set temperature")

            time_end = calendar.timegm(time.gmtime())
            time_start = calendar.timegm(time.gmtime())
            while self.result["set_temperature_response"] == -1 and (time_start - time_end) < self.time_out:
                time_start = calendar.timegm(time.gmtime())
                time.sleep(0.1)

            if self.result["set_temperature_response"] != -1:
                self.temp = data[0]

            return self.result["set_temperature_response"]
        except Exception as e:
            print(e)
            main.add_exception("set_temperature", str(e))

    def get_temperature(self):
        return self.temp

    def set_current(self, data):
        try:
            self.result["set_current_response"] = -1
            # print("sending set current")

            time_end = calendar.timegm(time.gmtime())
            time_start = calendar.timegm(time.gmtime())
            while not self.result["set_current_response"] and (time_start - time_end) < self.time_out:
                time_start = calendar.timegm(time.gmtime())
                time.sleep(0.1)
            self.relay_2 = data

            return self.result["set_current_response"]
        except Exception as e:
            print(e)
            main.add_exception("set_current", str(e))

    def get_current(self):
        return self.current

    def get_ip(self):

        return self.ip.split('.')[3]

    def info_switch_1(self):
        pass

    def info_switch_2(self):
        pass

    def set_network(self, ssid, password):
        try:
            print "in set networK"

            seq = str(random.randint(100000, 1000000))
            self.result["set_network_response"][seq] = -1

            msg = {"seq": seq, "action": "setnetwork", "ssid": ssid, "password": password}
            end = msg
            resp = json.dumps(end)

            print ("send network command:", resp)

            self.server.sendMessage(resp)

            time_end = calendar.timegm(time.gmtime())
            time_start = calendar.timegm(time.gmtime())

            while self.result["set_network_response"][seq] == -1 and (time_start - time_end) < self.time_out:
                time_start = calendar.timegm(time.gmtime())
                time.sleep(0.1)

            print ("response from chic:", self.result["set_network_response"][seq])

            return self.result["set_network_response"][seq]
        except Exception as e:
            print(e)
            main.add_exception("set_relay1", str(e))

    def set_name(self, thing, index, name, image):

        try:
            con = lite.connect(main.db_setting_address)
            with con:
                cur = con.cursor()
                res = 0
                for dic in mob.names:
                    print ("thins in set name", dic["thing"], thing)
                    if dic["thing"] == thing:
                        if index == "1":
                            cur.execute("UPDATE thing SET name1=?,image1=? where id =?", (name, image, thing))
                            self.name1 = name
                            dic["name1"] = name
                            self.image1 = image
                            dic["image1"] = image
                        else:
                            cur.execute("UPDATE thing SET name2=?,image2=? where id =?", (name, image, thing))
                            self.name2 = name
                            dic["name2"] = name
                            self.image2 = image
                            dic["image2"] = image
                        res = 1
                        break
                if not res:
                    if index == "1":
                        cur.execute("INSERT into thing(id,name1,image1) values(?,?,?)", (thing, name, image))
                        self.name1 = name
                        self.image1 = image
                        mob.names.append(
                            {"thing": thing, "name1": name, "name2": "-259", "image1": image, "image2": 0})
                    else:
                        cur.execute("INSERT into thing(id,name2,image2) values(?,?,?)", (thing, name, image))
                        self.name2 = name
                        self.image2 = image
                        mob.names.append(
                            {"thing": thing, "name1": "-259", "name2": name, "image1": 0, "image2": image})
                print ("names:", mob.names)
                con.commit()
            con.close()
            return 1
        except Exception as e:
            print (e)
            main.add_exception("set_name", str(e))



