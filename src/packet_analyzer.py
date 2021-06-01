from scapy.all import *

def read_file(path):
    a=rdpcap(path)
    offset = a[0].time
    for p in a:
        print(p.time - offset)
        print(p['IP'].src)