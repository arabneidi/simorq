import time
import threading
import os
import subprocess
import signal
import sys
from bottle import hook, route, run, response, request
import sqlite3 as lite

import gpio

db_address = '/root/app.db'
gg = gpio.Gpio()
debug = True
LISTEN_CONFIG = 7200  # 2 hours
reset_push = False
API_KEY = None
PASS_CHANGED = False


def set_api_key(api_key):
    global db_address, API_KEY

    try:
        con = lite.connect(db_address)
        con.row_factory = lite.Row

        with con:
            cur = con.cursor()
            cur.execute("UPDATE network SET api_key=?", (api_key, ))
            con.commit()
            cur.close()

        con.close()

        print ("API_KEY:", api_key)
        API_KEY = api_key

    except Exception as e:
        print(e)


def load_from_db():
    global db_address, API_KEY

    try:
        con = lite.connect(db_address)
        con.row_factory = lite.Row

        with con:
            cur = con.cursor()
            cur.execute("SELECT api_key FROM network")
            for row in cur:
                API_KEY = row["api_key"]

            print ("API_KEY:", API_KEY)
        con.close()

    except Exception as e:
        print(e)


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


# returns number and pid of ghost my_program.
def is_running(my_program):
    handle = os.popen("pgrep -f " + my_program)

    line, x = None, []
    for line in handle:
        x.insert(0, line.split())

    handle.close()

    strt = "grep '^PPid' '/proc/"
    end = "/status' |cut -f2"

    for i in range(len(x)):
        try:
            ppid = os.popen(strt + x[i][0] + end)

            line, y = None, []
            for line in ppid:
                y.insert(0, line.split())

            if y:
                for j in range(len(x)):
                    if y[0][0] == x[j][0] or y[0][0] == 1:
                        print("found ghost pid:", x[i][0])
                        ppid.close()
                        return len(x), x[i][0], x[len(x) - 1]

            ppid.close()
        except Exception as e:
            print("error", e)

    return len(x), None, x[len(x) - 1]


# if reset button is pressed for 5 seconds device will be set to reset factory setting.
def reset_factory():
    global debug, gg, reset_push, LISTEN_CONFIG, db_address

    try:
        print("111111")
        con = lite.connect(db_address)
        con.row_factory = lite.Row

        with con:
            cur = con.cursor()
            cur.execute("SELECT listen FROM network")
            for row in cur:
                if row["listen"] == 1:
                    reset_push = True

            cur.close()
    except Exception as e:
        print e

    push_time = time.time()

    reset_push = True

    while True:
        try:
            now = time.time()

            if int(abs(push_time - now)) > LISTEN_CONFIG:
                print ("config time passed")
                reset_push = False

            mode = 0
            # print("222222", gg.pin_reset_push())
            while gg.pin_reset_push():
                later = time.time()
                difference = int(abs(later - now))
                if True:
                    print("difference: ", difference)

                if difference > 5 and not mode:
                    mode = 2
                    if True:
                        print("Reset factory")

                    time.sleep(0.4)

                    push_time = time.time()
                    reset_push = True
                    # go_ap()

                time.sleep(0.2)

            time.sleep(1)
        except Exception as e:
            print e


def last_6_mac():
    point = subprocess.check_output('cat /sys/class/net/apcli0/address', shell=True)

    last_part = str(point[9:11]).upper() + str(point[12:14]).upper() + str(point[15:17]).upper()

    return last_part


def whole_mac():
    point = subprocess.check_output('cat /sys/class/net/eth0/address', shell=True)

    # whole_part = str(point[9:11]).upper() + str(point[12:14]).upper() + str(point[15:17]).upper()
    print "whole", point
    return point


def go_ap():
    last_six = last_6_mac()

    print last_six
    shell_command('uci set wireless.ap.ssid=' + "Simorq-" + last_six)
    shell_command('uci set wireless.ap.encryption=psk2')
    shell_command('uci set wireless.ap.key=' + "Simorq-" + last_six)

    shell_command('uci set network.lan.ipaddr=192.168.100.1')
    shell_command('uci set network.lan.macaddr=' + whole_mac())
    shell_command('uci set network.lan.proto=static')
    time.sleep(0.5)
    shell_command('uci commit')
    time.sleep(0.5)
    shell_command('wifi_mode ap')


def set_wifi(mode, my_password):
    global reset_push, db_address

    print "in set ap"
    if mode == "ap":
        con = lite.connect(db_address)
        con.row_factory = lite.Row

        with con:
            cur = con.cursor()
            cur.execute("UPDATE network SET mode=?,my_password=?,listen=?", (mode, my_password, 0))
            con.commit()
            cur.close()

        last_six = last_6_mac()

        print last_six
        shell_command('uci set wireless.ap.ssid=' + "Simorq-" + last_six)
        shell_command('uci set wireless.ap.encryption=psk2')
        shell_command('uci set wireless.ap.key=' + my_password)
        shell_command('uci set network.lan.ipaddr=192.168.100.1')
        shell_command('uci set network.lan.macaddr=' + whole_mac())
        shell_command('uci set network.lan.proto=static')
        time.sleep(0.5)
        shell_command('uci commit')
        time.sleep(0.5)
        shell_command('wifi_mode ap')
        return True
    return False


def set_wife(mode, my_password, ssid, password):
    global reset_push

    try:
        last_six = last_6_mac()
        print last_six
        if mode == "online":
            print "in set online"
            con = lite.connect(db_address)
            con.row_factory = lite.Row
            with con:
                cur = con.cursor()
                cur.execute("UPDATE network SET mode=?,my_password=?,ssid=?,password=?,listen=?",
                            (mode, my_password, ssid, password, 0))
                con.commit()
                cur.close()

            ap_list = get_wifi()
            fav_list = []

            enc = 'psk2'

            for ap in ap_list:
                if ap["ESSID"] == ssid:
                    fav_list.append(ap)

            print("fav:", fav_list)
            max_quality = 0
            for ap in fav_list:
                if ap["Quality"] > max_quality:
                    enc = ap["Encryption"]
                    if "WPA2" == enc:
                        enc = "psk2"

            print("enc decided:", enc, ssid, password, my_password)
            with con:
                cur = con.cursor()
                cur.execute("UPDATE network SET enc=?", (enc,))
                con.commit()
                cur.close()

            shell_command('wifi_mode ap')
            time.sleep(4)

            shell_command('uci set wireless.sta.ssid=' + ssid)
            shell_command('uci set wireless.sta.encryption=' + enc)
            shell_command('uci set wireless.sta.key=' + password)

            shell_command('uci set wireless.ap.ssid=' + "Simorq-" + last_six)
            shell_command('uci set wireless.ap.encryption=psk2')
            shell_command('uci set wireless.ap.key=' + my_password)
            shell_command('uci set wireless.radio0.linkit_mode=apsta')

            # shell_command('uci set network.lan.ipaddr=192.168.100.1')
            shell_command('uci set network.lan.macaddr=' + whole_mac())
            shell_command('uci set network.lan.proto=static')

            time.sleep(0.5)
            shell_command('uci commit')
            time.sleep(1)
            shell_command('wifi')

            return True
        elif mode == "repeater":
            print "in set repeater"
            con = lite.connect(db_address)
            con.row_factory = lite.Row
            with con:
                cur = con.cursor()
                cur.execute("UPDATE network SET mode=?,my_password=?,ssid=?,password=?",
                            (mode, my_password, ssid, password))
                con.commit()
                cur.close()

            shell_command('uci set wireless.radio0.linkit_mode=apsta')

            shell_command('uci set wireless.sta.ssid=' + ssid)
            shell_command('uci set wireless.sta.encryption=psk2')
            shell_command('uci set wireless.sta.key=' + password)

            shell_command('uci set wireless.ap.ssid=' + "Simorq-" + last_six)
            shell_command('uci set wireless.ap.encryption=psk2')
            shell_command('uci set wireless.ap.key=' + my_password)

            #  if we had more than one helping simorq, it changes to 100.3 or 100.4 ...
            # shell_command('uci set network.lan.ipaddr=192.168.100.2')
            shell_command('uci set network.lan.macaddr=' + whole_mac())
            shell_command('uci set network.lan.proto=dhcp')
            time.sleep(0.5)
            shell_command('uci commit')
            time.sleep(0.5)
            shell_command('wifi_mode apsta')
            return True
    except Exception as e:
        print e
        return False


def start_set_wifi(mode, my_password):
    global reset_push

    time.sleep(2)

    reset_push = False
    if set_wifi(mode, my_password):
        handle = os.popen("pgrep -f main | xargs kill")
        handle.close()


def start_set_wife(mode, my_password, ssid, password):
    global reset_push

    time.sleep(2)

    reset_push = False
    if set_wife(mode, my_password, ssid, password):
        handle = os.popen("pgrep -f main | xargs kill")
        handle.close()


def get_wifi():
    global debug
    res = None

    try:
        # reader.shell_command("ifconfig ra0 up")

        res = str(shell_command('iwinfo ra0 scan'))

    except Exception as e:
        print(e)
        # reader.my_reader.db_data.add_exception("network.get_wifi", str(e))

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
    return wifi_list


@route('/api/config/<mode>/<my_password>/<api_key>', method=['OPTIONS', 'GET'])
def wifi(mode, my_password, api_key):
    global reset_push, API_KEY

    print (mode, my_password)
    if reset_push:
        if request.method == 'OPTIONS':
            return ""
        elif request.method == 'GET':
            try:
                print "api ap mode received", reset_push
                print mode, my_password, api_key

                if not API_KEY and api_key != "":
                    set_api_key(api_key)

                if API_KEY == api_key and mode == "ap":
                    a = threading.Thread(name="start_set_wifi", args=(mode, my_password), target=start_set_wifi)
                    a.setDaemon(True)
                    a.start()

                    log = {
                        "result": [
                            {
                                "message": "successfully set"
                            }
                        ]
                    }

                    return log
                else:
                    response.status = 400
                    return {"code": "Invalid"}

            except Exception as e:
                print(e)
                response.status = 400
                return {"code": "Invalid"}

        else:
            response.status = 405
            return {"code": 405}
    else:
        response.status = 401
        return {"code": 401}


@route('/api/config/<mode>/<my_password>/<ssid>/<password>/<api_key>', method=['OPTIONS', 'GET'])
def wifi(mode, my_password, ssid, password, api_key):
    global reset_push, API_KEY

    print (mode, my_password, ssid, password, reset_push)
    if reset_push:
        if request.method == 'OPTIONS':
            return ""
        elif request.method == 'GET':
            try:
                print "api set network received", reset_push
                print mode, my_password, ssid, password, api_key, API_KEY

                if not API_KEY and api_key != "":
                    set_api_key(api_key)

                if API_KEY == api_key and (mode == "online" or mode == "repeater"):
                    a = threading.Thread(name="start_set_wife", args=(mode, my_password, ssid, password),
                                         target=start_set_wife)
                    a.setDaemon(True)
                    a.start()

                    log = {
                        "result": [
                            {
                                "message": "successfully set"
                            }
                        ]
                    }

                    return log
                else:
                    response.status = 400
                    return {"code": "Invalid"}

            except Exception as e:
                print(e)
                response.status = 400
                return {"code": "Invalid"}

        else:
            response.status = 405
            return {"code": 405}
    else:
        response.status = 401
        return {"code": 401}


def init_api_config():
    try:
        run(host='0.0.0.0', port=9002)
    except Exception as e:
        print("bottle 3333", e)


# if application is not running, runs it with -s.
# if more than one application is ruuning kills them.
# if can not kill ghost programs, kill them all with -9.
def segfault():
    global debug
    retry = 0
    x, pid, y = None, None, None
    while True:
        try:
            x, pid, y = is_running("main")
            if debug:
                print("x:", x, "pid:", pid)
        except Exception as e:
            print(e)
        if x == 2:
            if debug:
                print("1 is running")
            retry = 0
        elif x > 2:
            if pid:
                if debug:
                    print("fake")
                try:
                    handle = os.popen("kill -9 " + pid)
                    handle.close()
                except Exception as e:
                    print(e)
            else:
                retry += 1
                if retry > 3:
                    retry = 0
                    try:
                        os.kill(int(y[0]), signal.SIGUSR1)
                        time.sleep(1)

                        handle = os.popen("pgrep -f main | xargs kill")
                        handle.close()
                    except Exception as e:
                        print(e)

        else:
            if debug:
                print("not running")
            retry += 1
            if retry > 3:
                retry = 0
                if debug:
                    print("main restarts...")
                try:
                    h = os.popen("python /root/main.py -s > /dev/null 2>&1 &")
                    h.close()
                except Exception as e:
                    print(e)

        time.sleep(3)


def init_reset_factory():
    a = threading.Thread(name="reset_factory", target=reset_factory)
    a.setDaemon(True)
    a.start()


def init_segfault():
    c = threading.Thread(name="segfault", target=segfault)
    c.setDaemon(True)
    c.start()


def start():
    global gg

    c = threading.Thread(name="gpioo", target=gg.gpio_th)
    c.setDaemon(True)
    c.start()

    return c


start().join()
init_reset_factory()
init_segfault()
load_from_db()

b = threading.Thread(name="listen_config", target=init_api_config)
b.setDaemon(True)
b.start()

whole_mac()

while True:
    time.sleep(1)
