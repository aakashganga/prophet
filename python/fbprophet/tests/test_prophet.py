# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant 
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import numpy as np
import pandas as pd

# fb-block 1 start
from unittest import TestCase
from fbprophet import Prophet
# fb-block 1 end
# fb-block 2

class TestProphet(TestCase):
    def test_load_models(self):
        forecaster = Prophet()
        forecaster.get_linear_model()
        forecaster.get_logistic_model()

    def test_fit_predict(self):
        N = DATA.shape[0]
        train = DATA.head(N // 2)
        future = DATA.tail(N // 2)

        forecaster = Prophet()
        forecaster.fit(train)
        forecaster.predict(future)

    def test_fit_predict_no_seasons(self):
        N = DATA.shape[0]
        train = DATA.head(N // 2)
        future = DATA.tail(N // 2)

        forecaster = Prophet(weekly_seasonality=False, yearly_seasonality=False)
        forecaster.fit(train)
        forecaster.predict(future)

    def test_fit_predict_no_changepoints(self):
        N = DATA.shape[0]
        train = DATA.head(N // 2)
        future = DATA.tail(N // 2)

        forecaster = Prophet(n_changepoints=0)
        forecaster.fit(train)
        forecaster.predict(future)

    def test_setup_dataframe(self):
        m = Prophet()
        N = DATA.shape[0]
        history = DATA.head(N // 2).copy()

        history = m.setup_dataframe(history, initialize_scales=True)

        self.assertTrue('t' in history)
        self.assertEqual(history['t'].min(), 0.0)
        self.assertEqual(history['t'].max(), 1.0)

        self.assertTrue('y_scaled' in history)
        self.assertEqual(history['y_scaled'].max(), 1.0)

    def test_get_changepoints(self):
        m = Prophet()
        N = DATA.shape[0]
        history = DATA.head(N // 2).copy()

        history = m.setup_dataframe(history, initialize_scales=True)
        m.history = history

        m.set_changepoints()

        cp = m.get_changepoint_indexes()
        self.assertEqual(cp.shape[0], m.n_changepoints)
        self.assertEqual(len(cp.shape), 1)
        self.assertTrue(cp.min() > 0)
        self.assertTrue(cp.max() < N)

        mat = m.get_changepoint_matrix()
        self.assertEqual(mat.shape[0], N // 2)
        self.assertEqual(mat.shape[1], m.n_changepoints)

    def test_get_zero_changepoints(self):
        m = Prophet(n_changepoints=0)
        N = DATA.shape[0]
        history = DATA.head(N // 2).copy()

        history = m.setup_dataframe(history, initialize_scales=True)
        m.history = history

        m.set_changepoints()
        cp = m.get_changepoint_indexes()
        self.assertEqual(cp.shape[0], 1)
        self.assertEqual(cp[0], 0)

        mat = m.get_changepoint_matrix()
        self.assertEqual(mat.shape[0], N // 2)
        self.assertEqual(mat.shape[1], 1)

    def test_fourier_series_weekly(self):
        mat = Prophet.fourier_series(DATA['ds'], 7, 3)
        # These are from the R forecast package directly.
        true_values = np.array([
            0.7818315, 0.6234898, 0.9749279, -0.2225209, 0.4338837, -0.9009689,
        ])
        self.assertAlmostEqual(np.sum((mat[0] - true_values)**2), 0.0)

    def test_fourier_series_yearly(self):
        mat = Prophet.fourier_series(DATA['ds'], 365.25, 3)
        # These are from the R forecast package directly.
        true_values = np.array([
            0.7006152, -0.7135393, -0.9998330, 0.01827656, 0.7262249, 0.6874572,
        ])
        self.assertAlmostEqual(np.sum((mat[0] - true_values)**2), 0.0)

    def test_growth_init(self):
        model = Prophet(growth='logistic')
        history = DATA.copy()
        history['cap'] = history['y'].max()

        history = model.setup_dataframe(history, initialize_scales=True)

        k, m = model.linear_growth_init(history)
        self.assertAlmostEqual(k, 0.3055671)
        self.assertAlmostEqual(m, 0.5307511)

        k, m = model.logistic_growth_init(history)

        self.assertAlmostEqual(k, 1.507925, places=4)
        self.assertAlmostEqual(m, -0.08167497, places=4)

    def test_piecewise_linear(self):
        model = Prophet()

        t = np.arange(11.)
        m = 0
        k = 1.0
        deltas = np.array([0.5])
        changepoint_ts = np.array([5])

        y = model.piecewise_linear(t, deltas, k, m, changepoint_ts)
        y_true = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0,
                           6.5, 8.0, 9.5, 11.0, 12.5])
        self.assertEqual((y - y_true).sum(), 0.0)

        t = t[8:]
        y_true = y_true[8:]
        y = model.piecewise_linear(t, deltas, k, m, changepoint_ts)
        self.assertEqual((y - y_true).sum(), 0.0)

    def test_piecewise_logistic(self):
        model = Prophet()

        t = np.arange(11.)
        cap = np.ones(11) * 10
        m = 0
        k = 1.0
        deltas = np.array([0.5])
        changepoint_ts = np.array([5])

        y = model.piecewise_logistic(t, cap, deltas, k, m, changepoint_ts)
        y_true = np.array([5.000000, 7.310586, 8.807971, 9.525741, 9.820138,
                           9.933071, 9.984988, 9.996646, 9.999252, 9.999833,
                           9.999963])
        self.assertAlmostEqual((y - y_true).sum(), 0.0, places=5)

        t = t[8:]
        y_true = y_true[8:]
        cap = cap[8:]
        y = model.piecewise_logistic(t, cap, deltas, k, m, changepoint_ts)
        self.assertAlmostEqual((y - y_true).sum(), 0.0, places=5)

    def test_holidays(self):
        holidays = pd.DataFrame({
            'ds': pd.to_datetime(['2016-12-25']),
            'holiday': ['xmas'],
            'lower_window': [-1],
            'upper_window': [0],
        })
        model = Prophet(holidays=holidays)
        df = pd.DataFrame({
            'ds': pd.date_range('2016-12-20', '2016-12-31')
        })
        feats = model.make_holiday_features(df['ds'])
        # 11 columns generated even though only 8 overlap
        self.assertEqual(feats.shape, (df.shape[0], 2))
        self.assertEqual((feats.sum(0) - np.array([1.0, 1.0])).sum(), 0)

        holidays = pd.DataFrame({
            'ds': pd.to_datetime(['2016-12-25']),
            'holiday': ['xmas'],
            'lower_window': [-1],
            'upper_window': [10],
        })
        feats = Prophet(holidays=holidays).make_holiday_features(df['ds'])
        # 12 columns generated even though only 8 overlap
        self.assertEqual(feats.shape, (df.shape[0], 12))

    def test_fit_with_holidays(self):
        holidays = pd.DataFrame({
            'ds': pd.to_datetime(['2012-06-06', '2013-06-06']),
            'holiday': ['seans-bday'] * 2,
            'lower_window': [0] * 2,
            'upper_window': [1] * 2,
        })
        model = Prophet(holidays=holidays, uncertainty_samples=0)
        model.fit(DATA).predict()

DATA = pd.read_csv(StringIO("""
ds,y
2012-05-18,38.23
2012-05-21,34.03
2012-05-22,31.0
2012-05-23,32.0
2012-05-24,33.03
2012-05-25,31.91
2012-05-29,28.84
2012-05-30,28.19
2012-05-31,29.6
2012-06-01,27.72
2012-06-04,26.9
2012-06-05,25.87
2012-06-06,26.81
2012-06-07,26.31
2012-06-08,27.1
2012-06-11,27.01
2012-06-12,27.4
2012-06-13,27.27
2012-06-14,28.29
2012-06-15,30.01
2012-06-18,31.41
2012-06-19,31.91
2012-06-20,31.6
2012-06-21,31.84
2012-06-22,33.05
2012-06-25,32.06
2012-06-26,33.1
2012-06-27,32.23
2012-06-28,31.36
2012-06-29,31.1
2012-07-02,30.77
2012-07-03,31.2
2012-07-05,31.47
2012-07-06,31.73
2012-07-09,32.17
2012-07-10,31.47
2012-07-11,30.97
2012-07-12,30.81
2012-07-13,30.72
2012-07-16,28.25
2012-07-17,28.09
2012-07-18,29.11
2012-07-19,29.0
2012-07-20,28.76
2012-07-23,28.75
2012-07-24,28.45
2012-07-25,29.34
2012-07-26,26.85
2012-07-27,23.71
2012-07-30,23.15
2012-07-31,21.71
2012-08-01,20.88
2012-08-02,20.04
2012-08-03,21.09
2012-08-06,21.92
2012-08-07,20.72
2012-08-08,20.72
2012-08-09,21.01
2012-08-10,21.81
2012-08-13,21.6
2012-08-14,20.38
2012-08-15,21.2
2012-08-16,19.87
2012-08-17,19.05
2012-08-20,20.01
2012-08-21,19.16
2012-08-22,19.44
2012-08-23,19.44
2012-08-24,19.41
2012-08-27,19.15
2012-08-28,19.34
2012-08-29,19.1
2012-08-30,19.09
2012-08-31,18.06
2012-09-04,17.73
2012-09-05,18.58
2012-09-06,18.96
2012-09-07,18.98
2012-09-10,18.81
2012-09-11,19.43
2012-09-12,20.93
2012-09-13,20.71
2012-09-14,22.0
2012-09-17,21.52
2012-09-18,21.87
2012-09-19,23.29
2012-09-20,22.59
2012-09-21,22.86
2012-09-24,20.79
2012-09-25,20.28
2012-09-26,20.62
2012-09-27,20.32
2012-09-28,21.66
2012-10-01,21.99
2012-10-02,22.27
2012-10-03,21.83
2012-10-04,21.95
2012-10-05,20.91
2012-10-08,20.4
2012-10-09,20.23
2012-10-10,19.64
2012-10-11,19.75
2012-10-12,19.52
2012-10-15,19.52
2012-10-16,19.48
2012-10-17,19.88
2012-10-18,18.98
2012-10-19,19.0
2012-10-22,19.32
2012-10-23,19.5
2012-10-24,23.23
2012-10-25,22.56
2012-10-26,21.94
2012-10-31,21.11
2012-11-01,21.21
2012-11-02,21.18
2012-11-05,21.25
2012-11-06,21.17
2012-11-07,20.47
2012-11-08,19.99
2012-11-09,19.21
2012-11-12,20.07
2012-11-13,19.86
2012-11-14,22.36
2012-11-15,22.17
2012-11-16,23.56
2012-11-19,22.92
2012-11-20,23.1
2012-11-21,24.32
2012-11-23,24.0
2012-11-26,25.94
2012-11-27,26.15
2012-11-28,26.36
2012-11-29,27.32
2012-11-30,28.0
2012-12-03,27.04
2012-12-04,27.46
2012-12-05,27.71
2012-12-06,26.97
2012-12-07,27.49
2012-12-10,27.84
2012-12-11,27.98
2012-12-12,27.58
2012-12-13,28.24
2012-12-14,26.81
2012-12-17,26.75
2012-12-18,27.71
2012-12-19,27.41
2012-12-20,27.36
2012-12-21,26.26
2012-12-24,26.93
2012-12-26,26.51
2012-12-27,26.05
2012-12-28,25.91
2012-12-31,26.62
2013-01-02,28.0
2013-01-03,27.77
2013-01-04,28.76
2013-01-07,29.42
2013-01-08,29.06
2013-01-09,30.59
2013-01-10,31.3
2013-01-11,31.72
2013-01-14,30.95
2013-01-15,30.1
2013-01-16,29.85
2013-01-17,30.14
2013-01-18,29.66
2013-01-22,30.73
2013-01-23,30.82
2013-01-24,31.08
2013-01-25,31.54
2013-01-28,32.47
2013-01-29,30.79
2013-01-30,31.24
2013-01-31,30.98
2013-02-01,29.73
2013-02-04,28.11
2013-02-05,28.64
2013-02-06,29.05
2013-02-07,28.65
2013-02-08,28.55
2013-02-11,28.26
2013-02-12,27.37
2013-02-13,27.91
2013-02-14,28.5
2013-02-15,28.32
2013-02-19,28.93
2013-02-20,28.46
2013-02-21,27.28
2013-02-22,27.13
2013-02-25,27.27
2013-02-26,27.39
2013-02-27,26.87
2013-02-28,27.25
2013-03-01,27.78
2013-03-04,27.72
2013-03-05,27.52
2013-03-06,27.45
2013-03-07,28.58
2013-03-08,27.96
2013-03-11,28.14
2013-03-12,27.83
2013-03-13,27.08
2013-03-14,27.04
2013-03-15,26.65
2013-03-18,26.49
2013-03-19,26.55
2013-03-20,25.86
2013-03-21,25.74
2013-03-22,25.73
2013-03-25,25.13
2013-03-26,25.21
2013-03-27,26.09
2013-03-28,25.58
2013-04-01,25.53
2013-04-02,25.42
2013-04-03,26.25
2013-04-04,27.07
2013-04-05,27.39
2013-04-08,26.85
2013-04-09,26.59
2013-04-10,27.57
2013-04-11,28.02
2013-04-12,27.4
2013-04-15,26.52
2013-04-16,26.92
2013-04-17,26.63
2013-04-18,25.69
2013-04-19,25.73
2013-04-22,25.97
2013-04-23,25.98
2013-04-24,26.11
2013-04-25,26.14
2013-04-26,26.85
2013-04-29,26.98
2013-04-30,27.77
2013-05-01,27.43
2013-05-02,28.97
2013-05-03,28.31
2013-05-06,27.57
2013-05-07,26.89
2013-05-08,27.12
2013-05-09,27.04
2013-05-10,26.68
2013-05-13,26.82
2013-05-14,27.07
2013-05-15,26.6
2013-05-16,26.13
2013-05-17,26.25
2013-05-20,25.76
2013-05-21,25.66
2013-05-22,25.16
2013-05-23,25.06
2013-05-24,24.31
2013-05-28,24.1
2013-05-29,23.32
2013-05-30,24.55
2013-05-31,24.35
2013-06-03,23.85
2013-06-04,23.52
2013-06-05,22.9
2013-06-06,22.97
2013-06-07,23.29
2013-06-10,24.33
2013-06-11,24.03
2013-06-12,23.77
2013-06-13,23.73
2013-06-14,23.63
2013-06-17,24.02
2013-06-18,24.21
2013-06-19,24.31
2013-06-20,23.9
2013-06-21,24.53
2013-06-24,23.94
2013-06-25,24.25
2013-06-26,24.16
2013-06-27,24.66
2013-06-28,24.88
2013-07-01,24.81
2013-07-02,24.41
2013-07-03,24.52
2013-07-05,24.37
2013-07-08,24.71
2013-07-09,25.48
2013-07-10,25.8
2013-07-11,25.81
2013-07-12,25.91
2013-07-15,26.28
2013-07-16,26.32
2013-07-17,26.65
2013-07-18,26.18
2013-07-19,25.88
2013-07-22,26.05
2013-07-23,26.13
2013-07-24,26.51
2013-07-25,34.36
2013-07-26,34.01
2013-07-29,35.43
2013-07-30,37.63
2013-07-31,36.8
2013-08-01,37.49
2013-08-02,38.05
2013-08-05,39.19
2013-08-06,38.55
2013-08-07,38.87
2013-08-08,38.54
2013-08-09,38.5
2013-08-12,38.22
2013-08-13,37.02
2013-08-14,36.65
2013-08-15,36.56
2013-08-16,37.08
2013-08-19,37.81
2013-08-20,38.41
2013-08-21,38.32
2013-08-22,38.55
2013-08-23,40.55
2013-08-26,41.34
2013-08-27,39.64
2013-08-28,40.55
2013-08-29,41.28
2013-08-30,41.29
2013-09-03,41.87
2013-09-04,41.78
2013-09-05,42.66
2013-09-06,43.95
2013-09-09,44.04
2013-09-10,43.6
2013-09-11,45.04
2013-09-12,44.75
2013-09-13,44.31
2013-09-16,42.51
2013-09-17,45.07
2013-09-18,45.23
2013-09-19,45.98
2013-09-20,47.49
2013-09-23,47.19
2013-09-24,48.45
2013-09-25,49.46
2013-09-26,50.39
2013-09-27,51.24
2013-09-30,50.23
2013-10-01,50.42
2013-10-02,50.28
2013-10-03,49.18
2013-10-04,51.04
2013-10-07,50.52
2013-10-08,47.14
2013-10-09,46.77
2013-10-10,49.05
2013-10-11,49.11
2013-10-14,49.51
2013-10-15,49.5
2013-10-16,51.14
2013-10-17,52.21
2013-10-18,54.22
2013-10-21,53.85
2013-10-22,52.68
2013-10-23,51.9
2013-10-24,52.45
2013-10-25,51.95
2013-10-28,50.23
2013-10-29,49.4
2013-10-30,49.01
2013-10-31,50.21
2013-11-01,49.75
2013-11-04,48.22
2013-11-05,50.11
2013-11-06,49.12
2013-11-07,47.56
2013-11-08,47.53
2013-11-11,46.2
2013-11-12,46.61
2013-11-13,48.71
2013-11-14,48.99
2013-11-15,49.01
2013-11-18,45.83
2013-11-19,46.36
2013-11-20,46.43
2013-11-21,46.7
2013-11-22,46.23
2013-11-25,44.82
2013-11-26,45.89
2013-11-27,46.49
2013-11-29,47.01
2013-12-02,47.06
2013-12-03,46.73
2013-12-04,48.62
2013-12-05,48.34
2013-12-06,47.94
2013-12-09,48.84
2013-12-10,50.25
2013-12-11,49.38
2013-12-12,51.83
2013-12-13,53.32
2013-12-16,53.81
2013-12-17,54.86
2013-12-18,55.57
2013-12-19,55.05
2013-12-20,55.12
2013-12-23,57.77
2013-12-24,57.96
2013-12-26,57.73
2013-12-27,55.44
2013-12-30,53.71
2013-12-31,54.65
2014-01-02,54.71
2014-01-03,54.56
2014-01-06,57.2
2014-01-07,57.92
2014-01-08,58.23
2014-01-09,57.22
2014-01-10,57.94
2014-01-13,55.91
2014-01-14,57.74
2014-01-15,57.6
2014-01-16,57.19
2014-01-17,56.3
2014-01-21,58.51
2014-01-22,57.51
2014-01-23,56.63
2014-01-24,54.45
2014-01-27,53.55
2014-01-28,55.14
2014-01-29,53.53
2014-01-30,61.08
2014-01-31,62.57
2014-02-03,61.48
2014-02-04,62.75
2014-02-05,62.19
2014-02-06,62.16
2014-02-07,64.32
2014-02-10,63.55
2014-02-11,64.85
2014-02-12,64.45
2014-02-13,67.33
2014-02-14,67.09
2014-02-18,67.3
2014-02-19,68.06
2014-02-20,69.63
2014-02-21,68.59
2014-02-24,70.78
2014-02-25,69.85
2014-02-26,69.26
2014-02-27,68.94
2014-02-28,68.46
2014-03-03,67.41
2014-03-04,68.8
2014-03-05,71.57
2014-03-06,70.84
2014-03-07,69.8
2014-03-10,72.03
2014-03-11,70.1
2014-03-12,70.88
2014-03-13,68.83
2014-03-14,67.72
2014-03-17,68.74
2014-03-18,69.19
2014-03-19,68.24
2014-03-20,66.97
2014-03-21,67.24
2014-03-24,64.1
2014-03-25,64.89
2014-03-26,60.39
2014-03-27,60.97
2014-03-28,60.01
2014-03-31,60.24
"""), parse_dates=['ds'])
