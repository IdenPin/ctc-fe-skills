#!/usr/bin/env python3
"""检查当前技能的资料、内部引用与 PageSpec；不扫描业务页面或安装钩子。"""

import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def table_rows(section, prefix="| L0"):
    rows = {}
    for line in section.splitlines():
        if not line.startswith(prefix):
            continue
        cells = [part.strip() for part in line.strip("|").split("|")]
        require(len(cells) == 3, f"表格行格式错误：{line}")
        template_id, required, optional = cells
        require(template_id not in rows, f"契约重复定义 {template_id}")
        rows[template_id] = {
            "required": {item.strip() for item in required.split(",") if item.strip() and item.strip() != "无"},
            "optional": {item.strip() for item in optional.split(",") if item.strip() and item.strip() != "无"},
        }
    return rows


def read_contract():
    content = (ROOT / "references/layout-contract.md").read_text(encoding="utf-8")
    start = content.index("## 模板与插槽")
    end = content.index("## 空间约束与高度传导规则", start)
    layouts = table_rows(content[start:end], "| L0")
    require(len(layouts) == 8, f"契约应包含八个模板，当前为 {len(layouts)}")
    for template_id, slots in layouts.items():
        require(not slots["required"] & slots["optional"], f"{template_id} 必需与可选插槽重复")
    return layouts


def read_page_fields():
    content = (ROOT / "references/layout-contract.md").read_text(encoding="utf-8")
    start = content.index("### page：业务页面")
    end = content.index("## 组件与消费原则", start)
    fields = table_rows(content[start:end], "| L0")
    require(len(fields) == 8, f"PageSpec 字段契约应包含八个模板，当前为 {len(fields)}")
    for template_id, definition in fields.items():
        require(not definition["required"] & definition["optional"], f"{template_id} 必需与可选字段重复")
    return fields


class PreviewParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.articles = {}
        self.links = []
        self.label = None
        self.footer_inside_panel = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "href" in attrs:
            self.links.append(attrs["href"])
        template_id = attrs.get("data-template-id")
        if template_id:
            require(template_id not in self.articles, f"预览重复模板 {template_id}")
            self.articles[template_id] = {"labels": [], "rows": {}}
        current = next((item[1]["data-template-id"] for item in reversed(self.stack) if "data-template-id" in item[1]), template_id)
        if "data-slot" in attrs:
            require(current is not None, "插槽标签不属于任何模板")
            self.articles[current]["labels"].append(attrs["data-slot"])
            self.label = [attrs["data-slot"], ""]
        if "data-slot-row" in attrs:
            require(current is not None, "插槽表不属于任何模板")
            rows = self.articles[current]["rows"]
            name = attrs["data-slot-row"]
            require(name not in rows, f"{current} 插槽表重复 {name}")
            require(attrs.get("data-required") in {"true", "false"}, f"{name} 缺少必需/可选标记")
            rows[name] = attrs["data-required"] == "true"
        if "table-page-footer" in attrs.get("class", "").split():
            self.footer_inside_panel = any(
                "report-content" in item[1].get("class", "").split()
                or "parameter-panel" in item[1].get("class", "").split()
                or "registry-body" in item[1].get("class", "").split()
                for item in self.stack
            )
        if tag not in VOID_TAGS:
            self.stack.append((tag, attrs))

    def handle_startendtag(self, tag, attrs):
        if tag in VOID_TAGS:
            self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag not in VOID_TAGS:
            require(self.stack, f"多余的闭合标签：{tag}")
            opened, _ = self.stack.pop()
            require(opened == tag, f"标签闭合不匹配：<{opened}> 被 </{tag}> 闭合")
        if self.label and self.stack and not any(tag == "span" for tag, _ in self.stack):
            self.label = None

    def handle_data(self, data):
        if self.label:
            self.label[1] += data


def check_local_link(source, href):
    parsed = urlsplit(href)
    if parsed.scheme or not parsed.path:
        return
    target = (source.parent / unquote(parsed.path)).resolve()
    require(target.is_relative_to(ROOT), f"引用越出当前技能目录：{source.relative_to(ROOT)} → {href}")
    require(target.exists(), f"断开的引用：{source.relative_to(ROOT)} → {href}")


def semantic_errors(spec):
    """JSON Schema 之外的语义关系检查。"""
    errors = []

    def unique(items, field, scope):
        keys = [item.get(field) for item in items if isinstance(item, dict) and item.get(field) is not None]
        duplicates = [key for key, count in Counter(keys).items() if count > 1]
        if duplicates:
            errors.append(f"{scope} 的 {field} 重复：{duplicates}")

    for key in ("filters", "metrics", "sections", "steps"):
        if key in spec and isinstance(spec[key], list):
            unique(spec[key], "id" if key == "sections" else ("step" if key == "steps" else "name"), key)

    return errors


def schema_validator(schema, required=False):
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        require(not required, "校验 PageSpec 需要 jsonschema，请在工具环境安装后重试")
        return None
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def check_spec(spec, validator, label):
    require(isinstance(spec, dict), f"{label} 应为 JSON 对象")
    if validator is not None:
        errors = sorted(validator.iter_errors(spec), key=lambda item: str(list(item.path)))
        require(not errors, f"{label} 不符合 Schema：" + "; ".join(f"{list(item.path)}: {item.message}" for item in errors))
    errors = semantic_errors(spec)
    require(not errors, f"{label} 跨字段校验失败：" + "; ".join(errors))


def check_package():
    layouts = read_contract()
    page_fields = read_page_fields()
    schema = json.loads((ROOT / "references/page-spec.schema.json").read_text(encoding="utf-8"))
    require(set(schema["properties"]["templateId"]["enum"]) == set(layouts), "Schema 模板 ID 与契约不一致")
    branches = {entry.get("if", {}).get("properties", {}).get("templateId", {}).get("const"): entry for entry in schema["allOf"] if "templateId" in entry.get("if", {}).get("properties", {})}
    common_fields = {"pageTitle", "appearance", "enabledSlots", "surface", "layoutKey"}
    metadata_fields = {"contractVersion", "templateId", "mode"}
    require(set(page_fields) == set(layouts), "PageSpec 字段契约模板 ID 与插槽契约不一致")
    for template_id, slots in layouts.items():
        require(template_id in branches, f"Schema 缺少 {template_id} 分支")
        branch_properties = branches[template_id]["then"]["properties"]
        allowed = branch_properties["enabledSlots"]["items"]["enum"]
        require(set(allowed) == slots["required"] | slots["optional"], f"{template_id} Schema 插槽不一致")
        field_definition = page_fields[template_id]
        required_fields = field_definition["required"]
        optional_fields = field_definition["optional"]
        require("pageTitle" in required_fields, f"{template_id} 必须声明 pageTitle")
        nested_required = set(branches[template_id]["then"].get("allOf", [{}])[0].get("then", {}).get("required", []))
        require(nested_required == required_fields - {"pageTitle"}, f"{template_id} Schema 必填字段与 PageSpec 契约不一致")
        actual_fields = {
            name for name in schema["properties"]
            if name not in common_fields | metadata_fields and branch_properties.get(name) is not False
        }
        expected_fields = (required_fields | optional_fields) - common_fields
        require(actual_fields == expected_fields, f"{template_id} Schema 字段与 PageSpec 契约不一致；缺少 {expected_fields - actual_fields}，多出 {actual_fields - expected_fields}")

    source = ROOT / "assets/layout-spec.html"
    preview = source.read_text(encoding="utf-8")
    parser = PreviewParser()
    parser.feed(preview)
    parser.close()
    require(not parser.stack, "HTML 有未闭合标签")
    require(set(parser.articles) == set(layouts), "HTML 模板 ID 与契约不一致")
    require(parser.footer_inside_panel, "L01 底栏应属于同一内容卡片")
    require(any("layout-tokens.css" in href for href in parser.links), "预览未加载统一布局变量")
    for template_id, slots in layouts.items():
        expected = slots["required"] | slots["optional"]
        article = parser.articles[template_id]
        require(set(article["labels"]) == expected, f"{template_id} 预览标签与契约不一致：{set(article['labels'])} vs {expected}")
        require(len(article["labels"]) == len(expected), f"{template_id} 存在重复预览标签")
        require(set(article["rows"]) == expected, f"{template_id} 插槽说明表不完整：{set(article['rows'])} vs {expected}")
        require({name for name, needed in article["rows"].items() if needed} == slots["required"], f"{template_id} 必需/可选标记不一致")
    for href in parser.links:
        check_local_link(source, href)
    for markdown in ROOT.rglob("*.md"):
        if {".git", ".codegraph", ".cache", "docs"} & set(markdown.relative_to(ROOT).parts) or markdown.name == "AGENTS.md":
            continue
        for href in re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown.read_text(encoding="utf-8")):
            check_local_link(markdown, href)
    content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    require(content.startswith("---\n"), "当前技能缺少标准 frontmatter")
    metadata = content.split("---", 2)[1]
    require(bool(re.search(r"^name: [a-z0-9-]+$", metadata, re.M)) and "description:" in metadata, "当前技能元信息不完整")
    require("parameters:" not in metadata, "输入定义应放在 PageSpec Schema")
    require(not any(path.is_symlink() for path in ROOT.rglob("*")), "技能资料不应依赖符号链接")

    token_css = (ROOT / "assets/layout-tokens.css").read_text(encoding="utf-8")
    tokens = dict(re.findall(r"(--layout-[\w-]+):\s*([^;]+);", token_css))
    require(tokens.get("--layout-workspace-bg") == "#f5f7fc", "工作区底色偏离已确认值")
    require(tokens.get("--layout-content-bg") == "#ffffff", "内容卡片应为白色")
    require(tokens.get("--layout-sidebar-width") == "260px", "侧栏宽度应为 260px")
    for name, value in tokens.items():
        if value.endswith("px"):
            require(int(value[:-2]) % 4 == 0, f"布局变量 {name} 不符合 4px 栅格")
    used = set(re.findall(r"var\((--layout-[\w-]+)\)", preview))
    require(used <= set(tokens), f"预览引用了未定义变量：{used - set(tokens)}")

    # 检查组件库中 8 套布局组件的 defineSlots 声明
    layout_comp_dir = ROOT.parents[1] / "ctc-components-ui-next/src/components/layout"
    if not layout_comp_dir.is_dir():
        layout_comp_dir = ROOT.parents[0] / "ctc-components-ui-next/src/components/layout"
    if layout_comp_dir.is_dir():
        layout_comp_map = {
            "L01_STANDARD_TABLE_PAGE": layout_comp_dir / "src/table-page/CtcTablePageLayout.vue",
            "L02_SIDEBAR_TREE_SPLIT": layout_comp_dir / "src/sidebar-tree/CtcSidebarTreeLayout.vue",
            "L03_MASTER_DETAIL_SPLIT": layout_comp_dir / "src/master-detail/CtcMasterDetailLayout.vue",
            "L04_GIS_HUD_DASHBOARD": layout_comp_dir / "src/gis-hud/CtcGisHudLayout.vue",
            "L05_DUAL_PANE_REVIEW": layout_comp_dir / "src/dual-pane-review/CtcDualPaneReview.vue",
            "L06_GRID_DASHBOARD": layout_comp_dir / "src/dashboard-grid/CtcDashboardGridLayout.vue",
            "L07_SECTION_ANCHOR_FLOW": layout_comp_dir / "src/anchor-scroll/CtcAnchorScrollLayout.vue",
            "L08_STEP_WIZARD_FUNNEL": layout_comp_dir / "src/step-wizard/CtcStepWizardLayout.vue",
        }
        for tid, sfc_path in layout_comp_map.items():
            require(sfc_path.is_file(), f"{tid} 对应组件源文件不存在：{sfc_path}")
            sfc_content = sfc_path.read_text(encoding="utf-8")
            slot_block = re.search(r"defineSlots<\{(.*?)\}>\(\)", sfc_content, re.S)
            require(slot_block is not None, f"{tid} 未声明 defineSlots")
            declared = {
                quoted or plain
                for quoted, plain in re.findall(r"^\s*(?:'([^']+)'|([A-Za-z_$][\w$]*))\??\s*:", slot_block.group(1), re.M)
            }
            expected = layouts[tid]["required"] | layouts[tid]["optional"]
            require(declared == expected, f"{tid} 组件插槽声明与契约不一致：{declared} vs {expected}")

    for selector in (".registry-body", ".parameter-panel", ".report-content"):
        match = re.search(re.escape(selector) + r"\s*\{([^}]+)\}", preview)
        require(match is not None, f"预览缺少布局规则：{selector}")
        rule = match.group(1)
        require("margin: var(--layout-frame-gap)" in rule, f"{selector} 应使用统一四边外间距")
        require("background: var(--layout-content-bg)" in rule, f"{selector} 应保持白卡底色")

    examples = json.loads((ROOT / "references/page-spec.examples.json").read_text(encoding="utf-8"))
    require({item["spec"]["templateId"] for item in examples if item["spec"]["mode"] == "page"} == set(layouts), "业务输入示例未覆盖八个模板")
    require(any(item["spec"]["mode"] == "layout" for item in examples), "缺少纯布局示例")
    validator = schema_validator(schema)
    for item in examples:
        check_spec(item["spec"], validator, item["name"])

    import subprocess
    regression = subprocess.run([sys.executable, str(ROOT / "scripts/test_validate_page.py")], capture_output=True, text=True)
    require(regression.returncode == 0, "页面校验器回归失败：" + regression.stdout + regression.stderr)

    print(f"当前技能资料校验通过：{len(layouts)} 个模板，引用和插槽清单完整，L01 底栏归属正确。")
    print("页面校验器回归通过（包含原有 16 项边界用例）。")
    if validator is None:
        print("提示：当前环境无 jsonschema；输入示例仅检查跨字段关系，未执行完整 JSON Schema 校验。")
    else:
        print(f"输入 Schema 有效，{len(examples)} 组示例通过结构和跨字段校验。")
    return schema


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, help="额外校验一个 PageSpec JSON 文件（需要 jsonschema）")
    args = parser.parse_args()
    try:
        schema = check_package()
        if args.spec:
            spec = json.loads(args.spec.read_text(encoding="utf-8"))
            check_spec(spec, schema_validator(schema, required=True), str(args.spec))
            print(f"PageSpec 校验通过：{args.spec}")
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"检查失败：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
