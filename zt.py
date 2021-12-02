"""Example low-level socket usage"""

import time
import sys
import socket
import libzt
import threading


def print_usage():
    """print help"""
    print(
        "\nUsage: <server|client> <storage_path> <net_id> <remote_ip> <remote_port>\n"
    )
    print("Ex: python3 example.py server . 0123456789abcdef 8080 22")
    print("Ex: python3 example.py client . 0123456789abcdef 192.168.22.1 8080 1234\n")
    sys.exit(0)


#
# (Optional) Event handler
#
def on_zerotier_event(event_code, id):
    if event_code == libzt.ZTS_EVENT_NODE_ONLINE:
        print("ZTS_EVENT_NODE_ONLINE (" + str(event_code) + ") : " + hex(id))
    if event_code == libzt.ZTS_EVENT_NODE_OFFLINE:
        print("ZTS_EVENT_NODE_OFFLINE (" + str(event_code) + ") : " + hex(id))
    if event_code == libzt.ZTS_EVENT_NETWORK_READY_IP4:
        print("ZTS_EVENT_NETWORK_READY_IP4 (" + str(event_code) + ") : " + hex(id))
    if event_code == libzt.ZTS_EVENT_NETWORK_READY_IP6:
        print("ZTS_EVENT_NETWORK_READY_IP6 (" + str(event_code) + ") : " + hex(id))
    if event_code == libzt.ZTS_EVENT_PEER_DIRECT:
        print("ZTS_EVENT_PEER_DIRECT (" + str(event_code) + ") : " + hex(id))
    if event_code == libzt.ZTS_EVENT_PEER_RELAY:
        print("ZTS_EVENT_PEER_RELAY (" + str(event_code) + ") : " + hex(id))

def forwarding(src, dst):
    while True:
        try:
            buffer = src.recv(0x400)
            recvbyte = len(buffer)
        except:
            print("recv error")
            break
        if recvbyte == 0:
            print("[-] No data received! Breaking...")
            break
        try:
            sentbyte = dst.send(buffer)
        except:
            print("send error")
            break
        print("recv: ", recvbyte)
        print("sent: ", sentbyte)

def ztnet(net_id, storage_path):
    print("Starting ZeroTier...")

    n = libzt.ZeroTierNode()
    n.init_set_event_handler(on_zerotier_event)  # Optional
    n.init_from_storage(storage_path)  # Optional
    n.init_set_port(9994)  # Optional
    n.node_start()

    print("Waiting for node to come online...")
    while not n.node_is_online():
        time.sleep(1)
    print("Joining network:", hex(net_id))
    n.net_join(net_id)
    while not n.net_transport_is_ready(net_id):
        time.sleep(1)
    print("Joined network")

    print("addr = ", n.addr_get_ipv4(net_id))
    return n
#
# Main
#
def main():
    mode = None  # client|server
    storage_path = "."  # Where identity files are stored
    net_id = 0  # Network to join
    remote_ip = None  # ZeroTier IP of remote node
    remote_port = 8080  # ZeroTier port your app logic may use


    if sys.argv[1] == "server" and len(sys.argv) == 6:
        mode = sys.argv[1]
        storage_path = sys.argv[2]
        net_id = int(sys.argv[3], 16)
        remote_port = int(sys.argv[4])
        local_port = int(sys.argv[5])
    if sys.argv[1] == "client" and len(sys.argv) == 7:
        mode = sys.argv[1]
        storage_path = sys.argv[2]
        net_id = int(sys.argv[3], 16)
        remote_ip = sys.argv[4]
        remote_port = int(sys.argv[5])
        local_port = int(sys.argv[6])
    if mode is None:
        print_usage()
    print("mode         = ", mode)
    print("storage_path = ", storage_path)
    print("net_id       = ", net_id)
    print("remote_ip    = ", remote_ip)
    print("remote_port  = ", remote_port)

    
    #
    # Example server
    #
    if mode == "server":
        n = ztnet(net_id=net_id, storage_path=storage_path)
        while 1:
            try:
                serv = libzt.socket(libzt.ZTS_AF_INET, libzt.ZTS_SOCK_STREAM, 0)
                serv.setsockopt(libzt.ZTS_SOL_SOCKET, libzt.ZTS_SO_REUSEADDR, 1)
                serv.bind(("0.0.0.0", remote_port))
                serv.listen(5)
                print("Waiting for connection")
                conn, addr = serv.accept()
                print("Accepted connection from: ", addr)
            except Exception as ex:
                print("Conection failed:", ex)
                print("Cannot start server")
                continue

            try:        
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
                client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                client.connect(("127.0.0.1", local_port))
            except Exception as ex:
                print("Conection failed:", ex)
                print("Cannot start client")
                continue

            s = threading.Thread(target=forwarding, args=(
                conn, client))
            r = threading.Thread(target=forwarding, args=(
                client, conn))
            s.start()
            r.start()
            
            while 1:
                if not s.is_alive():
                    print("Forwarding down")
                    break
                if not r.is_alive():
                    print("Backwording down")
                    break
            
            try:
                serv.shutdown(libzt.ZTS_SHUT_RDWR)
                serv.close()
            except Exception as ex:
                print("Close serv error", ex)
            
            try:
                client.shutdown(socket.SHUT_RDWR)
                client.close()
            except Exception as ex:
                print("Close client error", ex)

    #
    # Example client
    #
    if mode == "client":
        n = ztnet(net_id=net_id, storage_path=storage_path)
        while 1:
            try:
                client = libzt.socket(libzt.ZTS_AF_INET, libzt.ZTS_SOCK_STREAM, 0)
                client.setsockopt(libzt.ZTS_SOL_SOCKET, libzt.ZTS_SO_REUSEADDR, 1)
                client.connect((remote_ip, remote_port))
            except Exception as ex:
                print("Conection failed:", ex)
                continue
                
            try:
                serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
                serv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                serv.bind(("127.0.0.1", local_port))
                serv.listen(5)
                conn, addr = serv.accept()
            except Exception as ex:
                print("Conection failed:", ex)
                continue
            
            s = threading.Thread(target=forwarding, args=(
                conn, client))
            r = threading.Thread(target=forwarding, args=(
                client, conn))
            s.start()
            r.start()
            
            while 1:
                if not s.is_alive():
                    print("Forwarding down")
                    break
                if not r.is_alive():
                    print("Backwording down")
                    break
            
            try:
                client.shutdown(libzt.ZTS_SHUT_RDWR)
                client.close()
            except Exception as ex:
                print("Close serv error", ex)
            
            try:
                serv.shutdown(socket.SHUT_RDWR)
                serv.close()
            except Exception as ex:
                print("Close client error", ex)

if __name__ == "__main__":
    main()
