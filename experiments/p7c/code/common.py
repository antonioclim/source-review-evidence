"""Local-only file operations and independent traversal for P7C."""
from __future__ import annotations
import ast, hashlib, json, shutil
from pathlib import Path

def sha(data): return hashlib.sha256(data).hexdigest()
def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def load(path):
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out: raise ValueError('duplicate JSON key '+k)
            out[k]=v
        return out
    return json.loads(Path(path).read_text(encoding='utf-8'),object_pairs_hook=unique,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
def save(path,x):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:f.write(json.dumps(x,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n')
def identities(root):
    return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}

def overlay_profiles(source:Path, destination:Path, thresholds):
    """Admitted explicit fixture namespace; unchanged code, two declared JSON changes.
    This is not a production profile update. Profile version fields follow the
    existing schema; the changed registry/inventory hashes identify each fixture.
    """
    shutil.copytree(source,destination)
    rel='research/s04/profiles.v1.json';reg=load(destination/rel)
    for profile,t in zip(reg['profiles'][1:],thresholds):
        rule=next(r for r in profile['rules'] if r['rule_id']=='mccabe_complexity')
        rule['threshold_set']=dict(zip(('lower','nominal','upper'),t))
    raw=json.dumps(reg,indent=2,ensure_ascii=False)+'\n';(destination/rel).write_text(raw)
    ip=destination/'research/ce04/component-inventory.v1.json';inv=load(ip)
    if rel in inv['inherited_sha256']:inv['inherited_sha256'][rel]=sha(raw.encode())
    elif rel in inv.get('revised_components',{}):inv['revised_components'][rel]['candidate_sha256']=sha(raw.encode())
    else:raise ValueError('unbound profile registry')
    ip.write_text(json.dumps(inv,indent=2,ensure_ascii=False)+'\n')
    return {'fixture_scope':'source-data overlay only, not default/public profile','changed':{rel:sha(raw.encode()),'research/ce04/component-inventory.v1.json':sha(ip.read_bytes())},'thresholds':thresholds}

def traversal(source):
    """Iterative AST audit, not the production NodeVisitor. Parser is shared CPython.
    Emitted source is parsed, never executed. Excluded subtree children are skipped.
    Source-byte admission is a caller precondition. Match the admitted text's
    one-BOM/newline normalisation and the production type-comment parser mode;
    this helper does not enforce the byte limit or replace source binding.
    """
    if source.startswith('\ufeff'):source=source[1:]
    source=source.replace('\r\n','\n').replace('\r','\n')
    tree=ast.parse(source,type_comments=True);roots=sorted((n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))),key=lambda n:(n.lineno,n.col_offset,n.name))
    rows=[]
    for root in roots:
        stack=[(root,0)];dp=0;depth=0;spans=[]
        while stack:
            node,d=stack.pop()
            if node is not root and isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda,ast.ClassDef)):continue
            if hasattr(node,'lineno') and hasattr(node,'end_lineno'):spans.append([node.lineno,node.end_lineno,node.col_offset,node.end_col_offset])
            typ=type(node).__name__
            if typ in ('If','For','AsyncFor','While','IfExp'):dp+=1
            if typ=='BoolOp':dp+=len(node.values)-1
            if typ in ('Try','TryStar'):dp+=len(node.handlers)
            if typ=='Match':dp+=len(node.cases)
            if typ in ('ListComp','SetComp','DictComp','GeneratorExp'):dp+=len(node.generators)+sum(len(g.ifs) for g in node.generators)
            nd=d+int(typ in ('If','For','AsyncFor','While','Try','TryStar','Match','With','AsyncWith'))
            depth=max(depth,nd);stack.extend((child,nd) for child in ast.iter_child_nodes(node))
        rows.append({'name':root.name,'start':root.lineno,'end':root.end_lineno,'traversal_start':min([root.lineno]+[d.lineno for d in root.decorator_list]),'dp':dp,'depth':depth,'spans':spans})
    return rows


def callable_index(rows):
    """Bind traversal/expected rows to the kernel's complete callable identity.

    Parsed definitions have distinct start lines. Source order therefore agrees
    with the kernel's (line, column, name) order. Refuse duplicate definition
    lines rather than invent an ordering from information absent from these rows.
    Simple names are descriptive and are not unique across scopes or rebindings.
    """
    indexed={};starts=set()
    for ordinal,row in enumerate(sorted(rows,key=lambda r:(r['start'],r['name'])),1):
        if row['start'] in starts:raise ValueError('ambiguous callable definition line')
        starts.add(row['start'])
        entity_id=f"python_callable:{ordinal}:{row['name']}:L{row['start']}"
        indexed[entity_id]=row
    return indexed
