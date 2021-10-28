from machine import Pin
from rp2 import asm_pio
from time import sleep


 
def main():
    """Mainloop is doing nothing.
    System is entirely driven by events."""
    while True:
        try:
            sleep(1)
        except:
            break

start_bits = 0b101000000000000000000000000
toogle_bit = 0b100000000000000000000000
toogle_bit_mask = 0b110000000000000000000000
address_bits = 0b1010011001000000000000
commands = [
    0b101010101010,
    0b101010101001,
    0b101010100110,
    0b101010100101,
    0b101010011010,
    0b101010011001,
    0b101010010110,
    0b101010010101,
    0b101001101010,
    0b101001101001
    ]
 
buttons = {
    2094078:0,
    4188156:1,
    4184058:2,
    4175862:3,
    4159470:4,
    4126686:5,
    4061118:6,
    3929982:7,
    3667710:8,
    3143166:9
}
 

def make_msg(cmd):
    'Creating message'
    global toogle_bit
    msg = start_bits | toogle_bit
    msg = msg | address_bits
    msg = msg | commands[cmd]
    # Invert toogle bit (used by receiver to spot dropped messages)
    toogle_bit = toogle_bit ^ toogle_bit_mask
    return msg
 

@asm_pio()
def parallel_read():
    'Reading button states and calling IRQ from state machine.'
    label('loop')
    nop() [31]
    nop() [31]
    mov(isr, 0)
    in_(pins, 11)
    mov(x, isr)
    jmp(x_not_y, 'event')
    jmp('loop')
    label('event')
    mov(y, isr)
    push()
    irq(block, 0)
    jmp('loop')
    

@asm_pio(out_init=rp2.PIO.OUT_LOW, set_init=rp2.PIO.OUT_LOW)
def send():
    'State machine responsible for sending messages.'
    wrap_target()
    pull()
    # Regardless of the length of the sent message
    # the retrieved word is always 32 bits long
    # the remaining bits precede the message and are zeros
    set(x, 31) 
    label('bitloop')
    out(pins, 1)
    jmp(x_dec, 'bitloop')
    set(pins, 0)
    wrap()
 

def parallel_read_handler(sm):
    'IRQ called when button state is changed'
    res = sm.get()
    # Necessary condition not to react to button release
    if res in buttons: 
        print('button', buttons[res])
        sm1.put(make_msg(buttons[res]))
 
for i in range(11):
    Pin(2+i, Pin.IN, Pin.PULL_UP)
 
# Initialize state machines
sm0 = rp2.StateMachine(0, parallel_read, freq = 100, in_base=Pin(2, Pin.IN))
sm0.irq(parallel_read_handler)
sm0.active(1)
 
sm1 = rp2.StateMachine(1, send, freq = 76_000, out_base=Pin(28), set_base=Pin(28))
sm1.active(1)

main()

sm0.active(0)
sm1.active(0)