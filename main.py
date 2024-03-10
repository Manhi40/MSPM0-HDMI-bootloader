from mspm0_bsl import MSPM0_BSL
import time
import sys

device = MSPM0_BSL(3)


if not device.connect():
    print("Failed to connect")
    sys.exit()
else:
    print("connection success")

dev_info = device.get_device_info()

if dev_info is not None:
    print(dev_info)
else:
    print("Failed to get dev info")
    sys.exit()

device.unlock_device()
device.mass_erase()
time.sleep(1)
device.program_hex("blinky.txt")
device.start_application()
