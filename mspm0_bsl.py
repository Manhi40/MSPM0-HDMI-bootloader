from mspm0_i2c import MSPM0_I2C


def slice_to_int(slice: list):
    return int.from_bytes(slice, 'little')


def int_to_4_byte_addr(addr):
    return [addr & 0xFF, (addr >> 8) & 0xFF, (addr >> 16) & 0xFF, (addr >> 24) & 0xFF]


class MSPM0_BSL:
    def __init__(self, i2c_bus):
        self._mspm0 = MSPM0_I2C(i2c_bus)
        self.info = None

    def connect(self):
        try:
            status = self._mspm0.send_command([0x12], 1)
            return status is not None and status[0] == 0x00
        except OSError:
            return False

    def get_device_info(self):
        info = {}
        try:
            dev_info = self._mspm0.memory_read(0x19)
            if dev_info is None:
                return None

            print([hex(x) for x in dev_info])
            info["Interpreter Version"] = slice_to_int(dev_info[0:2])
            info["Build ID"] = slice_to_int(dev_info[2:4])
            info["Application Version"] = slice_to_int(dev_info[4:8])
            info["Plug-in interface version"] = slice_to_int(dev_info[8:10])
            info["BSL Max buffer size"] = slice_to_int(dev_info[10:12])
            info["BSL Buffer Start address"] = slice_to_int(dev_info[12:16])
            info["BCR Config ID"] = slice_to_int(dev_info[16:20])
            info["BSL Config ID"] = slice_to_int(dev_info[20:24])

        except OSError:
            return None

        self.info = info
        return info

    def unlock_device(self):
        try:
            # Write the password to BSL
            if not self._mspm0.memory_write(0x21, [0xFF] * 32):
                print("erase failed")

            # Read the message
            if not self._mspm0.read_message():
                print("erase message failed")

            print("erased")

        except OSError:
            print("i2c error")
            return None

    def mass_erase(self):
        self._mspm0.send_command([0x15], 1)

        if not self._mspm0.read_message():
            print("mass erase failed")

    def start_application(self):
        print(self._mspm0.send_command([0x40], 1))

    def program_block(self, address, data):
        if len(data) > self.info["BSL Max buffer size"]:
            raise ValueError

        if len(address) != 4:
            raise ValueError

        # if len(data) < 8:
        #     data += [0xFF] * (8 - len(data))

        print(data)

        print("programming" % address)

        buffer = address + data

        if not self._mspm0.memory_write(0x20, buffer):
            print("write error")
        if not self._mspm0.read_message():
            print("message error")

    def program_hex(self, filename: str):
        with open(filename, "r") as fw_file:
            offset = 0
            for line in fw_file:
                if "@" not in line and "q" not in line:
                    line = line.strip()
                    values = line.split(' ')
                    data = [int("0x" + x, 16) for x in values]
                    print(offset)
                    self.program_block(int_to_4_byte_addr(offset), data)
                    offset += len(data)
                elif "@" in line:
                    value = line.strip().strip("@")
                    offset = int("0x" + value, 16)

    def verify(self, filename):
        fw = []
        with open(filename, "r") as fw_file:
            for line in fw_file:
                if "@" not in line and "q" not in line:
                    line = line.strip()
                    values = line.split(' ')
                    data = [int("0x" + x, 16) for x in values]
                    fw.append(data)
