from smbus import SMBus
# from smbus2 import SMBus
import zlib

MSP_ADDR = 0x48


def jamcrc(input_data):
    """
    Calculate the JAMCRC value for a given list of 8-bit integers.
    JAMCRC is a variant of CRC32 with no bit-reversal of data and
    the final CRC is XORed with 0xFFFFFFFF.

    :param input_data: Input data as a list of 8-bit integers.
    :return: JAMCRC value as an array of 4, 8-bit integers.
    """
    # Convert the list of 8-bit integers to bytes
    data_bytes = bytes(input_data)

    # Calculate the CRC32 value
    crc = zlib.crc32(data_bytes) ^ 0xFFFFFFFF

    # Convert to an array of 4, 8-bit integers
    crc_bytes = [(crc >> 24) & 0xFF, (crc >> 16) & 0xFF, (crc >> 8) & 0xFF, crc & 0xFF]
    return crc_bytes


def msp_crc(input_data) -> list:
    crc = jamcrc(input_data)
    crc.reverse()
    return crc


class MSPM0_I2C:
    def __init__(self, i2c_bus):
        self._bus = SMBus(i2c_bus)

    def send_command(self, cmd, read_len):
        crc = msp_crc(cmd)
        msg_length = len(cmd)
        self._bus.write_i2c_block_data(MSP_ADDR, 0x80, [msg_length & 0xFF, (msg_length >> 8) & 0xFF] + cmd + crc)
        ret = self._bus.read_i2c_block_data(MSP_ADDR, 0x80, read_len)
        return ret

    def memory_write(self, cmd, data):
        crc = msp_crc([cmd] + data)
        msg_length = len(data) + 1  # +1 for cmd
        data = [msg_length & 0xFF, (msg_length >> 8) & 0xFF] + [cmd] + data + crc
        remaining_data = msg_length

        if msg_length < 32:
            self._bus.write_i2c_block_data(MSP_ADDR, 0x80, data)
        else:
            self._bus.write_i2c_block_data(MSP_ADDR, 0x80, data[:32])

        remaining_data -= 32

        data = data[32:]

        while remaining_data > 0:
            self._bus.write_i2c_block_data(MSP_ADDR, data[0], data[1:32])
            remaining_data -= 32
            data = data[:32]

        ack = self._bus.read_byte(MSP_ADDR)

        if ack == 0x00:
            return True
        return False

    def memory_read(self, cmd):
        crc = msp_crc([cmd])
        self._bus.write_i2c_block_data(MSP_ADDR, 0x80, [0x01, 0x00, cmd] + crc)

        header = self._bus.read_i2c_block_data(MSP_ADDR, 0x80, 4)

        length = header[2] + ((header[3] << 8) & 0xFF00)
        ret = self._bus.read_i2c_block_data(MSP_ADDR, 0x00, length + 4)

        ret_crc = msp_crc(ret[0:-4])
        if ret_crc != ret[-4:]:
            return None

        return ret[1:-4]

    def read_message(self):
        # self.memory_read()
        header = self._bus.read_i2c_block_data(MSP_ADDR, 0x00, 4)
        if header[0] != 0x08:
            return False

        if header[3] != 0x3b:
            return False

        print(header)

        length = header[1] + ((header[2] << 8) & 0xFF00)

        ret = self._bus.read_i2c_block_data(MSP_ADDR, 0x00, length + 3)

        ret_crc = msp_crc([header[3]] + ret[0:-4])

        if ret_crc != ret[-4:]:
            return False

        if ret[0] == 0:
            return True

        print(ret[0])

        return False

    def send_data(self, cmd, msp_data, read_len):
        return self.send_command([cmd] + msp_data, read_len)
