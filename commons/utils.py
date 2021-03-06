from datetime import timedelta
from dateutil import parser
from flask import jsonify
from numpy import hamming
from scipy.signal import periodogram
from statistics import mean
import datetime


'''
This function receives a packet containing the raw data about a sleep session, the stop time and the daily habit and 
creates a packet that contains the aggregate data about that sleep session
'''
def prepare_packet(record, stop, habit):
    aggregate = dict()
    preview = dict()

    interval = int(parser.parse(stop).timestamp() - parser.parse(record["_id"]).timestamp())

    hours = str(interval//3600)

    minutes = str((interval - eval(hours)*3600)//60)

    aggregate["habit"] = habit

    aggregate["sleep_duration"] = hours + " h " + minutes + " m"

    aggregate["avg_spo2"] = mean(record["spo2"])
    aggregate["plot_spo2"] = aggregate_on_interval(record["spo2"], record["spo2_rate"], 3600)

    preview["avg_spo2"] = aggregate["avg_spo2"]

    aggregate["avg_hr"] = mean(record["hr"])
    aggregate["plot_hr"] = aggregate_on_interval(record["hr"], record["hr_rate"], 3600)

    preview["avg_hr"] = aggregate["avg_hr"]

    aggregate["total_movements"] = sum(record["movements_count"])
    aggregate["plot_movements"] = aggregate_on_interval(record["movements_count"], record["hr_rate"], 3600, sum)

    f, ps = spectral_analysis(record["spo2"], record["spo2_rate"])

    aggregate["spo2_spectra"] = {
        "frequencies": f,
        "spectral_density": ps
    }

    f, ps = spectral_analysis(record["hr"], record["hr_rate"])

    aggregate["hr_spectra"] = {
        "frequencies": f,
        "spectral_density": ps
    }

    oxy_events = []
    if "oxy_events" in record:
        oxy_events = record["oxy_events"]

    dia_events = []
    if "oxy_events" in record:
        dia_events = record["dia_events"]

    apnea_events = aggregate_apnea_events(oxy_events, dia_events)
    avg = 0

    if len(apnea_events) > 0:
        for event in apnea_events:
            avg += event["duration"]
        avg = avg // len(apnea_events)

    aggregate["apnea_events"] = len(apnea_events)
    aggregate["avg_duration"] = avg
    aggregate["plot_apnea_events"] = apnea_events

    preview["apnea_events"] = len(apnea_events)

    return aggregate, preview


'''
This function incapsulates an error message into a JSON packet
'''
def error_message(message):
    return jsonify(status="error", message=message)


'''
This functions aggregates a signal, applying a certain function (default is average) in order to reduce the number of 
samples
'''
def aggregate_on_interval(signal, rate, interval, aggregator=mean):

    if rate >= interval:
        return signal

    spi = interval//rate

    i = 0
    agg_sig = []
    while i < len(signal):
        agg_sig.append(aggregator(signal[i:i+spi]))
        i += spi

    return agg_sig


'''
This function performs the spectral analysis of a signal and returns the spectral density associated to each frequency
'''
def spectral_analysis(signal, rate):

    ham = hamming(len(signal))
    ham_wdw = ham*signal

    f, ps = periodogram(ham_wdw, 1 / rate)

    return list(f), list(ps)


'''
This function aggregates the apnea event, in order to aggregate data from the pulse oximeter and from the accelerometer
on the diaphragm
'''
def aggregate_apnea_events(oxy_events, dia_events):

    ret = []

    oxy_i = 0
    dia_i = 0

    while oxy_i < len(oxy_events) and dia_i < len(dia_events):
        oxy_ev = oxy_events[oxy_i]
        dia_ev = dia_events[dia_i]
        o_time = parser.parse(oxy_ev["time"])
        d_time = parser.parse(dia_ev["time"])

        if o_time <= d_time:
            if o_time + timedelta(seconds=oxy_ev["duration"]) < d_time:
                ret.append({
                    "time": o_time.strftime("%x %X"),
                    "duration": oxy_ev["duration"],
                    "type": "pulseox"
                })

            else:
                tmp_time = datetime.datetime.fromtimestamp((o_time.timestamp() + d_time.timestamp())/2)
                ret.append({
                    "time": tmp_time.strftime("%x %X"),
                    "duration": (oxy_ev["duration"]+dia_ev["duration"])//2,
                    "type": "consensus"
                })
                dia_i += 1

            oxy_i += 1

        else:
            if d_time + timedelta(seconds=dia_ev["duration"]) < o_time:
                ret.append({
                    "time": d_time.strftime("%x %X"),
                    "duration": dia_ev["duration"],
                    "type": "diaphragm"
                })
                oxy_i += 1

            else:
                tmp_time = datetime.datetime.fromtimestamp((o_time.timestamp() + d_time.timestamp()) / 2)
                ret.append({
                    "time": tmp_time.strftime("%x %X"),
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
