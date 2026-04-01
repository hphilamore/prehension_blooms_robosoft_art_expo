"""
AX‑12 MicroPython library for the Raspberry Pi Pico W using wiring:

UART0 TX = GP0

UART0 RX = GP1 (via 1 kΩ)

SN74AHCT125 1OE = GP2

Dynamixel default baud = 1,000,000 bps

"""
from machine import UART, Pin
import time

# ------------------------------------------------------------
# Hardware configuration (modify if needed)
# ------------------------------------------------------------
UART_ID = 0
TX_PIN = 0
RX_PIN = 1
OE_PIN = 2
BAUD = 1000000

# ------------------------------------------------------------
# Initialise UART + direction control (OE)
# ------------------------------------------------------------
uart = UART(
    UART_ID,
    baudrate=BAUD,
    bits=8,
    parity=None,
    stop=1,
    tx=Pin(TX_PIN),
    rx=Pin(RX_PIN)
)

oe = Pin(OE_PIN, Pin.OUT)
oe.high()  # Start in receive mode (high-Z from level shifter)

# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------
def clear_uart():
    """Flush any unread bytes."""
    while uart.any():
        uart.read()

def checksum(values):
    """Return Dynamixel checksum."""
    return (~sum(values) & 0xFF)

def send_packet(packet):
    """Send a packet, controlling buffer direction."""
    oe.low()                # TX mode
    time.sleep_us(20)
    uart.write(packet)
    uart.flush()
    time.sleep_us(20)
    oe.high()               # RX mode

def read_status(timeout_ms=20):
    """Read servo response, return raw bytes."""
    start = time.ticks_ms()
    rx = bytearray()
    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        if uart.any():
            rx.extend(uart.read())
        time.sleep_us(200)
    return rx

# ------------------------------------------------------------
# Protocol-level instructions
# ------------------------------------------------------------
def ping(id):
    """Send a PING instruction and return the raw response."""
    body = [id, 0x02, 0x01]  # ID, LENGTH=2, INST=PING
    pkt = bytearray([0xFF, 0xFF] + body + [checksum(body)])
    
    clear_uart()
    send_packet(pkt)
    resp = read_status()

    return resp

def write_data(id, address, params):
    """
    Generic WRITE_DATA instruction.
    LENGTH = number_of_params + 2 (instruction + address)
    """
    length = len(params) + 2
    body = [id, length, 0x03, address] + params
    packet = bytearray([0xFF, 0xFF] + body + [checksum(body)])

    clear_uart()
    send_packet(packet)
    return read_status()

def read_data(id, address, size):
    """Perform a READ_DATA instruction."""
    body = [id, 4, 0x02, address, size]  # LENGTH=4 (inst + addr + size)
    packet = bytearray([0xFF, 0xFF] + body + [checksum(body)])

    clear_uart()
    send_packet(packet)
    return read_status()

# ------------------------------------------------------------
# High-level servo commands
# ------------------------------------------------------------
def read_position(id):
    """Return 0–1023 current position, or None if invalid."""
    resp = read_data(id, 0x24, 2)
    if len(resp) >= 7:
        pos_l = resp[5]
        pos_h = resp[6]
        return pos_l + (pos_h << 8)
    return None

def set_speed(id, speed):
    """Set movement speed (0–1023)."""
    speed = max(0, min(1023, speed))
    low = speed & 0xFF
    high = (speed >> 8) & 0xFF
    return write_data(id, 0x20, [low, high])

def move_to_angle(id, angle_deg, speed=200):
    """
    Move servo to a given angle (0–300 degrees) 
    at the specified speed (0–1023).
    """
    # Convert angle to AX12 position units
    pos = int((angle_deg / 300) * 1023)
    pos = max(0, min(1023, pos))

    # Set speed first
    set_speed(id, speed)

    # Send goal position
    low = pos & 0xFF
    high = (pos >> 8) & 0xFF
    return write_data(id, 0x1E, [low, high])

def wait_until_reached(id, target_deg, tolerance=10):
    """
    Block until servo reaches target position.
    Useful for synchronous motion.
    """
    target = int((target_deg / 300) * 1023)
    while True:
        pos = read_position(id)
        if pos is None:
            continue
        if abs(pos - target) < tolerance:
            return pos
        time.sleep_ms(20)