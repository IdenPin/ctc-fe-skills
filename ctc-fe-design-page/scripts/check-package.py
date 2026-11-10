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


def read_contract():
    layouts = {}
    for line in (ROOT / "references/layout-contract.md").read_text(encoding="utf-8").splitlines():
        if re.match(r"^\| T0[1-7]_", line):
            template_id, required, optional = [part.strip() for part in line.strip("|").split("|")]
            require(template_id not in layouts, f"契约重复定义 {template_id}")
            layouts[template_id] = {
                "required": {item.strip() for item in required.split(",") if item.strip() and item.strip() != "无"},
                "optional": {item.strip() for item in optional.split(",") if item.strip() and item.strip() != "无"},
            }
    require(len(layouts) == 7, "契约应包含七个模板")
    for template_id, slots in layouts.items():
        require(not slots["required"] & slots["optional"], f"{template_id} 必需与可选插槽重复")
    return layouts


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
        if "parameter-footer" in attrs.get("class", "").split() or "table-page-footer" in attrs.get("class", "").split():
            self.footer_inside_panel = any(
                "parameter-panel" in item[1].get("class", "").split()
                or "registry-body" in item[1].get("class", "").split()
                or "main-card" in item[1].get("class", "").split()
                for item in self.stack
            )
        if tag not in VOID_TAGS:
            self.stack.append((tag, attrs))

    def handle_startendtag(self, tag, attrs):
        if tag in VOID_TAGS:
            self.handle_starttag(tag, attrs)
        else:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self.label is not None:
            self.label[1] += data

    def handle_endtag(self, tag):
        if tag == "span" and self.label is not None:
            name, label = self.label
            require(label.strip() == f"#{name}", f"插槽标签文字不一致：{name} / {label!r}")
            self.label = None
        require(bool(self.stack) and self.stack[-1][0] == tag, f"HTML 标签闭合错误：{tag}")
        self.stack.pop()


def check_local_link(source, href):
    parsed = urlsplit(href)
    if parsed.scheme or not parsed.path:
        return
    target = (source.parent / unquote(parsed.path)).resolve()
    require(target.is_relative_to(ROOT), f"引用越出当前技能目录：{source.relative_to(ROOT)} → {href}")
    require(target.exists(), f"断开的引用：{source.relative_to(ROOT)} → {href}")


def semantic_errors(spec):
    """JSON Schema 之外的集合 key、默认项和容量关系。"""
    errors = []

    def unique(items, field, scope):
        keys = [item.get(field) for item in items if isinstance(item, dict)]
        duplicates = [key for key, count in Counter(keys).items() if count > 1]
        if duplicates:
            errors.append(f"{scope} 的 {field} 重复：{duplicates}")

    for key in ("filters", "toolbar", "columns", "summary", "actions", "footer"):
        unique(spec.get(key, []), "key", key)
    tabs = spec.get("tabs", {})
    unique(tabs.get("items", []), "key", "tabs.items")
    if "defaultKey" in tabs and tabs["defaultKey"] not in {item.get("key") for item in tabs.get("items", [])}:
        errors.append("tabs.defaultKey 不属于页签集合")
    pagination = spec.get("pagination", {})
    for field, slot in (("pagination", "pagination"), ("legend", "legend"), ("mapTools", "map-tools")):
        if spec.get(field, {}).get("enabled") is False and slot in spec.get("enabledSlots", []):
            errors.append(f"{slot} 同时被启用和禁用")
    if "pageSize" in pagination and "pageSizes" in pagination and pagination["pageSize"] not in pagination["pageSizes"]:
        errors.append("pagination.pageSize 不属于 pageSizes")
    panels = spec.get("panels", [])
    unique(panels, "slot", "panels")
    for panel in panels:
        unique(panel.get("columns", []), "key", f"panels.{panel.get('slot')}.columns")
    for columns in [spec.get("columns", [])] + [panel.get("columns", []) for panel in panels]:
        for column in columns:
            unique(column.get("actions", []), "key", f"column.{column.get('key')}.actions")
    nodes = []

    def collect(branch):
        for node in branch:
            nodes.append(node)
            collect(node.get("children", []))

    collect(spec.get("sidebar", {}).get("nodes", []))
    unique(nodes, "key", "sidebar.nodes")
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
    schema = json.loads((ROOT / "references/page-spec.schema.json").read_text(encoding="utf-8"))
    require(set(schema["properties"]["templateId"]["enum"]) == set(layouts), "Schema 模板 ID 与契约不一致")
    branches = {entry.get("if", {}).get("properties", {}).get("templateId", {}).get("const"): entry for entry in schema["allOf"]}
    for template_id, slots in layouts.items():
        require(template_id in branches, f"Schema 缺少 {template_id} 分支")
        allowed = branches[template_id]["then"]["properties"]["enabledSlots"]["items"]["enum"]
        require(set(allowed) == slots["required"] | slots["optional"], f"{template_id} Schema 插槽不一致")

    source = ROOT / "assets/layout-spec.html"
    preview = source.read_text(encoding="utf-8")
    parser = PreviewParser()
    parser.feed(preview)
    parser.close()
    require(not parser.stack, "HTML 有未闭合标签")
    require(set(parser.articles) == set(layouts), "HTML 模板 ID 与契约不一致")
    require(parser.footer_inside_panel, "T01 底栏应属于同一白色内容卡片")
    require("layout-tokens.css" in parser.links, "预览未加载统一布局变量")
    for template_id, slots in layouts.items():
        expected = slots["required"] | slots["optional"]
        article = parser.articles[template_id]
        require(set(article["labels"]) == expected, f"{template_id} 预览标签与契约不一致")
        require(len(article["labels"]) == len(expected), f"{template_id} 存在重复预览标签")
        require(set(article["rows"]) == expected, f"{template_id} 插槽说明表不完整")
        require({name for name, needed in article["rows"].items() if needed} == slots["required"], f"{template_id} 必需/可选标记不一致")
    for href in parser.links:
        check_local_link(source, href)
    for markdown in ROOT.rglob("*.md"):
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
    for name, value in tokens.items():
        if value.endswith("px"):
            require(int(value[:-2]) % 4 == 0, f"布局变量 {name} 不符合 4px 栅格")
    used = set(re.findall(r"var\((--layout-[\w-]+)\)", preview))
    require(used <= set(tokens), f"预览引用了未定义变量：{used - set(tokens)}")
    for selector in (".registry-body", ".parameter-panel", ".report-content"):
        rule = re.search(re.escape(selector) + r"\s*\{([^}]+)\}", preview).group(1)
        require("margin: var(--layout-frame-gap)" in rule, f"{selector} 应使用统一四边外间距")
        require("background: var(--layout-content-bg)" in rule, f"{selector} 应保持白卡底色")

    examples = json.loads((ROOT / "references/page-spec.examples.json").read_text(encoding="utf-8"))
    require({item["spec"]["templateId"] for item in examples if item["spec"]["mode"] == "page"} == set(layouts), "业务输入示例未覆盖七个模板")
    require(any(item["spec"]["mode"] == "layout" for item in examples), "缺少纯布局示例")
    validator = schema_validator(schema)
    for item in examples:
        check_spec(item["spec"], validator, item["name"])
    print(f"当前技能资料校验通过：{len(layouts)} 个模板，引用和插槽清单完整，T01 底栏归属正确。")
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
