from bottle import hook, route, response, request, static_file
import bottle
from paste import httpserver
import random
import sqlite3 as lite
import json
import time
import calendar
import datetime
import math
from operator import itemgetter
import threading

import main
import thing
import web_socket_client
import db

command_number = 0
names = []
profiles = []
profile_id = 1
VERSION = "1.00.00"
API_KEY = ""


@hook('after_request')
def enable_cors():
    response.set_header('Expires', 'Thu, 01 Dec 1994 16:00:00 GMT')
    response.set_header('Pragma', 'no-cache')
    response.set_header('Cache-Control', 'no-cache, no-store, max-age=0, must-revalidate')
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers[
        'Access-Control-Allow-Headers'] = 'Authorization, Origin, Accept, Content-Type, X-Requested-With, ' \
                                          'X-CSRF-Token, Pragma, Connection, Content-Length, Referer, Cache-Control,' \
                                          ' Accept-Encoding, Accept-Language, User-Agent, Host'


def check_authorization(auth):
    global API_KEY

    if auth == API_KEY:
        return True
    else:
        return False


def get_name(thg):
    for item in list(thing.ITEMS):
        if item["thing"] == thg:
            return item["name"]

    return thg


def set_thing_password(value):
    print "SET set_thing_password", value

    for t in dict(thing.things_connected):
        packet = thing.things_connected[t]
        # print "network mac", packet.thing
        # if packet.thing == "A020A60645DF":
        #     print "IN SET NETWORK 5DF"
        if not packet.set_network(value["ssid"], value["password"]):
            if not packet.set_network(value["ssid"], value["password"]):
                packet.set_network(value["ssid"], value["password"])

    print "set_thing_password FINISH"


def setItemParam(thg, value):
    found = False

    try:

        print "id:", thg, "val:", value

        for item in thing.ITEMSComplete:
            if thg == item["thing"]:
                if "state" in value:
                    t = thg.replace("-1", "").replace("-2", "")
                    packet = thing.things_connected[t]
                    print "TAK", [value["state"]], thg

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

        return found
    except Exception as e:
        print e
        return False


def set_relay_pool(thg):
    # print "SET RELAY THING:", thg
    t = thg["thing"].replace("-1", "").replace("-2", "")

    if t in dict(thing.things_connected):
        packet = thing.things_connected[t]
        thing.relay_cnt2 += 1

        db.db_setting.grouping(db.db_setting.find_grouping(thg), thg["state"])
        # print "PROF", [thg["state"]], thg["thing"]
        if not packet.set_relay([thg["state"]], thg["thing"]):
            if not packet.set_relay([thg["state"]], thg["thing"]):
                packet.set_relay([thg["state"]], thg["thing"])

    # print "SET RELAY POOL FINISH", t


def setProfileParam(profileId, value):
    found = False

    try:

        # print "prof:", "profileId: ", profileId, "val:", value

        for profile in thing.PROFILESComplete:
            if profileId == profile["profileId"]:

                con = lite.connect(main.db_setting_address)
                with con:
                    cur = con.cursor()
                    cur.execute("INSERT OR REPLACE INTO profile(profileId,items,name,state,timers) VALUES(?,?,?,?,?)",
                                (profileId, json.dumps(value["things"]) if "things" in value else json.dumps(profile["things"]),
                                 value["name"] if "name" in value else profile["name"],
                                 value["state"] if "state" in value else profile["state"],
                                 json.dumps(value["timers"]) if "timers" in value else json.dumps(profile["timers"])))
                    con.commit()
                con.close()

                if "things" in value:
                    items = value["things"]
                    for item in items:
                        if "state" not in item or "name" not in item:
                            return False
                    profile["things"] = value["things"]

                if ("state" in value and value["state"] == 1) or (profile["state"] == 1):
                    thing.relay_cnt = 0
                    thing.relay_cnt1 = 0
                    thing.relay_cnt2 = 0
                    for thg in profile["things"]:
                        a = threading.Thread(name="check", args=(thg,), target=set_relay_pool)
                        a.setDaemon(True)
                        a.start()
                        time.sleep(0.25)

                    # for thg in profile["things"]:
                    #     t = thg["thing"].replace("-1", "").replace("-2", "")
                    #
                    #     if t in thing.things_connected:
                    #         packet = thing.things_connected[t]
                    #         not packet.set_relay([thg["state"]], thg["thing"])

                if "state" in value:
                    profile["state"] = value["state"]
                    # if value["state"] == 1:

                if "name" in value:
                    profile["name"] = value["name"]

                found = True
                break

        # print PROFILESComplete

        if found:

            if value["state"] == 1:

                con = lite.connect(main.db_setting_address)
                for p in thing.PROFILESComplete:
                    if p["profileId"] != profileId:
                        p["state"] = 0
                        with con:
                            cur = con.cursor()
                            cur.execute("UPDATE profile SET state=? WHERE profileId=?",
                                        (0, p["profileId"]))
                            con.commit()
                con.close()

            thing.PROFILES = []
            for profile in thing.PROFILESComplete:
                thing.PROFILES.append(
                    {"profileId": profile["profileId"], "name": profile["name"], "state": profile["state"]})

        return found
    except Exception as e:
        print e
        main.add_exception("setProfileParam", str(e))
        return False


def removeProfile(profileId):
    found = False

    try:

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

        return found
    except Exception as e:
        print e
        return False


def addProfile(value):
    try:
        print "in add profile", value
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

        # print "all", thing.PROFILESComplete

        # print PROFILESComplete, type([PROFILESComplete])

        thing.PROFILES = []
        for profile in thing.PROFILESComplete:
            # print "in fill profiles:", profile

            thing.PROFILES.append(
                {"profileId": profile["profileId"], "name": profile["name"], "state": profile["state"]})

        thing.PROFILE_NUMBER += 1
    except Exception as e:
        print e


def addGroup(value):
    try:
        print "in add profile", value
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

        # print "all", thing.PROFILESComplete

        # print PROFILESComplete, type([PROFILESComplete])

        thing.PROFILES = []
        for profile in thing.PROFILESComplete:
            # print "in fill profiles:", profile

            thing.PROFILES.append(
                {"profileId": profile["profileId"], "name": profile["name"], "state": profile["state"]})

        thing.PROFILE_NUMBER += 1
    except Exception as e:
        print e


def setTimer():
    for dic in thing.ITEMSComplete:
        for timer in dic["timers"]:
            if timer["timerId"] >= thing.TIMER_NUMBER:
                thing.TIMER_NUMBER = timer["timerId"] + 1

    for dic in thing.PROFILESComplete:
        for timer in dic["timers"]:
            if timer["timerId"] >= thing.TIMER_NUMBER:
                thing.TIMER_NUMBER = timer["timerId"] + 1
    print "timer:", thing.TIMER_NUMBER


def getThingChart(thg):
    msg = {"action": "thingChart", "thing": thg}
    cmd = {"seq": 123, "msg": msg}

    web_socket_client.answered = False
    web_socket_client.chart = {}
    web_socket_client.web_sock.send(json.dumps(cmd))

    i = 0

    while not web_socket_client.answered and i < 20:
        time.sleep(0.25)
        i += 1
    print "PASS!!!"
    return web_socket_client.chart


def getCurrentChart(thg):
    msg = {"action": "currentChart", "thing": thg}
    cmd = {"seq": 123, "msg": msg}

    web_socket_client.current_answered = False
    web_socket_client.current_chart = {}
    web_socket_client.web_sock.send(json.dumps(cmd))

    i = 0

    while not web_socket_client.current_answered and i < 20:
        time.sleep(0.25)
        i += 1
    print "PASS!!!"
    return web_socket_client.current_chart


@route('/api/things/', method=['OPTIONS', 'GET'])
def getItems():
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':

        try:
            auth = request.get_header("Authorization")
            print "AUTHORIZATION123:", auth

            if check_authorization(auth):

                new_list = list(thing.ITEMS)
                for item in list(thing.ITEMS):
                    for group in list(thing.GROUPS):
                        things = group["things"]
                        for thg in things:
                            if item["thing"] == thg["thing"] and thg["master"] != 1:
                                new_list.remove(item)

                new_list1 = sorted(new_list, key=itemgetter('name'))

                log = {"result": new_list1}

                return log
            else:
                response.status = 401
                return {"code": 401}

        except Exception as e:
            print(e)
            main.add_exception("api/things", str(e))
            response.status = 400
            return {"code": 400}

    else:
        response.status = 405
        return {"code": 405}


@route('/api/thing/<thg>', method=['OPTIONS', 'GET'])
def getItem(thg):
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':

        try:

            # print ("dddddddddd", ITEMSComplete, thing)
            auth = request.get_header("Authorization")
            if check_authorization(auth):

                for dic in thing.ITEMSComplete:
                    if thg == dic["thing"]:
                        print dic
                        log = {"result": dic}
                        # print ("dddddddddd", dic)

                        return log

                response.status = 404
                return {"code": "Item Not Found"}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            main.add_exception("api/thing/get", str(e))
            response.status = 400
            return {"code": 400}
    else:
        response.status = 405
        return {"code": 405}


@route('/api/thing/', method=['OPTIONS', 'PUT'])
def setItem():
    if request.method == 'OPTIONS':
        return ""
    if request.method == 'PUT':
        auth = request.get_header("Authorization")
        if check_authorization(auth):

            try:
                parsed_json = json.loads(request.body.read())
            except Exception as e:
                print(e)
                response.status = 400
                return {"code": 400}
            try:
                if setItemParam(parsed_json["thing"], parsed_json["value"]):
                    return {"code": 200}

                else:
                    response.status = 404
                    return {"code": 404}

            except Exception as e:
                print(e)
                main.add_exception("api/thing/put", str(e))
                response.status = 400
                return {"code": 400}
        else:
            response.status = 401
            return {"code": 401}
    else:
        response.status = 405
        return {"code": 405}


@route('/api/profiles/', method=['OPTIONS', 'GET'])
def getProfiles():
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':

        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):

                log = {"result": thing.PROFILES}
                return log
            else:
                response.status = 401
                return {"code": 401}

        except Exception as e:
            print(e)
            main.add_exception("api/profile/get", str(e))
            response.status = 400
            return {"code": 400}

    else:
        response.status = 405
        return {"code": 405}


@route('/api/profile/<profileId>', method=['OPTIONS', 'GET', 'DELETE'])
def getProfile(profileId):
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':

        try:
            # print ("xxx", PROFILESComplete, profileId)
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                for dic in thing.PROFILESComplete:
                    if int(profileId) == dic["profileId"]:
                        log = {"result": dic}
                        print "profile", log
                        return log

                response.status = 404
                return {"code": "Profile Not Found"}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}
    elif request.method == 'DELETE':
        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                if removeProfile(int(profileId)):
                    return {"code": 200}
                else:
                    response.status = 404
                    return {"code": "Profile Not Found"}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}
    else:
        response.status = 405
        return {"code": 405}


@route('/api/profile/', method=['OPTIONS', 'POST', 'PUT'])
def getProfile():
    if request.method == 'OPTIONS':
        return ""
    if request.method == 'POST':
        auth = request.get_header("Authorization")
        if check_authorization(auth):
            try:
                parsed_json = json.loads(request.body.read())
            except Exception as e:
                print(e)
                response.status = 400
                return {"code": 400}
            try:
                val = parsed_json["value"]
                if "name" in val and "state" in val and "things" in val:
                    things = val["things"]
                    for item in things:
                        if "state" not in item or "name" not in item:
                            response.status = 400
                            return {"code": "Parameter Missing in 'items'"}
                    addProfile(val)
                    return {"code": 200}
                else:
                    response.status = 400
                    return {"code": "Parameter Missing in 'value'"}
            except Exception as e:
                print(e)
                response.status = 400
                return {"code": 400}
        else:
            response.status = 401
            return {"code": 401}
    elif request.method == 'PUT':
        auth = request.get_header("Authorization")
        if check_authorization(auth):
            try:
                print "in api/profile/put"
                parsed_json = json.loads(request.body.read())
            except Exception as e:
                print(e)
                response.status = 400
                return {"code": 400}
            try:
                for dic in thing.PROFILESComplete:
                    if parsed_json["profileId"] == dic["profileId"]:
                        if setProfileParam(parsed_json["profileId"], parsed_json["value"]):
                            return {"code": 200}
                        else:
                            response.status = 400
                            return {"code": 400}

                response.status = 404
                return {"code": 404}
            except Exception as e:
                print(e)
                response.status = 400
                return {"code": 400}
        else:
            response.status = 400
            return {"code": 400}
    else:
        response.status = 405
        return {"code": 405}


@route('/api/thingTimer/<thg>', method=['OPTIONS', 'GET', 'POST', 'PUT'])
def getItemTimers1(thg):
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':
        auth = request.get_header("Authorization")
        if check_authorization(auth):
            # print "in /api/thingTimer/<thg>", thing.ITEMSComplete
            try:
                for dic in thing.ITEMSComplete:
                    # print "dic:", dic
                    if thg == dic["thing"]:
                        log = {"result": dic["timers"]}
                        return log

                response.status = 404
                return {"code": 404}

            except Exception as e:
                print(e)
                response.status = 400
                return {"code": 400}
        else:
            response.status = 400
            return {"code": 400}
    elif request.method == 'POST':
        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                try:
                    parsed_json = json.loads(request.body.read())
                    val = parsed_json["value"]

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

                                return {"code": 200}

                            response.status = 400
                            return {"code": "Parameter Missing In 'Timer'"}
                except Exception as e:
                    print(e)
                    response.status = 400
                    return {"code": 400}

                response.status = 404
                return {"code": 404}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}
    elif request.method == 'PUT':
        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):

                try:
                    parsed_json = json.loads(request.body.read())
                except Exception as e:
                    print(e)
                    response.status = 400
                    return {"code": 400}

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

                                    return {"code": 200}
                                response.status = 400
                                return {"code": "Parameter Missing In 'Timer'"}

                response.status = 404
                return {"code": 404}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}
    else:
        response.status = 405
        return {"code": 405}


@route('/api/thingTimer/<thg>/<tId>', method=['OPTIONS', 'DELETE'])
def getItemTimers1(thg, tId):
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'DELETE':
        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
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

                                return {"code": 200}
                response.status = 404
                return {"code": 404}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}
    else:
        response.status = 405
    return {"code": 405}


@route('/api/profileTimer/<profileId>', method=['OPTIONS', 'GET', 'POST', 'PUT'])
def getProfileTimers1(profileId):
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':

        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                for dic in thing.PROFILESComplete:
                    if int(profileId) == dic["profileId"]:
                        log = {"result": dic["timers"]}
                        return log

                response.status = 404
                return {"code": 404}
            else:
                response.status = 401
                return {"code": 401}

        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}
    elif request.method == 'POST':
        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                try:
                    parsed_json = json.loads(request.body.read())
                    val = parsed_json["value"]
                except Exception as e:
                    print(e)
                    response.status = 400
                    return {"code": 400}

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

                            return {"code": 200}
                        response.status = 400
                        return {"code": "Parameter Missing In 'Timer'"}
                response.status = 404
                return {"code": 404}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}
    elif request.method == 'PUT':
        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                try:
                    parsed_json = json.loads(request.body.read())
                except Exception as e:
                    print(e)
                    response.status = 400
                    return {"code": 400}

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

                                    return {"code": 200}
                                response.status = 400
                                return {"code": "Parameter Missing In 'Timer'"}

                response.status = 404
                return {"code": 404}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}
    else:
        response.status = 405
        return {"code": 405}


@route('/api/profileTimer/<profileId>/<tId>', method=['OPTIONS', 'DELETE'])
def getItemTimers1(profileId, tId):
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'DELETE':
        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
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

                                return {"code": 200}
                response.status = 404
                return {"code": 404}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}
    else:
        response.status = 405
        return {"code": 405}


@route('/api/grouping/', method=['OPTIONS', 'GET', 'POST'])
def getTimerSupport1():
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':
        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                print "get grouping"
                new_list = []
                for group in list(thing.GROUPS):
                    things = group["things"]
                    for item in things:
                        print "item", item
                        if item["master"] == 1:
                            name = get_name(item["thing"])
                            new_list.append({"master": item["thing"], "groupId": group["groupId"], "name": name})
                            break

                log = {"result": new_list}

                return log
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}
    elif request.method == 'POST':

        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                try:
                    parsed_json = json.loads(request.body.read())
                    val = parsed_json["value"]
                except Exception as e:
                    print(e)
                    response.status = 400
                    return {"code": 400}

                print "in group api", val
                lst = []

                has_master = False

                for item in val:
                    print "item", item
                    for group in list(thing.GROUPS):
                        things = group["things"]
                        for thg in things:
                            if item["thing"] == thg["thing"]:
                                response.status = 409
                                return {"code": 409}

                    if item["master"] and not has_master:
                        has_master = True
                        lst.append({"thing": item["thing"], "master": 1})
                    else:
                        lst.append({"thing": item["thing"], "master": 0})

                groupId = str(random.randint(100000, 1000000))

                con = lite.connect(main.db_setting_address)
                with con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO grouping(groupId,things) VALUES(?,?)", (groupId, json.dumps(lst)))
                    con.commit()
                con.close()

                thing.GROUPS.append({"groupId": groupId, "things": val})

                print "GROUPS: ", thing.GROUPS

                return {"code": 200}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}
    else:
        response.status = 405
        return {"code": 405}


@route('/api/grouping/<group_id>', method=['OPTIONS', 'DELETE'])
def getItemTimers1(group_id):
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'DELETE':

        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                print "in delete group", group_id
                for group in list(thing.GROUPS):
                    g_id = group["groupId"]
                    print "id", g_id, group_id
                    if g_id == int(group_id):
                        print "111"
                        con = lite.connect(main.db_setting_address)
                        with con:
                            cur = con.cursor()
                            cur.execute('DELETE FROM grouping WHERE groupId=?', (g_id,))
                            con.commit()
                        con.close()
                        print "222"
                        thing.GROUPS.remove(group)
                        print "333"
                        return {"code": 200}

                response.status = 404
                return {"code": 404}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}
    else:
        response.status = 405
        return {"code": 405}


@route('/api/timerSupport/', method=['OPTIONS', 'GET'])
def getTimerSupport1():
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':

        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                log = {"result": {"timerSupport": True}}
                return log
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}

    else:
        response.status = 405
        return {"code": 405}


@route('/api/getTime/', method=['OPTIONS', 'GET'])
def getTimerSupport1():
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':

        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                log = {"result": {"time": calendar.timegm(time.gmtime())}}
                return log
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}

    else:
        response.status = 405
        return {"code": 405}


@route('/api/setTime/', method=['OPTIONS', 'PUT'])
def getTimerSupport1():
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'PUT':

        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):

                try:
                    parsed_json = json.loads(request.body.read())
                except Exception as e:
                    print(e)
                    response.status = 400
                    return {"code": 400}
                print "TIME:", parsed_json["time"]

                if "time" in parsed_json:
                    setting_time = "date -s '" + datetime.datetime.fromtimestamp(
                        int(math.floor(parsed_json["time"]))).strftime('%Y-%m-%d %H:%M:%S') + "'"

                    main.shell_command(setting_time)

                    print"\tsetting_time", setting_time

                    response.status = 200
                    return {"code": 200}
                else:
                    response.status = 400
                    return {"code": "Parameter Missing."}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}

    else:
        response.status = 405
        return {"code": 405}


@route('/api/allCharts/', method=['OPTIONS', 'GET'])
def getTimerSupport1():

    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':

        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                all_charts = []

                for dic in list(thing.ITEMS):
                    all_charts.append({"name": dic["name"], "thing": dic["thing"]})

                newlist = sorted(all_charts, key=itemgetter('name'))
                print all_charts
                log = {"result": newlist}
                return log
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}

    else:
        response.status = 405
        return {"code": 405}


@route('/api/thingCharts/<thg>', method=['OPTIONS', 'GET'])
def getTimerSupport1(thg):

    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':

        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                chart = getThingChart(thg)

                print "chart", chart
                #
                # data = [{"fieldName": "state", "entries": []}, {"fieldName": "temp", "entries": []},
                #         {"fieldName": "current", "entries": []}, {"fieldName": "freeMemory", "entries": []},
                #         {"fieldName": "upTime", "entries": []}]

                data = [{"fieldName": "state", "entries": []}, {"fieldName": "temp", "entries": []},
                        {"fieldName": "current", "entries": []}]

                for dic in chart["data"]:
                    # print "DIC:", dic
                    current = dic["current"]
                    temp = dic["temp"]
                    state = dic["state"]
                    # freeMemory = dic["freeMemory"]
                    # upTime = dic["upTime"]
                    time = int(dic["time"])
                    # print "333",
                    for d in data:
                        # print "444", d
                        if d["fieldName"] == "state":
                            d["entries"].append({"value": state, "time": time})
                        elif d["fieldName"] == "temp":
                            d["entries"].append({"value": temp, "time": time})
                        elif d["fieldName"] == "current":
                            d["entries"].append({"value": current, "time": time})
                        # elif d["fieldName"] == "freeMemory":
                        #     d["entries"].append({"value": freeMemory, "time": time})
                        # elif d["fieldName"] == "upTime":
                        #     d["entries"].append({"value": upTime, "time": time})

                reformat_chart = {"name": chart["name"], "thing": chart["thing"], "data": data}
                # print "666", reformat_chart
                if chart:
                    log = {"result": reformat_chart}
                    return log

                response.status = 404
                return {"code": 404}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}

    else:
        response.status = 405
        return {"code": 405}


@route('/api/currentChart/<thg>', method=['OPTIONS', 'GET'])
def getTimerSupport1(thg):
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':

        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                chart = getCurrentChart(thg)

                # print "chart", chart

                if chart:
                    log = {"result": chart}
                    print "chart", log
                    return log

                response.status = 404
                return {"code": 404}
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}

    else:
        response.status = 405
        return {"code": 405}


@route('/api/version/<device>', method=['OPTIONS', 'GET', 'PUT'])
def version(device):

    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':
        try:
            auth = request.get_header("Authorization")
            if check_authorization(auth):
                ver = {}
                con = lite.connect('/root/app.db')
                con.row_factory = lite.Row

                with con:
                    cur = con.cursor()
                    s = "SELECT " + device + " FROM version"
                    cur.execute(s)
                    for row in cur:
                        ver["version"] = row[device]

                    print ("ver:", ver)
                con.close()
                log = {"result": ver}
                return log
            else:
                response.status = 401
                return {"code": 401}
        except Exception as e:
            response.status = 408
            return {"code": 408}

    else:
        response.status = 405
        return {"code": 405}


@route('/api/update_file/<file_name>', method=['OPTIONS', 'GET'])
def getTimerSupport1(file_name):
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'GET':

        try:
            return static_file(file_name, root="/tmp")
        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}

    else:
        response.status = 405
        return {"code": 405}


@route('/api/setNetwork/', method=['OPTIONS', 'PUT'])
def getTimerSupport1():
    if request.method == 'OPTIONS':
        return ""
    elif request.method == 'PUT':

        try:

            try:
                parsed_json = json.loads(request.body.read())
            except Exception as e:
                print(e)
                response.status = 400
                return {"code": 400}
            print "password:", parsed_json

            if "password" in parsed_json:
                set_thing_password(parsed_json)

                response.status = 200
                return {"code": 200}
            else:
                response.status = 400
                return {"code": "Parameter Missing."}

        except Exception as e:
            print(e)
            response.status = 400
            return {"code": 400}

    else:
        response.status = 405
        return {"code": 405}


def init_api():
    try:
        application = bottle.default_app()
        httpserver.serve(application, host='0.0.0.0', port=9888)
    except Exception as e:
        print("bottle 3333", e)
