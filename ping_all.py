from machine import UART, Pin
import time

uart = UART(0, baudrate=1000000, bits=8, parity=None, stop=1,
             tx=Pin(0), rx=Pin(1))

oe = Pin(2, Pin.OUT)
oe.high()   # Start in receive mode

def clear_uart():
    while uart.any():
        uart.read()

def send_packet(pkt):
    oe.low()
    time.sleep_us(20)
    uart.write(pkt)
    uart.flush()
    time.sleep_us(20)
    oe.high()

def read_status(timeout=10):
    start = time.ticks_ms()
    buf = bytearray()
    while time.ticks_diff(time.ticks_ms(), start) < timeout:
        if uart.any():
            buf.extend(uart.read())
        time.sleep_us(200)
    return buf

def checksum(b):
    return (~sum(b) & 0xFF)

def ping_id(dxl_id):
    # Build a PING packet for this ID
    body = [dxl_id, 0x02, 0x01]   # ID, LENGTH=2, INSTRUCTION=PING
    cs = checksum(body)
    pkt = bytearray([0xFF, 0xFF] + body + [cs])

    clear_uart()
    send_packet(pkt)
    resp = read_status()

    # A valid response starts with FF FF ID ...
    if len(resp) >= 6 and resp[0] == 0xFF and resp[1] == 0xFF:
        return True, resp
    return False, resp

# print("Scanning all possible AX-12 IDs...")
# 
# found = []
# 
# for i in range(0, 254):  # valid range for AX-series
#     ok, resp = ping_id(i)
#     if ok:
#         print("Found servo at ID:", i, " Response:", [hex(b) for b in resp])
#         found.append(i)
# 
# if not found:
#     print("No servos found.")
# else:
#     print("Scan complete. IDs detected:", found)

ping_id(1)