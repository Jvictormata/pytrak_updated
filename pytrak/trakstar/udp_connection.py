""" A lan connect class using udp
"""

__author__ = "Oliver Lindemann <oliver@expyriment.org>"
__version__ = "0.1"

import os
from time import sleep, time
import socket

if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(),
                                            0x8915, struct.pack('256s',
                                                                ifname[:15]))[20:24])


def get_lan_ip():
    # code bas on http://stackoverflow.com/questions/11735821/python-get-localhost-ip
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
        ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip


class UDPConnection(object):
    # todo: document the usage "connecting" "unconecting"
    COMMAND_CHAR = "$"
    CONNECT = COMMAND_CHAR + "connect"
    UNCONNECT = COMMAND_CHAR + "unconnect"
    COMMAND_REPLY = COMMAND_CHAR + "ok"
    PING = COMMAND_CHAR + "ping"

    def __init__(self, udp_port=5005):
        self.udp_port = udp_port

        self.socket = socket.socket(socket.AF_INET,  # Internet
                                    socket.SOCK_DGRAM)  # UDP
        self.my_ip = get_lan_ip()
        self.socket.bind((self.my_ip, self.udp_port))
        self.socket.setblocking(False)
        self.peer_ip = None

    def __str__(self):
        return "ip: {0} (port: {1}); peer: {2}".format(self.my_ip,
                                                       self.udp_port, self.peer_ip)

    def poll(self):
        """returns data or None if no data found
        process also commands

        if send is unkown input is ignored
        """

        try:
            data, sender = self.socket.recvfrom(1024)
        except:
            return None

        # process data
        if data == UDPConnection.CONNECT:
            #connection request
            self.peer_ip = sender[0]
            if not self.send(UDPConnection.COMMAND_REPLY):
                self.peer_ip = None
        elif sender[0] != self.peer_ip:
            return None  # ignore data
        elif data == UDPConnection.PING:
            self.send(UDPConnection.COMMAND_REPLY)
        elif data == self.UNCONNECT:
            self.unconnect_peer()
        return data

    def send(self, data, timeout=1.0):
        """returns if problems or not
        timeout in seconds (default = 1.0)
        return False if failed to send

        """
        if self.peer_ip is None:
            return False
        start = time()
        while time() - start < timeout:
            try:
                self.socket.sendto(data, (self.peer_ip, self.udp_port))
                # print "send:", data, self.peer_ip
                return True
            except:
                sleep(0.001)  # wait 1 ms
        return False

    def connect_peer(self, peer_ip, timeout=1):
        self.unconnect_peer()
        self.peer_ip = peer_ip
        if self.send(UDPConnection.CONNECT, timeout=timeout) and \
                self.wait_input(UDPConnection.COMMAND_REPLY, duration=timeout):
            return True
        self.peer_ip = None
        return False

    def wait_input(self, input_string, duration=1):
        """poll the connection and waits for a specific input"""
        start = time()
        while time() - start < duration:
            in_ = self.poll()
            if in_ == UDPConnection.COMMAND_REPLY:
                return True
        return False

    def unconnect_peer(self, timeout=1.0):
        self.send(UDPConnection.UNCONNECT)
        self.peer_ip = None

    @property
    def is_connected(self):
        return self.peer_ip is not None

    def ping(self, timeout=0.5):
        """returns boolean if suceeded and ping time"""
        if self.peer_ip == None:
            return (False, None)
        start = time()
        if self.send(UDPConnection.PING, timeout=timeout) and \
                self.wait_input(UDPConnection.COMMAND_REPLY, duration=timeout):
            return (True, ((time() - start) * 1000))
        return (False, None)

    def clear_receive_buffer(self):
        data = ""
        while data is not None:
            data = self.poll()

    def poll_last_data(self):
        """polls all data and returns only the last one
        return None if not data found"""
        rtn = None
        tmp = self.poll()
        while tmp is not None:
            rtn = tmp
            tmp = self.poll()
        return rtn
