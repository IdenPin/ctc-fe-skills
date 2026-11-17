import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE = importlib.util.spec_from_file_location("page_validator", Path(__file__).with_name("validate-page.py"))
VALIDATOR = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(VALIDATOR)


class PageValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.spec = {
            "contractVersion": "2.0.0", "mode": "page", "pageTitle": "检索",
            "templateId": "L01_STANDARD_TABLE_PAGE", "viewport": {},
            "enabledSlots": ["main-viewport"], "layoutProps": {},
        }

    def tearDown(self):
        self.directory.cleanup()

    def check(self, attrs="", body="", script="", style="", spec=None):
        spec = self.spec if spec is None else spec
        source = (
            '<script setup lang="ts">'
            "import { CtcTablePageLayout, CtcDualPaneReview, CtcDashboardGridLayout } "
            "from '@ctc-front/components-ui-next/layout';" + script + '</script>'
            '<template><CtcTablePageLayout ' + attrs + '>'
            '<template #main-viewport>表格</template></CtcTablePageLayout>' + body + '</template>'
            '<style scoped>' + style + '</style>'
        )
        page = self.root / "Page.vue"
        config = self.root / "page-spec.json"
        page.write_text(source)
        config.write_text(json.dumps(spec))
        return VALIDATOR.validate_vue_page(page, config)

    def test_boolean_literals_and_camel_case(self):
        for attrs, props in [(':card="false"', {"card": False}), ('card', {"card": True}),
                             (':autoHeight="true"', {"autoHeight": True})]:
            with self.subTest(attrs=attrs):
                self.spec["layoutProps"] = props
                self.assertEqual([], self.check(attrs))

    def test_frozen_spec_import_and_object_binding(self):
        self.spec["layoutProps"] = {"card": False, "toolbarPlacement": "filter-inline"}
        self.assertEqual([], self.check('v-bind="pageSpec.layoutProps"', script="import pageSpec from './page-spec.json';"))
        self.assertEqual([], self.check('v-bind="pageSpec.layoutProps as CtcTablePageLayoutProps"', script="import pageSpec from './page-spec.json';"))

    def test_extra_property_must_match_default(self):
        self.assertTrue(self.check(':card="false"'))
        self.assertEqual([], self.check('card'))

    def test_root_geometry_is_protected(self):
        self.assertTrue(self.check('style="display:grid;grid-template-columns:1fr 1fr"'))
        self.assertTrue(self.check('class="page-root"', style='.page-root { flex-direction: row; }'))
        self.assertTrue(self.check('', style='.ctc-table-page-layout__viewport { overflow:auto }'))
        self.assertTrue(self.check('style="/* display override */ display:grid"'))
        self.assertTrue(self.check("v-bind=' {\"style\": {\"display\": \"grid\"}} '"))

    def test_business_layout_inside_slot_is_allowed(self):
        self.assertEqual([], self.check('class="page-root"', style='.page-root .business { display:flex; }'))

    def test_nonliteral_geometry_cannot_silently_pass(self):
        self.assertTrue(self.check(':style="customLayout"'))
        self.assertTrue(self.check('v-bind="unknownProps"'))

    def test_l05_requires_ctc_shell(self):
        review = '<CtcDualPaneReview><template #pane-left>左</template><template #pane-right>右</template></CtcDualPaneReview>'
        errors = self.check(body='<ElDialog content-fill>' + review + '</ElDialog>')
        self.assertIn('原生 Element Plus', '\n'.join(errors))

    def test_every_surface_requires_its_own_spec(self):
        review = '<CtcDialog content-fill><CtcDualPaneReview><template #pane-left>左</template><template #pane-right>右</template></CtcDualPaneReview></CtcDialog>'
        self.assertTrue(self.check(body=review))
        overlay = self.root / "review.json"
        overlay.write_text(json.dumps({
            "contractVersion": "2.0.0", "mode": "page", "pageTitle": "审核",
            "templateId": "L05_DUAL_PANE_REVIEW", "surface": "dialog",
            "enabledSlots": ["pane-left", "pane-right"], "leftPane": {}, "rightPane": {},
        }))
        page = self.root / "Page.vue"
        self.assertEqual([], VALIDATOR.validate_vue_page(page, [self.root / "page-spec.json", overlay]))

    def test_grid_cards_must_use_frozen_configuration(self):
        self.spec = {
            "contractVersion": "2.0.0", "mode": "page", "pageTitle": "看板",
            "templateId": "L06_GRID_DASHBOARD", "enabledSlots": ["dashboard-grid"],
            "grid": {"cards": [{"title": "A", "span": 8}, {"title": "B", "span": 4}]},
        }
        page = self.root / "Page.vue"
        config = self.root / "page-spec.json"
        config.write_text(json.dumps(self.spec))
        prefix = "<script setup>import { CtcDashboardGridLayout } from '@ctc-front/components-ui-next/layout';import pageSpec from './page-spec.json';</script><template>"
        page.write_text(prefix + '<CtcDashboardGridLayout><template #dashboard-grid><div style="grid-column:span 6">A</div></template></CtcDashboardGridLayout></template>')
        self.assertTrue(VALIDATOR.validate_vue_page(page, config))
        page.write_text(prefix + '<CtcDashboardGridLayout :cards="pageSpec.grid.cards"><template #dashboard-grid="{ card }">{{ card.title }}</template></CtcDashboardGridLayout></template>')
        self.assertEqual([], VALIDATOR.validate_vue_page(page, config))


LEGACY_CASES = [
    ("l01-valid", """<script setup lang="ts">import { CtcTablePageLayout } from '@ctc-front/components-ui-next/layout'</script><template><CtcTablePageLayout><template #main-viewport>表格</template></CtcTablePageLayout></template>""", None, True),
    ("l01-missing-slot", """<script setup lang="ts">import { CtcTablePageLayout } from '@ctc-front/components-ui-next/layout'</script><template><CtcTablePageLayout><div>表格</div></CtcTablePageLayout></template>""", None, False),
    ("100vh-forbidden", """<script setup lang="ts">import { CtcTablePageLayout } from '@ctc-front/components-ui-next/layout'</script><template><CtcTablePageLayout><template #main-viewport>表格</template></CtcTablePageLayout></template><style>.page{height:100vh}</style>""", None, False),
    ("l05-valid", """<script setup lang="ts">import { CtcDualPaneReview } from '@ctc-front/components-ui-next/layout'</script><template><CtcDialog content-fill><CtcDualPaneReview><template #pane-left>左</template><template #pane-right>右</template></CtcDualPaneReview></CtcDialog></template>""", None, True),
    ("l05-without-shell", """<script setup lang="ts">import { CtcDualPaneReview } from '@ctc-front/components-ui-next/layout'</script><template><CtcDualPaneReview><template #pane-left>左</template><template #pane-right>右</template></CtcDualPaneReview></template>""", None, False),
    ("l05-false-fill", """<script setup lang="ts">import { CtcDualPaneReview } from '@ctc-front/components-ui-next/layout'</script><template><CtcDialog :content-fill="false"><CtcDualPaneReview><template #pane-left>左</template><template #pane-right>右</template></CtcDualPaneReview></CtcDialog></template>""", None, False),
    ("l05-inline-column", """<script setup lang="ts">import { CtcDualPaneReview } from '@ctc-front/components-ui-next/layout'</script><template><CtcDialog content-fill><CtcDualPaneReview style="flex-direction:column"><template #pane-left>左</template><template #pane-right>右</template></CtcDualPaneReview></CtcDialog></template>""", None, False),
    ("l05-class-column", """<script setup lang="ts">import { CtcDualPaneReview } from '@ctc-front/components-ui-next/layout'</script><template><CtcDialog content-fill><CtcDualPaneReview class="review-root"><template #pane-left>左</template><template #pane-right>右</template></CtcDualPaneReview></CtcDialog></template><style scoped>.review-root{flex-direction:column}</style>""", None, False),
    ("business-card-header", """<script setup lang="ts">import { CtcTablePageLayout } from '@ctc-front/components-ui-next/layout'</script><template><CtcTablePageLayout><template #main-viewport><ElCard><template #header>标题</template>内容</ElCard></template></CtcTablePageLayout></template>""", None, True),
    ("unknown-direct-slot", """<script setup lang="ts">import { CtcTablePageLayout } from '@ctc-front/components-ui-next/layout'</script><template><CtcTablePageLayout><template #main-viewport>表格</template><template #filter-bars>错拼</template></CtcTablePageLayout></template>""", None, False),
    ("nested-slot-hides-missing", """<script setup lang="ts">import { CtcTablePageLayout } from '@ctc-front/components-ui-next/layout'</script><template><CtcTablePageLayout><BusinessPanel><template #main-viewport>放错层级</template></BusinessPanel></CtcTablePageLayout></template>""", None, False),
    ("forbidden-l02-nests-l01", """<script setup lang="ts">import { CtcSidebarTreeLayout, CtcTablePageLayout } from '@ctc-front/components-ui-next/layout'</script><template><CtcSidebarTreeLayout><template #sidebar-nav>目录</template><template #content-body><CtcTablePageLayout><template #main-viewport>表格</template></CtcTablePageLayout></template></CtcSidebarTreeLayout></template>""", None, False),
    ("second-instance-missing", """<script setup lang="ts">import { CtcTablePageLayout } from '@ctc-front/components-ui-next/layout'</script><template><CtcTablePageLayout><template #main-viewport>表格</template></CtcTablePageLayout><CtcTablePageLayout><div>漏检的第二个布局</div></CtcTablePageLayout></template>""", None, False),
    ("spec-extra-actual-slot", """<script setup lang="ts">import { CtcTablePageLayout } from '@ctc-front/components-ui-next/layout'</script><template><CtcTablePageLayout><template #main-viewport>表格</template><template #filter-bar>未启用的筛选栏</template></CtcTablePageLayout></template>""", {"contractVersion": "2.0.0", "mode": "page", "pageTitle": "测试", "templateId": "L01_STANDARD_TABLE_PAGE", "viewport": {}, "enabledSlots": ["main-viewport"]}, False),
    ("spec-width-mismatch", """<script setup lang="ts">import { CtcDualPaneReview } from '@ctc-front/components-ui-next/layout'</script><template><CtcDialog content-fill><CtcDualPaneReview left-width="70%"><template #pane-left>左</template><template #pane-right>右</template></CtcDualPaneReview></CtcDialog></template>""", {"contractVersion": "2.0.0", "mode": "page", "pageTitle": "测试", "templateId": "L05_DUAL_PANE_REVIEW", "enabledSlots": ["pane-left", "pane-right"], "leftPane": {}, "rightPane": {}, "layoutProps": {"leftWidth": "40%"}}, False),
    ("spec-empty-object", """<script setup lang="ts">import { CtcTablePageLayout } from '@ctc-front/components-ui-next/layout'</script><template><CtcTablePageLayout><template #main-viewport>表格</template></CtcTablePageLayout></template>""", {}, False),
]

class LegacyPageChecks(unittest.TestCase):
    def test_existing_boundary_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, content, spec, expected in LEGACY_CASES:
                with self.subTest(name=name):
                    page = root / (name + ".vue")
                    page.write_text(content)
                    config = None
                    if spec is not None:
                        config = root / (name + ".json")
                        config.write_text(json.dumps(spec))
                    self.assertEqual(expected, not VALIDATOR.validate_vue_page(page, config))


if __name__ == "__main__":
    unittest.main()
