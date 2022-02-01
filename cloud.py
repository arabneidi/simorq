import unirest
import Queue
import time
import main

request_queue = Queue.Queue(30)
total_sock = 0


class CallSensor:
    def __init__(self):
        pass

    @staticmethod
    def callback(response):
        global total_sock

        total_sock -= 1
        # print("code sensor: ", response.code, response.raw_body)
        # main.add_exception("not time out", str(total_sock))

    @staticmethod
    def test(e):
        global total_sock
        print("in time out", str(e))
        total_sock -= 1
        # main.add_exception("time out", str(total_sock))


# receives request contents and sends them to send module.
def send_unirest():
    global total_sock

    unirest.timeout(20)  # 20s timeout

    while True:
        try:
            print ("total sock", total_sock)
            main.add_exception("unirest", str(total_sock))
            if total_sock < 15:
                content = request_queue.get()

                c = CallSensor()

                total_sock += 1

                # unirest.post(content[0], headers=content[2], params=content[1], callback=c.callback,
                #              fail_callback=c.test)
                unirest.get(content[0], callback=c.callback, fail_callback=c.test)

            time.sleep(0.1)
        except Exception as e:
            print(e)