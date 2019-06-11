from datetime import timedelta
from dateutil.parser import parser
from flask import jsonify
from numpy import hamming
from scipy.signal import periodogram


def error_message(message):
    return jsonify(status="error", message=message)


def interval_avg(signal, rate, interval):

    if rate >= interval:
        return signal

    spi = interval//rate
    approx_len = len(signal) - len(signal) % spi

    i = 0
    agg_sig = []
    while i < approx_len:
        agg_sig.append(signal[i:i+spi])
        i += spi

    return agg_sig


def spectral_analysis(signal, rate):

    ham = hamming(len(signal))
    ham_wdw = ham*signal

    return periodogram(ham_wdw, 1/rate)


def aggregate_apnea_events(oxy_events, dia_events):

    ret = []

    oxy_i = 0
    dia_i = 0

    while oxy_i < len(oxy_events) and dia_i < len(dia_events):
        oxy_ev = oxy_events[oxy_i]
        dia_ev = dia_events[dia_i]
        o_time = parser().parse(oxy_ev["time"])
        d_time = parser().parse(oxy_ev["time"])

        if o_time <= d_time:
            if o_time + timedelta(seconds=oxy_ev["duration"]) < d_time:
                ret.append({
                    "time": o_time.strftime("%x %X"),
                    "duration": oxy_ev["duration"],
                    "type": "pulseox"
                })

            else:
                ret.append({
                    "time": ((o_time+d_time)/2).strftime("%x %X"),
                    "duration": (oxy_ev["duration"]+dia_ev["duration"])//2,
                    "type": "consensus"
                })

            oxy_i += 1

        else:
            if d_time + timedelta(seconds=dia_ev["duration"]) < o_time:
                ret.append({
                    "time": d_time.strftime("%x %X"),
                    "duration": dia_ev["duration"],
                    "type": "diaphragm"
                })

            else:
                ret.append({
                    "time": ((o_time + d_time) / 2).strftime("%x %X"),
                    "duration": (oxy_ev["duration"] + dia_ev["duration"]) // 2,
                    "type": "consensus"
                })

            dia_i += 1

    while dia_i < len(dia_events):
        ret.append({
            "time": d_time.strftime("%x %X"),
            "duration": dia_ev["duration"],
            "type": "diaphragm"
        })
        dia_i += 1

    while oxy_i < len(oxy_events):
        ret.append({
            "time": o_time.strftime("%x %X"),
            "duration": oxy_ev["duration"],
            "type": "pulseox"
        })
        oxy_i += 1

    return ret
