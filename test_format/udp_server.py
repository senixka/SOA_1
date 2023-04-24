import os, struct, socket
from threading import Thread
from tester import Test


MULTICAST_PORT = int(os.environ.get("MULTICAST_PORT", "5000"))
MULTICAST_GROUP = str(os.environ.get("MULTICAST_GROUP", "224.0.0.1"))

REGULAR_PORT= int(os.environ.get("REGULAR_PORT", "2001"))
REGULAR_ADDR = "0.0.0.0"

TEST_TYPE = str(os.environ.get("FORMAT_TYPE", "NATIVE"))


def ListenMulticast():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((MULTICAST_GROUP, MULTICAST_PORT))

    mreq = struct.pack("4sL", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        _, address = sock.recvfrom(4096)
        sock.sendto(Test(TEST_TYPE).encode(), address)


def ListenRegular():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((REGULAR_ADDR, REGULAR_PORT))

    while True:
        _, address = sock.recvfrom(4096)
        sock.sendto(Test(TEST_TYPE).encode(), address)


if __name__ == "__main__":
    t1, t2 = Thread(target=ListenRegular), Thread(target=ListenMulticast)
    t1.start(), t2.start()
    t1.join(), t2.join()
