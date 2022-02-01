import websocket
import calendar
import threading
import Queue
import time
import json
import sys
import datetime
import subprocess
import math
from operator import itemgetter
import sqlite3 as lite

import main
import thing
import mob
import db


IDEAL = 0
OPEN = 1
CLOSING = 2
CLOSED = 3
ws_connection = IDEAL
web_sock = None
answered = False
current_answered = False
chart = {}
current_chart = {}

time_end = calendar.timegm(time.gmtime())
BACK_OFF = 1
sent_cloud = 0
tot_get = 0
SEQUENCE = 0
request_queue1 = Queue.Queue(40)


def send_cloud():
    global sent_cloud, tot_get, SEQUENCE, web_sock, ws_connection, request_queue1

    while True:
        try:

            if ws_connection == OPEN:

                body = request_queue1.get()

                msg = {"action": "info", "body": body}
                cmd = {"seq": "123", "api_key": mob.API_KEY, "msg": msg}
                # print ("ws web_sock:", web_sock, cmd)
                bb = json.dumps(cmd)

                web_sock.send(bb)
                # web_sock.send("#!hello!#")

        except Exception as e:
            print e
        time.sleep(0.3)


def info(parsed_json):
    print "info response", parsed_json


def packet_received(parsed_json):
    print("in packet_received")
    try:
        seq = parsed_json["seq"]

    except Exception as e:
        # reader.my_reader.db_data.add_exception("websocket.getInfo", str(e))
        print(e)


def thingChart(parsed_json):
    global chart, answered

    print("in packet_received")
    print parsed_json
    try:
        chart = parsed_json["msg"]["chart"]
        answered = True

    except Exception as e:
        print(e)


def currentChart(parsed_json):
    global current_chart, current_answered

    print("in packet_received")
    print parsed_json
    try:
        current_chart = parsed_json["msg"]["chart"]
        current_answered = True

    except Exception as e:
        print e


def get_items(parsed_json):
    print "in get_items", parsed_json
    try:
        if ws_connection == OPEN:
            new_list = list(thing.ITEMS)
            for item in list(thing.ITEMS):
                for group in list(thing.GROUPS):
                    things = group["things"]
                    for thg in things:
                        if item["thing"] == thg["thing"] and thg["master"] != 1:
                            new_list.remove(item)
            
            body = sorted(new_list, key=itemgetter('name'))
            msg = {"action": parsed_json["msg"]["action"], "body": body}
            cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
            web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def get_item(parsed_json):
    print "in get_item", parsed_json
    try:
        if ws_connection == OPEN:
            thg = parsed_json["msg"]["value"]
            for dic in thing.ITEMSComplete:
                if thg == dic["thing"]:
                    body = dic

                    msg = {"action": parsed_json["msg"]["action"], "body": body}
                    cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
                    web_sock.send(json.dumps(cmd))
                    return

        msg = {"action": parsed_json["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def set_item_param(parsed_json):
    found = False

    print "in set_item_param", parsed_json
    try:
        thg, value = parsed_json["msg"]["value"]
        if ws_connection == OPEN:
            print "id:", thg, "val:", value

            for item in thing.ITEMSComplete:
                if thg == item["thing"]:
                    if "state" in value:
                        t = thg.replace("-1", "").replace("-2", "")
                        packet = thing.things_connected[t]
                        db.db_setting.grouping(db.db_setting.find_grouping(thg), value["state"])

                        if not packet.set_relay([value["state"]], thg):
                            if not packet.set_relay([value["state"]], thg):
                                print "relay not successful"
                                return False

                        item["state"] = value["state"]

                    con = lite.connect(main.db_setting_address)
                    with con:
                        cur = con.cursor()
                        cur.execute("INSERT OR REPLACE INTO thing(thing,name,image,lock,timers) VALUES(?,?,?,?,?)",
                                    (thg, value["name"] if "name" in value else item["name"],
                                     value["image"] if "image" in value else item["image"],
                                     value["lock"] if "lock" in value else item["lock"],
                                     json.dumps(item["timers"])))
                        con.commit()
                    con.close()

                    if "name" in value:
                        item["name"] = value["name"]
                    if "lock" in value:
                        t = thg.replace("-1", "").replace("-2", "")
                        packet = thing.things_connected[t]
                        # print "LOCK", [value["lock"]], thg

                        if "image" not in value:
                            if not packet.set_lock([value["lock"]], thg):
                                if not packet.set_lock([value["lock"]], thg):
                                    print "lock not successful"
                                    return False
                        item["lock"] = value["lock"]
                    if "image" in value:
                        item["image"] = value["image"]
                    if "status" in value:
                        item["status"] = value["status"]

                    found = True
                    break

            if found:
                thing.ITEMS = []
                for item in thing.ITEMSComplete:
                    if item["status"] == 1:
                        thing.ITEMS.append({"thing": item["thing"], "name": item["name"], "state": item["state"],
                                            "temp": item["temp"], "lock": item["lock"], "image": item["image"]})

                msg = {"action": parsed_json["msg"]["action"], "body": True}
                cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
                web_sock.send(json.dumps(cmd))
                return

        msg = {"action": parsed_json["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def get_profiles(parsed_json):
    print "in get_profiles", parsed_json
    try:
        if ws_connection == OPEN:
            body = thing.PROFILES

            msg = {"action": parsed_json["msg"]["action"], "body": body}
            cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
            web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def get_profile(parsed_json):
    print "in get_profile", parsed_json
    try:
        if ws_connection == OPEN:
            profile_id = parsed_json["msg"]["value"]

            for dic in thing.PROFILESComplete:
                if int(profile_id) == dic["profileId"]:
                    body = dic

                    msg = {"action": parsed_json["msg"]["action"], "body": body}
                    cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
                    web_sock.send(json.dumps(cmd))
                    return

        msg = {"action": parsed_json["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def add_profile(parsed_json):
    try:
        value = parsed_json["msg"]["value"]
        con = lite.connect(main.db_setting_address)

        profileId = thing.PROFILE_NUMBER
        v = dict(value)
        v["profileId"] = profileId
        v["timers"] = []
        if v["state"] == 1:
            for thg in v["things"]:
                t = thg["thing"].replace("-1", "").replace("-2", "")

                packet = thing.things_connected[t]
                packet.set_relay([thg["state"]], thg["thing"])

            for profile in thing.PROFILESComplete:
                if profile["profileId"] != profileId:
                    profile["state"] = 0
                    with con:
                        cur = con.cursor()
                        cur.execute("UPDATE profile SET state=? WHERE profileId=?",
                                    (0, profile["profileId"]))
                        con.commit()

        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO profile(profileId, name, state, items, timers) values (?,?,?,?,?)", (
                v["profileId"], v["name"], v["state"], json.dumps(v["things"]), json.dumps(v["timers"])))
            con.commit()

        con.close()
        thing.PROFILESComplete.append(v)

        thing.PROFILES = []
        for profile in thing.PROFILESComplete:
            thing.PROFILES.append(
                {"profileId": profile["profileId"], "name": profile["name"], "state": profile["state"]})

        thing.PROFILE_NUMBER += 1

        msg = {"action": parsed_json["msg"]["action"], "body": True}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))

    except Exception as e:
        print e
        msg = {"action": parsed_json["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))


def edit_profile(parsed_json):
    try:
        profileId, value = parsed_json["msg"]["value"]
        for dic in thing.PROFILESComplete:
            if profileId == dic["profileId"]:
                if mob.setProfileParam(profileId, value):
                    msg = {"action": parsed_json["msg"]["action"], "body": True}
                    cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
                    web_sock.send(json.dumps(cmd))
                    return

        msg = {"action": parsed_json["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def remove_profile(parsed_json):
    found = False

    try:
        profileId = parsed_json["msg"]["value"]
        for profile in list(thing.PROFILESComplete):
            if int(profileId) == profile["profileId"]:
                thing.PROFILESComplete.remove(profile)

                con = lite.connect(main.db_setting_address)
                with con:
                    cur = con.cursor()
                    cur.execute('DELETE FROM profile WHERE profileId=?', (int(profileId),))
                    con.commit()

                con.close()
                found = True
                break

        if found:
            thing.PROFILES = []
            for profile in thing.PROFILESComplete:
                thing.PROFILES.append(
                    {"profileId": profile["profileId"], "name": profile["name"], "state": profile["state"]})

            msg = {"action": parsed_json["msg"]["action"], "body": True}
            cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
            web_sock.send(json.dumps(cmd))
            return

        msg = {"action": parsed_json["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))

    except Exception as e:
        print e
        return False


def get_item_timer(parsed_json):
    try:
        print "in get_item_timer"
        thg = parsed_json["msg"]["value"]
        for dic in thing.ITEMSComplete:
            # print "dic:", dic
            if thg == dic["thing"]:
                body = dic["timers"]
                print "item timer body:", body
                msg = {"action": parsed_json["msg"]["action"], "body": body}
                cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
                web_sock.send(json.dumps(cmd))
                return

        msg = {"action": parsed_json["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))

    except Exception as e:
        print e


def get_profile_timer(parsed_json):
    try:
        profileId = parsed_json["msg"]["value"]
        # print "profiles com", thing.PROFILESComplete
        for dic in thing.PROFILESComplete:
            if int(profileId) == dic["profileId"]:
                body = dic["timers"]
                print "profile timer body:", body
                msg = {"action": parsed_json["msg"]["action"], "body": body}
                cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
                web_sock.send(json.dumps(cmd))
                return

        msg = {"action": parsed_json["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))

    except Exception as e:
        print e


def add_item_timer(parsed_json):
    try:
        thg, val = parsed_json["msg"]["value"]
        for dic in thing.ITEMSComplete:
            if thg == dic["thing"]:
                timers = dic["timers"]
                # print ("timers:", timers)

                if "state" in val and "time" in val:
                    timers.append(
                        {"timerId": thing.TIMER_NUMBER, "state": val["state"], "time": val["time"], "status": 1})
                    thing.TIMER_NUMBER += 1

                    con = lite.connect(main.db_setting_address)
                    with con:
                        cur = con.cursor()
                        cur.execute("INSERT OR REPLACE INTO thing(thing,name,image,lock,timers) VALUES(?,?,?,?,?)",
                                    (thg, dic["name"], dic["image"], dic["lock"], json.dumps(timers)))
                        con.commit()
                    con.close()

                    msg = {"action": parsed_json["msg"]["action"], "body": True}
                    cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
                    web_sock.send(json.dumps(cmd))
                    return
                break

        msg = {"action": parsed_json["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def edit_item_timer(parsed_json1):
    try:
        thg, parsed_json = parsed_json1["msg"]["value"]
        for dic in thing.ITEMSComplete:
            if thg == dic["thing"]:
                timers = dic["timers"]

                for timer in timers:
                    if "timerId" in parsed_json["value"] and parsed_json["value"]["timerId"] == timer["timerId"]:

                        if "state" in parsed_json["value"] and "time" in parsed_json["value"]:
                            timer["state"] = parsed_json["value"]["state"]
                            timer["time"] = parsed_json["value"]["time"]

                            con = lite.connect(main.db_setting_address)
                            with con:
                                cur = con.cursor()
                                cur.execute("UPDATE thing SET timers=? WHERE thing=?", (json.dumps(timers), thg))
                                con.commit()
                            con.close()

                            msg = {"action": parsed_json1["msg"]["action"], "body": True}
                            cmd = {"seq": parsed_json1["seq"], "api_key": mob.API_KEY, "msg": msg}
                            web_sock.send(json.dumps(cmd))
                            return

                        break

        msg = {"action": parsed_json1["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json1["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def remove_item_timer(parsed_json):
    try:
        thg, tId = parsed_json["msg"]["value"]
        for dic in thing.ITEMSComplete:
            if thg == dic["thing"]:
                timers = dic["timers"]
                for timer in list(timers):
                    if int(tId) == timer["timerId"]:
                        timers.remove(timer)
                        con = lite.connect(main.db_setting_address)
                        with con:
                            cur = con.cursor()
                            cur.execute("UPDATE thing SET timers=? WHERE thing=?", (json.dumps(timers), thg))
                            con.commit()
                        con.close()

                        msg = {"action": parsed_json["msg"]["action"], "body": True}
                        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
                        web_sock.send(json.dumps(cmd))
                        return

        msg = {"action": parsed_json["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def add_profile_timer(parsed_json):
    try:
        profileId, val = parsed_json["msg"]["value"]
        for dic in thing.PROFILESComplete:
            if int(profileId) == dic["profileId"]:
                timers = dic["timers"]

                if "state" in val and "time" in val:
                    timers.append(
                        {"timerId": thing.TIMER_NUMBER, "state": val["state"], "time": val["time"], "status": 1})
                    thing.TIMER_NUMBER += 1

                    con = lite.connect(main.db_setting_address)
                    with con:
                        cur = con.cursor()
                        cur.execute("INSERT OR REPLACE INTO profile(profileId,name,items,state,timers) "
                                    "VALUES(?,?,?,?,?)", (int(profileId), dic["name"], json.dumps(dic["things"]),
                                                          dic["state"], json.dumps(timers)))
                        con.commit()
                    con.close()

                    msg = {"action": parsed_json["msg"]["action"], "body": True}
                    cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
                    web_sock.send(json.dumps(cmd))
                    return

                break

        msg = {"action": parsed_json["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def edit_profile_timer(parsed_json1):
    try:
        profileId, parsed_json = parsed_json1["msg"]["value"]
        for dic in thing.PROFILESComplete:
            if int(profileId) == dic["profileId"]:
                timers = dic["timers"]

                for timer in timers:
                    if "timerId" in parsed_json["value"] and parsed_json["value"]["timerId"] == timer["timerId"]:

                        if "state" in parsed_json["value"] and "time" in parsed_json["value"]:
                            timer["state"] = parsed_json["value"]["state"]
                            timer["time"] = parsed_json["value"]["time"]

                            con = lite.connect(main.db_setting_address)
                            with con:
                                cur = con.cursor()
                                cur.execute("UPDATE profile SET timers=? WHERE profileId=?",
                                            (json.dumps(timers), int(profileId)))
                                con.commit()
                            con.close()

                            msg = {"action": parsed_json1["msg"]["action"], "body": True}
                            cmd = {"seq": parsed_json1["seq"], "api_key": mob.API_KEY, "msg": msg}
                            web_sock.send(json.dumps(cmd))
                            return

                        break

        msg = {"action": parsed_json1["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json1["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def remove_profile_timer(parsed_json):
    try:
        profileId, tId = parsed_json["msg"]["value"]
        for dic in thing.PROFILESComplete:
            if int(profileId) == dic["profileId"]:
                timers = dic["timers"]
                for timer in list(timers):
                    if int(tId) == timer["timerId"]:
                        timers.remove(timer)

                        con = lite.connect(main.db_setting_address)
                        with con:
                            cur = con.cursor()
                            cur.execute("UPDATE profile SET timers=? WHERE profileId=?",
                                        (json.dumps(timers), int(profileId)))
                            con.commit()
                        con.close()

                        msg = {"action": parsed_json["msg"]["action"], "body": True}
                        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
                        web_sock.send(json.dumps(cmd))
                        return

        msg = {"action": parsed_json["msg"]["action"], "body": False}
        cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
        web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def get_time(parsed_json):
    print "in get_time"
    try:
        if ws_connection == OPEN:
            body = calendar.timegm(time.gmtime())

            msg = {"action": parsed_json["msg"]["action"], "body": body}
            cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
            web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


def set_time(parsed_json):
    print "in set_time", parsed_json
    try:
        if ws_connection == OPEN:
            t = parsed_json["msg"]["value"]
            if t:
                setting_time = "date -s '" + datetime.datetime.fromtimestamp(
                    int(math.floor(t))).strftime('%Y-%m-%d %H:%M:%S') + "'"

                main.shell_command(setting_time)

                print"\tsetting_time", setting_time

                msg = {"action": parsed_json["msg"]["action"], "body": True}
                cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
                web_sock.send(json.dumps(cmd))

            else:
                msg = {"action": parsed_json["msg"]["action"], "body": False}
                cmd = {"seq": parsed_json["seq"], "api_key": mob.API_KEY, "msg": msg}
                web_sock.send(json.dumps(cmd))
    except Exception as e:
        print e


actions = {
    "packet_received": packet_received,
    "thingChart": thingChart,
    "currentChart": currentChart,
    "get_items": get_items,
    "get_item": get_item,
    "set_item_param": set_item_param,
    "get_profiles": get_profiles,
    "get_profile": get_profile,
    "add_profile": add_profile,
    "edit_profile": edit_profile,
    "remove_profile": remove_profile,
    "get_item_timer": get_item_timer,
    "get_profile_timer": get_profile_timer,
    "add_item_timer": add_item_timer,
    "edit_item_timer": edit_item_timer,
    "remove_item_timer": remove_item_timer,
    "add_profile_timer": add_profile_timer,
    "edit_profile_timer": edit_profile_timer,
    "remove_profile_timer": remove_profile_timer,
    "get_time": get_time,
    "set_time": set_time,
}


def hello():
    global time_end, ws_connection, web_sock

    try:
        while True:
            # print("hello", ws_connection)
            time.sleep(5)
            if ws_connection == CLOSING:
                web_sock.close()

            time_end = calendar.timegm(time.gmtime())
            try:
                while ws_connection == OPEN:
                    web_sock.send("#!hello!#")
                    time_start = calendar.timegm(time.gmtime())
                    # print("in hello", time_start - time_end)
                    if (time_start - time_end) >= 30:  # 5 seconds
                        print("server dead!")
                        # reader.my_reader.db_data.add_exception("websocket.hello", "server dead")
                        time_end = calendar.timegm(time.gmtime())
                        ws_connection = CLOSING
                        web_sock.close()

                    time.sleep(10)

            except Exception as e:
                print(e)

    except Exception as e:
        # reader.my_reader.db_data.add_exception("websocket.hello", str(e))
        print(e)


def on_message(ws, message):
    global time_end, BACK_OFF

    # print("From server", message)
    try:
        if message == "#!hello!#":
            ws.send("#!ok!#")
            # print ("ws hello:", ws)
        elif message == "#!ok!#":
            time_end = calendar.timegm(time.gmtime())
        else:
            whole = json.loads(message)
            if "msg" in whole and "seq" in whole:
                res = whole["msg"]
                if "action" in res:
                    if res["action"] == "info":
                        pass
                    elif res["action"] == "reboot":
                        ws.send(json.dumps({"seq": whole["seq"], "msg": {"action": "reboot",
                                                                         "response": {"text": "OK", "code": 200}}}))
                        time.sleep(1)

                        # reader.my_reader.setting.reboot()
                    elif res["action"] in actions:
                        actions[res["action"]](whole)
                        # end = {"seq": whole["seq"], "msg": actions[res["action"]](res)}
                        # print("RESPONSE::::", end)
                        # resp = json.dumps(end)
                        #
                        # ws.send(resp)
                    else:
                        end = {"seq": whole["seq"], "msg": {"action": "error",
                                                            "response": {"text": "Invalid Action", "code": 404}}}
                        print("RESPONSE::::", end)
                        resp = json.dumps(end)

                        ws.send(resp)

                else:
                    print "nothing..."
                    end = {"seq": whole["seq"], "msg": {"action": "No action specified",
                                                        "response": {"text": "No action specified", "code": 400}}}
                    print("RESPONSE::::", end)
                    resp = json.dumps(end)

                    ws.send(resp)

            else:
                if "action" in whole:
                    if whole["response"]["text"] == "OK":
                        print("Token OK!")
                        BACK_OFF = 1

                    else:
                        print("Token Fail!")
                        if BACK_OFF < 64:
                            BACK_OFF *= 2

                elif "error" in whole:
                    print("ERROR", whole["error"], whole["text"])
                else:
                    ws.send(str({"action": "", "response": {"text": "FAIL", "code": 404}}))

    except Exception as e:
        print(e)
        ws.send(str({"action": "", "response": {"text": "FAIL", "code": 404}}))
        # reader.my_reader.db_data.add_exception("web_socket/on_message/", str(e))


def on_error(ws, error):
    global ws_connection
    print("in error", error)

    ws_connection = CLOSED


def on_close(ws):
    global ws_connection
    print("in close")
    ws_connection = CLOSED


def on_open(ws):
    global ws_connection
    # print("token sent", reader.my_reader.setting.auto_launch)

    ws_connection = OPEN


def on_ping(ws, data):
    print("on ping")


def on_pong(ws, data):
    # print("on pong")
    pass


def web_socket():
    global ws_connection, web_sock, BACK_OFF

    last = calendar.timegm(time.gmtime())

    counter = 0

    while True:
        time.sleep(BACK_OFF)
        try:
            # websocket.enableTrace(True)
            print "ws_connection", ws_connection
            if ws_connection == IDEAL or ws_connection == CLOSED:
                web_sock = websocket.WebSocketApp("ws://cloud.simorq.io:9003/",
                                                  on_message=on_message,
                                                  on_open=on_open,
                                                  on_error=on_error,
                                                  on_close=on_close,
                                                  on_pong=on_pong,
                                                  on_ping=on_ping
                                                  )

                web_sock.run_forever(ping_timeout=20, ping_interval=30)

                now = calendar.timegm(time.gmtime())

                if now - last > 20:
                    last = calendar.timegm(time.gmtime())
                    counter += 1

                    register_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    con = lite.connect(main.db_setting_address)
                    con.row_factory = lite.Row

                    with con:
                        cur = con.cursor()
                        cur.execute("INSERT into log (event_id,log_description,Time) values(?,?,?)",
                                    ("Simorq", counter, register_time))
                        con.commit()

                        cur.close()

                print("old ended!")
        except Exception as e:
            print(e)
            # reader.my_reader.db_data.add_exception("websocket.web_socket", str(e))
            ws_connection = CLOSED


def start():
    a = threading.Thread(name="hello", target=hello)
    a.setDaemon(True)
    a.start()

    b = threading.Thread(name="web_socket", target=web_socket)
    b.setDaemon(True)
    b.start()

    c = threading.Thread(name="send_cloud", target=send_cloud)
    c.setDaemon(True)
    c.start()

