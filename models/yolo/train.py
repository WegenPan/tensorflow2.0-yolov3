# -*- coding: utf-8 -*-

import tensorflow as tf
import os
from tqdm import tqdm
from yolo.loss import loss_fn
from tensorflow import keras

def train_fn(model, train_generator, valid_generator=None, learning_rate=1e-4, num_epoches=500, save_dname=None):
  save_fname = _setup(save_dname)
  optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
  history = []
  for i in range(num_epoches):

    # 1. update params
    train_loss = _loop_train(model, optimizer, train_generator)

    # 2. monitor validation loss
    if valid_generator:
      valid_loss = _loop_validation(model, valid_generator)
      loss_value = valid_loss
    else:
      loss_value = train_loss
    print("{}-th loss = {}, train_loss = {}".format(i, loss_value, train_loss))

    # 3. update weights
    history.append(loss_value)
    if save_fname is not None and loss_value == min(history):
      print("    update weight {}".format(loss_value))
      model.save_weights("{}.h5".format(save_fname))

  return history

def _loop_train(model, optimizer, generator):
  n_steps = generator.steps_per_epoch
  loss_value = 0
  for _ in tqdm(range(n_steps)):
    xs, yolo_1, yolo_2, yolo_3 = generator.next_batch()
    # xs img
    # print(yolo_1.shape)(2, 9, 9, 3, 9) 第一维为batchsize
    # print(yolo_2.shape)(2, 18, 18, 3, 9)
    # print(yolo_3.shape)(2, 36, 36, 3, 9)
    ys = [yolo_1, yolo_2, yolo_3]
    loss = _grad_fn(model, xs, ys,optimizer)
    loss_value += loss
    # optimizer.apply_gradients(zip(grads, model.trainable_variables))
  loss_value /= generator.steps_per_epoch
  return loss_value


def _loop_validation(model, generator):
  # one epoch
  n_steps = generator.steps_per_epoch
  loss_value = 0
  for _ in range(n_steps):
    xs, yolo_1, yolo_2, yolo_3 = generator.next_batch()
    ys = [yolo_1, yolo_2, yolo_3]
    ys_ = model(xs)
    loss_value += loss_fn(ys, ys_)
  loss_value /= generator.steps_per_epoch
  return loss_value


def _setup(save_dname):
  if save_dname:
    if not os.path.exists(save_dname):
      os.makedirs(save_dname)
    save_fname = os.path.join(save_dname, "weights")
  else:
    save_fname = None
  return save_fname

@tf.function
def _grad_fn(model, images_tensor, list_y_trues,optimizer):
  with tf.GradientTape() as tape:
    logits = model(images_tensor)
    loss = loss_fn(list_y_trues, logits)
    # print("loss = ", loss)
    grads=tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(grads, model.trainable_variables))
  return loss


if __name__ == '__main__':
  tf.enable_eager_execution()
  pass
