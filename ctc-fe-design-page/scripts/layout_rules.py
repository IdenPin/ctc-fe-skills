import ast
import json
from pathlib import Path
import re

UNRESOLVED = object()
DEFAULTS = {
    'CtcTablePageLayout': {'autoHeight': True, 'toolbarPlacement': 'separate', 'card': True},
    'CtcSidebarTreeLayout': {'sidebarWidth': '260px', 'collapsible': True},
    'CtcMasterDetailLayout': {'masterWidth': '340px'},
    'CtcGisHudLayout': {'theme': 'light'},
    'CtcDualPaneReview': {'leftWidth': '45%', 'gap': '16px'},
    'CtcDashboardGridLayout': {'gap': '16px', 'scrollable': True},
    'CtcAnchorScrollLayout': {'anchorWidth': '180px'},
    'CtcStepWizardLayout': {'activeStep': 0},
}
GEOMETRY = re.compile(r'^(?:display|position|inset.*|top|right|bottom|left|(?:min-|max-)?(?:height|width)|flex.*|grid.*|overflow.*|padding.*|margin.*|gap|row-gap|column-gap|transform|order)$')


def normalize(name):
    return name.replace('-', '').lower()


def load_spec(path):
    import jsonschema
    spec = json.loads(path.read_text(encoding='utf-8'))
    schema = json.loads((Path(__file__).resolve().parents[1] / 'references/page-spec.schema.json').read_text())
    jsonschema.Draft202012Validator(schema).validate(spec)
    for field, key in [('steps', 'step'), ('sections', 'id'), ('filters', 'name'), ('metrics', 'name')]:
        identifiers = [item[key] for item in spec.get(field, []) if isinstance(item, dict) and key in item]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError(f'{field}.{key} 重复')
    return spec


def spec_bindings(content, page_path, paths):
    bindings = {}
    for name, relative in re.findall(r"import\s+([\w$]+)\s+from\s+['\"]([^'\"]+\.json)['\"]", content):
        imported = (page_path.parent / relative).resolve()
        if imported in {path.resolve() for path in paths}:
            bindings[name] = json.loads(imported.read_text())
    return bindings


def literal(expression, bindings):
    expression = expression.strip()
    expression = re.sub(r'\s+as\s+[\w.$]+$', '', expression).strip()
    if expression in {'true', 'false', 'null'}:
        return {'true': True, 'false': False, 'null': None}[expression]
    try:
        return json.loads(expression)
    except (ValueError, TypeError):
        pass
    if expression.startswith("'") and expression.endswith("'"):
        try:
            value = ast.literal_eval(expression)
            return value if isinstance(value, str) else UNRESOLVED
        except (ValueError, SyntaxError):
            return UNRESOLVED
    parts = expression.split('.')
    if parts[0] not in bindings:
        return UNRESOLVED
    value = bindings[parts[0]]
    for part in parts[1:]:
        if not isinstance(value, dict) or part not in value:
            return UNRESOLVED
        value = value[part]
    return value


def node_properties(node, bindings):
    values, errors = {}, []
    for name, raw in node.attrs.items():
        if name == 'v-bind':
            spread = literal(raw or '', bindings)
            if not isinstance(spread, dict):
                errors.append('布局 v-bind 必须引用本次冻结 Spec 的属性对象')
            else:
                if any(normalize(key) in {'style', 'class'} for key in spread):
                    errors.append('布局 v-bind 不得夹带 style/class；仅绑定冻结的布局属性')
                values.update({normalize(key): value for key, value in spread.items()})
        elif name.startswith(':') or name.startswith('v-bind:'):
            key = name[1:] if name.startswith(':') else name[7:]
            values[normalize(key)] = literal(raw or '', bindings)
        else:
            values[normalize(name)] = True if raw is None or raw == '' else raw
    return values, errors


def same_value(actual, expected):
    if isinstance(expected, bool):
        return isinstance(actual, bool) and actual == expected
    if isinstance(expected, (int, float)):
        return isinstance(actual, (int, float)) and not isinstance(actual, bool) and actual == expected
    return type(actual) is type(expected) and actual == expected


def compare_properties(comp, node, spec, bindings):
    values, errors = node_properties(node, bindings)
    expected = {**DEFAULTS[comp], **spec.get('layoutProps', {})}
    if comp == 'CtcDashboardGridLayout' and spec.get('mode') == 'page':
        expected['cards'] = spec['grid']['cards']
    allowed = {normalize(key): key for key in expected}
    for key in values:
        if key in allowed or key in {'style', 'class', 'id', 'key', 'ref'} or key.startswith(('data', 'aria', '@', 'on', 'v')):
            continue
        errors.append(f'{comp} 不支持或未登记的布局属性: {key}')
    for key, value in expected.items():
        actual = values.get(normalize(key), DEFAULTS[comp].get(key, UNRESOLVED))
        if key == 'activeStep' and actual is UNRESOLVED:
            continue
        if not same_value(actual, value):
            errors.append(f'{comp}.{key} 与冻结 Spec 不一致；应为 {value!r}，请使用字面量或 Spec JSON 绑定')
    return errors


def declarations(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    return [name.strip().lower() for name in re.findall(r'(?:^|;)\s*([\w-]+)\s*:', css)]


def protected_style(node, styles, bindings):
    _, errors = node_properties(node, bindings)
    inline = node.attrs.get('style') or ''
    if any(GEOMETRY.match(name) for name in declarations(inline)):
        errors.append('禁止在布局根节点覆盖结构样式；尺寸与排列请使用登记的布局属性')
    for name in (':style', 'v-bind:style'):
        if name in node.attrs:
            value = literal(node.attrs[name], bindings)
            if not isinstance(value, dict) or any(GEOMETRY.match(re.sub(r'([A-Z])', r'-\1', key).lower()) for key in value):
                errors.append('布局根节点的动态 style 不得改变受控结构')
    classes = (node.attrs.get('class') or '').split()
    for name in (':class', 'v-bind:class'):
        if name in node.attrs:
            value = literal(node.attrs[name], bindings)
            if isinstance(value, str):
                classes.extend(value.split())
            else:
                errors.append('布局根节点动态 class 无法静态核实；请将装饰样式放入业务内容区')
    styles = re.sub(r'/\*.*?\*/', '', styles, flags=re.S)
    for selector, rule in re.findall(r'([^{}]+)\{([^{}]*)\}', styles):
        structural = any(GEOMETRY.match(name) for name in declarations(rule))
        internal = re.search(r'\.ctc-(?:table-page-layout|sidebar-tree-layout|master-detail-layout|gis-hud-layout|dual-pane-review|dashboard-grid-layout|anchor-scroll-layout|step-wizard-layout)(?:\b|__)', selector)
        targets_root = any(re.search(r'\.' + re.escape(cls) + r'(?:[\w.\-:#()\[\]="\s]*)?$', part.strip()) and not re.search(r'\.' + re.escape(cls) + r'\s+[.#\w]', part.strip()) for cls in classes for part in selector.split(','))
        if structural and (internal or targets_root):
            errors.append(f'样式选择器 {selector.strip()} 覆盖受控布局结构')
    return errors
