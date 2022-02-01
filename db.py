import threading
import Queue
import time
import functools
import calendar

import main
import thing
import web_socket_client

debug = False
OFFSET = 0
db_setting = None


class Setting:
    def __init__(self):
        self.current_table = [0, 3, 7, 11, 15, 19, 23, 27, 31, 34, 38,
                              42, 45, 49, 52, 55, 59, 62, 66, 69,
                              73, 76, 79, 83, 86, 89, 90, 93, 99,
                              103, 107, 110, 114, 117, 120, 124, 127, 130,
                              134, 137, 140, 144, 147, 150, 153, 157, 161,
                              163, 166, 170, 175]
        self.result = {"info": False,
                       "setrelay1": False,
                       "setrelay2": False,
                       "setnetwork": False,
                       }
        self.result_wait_time = 8  # second

        # self.is_on = False  # is db started
        self.queue_size = 0
        self.address = main.db_setting_address
        self.queue = Queue.Queue()

    def start(self):
        a = threading.Thread(name="db_setting", target=self.db_setting_th)
        a.setDaemon(True)
        a.start()

        print("\tPASSED")

    def wait_for_result(self, dic):
        global debug
        try:

            func = dic["function"]

            if debug:
                mod = dic["module"]
                print("in wait for result ", mod, func)

            self.result[func] = False
            self.queue.put(dic)

            time_end = calendar.timegm(time.gmtime())
            time_start = calendar.timegm(time.gmtime())

            while (time_start - time_end) < self.result_wait_time:  # 8 seconds:
                time_start = calendar.timegm(time.gmtime())
                if self.result[func]:
                    return True
                time.sleep(0.5)
        except Exception as e:
            # print(e)
            return False

        return False

    def run_setting_functions(self, dic):
        try:
            setting_functions = {
                "info": self.info,
                "setrelay1": self.setrelay1,
                "setrelay2": self.setrelay2,
                "setlock1": self.setlock1,
                "setlock2": self.setlock2,
                "setnetwork": self.setnetwork,
                "update": self.update
            }

            setting_functions[dic["function"]](dic)
        except Exception as e:
            print(e)

    def grouping_th(self, state, item):

        t = item.replace("-1", "").replace("-2", "")

        if t in dict(thing.things_connected):
            packet = thing.things_connected[t]
            # print "GROUPING3:", state, item, packet.thing
            if not packet.set_relay([state], item):
                packet.set_relay([state], item)

    def find_grouping(self, thg):
        in_same_group = []

        for group in list(thing.GROUPS):
            things = group["things"]
            for item in things:
                if thg == item["thing"]:
                    for it in things:
                        # print "ITTTT:", it["thing"], "thg"
                        if it["thing"] != thg:
                            in_same_group.append(it["thing"])
                    print "same group:", in_same_group
                    return in_same_group

        return []

    def grouping(self, group_list, state):

        for item in group_list:
            a = threading.Thread(name="check", args=(state, item), target=self.grouping_th)
            a.setDaemon(True)
            a.start()

    def info(self, dic):
        global OFFSET

        try:
            device, data = dic["data"]

            device.thing = data["serialno"]
            device.type = data["model"]

            if "relay1" in data and device.relay_1 != int(data["relay1"]):
                device.changed = True
                if device.relay_1 != -1:
                    print "CHANGED..."
                    self.grouping(self.find_grouping(device.thing), int(data["relay1"]))
            elif "relay2" in data and device.relay_2 != int(data["relay2"]):
                device.changed = True
                if device.relay_2 != -1:
                    print "CHANGED..."
                    self.grouping(self.find_grouping(device.thing), int(data["relay2"]))

            if device.thing.lower() == "a020a6064ba3":
                print ("info received", data["serialno"], data)

            device.temp = int(data["temp"])

            if "relay1" in data:
                device.relay_1 = int(data["relay1"])
            if device.type == "SANA-102" or device.type == "SANA-102s":
                device.relay_2 = int(data["relay2"])

            if "lock1" in data:
                # print "new lock1"
                device.lock_1 = int(data["lock1"])
            if device.type == "SANA-102" or device.type == "SANA-102s":
                if "lock2" in data:
                    # print "new loc2"
                    device.lock_2 = int(data["lock2"])

            device.ip = data["ip"]
            # device.current = data["current"]
            # print "CURRENT:", self.current_converter(int(data["current"])), device.ip

            if device.type == "SANA-101P":
                device.current = self.current_converter(int(data["current"]) - OFFSET)
            device.mac = data["mac"]

            if "freeMem" in data:
                device.mem = data["freeMem"]
            if "upTime" in data:
                device.uptime = data["upTime"]

            if device.type == "SANA-P30":
                device.type = "SANA-101"

                # device.current = int(float(data["actPower"]))
                device.avg_list_actp.append(int(float(data["actPower"])))
                if len(device.avg_list_actp) > 4:
                    device.avg_list_actp.pop(0)
                device.current = functools.reduce(lambda x, y: x + y, device.avg_list_actp) / len(device.avg_list_actp)

                # device.temp = int(float(data["acVoltage"]))
                device.avg_list_volt.append(int(float(data["acVoltage"])))
                if len(device.avg_list_volt) > 4:
                    device.avg_list_volt.pop(0)
                device.temp = functools.reduce(lambda x, y: x + y, device.avg_list_volt) / len(
                    device.avg_list_volt)

                # print "CURRENT, TEMP",
                # device.app_power = data["appPower"]

            if "version" in data:
                device.version = data["version"]
            else:
                print "HHHHHHH", device.thing

            if device.version != thing.VERSION[device.type]:
                device.update_request_th()
            # print "versionxxx:", data["version"]

            new_thing = True
            new_thing_1 = True
            new_thing_2 = True
            item1 = None
            item2 = None

            for item in list(thing.ITEMSComplete):
                if device.type == "SANA-102" or device.type == "SANA-102s":

                    th1 = device.thing + "-1"
                    th2 = device.thing + "-2"
                    # print ("th1 th2", th1, th2, item["thing"])

                    if item["thing"] == th1:
                        # print "th1 found"
                        item["status"] = 1
                        item["state"] = device.relay_1
                        item["temp"] = device.temp
                        # item["current"] = device.current
                        item["ip"] = device.ip
                        item["type"] = device.type
                        item["upTime"] = device.uptime
                        item["freeMemory"] = device.mem
                        new_thing_1 = False
                        item1 = dict(item)

                    elif item["thing"] == th2:
                        # print "th2 found"
                        item["status"] = 1
                        item["state"] = device.relay_2
                        item["temp"] = device.temp
                        # item["current"] = device.current
                        item["ip"] = device.ip
                        item["type"] = device.type
                        item["upTime"] = device.uptime
                        item["freeMemory"] = device.mem
                        new_thing_2 = False
                        item2 = dict(item)

                elif device.type == "SANA-101" or device.type == "SANA-101s":
                    if item["thing"] == device.thing:
                        item["status"] = 1
                        item["state"] = device.relay_1
                        item["temp"] = device.temp
                        item["current"] = device.current
                        item["ip"] = device.ip
                        item["type"] = device.type
                        item["upTime"] = device.uptime
                        item["freeMemory"] = device.mem
                        new_thing = False
                        item1 = dict(item)

                elif device.type == "SANA-101P":
                    if item["thing"] == device.thing:
                        item["status"] = 1
                        item["state"] = device.relay_1
                        item["temp"] = device.temp
                        item["current"] = device.current
                        item["ip"] = device.ip
                        item["type"] = device.type
                        item["upTime"] = device.uptime
                        item["freeMemory"] = device.mem
                        new_thing = False
                        item1 = dict(item)
                elif device.type == "SANA-P30":
                    if item["thing"] == device.thing:
                        item["status"] = 1
                        item["temp"] = device.temp
                        item["ip"] = device.ip
                        item["type"] = device.type
                        item["upTime"] = device.uptime
                        item["freeMemory"] = device.mem
                        item["actPower"] = device.act_power
                        item["appPower"] = device.app_power
                        item["acVoltage"] = device.ac_voltage

                        new_thing = False
                        item1 = dict(item)

            thing.things_connected[device.thing] = device

            if device.type == "SANA-102" or device.type == "SANA-102s":

                if new_thing_1:
                    item1 = {"model": device.type, "temp": device.temp, "state": device.relay_1, "status": 1,
                             "thing": device.thing + "-1", "freeMemory": device.mem,
                             "upTime": device.uptime, "ip": device.ip, "name": device.thing + "-1", "lock": device.lock_1,
                             "image": 0, "timers": []}

                    thing.ITEMSComplete.append(item1)

                if new_thing_2:
                    item2 = {"model": device.type, "temp": device.temp, "state": device.relay_2, "status": 1,
                             "thing": device.thing + "-2", "freeMemory": device.mem,
                             "upTime": device.uptime, "ip": device.ip, "name": device.thing + "-2", "lock": device.lock_2,
                             "image": 0, "timers": []}

                    thing.ITEMSComplete.append(item2)

            elif device.type == "SANA-101" or device.type == "SANA-101s" or device.type == "SANA-101P":
                if new_thing:
                    item1 = {"model": device.type, "temp": device.temp, "state": device.relay_1, "status": 1,
                             "thing": device.thing, "freeMemory": device.mem, "current": device.current,
                             "upTime": device.uptime, "ip": device.ip, "name": device.thing, "lock": device.lock_1,
                             "image": 0, "timers": []}
                    thing.ITEMSComplete.append(item1)

            elif device.type == "SANA-101P":
                if new_thing:
                    item1 = {"model": device.type, "temp": device.temp, "state": device.relay_1, "status": 1,
                             "thing": device.thing, "current": device.current, "freeMemory": device.mem,
                             "upTime": device.uptime, "ip": device.ip, "name": device.thing, "lock": device.lock_1,
                             "image": 0, "timers": []}
                    thing.ITEMSComplete.append(item1)

            thing.ITEMS = []
            for item in list(thing.ITEMSComplete):
                if item["status"] == 1:
                    thing.ITEMS.append(
                        {"thing": item["thing"], "name": item["name"], "state": item["state"], "lock": item["lock"],
                         "temp": item["temp"], "image": item["image"]})

            if device.thing not in thing.things_time:
                print("new", device.thing)
                thing.things_time[device.thing] = 0

            for key in dict(thing.clients):
                try:

                    if thing.clients[key][1].thing == device.thing:
                        thing.clients[key][2] = time.time()
                except Exception as e:
                    print e
                    main.add_exception("checking 2", str(e))

            time_start = calendar.timegm(time.gmtime())
            if (time_start - thing.things_time[device.thing]) > 60 or device.changed:  # 60 seconds
                self.put_cloud(device)

            self.result[dic["function"]] = True
        except Exception as e:
            self.result[dic["function"]] = False
            main.add_exception("left exception", str(e))
            print(e, "hele")

    def current_converter(self, current):
        try:
            res, minn, maxx = 0, 0, 50
            if current > 0:
                while maxx - minn >= 1:
                    x = (minn + maxx) // 2

                    if minn == x:
                        res = x + (current - self.current_table[x]) / (
                                self.current_table[x + 1] - self.current_table[x])
                        break
                    if current == self.current_table[x]:
                        res = x
                        break
                    elif current > self.current_table[x]:
                        minn = x
                    elif current < self.current_table[x]:
                        maxx = x

            return round(res / 10.0, 1)
        except Exception as e:
            print(e)
            main.add_exception("current_converter", str(e))

    def update(self, dic):
        try:
            device, data = dic["data"]
            # print ("response update", device, data)

            if data["response"] == "OK":
                device.result["update_response"][data["seq"]] = 1
            else:
                device.result["update_response"][data["seq"]] = 0

            self.result[dic["function"]] = True
        except Exception as e:
            self.result[dic["function"]] = False
            print(e)

    def set_password(self, dic):
        try:
            device, data = dic["data"]
            print ("response update", device, data)

            if data["response"] == "OK":
                device.result["set_password_response"][data["seq"]] = 1
            else:
                device.result["set_password_response"][data["seq"]] = 0

            self.result[dic["function"]] = True
        except Exception as e:
            self.result[dic["function"]] = False
            print(e)

    def setrelay1(self, dic):
        try:

            device, data = dic["data"]
            # print ("response setrealy1", device, data)

            if data["response"] == "OK":
                device.result["set_relay_1_response"][data["seq"]] = 1
                time.sleep(0.3)
                self.put_cloud(device)

            else:
                device.result["set_relay_1_response"][data["seq"]] = 0

            self.result[dic["function"]] = True
        except Exception as e:
            self.result[dic["function"]] = False
            print(e)

    def setrelay2(self, dic):
        try:
            device, data = dic["data"]

            if data["response"] == "OK":
                device.result["set_relay_2_response"][data["seq"]] = 1
                time.sleep(0.3)
                self.put_cloud(device)
            else:
                device.result["set_relay_2_response"][data["seq"]] = 0
            self.result[dic["function"]] = True
        except Exception as e:
            self.result[dic["function"]] = False
            print(e)

    def setlock1(self, dic):
        try:

            device, data = dic["data"]
            # print ("response setlock1", device, data)

            if data["response"] == "OK":
                device.result["set_lock_1_response"][data["seq"]] = 1

            else:
                device.result["set_lock_1_response"][data["seq"]] = 0

            self.result[dic["function"]] = True
        except Exception as e:
            self.result[dic["function"]] = False
            print(e)

    def setlock2(self, dic):
        try:
            device, data = dic["data"]

            if data["response"] == "OK":
                device.result["set_lock_2_response"][data["seq"]] = 1

            else:
                device.result["set_lock_2_response"][data["seq"]] = 0
            self.result[dic["function"]] = True
        except Exception as e:
            self.result[dic["function"]] = False
            print(e)

    def setnetwork(self, dic):
        try:
            device, data = dic["data"]

            if data["response"] == "OK":
                device.result["set_network_response"][data["seq"]] = 1

            else:
                device.result["set_network_response"][data["seq"]] = 0

            self.result[dic["function"]] = True
        except Exception as e:
            self.result[dic["function"]] = False
            print(e)

    @staticmethod
    def put_cloud(device):
        global API
        device.changed = False
        # print ("sent", device.thing, device.relay_1, device.relay_2)
        thing.things_time[device.thing] = calendar.timegm(time.gmtime())

        if device.type == "SANA-102" or device.type == "SANA-102s":
            body = {"thing": device.thing + "-1", "time": calendar.timegm(time.gmtime()), "temp": device.temp,
                    "name": device.thing + "-1", "state": device.relay_1, "current": 0, "ip": device.ip}

            if web_socket_client.request_queue1.full():
                web_socket_client.request_queue1.get()

            web_socket_client.request_queue1.put(body)

            body = {"thing": device.thing + "-2", "time": calendar.timegm(time.gmtime()), "temp": device.temp,
                    "name": device.thing + "-2", "state": device.relay_2, "current": 0, "ip": device.ip}

            if web_socket_client.request_queue1.full():
                web_socket_client.request_queue1.get()

            web_socket_client.request_queue1.put(body)

        elif device.type == "SANA-101" or device.type == "SANA-101s" or device.type == "SANA-101P":
            body = {"thing": device.thing, "time": calendar.timegm(time.gmtime()), "temp": device.temp,
                    "name": device.thing, "state": device.relay_1, "current": device.current, "ip": device.ip}

            if web_socket_client.request_queue1.full():
                web_socket_client.request_queue1.get()

            web_socket_client.request_queue1.put(body)

    def db_setting_th(self):
        global debug

        try:
            while True:

                dic = self.queue.get()

                if dic["module"] == "setting":
                    self.run_setting_functions(dic)

        except Exception as e:
            print(e)
            print("\tDB_Setting FAILED")
