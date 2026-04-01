from machine import UART, Pin
import time

# UART for Dynamixel: 1 Mbps
uart = UART(0, baudrate=1000000, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1))

# Output Enable pin for SN74AHCT125 (active LOW to transmit)
oe = Pin(2, Pin.OUT)
oe.high()  # start in receive mode

DXL_ID = 2

def clear_uart():
    while uart.any():
        uart.read()

def send_packet(packet):
    oe.low()             # enable transmitter
    time.sleep_us(20)
    uart.write(packet)
    uart.flush()
    time.sleep_us(20)
    oe.high()            # release bus

def read_status(timeout=20):
    start = time.ticks_ms()
    buf = bytearray()

    while time.ticks_diff(time.ticks_ms(), start) < timeout:
        if uart.any():
            buf.extend(uart.read())
        time.sleep_us(200)

    return buf

def checksum(data_bytes):
    return (~sum(data_bytes) & 0xFF)

def move_to_angle(angle_deg, id=DXL_ID):
    # Convert angle in degrees → Dynamixel 0–1023 range
    pos = int((angle_deg / 300) * 1023)
    pos = max(0, min(1023, pos))

    low = pos & 0xFF
    high = (pos >> 8) & 0xFF

    # Build Dynamixel WRITE_DATA packet:
    # FF FF ID LENGTH INST ADDR PARAMS CHECKSUM
    body = [id, 5, 3, 0x1E, low, high]
    csum = checksum(body)

    packet = bytearray([0xFF, 0xFF] + body + [csum])

    clear_uart()
    send_packet(packet)
    resp = read_status()

    print("Sent angle:", angle_deg, "deg → pos", pos)
    print("Status response:", [hex(b) for b in resp])




# Move to 150 degrees (mid-point)
ang = 150
# move_to_angle(ang, 1)
# time.sleep(5)
move_to_angle(ang, 2)
time.sleep(1)

# Move to 150 degrees (mid-point)
ang = 300
# move_to_angle(ang, 1)
# time.sleep(5)
move_to_angle(ang, 2)
time.sleep(5)

# # Move to 00 degrees (mid-point)
# ang = 0
# move_to_angle(ang, 2)
# time.sleep(1)
# move_to_angle(ang, 1)

# Move to 150 degrees (mid-point)
ang = 150
# move_to_angle(ang, 1)
# time.sleep(1)
move_to_angle(ang, 2)
