from machine import UART, Pin
import time

uart = UART(0, baudrate=1000000, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1))

oe = Pin(2, Pin.OUT)
oe.high()

DXL_ID = 1

# PING packet
packet = bytearray([0xFF, 0xFF, DXL_ID, 0x02, 0x01])
packet.append(~(DXL_ID + 2 + 1) & 0xFF)

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

def read_status(timeout=20):
    start = time.ticks_ms()
    buf = bytearray()

    while time.ticks_diff(time.ticks_ms(), start) < timeout:
        if uart.any():
            buf.extend(uart.read())
        time.sleep_us(200)

    return buf

print("Clearing UART…")
clear_uart()

print("Sending PING…")
send_packet(packet)

resp = read_status()

print("Response:", [hex(b) for b in resp])