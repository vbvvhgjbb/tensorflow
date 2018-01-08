/* Copyright 2016 The TensorFlow Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/

#include "tensorflow/core/framework/common_shape_fns.h"
#include "tensorflow/core/framework/op.h"
#include "tensorflow/core/framework/shape_inference.h"

namespace tensorflow {

using shape_inference::InferenceContext;
using shape_inference::ShapeHandle;

// TODO (ringwalt): Add a "fill_mode" argument with "constant", "mirror", etc. id:972 gh:973
// TODO (ringwalt): Add a "fill_constant" argument for constant mode (default 0). id:889 gh:890
// TODO (ringwalt): Add an "output_shape" argument. This is sufficient to id:684 gh:685
// implement "same" and "valid" modes in the Python function.
REGISTER_OP("ImageProjectiveTransform")
    .Input("images: dtype")
    .Input("transforms: float32")
    .Attr("dtype: {uint8, int32, int64, float32, float64}")
    .Attr("interpolation: string")
    .Output("transformed_images: dtype")
    .SetShapeFn([](InferenceContext* c) {
      c->set_output(0, c->input(0));
      return Status::OK();
    })
    .Doc(R"doc(
Applies the given transform to each of the images.

Input `image` is a `Tensor` in NHWC format (where the axes are image in batch,
rows, columns, and channels. Input `transforms` is a num_images x 8 or 1 x 8
matrix, where each row corresponds to a 3 x 3 projective transformation matrix,
with the last entry assumed to be 1. If there is one row, the same
transformation will be applied to all images.

If one row of `transforms` is `[a0, a1, a2, b0, b1, b2, c0, c1]`, then it maps
the *output* point `(x, y)` to a transformed *input* point
`(x', y') = ((a0 x + a1 y + a2) / k, (b0 x + b1 y + b2) / k)`, where
`k = c0 x + c1 y + 1`. If the transformed point lays outside of the input
image, the output pixel is set to 0. The output is the same size as the input,

images: 4D `Tensor`, input image(s) in NHWC format.
transforms: 2D `Tensor`, projective transform(s) to apply to the image(s).

transformed_images: 4D `Tensor`, image(s) in NHWC format, generated by applying
the `transforms` to the `images`. Satisfies the description above.
)doc");

REGISTER_OP("BipartiteMatch")
    .Input("distance_mat: float")
    .Input("num_valid_rows: float")
    .Attr("top_k: int = -1")
    .Output("row_to_col_match_indices: int32")
    .Output("col_to_row_match_indices: int32")
    .SetIsStateful()
    .SetShapeFn([](InferenceContext* c) {
      ShapeHandle input;
      TF_RETURN_IF_ERROR(c->WithRank(c->input(0), 2, &input));
      c->set_output(0, c->MakeShape({c->Dim(input, 0)}));
      c->set_output(1, c->MakeShape({c->Dim(input, 1)}));
      return Status::OK();
    })
    .Doc(R"doc(
Find bipartite matching based on a given distance matrix.

A greedy bi-partite matching algorithm is used to obtain the matching with the
(greedy) minimum distance.

distance_mat: A 2-D float tensor of shape `[num_rows, num_columns]`. It is a
  pair-wise distance matrix between the entities represented by each row and
  each column. It is an asymmetric matrix. The smaller the distance is, the more
  similar the pairs are. The bipartite matching is to minimize the distances.
num_valid_rows: A scalar or a 1-D tensor with one element describing the
  number of valid rows of distance_mat to consider for the bipartite matching.
  If set to be negative, then all rows from `distance_mat` are used.
top_k: A scalar that specifies the number of top-k matches to retrieve.
  If set to be negative, then is set according to the maximum number of
  matches from `distance_mat`.
row_to_col_match_indices: A vector of length num_rows, which is the number of
  rows of the input `distance_matrix`.
  If `row_to_col_match_indices[i]` is not -1, row i is matched to column
  `row_to_col_match_indices[i]`.
col_to_row_match_indices: A vector of length num_columns, which is the number
  of columns of the input ditance matrix.
  If `col_to_row_match_indices[j]` is not -1, column j is matched to row
  `col_to_row_match_indices[j]`.
)doc");

}  // namespace tensorflow
