from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import json
import threading
import time
import ast
import datetime
import os
import sqlite3 as lite
import calendar
import sys
import subprocess
import web_socket_client
from operator import itemgetter
import operator

import thing
import mob
import db

db_setting_address = '/root/app.db'
debug = False

ws_server = None
PORT = 0
exception_log = {}
disconnection_log = {}
clients_lock = threading.RLock()
wifi_ssid = None
wifi_password = None
wifi_my_password = None
wifi_mode = None
wifi_enc = None
back_off = 120
tmp_mode = False
DEFAULT_TIME = 120  # sec
COUNT = 0


def shell_command(command):
    try:
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output = p.communicate()

        for i in range(100):
            time.sleep(0.001)
            if not (p.returncode is None):
                break

        if p.returncode is None:
            print("not exited yet,exit by hand")
            p.terminate()

        return output[0]
    except Exception as e:
        res = str(e).find("memory")
        if res != -1:
            sys.exit(0)


def last_6_mac():
    point = subprocess.check_output('cat /sys/class/net/apcli0/address', shell=True)

    last_part = str(point[9:11]).upper() + str(point[12:14]).upper() + str(point[15:17]).upper()

    return last_part


def has_wifi_connection():
    try:

        route = shell_command("route | grep default")
        InAcc = subprocess.call('ping -q -c 1 -W 2 ' + route, shell=True, stdout=open(os.devnull, 'w'),
                                stderr=open(os.devnull, 'w'))

        if InAcc == 0:
            if debug:
                print("WIFI ACCESS")
            return True
        else:
            if debug:
                print("NO WIFI ACCESS")
            return False

    except Exception as e:
        # print(e)
        pass


def set_wifi(mode, my_password):
    if mode == "ap":
        print "in main set ap"
        last_six = last_6_mac()

        print last_six
        shell_command('uci set wireless.ap.ssid=' + "Simorq-" + "112")
        shell_command('uci set wireless.ap.encryption=psk2')
        shell_command('uci set wireless.ap.key=' + my_password)
        shell_command('uci commit')
        shell_command('wifi_mode ap')


def set_wife(my_password, ssid, password, enc):
    try:
        print "in set online mode with enc ->", enc
        last_six = last_6_mac()
        print last_six

        shell_command('wifi_mode ap')
        time.sleep(4)

        shell_command('uci set wireless.sta.ssid=' + ssid)
        shell_command('uci set wireless.sta.encryption=' + enc)
        shell_command('uci set wireless.sta.key=' + password)

        shell_command('uci set wireless.ap.ssid=' + "Simorq-" + "112")
        shell_command('uci set wireless.ap.encryption=psk2')
        shell_command('uci set wireless.ap.key=' + my_password)
        shell_command('uci set wireless.radio0.linkit_mode=apsta')
        time.sleep(0.5)
        shell_command('uci commit')
        time.sleep(1)
        shell_command('wifi')

        return True
    except Exception as e:
        print e
        add_exception("set wife", str(e))
        return False


def get_wifi():
    global debug
    res = None

    try:
        # reader.shell_command("ifconfig ra0 up")

        res = str(shell_command('iwinfo ra0 scan'))

    except Exception as e:
        print(e)
        add_exception("get_wifi", str(e))

    wifi_list = []

    if res:
        while True:
            try:
                wifii = {}
                point_s = res.find("Address:")
                point_e1 = res.find("ESSID") - 11
                if point_s != -1:
                    mac = res[point_s + 9:point_e1]
                    if debug:
                        print("mac", mac)
                    wifii["mac"] = mac
                    res = res[point_e1 + 1:]
                    point_s = res.find('ESSID:')
                    point_e2 = res.find("\n")
                    if point_s != -1:
                        ESSID = res[point_s + 8:point_e2 - 1]
                        if debug:
                            print("ESSID", ESSID)
                        wifii["ESSID"] = ESSID
                        res = res[point_e2 + 1:]
                        point_s = res.find('Channel:')
                        point_e3 = res.find("\n")
                        if point_s != -1:
                            Channel = res[point_s + 9:point_e3]
                            if debug:
                                print("Channel", Channel)
                            wifii["Channel"] = Channel
                            res = res[point_e3 + 1:]
                            point_s = res.find('Quality:')
                            point_e4 = res.find("/100")
                            if point_s != -1:
                                Quality = res[point_s + 9:point_e4]
                                if debug:
                                    print("Quality", Quality)
                                wifii["Quality"] = Quality
                                res = res[point_e4 + 5:]
                                point_s = res.find('Encryption:')
                                point_e5 = res.find("\n")
                                if point_s != -1:
                                    Encryption = res[point_s + 12:point_s + 16]
                                    if debug:
                                        print("Encryption", Encryption)
                                    wifii["Encryption"] = Encryption
                                    res = res[point_e5 + 1:]
                                    wifi_list.append(wifii)

                                else:
                                    break
                            else:
                                break
                        else:
                            break
                    else:
                        break
                else:
                    break
            except Exception as e:
                print(e)
                add_exception("get_wifi", str(e))
    return wifi_list


def monitor():
    while True:
        not_connected = []
        time_start = calendar.timegm(time.gmtime())
        try:
            # print("start")
            for th in thing.clients:
                # print("th:", thing.clients[th])
                # print("difference", th, time_start - thing.clients[th].time_updated)
                if (time_start - thing.clients[th].time_updated) > 13:
                    not_connected.append(thing.clients[th])
            try:
                for item in not_connected:
                    thing.clients = {key: value for key, value in thing.clients.items() if value != item}
                    item.connection.close()
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)
            add_exception("monitor", str(e))
        time.sleep(5)


def update_profiles(ID):
    try:
        print ("in update profile2")
        for dic in mob.profiles:
            if dic["id"] == int(ID):
                print ("dic in update", dic)

                con = lite.connect(db_setting_address)
                con.row_factory = lite.Row
                with con:
                    cur = con.cursor()

                    cur.execute("UPDATE profile SET state=? WHERE Id=?", (1, dic["id"]))
                    con.commit()
                con.close()
                for d in dic["data"]["things"]:
                    print ("dic d", d)
                    thg = d["thing"]
                    number = d["index"]
                    value = int(d["relay"])
                    try:
                        packet = thing.things_connected[thg]

                        if number == 1:
                            print("11111")
                            val = packet.set_relay_1([value])
                            print("before 200 relay 1", val)
                        elif number == 2:
                            print("222222")
                            val = packet.set_relay_2([value])
                            print("before 200 relay 2", val)

                    except Exception as e:
                        add_exception("update_profiles", "clients" + str(e))

                dic["state"] = 1
            else:
                if dic["state"] == 1:
                    con = lite.connect(db_setting_address)
                    con.row_factory = lite.Row
                    with con:
                        cur = con.cursor()

                        cur.execute("UPDATE profile SET state=? WHERE Id=?", (0, dic["id"]))
                        con.commit()
                    con.close()

                dic["state"] = 0

    except Exception as e:
        print(e)
        add_exception("update_profiles", str(e))


def load_from_db():
    global wifi_ssid, wifi_password, wifi_my_password, wifi_mode, wifi_enc

    try:
        con = lite.connect(db_setting_address)
        con.row_factory = lite.Row

        with con:
            cur = con.cursor()
            cur.execute('SELECT * FROM thing')

            for row in cur:

                if row["timers"]:
                    thing.ITEMSComplete.append({"thing": row["thing"], "timers": ast.literal_eval(row["timers"]),
                                                "name": row["name"], "image": row["image"], "lock": row["lock"],
                                                "status": 0, "state": 0})
                else:
                    thing.ITEMSComplete.append({"thing": row["thing"], "name": row["name"], "image": row["image"],
                                                "lock": row["lock"], "status": 0, "timers": [], "state": 0})
        i = 0
        with con:
            cur = con.cursor()
            cur.execute('SELECT * FROM profile')
            for row in cur:

                if row["items"]:
                    if row["timers"]:

                        thing.PROFILESComplete.append({"profileId": row["profileId"], "name": row["name"],
                                                       "things": ast.literal_eval(row["items"]), "state": row["state"],
                                                       "timers": ast.literal_eval(row["timers"])})
                    else:
                        thing.PROFILESComplete.append({"profileId": row["profileId"], "name": row["name"],
                                                       "things": ast.literal_eval(row["items"]), "state": row["state"],
                                                       "timers": []})
                else:

                    if row["timers"]:

                        thing.PROFILESComplete.append({"profileId": row["profileId"], "name": row["name"], "things": [],
                                                       "state": row["state"],
                                                       "timers": ast.literal_eval(row["timers"])})
                    else:

                        thing.PROFILESComplete.append(
                            {"profileId": row["profileId"], "name": row["name"], "state": row["state"],
                             "things": [], "timers": []})
                i += 1

        for item in thing.ITEMSComplete:
            if item["status"] == 1:
                thing.ITEMS.append(
                    {"thing": item["thing"], "name": item["name"], "state": item["state"], "lock": item["lock"],
                     "temp": item["temp"], "image": item["image"]})

        for profile in thing.PROFILESComplete:
            thing.PROFILES.append(
                {"profileId": profile["profileId"], "name": profile["name"], "state": profile["state"]})

        setProfileNumber()
        setTimerNumber()

        with con:
            cur = con.cursor()
            cur.execute("SELECT * FROM network")
            for row in cur:
                wifi_ssid = row["ssid"]
                wifi_mode = row["mode"]
                wifi_enc = row["enc"]
                wifi_password = row["password"]
                wifi_my_password = row["my_password"]
                mob.API_KEY = row["api_key"]

            print ("wifi:", wifi_ssid, wifi_mode, wifi_enc, wifi_password, wifi_my_password, mob.API_KEY)

        with con:
            cur = con.cursor()
            cur.execute("SELECT * FROM grouping")
            for row in cur:
                thing.GROUPS.append({"groupId": row["groupId"], "things": ast.literal_eval(row["things"])})

        with con:
            cur = con.cursor()
            cur.execute("SELECT * FROM version")

            thing.VERSION = {}
            for row in cur:
                thing.VERSION["SANA-101"] = row["sana101"]
                thing.VERSION["SANA-101P"] = row["sana101p"]
                thing.VERSION["SANA-102"] = row["sana102"]
                thing.VERSION["SANA-102s"] = row["sana102s"]
                thing.VERSION["SANA-P30"] = row["sanap30"]

        con.close()

    except Exception as e:
        print(e)
        add_exception("load_from_db", str(e))


def add_exception(key, err):
    global exception_log

    try:
        exception_log[key] = err

        l2 = str(datetime.date.today())
        l2 = l2.replace(" ", "")
        l2 = l2.replace(":", "")

        dat = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if not os.path.exists('/root/'):
            os.makedirs('/root/')

        file_name = "error." + l2 + ".txt"

        with open("/root/" + file_name, "a") as my_file:
            my_file.write(dat + " : " + key + ": " + "-->" + err + "\n")

    except Exception as e:
        print(e)
        time.sleep(1)


def setProfileNumber():
    try:
        for dic in thing.PROFILESComplete:
            print "xxx", dic["profileId"]
            if dic["profileId"] >= thing.PROFILE_NUMBER:
                thing.PROFILE_NUMBER = dic["profileId"] + 1
        print "timer:", thing.PROFILE_NUMBER
    except Exception as e:
        print e
        add_exception("setProfileNumber", str(e))


def setTimerNumber():
    try:
        for dic in thing.ITEMSComplete:
            for timer in dic["timers"]:
                if timer["timerId"] >= thing.TIMER_NUMBER:
                    thing.TIMER_NUMBER = timer["timerId"] + 1

        for dic in thing.PROFILESComplete:
            for timer in dic["timers"]:
                if timer["timerId"] >= thing.TIMER_NUMBER:
                    thing.TIMER_NUMBER = timer["timerId"] + 1
        print "timer:", thing.TIMER_NUMBER
    except Exception as e:
        print e
        add_exception("setTimerNumber", str(e))


def update_request(ws, parsed_json):
    # print("in update")
    try:
        # print("update resp:xxx", parsed_json["response"])

        for cln in thing.clients:
            if thing.clients[cln][0] == ws:
                db.db_setting.wait_for_result(
                    {"module": "setting", "function": "update", "data": (thing.clients[ws.address][1], parsed_json)})
                break

        return {"action": "info", "response": "OK"}

    except Exception as e:
        print(e)
        add_exception("update", str(e))
        return {"action": "info", "response": "OK"}


def set_password_pool(ws, parsed_json):
    for cln in thing.clients:
        if thing.clients[cln][0] == ws:
            db.db_setting.wait_for_result(
                {"module": "setting", "function": "set_password", "data": (thing.clients[ws.address][1], parsed_json)})
            break


def set_password(ws, parsed_json):
    print("in set_password")
    try:
        print(parsed_json["response"])

        a = threading.Thread(name="check", args=(ws, parsed_json), target=set_password_pool)
        a.setDaemon(True)
        a.start()

        return {"action": "info", "response": "OK"}

    except Exception as e:
        print(e)
        add_exception("set_password", str(e))
        return {"action": "info", "response": "OK"}


def set_relay1_pool(ws, parsed_json):
    # print "IN SET RELAY1 POOOOOL"
    for cln in thing.clients:
        if thing.clients[cln][0] == ws:
            db.db_setting.wait_for_result(
                {"module": "setting", "function": "setrelay1", "data": (thing.clients[ws.address][1], parsed_json)})
            break


def setrelay1(ws, parsed_json):
    # print("in setrelay1 resp")
    try:
        # print(parsed_json["response"])

        a = threading.Thread(name="check", args=(ws, parsed_json), target=set_relay1_pool)
        a.setDaemon(True)
        a.start()

        return {"action": "info", "response": "OK"}

    except Exception as e:
        print(e)
        add_exception("setrelay1", str(e))
        return {"action": "info", "response": "OK"}


def getrelay1(ws, parsed_json):
    try:
        print("in getrelay1")
        print (ws.address, parsed_json["value"])

    except Exception as e:
        print(e)
        return {"action": str(parsed_json["action"]),
                "response": {"text": "FAIL", "code": 408}}


def set_relay2_pool(ws, parsed_json):
    # print "IN SET RELAY2 POOOOOL"
    for cln in thing.clients:
        if thing.clients[cln][0] == ws:
            db.db_setting.wait_for_result(
                {"module": "setting", "function": "setrelay2", "data": (thing.clients[ws.address][1], parsed_json)})
            break


def setrelay2(ws, parsed_json):
    # print("in setrelay2 resp")
    try:
        # print(parsed_json["response"])

        a = threading.Thread(name="check", args=(ws, parsed_json), target=set_relay2_pool)
        a.setDaemon(True)
        a.start()

        return {"action": "info", "response": "OK"}
    except Exception as e:
        print(e)
        add_exception("setrelay2", str(e))
        return {"action": "info", "response": "Fail"}


def set_lock1_pool(ws, parsed_json):
    print "IN SET lock1 POOOOOL"
    for cln in thing.clients:
        if thing.clients[cln][0] == ws:
            db.db_setting.wait_for_result(
                {"module": "setting", "function": "setlock1", "data": (thing.clients[ws.address][1], parsed_json)})
            break


def setlock1(ws, parsed_json):
    print("in setlock1")
    try:
        print(parsed_json["response"])

        a = threading.Thread(name="check", args=(ws, parsed_json), target=set_lock1_pool)
        a.setDaemon(True)
        a.start()

        return {"action": "info", "response": "OK"}
    except Exception as e:
        print(e)
        add_exception("setlock1", str(e))
        return {"action": "info", "response": "Fail"}


def set_lock2_pool(ws, parsed_json):
    print "IN SET lock2 POOOOOL"
    for cln in thing.clients:
        if thing.clients[cln][0] == ws:
            db.db_setting.wait_for_result(
                {"module": "setting", "function": "setlock2", "data": (thing.clients[ws.address][1], parsed_json)})
            break


def setlock2(ws, parsed_json):
    print("in setlock2")
    try:
        print(parsed_json["response"])

        a = threading.Thread(name="check", args=(ws, parsed_json), target=set_lock2_pool)
        a.setDaemon(True)
        a.start()

        return {"action": "info", "response": "OK"}
    except Exception as e:
        print(e)
        add_exception("setlock2", str(e))
        return {"action": "info", "response": "Fail"}


def getrelay2(ws, parsed_json):
    try:
        print("in getrelay2")
        print (ws.address, parsed_json["value"])

    except Exception as e:
        print(e)
        return {"action": str(parsed_json["action"]),
                "response": {"text": "FAIL", "code": 408}}


def settemp(ws, parsed_json):
    print("in settemp")
    try:
        print(ws.address, parsed_json["response"])

    except Exception as e:
        print(e)
        return {"action": str(parsed_json["action"]),
                "response": {"text": "FAIL", "code": 408}}


def gettemp(ws, parsed_json):
    try:
        print("in gettemp")
        print (ws.address, parsed_json["value"])

    except Exception as e:
        print(e)
        return {"action": str(parsed_json["action"]),
                "response": {"text": "FAIL", "code": 408}}


def setcurrent(ws, parsed_json):
    print("in setcurrent")
    try:
        print(ws.address, parsed_json["response"])

    except Exception as e:
        print(e)
        return {"action": str(parsed_json["action"]),
                "response": {"text": "FAIL", "code": 408}}


def getcurrent(ws, parsed_json):
    try:
        print("in getcurrent")
        print (ws.address, parsed_json["value"])

    except Exception as e:
        print(e)
        return {"action": str(parsed_json["action"]),
                "response": {"text": "FAIL", "code": 408}}


def setnetwork(ws, parsed_json):
    print("in setnetwork ws response")
    try:
        print(ws.address, parsed_json["response"])

        for cln in thing.clients:
            if thing.clients[cln][0] == ws:
                db.db_setting.wait_for_result(
                    {"module": "setting", "function": "setnetwork", "data": (thing.clients[ws.address][1], parsed_json)})
                break

    except Exception as e:
        print(e)
        return {"action": str(parsed_json["action"]),
                "response": {"text": "FAIL", "code": 408}}


def getnetwork(ws, parsed_json):
    try:
        print("in getnetwork")
        print (ws.address, parsed_json["ssid"], parsed_json["password"])

    except Exception as e:
        print(e)
        return {"action": str(parsed_json["action"]),
                "response": {"text": "FAIL", "code": 408}}


def info(ws, parsed_json):
    try:
        for cln in thing.clients:
            if thing.clients[cln][0] == ws:
                thing.clients[ws.address][2] = time.time()

                db.db_setting.queue.put(
                    {"module": "setting", "function": "info", "data": (thing.clients[ws.address][1], parsed_json)})
                break

        return {"action": "info", "response": "OK"}
    except Exception as e:
        print e
        add_exception("info", str(e))
        return {"action": "info", "response": "Fail"}


actions = {"info": info,
           "setrelay1": setrelay1,
           "getrelay1": getrelay1,
           "setrelay2": setrelay2,
           "getrelay2": getrelay2,
           "settemp": settemp,
           "gettemp": gettemp,
           "setlock1": setlock1,
           "setlock2": setlock2,
           "setcurrent": setcurrent,
           "getcurrent": getcurrent,
           "setnetwork": setnetwork,
           "update": update_request,
           }


def wifi_connected():
    try:
        route = shell_command("route | grep default")

        while "  " in route:
            route = route.replace("  ", " ")

        if route == "":
            print "no route!"
        else:
            items = route.split(" ")

            res = shell_command("cat /proc/net/arp | grep " + items[1])

            while "  " in res:
                res = res.replace("  ", " ")

            if res == "":
                print "no gateway yet"
            else:
                res_list = res.split(" ")

                if res_list[2].lower() == "0x2":
                    print "FLAG 0x2!"
                    return True
                elif res_list[2].lower() == "0x0":
                    print "FLAG 0x0!"
        return False
    except Exception as e:
        print e
        add_exception("wifi connected", str(e))


def check_wifi(max_try):
    global back_off, tmp_mode, DEFAULT_TIME
    connected = False
    i = 0
    try:
        while not connected and i < max_try:
            ap_list = get_wifi()
            for ap in ap_list:
                if ap["ESSID"] == wifi_ssid:
                    if wifi_connected():
                        connected = True
                        back_off = DEFAULT_TIME
                        tmp_mode = False
                        break
            i += 1
        return connected
    except Exception as e:
        print e
        add_exception("check wifi", str(e))
        return False


def checking():
    global ws_server, clients_lock, wifi_ssid, wifi_mode, wifi_password, wifi_my_password, back_off, tmp_mode, \
        DEFAULT_TIME, disconnection_log

    time.sleep(5)  # wait for load db
    ping_cmd = {"action": "info"}
    later = time.time()
    time_end = calendar.timegm(time.gmtime())

    while True:
        now1 = time.time()
        try:
            pass
            # print ("watch")
            # shell_command("echo 1 > /dev/watchdog1")
        except Exception as e:
            print e
            add_exception("checking 1", str(e))

        try:
            if now1 - time_end > 40:  # 1 hour
                print "check for update"
                time_end = time.time()
                con = lite.connect(db_setting_address)
                con.row_factory = lite.Row

                with con:
                    cur = con.cursor()
                    cur.execute("SELECT * FROM version")

                    thing.VERSION = {}
                    for row in cur:
                        thing.VERSION["SANA-101"] = row["sana101"]
                        thing.VERSION["SANA-101P"] = row["sana101p"]
                        thing.VERSION["SANA-102"] = row["sana102"]
                        thing.VERSION["SANA-102s"] = row["sana102s"]
                        thing.VERSION["SANA-P30"] = row["sanap30"]

                print "version", thing.VERSION
                con.close()
        except Exception as e:
            print e
            add_exception("update version in main.checking", str(e))

        try:
            for t in thing.ITEMSComplete:
                pass
                # print ("thing", t)

            # print "******************************************************"
            # print "CLIENTS:", thing.clients
            # print "******************************************************"
            # print "CONNECTED:", thing.things_connected
            # print "******************************************************"
            for key in dict(thing.clients):
                # print "CLIENT:", key

                try:
                    server = thing.clients[key][0]

                    # print ("client time:", now1 - thing.clients[key][2])
                    if (now1 - thing.clients[key][2]) > 13:

                        server.close()
                        with thing.things_connected_lock:

                            # add_exception("client found", str(self.address))
                            # print ("client found", str(server.address))
                            p = thing.clients[key][1]

                            if p.thing != "NA":
                                mob.setItemParam(p.thing, {"status": 0})
                                mob.setItemParam(p.thing + "-1", {"status": 0})
                                mob.setItemParam(p.thing + "-2", {"status": 0})
                                # p.db_setting.is_on = False
                                # p.db_setting.wait_for_result({"module": "test", "function": "info", "data": ""})

                                if p.thing in thing.things_connected:
                                    del thing.things_connected[p.thing]

                            # add_exception("in thing deleted", str(p.thing))
                            with clients_lock:
                                print ("xxxxxxxxxxxxxxxxxxxxxxxx:", str(p.thing), thing.clients[key][2], time.time(),
                                       now1, thing.clients[key][2] - time.time())
                                del thing.clients[server.address]
                                # add_exception("in clients deleted", str(p.thing))
                                # print ("in things_connected deleted")
                            # add_exception("thing left", str(self.address) + " " + str(p.thing))

                        register_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        con = lite.connect(db_setting_address)
                        con.row_factory = lite.Row

                        if p.thing in dict(disconnection_log):
                            disconnection_log[p.thing] += 1
                        else:
                            disconnection_log[p.thing] = 1

                        with con:
                            cur = con.cursor()
                            cur.execute("INSERT into log (event_id,log_description,Time) values(?,?,?)",
                                        (p.thing, disconnection_log[p.thing], register_time))
                            con.commit()

                            cur.close()

                        continue
                    server.sendMessage(json.dumps(ping_cmd))

                except Exception as e:
                    print e
                    add_exception("checking 2", str(e))

            # print "************************************"
            print ("keys", len(thing.things_connected))

            # sorted_x = sorted(disconnection_log.items(), key=operator.itemgetter(1))
            # print "DISCONNECTION:", sorted_x
            # for key in dict(sorted_x):
            #     print "DISCONNECTION:", key, sorted_x[key]
            # print "************************************"
            time.sleep(5)
        except Exception as e:
            print e
            add_exception("checking 3", str(e))

            # try:
            #     if wifi_mode == "online":
            #         now = time.time()
            #         if int(abs(now - later)) > back_off:
            #             if tmp_mode:
            #                 later = time.time()
            #                 print "in temp mode -> try to go online", back_off
            #                 ap_list = get_wifi()
            #                 for ap in ap_list:
            #                     if ap["ESSID"] == wifi_ssid:
            #                         print "in check ssid found -> set online"
            #                         if set_wife(wifi_my_password, wifi_ssid, wifi_password, wifi_enc):
            #                             tmp_mode = False
            #         print ("time:", int(abs(now - later)), back_off)
            #         if int(abs(now - later)) > DEFAULT_TIME:
            #             if not tmp_mode:
            #                 later = time.time()
            #                 print "not tmp mode", back_off
            #                 result = check_wifi(2)
            #                 print "wifi result", result
            #                 if not result:
            #                     print "wifi not connected -> go to ap mode"
            #                     tmp_mode = True
            #                     back_off *= 2
            #                     if back_off > 86400:  # 1 day
            #                         back_off = 86400
            #                     set_wifi("ap", wifi_my_password)
            #
            # except Exception as e:
            #     print e


def check_timers():
    while True:

        try:
            now = calendar.timegm(time.gmtime())

            for thg in thing.ITEMSComplete:
                for timer in list(thg["timers"]):
                    # print "now:", timer["time"], str(now)

                    if timer["time"] <= str(now):
                        t = thg["thing"].replace("-1", "").replace("-2", "")
                        if t in thing.things_connected:
                            packet = thing.things_connected[t]
                            if not packet.set_relay([timer["state"]], thg["thing"]):
                                packet.set_relay([timer["state"]], thg["thing"])
                                print "relay not successful"
                        thg["timers"].remove(timer)

                        con = lite.connect(db_setting_address)
                        with con:
                            cur = con.cursor()
                            cur.execute("UPDATE thing SET timers=? WHERE thing=?",
                                        (json.dumps(thg["timers"]), thg["thing"]))
                            con.commit()

            now = calendar.timegm(time.gmtime())
            for p in thing.PROFILESComplete:
                for timer in list(p["timers"]):
                    # print "now:", timer["time"], str(now)

                    if timer["time"] <= str(now):
                        p["state"] = 1
                        for thg in p["things"]:
                            t = thg["thing"].replace("-1", "").replace("-2", "")
                            if t in thing.things_connected:
                                packet = thing.things_connected[t]
                                if not packet.set_relay([thg["state"]], thg["thing"]):
                                    packet.set_relay([thg["state"]], thg["thing"])
                        p["timers"].remove(timer)

                        con = lite.connect(db_setting_address)
                        with con:
                            cur = con.cursor()
                            cur.execute("UPDATE profile SET timers=?,state=1 WHERE profileId=?",
                                        (json.dumps(p["timers"]), p["profileId"]))
                            con.commit()

                        for pp in thing.PROFILESComplete:
                            if pp["profileId"] != p["profileId"]:
                                pp["state"] = 0
                                with con:
                                    cur = con.cursor()
                                    cur.execute("UPDATE profile SET state=? WHERE profileId=?", (0, pp["profileId"]))
                                    con.commit()
                        con.close()

                        thing.PROFILES = []
                        for profile in thing.PROFILESComplete:
                            thing.PROFILES.append(
                                {"profileId": profile["profileId"], "name": profile["name"], "state": profile["state"]})

        except Exception as e:
            print e
            add_exception("check_timers", str(e))

        time.sleep(5)


class SimpleEcho(WebSocket):
    def handleMessage(self):
        try:
            message = self.data
            # print ("dataa:", message)

            # print("Client(%d) said: %s" % (client['id'], message))
            # print ("new SANA message received", message)

            res = json.loads(message)

            if "action" in res:
                if res["action"] == "error":
                    print ("error", res["response"])
                if res["action"] in actions:
                    end = actions[res["action"]](self, res)

                    resp = json.dumps(end)
                    # print("RESPONSE::::", resp)

                    self.sendMessage(resp)
                else:
                    end = {"action": res["action"], "response": "Invalid Action"}
                    print("ERROR RESPONSE::::", end)
                    resp = json.dumps(end)

                    self.sendMessage(resp)

            else:
                end = {"action": "error", "response": "message should have action object"}
                print("ERROR RESPONSE::::", end)
                resp = json.dumps(end)

                self.sendMessage(resp)
        except Exception as e:
            print e
            add_exception("handleMessage", str(e))

    def handleConnected(self):
        global COUNT, disconnection_log
        print(self.address, 'connected')
        try:
            print("New client connected and was given address", self.address)
            # add_exception("new client", str(self.address))
            # server.send_message_to_all("Hey all, a new client has joined us")

            p = thing.Thing(self)

            # p.db_setting.start()
            t = time.time()
            thing.clients[self.address] = [self, p, t]
            COUNT += 1

        except Exception as e:
            print e
            add_exception("handleConnected", str(e))

    def handleClose(self):
        print(self.address, 'closed')
        global clients_lock, disconnection_log

        print("Client() disconnected", self.address)
        # add_exception("client left", str(self.address))

        try:
            with thing.things_connected_lock:

                for cln in dict(thing.clients):

                    if thing.clients[cln][0] == self:

                        # add_exception("client found", str(self.address))
                        print ("client found", str(self.address))
                        p = thing.clients[cln][1]

                        if p.thing != "NA":
                            mob.setItemParam(p.thing, {"status": 0})
                            mob.setItemParam(p.thing + "-1", {"status": 0})
                            mob.setItemParam(p.thing + "-2", {"status": 0})
                            # p.db_setting.is_on = False
                            # p.db_setting.wait_for_result({"module": "test", "function": "info", "data": ""})
                            if p.thing in thing.things_connected:
                                del thing.things_connected[p.thing]

                        # add_exception("in thing deleted", str(p.thing))
                        with clients_lock:

                            # print ("in things_connected deleted1", str(p.thing))

                            # print ("xxxxxxxxxxxxxxxxxxxxxxxx111:", str(p.thing), thing.clients[cln][2], time.time(),
                                   thing.clients[cln][2] - time.time())
                            del thing.clients[self.address]

                            # add_exception("in clients deleted", str(p.thing))

                        register_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        con = lite.connect(db_setting_address)
                        con.row_factory = lite.Row

                        if p.thing in dict(disconnection_log):
                            disconnection_log[p.thing] += 1
                        else:
                            disconnection_log[p.thing] = 1

                        with con:
                            cur = con.cursor()
                            cur.execute("INSERT into log (event_id,log_description,Time) values(?,?,?)",
                                        (p.thing, disconnection_log[p.thing], register_time))
                            con.commit()

                            cur.close()

                        # add_exception("thing left", str(self.address) + " " + str(p.thing))
                        break

        except Exception as e:
            print e
            add_exception("handleClose", str(e))


def main(argv):
    global ws_server, PORT, wifi_mode

    load_from_db()

    db.db_setting = db.Setting()
    db.db_setting.start()
    if wifi_mode != "repeater":
        c = threading.Thread(name="cloud", target=web_socket_client.start)
        c.setDaemon(True)
        c.start()

    b = threading.Thread(name="api", target=mob.init_api)
    b.setDaemon(True)
    b.start()

    a = threading.Thread(name="check", target=checking)
    a.setDaemon(True)
    a.start()

    d = threading.Thread(name="check_timers", target=check_timers)
    d.setDaemon(True)
    d.start()

    ws_server = SimpleWebSocketServer('', 9001, SimpleEcho)
    ws_server.serveforever()


if __name__ == "__main__":
    main(sys.argv)
