"""Run the pinned Langfuse Claude Code hook with the langfuse-py venv's packages.

Usage: <base python> claude-hook-boot.py <site-packages> <langfuse_hook.py>
The hook payload arrives on stdin and passes through unchanged. A base interpreter plus
site.addsitedir avoids the venv launcher, which cannot start inside a Windows MXC container.
With GEEKY_TRACE_NAME set, the hook's one hard-coded trace name ("Claude Code Turn") is replaced
in memory; the pinned file on disk is never modified.
"""
import os
import site
import sys
import types

site.addsitedir(sys.argv[1])
hook = sys.argv[2]
sys.argv = [hook]
with open(hook, encoding='utf-8') as f:
    source = f.read()
name = os.environ.get('GEEKY_TRACE_NAME')
if name:
    default = 'TRACE_NAME = "Claude Code Turn"'
    if source.count(default) != 1:
        raise SystemExit(f'claude-hook-boot: expected one {default!r} in {hook}')
    source = source.replace(default, f'TRACE_NAME = {name!r}')
module = types.ModuleType('geeky_claude_langfuse_hook')
module.__file__ = hook
sys.modules[module.__name__] = module
exec(compile(source, hook, 'exec'), module.__dict__)
if os.environ.get('GEEKY_AGENT_FAMILY'):
    from claude_identity import install
    install(module)
raise SystemExit(module.main())
