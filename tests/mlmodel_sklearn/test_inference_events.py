# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

import numpy as np
import pandas
from testing_support.fixtures import (
    override_application_settings,
    reset_core_stats_engine,
)
from testing_support.validators.validate_ml_event_count import validate_ml_event_count
from testing_support.validators.validate_ml_events import validate_ml_events

from newrelic.api.background_task import background_task

pandas_df_category_recorded_custom_events = [
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "feature_name": "col1",
            "feature_type": "categorical",
            "feature_value": "2.0",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "feature_name": "col2",
            "feature_type": "categorical",
            "feature_value": "4.0",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "label_name": "0",
            "label_type": "numeric",
            "label_value": "27.0",
        },
    ),
]


@reset_core_stats_engine()
def test_pandas_df_categorical_feature_event():
    @validate_ml_events(pandas_df_category_recorded_custom_events)
    @validate_ml_event_count(count=3)
    @background_task()
    def _test():
        import sklearn.tree

        clf = getattr(sklearn.tree, "DecisionTreeClassifier")(random_state=0)
        model = clf.fit(
            pandas.DataFrame({"col1": [27.0, 24.0], "col2": [23.0, 25.0]}, dtype="category"),
            pandas.DataFrame({"label": [27.0, 28.0]}),
        )

        labels = model.predict(pandas.DataFrame({"col1": [2.0], "col2": [4.0]}, dtype="category"))
        return model

    _test()


label_type = "bool" if sys.version_info < (3, 8) else "numeric"
true_label_value = "True" if sys.version_info < (3, 8) else "1.0"
false_label_value = "False" if sys.version_info < (3, 8) else "0.0"
pandas_df_bool_recorded_custom_events = [
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "feature_name": "col1",
            "feature_type": "bool",
            "feature_value": "True",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "feature_name": "col2",
            "feature_type": "bool",
            "feature_value": "True",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "label_name": "0",
            "label_type": label_type,
            "label_value": true_label_value,
        },
    ),
]


@reset_core_stats_engine()
def test_pandas_df_bool_feature_event():
    @validate_ml_events(pandas_df_bool_recorded_custom_events)
    @validate_ml_event_count(count=3)
    @background_task()
    def _test():
        import sklearn.tree

        dtype_name = "bool" if sys.version_info < (3, 8) else "boolean"
        x_train = pandas.DataFrame({"col1": [True, False], "col2": [True, False]}, dtype=dtype_name)
        y_train = pandas.DataFrame({"label": [True, False]}, dtype=dtype_name)
        x_test = pandas.DataFrame({"col1": [True], "col2": [True]}, dtype=dtype_name)

        clf = getattr(sklearn.tree, "DecisionTreeClassifier")(random_state=0)
        model = clf.fit(x_train, y_train)

        labels = model.predict(x_test)
        return model

    _test()


pandas_df_float_recorded_custom_events = [
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeRegressor",
            "model_version": "0.0.0",
            "feature_name": "col1",
            "feature_type": "numeric",
            "feature_value": "100.0",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeRegressor",
            "model_version": "0.0.0",
            "feature_name": "col2",
            "feature_type": "numeric",
            "feature_value": "300.0",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeRegressor",
            "model_version": "0.0.0",
            "label_name": "0",
            "label_type": "numeric",
            "label_value": "345.6",
        },
    ),
]


@reset_core_stats_engine()
def test_pandas_df_float_feature_event():
    @validate_ml_events(pandas_df_float_recorded_custom_events)
    @validate_ml_event_count(count=3)
    @background_task()
    def _test():
        import sklearn.tree

        x_train = pandas.DataFrame({"col1": [120.0, 254.0], "col2": [236.9, 234.5]}, dtype="float64")
        y_train = pandas.DataFrame({"label": [345.6, 456.7]}, dtype="float64")
        x_test = pandas.DataFrame({"col1": [100.0], "col2": [300.0]}, dtype="float64")

        clf = getattr(sklearn.tree, "DecisionTreeRegressor")(random_state=0)

        model = clf.fit(x_train, y_train)
        labels = model.predict(x_test)

        return model

    _test()


int_list_recorded_custom_events = [
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "ExtraTreeRegressor",
            "model_version": "0.0.0",
            "feature_name": "0",
            "feature_type": "numeric",
            "feature_value": "1",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "ExtraTreeRegressor",
            "model_version": "0.0.0",
            "feature_name": "1",
            "feature_type": "numeric",
            "feature_value": "2",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "ExtraTreeRegressor",
            "model_version": "0.0.0",
            "label_name": "0",
            "label_type": "numeric",
            "label_value": "1.0",
        },
    ),
]


@reset_core_stats_engine()
def test_int_list():
    @validate_ml_events(int_list_recorded_custom_events)
    @validate_ml_event_count(count=3)
    @background_task()
    def _test():
        import sklearn.tree

        x_train = [[0, 0], [1, 1]]
        y_train = [0, 1]
        x_test = [[1, 2]]

        clf = getattr(sklearn.tree, "ExtraTreeRegressor")(random_state=0)
        model = clf.fit(x_train, y_train)

        labels = model.predict(x_test)
        return model

    _test()


numpy_int_recorded_custom_events = [
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "ExtraTreeRegressor",
            "model_version": "0.0.0",
            "feature_name": "0",
            "feature_type": "numeric",
            "feature_value": "12",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "ExtraTreeRegressor",
            "model_version": "0.0.0",
            "feature_name": "1",
            "feature_type": "numeric",
            "feature_value": "13",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "ExtraTreeRegressor",
            "model_version": "0.0.0",
            "label_name": "0",
            "label_type": "numeric",
            "label_value": "11.0",
        },
    ),
]


@reset_core_stats_engine()
def test_numpy_int_array():
    @validate_ml_events(numpy_int_recorded_custom_events)
    @validate_ml_event_count(count=3)
    @background_task()
    def _test():
        import sklearn.tree

        x_train = np.array([[10, 10], [11, 11]], dtype="int")
        y_train = np.array([10, 11], dtype="int")
        x_test = np.array([[12, 13]], dtype="int")

        clf = getattr(sklearn.tree, "ExtraTreeRegressor")(random_state=0)
        model = clf.fit(x_train, y_train)

        labels = model.predict(x_test)
        return model

    _test()


numpy_str_recorded_custom_events = [
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "feature_name": "0",
            "feature_type": "str",
            "feature_value": "20",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "feature_name": "1",
            "feature_type": "str",
            "feature_value": "21",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "feature_name": "0",
            "feature_type": "str",
            "feature_value": "22",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "feature_name": "1",
            "feature_type": "str",
            "feature_value": "23",
        },
    ),
]


@reset_core_stats_engine()
def test_numpy_str_array_multiple_features():
    @validate_ml_events(numpy_str_recorded_custom_events)
    @validate_ml_event_count(count=6)
    @background_task()
    def _test():
        import sklearn.tree

        x_train = np.array([[20, 20], [21, 21]], dtype="<U4")
        y_train = np.array([20, 21], dtype="<U4")
        x_test = np.array([[20, 21], [22, 23]], dtype="<U4")
        clf = getattr(sklearn.tree, "DecisionTreeClassifier")(random_state=0)

        model = clf.fit(x_train, y_train)
        labels = model.predict(x_test)

        return model

    _test()


numpy_str_recorded_custom_events_no_value = [
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "feature_name": "0",
            "feature_type": "str",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "feature_name": "1",
            "feature_type": "str",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "DecisionTreeClassifier",
            "model_version": "0.0.0",
            "label_name": "0",
            "label_type": "str",
        },
    ),
]


@reset_core_stats_engine()
@override_application_settings({"machine_learning.inference_events_value.enabled": False})
def test_does_not_include_value_when_inference_event_value_enabled_is_false():
    @validate_ml_events(numpy_str_recorded_custom_events_no_value)
    @validate_ml_event_count(count=3)
    @background_task()
    def _test():
        import sklearn.tree

        x_train = np.array([[20, 20], [21, 21]], dtype="<U4")
        y_train = np.array([20, 21], dtype="<U4")
        x_test = np.array([[20, 21]], dtype="<U4")
        clf = getattr(sklearn.tree, "DecisionTreeClassifier")(random_state=0)

        model = clf.fit(x_train, y_train)
        labels = model.predict(x_test)

        return model

    _test()


@reset_core_stats_engine()
@override_application_settings({"ml_insights_events.enabled": False})
def test_does_not_include_events_when_ml_insights_events_enabled_is_false():
    """
    Verifies that all ml events can be disabled by setting
    custom_insights_events.enabled.
    """

    @validate_ml_event_count(count=0)
    @background_task()
    def _test():
        import sklearn.tree

        x_train = np.array([[20, 20], [21, 21]], dtype="<U4")
        y_train = np.array([20, 21], dtype="<U4")
        x_test = np.array([[20, 21]], dtype="<U4")
        clf = getattr(sklearn.tree, "DecisionTreeClassifier")(random_state=0)

        model = clf.fit(x_train, y_train)
        labels = model.predict(x_test)

        return model

    _test()


@reset_core_stats_engine()
@override_application_settings({"machine_learning.enabled": False})
def test_does_not_include_events_when_machine_learning_enabled_is_false():
    @validate_ml_event_count(count=0)
    @background_task()
    def _test():
        import sklearn.tree

        x_train = np.array([[20, 20], [21, 21]], dtype="<U4")
        y_train = np.array([20, 21], dtype="<U4")
        x_test = np.array([[20, 21]], dtype="<U4")
        clf = getattr(sklearn.tree, "DecisionTreeClassifier")(random_state=0)

        model = clf.fit(x_train, y_train)
        labels = model.predict(x_test)

        return model

    _test()


multilabel_output_label_events = [
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "MultiOutputClassifier",
            "model_version": "0.0.0",
            "label_name": "0",
            "label_type": "numeric",
            "label_value": "1",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "MultiOutputClassifier",
            "model_version": "0.0.0",
            "label_name": "1",
            "label_type": "numeric",
            "label_value": "0",
        },
    ),
    (
        {"type": "InferenceData"},
        {
            "inference_id": None,
            "modelName": "MultiOutputClassifier",
            "model_version": "0.0.0",
            "label_name": "2",
            "label_type": "numeric",
            "label_value": "1",
        },
    ),
]


@reset_core_stats_engine()
def test_custom_event_count_multilabel_output():
    @validate_ml_events(multilabel_output_label_events)
    # The expected count of 23 comes from 20 feature events + 3 label events to be generated
    @validate_ml_event_count(count=23)
    @background_task()
    def _test():
        from sklearn.datasets import make_multilabel_classification
        from sklearn.linear_model import LogisticRegression
        from sklearn.multioutput import MultiOutputClassifier

        x_train, y_train = make_multilabel_classification(n_classes=3, random_state=0)
        clf = MultiOutputClassifier(LogisticRegression()).fit(x_train, y_train)
        clf.predict([x_train[-1]])

    _test()