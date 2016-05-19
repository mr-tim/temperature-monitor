import struct
import socket


def signals():
    max_amplitude = 0
    min_amplitude = 0

    index = 0
    raw_values = []

    min_signal = 5000
    high = False
    high_at = 0
    first_high = 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 7355))

    b = ''

    while True:
        # 48khz 16 bit signed, le (S16LE)
        data, addr = sock.recvfrom(1024)

        b = b+data

        while len(b) > 2:
            value = struct.unpack("<h", b[0:2])[0]
            b = b[2:]

            #print repr(b), "=>", value
            max_amplitude = max(max_amplitude, value)
            min_amplitude = min(min_amplitude, value)
            raw_values.append(value)
            if len(raw_values) > 100:
                raw_values = raw_values[-100:]
            recent_min = min(raw_values[-min(len(raw_values), 100):])
            value = value-recent_min
            if not high and value > min_signal:
                high = True
                if first_high == 0:
                    first_high = index
                high_at = index - first_high
                #print "High at", high_at
            elif high and value < min_signal:
                high = False
                #print "Low at", index-first_high, "(", (index-first_high-high_at), ")"
                yield (high_at, index-first_high)

            index += 1

sync_pulses = []
previous_end = -1
bits = [1]
for signal in signals():
    start, end = (signal)
    pulse_length = end-start
    if (previous_end != -1 and previous_end < start-50):
        if len(bits) == 63:
            bits.append(0)
        print "0x%x" % int(''.join(map(str, bits)), 2), bits, len(bits)
        sync_pulses = []
        bits = [1]
        previous_end = -1

    if len(sync_pulses) < 8 and pulse_length < 13 and pulse_length > 5:
        sync_pulses.append(signal)
        if len(sync_pulses) == 8:
            pulse_width = sum(map(lambda x: x[1]-x[0], sync_pulses))/8
    elif len(sync_pulses) == 8:
        if (pulse_length > 15):
            bits.append(0 if bits[-1] == 1 else 1)
        else:
            bits.append(bits[-1])
        previous_end = end
