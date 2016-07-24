import wave
import struct

def wav_source(filename):
    r = wave.open(filename)

    while True:
        frame = r.readframes(1)[0:2]
        if len(frame) < 2:
            break
        value = struct.unpack("<h", frame)[0]

        yield value


def dc_adjustment(source):
    raw_values = []

    for value in source:
        raw_values.append(value)

        if len(raw_values) > 100:
            raw_values = raw_values[-100:]
        recent_min = min(raw_values[-min(len(raw_values), 100):])
        value = value-recent_min

        yield value


def binary(source, threshold):
    for value in source:
        yield value > threshold

def wait_for_sync(source):
    count = 0
    high = False
    high_at = 0

    min_pulse_width = 0.00016
    max_pulse_width = 0.00026

    pulse_count = 0
    last_pulse_at = 0

    for sample in source:
        t = float(count)/48000.0
        if not high and sample:
            #print "High at %s" % t
            high_at = t
            high = True
        elif high and not sample:
            duration = (t-high_at)
            high = False
            #print "%0.6f" % duration

            if duration > min_pulse_width and duration < max_pulse_width \
                and (last_pulse_at == 0 or (t-last_pulse_at < 0.01)):
                    pulse_count += 1
                    last_pulse_at = t
                    #print "Pulse! %0.6f" % t
            else:
                pulse_count = 0
                last_pulse_at = 0

            if pulse_count == 8:
                #print "synced!"
                break

        count += 1

def manchester_decode(source):
    timer = 0
    last_edge = -1
    last_value = False

    pulse_widths = []
    multiples = []
    waiting_for_short = False

    for s in source:
        if last_edge != -1 and (timer-last_edge) > 150:
            break

        timer += 1

        if last_value != s:
            #print "Edge at %s" % timer
            if last_edge != -1:
                w = timer-last_edge
                pulse_widths.append(w)

            last_edge = timer
            last_value = s

    multiples = map(width_multiple, pulse_widths)

    current_bit = False
    bits = []
    i=0
    while i < len(multiples):
        if multiples[i] == 2:
            current_bit = not current_bit
            bits.append(1 if current_bit else 0)
            i+=1
        elif multiples[i] == 1 and multiples[i+1] == 1:
            bits.append(1 if current_bit else 0)
            i+=2
        else:
            break
    s = str(int(''.join(map(str, bits)), 2))
    print s


def width_multiple(w):
    width = 12
    window = 5

    if w > width-window and w < width + window:
        return 1
    elif w > 2*width-window and w < 2*width+window:
        return 2
    else:
        return 0



if __name__ == '__main__':
    analog_source = dc_adjustment(wav_source('2_pulses.wav'))

    source = binary(analog_source, 3000)

    for i in range(4):
        wait_for_sync(source)

        manchester_decode(source)
