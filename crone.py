import urllib2
import subprocess
import os

device_mac = ""
version = "2.00.00"


def get_device_mac():
    global device_mac

    point = subprocess.check_output('cat /sys/class/net/eth0/address', shell=True)

    device_mac = str(point[9:11]).upper() + str(point[12:14]).upper() + str(point[15:17]).upper()

    # return last_part


def update_simorq():
    global device_mac

    try:
        download = "http://cloud.simorq.io:9888/api/update/check_version.tar.gz.enc"
        print(download)
        # request = urllib2.urlopen(download)

        request = ""
        try:
            request = urllib2.urlopen(download, timeout=60)
        except urllib2.URLError as e:
            print("urlopen crone", e)

        # save
        output = open("/tmp/check_version.tar.gz.enc", "w")
        output.write(request.read())
        output.close()

        h = os.popen(
            "openssl enc -aes-256-cbc -d -in /tmp/check_version.tar.gz.enc   -out /tmp/check_version.tar.gz"
            "  -k KweKXDEqAQhJy6A4wRbu7XL3YZQVSEjdZpzNC5N4")
        h.close()

        h = os.popen("tar -zxvf /tmp/check_version.tar.gz -C /tmp/")
        h.close()

        h = os.popen("sh /tmp/run_update_simorq.sh > /dev/null 2>&1 &")
        h.close()
    except Exception as e:
        print(e)


def update_sana102():
    global device_mac

    try:
        # if not os.path.isfile("/tmp/SANA-102"):
        #     download = "http://cloud.simorq.io:9888/api/update/update_sana102.tar.gz.enc"
        #     print(download)
        #     # request = urllib2.urlopen(download)
        #
        #     request = ""
        #     try:
        #         request = urllib2.urlopen(download, timeout=120)
        #     except urllib2.URLError as e:
        #         print("urlopen crone", e)
        #
        #     # save
        #     output = open("/tmp/update_sana102.tar.gz.enc", "w")
        #     output.write(request.read())
        #     output.close()
        #
        #     h = os.popen(
        #         "openssl enc -aes-256-cbc -d -in /tmp/update_sana102.tar.gz.enc   -out /tmp/update_sana102.tar.gz"
        #         "  -k KweKXDEqAQhJy6A4wRbu7XL3YZQVSEjdZpzNC5N4")
        #     h.close()
        #
        #     h = os.popen("tar -zxvf /tmp/update_sana102.tar.gz -C /tmp/")
        #     h.close()
        # else:
        download = "http://cloud.simorq.io:9888/api/update/check_version_sana102.tar.gz.enc"
        print(download)
        # request = urllib2.urlopen(download)

        request = ""
        try:
            request = urllib2.urlopen(download, timeout=60)
        except urllib2.URLError as e:
            print("urlopen crone", e)

        # save
        output = open("/tmp/check_version_sana102.tar.gz.enc", "w")
        output.write(request.read())
        output.close()

        h = os.popen("openssl enc -aes-256-cbc -d -in /tmp/check_version_sana102.tar.gz.enc   -out "
                     "/tmp/check_version_sana102.tar.gz  -k KweKXDEqAQhJy6A4wRbu7XL3YZQVSEjdZpzNC5N4")
        h.close()

        h = os.popen("tar -zxvf /tmp/check_version_sana102.tar.gz -C /tmp/")
        h.close()

        h = os.popen("sh /tmp/run_update_sana102.sh > /dev/null 2>&1 &")
        h.close()
    except Exception as e:
        print(e)


def update_sana101():
    global device_mac

    try:
        # if not os.path.isfile("/tmp/SANA-101"):
        #     download = "http://cloud.simorq.io:9888/api/update/update_sana101.tar.gz.enc"
        #     print(download)
        #     # request = urllib2.urlopen(download)
        #
        #     request = ""
        #     try:
        #         request = urllib2.urlopen(download, timeout=120)
        #     except urllib2.URLError as e:
        #         print("urlopen crone", e)
        #
        #     # save
        #     output = open("/tmp/update_sana101.tar.gz.enc", "w")
        #     output.write(request.read())
        #     output.close()
        #
        #     h = os.popen(
        #         "openssl enc -aes-256-cbc -d -in /tmp/update_sana101.tar.gz.enc   -out /tmp/update_sana101.tar.gz"
        #         "  -k KweKXDEqAQhJy6A4wRbu7XL3YZQVSEjdZpzNC5N4")
        #     h.close()
        #
        #     h = os.popen("tar -zxvf /tmp/update_sana101.tar.gz -C /tmp/")
        #     h.close()
        # else:
        download = "http://cloud.simorq.io:9888/api/update/check_version_sana101.tar.gz.enc"
        print(download)
        # request = urllib2.urlopen(download)

        request = ""
        try:
            request = urllib2.urlopen(download, timeout=60)
        except urllib2.URLError as e:
            print("urlopen crone", e)

        # save
        output = open("/tmp/check_version_sana101.tar.gz.enc", "w")
        output.write(request.read())
        output.close()

        h = os.popen("openssl enc -aes-256-cbc -d -in /tmp/check_version_sana101.tar.gz.enc   -out "
                     "/tmp/check_version_sana101.tar.gz  -k KweKXDEqAQhJy6A4wRbu7XL3YZQVSEjdZpzNC5N4")
        h.close()

        h = os.popen("tar -zxvf /tmp/check_version_sana101.tar.gz -C /tmp/")
        h.close()

        h = os.popen("sh /tmp/run_update_sana101.sh > /dev/null 2>&1 &")
        h.close()
    except Exception as e:
        print(e)


def update_sana101p():
    global device_mac

    try:
        # if not os.path.isfile("/tmp/SANA-101P"):
        #     download = "http://cloud.simorq.io:9888/api/update/update_sana101p.tar.gz.enc"
        #     print(download)
        #     # request = urllib2.urlopen(download)
        #
        #     request = ""
        #     try:
        #         request = urllib2.urlopen(download, timeout=120)
        #     except urllib2.URLError as e:
        #         print("urlopen crone", e)
        #
        #     # save
        #     output = open("/tmp/update_sana101p.tar.gz.enc", "w")
        #     output.write(request.read())
        #     output.close()
        #
        #     h = os.popen(
        #         "openssl enc -aes-256-cbc -d -in /tmp/update_sana101p.tar.gz.enc   -out /tmp/update_sana101p.tar.gz"
        #         "  -k KweKXDEqAQhJy6A4wRbu7XL3YZQVSEjdZpzNC5N4")
        #     h.close()
        #
        #     h = os.popen("tar -zxvf /tmp/update_sana101p.tar.gz -C /tmp/")
        #     h.close()
        # else:
        download = "http://cloud.simorq.io:9888/api/update/check_version_sana101p.tar.gz.enc"
        print(download)
        # request = urllib2.urlopen(download)

        request = ""
        try:
            request = urllib2.urlopen(download, timeout=60)
        except urllib2.URLError as e:
            print("urlopen crone", e)

        # save
        output = open("/tmp/check_version_sana101p.tar.gz.enc", "w")
        output.write(request.read())
        output.close()

        h = os.popen("openssl enc -aes-256-cbc -d -in /tmp/check_version_sana101p.tar.gz.enc   -out "
                     "/tmp/check_version_sana101p.tar.gz  -k KweKXDEqAQhJy6A4wRbu7XL3YZQVSEjdZpzNC5N4")
        h.close()

        h = os.popen("tar -zxvf /tmp/check_version_sana101p.tar.gz -C /tmp/")
        h.close()

        h = os.popen("sh /tmp/run_update_sana101p.sh > /dev/null 2>&1 &")
        h.close()
    except Exception as e:
        print(e)


def update_sanap30():
    global device_mac

    try:
        # if not os.path.isfile("/tmp/SANA-P30"):
        #     download = "http://cloud.simorq.io:9888/api/update/update_sanap30.tar.gz.enc"
        #     print(download)
        #     # request = urllib2.urlopen(download)
        #
        #     request = ""
        #     try:
        #         request = urllib2.urlopen(download, timeout=120)
        #     except urllib2.URLError as e:
        #         print("urlopen crone", e)
        #
        #     # save
        #     output = open("/tmp/update_sana200.tar.gz.enc", "w")
        #     output.write(request.read())
        #     output.close()
        #
        #     h = os.popen(
        #         "openssl enc -aes-256-cbc -d -in /tmp/update_sanap30.tar.gz.enc   -out /tmp/update_sanap30.tar.gz"
        #         "  -k KweKXDEqAQhJy6A4wRbu7XL3YZQVSEjdZpzNC5N4")
        #     h.close()
        #
        #     h = os.popen("tar -zxvf /tmp/update_sanap30.tar.gz -C /tmp/")
        #     h.close()
        # else:
        download = "http://cloud.simorq.io:9888/api/update/check_version_sanap30.tar.gz.enc"
        print(download)
        # request = urllib2.urlopen(download)

        request = ""
        try:
            request = urllib2.urlopen(download, timeout=60)
        except urllib2.URLError as e:
            print("urlopen crone", e)

        # save
        output = open("/tmp/check_version_sanap30.tar.gz.enc", "w")
        output.write(request.read())
        output.close()

        h = os.popen("openssl enc -aes-256-cbc -d -in /tmp/check_version_sanap30.tar.gz.enc   -out "
                     "/tmp/check_version_sanap30.tar.gz  -k KweKXDEqAQhJy6A4wRbu7XL3YZQVSEjdZpzNC5N4")
        h.close()

        h = os.popen("tar -zxvf /tmp/check_version_sanap30.tar.gz -C /tmp/")
        h.close()

        h = os.popen("sh /tmp/run_update_sanap30.sh > /dev/null 2>&1 &")
        h.close()
    except Exception as e:
        print(e)


get_device_mac()
update_simorq()
update_sana102()
update_sana101()
update_sana101p()
# update_sanap30()
