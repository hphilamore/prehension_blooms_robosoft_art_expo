from ax12 import AX12
import time
import machine


led = machine.Pin('LED', machine.Pin.OUT)

# Pico pins:
# UART0 TX = GP0
# UART0 RX = GP1
# Half-duplex direction control = GP2

ax = AX12(
    uart_id=0,
    tx_pin=0,
    rx_pin=1,
    direction_pin=2,
    baudrate=1000000
)

SERVO_ID = 0

print("Pinging servo...")
resp = ax.ping(SERVO_ID)
print('Ping response:', resp)

print("Turning LED on...")
led.toggle()
ax.set_led(SERVO_ID, True)
time.sleep(1)


print("Turning LED off...")
led.toggle()
ax.set_led(SERVO_ID, False)
time.sleep(1)
# 
# print("Moving to 300...")
# ax.move(SERVO_ID, 300)
# time.sleep(2)
# 
# print("Moving to 700...")
# ax.move(SERVO_ID, 700)
# time.sleep(2)
# 
# print("Done.")


print("Scanning for AX-12 servos...")

found = []

for sid in range(0, 254):
    resp = ax.ping(sid)
    if resp:
        print("Found servo at ID:", sid, " raw response:", resp)
        found.append(sid)
        time.sleep(0.05)

if not found:
    print("No servos detected.")
else:
    print("Servos found:", found)

