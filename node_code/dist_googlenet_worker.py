from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import numpy as np
import os
import tensorflow as tf
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime

try:
    import urllib2 as urllib
except ImportError:
    import urllib.request as urllib

import sys
sys.path.append("../models/research/slim/")

from datasets import imagenet
from datasets import dataset_utils
from nets import inception
from preprocessing import inception_preprocessing

from tensorflow.contrib import slim

def build_graph(cluster, task):
    num_workers = cluster.num_tasks('worker')
    image_size = inception.inception_v1_dist.default_image_size
    shared_image_shape = np.array([1, image_size, image_size, 3])
    
    # shared done list, ready list, and shared image 
    with tf.device("/job:ps/task:0"):
        done_list = tf.get_variable("done_list", [num_workers+1], tf.int32, tf.zeros_initializer)
        ready_list = tf.get_variable("ready_list", [num_workers], tf.int32, tf.zeros_initializer)
    with tf.device("/job:worker/task:0"): 
        shared_image = tf.get_variable("shared_image", shared_image_shape, tf.float32)

    server = tf.train.Server(cluster, job_name='worker', task_index=task)
    sess = tf.Session(target=server.target)

    # build the graph
    with slim.arg_scope(inception.inception_v1_dist_arg_scope()):
        logits, _ = inception.inception_v1_dist(shared_image, num_workers, num_classes=1001, is_training=False, reuse=tf.AUTO_REUSE)
        probabilities = tf.nn.softmax(logits)
        
    # wait until all variables are initialized
    print("waiting for variables to be initialized")
    uninit = sess.run(tf.report_uninitialized_variables())
    while len(uninit) > 0:
        print(uninit)
        uninit = sess.run(tf.report_uninitialized_variables())

    # worker tells the ps it's ready for computation
    sess.run(tf.scatter_update(ready_list, [task], 1)) 

    # do the thing
    #run_options = tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE)
    #run_metadata = tf.RunMetadata()
    #np_image, probabilities = sess.run([shared_image, probabilities], options=run_options, run_metadata=run_metadata)
    #print("after getting probs")

    # see who did what
    #for device in run_metadata.step_stats.dev_stats:
    #    print(device.device)
    #    for node in device.node_stats:
    #        print("  ", node.node_name)

    # indicate that this task is done
    sess.run(tf.scatter_update(done_list, [task+1], 1))
   
    # wait until all tasks are done
    num_done = 1
    while num_done < num_workers+1:
        num_done = sess.run(tf.reduce_sum(done_list)) 
    
    sess.close()
