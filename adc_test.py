import spidev
import time

class LTC1859:
    def __init__(self, bus=0, device=0, max_speed_hz=50000, mode=0b11):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = max_speed_hz
        self.spi.mode = mode

    def read_channel(self, channel):
        if not (0 <= channel <= 7):
            raise ValueError("Channel must be between 0 and 7.")
        command = 0x8000 | (channel << 11)
        self.spi.xfer2([(command >> 8) & 0xFF, command & 0xFF])
        time.sleep(0.001)  # Delay for signal stabilization
        adc = self.spi.xfer2([0x00, 0x00])
        return ((adc[0] & 0xFF) << 8) | (adc[1] & 0xFF)

    def close(self):
        self.spi.close()

    def monitor_channels(self, channels, change_threshold):
        last_readings = {channel: None for channel in channels}
        try:
            while True:
                for channel in channels:
                    current_reading = self.read_channel(channel)
                    last_reading = last_readings[channel]
                    if last_reading is None or abs(current_reading - last_reading) > change_threshold:
                        print(f"Significant change in channel {channel}: {current_reading}")
                        last_readings[channel] = current_reading
                time.sleep(0.01)  # Adjust the sleep time as necessary
        except KeyboardInterrupt:
            print("Monitoring stopped.")

# Exemple d'utilisation de la classe LTC1859
if __name__ == "__main__":
    adc = LTC1859()
    try:
        channels = [0, 1, 2, 3, 4, 5, 6, 7]  # Channels to monitor
        change_threshold = 10  # Change threshold to decide when to print new data
        adc.monitor_channels(channels, change_threshold)
    finally:
        adc.close()
