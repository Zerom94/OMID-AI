import argparse, socket, json, threading, queue, sys

def scan(q, ip, timeout, results):
    while True:
        try: port = q.get_nowait()
        except queue.Empty: break
        s=socket.socket()
        s.settimeout(timeout)
        try:
            s.connect((ip, port))
            try:
                s.sendall(b'\r\n')
                banner=s.recv(1024).decode(errors='ignore').strip()
            except:
                banner=''
            results.append({'port':port,'banner':banner})
        except:
            pass
        finally:
            s.close()
        q.task_done()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('target')
    p.add_argument('start',type=int)
    p.add_argument('end',type=int)
    args=p.parse_args()
    ip=socket.gethostbyname(args.target)
    q=queue.Queue()
    for pnum in range(args.start, args.end+1):
        q.put(pnum)
    results=[]
    for _ in range(100):
        t=threading.Thread(target=scan,args=(q,ip,0.5,results))
        t.daemon=True
        t.start()
    q.join()
    out={'open_ports':sorted(results,key=lambda x:x['port'])}
    with open('scan_results.json','w') as f:
        json.dump(out,f,indent=2)
if __name__=='__main__':
    main()
