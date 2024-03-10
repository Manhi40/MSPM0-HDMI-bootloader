# MSPM0 HDMI Bootloader
This project aims to provide a bootlodaing program that will bootload a TI MSPM0 family microcontroller over any native Linux I2C port. This includes the I2C connectins found inside of HDMI connections.
The only compatible input binary format is TI-TXT as exported from CCS or CCS-Thiea.

## Warning
This project directly controls the I2C/SMBus ports on your Linux PC. This can cause damage and I'm not responsible for anythying that goes wrong! Be careful!

## Usage
To use this, somehow connect your MPSM0 to an I2C bus on your PC, whether that be through HDMI or some other method. This you can use i2c-detect to find which port that corresponds to. In main.py you can change the port number for the BSL object, then update the filename for the TI-TXT file. The project comes with a "blinky.txt" example which is only compatible with a MSPM0Ll304 with an LED connected on pin PA17.
