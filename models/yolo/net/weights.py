# -*- coding: utf-8 -*-

import numpy as np
import struct


class WeightReader:
  def __init__(self, weight_file):
    with open(weight_file, 'rb') as w_f:
      major, = struct.unpack('i', w_f.read(4))
      minor, = struct.unpack('i', w_f.read(4))
      _, = struct.unpack('i', w_f.read(4))

      if (major * 10 + minor) >= 2 and major < 1000 and minor < 1000:
        w_f.read(8)
      else:
        w_f.read(4)
      binary = w_f.read()

    self.offset = 0
    self.all_weights = np.frombuffer(binary, dtype='float32')
  def load_origin_weights(self, model, skip_detect_layer=False):
    # 81 93 105
    for i in range(model.num_layers):
      if skip_detect_layer and i in [81, 93, 105]:
        skip_size = self._skip(i)
        self._read_bytes(skip_size)
        continue

      suffixes = ["beta", "gamma", "moving_mean", "moving_variance", "bias"]
      for suffix in suffixes:
        variables = model.get_variables(layer_idx=i, suffix=suffix)
        if variables:
          self._load_1d_var(variables[0])

      variables = model.get_variables(layer_idx=i, suffix="kernel")
      if variables:
        self._load_4d_var(variables[0])

  def load_bodynet(self,model, skip_detect_layer=False):
    for i in range(model.num_body):
      if skip_detect_layer and i in [53]:
        skip_size = self._skip(i)
        self._read_bytes(skip_size)
        continue

      suffixes = ["beta", "gamma", "moving_mean", "moving_variance", "bias"]
      for suffix in suffixes:
        variables = model.get_variables(layer_idx=i, suffix=suffix)
        if variables:
          self._load_1d_var(variables[0])
      variables = model.get_variables(layer_idx=i, suffix="kernel")
      if variables:

        self._load_4d_var(variables[0])

  def _skip(self, i):
    if i == 81:
      skip_size = 255 + 1024 * 255
    elif i == 93:
      skip_size = 255 + 512 * 255
    elif i == 105:
      skip_size = 255 + 256 * 255
    else:
      skip_size = 0
    return skip_size

  def _read_bytes(self, size):
    self.offset = self.offset + size
    return self.all_weights[self.offset - size:self.offset]

  def _load_1d_var(self, variable):
    size = np.prod(variable.shape)
    value = self._read_bytes(size)  # bias
    variable.assign(value)

  def _load_4d_var(self, variable):
    size = np.prod(variable.shape)
    value = self._read_bytes(size)  # scale
    value = value.reshape(list(reversed(variable.shape)))
    value = value.transpose([2, 3, 1, 0])
    variable.assign(value)


if __name__ == '__main__':
  from models.yolo.net import yolonet
  import os
  net = yolonet.Yolonet(n_classes=80)

  rootpath='/home/gwl/PycharmProjects/mine/tf2-yolo3/checkpoints/darknet_coco'
  weightfile_all='yolov3.weights'
  weightfile_conv='darknet53.conv.74'
  file=os.path.join(rootpath,weightfile_conv)
  weight_reader = WeightReader(file)

  for op in net.body.layers:
    op.trainable=False
  weight_reader.load_bodynet(net,skip_detect_layer=True)
  for op in net.non_trainable_variables:
    print(op.name)