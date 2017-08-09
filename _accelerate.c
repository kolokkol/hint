#include "Python.h"

/* This module provides C implementations for the most heavy
operations in the hint package.

Currently the following functions/operations are defined in C code:
	- Computing Lenenshtein distance
*/


/* We need to find the minimum of 3 integer values;
This can be done easily using a function returning the minimum
of 2 integers, sinc min(a, b, c) == min(min(a, b), c) */
#define _MIN(x, y) (x) < (y) ? (x) : (y)

int minimum(int a, int b, int c) {
	return _MIN(_MIN(a, b), c);
}


static PyObject *levenshtein_distance(PyObject *self, PyObject *args) {
	/* Function takes two string arguments */
	PyObject *a;
	PyObject *b;
	if (!PyArg_ParseTuple(args, "OO", &a, &b)) {
		return NULL;
	}

	/* PyArg_ParseTuple does not increase the reference count for
	the passed PyObject; It's our responsibility to do so. */
	Py_INCREF(a);
	Py_INCREF(b);

	/* Type-check the PyObject*/
	if (!(PyUnicode_CheckExact(a) && PyUnicode_CheckExact(b))) {
		PyErr_SetString(PyExc_TypeError, "Expected two strings");
		/* Decrease/re-set reference count */
		Py_DECREF(a);
		Py_DECREF(b);
		return NULL; 	/* Indicate an exception has occurred */
	}

	Py_ssize_t size_a = PyUnicode_GetLength(a);
	Py_ssize_t size_b = PyUnicode_GetLength(b);

	/* Some allocation magic
	NOTE: The matrix has actual size DIM1 x DIM2,
	thus, use size_a + 1 and size_b + 1. Doing otherwise
	will cause the calls to free to fail. */
	int **d = malloc(sizeof(int *) * (size_a + 1));
	for (int i = 0; i <= size_a; i++) {
		d[i]/*e*/ = malloc(sizeof(int) * (size_b + 1));
	}

	/* Set all fields to 0 */
	for (int i = 0; i <= size_a; i++) {
		for (int j = 0; j <= size_b; j++) {
			d[i][j] = 0;
		}
	}

	/* Start algorithm */
	for (int i = 1; i <= size_a; i++) {
		d[i][0] = i;
	}

	for (int j = 1; j <= size_b; j++) {
		d[0][j] = j;
	}

	/* Some magic to make indexing as fast as possible */
	void *raw_a = PyUnicode_DATA(a);
	void *raw_b = PyUnicode_DATA(b);
	int kind_a = PyUnicode_KIND(a);
	int kind_b = PyUnicode_KIND(b);
	for (int j = 1; j <= size_b; j++) {
		for (int i = 1; i <= size_a; i++) {
			int cost = PyUnicode_READ(kind_a, raw_a, i-1) == PyUnicode_READ(kind_b, raw_b, j-1) ? 0 : 1;
			d[i][j] = minimum(d[i-1][j]+1, d[i][j-1]+1, d[i-1][j-1]+cost);
		}
	}

	/* Save result since we'll have to cleanup the matrix */
	int result = d[size_a][size_b];

	/* Free memory used for matrix */
	for (int i = 0; i <= size_a; i++) {
		free(d[i]);
	}
	free(d);

	/* Decref */
	Py_DECREF(a);
	Py_DECREF(b);

	return PyLong_FromLong(result);
}

/* Export */
static PyMethodDef AccelerationFunctions[] = {
	{"ldist", levenshtein_distance, METH_VARARGS, "Compute levenshtein distance"},
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef acceleration_module = {
	PyModuleDef_HEAD_INIT,
	"_acceleration",
	NULL,
	-1,
	AccelerationFunctions
};

PyMODINIT_FUNC PyInit__accelerate(void) {
	return PyModule_Create(&acceleration_module);
}
