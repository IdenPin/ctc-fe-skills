#!/usr/bin/env python3
"""检查全部布局实例及各自冻结的 PageSpec；不执行页面中的 JavaScript。"""
import argparse
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout_template import LAYOUT_REGISTRY, SHELL_TAGS, TAG_TO_COMP, VueTemplateParser, find_layout_instances, get_slot_name, has_descendant
from layout_rules import compare_properties, load_spec, node_properties, protected_style, spec_bindings


def shell_of(node):
    parent = node.parent
    while parent is not None:
        if parent.tag.lower() in SHELL_TAGS:
            return parent
        parent = parent.parent
    return None


def surface_of(node):
    shell = shell_of(node)
    if shell is None:
        return 'embedded'
    return 'dialog' if 'dialog' in shell.tag.lower() else 'drawer'


def direct_slots(node):
    return {name for child in node.children if (name := get_slot_name(child))}


def validate_instance(comp, node, styles, bindings):
    meta = LAYOUT_REGISTRY[comp]
    slots = direct_slots(node)
    errors = protected_style(node, styles, bindings)
    missing = meta['required_slots'] - slots
    illegal = slots - meta['required_slots'] - meta['optional_slots']
    if missing:
        errors.append(f'{comp} 缺少必需直接插槽: {sorted(missing)}')
    if illegal:
        errors.append(f'{comp} 存在未定义直接插槽: {sorted(illegal)}')
    if comp == 'CtcSidebarTreeLayout' and has_descendant(node, lambda child: TAG_TO_COMP.get(child.tag.lower()) == 'CtcTablePageLayout'):
        errors.append('L02 禁止嵌套 L01；请使用 content-header/body/footer')
    if comp == 'CtcDualPaneReview':
        shell = shell_of(node)
        if shell is None:
            errors.append('L05 必须由 CtcDialog/CtcDrawer 承载；原生 Element Plus 弹层不具备 content-fill 适配')
        else:
            shell_props, shell_errors = node_properties(shell, bindings)
            errors.extend(shell_errors)
            enabled = shell_props.get('contentfill') is True
            if not enabled:
                errors.append('L05 外壳必须显式开启 content-fill')
    if comp == 'CtcAnchorScrollLayout':
        for child in node.children:
            if get_slot_name(child) == 'sections-stream' and has_descendant(child, lambda descendant: bool(re.search(r'overflow(?:-y)?\s*:\s*auto', descendant.attrs.get('style', '')))):
                errors.append('L07 章节内部禁止重复 overflow:auto 滚动容器')
    return errors


def match_specs(instances, specs, bindings):
    errors, consumed = [], set()
    for spec in specs:
        candidates = []
        for index, (comp, node) in enumerate(instances):
            if index in consumed or LAYOUT_REGISTRY[comp]['templateId'] != spec['templateId']:
                continue
            surface = spec.get('surface', 'embedded')
            if surface != surface_of(node) and not (surface == 'standalone' and shell_of(node) is None):
                continue
            if spec.get('layoutKey') and node.attrs.get('data-layout-id') != spec['layoutKey']:
                continue
            candidates.append(index)
        if len(candidates) != 1:
            errors.append(f"Spec {spec.get('layoutKey', spec['templateId'])} 必须唯一匹配一个对应页面/弹层实例；实际 {len(candidates)} 个，请声明 layoutKey 与 data-layout-id")
            continue
        index = candidates[0]
        consumed.add(index)
        comp, node = instances[index]
        expected = set(spec.get('enabledSlots', [])) | LAYOUT_REGISTRY[comp]['required_slots']
        if direct_slots(node) != expected:
            errors.append(f'{comp} 插槽与冻结 Spec 不一致: 应为 {sorted(expected)}，实际 {sorted(direct_slots(node))}')
        errors.extend(compare_properties(comp, node, spec, bindings))
    if len(consumed) != len(instances):
        errors.append('每个页面或弹层布局都必须提供独立的冻结 Spec；存在未匹配的实例')
    return errors


def validate_vue_page(vue_path, spec_path=None):
    vue_path = Path(vue_path)
    if not vue_path.is_file():
        return [f'文件不存在: {vue_path}']
    content = vue_path.read_text(encoding='utf-8')
    if not re.search(r"import\s+\{[^}]+\}\s+from\s+['\"]@ctc-front/components-ui-next/layout['\"]", content):
        return ['必须从 @ctc-front/components-ui-next/layout 导入布局组件']
    template = re.search(r'<template\b[^>]*>(.*)</template>', content, re.S)
    if template is None:
        return ['未找到 template 区域']
    parser = VueTemplateParser()
    parser.feed(template.group(1))
    instances = find_layout_instances(parser.root)
    if not instances:
        return ['未找到布局组件实例']
    paths = [] if spec_path is None else ([Path(spec_path)] if isinstance(spec_path, (str, Path)) else [Path(path) for path in spec_path])
    try:
        specs = [load_spec(path) for path in paths]
        bindings = spec_bindings(content, vue_path, paths)
    except Exception as error:
        return [f'PageSpec 校验失败: {error}']
    styles = ''.join(re.findall(r'<style\b[^>]*>(.*?)</style>', content, re.S))
    errors = []
    inline_viewport = has_descendant(parser.root, lambda node: shell_of(node) is None and bool(re.search(r'\b100vh\b', node.attrs.get('style') or '')))
    if (inline_viewport or re.search(r'\b100vh\b', styles)) and not (specs and all(spec.get('surface') == 'standalone' for spec in specs)):
        errors.append('嵌入式页面禁止 100vh；使用父容器高度链')
    for comp, node in instances:
        if re.search(r'\b100vh\b', node.attrs.get('style', '')):
            errors.append('布局根节点禁止 100vh')
        errors.extend(validate_instance(comp, node, styles, bindings))
    if paths:
        errors.extend(match_specs(instances, specs, bindings))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('vue_file', type=Path)
    parser.add_argument('--spec', type=Path, action='append', required=True, help='每个页面/弹层的冻结 JSON；多个实例可重复传入')
    args = parser.parse_args()
    errors = validate_vue_page(args.vue_file, args.spec)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'页面布局与冻结 Spec 校验通过: {args.vue_file}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
