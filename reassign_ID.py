from machine import UART, Pin
import time

# -----------------------------
# UART + Pins
# -----------------------------
uart = UART(
    0,
    baudrate=1000000,   # AX-12 default
    bits=8,
    parity=None,
    stop=1,
    tx=Pin(0),          # Pico TX → SN74AHCT125 1A
    rx=Pin(1)           # Pico RX ← DATA (via 1k resistor)
)

oe = Pin(2, Pin.OUT)    # Output Enable for SN74AHCT125
oe.high()               # Start in receive mode


# -----------------------------
# Utility functions
# -----------------------------
def clear_uart():
    """Remove leftover bytes from UART buffer."""
    while uart.any():
        uart.read()


def send_packet(pkt):
    """Send Dynamixel packet and switch bus directions."""
    oe.low()            # enable buffer → TX mode
    time.sleep_us(20)

    uart.write(pkt)
    uart.flush()

    time.sleep_us(20)
    oe.high()           # disable buffer → RX mode


def read_status(timeout_ms=30):
    """Read any response bytes from the servo."""
    start = time.ticks_ms()
    buf = bytearray()

    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        if uart.any():
            buf.extend(uart.read())
        time.sleep_us(200)

    return buf


def checksum(b):
    """Dynamixel checksum."""
    return (~sum(b) & 0xFF)


def ping(id):
    """Send PING and return response bytes."""
    body = [id, 0x02, 0x01]     # ID, LENGTH=2, INST=PING
    pkt = bytearray([0xFF, 0xFF] + body + [checksum(body)])

    clear_uart()
    send_packet(pkt)
    resp = read_status()

    print("PING response:", [hex(x) for x in resp])
    return resp


# -----------------------------
# Write data instruction
# -----------------------------
def write_data(id, address, params):
    """Generic WRITE_DATA instruction."""
    # body = [id, 2 + len(params), 0x03, address] + params
    
    # packet length = instruction length + address length + length params
    length = 2 + 1 + len(params)   
    body = [id, length, 0x03, address] + params
    
    pkt = bytearray([0xFF, 0xFF] + body + [checksum(body)])

    print("SEND:", [hex(x) for x in pkt])

    clear_uart()
    send_packet(pkt)
    resp = read_status()

    print("RESPONSE:", [hex(x) for x in resp])
    return resp


# -----------------------------
# Servo control helpers
# -----------------------------
def set_torque(id, enable):
    """Enable/disable torque."""
    print("\n--- Setting torque =", enable, "---")
    return write_data(id, 0x18, [1 if enable else 0])


def change_id(old_id, new_id):
    """Full safe ID change procedure."""
    print("\n===== ID CHANGE START =====")

    print("Disabling torque...")
    set_torque(old_id, False)
    time.sleep_ms(50)

    print("\nWriting new ID =", new_id)
    write_data(old_id, 0x03, [new_id])
    time.sleep_ms(50)

    print("\nTesting new ID...")
    ping(new_id)

    print("\nTesting old ID (should be silent)...")
    ping(old_id)

    print("\n===== ID CHANGE COMPLETE =====")


# -----------------------------
# RUN THE ID CHANGE HERE
# -----------------------------
CURRENT_ID = 1      # change this if needed
NEW_ID     = 2      # ID you want to assign

change_id(CURRENT_ID, NEW_ID)
# ping(1)