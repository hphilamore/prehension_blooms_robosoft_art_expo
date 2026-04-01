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


def move_to_angle(id, angle_deg):
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
    

def write_speed(id, speed):
    speed = max(0, min(1023, speed))
    low = speed & 0xFF
    high = (speed >> 8) & 0xFF
    write_data(id, 0x20, [low, high])
    
def read_position(id):
    # Build READ_DATA packet for address 0x24 (2 bytes)
    body = [id, 4, 2, 0x24, 2]
    pkt = bytearray([0xFF, 0xFF] + body + [checksum(body)])

    clear_uart()
    send_packet(pkt)
    resp = read_status()

    # Scan for valid status packets
    for i in range(len(resp) - 7):
        if resp[i] == 0xFF and resp[i+1] == 0xFF and resp[i+2] == id:
            length = resp[i+3]
            error  = resp[i+4]

            # Ignore echo packet (its "error" byte is READ_DATA=0x02)
            if error != 0:
                continue

            # Now it's guaranteed to be a valid status packet
            pos_l = resp[i+5]
            pos_h = resp[i+6]
            return pos_l + (pos_h << 8)

    return None

def wait_until_reached(id, target_angle_deg, tolerance_deg=3):
    # Convert target angle to AX-12 position units
    target_pos = int((target_angle_deg / 300) * 1023)
    tol = int((tolerance_deg / 300) * 1023)

    while True:
        cur = read_position(id)
        print(cur)
        if cur is not None:
            if abs(cur - target_pos) < tol:
                print("Reached:", cur)
                return cur
        time.sleep_ms(20)


def read_position_debug(id):
    body = [id, 4, 2, 0x24, 2]
    pkt = bytearray([0xFF, 0xFF] + body + [checksum(body)])

    clear_uart()
    send_packet(pkt)
    resp = read_status()

    print("RAW:", [hex(b) for b in resp])
    return resp


write_speed(1,  200)
write_speed(2,  200)


id = 1
angle = 300
move_to_angle(id, angle)  
wait_until_reached(id, angle)

id = 2
angle = 150
move_to_angle(id, anlge)  
wait_until_reached(id, angle)

write_speed(1,  100)
write_speed(2,  100)

id = 1
angle = 150
move_to_angle(id, angle)  
wait_until_reached(id, angle)

id = 2
angle = 300
move_to_angle(id, anlge)  
wait_until_reached(id, angle)




# # Move to 150 degrees (mid-point)
# ang = 150
# move_to_angle(ang, 1)
# time.sleep(5)
# move_to_angle(ang, 2)
# time.sleep(1)


