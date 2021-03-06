# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
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
"""Tests for the Python extension-based XLA client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import itertools

import numpy as np

from tensorflow.compiler.xla.python import xla_client
import unittest


class LocalComputationTest(unittest.TestCase):
  """Base class for running an XLA Computation through the local client."""

  def _NewComputation(self, name=None):
    if name is None:
      name = self.id()
    return xla_client.ComputationBuilder(name)

  def _Execute(self, c, arguments):
    compiled_c = c.Build().CompileWithExampleArguments(arguments)
    return compiled_c.Execute(arguments)

  def _ExecuteAndAssertWith(self, assert_func, c, arguments, expected):
    assert expected is not None
    result = self._Execute(c, arguments)
    # Numpy's comparison methods are a bit too lenient by treating inputs as
    # "array-like", meaning that scalar 4 will be happily compared equal to
    # [[4]]. We'd like to be more strict so assert shapes as well.
    self.assertEqual(np.asanyarray(result).shape, np.asanyarray(expected).shape)
    assert_func(result, expected)

  def _ExecuteAndCompareExact(self, c, arguments=(), expected=None):
    self._ExecuteAndAssertWith(np.testing.assert_equal, c, arguments, expected)

  def _ExecuteAndCompareClose(self, c, arguments=(), expected=None):
    self._ExecuteAndAssertWith(np.testing.assert_allclose, c, arguments,
                               expected)


def NumpyArrayF32(*args, **kwargs):
  """Convenience wrapper to create Numpy arrays with a np.float32 dtype."""
  return np.array(*args, dtype=np.float32, **kwargs)


def NumpyArrayF64(*args, **kwargs):
  """Convenience wrapper to create Numpy arrays with a np.float64 dtype."""
  return np.array(*args, dtype=np.float64, **kwargs)


def NumpyArrayS32(*args, **kwargs):
  """Convenience wrapper to create Numpy arrays with a np.int32 dtype."""
  return np.array(*args, dtype=np.int32, **kwargs)


def NumpyArrayS64(*args, **kwargs):
  """Convenience wrapper to create Numpy arrays with a np.int64 dtype."""
  return np.array(*args, dtype=np.int64, **kwargs)


def NumpyArrayBool(*args, **kwargs):
  """Convenience wrapper to create Numpy arrays with a np.bool dtype."""
  return np.array(*args, dtype=np.bool, **kwargs)


class ComputationsWithConstantsTest(LocalComputationTest):
  """Tests focusing on Constant ops."""

  def testConstantScalarSumF32(self):
    c = self._NewComputation()
    c.Add(c.ConstantF32Scalar(1.11), c.ConstantF32Scalar(3.14))
    self._ExecuteAndCompareClose(c, expected=4.25)

  def testConstantScalarSumF64(self):
    c = self._NewComputation()
    c.Add(c.ConstantF64Scalar(1.11), c.ConstantF64Scalar(3.14))
    self._ExecuteAndCompareClose(c, expected=4.25)

  def testConstantScalarSumS32(self):
    c = self._NewComputation()
    c.Add(c.ConstantS32Scalar(1), c.ConstantS32Scalar(2))
    self._ExecuteAndCompareClose(c, expected=3)

  def testConstantScalarSumS64(self):
    c = self._NewComputation()
    c.Add(c.ConstantS64Scalar(1), c.ConstantS64Scalar(2))
    self._ExecuteAndCompareClose(c, expected=3)

  def testConstantVectorMulF32(self):
    c = self._NewComputation()
    c.Mul(
        c.Constant(NumpyArrayF32([2.5, 3.3, -1.2, 0.7])),
        c.Constant(NumpyArrayF32([-1.2, 2, -2, -3])))
    self._ExecuteAndCompareClose(c, expected=[-3, 6.6, 2.4, -2.1])

  def testConstantVectorMulF64(self):
    c = self._NewComputation()
    c.Mul(
        c.Constant(NumpyArrayF64([2.5, 3.3, -1.2, 0.7])),
        c.Constant(NumpyArrayF64([-1.2, 2, -2, -3])))
    self._ExecuteAndCompareClose(c, expected=[-3, 6.6, 2.4, -2.1])

  def testConstantVectorScalarDivF32(self):
    c = self._NewComputation()
    c.Div(
        c.Constant(NumpyArrayF32([1.5, 2.5, 3.0, -10.8])),
        c.ConstantF32Scalar(2.0))
    self._ExecuteAndCompareClose(c, expected=[0.75, 1.25, 1.5, -5.4])

  def testConstantVectorScalarDivF64(self):
    c = self._NewComputation()
    c.Div(
        c.Constant(NumpyArrayF64([1.5, 2.5, 3.0, -10.8])),
        c.ConstantF64Scalar(2.0))
    self._ExecuteAndCompareClose(c, expected=[0.75, 1.25, 1.5, -5.4])

  def testConstantVectorScalarPowF32(self):
    c = self._NewComputation()
    c.Pow(c.Constant(NumpyArrayF32([1.5, 2.5, 3.0])), c.ConstantF32Scalar(2.))
    self._ExecuteAndCompareClose(c, expected=[2.25, 6.25, 9.])

  def testConstantVectorScalarPowF64(self):
    c = self._NewComputation()
    c.Pow(c.Constant(NumpyArrayF64([1.5, 2.5, 3.0])), c.ConstantF64Scalar(2.))
    self._ExecuteAndCompareClose(c, expected=[2.25, 6.25, 9.])

  def testBooleanAnd(self):
    c = self._NewComputation()
    c.And(
        c.Constant(NumpyArrayBool([True, False, True, False])),
        c.Constant(NumpyArrayBool([True, True, False, False])))
    self._ExecuteAndCompareExact(c, expected=[True, False, False, False])

  def testBooleanOr(self):
    c = self._NewComputation()
    c.Or(
        c.Constant(NumpyArrayBool([True, False, True, False])),
        c.Constant(NumpyArrayBool([True, True, False, False])))
    self._ExecuteAndCompareExact(c, expected=[True, True, True, False])

  def testSum2DF32(self):
    c = self._NewComputation()
    c.Add(
        c.Constant(NumpyArrayF32([[1, 2, 3], [4, 5, 6]])),
        c.Constant(NumpyArrayF32([[1, -1, 1], [-1, 1, -1]])))
    self._ExecuteAndCompareClose(c, expected=[[2, 1, 4], [3, 6, 5]])

  def testSum2DF64(self):
    c = self._NewComputation()
    c.Add(
        c.Constant(NumpyArrayF64([[1, 2, 3], [4, 5, 6]])),
        c.Constant(NumpyArrayF64([[1, -1, 1], [-1, 1, -1]])))
    self._ExecuteAndCompareClose(c, expected=[[2, 1, 4], [3, 6, 5]])

  def testSum2DWith1DBroadcastDim0F32(self):
    # sum of a 2D array with a 1D array where the latter is replicated across
    # dimension 0 to match the former's shape.
    c = self._NewComputation()
    c.Add(
        c.Constant(NumpyArrayF32([[1, 2, 3], [4, 5, 6], [7, 8, 9]])),
        c.Constant(NumpyArrayF32([10, 20, 30])),
        broadcast_dimensions=(0,))
    self._ExecuteAndCompareClose(
        c, expected=[[11, 12, 13], [24, 25, 26], [37, 38, 39]])

  def testSum2DWith1DBroadcastDim0F64(self):
    # sum of a 2D array with a 1D array where the latter is replicated across
    # dimension 0 to match the former's shape.
    c = self._NewComputation()
    c.Add(
        c.Constant(NumpyArrayF64([[1, 2, 3], [4, 5, 6], [7, 8, 9]])),
        c.Constant(NumpyArrayF64([10, 20, 30])),
        broadcast_dimensions=(0,))
    self._ExecuteAndCompareClose(
        c, expected=[[11, 12, 13], [24, 25, 26], [37, 38, 39]])

  def testSum2DWith1DBroadcastDim1F32(self):
    # sum of a 2D array with a 1D array where the latter is replicated across
    # dimension 1 to match the former's shape.
    c = self._NewComputation()
    c.Add(
        c.Constant(NumpyArrayF32([[1, 2, 3], [4, 5, 6], [7, 8, 9]])),
        c.Constant(NumpyArrayF32([10, 20, 30])),
        broadcast_dimensions=(1,))
    self._ExecuteAndCompareClose(
        c, expected=[[11, 22, 33], [14, 25, 36], [17, 28, 39]])

  def testSum2DWith1DBroadcastDim1F64(self):
    # sum of a 2D array with a 1D array where the latter is replicated across
    # dimension 1 to match the former's shape.
    c = self._NewComputation()
    c.Add(
        c.Constant(NumpyArrayF64([[1, 2, 3], [4, 5, 6], [7, 8, 9]])),
        c.Constant(NumpyArrayF64([10, 20, 30])),
        broadcast_dimensions=(1,))
    self._ExecuteAndCompareClose(
        c, expected=[[11, 22, 33], [14, 25, 36], [17, 28, 39]])

  def testConstantAxpyF32(self):
    c = self._NewComputation()
    c.Add(
        c.Mul(
            c.ConstantF32Scalar(2),
            c.Constant(NumpyArrayF32([2.2, 3.3, 4.4, 5.5]))),
        c.Constant(NumpyArrayF32([100, -100, 200, -200])))
    self._ExecuteAndCompareClose(c, expected=[104.4, -93.4, 208.8, -189])

  def testConstantAxpyF64(self):
    c = self._NewComputation()
    c.Add(
        c.Mul(
            c.ConstantF64Scalar(2),
            c.Constant(NumpyArrayF64([2.2, 3.3, 4.4, 5.5]))),
        c.Constant(NumpyArrayF64([100, -100, 200, -200])))
    self._ExecuteAndCompareClose(c, expected=[104.4, -93.4, 208.8, -189])


class ParametersTest(LocalComputationTest):
  """Tests focusing on Parameter ops and argument-passing."""

  def setUp(self):
    self.f32_scalar_2 = NumpyArrayF32(2.0)
    self.f32_4vector = NumpyArrayF32([-2.3, 3.3, -4.3, 5.3])
    self.f64_scalar_2 = NumpyArrayF64(2.0)
    self.f64_4vector = NumpyArrayF64([-2.3, 3.3, -4.3, 5.3])
    self.s32_scalar_3 = NumpyArrayS32(3)
    self.s32_4vector = NumpyArrayS32([10, 15, -2, 7])
    self.s64_scalar_3 = NumpyArrayS64(3)
    self.s64_4vector = NumpyArrayS64([10, 15, -2, 7])

  def testScalarTimesVectorAutonumberF32(self):
    c = self._NewComputation()
    p0 = c.ParameterFromNumpy(self.f32_scalar_2)
    p1 = c.ParameterFromNumpy(self.f32_4vector)
    c.Mul(p0, p1)
    self._ExecuteAndCompareClose(
        c,
        arguments=[self.f32_scalar_2, self.f32_4vector],
        expected=[-4.6, 6.6, -8.6, 10.6])

  def testScalarTimesVectorAutonumberF64(self):
    c = self._NewComputation()
    p0 = c.ParameterFromNumpy(self.f64_scalar_2)
    p1 = c.ParameterFromNumpy(self.f64_4vector)
    c.Mul(p0, p1)
    self._ExecuteAndCompareClose(
        c,
        arguments=[self.f64_scalar_2, self.f64_4vector],
        expected=[-4.6, 6.6, -8.6, 10.6])

  def testScalarTimesVectorS32(self):
    c = self._NewComputation()
    p0 = c.ParameterFromNumpy(self.s32_scalar_3)
    p1 = c.ParameterFromNumpy(self.s32_4vector)
    c.Mul(p0, p1)
    self._ExecuteAndCompareExact(
        c,
        arguments=[self.s32_scalar_3, self.s32_4vector],
        expected=[30, 45, -6, 21])

  def testScalarTimesVectorS64(self):
    c = self._NewComputation()
    p0 = c.ParameterFromNumpy(self.s64_scalar_3)
    p1 = c.ParameterFromNumpy(self.s64_4vector)
    c.Mul(p0, p1)
    self._ExecuteAndCompareExact(
        c,
        arguments=[self.s64_scalar_3, self.s64_4vector],
        expected=[30, 45, -6, 21])

  def testScalarMinusVectorExplicitNumberingF32(self):
    # Use explicit numbering and pass parameter_num first. Sub is used since
    # it's not commutative and can help catch parameter reversal within the
    # computation.
    c = self._NewComputation()
    p1 = c.ParameterFromNumpy(self.f32_4vector, parameter_num=1)
    p0 = c.ParameterFromNumpy(self.f32_scalar_2, parameter_num=0)
    c.Sub(p1, p0)
    self._ExecuteAndCompareClose(
        c,
        arguments=[self.f32_scalar_2, self.f32_4vector],
        expected=[-4.3, 1.3, -6.3, 3.3])

  def testScalarMinusVectorExplicitNumberingF64(self):
    # Use explicit numbering and pass parameter_num first. Sub is used since
    # it's not commutative and can help catch parameter reversal within the
    # computation.
    c = self._NewComputation()
    p1 = c.ParameterFromNumpy(self.f64_4vector, parameter_num=1)
    p0 = c.ParameterFromNumpy(self.f64_scalar_2, parameter_num=0)
    c.Sub(p1, p0)
    self._ExecuteAndCompareClose(
        c,
        arguments=[self.f64_scalar_2, self.f64_4vector],
        expected=[-4.3, 1.3, -6.3, 3.3])


class LocalBufferTest(LocalComputationTest):
  """Tests focusing on execution with LocalBuffers."""

  def _Execute(self, c, arguments):
    compiled_c = c.Build().CompileWithExampleArguments(arguments)
    arg_buffers = [xla_client.LocalBuffer.from_py(arg) for arg in arguments]
    result_buffer = compiled_c.ExecuteWithLocalBuffers(arg_buffers)
    return result_buffer.to_py()

  def testConstantSum(self):
    c = self._NewComputation()
    c.Add(c.ConstantF32Scalar(1.11), c.ConstantF32Scalar(3.14))
    self._ExecuteAndCompareClose(c, expected=4.25)

  def testOneParameterSum(self):
    c = self._NewComputation()
    c.Add(c.ParameterFromNumpy(NumpyArrayF32(0.)), c.ConstantF32Scalar(3.14))
    self._ExecuteAndCompareClose(
        c,
        arguments=[NumpyArrayF32(1.11)],
        expected=4.25)

  def testTwoParameterSum(self):
    c = self._NewComputation()
    c.Add(c.ParameterFromNumpy(NumpyArrayF32(0.)),
          c.ParameterFromNumpy(NumpyArrayF32(0.)))
    self._ExecuteAndCompareClose(
        c,
        arguments=[NumpyArrayF32(1.11), NumpyArrayF32(3.14)],
        expected=4.25)

  def testCannotCallWithDeletedBuffers(self):
    c = self._NewComputation()
    c.Add(c.ParameterFromNumpy(NumpyArrayF32(0.)), c.ConstantF32Scalar(3.14))
    arg = NumpyArrayF32(1.11)
    compiled_c = c.Build().CompileWithExampleArguments([arg])
    arg_buffer = xla_client.LocalBuffer.from_py(arg)
    arg_buffer.delete()
    with self.assertRaises(ValueError):
      compiled_c.ExecuteWithLocalBuffers([arg_buffer])


class SingleOpTest(LocalComputationTest):
  """Tests for single ops.

  The goal here is smoke testing - to exercise the most basic functionality of
  single XLA ops. As minimal as possible number of additional ops are added
  around the op being tested.
  """

  def testConcatenateF32(self):
    c = self._NewComputation()
    c.Concatenate(
        (c.Constant(NumpyArrayF32([1.0, 2.0, 3.0])),
         c.Constant(NumpyArrayF32([4.0, 5.0, 6.0]))),
        dimension=0)
    self._ExecuteAndCompareClose(c, expected=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

  def testConcatenateF64(self):
    c = self._NewComputation()
    c.Concatenate(
        (c.Constant(NumpyArrayF64([1.0, 2.0, 3.0])),
         c.Constant(NumpyArrayF64([4.0, 5.0, 6.0]))),
        dimension=0)
    self._ExecuteAndCompareClose(c, expected=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

  def testConvertElementType(self):
    xla_types = {
        np.bool: xla_client.xla_data_pb2.PRED,
        np.int32: xla_client.xla_data_pb2.S32,
        np.int64: xla_client.xla_data_pb2.S64,
        np.float32: xla_client.xla_data_pb2.F32,
        np.float64: xla_client.xla_data_pb2.F64,
    }

    def _ConvertAndTest(template, src_dtype, dst_dtype):
      c = self._NewComputation()
      x = c.Constant(np.array(template, dtype=src_dtype))
      c.ConvertElementType(x, xla_types[dst_dtype])

      result = c.Build().Compile().Execute()
      expected = np.array(template, dtype=dst_dtype)

      self.assertEqual(result.shape, expected.shape)
      self.assertEqual(result.dtype, expected.dtype)
      np.testing.assert_equal(result, expected)

    x = [0, 1, 0, 0, 1]
    for src_dtype, dst_dtype in itertools.product(xla_types, xla_types):
      _ConvertAndTest(x, src_dtype, dst_dtype)

  def testCrossReplicaSumOneReplica(self):
    samples = [
        NumpyArrayF32(42.0),
        NumpyArrayF32([97.0]),
        NumpyArrayF32([64.0, 117.0]),
        NumpyArrayF32([[2.0, 3.0], [4.0, 5.0]]),
    ]
    for lhs in samples:
      c = self._NewComputation()
      c.CrossReplicaSum(c.Constant(lhs))
      self._ExecuteAndCompareExact(c, expected=lhs)

  def testDotMatrixVectorF32(self):
    c = self._NewComputation()
    lhs = NumpyArrayF32([[2.0, 3.0], [4.0, 5.0]])
    rhs = NumpyArrayF32([[10.0], [20.0]])
    c.Dot(c.Constant(lhs), c.Constant(rhs))
    self._ExecuteAndCompareClose(c, expected=np.dot(lhs, rhs))

  def testDotMatrixVectorF64(self):
    c = self._NewComputation()
    lhs = NumpyArrayF64([[2.0, 3.0], [4.0, 5.0]])
    rhs = NumpyArrayF64([[10.0], [20.0]])
    c.Dot(c.Constant(lhs), c.Constant(rhs))
    self._ExecuteAndCompareClose(c, expected=np.dot(lhs, rhs))

  def testDotMatrixMatrixF32(self):
    c = self._NewComputation()
    lhs = NumpyArrayF32([[2.0, 3.0], [4.0, 5.0]])
    rhs = NumpyArrayF32([[10.0, 20.0], [100.0, 200.0]])
    c.Dot(c.Constant(lhs), c.Constant(rhs))
    self._ExecuteAndCompareClose(c, expected=np.dot(lhs, rhs))

  def testDotMatrixMatrixF64(self):
    c = self._NewComputation()
    lhs = NumpyArrayF64([[2.0, 3.0], [4.0, 5.0]])
    rhs = NumpyArrayF64([[10.0, 20.0], [100.0, 200.0]])
    c.Dot(c.Constant(lhs), c.Constant(rhs))
    self._ExecuteAndCompareClose(c, expected=np.dot(lhs, rhs))

  def testConvF32Same(self):
    c = self._NewComputation()
    a = lambda *dims: np.arange(np.prod(dims)).reshape(dims).astype("float32")
    lhs = a(1, 2, 3, 4)
    rhs = a(1, 2, 1, 2) * 10
    c.Conv(c.Constant(lhs), c.Constant(rhs),
           [1, 1], xla_client.PaddingType.SAME)
    result = np.array([[[[640., 700., 760., 300.],
                         [880., 940., 1000., 380.],
                         [1120., 1180., 1240., 460.]]]])
    self._ExecuteAndCompareClose(c, expected=result)

  def testConvF32Valid(self):
    c = self._NewComputation()
    a = lambda *dims: np.arange(np.prod(dims)).reshape(dims).astype("float32")
    lhs = a(1, 2, 3, 4)
    rhs = a(1, 2, 1, 2) * 10
    c.Conv(c.Constant(lhs), c.Constant(rhs),
           [2, 1], xla_client.PaddingType.VALID)
    result = np.array([[[[640., 700., 760.],
                         [1120., 1180., 1240.]]]])
    self._ExecuteAndCompareClose(c, expected=result)

  def testConvWithGeneralPaddingF32(self):
    c = self._NewComputation()
    a = lambda *dims: np.arange(np.prod(dims)).reshape(dims).astype("float32")
    lhs = a(1, 1, 2, 3)
    rhs = a(1, 1, 1, 2) * 10
    strides = [1, 1]
    pads = [(1, 0), (0, 1)]
    lhs_dilation = (2, 1)
    rhs_dilation = (1, 1)
    c.ConvWithGeneralPadding(c.Constant(lhs), c.Constant(rhs),
                             strides, pads, lhs_dilation, rhs_dilation)
    result = np.array([[[[0., 0., 0.],
                         [10., 20., 0.],
                         [0., 0., 0.],
                         [40., 50., 0.]]]])
    self._ExecuteAndCompareClose(c, expected=result)

  def testBooleanNot(self):
    c = self._NewComputation()
    arr = NumpyArrayBool([True, False, True])
    c.Not(c.Constant(arr))
    self._ExecuteAndCompareClose(c, expected=~arr)

  def testExp(self):
    c = self._NewComputation()
    arr = NumpyArrayF32([3.3, 12.1])
    c.Exp(c.Constant(arr))
    self._ExecuteAndCompareClose(c, expected=np.exp(arr))

  def testLog(self):
    c = self._NewComputation()
    arr = NumpyArrayF32([3.3, 12.1])
    c.Log(c.Constant(arr))
    self._ExecuteAndCompareClose(c, expected=np.log(arr))

  def testNeg(self):
    c = self._NewComputation()
    arr = NumpyArrayF32([3.3, 12.1])
    c.Neg(c.Constant(arr))
    self._ExecuteAndCompareClose(c, expected=-arr)

  def testFloor(self):
    c = self._NewComputation()
    arr = NumpyArrayF32([3.3, 12.1])
    c.Floor(c.Constant(arr))
    self._ExecuteAndCompareClose(c, expected=np.floor(arr))

  def testCeil(self):
    c = self._NewComputation()
    arr = NumpyArrayF32([3.3, 12.1])
    c.Ceil(c.Constant(arr))
    self._ExecuteAndCompareClose(c, expected=np.ceil(arr))

  def testAbs(self):
    c = self._NewComputation()
    arr = NumpyArrayF32([3.3, -12.1, 2.4, -1.])
    c.Abs(c.Constant(arr))
    self._ExecuteAndCompareClose(c, expected=np.abs(arr))

  def testTanh(self):
    c = self._NewComputation()
    arr = NumpyArrayF32([3.3, 12.1])
    c.Tanh(c.Constant(arr))
    self._ExecuteAndCompareClose(c, expected=np.tanh(arr))

  def testTrans(self):

    def _TransposeAndTest(array):
      c = self._NewComputation()
      c.Trans(c.Constant(array))
      self._ExecuteAndCompareClose(c, expected=array.T)

    # Test square and non-square matrices in both default (C) and F orders.
    for array_fun in [NumpyArrayF32, NumpyArrayF64]:
      _TransposeAndTest(array_fun([[1, 2, 3], [4, 5, 6]]))
      _TransposeAndTest(array_fun([[1, 2, 3], [4, 5, 6]], order="F"))
      _TransposeAndTest(array_fun([[1, 2], [4, 5]]))
      _TransposeAndTest(array_fun([[1, 2], [4, 5]], order="F"))

  def testTranspose(self):

    def _TransposeAndTest(array, permutation):
      c = self._NewComputation()
      c.Transpose(c.Constant(array), permutation)
      expected = np.transpose(array, permutation)
      self._ExecuteAndCompareClose(c, expected=expected)

    _TransposeAndTest(NumpyArrayF32([[1, 2, 3], [4, 5, 6]]), [0, 1])
    _TransposeAndTest(NumpyArrayF32([[1, 2, 3], [4, 5, 6]]), [1, 0])
    _TransposeAndTest(NumpyArrayF32([[1, 2], [4, 5]]), [0, 1])
    _TransposeAndTest(NumpyArrayF32([[1, 2], [4, 5]]), [1, 0])

    arr = np.random.RandomState(0).randn(2, 3, 4).astype(np.float32)
    for permutation in itertools.permutations(range(arr.ndim)):
      _TransposeAndTest(arr, permutation)
      _TransposeAndTest(np.asfortranarray(arr), permutation)

  def testEq(self):
    c = self._NewComputation()
    c.Eq(
        c.Constant(NumpyArrayS32([1, 2, 3, 4])),
        c.Constant(NumpyArrayS32([4, 2, 3, 1])))
    self._ExecuteAndCompareExact(c, expected=[False, True, True, False])

  def testNe(self):
    c = self._NewComputation()
    c.Ne(
        c.Constant(NumpyArrayS32([1, 2, 3, 4])),
        c.Constant(NumpyArrayS32([4, 2, 3, 1])))
    self._ExecuteAndCompareExact(c, expected=[True, False, False, True])

    c.Ne(
        c.Constant(NumpyArrayF32([-2.0, 0.0,
                                  float("nan"),
                                  float("nan")])),
        c.Constant(NumpyArrayF32([2.0, -0.0, 1.0, float("nan")])))
    self._ExecuteAndAssertWith(
        np.testing.assert_allclose, c, (), expected=[True, False, True, True])

  def testGt(self):
    c = self._NewComputation()
    c.Gt(
        c.Constant(NumpyArrayS32([1, 2, 3, 4, 9])),
        c.Constant(NumpyArrayS32([1, 0, 2, 7, 12])))
    self._ExecuteAndCompareExact(c, expected=[False, True, True, False, False])

  def testGe(self):
    c = self._NewComputation()
    c.Ge(
        c.Constant(NumpyArrayS32([1, 2, 3, 4, 9])),
        c.Constant(NumpyArrayS32([1, 0, 2, 7, 12])))
    self._ExecuteAndCompareExact(c, expected=[True, True, True, False, False])

  def testLt(self):
    c = self._NewComputation()
    c.Lt(
        c.Constant(NumpyArrayS32([1, 2, 3, 4, 9])),
        c.Constant(NumpyArrayS32([1, 0, 2, 7, 12])))
    self._ExecuteAndCompareExact(c, expected=[False, False, False, True, True])

  def testLe(self):
    c = self._NewComputation()
    c.Le(
        c.Constant(NumpyArrayS32([1, 2, 3, 4, 9])),
        c.Constant(NumpyArrayS32([1, 0, 2, 7, 12])))
    self._ExecuteAndCompareExact(c, expected=[True, False, False, True, True])

  def testMax(self):
    c = self._NewComputation()
    c.Max(
        c.Constant(NumpyArrayF32([1.0, 2.0, 3.0, 4.0, 9.0])),
        c.Constant(NumpyArrayF32([1.0, 0.0, 2.0, 7.0, 12.0])))
    self._ExecuteAndCompareExact(c, expected=[1.0, 2.0, 3.0, 7.0, 12.0])

  def testMaxExplicitBroadcastDim0(self):
    c = self._NewComputation()
    c.Max(
        c.Constant(NumpyArrayF32([[1, 2, 3], [4, 5, 6], [7, 8, 9]])),
        c.Constant(NumpyArrayF32([3, 4, 5])),
        broadcast_dimensions=(0,))
    self._ExecuteAndCompareExact(c, expected=[[3, 3, 3], [4, 5, 6], [7, 8, 9]])

  def testMaxExplicitBroadcastDim1(self):
    c = self._NewComputation()
    c.Max(
        c.Constant(NumpyArrayF32([[1, 2, 3], [4, 5, 6], [7, 8, 9]])),
        c.Constant(NumpyArrayF32([3, 4, 5])),
        broadcast_dimensions=(1,))
    self._ExecuteAndCompareExact(c, expected=[[3, 4, 5], [4, 5, 6], [7, 8, 9]])

  def testMin(self):
    c = self._NewComputation()
    c.Min(
        c.Constant(NumpyArrayF32([1.0, 2.0, 3.0, 4.0, 9.0])),
        c.Constant(NumpyArrayF32([1.0, 0.0, 2.0, 7.0, 12.0])))
    self._ExecuteAndCompareExact(c, expected=[1.0, 0.0, 2.0, 4.0, 9.0])

  def testReshape(self):
    c = self._NewComputation()
    c.Reshape(
        c.Constant(NumpyArrayS32([[1, 2], [3, 4], [5, 6]])),
        dimensions=[0, 1],
        new_sizes=[2, 3])
    self._ExecuteAndCompareExact(c, expected=[[1, 2, 3], [4, 5, 6]])

  def testCollapse(self):
    c = self._NewComputation()
    c.Collapse(
        c.Constant(NumpyArrayS32([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])),
        dimensions=[1, 2])
    self._ExecuteAndCompareExact(c, expected=[[1, 2, 3, 4], [5, 6, 7, 8]])

  def testRev(self):
    c = self._NewComputation()
    c.Rev(
        c.Constant(NumpyArrayS32([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])),
        dimensions=[0, 2])
    self._ExecuteAndCompareExact(
        c, expected=[[[6, 5], [8, 7]], [[2, 1], [4, 3]]])

  def testSelect(self):
    c = self._NewComputation()
    c.Select(
        c.Constant(NumpyArrayBool([True, False, False, True, False])),
        c.Constant(NumpyArrayS32([1, 2, 3, 4, 5])),
        c.Constant(NumpyArrayS32([-1, -2, -3, -4, -5])))
    self._ExecuteAndCompareExact(c, expected=[1, -2, -3, 4, -5])

  def testSlice(self):
    c = self._NewComputation()
    c.Slice(
        c.Constant(NumpyArrayS32([[1, 2, 3], [4, 5, 6], [7, 8, 9]])), [1, 0],
        [3, 2])
    self._ExecuteAndCompareExact(c, expected=[[4, 5], [7, 8]])

  def testDynamicSlice(self):
    c = self._NewComputation()
    c.DynamicSlice(
        c.Constant(NumpyArrayS32([[1, 2, 3], [4, 5, 6], [7, 8, 9]])),
        c.Constant(NumpyArrayS32([1, 0])), [2, 2])
    self._ExecuteAndCompareExact(c, expected=[[4, 5], [7, 8]])

  def testDynamicUpdateSlice(self):
    c = self._NewComputation()
    c.DynamicUpdateSlice(
        c.Constant(NumpyArrayS32([[1, 2, 3], [4, 5, 6], [7, 8, 9]])),
        c.Constant(NumpyArrayS32([[1, 2], [3, 4]])),
        c.Constant(NumpyArrayS32([1, 1])))
    self._ExecuteAndCompareExact(c, expected=[[1, 2, 3], [4, 1, 2], [7, 3, 4]])

  def testTuple(self):
    c = self._NewComputation()
    c.Tuple(
        c.ConstantS32Scalar(42), c.Constant(NumpyArrayF32([1.0, 2.0])),
        c.Constant(NumpyArrayBool([True, False, False, True])))
    result = c.Build().Compile().Execute()
    self.assertIsInstance(result, tuple)
    np.testing.assert_equal(result[0], 42)
    np.testing.assert_allclose(result[1], [1.0, 2.0])
    np.testing.assert_equal(result[2], [True, False, False, True])

  def testGetTupleElement(self):
    c = self._NewComputation()
    c.GetTupleElement(
        c.Tuple(
            c.ConstantS32Scalar(42), c.Constant(NumpyArrayF32([1.0, 2.0])),
            c.Constant(NumpyArrayBool([True, False, False, True]))), 1)
    self._ExecuteAndCompareClose(c, expected=[1.0, 2.0])

  def testBroadcast(self):
    c = self._NewComputation()
    c.Broadcast(c.Constant(NumpyArrayS32([10, 20, 30, 40])), sizes=(3,))
    self._ExecuteAndCompareExact(
        c, expected=[[10, 20, 30, 40], [10, 20, 30, 40], [10, 20, 30, 40]])

  def testRngNormal(self):
    shape = (2, 3)
    c = self._NewComputation()
    c.RngNormal(c.Constant(NumpyArrayF32(0.)), c.Constant(NumpyArrayF32(1.)),
                dims=shape)
    result = c.Build().Compile().Execute()
    # since the result is random, we just check shape and uniqueness
    self.assertEqual(result.shape, shape)
    self.assertEqual(len(np.unique(result)), np.prod(shape))

  def testRngUniformF32(self):
    lo, hi = 2., 4.
    shape = (2, 3)
    c = self._NewComputation()
    c.RngUniform(c.Constant(NumpyArrayF32(lo)), c.Constant(NumpyArrayF32(hi)),
                 dims=shape)
    result = c.Build().Compile().Execute()
    # since the result is random, we just check shape, uniqueness, and range
    self.assertEqual(result.shape, shape)
    self.assertEqual(len(np.unique(result)), np.prod(shape))
    self.assertTrue(np.all(lo <= result))
    self.assertTrue(np.all(result < hi))

  def testRngUniformS32(self):
    lo, hi = 2, 4
    shape = (2, 3)
    c = self._NewComputation()
    c.RngUniform(c.Constant(NumpyArrayS32(lo)), c.Constant(NumpyArrayS32(hi)),
                 dims=shape)
    result = c.Build().Compile().Execute()
    # since the result is random, we just check shape, integrality, and range
    self.assertEqual(result.shape, shape)
    self.assertEqual(result.dtype, np.int32)
    self.assertTrue(np.all(lo <= result))
    self.assertTrue(np.all(result < hi))


class EmbeddedComputationsTest(LocalComputationTest):
  """Tests for XLA graphs with embedded computations (such as maps)."""

  def _CreateConstantS32Computation(self):
    """Computation (f32) -> s32 that returns a constant 1 for any input."""
    c = self._NewComputation("constant_s32_one")
    # TODO (eliben): consider adding a nicer way to create new parameters without id:264 gh:265
    # having to create dummy Numpy arrays or populating Shape messages. Perhaps
    # we need our own (Python-client-own) way to represent Shapes conveniently.
    c.ParameterFromNumpy(NumpyArrayF32(0))
    c.ConstantS32Scalar(1)
    return c.Build()

  def _CreateConstantS64Computation(self):
    """Computation (f64) -> s64 that returns a constant 1 for any input."""
    c = self._NewComputation("constant_s64_one")
    # TODO (eliben): consider adding a nicer way to create new parameters without id:303 gh:304
    # having to create dummy Numpy arrays or populating Shape messages. Perhaps
    # we need our own (Python-client-own) way to represent Shapes conveniently.
    c.ParameterFromNumpy(NumpyArrayF64(0))
    c.ConstantS64Scalar(1)
    return c.Build()

  def _CreateConstantF32Computation(self):
    """Computation (f32) -> f32 that returns a constant 1.0 for any input."""
    c = self._NewComputation("constant_f32_one")
    c.ParameterFromNumpy(NumpyArrayF32(0))
    c.ConstantF32Scalar(1.0)
    return c.Build()

  def _CreateConstantF64Computation(self):
    """Computation (f64) -> f64 that returns a constant 1.0 for any input."""
    c = self._NewComputation("constant_f64_one")
    c.ParameterFromNumpy(NumpyArrayF64(0))
    c.ConstantF64Scalar(1.0)
    return c.Build()

  def _CreateMulF32By2Computation(self):
    """Computation (f32) -> f32 that multiplies its parameter by 2."""
    c = self._NewComputation("mul_f32_by2")
    c.Mul(c.ParameterFromNumpy(NumpyArrayF32(0)), c.ConstantF32Scalar(2.0))
    return c.Build()

  def _CreateMulF64By2Computation(self):
    """Computation (f64) -> f64 that multiplies its parameter by 2."""
    c = self._NewComputation("mul_f64_by2")
    c.Mul(c.ParameterFromNumpy(NumpyArrayF64(0)), c.ConstantF64Scalar(2.0))
    return c.Build()

  def _CreateBinaryAddF32Computation(self):
    """Computation (f32, f32) -> f32 that adds its two parameters."""
    c = self._NewComputation("add_param0_by_param1")
    c.Add(
        c.ParameterFromNumpy(NumpyArrayF32(0)),
        c.ParameterFromNumpy(NumpyArrayF32(0)))
    return c.Build()

  def _CreateBinaryAddF64Computation(self):
    """Computation (f64, f64) -> f64 that adds its two parameters."""
    c = self._NewComputation("add_param0_by_param1")
    c.Add(
        c.ParameterFromNumpy(NumpyArrayF64(0)),
        c.ParameterFromNumpy(NumpyArrayF64(0)))
    return c.Build()

  def _CreateBinaryDivF32Computation(self):
    """Computation (f32, f32) -> f32 that divides its two parameters."""
    c = self._NewComputation("div_param0_by_param1")
    c.Div(
        c.ParameterFromNumpy(NumpyArrayF32(0)),
        c.ParameterFromNumpy(NumpyArrayF32(0)))
    return c.Build()

  def _CreateBinaryDivF64Computation(self):
    """Computation (f64, f64) -> f64 that divides its two parameters."""
    c = self._NewComputation("div_param0_by_param1")
    c.Div(
        c.ParameterFromNumpy(NumpyArrayF64(0)),
        c.ParameterFromNumpy(NumpyArrayF64(0)))
    return c.Build()

  def _CreateTestF32Lt10Computation(self):
    """Computation (f32) -> bool that tests if its parameter is less than 10."""
    c = self._NewComputation("test_f32_lt_10")
    c.Lt(c.ParameterFromNumpy(NumpyArrayF32(0)), c.ConstantF32Scalar(10.))
    return c.Build()

  def _CreateTestF64Lt10Computation(self):
    """Computation (f64) -> bool that tests if its parameter is less than 10."""
    c = self._NewComputation("test_f64_lt_10")
    c.Lt(c.ParameterFromNumpy(NumpyArrayF64(0)), c.ConstantF64Scalar(10.))
    return c.Build()

  def _MakeSample3DArrayF32(self):
    return NumpyArrayF32([[[1, 2, 3], [4, 5, 6]], [[1, 2, 3], [4, 5, 6]],
                          [[1, 2, 3], [4, 5, 6]], [[1, 2, 3], [4, 5, 6]]])

  def _MakeSample3DArrayF64(self):
    return NumpyArrayF64([[[1, 2, 3], [4, 5, 6]], [[1, 2, 3], [4, 5, 6]],
                          [[1, 2, 3], [4, 5, 6]], [[1, 2, 3], [4, 5, 6]]])

  def testCallF32(self):
    c = self._NewComputation()
    c.Call(
        self._CreateMulF32By2Computation(),
        operands=(c.ConstantF32Scalar(5.0),))
    self._ExecuteAndCompareClose(c, expected=10.0)

  def testCallF64(self):
    c = self._NewComputation()
    c.Call(
        self._CreateMulF64By2Computation(),
        operands=(c.ConstantF64Scalar(5.0),))
    self._ExecuteAndCompareClose(c, expected=10.0)

  def testMapEachElementToS32Constant(self):
    c = self._NewComputation()
    c.Map([c.Constant(NumpyArrayF32([1.0, 2.0, 3.0, 4.0]))],
          self._CreateConstantS32Computation(), [0])
    self._ExecuteAndCompareExact(c, expected=[1, 1, 1, 1])

  def testMapEachElementToS64Constant(self):
    c = self._NewComputation()
    c.Map([c.Constant(NumpyArrayF64([1.0, 2.0, 3.0, 4.0]))],
          self._CreateConstantS64Computation(), [0])
    self._ExecuteAndCompareExact(c, expected=[1, 1, 1, 1])

  def testMapMulBy2F32(self):
    c = self._NewComputation()
    c.Map([c.Constant(NumpyArrayF32([1.0, 2.0, 3.0, 4.0]))],
          self._CreateMulF32By2Computation(), [0])
    self._ExecuteAndCompareClose(c, expected=[2.0, 4.0, 6.0, 8.0])

  def testMapMulBy2F64(self):
    c = self._NewComputation()
    c.Map([c.Constant(NumpyArrayF64([1.0, 2.0, 3.0, 4.0]))],
          self._CreateMulF64By2Computation(), [0])
    self._ExecuteAndCompareClose(c, expected=[2.0, 4.0, 6.0, 8.0])

  def testSimpleMapChainF32(self):
    # Chains a map of constant-f32 with a map of mul-by-2
    c = self._NewComputation()
    const_f32 = c.Map([c.Constant(NumpyArrayF32([1.0, 2.0, 3.0, 4.0]))],
                      self._CreateConstantF32Computation(), [0])
    c.Map([const_f32], self._CreateMulF32By2Computation(), [0])
    self._ExecuteAndCompareClose(c, expected=[2.0, 2.0, 2.0, 2.0])

  def testSimpleMapChainF64(self):
    # Chains a map of constant-f64 with a map of mul-by-2
    c = self._NewComputation()
    const_f64 = c.Map([c.Constant(NumpyArrayF64([1.0, 2.0, 3.0, 4.0]))],
                      self._CreateConstantF64Computation(), [0])
    c.Map([const_f64], self._CreateMulF64By2Computation(), [0])
    self._ExecuteAndCompareClose(c, expected=[2.0, 2.0, 2.0, 2.0])

  def testDivVectorsWithMapF32(self):
    c = self._NewComputation()
    c.Map((c.Constant(NumpyArrayF32([1.0, 2.0, 3.0, 4.0])),
           c.Constant(NumpyArrayF32([5.0, 5.0, 4.0, 4.0]))),
          self._CreateBinaryDivF32Computation(), [0])
    self._ExecuteAndCompareClose(c, expected=[0.2, 0.4, 0.75, 1.0])

  def testDivVectorsWithMapF64(self):
    c = self._NewComputation()
    c.Map((c.Constant(NumpyArrayF64([1.0, 2.0, 3.0, 4.0])),
           c.Constant(NumpyArrayF64([5.0, 5.0, 4.0, 4.0]))),
          self._CreateBinaryDivF64Computation(), [0])
    self._ExecuteAndCompareClose(c, expected=[0.2, 0.4, 0.75, 1.0])

  def testReduce1DtoScalarF32(self):
    c = self._NewComputation()
    c.Reduce(
        operand=c.Constant(NumpyArrayF32([1.0, 2.0, 3.0, 4.0])),
        init_value=c.ConstantF32Scalar(0),
        computation_to_apply=self._CreateBinaryAddF32Computation(),
        dimensions=[0])
    self._ExecuteAndCompareClose(c, expected=10)

  def testReduce1DtoScalarF64(self):
    c = self._NewComputation()
    c.Reduce(
        operand=c.Constant(NumpyArrayF64([1.0, 2.0, 3.0, 4.0])),
        init_value=c.ConstantF64Scalar(0),
        computation_to_apply=self._CreateBinaryAddF64Computation(),
        dimensions=[0])
    self._ExecuteAndCompareClose(c, expected=10)

  def testReduce2DTo1DDim0F32(self):
    input_array = NumpyArrayF32([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    c = self._NewComputation()
    c.Reduce(
        operand=c.Constant(input_array),
        init_value=c.ConstantF32Scalar(0),
        computation_to_apply=self._CreateBinaryAddF32Computation(),
        dimensions=[0])
    self._ExecuteAndCompareClose(c, expected=[5, 7, 9])

  def testReduce2DTo1DDim0F64(self):
    input_array = NumpyArrayF64([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    c = self._NewComputation()
    c.Reduce(
        operand=c.Constant(input_array),
        init_value=c.ConstantF64Scalar(0),
        computation_to_apply=self._CreateBinaryAddF64Computation(),
        dimensions=[0])
    self._ExecuteAndCompareClose(c, expected=[5, 7, 9])

  def testReduce2DTo1DDim1F32(self):
    input_array = NumpyArrayF32([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    c = self._NewComputation()
    c.Reduce(
        operand=c.Constant(input_array),
        init_value=c.ConstantF32Scalar(0),
        computation_to_apply=self._CreateBinaryAddF32Computation(),
        dimensions=[1])
    self._ExecuteAndCompareClose(c, expected=[6, 15])

  def testReduce2DTo1DDim1F64(self):
    input_array = NumpyArrayF64([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    c = self._NewComputation()
    c.Reduce(
        operand=c.Constant(input_array),
        init_value=c.ConstantF64Scalar(0),
        computation_to_apply=self._CreateBinaryAddF64Computation(),
        dimensions=[1])
    self._ExecuteAndCompareClose(c, expected=[6, 15])

  def testReduce3DAllPossibleWaysF32(self):
    input_array = self._MakeSample3DArrayF32()

    def _ReduceAndTest(*dims):
      c = self._NewComputation()
      c.Reduce(
          operand=c.Constant(input_array),
          init_value=c.ConstantF32Scalar(0),
          computation_to_apply=self._CreateBinaryAddF32Computation(),
          dimensions=dims)
      self._ExecuteAndCompareClose(
          c, expected=np.sum(input_array, axis=tuple(dims)))

    _ReduceAndTest(0)
    _ReduceAndTest(0)
    _ReduceAndTest(0, 1)
    _ReduceAndTest(0, 2)
    _ReduceAndTest(1, 2)
    _ReduceAndTest(0, 1, 2)

  def testReduce3DAllPossibleWaysF64(self):
    input_array = self._MakeSample3DArrayF64()

    def _ReduceAndTest(*dims):
      c = self._NewComputation()
      c.Reduce(
          operand=c.Constant(input_array),
          init_value=c.ConstantF64Scalar(0),
          computation_to_apply=self._CreateBinaryAddF64Computation(),
          dimensions=dims)
      self._ExecuteAndCompareClose(
          c, expected=np.sum(input_array, axis=tuple(dims)))

    _ReduceAndTest(0)
    _ReduceAndTest(0)
    _ReduceAndTest(0, 1)
    _ReduceAndTest(0, 2)
    _ReduceAndTest(1, 2)
    _ReduceAndTest(0, 1, 2)

  def testWhileF32(self):
    cond = self._CreateTestF32Lt10Computation()
    body = self._CreateMulF32By2Computation()
    c = self._NewComputation()
    init = c.ConstantF32Scalar(1.)
    c.While(cond, body, init)
    self._ExecuteAndCompareClose(c, expected=16.)

  def testWhileF64(self):
    cond = self._CreateTestF64Lt10Computation()
    body = self._CreateMulF64By2Computation()
    c = self._NewComputation()
    init = c.ConstantF64Scalar(1.)
    c.While(cond, body, init)
    self._ExecuteAndCompareClose(c, expected=16.)

  def testInfeedS32Values(self):
    to_infeed = NumpyArrayS32([1, 2, 3, 4])
    c = self._NewComputation()
    c.Infeed(xla_client.Shape.from_numpy(to_infeed[0]))
    compiled_c = c.Build().CompileWithExampleArguments()
    for item in to_infeed:
      xla_client.transfer_to_infeed(item)

    for item in to_infeed:
      result = compiled_c.Execute()
      self.assertEqual(result, item)


class ErrorTest(LocalComputationTest):

  def setUp(self):
    self.f32_scalar_2 = NumpyArrayF32(2.0)
    self.s32_scalar_2 = NumpyArrayS32(2)

  def testInvokeWithWrongElementType(self):
    c = self._NewComputation()
    c.ParameterFromNumpy(self.s32_scalar_2)
    self.assertRaisesRegexp(
        RuntimeError, r"invalid argument shape.*expected s32\[\], got f32\[\]",
        lambda: c.Build().CompileWithExampleArguments([self.f32_scalar_2]))


if __name__ == "__main__":
  unittest.main()
