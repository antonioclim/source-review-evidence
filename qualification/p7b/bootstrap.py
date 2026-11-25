"""Workspace-only audit bootstrap. Keeps interpreter flags and target argv.
No installation, .pth or global environment mutation. Direct Python Popen
children, including -I -S with replaced environments, use the same bootstrap.
"""
import sys, os, json, time, runpy, atexit, pathlib, hashlib, importlib.machinery, ast
P=pathlib.Path
args=sys.argv[1:];cfgpath=args[args.index('--cfg')+1];cfg=json.loads(P(cfgpath).read_text());target=args[args.index('--')+1:]
logroot=P(cfg['output']);logroot.mkdir(parents=True,exist_ok=True)
pid=os.getpid();log=logroot/f'process-{pid}.jsonl'
def event(kind,**kw):
 with log.open('a') as f:f.write(json.dumps({'kind':kind,'pid':pid,'ppid':os.getppid(),'monotonic':time.monotonic(),**kw})+'\n')
event('start',target=target,executable=sys.executable,flags={'isolated':sys.flags.isolated,'no_site':sys.flags.no_site,'safe_path':sys.flags.safe_path})
core=set(cfg.get('core',[]));mut=cfg.get('mutation');original_get_code=importlib.machinery.SourceFileLoader.get_code
# Exact bytes bind each fault; unrelated modified source fixtures are reported.
def get_code(self,fullname):
 p=P(self.path)
 if p.name in core and str(p).startswith(cfg['workspace']):
  raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest();event('core_load',file=str(p),sha256=sha,module=fullname)
  if mut and p.name==mut['file']:
   if sha!=mut['source_sha256']:event('mutation_not_applied_source_variant',file=str(p),sha256=sha)
   else:
    tree=ast.parse(raw.decode());nchanges=0
    if mut['kind']=='expression':
     class T(ast.NodeTransformer):
      def visit_BoolOp(self,node):
       nonlocal nchanges
       if node.lineno==mut['line'] and node.col_offset==mut['col']:
        assert ast.dump(node,include_attributes=False)==mut['target_ast']
        replacement=ast.parse(mut['replacement'],mode='eval').body
        replacement=ast.copy_location(replacement,node);ast.fix_missing_locations(replacement);nchanges+=1;return replacement
       return self.generic_visit(node)
     tree=T().visit(tree)
    for n in ast.walk(tree):
     if getattr(n,'lineno',None)==mut['line'] and getattr(n,'col_offset',None)==mut['col']:
      if isinstance(n,ast.Compare) and mut['kind']=='comparison':
       assert type(n.ops[mut['index']]).__name__==mut['before'];n.ops[mut['index']]=getattr(ast,mut['after'])();nchanges+=1
      elif isinstance(n,ast.BoolOp) and mut['kind']=='boolean':
       assert type(n.op).__name__==mut['before'];n.op=getattr(ast,mut['after'])();nchanges+=1
    assert nchanges==1,(mut,nchanges)
    event('mutation_applied',id=mut['id'],file=str(p));return compile(tree,str(p),'exec')
 if cfg.get('compile_identity') and p.name in core and str(p).startswith(cfg['workspace']):return compile(ast.parse(p.read_bytes().decode()),str(p),'exec')
 return original_get_code(self,fullname)
importlib.machinery.SourceFileLoader.get_code=get_code
cov=None
if cfg.get('coverage'):
 old=list(sys.path);sys.path.insert(0,cfg['site_packages']);import coverage;sys.path[:]=old
 cov=coverage.Coverage(data_file=str(logroot/f'.coverage.{pid}'),branch=True,config_file=False,source=cfg.get('source_dirs'),include=cfg.get('include'),data_suffix=False)
 # Keep instrumentation warnings off target stdout/stderr; retain their full text
 # in the audit side channel. This is not warning suppression in the product.
 import warnings
 from coverage.exceptions import CoverageWarning
 old_showwarning=warnings.showwarning
 def showwarning(message,category,filename,lineno,file=None,line=None):
  if issubclass(category,CoverageWarning):
   event('instrumentation_warning',message=str(message),category=category.__name__,filename=filename,line=lineno)
  else:old_showwarning(message,category,filename,lineno,file,line)
 warnings.showwarning=showwarning
 cov.set_option('run:core','ctrace');cov.start()
 import builtins
 expected_trace=sys.gettrace()
 def restore_trace():
  global expected_trace
  if sys.gettrace() is not expected_trace:
   event('trace_changed');cov.stop();cov.start();expected_trace=sys.gettrace()
 builtins._cp7b_restore_trace=restore_trace
 def finish():
  try:cov.stop();cov.save();event('coverage_saved',data=str(logroot/f'.coverage.{pid}'))
  except Exception as e:event('coverage_save_error',error=repr(e))
 atexit.register(finish)
import subprocess
OrigPopen=subprocess.Popen
class AuditPopen(OrigPopen):
 def __init__(self,args,*aa,**kw):
  original=list(args) if isinstance(args,(tuple,list)) else args;rewritten=args
  if isinstance(args,(tuple,list)) and args and not kw.get('shell'):
   argv=[os.fsdecode(x) for x in args];prog=kw.get('executable') or argv[0]
   try:python=(P(prog).resolve()==P(sys.executable).resolve())
   except (OSError,TypeError):python=False
   if python:
    switches=[];j=1
    while j<len(argv) and argv[j].startswith('-') and argv[j] not in ('-c','-m','-'):
     switches.append(argv[j]);j+=1
     if switches[-1] in ('-W','-X') and j<len(argv):switches.append(argv[j]);j+=1
    if j<len(argv):rewritten=[argv[0],*switches,str(P(__file__).resolve()),'--cfg',cfgpath,'--',*argv[j:]]
  super().__init__(rewritten,*aa,**kw)
  event('launch',child=self.pid,original=[os.fsdecode(x) for x in original] if isinstance(original,list) else str(original),measured=rewritten is not args)
subprocess.Popen=AuditPopen
old_exit=os._exit
def exit_now(status):
 if cov:
  try:cov.save();event('coverage_saved_exit')
  except Exception as e:event('coverage_save_error',error=repr(e))
 event('os_exit',status=status);old_exit(status)
os._exit=exit_now
# Audit other process APIs rather than silently asserting they are instrumented.
def audit(kind,args):
 if kind in ('os.fork','os.exec','os.posix_spawn','os.system'):event('other_process_api',api=kind,args=repr(args)[:1000])
sys.addaudithook(audit)
try:
 if target[0]=='-m':
  sys.argv=target[1:]
  if not sys.flags.safe_path:sys.path.insert(0,os.getcwd())
  runpy.run_module(target[1],run_name='__main__',alter_sys=True)
 elif target[0]=='-c':
  sys.argv=['-c',*target[2:]]
  if not sys.flags.safe_path:sys.path.insert(0,'')
  exec(compile(target[1],'<string>','exec'),{'__name__':'__main__','__builtins__':__builtins__})
 else:
  sys.argv=target[:]
  if not sys.flags.safe_path:sys.path.insert(0,str(P(target[0]).resolve().parent))
  runpy.run_path(target[0],run_name='__main__')
 event('end',status=0)
except SystemExit as e:event('end',status=e.code);raise
except BaseException as e:event('unhandled',error=repr(e));raise
