import os
import subprocess
import sqlite3 as lite
import time
import datetime

db_address = '/root/app.db'
firmware = "1.00.00"
updater = "crone"
update_done = 0
current_path = ""


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
        print(e)


def cron_task():
    global current_path

    try:
        point = subprocess.check_output('cat /sys/class/net/eth0/address', shell=True)

        device_mac = str(point[12:14]).upper() + str(point[15:17]).upper()
        i = 0
        for ch in device_mac:
            i += int(ch, 16)

        with open(current_path + "/root", "w") as my_file:
            my_file.write(str(i) + "       *       *       *       *       python /root/cron.py > /dev/null  2>&1 &")

    except Exception as e:
        print(e)


def upgrade():
    global current_path, update_done, db_address, firmware, updater

    try:

        current_path = os.path.dirname(os.path.abspath(__file__))
        handle = os.popen("pgrep -f main | xargs kill")
        handle.close()
        handle = os.popen("pgrep -f reset_factory | xargs kill")
        handle.close()

        time.sleep(4)

        h = os.popen("echo V > /dev/watchdog1")
        h.close()

        h = os.popen("cp -R " + current_path + "/backup/. /etc/")
        h.close()
        #
        # h = os.popen("cp -R " + current_path + "/module/. /usr/lib/python2.7/site-packages/")
        # h.close()

        h = os.popen("cp -R " + current_path + "/first_up/. /etc/config/")
        h.close()

        h = os.popen("tar -zxf " + current_path + "/root.tar.gz -C /root/")
        h.close()

        # h = os.popen("tar -zxf " + current_path + "/www.tar.gz -C /www/")
        # h.close()

        h = os.popen("chmod 777 /root/* -R")
        h.close()

        # h = os.popen("chmod 777 /www/* -R")
        # h.close()

        cron_task()
        h = os.popen("cp -R " + current_path + "/root /etc/crontabs/")
        h.close()

        update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        con = lite.connect(db_address)
        con.row_factory = lite.Row
        with con:
            cur = con.cursor()
            cur.execute("UPDATE version SET ver=?,date=?,updater=?", (firmware, update_time, updater))
            con.commit()
            cur.close()
            print("committed")

        print("finished")

        update_done = 1

        time.sleep(1)

        # handle = os.popen("reboot")
        # handle.close()
    except Exception as e:
        print(e)


upgrade()
