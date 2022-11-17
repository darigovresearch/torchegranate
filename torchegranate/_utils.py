# _utils.py
# Jacob Schreiber <jmschreiber91@gmail.com>

import numpy
import torch


eps = torch.finfo(torch.float32).eps


def _cast_as_tensor(value, dtype=None):
	"""Set the parameter.""" 

	if value is None:
		return None

	if isinstance(value, (torch.nn.Parameter, torch.Tensor)):
		if dtype is None:
			return value
		elif value.dtype == dtype:
			return value
		else:
			return value.type(dtype)

	if isinstance(value, (float, int, list, tuple, numpy.ndarray)):
		if dtype is None:
			return torch.tensor(value)
		else:
			return torch.tensor(value, dtype=dtype)


def _update_parameter(value, new_value, inertia=0.0, frozen=None):
	"""Update a parameters unles.
	"""

	if hasattr(value, "frozen") and getattr(value, "frozen") == True:
		return

	value[:] = inertia*value + (1-inertia)*new_value


def _check_parameter(parameter, name, min_value=None, max_value=None, 
	value_sum=None, value_set=None, dtypes=None, ndim=None, shape=None,
	epsilon=1e-6):
	"""Ensures that the parameter falls within a valid range.

	This check accepts several optional conditions that can be used to ensure
	that the value has the desired properties. If these conditions are set to
	`None`, they are not checked. 

	Note: `parameter` can be a single value or it can be a whole tensor/array
	of values. These checks are run either against the entire tensor, e.g.
	ndims, or against each of the values in the parameter.

	
	Parameters
	----------
	parameter: anything
		The parameter meant to be checked

	name: str
		The name of the parameter for error logging purposes.

	min_value: float or None, optional
		The minimum numeric value that any values in the parameter can take.
		Default is None.

	max_value: float or None, optional
		The maximum numeric value that any values in the parameter can take.
		Default is None.

	value_sum: float or None, optional
		The approximate sum, within eps, of the parameter. Default is None.

	value_set: tuple or list or set or None, optional
		The set of values that each element in the parameter can take. Default
		is None.

	dtypes: tuple or list or set or None, optional
		The set of dtypes that the parameter can take. Default is None.

	ndim: int or None, optional
		The number of dimensions of the tensor. Should not be used when the
		parameter is a single value. Default is None.

	shape: tuple or None, optional
		The shape of the parameter. -1 can be used to accept any value for that
		dimension.

	epsilon: float, optional
		When using `value_sum`, this is the maximum difference acceptable.
		Default is 1e-6.
	"""

	vector = (numpy.ndarray, torch.Tensor, torch.nn.Parameter)

	if parameter is None:
		return None

	if dtypes is not None:
		if isinstance(parameter, vector):
			if parameter.dtype not in dtypes:
				raise ValueError("Parameter {} dtype must be one of {}".format(
					name, dtypes))
		else:
			if type(parameter) not in dtypes:
				raise ValueError("Parameter {} dtype must be one of {}".format(
					name, dtypes))


	if min_value is not None:
		if isinstance(parameter, vector):
			if (parameter < min_value).sum() > 0:
				raise ValueError("Parameter {} must have a minimum value above"
					" {}".format(name, min_value))
		else:
			if parameter < min_value:
				raise ValueError("Parameter {} must have a minimum value above"
					" {}".format(name, min_value))


	if max_value is not None:
		if isinstance(parameter, vector):
			if (parameter > max_value).sum() > 0:
				raise ValueError("Parameter {} must have a maximum value below"
					" {}".format(name, max_value))
		else:
			if parameter > max_value:
				raise ValueError("Parameter {} must have a maximum value below"
					" {}".format(name, max_value))


	if value_sum is not None:
		if isinstance(parameter, vector):
			if torch.abs(torch.sum(parameter) - value_sum) > epsilon:
				raise ValueError("Parameter {} must sum to {}".format(name, 
					value_sum))
		else:
			if abs(parameter - value_sum) > epsilon:
				raise ValueError("Parameter {} must sum to {}".format(name, 
					value_sum))


	if value_set is not None:
		if isinstance(parameter, vector):
			if (~numpy.isin(parameter, value_set)).sum() > 0:
				raise ValueError("Parameter {} must contain values in set"
					" {}".format(name, value_set))
		else:
			if parameter not in value_set:
				raise ValueError("Parameter {} must contain values in set"
					" {}".format(name, value_set))


	if ndim is not None:
		if isinstance(parameter, vector):
			if len(parameter.shape) != ndim:
				raise ValueError("Parameter {} must have {} dims".format(
					name, ndim))
		else:
			if ndim != 0:
				raise ValueError("Parameter {} must have {} dims".format(
					name, ndim))

	if shape is not None:
		if isinstance(parameter, vector):
			if len(parameter.shape) != len(shape):
				raise ValueError("Parameter {} must have shape {}".format(
					name, shape))

			for i in range(len(shape)):
				if shape[i] != -1 and shape[i] != parameter.shape[i]:
					raise ValueError("Parameter {} must have shape {}".format(
						name, shape))

	return parameter


def _check_shapes(parameters, names):
	n = len(parameters)

	for i in range(n):
		for j in range(n):
			if parameters[i] is None:
				continue

			if parameters[j] is None:
				continue

			n1, n2 = names[i], names[j]
			if len(parameters[i]) != len(parameters[j]):
				raise ValueError("Parameters {} and {} must be the same "
					"shape.".format(names[i], names[j]))


def _reshape_weights(X, sample_weight):
	"""Handle a sample weight tensor by creating and reshaping it.

	This function will take any weight input, including None, 1D weights, and
	2D weights, and shape it into a 2D matrix with the same shape as the data
	X also passed in.

	Both elements must be PyTorch tensors.


	Parameters
	----------
	X: torch.tensor, ndims=2
		The data being weighted. The contents of this tensor are not used, only
		the shape is.

	sample_weight: torch.tensor or None
		The weight for each element in the data or None.


	Returns
	-------
	sample_weight: torch.tensor, shape=X.shape
		A tensor with the same dimensions as X with elements repeated as
		necessary.
	"""

	if sample_weight is None:
		sample_weight = torch.ones(*X.shape)
	elif len(sample_weight.shape) == 1: 
		sample_weight = sample_weight.reshape(-1, 1).expand(-1, X.shape[1])
	elif sample_weight.shape[1] == 1:
		sample_weight = sample_weight.expand(-1, X.shape[1])

	_check_parameter(sample_weight, "sample_weight", min_value=0, 
		shape=X.shape, ndim=2)

	return sample_weight