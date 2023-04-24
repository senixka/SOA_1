import os, struct, socket


MULTICAST_PORT = int(os.environ.get("MULTICAST_PORT", "5000"))
MULTICAST_GROUP = str(os.environ.get("MULTICAST_GROUP", "224.0.0.1"))

REGULAR_PORT = 2000
REGULAR_ADDR = "0.0.0.0"

REGISTRY = {"NATIVE": ("test_native", 2001),
            "JSON": ("test_json", 2002),
            "PROTOBUF": ("test_protobuf", 2003),
            "MSGPACK": ("test_msgpack", 2004),
            "YAML": ("test_yaml", 2005),
            "XML": ("test_xml", 2006),
            "AVRO": ("test_avro", 2007),
            "all": (MULTICAST_GROUP, MULTICAST_PORT)}


def MainLoop():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((REGULAR_ADDR, REGULAR_PORT))

    while True:
        data, address = sock.recvfrom(4096)
        request = data.decode().strip()
                
        if not request.startswith("get_result "):
            sock.sendto(b"Bad request\n", address)
            continue
        
        if len(request.split()) != 2 or (request.split()[-1] not in REGISTRY.keys()):
            sock.sendto(b"Bad type in get_result request\n", address)
            continue

        format_type = request.split()[-1]
        dest_address = REGISTRY[format_type]

        if format_type != "all":
            inner_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            inner_sock.sendto(b"get_result", dest_address)
            result, _ = inner_sock.recvfrom(4096)
            
            sock.sendto(result, address)
        else:
            inner_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            inner_sock.settimeout(5)
            inner_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("b", 1))
            inner_sock.sendto(b"get", dest_address)

            for i in range(len(REGISTRY) - 1):
                try:
                    data, _ = inner_sock.recvfrom(4096)
                except socket.timeout:
                    break
                else:
                    sock.sendto(data, address)


if __name__ == "__main__":
    MainLoop()
