import os
import re
from typing import Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(__file__))
ROUTES_DIR = os.path.join(ROOT, 'app', 'routes')
TEMPLATES_DIR = os.path.join(ROOT, 'app', 'templates')


def read_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def discover_blueprints_and_routes() -> List[str]:
    # Map blueprint var name -> url_prefix
    bp_prefix: Dict[str, str] = {}
    endpoints: List[str] = []

    bp_def_re = re.compile(r"(\w+)\s*=\s*Blueprint\(\s*['\"]([\w-]+)['\"][^)]*?url_prefix\s*=\s*['\"]([^'\"]+)['\"][^)]*\)")
    route_re = re.compile(r"@\s*(\w+)\.route\(\s*['\"]([^'\"]+)['\"][^)]*\)")

    if not os.path.isdir(ROUTES_DIR):
        return endpoints

    for root, _, files in os.walk(ROUTES_DIR):
        for name in files:
            if not name.endswith('.py'):
                continue
            path = os.path.join(root, name)
            src = read_file(path)

            # collect blueprint prefixes
            for m in bp_def_re.finditer(src):
                var, _bpname, prefix = m.groups()
                bp_prefix[var] = prefix.rstrip('/')

            # collect routes per blueprint var
            for m in route_re.finditer(src):
                var, route = m.groups()
                prefix = bp_prefix.get(var, '')
                full = f"{prefix}/{route.lstrip('/')}" if prefix else route
                full = '/' + full.lstrip('/')
                # normalize placeholders like <int:id> -> <id>
                full = re.sub(r"<[^>]+>", "<id>", full)
                endpoints.append(full.rstrip('/'))

    # de-duplicate
    endpoints = sorted(set(endpoints))
    return endpoints


def normalize_template_path(path: str) -> str:
    # Replace jinja expressions with a generic placeholder
    p = re.sub(r"\{\{[^}]+\}\}", "<id>", path)
    # collapse multiple slashes and strip trailing slash
    p = '/' + p.lstrip('/')
    p = p.rstrip('/')
    return p


def seg_is_placeholder(seg: str) -> bool:
    return seg.startswith('<') and seg.endswith('>')


def path_matches(endpoint: str, candidate: str) -> bool:
    # Compare by segments; placeholders match anything
    e_segs = [s for s in endpoint.split('/') if s != '']
    c_segs = [s for s in candidate.split('/') if s != '']
    if len(e_segs) != len(c_segs):
        return False
    for es, cs in zip(e_segs, c_segs):
        if seg_is_placeholder(es):
            continue
        if seg_is_placeholder(cs):
            continue
        if es != cs:
            return False
    return True


def find_template_links() -> List[Tuple[str, int, str]]:
    # Returns (file, line_no, link)
    findings: List[Tuple[str, int, str]] = []
    href_re = re.compile(r"\b(?:href|action)\s*=\s*(['\"])(/[^'\"]*)\1")
    for root, _, files in os.walk(TEMPLATES_DIR):
        for name in files:
            if not (name.endswith('.html') or name.endswith('.htm')):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, start=1):
                        for m in href_re.finditer(line):
                            link = m.group(2)
                            findings.append((os.path.relpath(path, ROOT), i, link))
            except Exception:
                continue
    return findings


def main():
    endpoints = discover_blueprints_and_routes()
    if not endpoints:
        print('No endpoints discovered under app/routes — is the project layout expected?')
    else:
        print(f'Discovered {len(endpoints)} endpoints:')
        for e in endpoints:
            print('  -', e)

    unmatched: List[Tuple[str, int, str]] = []
    for file, line_no, link in find_template_links():
        norm = normalize_template_path(link)
        if any(path_matches(ep, norm) for ep in endpoints):
            continue
        # allow homepage and static resources that aren't routed
        if norm in ('/', ''):
            continue
        # ignore hash and mailto etc.
        if norm.startswith('/static/'):
            continue
        unmatched.append((file, line_no, link))

    print('\nTemplate links not matching any discovered route:')
    if not unmatched:
        print('  None — all checked links have a matching route pattern.')
    else:
        for file, line_no, link in unmatched:
            print(f'  - {file}:{line_no} -> {link}')


if __name__ == '__main__':
    main()
