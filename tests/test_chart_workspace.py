import unittest

from logic.chart_canvas import marker_stride
from logic.c_chart import CChartPopup
from logic.histogram import HistogramChartPopup
from logic.imr_chart import IMRChartPopup
from logic.np_chart import NPChartPopup
from logic.p_chart import PChartPopup
from logic.pareto import ParetoChartPopup
from logic.scatter import ScatterChartPopup
from logic.u_chart import UChartConvertedPopup, UChartPopup
from logic.xbar_r import XbarRChartPopup
from logic.xbar_s import XbarSChartPopup
from ui.chart_view import EmbeddedChartFrame


class ChartWorkspaceTests(unittest.TestCase):
    def test_marker_stride_only_reduces_dense_point_glyphs(self):
        self.assertEqual(marker_stride(1001), 6)
        self.assertEqual(marker_stride(200), 1)

    def test_primary_chart_views_use_the_shared_embedded_host(self):
        chart_views = (
            HistogramChartPopup, ParetoChartPopup, ScatterChartPopup,
            IMRChartPopup, XbarRChartPopup, XbarSChartPopup,
            PChartPopup, NPChartPopup, CChartPopup, UChartPopup,
        )
        for chart_view in chart_views:
            with self.subTest(chart=chart_view.__name__):
                self.assertTrue(issubclass(chart_view, EmbeddedChartFrame))

        # This is a configuration workflow, so it remains a separate dialog.
        self.assertFalse(issubclass(UChartConvertedPopup, EmbeddedChartFrame))


if __name__ == "__main__":
    unittest.main()
