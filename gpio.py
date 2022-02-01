import mraa


class Gpio:
    def __init__(self):
        self.PIN_RESET_num = 2
        self.PIN_RESET = None

    def pin_reset_push(self):
        return not self.PIN_RESET.read()

    def gpio_th(self):
        self.PIN_RESET = mraa.Gpio(self.PIN_RESET_num)
        self.PIN_RESET.dir(mraa.DIR_IN)
