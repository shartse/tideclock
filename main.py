
from secrets import SSID, PASSWORD
from time import sleep, localtime, mktime
from machine import Pin
import network
import urequests
import ntptime

from epd import EPD_2in7, EPD_HEIGHT, EPD_WIDTH

"""Connect to WiFi using the credentials from secrets.py"""
def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        sleep(1)


"""Returns the string padded with leading zeros until it reaches the desired width"""
def zfill(str, width):
    if len(str) >= width:
        return str
    else:
        new_str = "0" + str
        return zfill(new_str, width)

"""Maps value from one range [fromMin, fromMax] into another [toMin, toMax]"""
def map_range(value, from_min, from_max, to_min, to_max):
    # Figure out how 'wide' each range is
    from_span = from_max - from_min
    to_span = to_max - to_min

    # Convert the from range into a 0-1 range (float)
    value_scaled = float(value - from_min) / float(from_span)

    # Convert the 0-1 range into a value in the to range.
    return to_min + (value_scaled * to_span)

"""Return the current timestamp offset by UTC_OFFSET"""
def timezone_current_time():
    now_utc = localtime()
    now_utc_seconds = mktime(now_utc)
    timezone_seconds = now_utc_seconds + (UTC_OFFSET * 60 * 60)
    return localtime(timezone_seconds)

"""Return the current date in the for 'YYYYMMDD'"""
def current_date():
    now_timezone = timezone_current_time()
    return str(now_timezone[0]) + zfill(str(now_timezone[1]), 2) + zfill(str(now_timezone[2]), 2)

"""
An object that draws a plot of 'data' into a 'framebuf', offset by the 'border_width'. 
'data' is a list of numbers, which are used for y values. Their indices are used for x values.
"""
class Plot:
    WHITE=0xff
    BLACK=0x00

    def __init__(self, frame_buf, data, border_width):
        self.frame_buf = frame_buf
        self.data = data
        self.border_width = border_width
       
    def x_axis_len(self):
        return EPD_HEIGHT - (self.border_width * 2)
     
    def y_axis_len(self):
        return EPD_WIDTH - (self.border_width * 2)
        
    def draw_title(self, title):
        start = int((EPD_HEIGHT/2) - ((len(title)*8)/2))
        self.frame_buf.text(title, start, 5, Plot.BLACK)
        
    def draw_x_axis(self):
        self.frame_buf.hline(self.border_width, EPD_WIDTH - self.border_width, self.x_axis_len(), Plot.BLACK)
        
    def draw_y_axis(self):
        self.frame_buf.vline(self.border_width, self.border_width, self.y_axis_len(), Plot.BLACK)

    def plot_points(self):
        # data values range
        max_val = max(self.data) + 1
        min_val = min(self.data) - 1
        self.label_y_axis(max_val + 1, min_val -1)
        # y axis screen range
        y_min = EPD_WIDTH - self.border_width
        y_max = self.border_width

        x_min = self.border_width
        interval = int(self.x_axis_len() / len(self.data))
        self.label_x_axis(interval)

        self.draw_now_line()
        for i,val in enumerate(self.data):
            y = int(map_range(val, min_val, max_val, y_min, y_max))
            x = int(x_min + ((i+1) * interval))
            self.frame_buf.rect(x, y, 2, 2, Plot.BLACK, True)

    def draw_now_line(self):
        # Draw a vertical line representing the current time (rounded down to the hour)
        x_min = self.border_width
        x_max = EPD_HEIGHT - self.border_width

        now = timezone_current_time()
        time_now = now[3]

        y = self.border_width
        x = int(map_range(time_now, 0, 23, x_min, x_max))
        self.frame_buf.vline(x, y, self.y_axis_len(), Plot.BLACK)

    def label_y_axis(self, max_val, min_val):
        y_min = EPD_WIDTH - self.border_width
        y_max = self.border_width
        x = self.border_width    
        for i in range(int(min_val), int(max_val)):
            # Draw ticks at every interval
            y = int(map_range(i, min_val, max_val, y_min, y_max))
            self.frame_buf.hline(x-2, y, 4, Plot.BLACK)
            # Draw y values at every interval, offset 4 pixels since chars are 8 pixels wide
            y = int(map_range(i, min_val, max_val, y_min, y_max))
            self.frame_buf.text(str(i), x-self.border_width, y-4, Plot.BLACK)

    def label_x_axis(self, interval):
        x_min = self.border_width
        y = EPD_WIDTH - self.border_width
        for i, _ in enumerate(self.data):
            # Draw ticks at every interval
            x = x_min + ((i+1)*interval)
            self.frame_buf.vline(x , y - 2, 4, Plot.BLACK)
            # Draw the times for every 6th entry, offset 4 pixels since chars are 8 wide
            if i % 6 == 0:
                self.frame_buf.text(str(i), x - 4, y + 3, Plot.BLACK)

    def draw_pixel(self, x, y):
        self.frame_buf.pixel(x, y, Plot.BLACK)

    def draw_centered_bitmap(self, bitmap):
        width = len(bitmap[0])
        start_x = int((EPD_HEIGHT - width) / 2)
        height = len(bitmap)
        start_y = int((EPD_WIDTH - height) / 2)
        self.draw_bitmap(bitmap, start_x, start_y)

    def draw_bitmap(self, bitmap, start_x, start_y):
        for (y, row) in enumerate(bitmap):
            for (x, pixel) in enumerate(row):
                if pixel == 0:
                    self.draw_pixel(start_x+x, start_y+y) 
"""
A wrapper around an e-paper display and a NOAA tide data API. Provide an 'epd' and a 'station' (the id of the NOAA station
you're interested inL https://tidesandcurrents.noaa.gov/map/).
"""
class TideClock:
    NOAA_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

    def __init__(self, epd, station):
        self.epd = epd
        self.station = station
        self.last_fetched = None
        self.predictions = None

    def fetch_and_plot_tide_data(self):
        # Initialize the EPD on start up
        self.epd.image1Gray_Landscape.fill(0xff)
        self.epd.EPD_2IN7_Init()
        self.epd.EPD_2IN7_Clear()

        # Query some data and draw it on the EPD buffer
        self.fetch_tide_data()
        self.plot_tide_data()

        # Draw the contents on the buffer on the EPD display.
        # This is when the EPD is actually drawn to.
        self.epd.EPD_2IN7_Display_Landscape(self.epd.buffer_1Gray_Landscape)

    def plot_tide_data(self):
        plot = Plot(frame_buf=self.epd.image1Gray_Landscape,
                    data=self.predictions,
                    border_width=18)

        plot.draw_y_axis()
        plot.draw_x_axis()

        date = current_date()
        title = "Tides: {month}/{day}/{year}".format(year=date[0:4], month=date[4:6], day=date[6:] )
        plot.draw_title(title)
        plot.plot_points()

    """Fetch hourly tide height prediction for the current day at the specified tide station.
    See https://tidesandcurrents.noaa.gov/products.html for more information about how queries are structured."""
    def fetch_tide_data(self):
        today = current_date()
        if today != self.last_fetched:
            self.last_fetched = today
            query = ("{url}?"
             "begin_date={start}"
             "&end_date={end}"
             "&station={station}"
             "&product=predictions"
             "&datum=MLLW"
             "&time_zone=lst_ldt"
             "&interval=h"
             "&units=english"
             "&application=DataAPI_Sample"
             "&format=json").format(url=TideClock.NOAA_URL, start=today, end=today, station=self.station)
            result = urequests.get(query)
            data = result.json().get('predictions')
            self.predictions = [float(x.get('v')) for x in data]

# This is the tide data collection station at the Golden Gate bridge. Found using https://tidesandcurrents.noaa.gov/map/.
STATION = "9414290"

# PST'a offset from UTC. micropython's NTP implementation is UTC only.
UTC_OFFSET = -7

# Sleep briefly (this helps main.py successfully run on boot more consistently)
sleep(1)
led = Pin("LED", Pin.OUT)
led.on()

# Connect to Wifi
connect_to_wifi(SSID, PASSWORD)

# Synchronize the RTC with NTP
ntptime.settime()

# Initialize the EPD device
display = EPD_2in7()

# Initialize the tide clock, specifying the epd, the data source and station
tide_clock = TideClock(display, STATION)

# Clear the epd, fetch tide data for the first time and plots it.
tide_clock.fetch_and_plot_tide_data()

# Register a callback to the Key0 on the epd, which clears, re-fetches the data (if needed) and plots it.
key0 = Pin(15, Pin.IN, Pin.PULL_UP)
key0.irq(lambda p:tide_clock.fetch_and_plot_tide_data(), trigger=Pin.IRQ_FALLING)
