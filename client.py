import websocket
import json
import threading
import time
import os
import calendar
import mraa
import sys
import serial
import subprocess
import socket

VERSION = "5.5"


class Thing:
    def __init__(self):
        self.actions = {"setrelay1": self.setrelay1,
                        "setrelay2": self.setrelay2,
                        "settemp": self.settemp,
                        "setcurrent": self.setcurrent,
                        "setlock1": self.setlock1,
                        "setlock2": self.setlock2,
                        "update": self.update,
                        }
        self.RELAY1 = 46
        self.RELAY1_pin = None
        self.RELAY2 = 0
        self.RELAY2_pin = None
        self.SWITCH1 = 3
        self.SWITCH1_pin = None
        self.SWITCH2 = 4
        self.LED1 = 1
        self.LED1_pin = None
        self.LED2 = 2
        self.LED2_pin = None
        self.RESET = 5
        self.RESET_pin = None
        self.ACTIVE_PEAK = 2
        self.ACTIVE_PEAK_pin = None
        self.SWITCH2_pin = None
        self.SWITCH1_LAST_VALUE = 1
        self.SWITCH2_LAST_VALUE = 1
        self.beacon = "111"
        self.web_sock = None
        self.time_end = calendar.timegm(time.gmtime())
        self.connection_alive = 0
        self.model = "SANA-102s"
        self.relay1 = 0
        self.relay2 = 0
        self.lock1 = 0
        self.lock2 = 0
        self.switch1 = 0
        self.switch2 = 0
        self.temp = 0
        self.current = 0
        self.up_time = ""
        self.eth_mac = ""
        self.wifi_mac = ""
        self.load_eth_mac()
        self.load_wifi_mac()

    def start(self):

        self.gpio_init()

        a = threading.Thread(name="hello", target=self.send_info)
        a.setDaemon(True)
        a.start()

        a = threading.Thread(name="switch", target=self.switches)
        a.setDaemon(True)
        a.start()

    def switches(self):

        time_later = time.time()
        s_l_v = 0
        phase = 0
        counter = 0

        while True:
            try:
                time_now = time.time()
                s1 = self.SWITCH1_pin.read()

                if s1 != s_l_v:
                    s_l_v = s1
                    if counter == 0 and 2 < time_now - time_later < 3:
                        counter += 1
                    elif counter == 1 and 3 < time_now - time_later < 4:
                        counter += 1
                    elif counter == 2 and 2 < time_now - time_later < 3:
                        counter += 1
                    else:
                        counter = 0
                if counter == 3:
                    pass
                    
                r1 = self.RELAY1_pin.read()
                # print ("s1, r1", s1, r1)
                if s1 != self.SWITCH1_LAST_VALUE:
                    self.SWITCH1_LAST_VALUE = s1
                    if not self.lock1:
                        if r1:
                            self.RELAY1_pin.write(0)
                            self.relay1 = 0
                            self.LED1_pin.write(0)
                        else:
                            self.RELAY1_pin.write(1)
                            self.relay1 = 1
                            self.LED1_pin.write(1)

                s2 = self.SWITCH2_pin.read()
                r2 = self.RELAY2_pin.read()
                # print ("s2, r2", s2, r2)
                if s2 != self.SWITCH2_LAST_VALUE:
                    self.SWITCH2_LAST_VALUE = s2
                    if not self.lock2:
                        if r2:
                            self.RELAY2_pin.write(0)
                            self.relay2 = 0
                            self.LED2_pin.write(0)
                        else:
                            self.RELAY2_pin.write(1)
                            self.relay2 = 1
                            self.LED2_pin.write(1)
                # time.sleep(0.1)
            except Exception as e:
                print e

    def gpio_init(self):
        self.RELAY1_pin = mraa.Gpio(self.RELAY1)
        self.RELAY1_pin.dir(mraa.DIR_OUT)

        self.RELAY2_pin = mraa.Gpio(self.RELAY2)
        self.RELAY2_pin.dir(mraa.DIR_OUT)

        self.LED1_pin = mraa.Gpio(self.LED1)
        self.LED1_pin.dir(mraa.DIR_OUT)

        self.LED2_pin = mraa.Gpio(self.LED2)
        self.LED2_pin.dir(mraa.DIR_OUT)

        self.RESET_pin = mraa.Gpio(self.RESET)
        self.RESET_pin.dir(mraa.DIR_IN)

        self.ACTIVE_PEAK_pin = mraa.Gpio(self.ACTIVE_PEAK)
        self.ACTIVE_PEAK_pin.dir(mraa.DIR_OUT)
        self.ACTIVE_PEAK_pin.write(1)

        self.SWITCH1_pin = mraa.Gpio(self.SWITCH1)
        self.SWITCH1_pin.dir(mraa.DIR_IN)
        self.SWITCH1_pin.write(1)

        self.SWITCH2_pin = mraa.Gpio(self.SWITCH2)
        self.SWITCH2_pin.dir(mraa.DIR_IN)
        self.SWITCH2_pin.write(1)

    def setrelay1(self, parsed_json):
        print("in setrelay1", parsed_json["value"])

        self.RELAY1_pin.write(int(parsed_json["value"]))
        self.SWITCH1_pin.write(int(parsed_json["value"]))
        self.relay1 = int(parsed_json["value"])

        print ("passed")
        try:
            return {"seq": parsed_json["seq"], "action": str(parsed_json["action"]),
                    "response": "OK"}

        except Exception as e:
            print(e)
            return {"seq": parsed_json["seq"], "action": str(parsed_json["action"]),
                    "response": "FAIL"}

    def setrelay2(self, parsed_json):
        try:
            print("in setrelay2", parsed_json["value"])

            self.RELAY2_pin.write(int(parsed_json["value"]))
            self.SWITCH2_pin.write(int(parsed_json["value"]))
            self.relay2 = int(parsed_json["value"])

            return {"seq": parsed_json["seq"], "action": str(parsed_json["action"]),
                    "response": "OK"}

        except Exception as e:
            print(e)
            return {"seq": parsed_json["seq"], "action": str(parsed_json["action"]),
                    "response": "FAIL"}

    def setlock1(self, parsed_json):
        print("in setlock1", parsed_json["value"])

        self.lock1 = int(parsed_json["value"])

        print ("passed")
        try:
            return {"seq": parsed_json["seq"], "action": str(parsed_json["action"]),
                    "response": "OK"}

        except Exception as e:
            print(e)
            return {"seq": parsed_json["seq"], "action": str(parsed_json["action"]),
                    "response": "FAIL"}

    def setlock2(self, parsed_json):
        try:
            print("in setlock2", parsed_json["value"])

            self.lock2 = int(parsed_json["value"])

            return {"seq": parsed_json["seq"], "action": str(parsed_json["action"]),
                    "response": "OK"}

        except Exception as e:
            print(e)
            return {"seq": parsed_json["seq"], "action": str(parsed_json["action"]),
                    "response": "FAIL"}

    def update(self, parsed_json):
        return {"seq": parsed_json["seq"], "action": str(parsed_json["action"]),
                "response": "OK"}

    def settemp(self, temp):
        self.temp = temp

    def setcurrent(self, current):
        self.current = current

    def getrelay1(self):
        return self.relay1

    def getrelay2(self):
        return self.relay2

    def gettemp(self):
        self.temp = 71
        return self.temp

    def getcurrent(self):
        return self.current

    @staticmethod
    def upgrade(parsed_json):
        print("in upgrade")
        try:
            h = os.popen("python /root/crone.py > /dev/null 2>&1 &")
            h.close()

            return {"action": str(parsed_json["action"]),
                    "response": {"text": "OK", "code": 200}
                    }

        except Exception as e:
            print(e)
            return {"action": str(parsed_json["action"]),
                    "response": {"text": "FAIL", "code": 408}}

    def load_eth_mac(self):
        try:
            while len(self.eth_mac) < 17:
                point = self.shell_command('cat /sys/class/net/eth0/address')

                whole_part = str(point[0:2]).upper() + ":" + str(point[3:5]).upper() + ":" + str(
                    point[6:8]).upper() + ":" + str(
                    point[9:11]).upper() + ":" + str(point[12:14]).upper() + ":" + str(point[15:17]).upper()

                self.set_eth_mac(whole_part)
                self.beacon = whole_part.replace(":", "")
                time.sleep(1)
        except Exception as e:
            print(e)

    def set_eth_mac(self, eth_mac):
        self.eth_mac = eth_mac

    def get_eth_mac(self):
        return self.eth_mac

    def load_wifi_mac(self):
        try:
            while len(self.wifi_mac) < 17:
                last_part = self.shell_command(
                    'echo $(dd bs=1 skip=7 count=3 if=/dev/mtd2 2>/dev/null | hexdump -v -n 3 -e \'3/1'
                    ' "%02X"\')')
                wifi_mac = (self.get_eth_mac())[0] + "E" + (self.get_eth_mac())[2:9] + "0" + last_part[1:2] + ":" + \
                           last_part[2:4] + ":" + last_part[4:6]
                self.set_wifi_mac(wifi_mac)
                time.sleep(1)
        except Exception as e:
            print(e)

    def set_wifi_mac(self, wifi_mac):
        self.wifi_mac = wifi_mac

    def get_wifi_mac(self):
        return self.wifi_mac

    def upTime(self):
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])

            self.up_time = uptime_seconds * 1000

            return str(self.up_time)
        except Exception as e:
            print(e)

    @staticmethod
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

    def send_info(self):
        global VERSION

        try:
            hostname = socket.gethostname()
            IPAddr = socket.gethostbyname(hostname)
            while True:
                try:
                    time.sleep(5)
                    if self.connection_alive == 2:
                        self.web_sock.close()

                    self.time_end = calendar.timegm(time.gmtime())

                    while self.connection_alive == 1:
                        info = {"action": "info", "model": self.model, "temp": self.gettemp(), "ip": IPAddr,
                                "relay1": self.getrelay1(), "relay2": self.getrelay2(), "freeMem": "0",
                                "version": VERSION, "mac": self.get_wifi_mac(), "serialno": self.beacon,
                                "upTime": self.upTime()}

                        end = info
                        # print("INFO::::", end)
                        resp = json.dumps(end)

                        self.web_sock.send(resp)

                        time_start = calendar.timegm(time.gmtime())
                        # print("in hello", time_start - time_end)
                        if (time_start - self.time_end) >= 60:  # 60 seconds
                            print("server dead!")
                            self.time_end = calendar.timegm(time.gmtime())
                            self.connection_alive = 2
                            self.web_sock.close()

                        time.sleep(5)

                except Exception as e:
                    print(e)

        except Exception as e:
            print(e)


class Websocket:
    def __init__(self, chic):
        self.BACK_OFF = 5
        self.chic = chic

    def start(self):
        c = threading.Thread(name="web_socket", target=self.web_socket)
        c.setDaemon(True)
        c.start()

    def on_message(self, ws, message):

        print("From server", message)
        try:
            res = json.loads(message)

            if "action" in res:
                if res["action"] == "error":
                    print ("error", res["response"])
                elif res["action"] == "info":
                    self.chic.time_end = calendar.timegm(time.gmtime())
                elif res["action"] in self.chic.actions:
                    end = self.chic.actions[res["action"]](res)
                    print("RESPONSE::::", end)
                    resp = json.dumps(end)

                    ws.send(resp)
                else:
                    end = {"action": res["action"], "response": "Invalid Action"}
                    print("RESPONSE::::", end)
                    resp = json.dumps(end)

                    ws.send(resp)

            else:
                end = {"action": "error", "response": "no Action"}
                print("ERROR RESPONSE::::", end)
                resp = json.dumps(end)

                ws.send(resp)

        except Exception as e:
            print(e)
            end = {"action": "error", "response": "bad json"}
            print("ERROR RESPONSE::::", end)
            resp = json.dumps(end)

            ws.send(resp)

    def on_error(self, ws, error):
        # print("in error", error)

        self.chic.connection_alive = 3

    def on_close(self, ws):
        # print("in close")
        self.chic.connection_alive = 3

    def on_open(self, ws):
        # print("token sent", reader.my_reader.setting.auto_launch)

        self.chic.connection_alive = 1

    def on_ping(self, ws, data):
        print("on ping")

    def on_pong(self, ws, data):
        # print("on pong")
        pass

    def web_socket(self):

        while True:
            time.sleep(self.BACK_OFF)
            try:
                # websocket.enableTrace(True)

                if self.chic.connection_alive == 0 or self.chic.connection_alive == 3:
                    self.chic.web_sock = websocket.WebSocketApp("ws://192.168.100.1:9001/",
                                                                on_message=self.on_message,
                                                                on_open=self.on_open,
                                                                on_error=self.on_error,
                                                                on_close=self.on_close,
                                                                on_pong=self.on_pong,
                                                                on_ping=self.on_ping
                                                                )

                    self.chic.web_sock.run_forever(ping_timeout=20, ping_interval=30)

                    # print("old ended!")
            except Exception as e:
                print(e)
                self.chic.connection_alive = 3


class Decoder(object):
    def __init__(self, header, ender, crc_range, devices):
        self.header = header
        self.ender = ender
        self.len = 0
        self.lst = []
        self.cmd = 0
        self.perform_on_device = devices
        self.crc_start, self.crc_end = crc_range

    @staticmethod
    def crc_checker(srt, end, length, lst):
        crc = 0
        for i in range(srt, length - end):
            crc ^= lst[i]
        # print("crc", crc, lst[length - end])
        return crc == lst[length - end]

    def decode(self, data):
        try:
            self.lst += [int(x, 16) for x in ["{:02x}".format(ord(ch)) for ch in data]]
            # self.lst += data

            while len(self.lst) >= 6:
                if self.lst[0] == self.header:
                    self.len = 7
                    if 5 < self.len < 35:
                        if self.len <= len(self.lst):
                            if self.lst[self.len - 1] == self.ender:
                                lll = self.lst[:self.len]
                                if self.crc_checker(self.crc_start, self.crc_end, self.len, lll):
                                    self.perform_on_device["0"](lll)
                                for i in range(self.len):
                                    self.lst.pop(0)
                            else:
                                self.lst.pop(0)
                        else:
                            break
                    else:
                        self.lst.pop(0)
                else:
                    self.lst.pop(0)
        except Exception as e:
            print(e)


# serial decoder.
class SerialDecoder:
    def __init__(self, chic):
        self.header = 0xAA
        self.ender = 0xBB
        self.len = 0
        self.lst = []
        self.cmd = 0
        self.chic = chic

        self.crc_start, self.crc_end = (1, 2)
        self.perform_on_device = {"0": self.sensor}

    def sensor(self, lst):
        TEMP = 256 * lst[1] + lst[2]
        CURRENT = 256 * lst[3] + lst[4]
        self.chic.temp = TEMP
        self.chic.current = CURRENT

        print ("xxx:", TEMP, CURRENT)

    @staticmethod
    def crc_checker(srt, end, length, lst):
        crc = 0
        for i in range(srt, length - end):
            crc ^= lst[i]
        # print("crc", crc, lst[length - end])
        return crc == lst[length - end]

    def decode(self, data):
        try:
            self.lst += [int(x, 16) for x in ["{:02x}".format(ord(ch)) for ch in data]]
            # self.lst += data

            while len(self.lst) >= 6:
                if self.lst[0] == self.header:
                    self.len = 7
                    if 5 < self.len < 35:
                        if self.len <= len(self.lst):
                            if self.lst[self.len - 1] == self.ender:
                                lll = self.lst[:self.len]
                                if self.crc_checker(self.crc_start, self.crc_end, self.len, lll):
                                    self.perform_on_device["0"](lll)
                                for i in range(self.len):
                                    self.lst.pop(0)
                            else:
                                self.lst.pop(0)
                        else:
                            break
                    else:
                        self.lst.pop(0)
                else:
                    self.lst.pop(0)
        except Exception as e:
            print(e)


# reads from serial.
def serial_th(chic):
    try:
        ser = serial.Serial(port='/dev/ttyS0', baudrate=600)
        serial_d = SerialDecoder(chic)

        while True:
            try:
                if ser.isOpen():
                    # print "after open"
                    try:
                        data = ser.read(7)

                        if True:
                            print(":".join("{:02x}".format(ord(ch)) for ch in data))

                        serial_d.decode(data)

                    except serial.SerialException as e:
                        print(e)
                        time.sleep(1)
                else:
                    try:
                        ser = serial.Serial(port='/dev/ttyS0', baudrate=300)
                    except Exception as e:
                        print(e)

            except Exception as e:
                print(e)
                time.sleep(1)

    except Exception as e:
        print(e)


def main(argv):
    try:
        chic = Thing()
        chic.start()

        ws = Websocket(chic)
        ws.start()

        a = threading.Thread(name="serial", args=(chic,), target=serial_th)
        a.setDaemon(True)
        a.start()

        while True:
            time.sleep(2)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    main(sys.argv)
