import socket, argparse

def scan(host, port):
    s = socket.socket()
    s.settimeout(0.5)
    try:
        s.connect((host, port))
    except Exception:
        return False
    else:
        s.close()
        return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("host")
    parser.add_argument("-p", "--ports", default="1-1024", help="port range, e.g., 20-80")
    args = parser.parse_args()
    host = args.host
    start, end = map(int, args.ports.split("-"))
    for port in range(start, end + 1):
        if scan(host, port):
            print(f"{port}/tcp open")

if __name__ == "__main__":
    main()
