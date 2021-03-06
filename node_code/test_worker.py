import configparser
import tensorflow as tf
import socket
import dist_googlenet_worker as dg # for calling this file as the entry point, from the node_code directory

# distribute this code exactly to all workers
# functionality depends on the jobs dictionary being exactly the same
def main():
    config = configparser.ConfigParser()
    config.read("./ps_worker.ini")
    workers_listing = []
    ps_listing = []

    for worker in config["IP Listing"]["worker"].split(", "):
        worker = str(worker) + ":2222"
        workers_listing.append(worker)

    for ps in [config["IP Listing"]["ps"]]:
        ps = str(ps) + ":2222"
        ps_listing.append(ps)

    jobs = { "worker" : workers_listing,
             "ps" : ps_listing
    }
    cluster = tf.train.ClusterSpec(jobs)

    my_ip = get_ip()
    task = jobs["worker"].index(my_ip+':2222')

    dg.build_graph(cluster, task)

# from https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

main()
