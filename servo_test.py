from machine import UART, Pin
import time

# UART for Dynamixel: 1 Mbps, 8N1
uart = UART(0, baudrate=1000000, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1))

# Output Enable pin for SN74AHCT125, active LOW to transmit
oe = Pin(2, Pin.OUT)
oe.high()   # Start in receive mode (Hi-Z buffer)

# AX-12 default ID
DXL_ID = 1

# Build a PING packet
# Format: 0xFF 0xFF ID LENGTH INSTRUCTION CHECKSUM
packet = bytearray([0xFF, 0xFF, DXL_ID, 0x02, 0x01])
checksum = ~(DXL_ID + 2 + 1) & 0xFF
packet.append(checksum)

def send_packet(pkt):
    # Enable transmitter
    oe.low()
    time.sleep_us(20)

    uart.write(pkt)
    uart.flush()

    # Release bus for servo to reply
    time.sleep_us(20)
    oe.high()

def read_status(timeout=30):  # ms
    start = time.ticks_ms()
    data = bytearray()

    while time.ticks_diff(time.ticks_ms(), start) < timeout:
        if uart.any():
            data.extend(uart.read())
        time.sleep_ms(1)

    return data

print("Sending PING to AX-12...")

send_packet(packet)
response = read_status()

if response:
    print("Received response:", [hex(b) for b in response])
else:
    print("No response received.")