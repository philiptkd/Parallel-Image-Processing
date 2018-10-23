import tensorflow as tf
from test_graph import TestGraph

output = TestGraph()
init = tf.global_variables_initializer()

cluster = tf.train.ClusterSpec({
    "worker": ["192.168.0.7:2222"],
    "ps": ["192.168.0.4:2222"]
    })

server = tf.train.Server(cluster, job_name="worker", task_index=0)

with tf.Session(server.target) as sess:
    server.join()#blocks until all servers have joined