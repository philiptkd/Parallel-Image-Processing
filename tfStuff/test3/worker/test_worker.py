import tensorflow as tf
import dist_googlenet_worker as dg

cluster = tf.train.ClusterSpec({
    "worker": ["192.168.0.7:2222"],
    "ps": ["192.168.0.4:2222"]
    })
server = tf.train.Server(cluster, job_name="worker", task_index=0)

dg.build_graph(server)