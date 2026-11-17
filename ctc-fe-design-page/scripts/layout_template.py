from __future__ import annotations

from html.parser import HTMLParser

TAG_TO_COMP = {
    "ctctablepagelayout": "CtcTablePageLayout",
    "ctc-table-page-layout": "CtcTablePageLayout",
    "ctcsidebartreelayout": "CtcSidebarTreeLayout",
    "ctc-sidebar-tree-layout": "CtcSidebarTreeLayout",
    "ctcmasterdetaillayout": "CtcMasterDetailLayout",
    "ctc-master-detail-layout": "CtcMasterDetailLayout",
    "ctcgishudlayout": "CtcGisHudLayout",
    "ctc-gis-hud-layout": "CtcGisHudLayout",
    "ctcdualpanereview": "CtcDualPaneReview",
    "ctc-dual-pane-review": "CtcDualPaneReview",
    "ctcdashboardgridlayout": "CtcDashboardGridLayout",
    "ctc-dashboard-grid-layout": "CtcDashboardGridLayout",
    "ctcanchorscrolllayout": "CtcAnchorScrollLayout",
    "ctc-anchor-scroll-layout": "CtcAnchorScrollLayout",
    "ctcstepwizardlayout": "CtcStepWizardLayout",
    "ctc-step-wizard-layout": "CtcStepWizardLayout",
}

LAYOUT_REGISTRY = {
    "CtcTablePageLayout": {
        "templateId": "L01_STANDARD_TABLE_PAGE",
        "required_slots": {"main-viewport"},
        "optional_slots": {"filter-bar", "toolbar", "footer-bar"},
    },
    "CtcSidebarTreeLayout": {
        "templateId": "L02_SIDEBAR_TREE_SPLIT",
        "required_slots": {"sidebar-nav", "content-body"},
        "optional_slots": {"content-header", "content-footer"},
    },
    "CtcMasterDetailLayout": {
        "templateId": "L03_MASTER_DETAIL_SPLIT",
        "required_slots": {"master-list", "detail-body"},
        "optional_slots": {"master-filter", "detail-head", "detail-actions"},
    },
    "CtcGisHudLayout": {
        "templateId": "L04_GIS_HUD_DASHBOARD",
        "required_slots": {"canvas-bg"},
        "optional_slots": {
            "hud-top",
            "hud-left",
            "hud-right",
            "hud-bottom-left",
            "hud-bottom-right",
        },
    },
    "CtcDualPaneReview": {
        "templateId": "L05_DUAL_PANE_REVIEW",
        "required_slots": {"pane-left", "pane-right"},
        "optional_slots": set(),
    },
    "CtcDashboardGridLayout": {
        "templateId": "L06_GRID_DASHBOARD",
        "required_slots": {"dashboard-grid"},
        "optional_slots": {"metric-cards", "dashboard-toolbar"},
    },
    "CtcAnchorScrollLayout": {
        "templateId": "L07_SECTION_ANCHOR_FLOW",
        "required_slots": {"anchor-nav", "sections-stream"},
        "optional_slots": {"profile-header", "sticky-actions"},
    },
    "CtcStepWizardLayout": {
        "templateId": "L08_STEP_WIZARD_FUNNEL",
        "required_slots": {"step-tracker", "stage-viewport", "action-rail"},
        "optional_slots": {"step-summary"},
    },
}

SHELL_TAGS = {
    "ctcdialog",
    "ctc-dialog",
    "ctcdrawer",
    "ctc-drawer",
}


class TemplateNode:
    def __init__(self, tag: str, attrs: list[tuple[str, str | None]], parent: TemplateNode | None = None):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.children: list[TemplateNode] = []


class VueTemplateParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = TemplateNode("root", [])
        self.current = self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        node = TemplateNode(tag, attrs, parent=self.current)
        self.current.children.append(node)
        if tag.lower() not in {
            "area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"
        }:
            self.current = node

    def handle_endtag(self, tag: str):
        curr = self.current
        while curr is not None and curr.tag.lower() != tag.lower() and curr != self.root:
            curr = curr.parent
        if curr is not None and curr != self.root:
            self.current = curr.parent

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]):
        node = TemplateNode(tag, attrs, parent=self.current)
        self.current.children.append(node)


def get_slot_name(child_node: TemplateNode) -> str | None:
    if child_node.tag.lower() != "template":
        return None
    for attr_name in child_node.attrs:
        if attr_name.startswith("#"):
            return attr_name[1:]
        if attr_name.startswith("v-slot:"):
            return attr_name[len("v-slot:"):]
    return None


def find_layout_instances(node: TemplateNode) -> list[tuple[str, TemplateNode]]:
    instances = []
    comp_name = TAG_TO_COMP.get(node.tag.lower())
    if comp_name:
        instances.append((comp_name, node))
    for child in node.children:
        instances.extend(find_layout_instances(child))
    return instances


def has_descendant(node: TemplateNode, predicate) -> bool:
    for ch in node.children:
        if predicate(ch) or has_descendant(ch, predicate):
            return True
    return False


