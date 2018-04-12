# Copyright 2015 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Builds the CIFAR-10 network.

Summary of available functions:

 # Compute input images and labels for training. If you would like to run
 # evaluations, use inputs() instead.
 inputs, labels = distorted_inputs()

 # Compute inference on the model inputs to make a prediction.
 predictions = inference(inputs)

 # Compute the total loss of the prediction with respect to the labels.
 loss = loss(predictions, labels)

 # Create a graph to run one step of training with respect to the loss.
 train_op = train(loss, global_step)
"""
# pylint: disable=missing-docstring
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import re
import sys
import tarfile

from six.moves import urllib
import tensorflow as tf

import cifar10_input

FLAGS = tf.app.flags.FLAGS

# Basic model parameters.
# batch size makes it smaller in case of large image size (e.g. 227x227 )
tf.app.flags.DEFINE_integer('batch_size', 48,
                            """Number of images to process in a batch.""")
tf.app.flags.DEFINE_string('data_dir', '../fold0/',  
                           """Path to the adience data.""")
tf.app.flags.DEFINE_boolean('use_fp16', False,
                            """Train the model using fp16.""")

# Global constants describing the CIFAR-10 data set.
IMAGE_SIZE = cifar10_input.IMAGE_SIZE
NUM_CLASSES = cifar10_input.NUM_CLASSES
NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN = cifar10_input.NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN
NUM_EXAMPLES_PER_EPOCH_FOR_EVAL = cifar10_input.NUM_EXAMPLES_PER_EPOCH_FOR_EVAL


# Constants describing the training process.
MOVING_AVERAGE_DECAY = 0.9999     # The decay to use for the moving average.
NUM_EPOCHS_PER_DECAY = 350.0      # Epochs after which learning rate decays.
LEARNING_RATE_DECAY_FACTOR = 0.1  # Learning rate decay factor.
INITIAL_LEARNING_RATE = 0.01       # Initial learning rate.

# If a model is trained with multiple GPUs, prefix all Op names with tower_name
# to differentiate the operations. Note that this prefix is removed from the
# names of the summaries when visualizing a model.
TOWER_NAME = 'tower'

#DATA_URL = 'https://www.cs.toronto.edu/~kriz/cifar-10-binary.tar.gz'


def _activation_summary(x):
  """Helper to create summaries for activations.

  Creates a summary that provides a histogram of activations.
  Creates a summary that measures the sparsity of activations.

  Args:
    x: Tensor
  Returns:
    nothing
  """
  # Remove 'tower_[0-9]/' from the name in case this is a multi-GPU training
  # session. This helps the clarity of presentation on tensorboard.
  tensor_name = re.sub('%s_[0-9]*/' % TOWER_NAME, '', x.op.name)
  tf.summary.histogram(tensor_name + '/activations', x)
  tf.summary.scalar(tensor_name + '/sparsity',
                                       tf.nn.zero_fraction(x))


def _variable_on_cpu(name, shape, initializer):
  """Helper to create a Variable stored on CPU memory.

  Args:
    name: name of the variable
    shape: list of ints
    initializer: initializer for Variable

  Returns:
    Variable Tensor
  """
  with tf.device('/cpu:0'):
    dtype = tf.float16 if FLAGS.use_fp16 else tf.float32
    var = tf.get_variable(name, shape, initializer=initializer, dtype=dtype)
  return var


def _variable_with_weight_decay(name, shape, stddev, wd):
  """Helper to create an initialized Variable with weight decay.

  Note that the Variable is initialized with a truncated normal distribution.
  A weight decay is added only if one is specified.

  Args:
    name: name of the variable
    shape: list of ints
    stddev: standard deviation of a truncated Gaussian
    wd: add L2Loss weight decay multiplied by this float. If None, weight
        decay is not added for this Variable.

  Returns:
    Variable Tensor
  """
  dtype = tf.float16 if FLAGS.use_fp16 else tf.float32
  var = _variable_on_cpu(
      name,
      shape,
      tf.truncated_normal_initializer(stddev=stddev, dtype=dtype))
  if wd is not None:
    weight_decay = tf.multiply(tf.nn.l2_loss(var), wd, name='weight_loss')
    tf.add_to_collection('losses', weight_decay)
  return var


def distorted_inputs():
  """Construct distorted input for CIFAR training using the Reader ops.

  Returns:
    images: Images. 4D tensor of [batch_size, IMAGE_SIZE, IMAGE_SIZE, 3] size.
    labels: Labels. 1D tensor of [batch_size] size.

  Raises:
    ValueError: If no data_dir
  """
  if not FLAGS.data_dir:
    raise ValueError('Please supply a data_dir')
  data_dir = os.path.join(FLAGS.data_dir, '')
  images, labels = cifar10_input.distorted_inputs(data_dir=data_dir,
                                                  batch_size=FLAGS.batch_size)
  if FLAGS.use_fp16:
    images = tf.cast(images, tf.float16)
    labels = tf.cast(labels, tf.float16)
  return images, labels


def inputs(eval_data):
  """Construct input for CIFAR evaluation using the Reader ops.

  Args:
    eval_data: bool, indicating if one should use the train or eval data set.

  Returns:
    images: Images. 4D tensor of [batch_size, IMAGE_SIZE, IMAGE_SIZE, 3] size.
    labels: Labels. 1D tensor of [batch_size] size.

  Raises:
    ValueError: If no data_dir
  """
  if not FLAGS.data_dir:
    raise ValueError('Please supply a data_dir')
  data_dir = os.path.join(FLAGS.data_dir, '')
  images, labels = cifar10_input.inputs(eval_data=eval_data,
                                        data_dir=data_dir,
                                        batch_size=FLAGS.batch_size)
  if FLAGS.use_fp16:
    images = tf.cast(images, tf.float16)
    labels = tf.cast(labels, tf.float16)
  return images, labels

# adience - paper - structure 
def inference(x, pkeep):
    # Encoding phase
    #fer2013: we use 1 channel : x_image = tf.reshape(x, [-1, 227, 227, 3])    
    print('>>>>> x input size = ', x)
    #x = tf.image.rgb_to_hsv(x)
#1st conv. 
    with tf.variable_scope('conv1') as scope:
        x_image = tf.reshape(x, [-1, 227, 227, 3])    
        x_image_d = tf.nn.dropout(x_image,keep_prob=pkeep)
        kernel = _variable_with_weight_decay('weights',shape=[7,7,3,96],stddev=1e-2,wd=None)
        print('>>>> kernel1 = ', kernel)
        conv = tf.nn.conv2d(x_image_d,kernel,[1,4,4,1],padding='SAME')
        biases = _variable_on_cpu('biases',[96],tf.constant_initializer(0.0))
        pre_activation = tf.nn.bias_add(conv, biases)
        conv1 = tf.nn.relu(pre_activation, name=scope.name)
        print('>>>>> conv1=',conv1)
# old one	
#    conv1 = Convolution2D(x_image, (227, 227), 3, 96, (7, 7), activation='relu',S=4)
#    conv1_out = conv1.output()

#1st pooling
#    pool1 = MaxPooling2D(conv1_out,ksize=[1,3,3,1], S=2)
#    pool1_out = pool1.output()
    pool1 = tf.nn.max_pool(conv1, ksize=[1,3,3,1], strides=[1,2,2,1],padding='SAME',name='pool1')
    drop1 = tf.nn.dropout(pool1,keep_prob=pkeep)

#LRN1
#    norm1 = tf.nn.local_response_normalization(pool1_out, depth_radius=5, alpha=0.0001, beta=0.75)
    norm1 = tf.nn.local_response_normalization(drop1, bias = 1.0, depth_radius=5, alpha=0.0001, beta=0.75,name='norm1')
    print('>>>>> norm1',norm1) 
#2nd conv. 
#    conv2 = Convolution2D(norm1, (29, 29), 96, 256, (5, 5), activation='relu',S=1)  # pad=2 - how to do it????
#    conv2_out = conv2.output()
    with tf.variable_scope('conv2') as scope:
        kernel = _variable_with_weight_decay('weights',shape=[5,5,96,256],stddev=1e-2,wd=None)
        print('>>>> kernel2 = ', kernel)
        conv = tf.nn.conv2d(norm1, kernel, [1,1,1,1], padding='SAME')
        biases = _variable_on_cpu('biases',[256], tf.constant_initializer(1.0))
        pre_activation = tf.nn.bias_add(conv,biases)
        conv2 = tf.nn.relu(pre_activation,name=scope.name)
        print('>>>>> conv2=',conv2)
# 2ndmmaxpool
    pool2= tf.nn.max_pool(conv2, ksize=[1,3,3,1], strides=[1,2,2,1],padding='SAME',name='pool2')
    drop2 = tf.nn.dropout(pool2,keep_prob=pkeep)
# lrn
    norm2 = tf.nn.local_response_normalization(drop2,bias=1.0,depth_radius=5,alpha=0.0001,beta=0.75,name='norm2')
    print('>>>>> norm2 =', norm2)
#3rd conv. 
#    conv3 = Convolution2D(norm2, (15, 15), 256, 384, (3, 3), activation='relu',S=1)  # pad=2 - how to do it????
#    conv3_out = conv3.output()
    with tf.variable_scope('conv3') as scope:
        kernel = _variable_with_weight_decay('weights',shape=[3,3,256,384],stddev=1e-2,wd=None)
        print('>>>> kernel3 = ', kernel)
        conv = tf.nn.conv2d(norm2, kernel, [1,1,1,1], padding='SAME')
        biases = _variable_on_cpu('biases',[384], tf.constant_initializer(0.0))
        pre_activation = tf.nn.bias_add(conv, biases)
        conv3 = tf.nn.relu(pre_activation, name=scope.name)
        print('>>>>>> conv3=',conv3)

#3rd pooling
#    pool3 = MaxPooling2D(conv3_out, ksize=(1,3,3,1), S=2)
#    pool3_out = pool3.output()
    pool3 =  tf.nn.max_pool(conv3, ksize=[1,3,3,1], strides=[1,2,2,1],padding='SAME',name='pool3')
    print('>>>>pool3 =', pool3) 
    drop3 = tf.nn.dropout(pool3,keep_prob=pkeep)

# fully connected 
#    fc4 = FullConnected(po, 384*8*8, 512, activation='relu')
#    fc4 = fc4.output()
    with tf.variable_scope('full4') as scope:
        reshape = tf.reshape(drop3, [x_image.get_shape()[0],-1 ] )
        dim = reshape.get_shape()[1].value	
        print('>>>>> reshape4 = ', reshape,'dim=',dim)
        weights = _variable_with_weight_decay('weights',shape=[dim,512],stddev=5e-3,wd=0.004) #wd??
        print('>>>>> weight4 =', weights)
        biases = _variable_on_cpu('biases',[512], tf.constant_initializer(1.0))
        full4 = tf.nn.relu(tf.matmul(reshape,weights) + biases, name=scope.name)
        print('>>>>> full4 = ', full4)
    drop4 = tf.nn.dropout(full4,keep_prob=pkeep)
    print('>>>> drop4 =', drop4)

#fully connected 
#    fc5 = FullConnected(drop6, 512, 512, activation='relu')
#    fc5_out = fc5.output()
    with tf.variable_scope('full5') as scope:
        dim = drop4.get_shape()[1].value
        print('>>>>> drop4 dim = ', dim)
        weights = _variable_with_weight_decay('weights',shape=[dim,512],stddev=5e-3,wd=0.004) #wd??
        print('>>>>> weight5 = ', weights)
        biases = _variable_on_cpu('biases',[512], tf.constant_initializer(1.0))
        full5 = tf.nn.relu(tf.matmul(drop4,weights) + biases, name=scope.name)
        print('>>>>> full5 >>>>> full5 = ', full5)

    drop5 = tf.nn.dropout(full5,keep_prob=pkeep)

#fully connected final layer
    with tf.variable_scope('softmax_linear') as scope:
        dim = drop5.get_shape()[1].value
        print('>>>> softmax_linear >>>>> dim = ', dim)
        weights = _variable_with_weight_decay('weights',shape=[512,NUM_CLASSES],stddev=1e-2,wd=None) 
        print('>>>> softmax_linear >>>>> weights = ', weights)
        biases = _variable_on_cpu('biases',[NUM_CLASSES], tf.constant_initializer(0.0))
        softmax_linear = tf.add(tf.matmul(drop5,weights), biases, name=scope.name)
        print('>>>> softmax_linear >>>>> = ', softmax_linear)
        _activation_summary(softmax_linear)

    return softmax_linear



def loss(logits, labels):
  """Add L2Loss to all the trainable variables.

  Add summary for "Loss" and "Loss/avg".
  Args:
    logits: Logits from inference().
    labels: Labels from distorted_inputs or inputs(). 1-D tensor
            of shape [batch_size]

  Returns:
    Loss tensor of type float.
  """
  # Calculate the average cross entropy loss across the batch.
  labels = tf.cast(labels, tf.int64)
  cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(
      labels=labels, logits=logits, name='cross_entropy_per_example')
  cross_entropy_mean = tf.reduce_mean(cross_entropy, name='cross_entropy')
  tf.add_to_collection('losses', cross_entropy_mean)

  # The total loss is defined as the cross entropy loss plus all of the weight
  # decay terms (L2 loss).
  return tf.add_n(tf.get_collection('losses'), name='total_loss')


def _add_loss_summaries(total_loss):
  """Add summaries for losses in CIFAR-10 model.

  Generates moving average for all losses and associated summaries for
  visualizing the performance of the network.

  Args:
    total_loss: Total loss from loss().
  Returns:
    loss_averages_op: op for generating moving averages of losses.
  """
  # Compute the moving average of all individual losses and the total loss.
  loss_averages = tf.train.ExponentialMovingAverage(0.9, name='avg')
  losses = tf.get_collection('losses')
  loss_averages_op = loss_averages.apply(losses + [total_loss])

  # Attach a scalar summary to all individual losses and the total loss; do the
  # same for the averaged version of the losses.
  for l in losses + [total_loss]:
    # Name each loss as '(raw)' and name the moving average version of the loss
    # as the original loss name.
    tf.summary.scalar(l.op.name + ' (raw)', l)
    tf.summary.scalar(l.op.name, loss_averages.average(l))

  return loss_averages_op


def train(total_loss, global_step):
  """Train CIFAR-10 model.

  Create an optimizer and apply to all trainable variables. Add moving
  average for all trainable variables.

  Args:
    total_loss: Total loss from loss().
    global_step: Integer Variable counting the number of training steps
      processed.
  Returns:
    train_op: op for training.
  """
  # Variables that affect learning rate.
  num_batches_per_epoch = NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN / FLAGS.batch_size
  decay_steps = int(num_batches_per_epoch * NUM_EPOCHS_PER_DECAY)

  # Decay the learning rate exponentially based on the number of steps.
  lr = tf.train.exponential_decay(INITIAL_LEARNING_RATE,
                                  global_step,
                                  decay_steps,
                                  LEARNING_RATE_DECAY_FACTOR,
                                  staircase=True)
  tf.summary.scalar('learning_rate', lr)

  # Generate moving averages of all losses and associated summaries.
  loss_averages_op = _add_loss_summaries(total_loss)

  # Compute gradients.
  with tf.control_dependencies([loss_averages_op]):
    opt = tf.train.GradientDescentOptimizer(lr)
    grads = opt.compute_gradients(total_loss)

  # Apply gradients.
  apply_gradient_op = opt.apply_gradients(grads, global_step=global_step)

  # Add histograms for trainable variables.
  for var in tf.trainable_variables():
    print('var=',var)
    tf.summary.histogram(var.op.name, var)

  # Add histograms for gradients.
  for grad, var in grads:
    if grad is not None:
      tf.summary.histogram(var.op.name + '/gradients', grad)

  # Track the moving averages of all trainable variables.
  variable_averages = tf.train.ExponentialMovingAverage(
      MOVING_AVERAGE_DECAY, global_step)
  variables_averages_op = variable_averages.apply(tf.trainable_variables())

  with tf.control_dependencies([apply_gradient_op, variables_averages_op]):
    train_op = tf.no_op(name='train')

  return train_op


#def maybe_download_and_extract():
#  """Download and extract the tarball from Alex's website."""
#  dest_directory = FLAGS.data_dir
#  if not os.path.exists(dest_directory):
#    os.makedirs(dest_directory)
#  filename = DATA_URL.split('/')[-1]
#  filepath = os.path.join(dest_directory, filename)
#  if not os.path.exists(filepath):
#    def _progress(count, block_size, total_size):
#      sys.stdout.write('\r>> Downloading %s %.1f%%' % (filename,
#          float(count * block_size) / float(total_size) * 100.0))
#      sys.stdout.flush()
#    filepath, _ = urllib.request.urlretrieve(DATA_URL, filepath, _progress)
#    print()
#    statinfo = os.stat(filepath)
#    print('Successfully downloaded', filename, statinfo.st_size, 'bytes.')
#  extracted_dir_path = os.path.join(dest_directory, 'cifar-10-batches-bin')
#  if not os.path.exists(extracted_dir_path):
#    tarfile.open(filepath, 'r:gz').extractall(dest_directory)