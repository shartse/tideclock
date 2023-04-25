## Overview
This is an `MicroPython` program for a Raspberry Pi Pico W micro-controller which fetches tide height predictions from NOAA and displays the predictions for
the current day on a ePaper (also known as eInk) display. There display graphs the height predictions as well as indicating the current time, making it easy to see
if the tide is rising or falling and the time of the next low or high tide. Pressing `Key0` on the display triggers a refresh, which redraws the graph and current time as
well as re-fetching data if needed.

## Tools
+ [Raspberry Pi Pico WH](https://www.raspberrypi.com/products/raspberry-pi-pico/) - WiFi (`W`) is required to make NOAA API requests, but pre-soldered headers (`H`) just makes this a solderless project.
+ [Waveshare Pico ePaper display](https://www.waveshare.com/wiki/Pico-ePaper-2.7) - This device is designed to plug directly onto the Pico's headers. Other Waveshare devices should work as well,
you'd just need to do the wiring yourself.
+ [MicroPython](https://micropython.org/)
+ `MicroPython` editor and deployment tool for interating such as [`Thonny`](https://projects.raspberrypi.org/en/projects/getting-started-with-the-pico/2)
+ [Waveshare EPD drivers](https://github.com/waveshare/Pico_ePaper_Code) for your device
+ [NOAA tides and currents API](https://tidesandcurrents.noaa.gov/products.html)

## Getting Started
1. Attach your Pico and EPD to each other. Then, plug your USB into the Pico and your computer.
2. Find the module corresponding to your EPD in waveshare's [repo](https://github.com/waveshare/Pico_ePaper_Code). I suggest running it directly on you Pico with `Thonny` and make sure it displays the
 sequence of test images. Then, copy it onto your pico under the name `epd.py`.
3. Create a file named `secrets.py` and in it define variables `SSID` and `PASSWORD` for the WiFi network you plan to use. Copy `secrets.py` onto your pico.
4. In `main.py`, update `STATION` and `UTC_OFFSET` to match the location and timezone you want to display. Use the [station listings](https://github.com/waveshare/Pico_ePaper_Code) to find the station id.
5. Verify the GPIO pin that corresponds to your EPD's `Key0`
6. Use `Thonny` to try running `main.py` on your Pico. The first sign of life should be the onboard LED turning on.
7. If you want the program to run automatically, copy `main.py` to your Pico directly and it should always run on start up.



