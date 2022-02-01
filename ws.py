from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import json
import sys


def info(ws, parsed_json):
    try:
        print parsed_json["ip"], parsed_json["serialno"]
        return {"action": "info", "response": "OK"}
    except Exception as e:
        print e


actions = {"info": info,
           }


class SimpleEcho(WebSocket):
    def handleMessage(self):
        try:
            message = self.data
            res = json.loads(message)

            if "action" in res:
                if res["action"] in actions:
                    end = actions[res["action"]](self, res)
                    resp = json.dumps(end)
                    # print("RESPONSE::::", resp)

                    self.sendMessage(resp)

        except Exception as e:
            print e

    def handleConnected(self):
        print(self.address, 'connected')
        try:
            print("New client connected and was given address", self.address)
        except Exception as e:
            print e

    def handleClose(self):
        print("Client() disconnected", self.address)


def main(argv):
    ws_server = SimpleWebSocketServer('', 9001, SimpleEcho)
    ws_server.serveforever()


if __name__ == "__main__":
    main(sys.argv)
