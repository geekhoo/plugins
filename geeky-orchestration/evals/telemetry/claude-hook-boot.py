"""Run the pinned Langfuse Claude Code hook with the langfuse-py venv's packages.

Usage: <base python> claude-hook-boot.py <site-packages> <langfuse_hook.py>
The hook payload arrives on stdin and passes through unchanged. A base interpreter plus
site.addsitedir avoids the venv launcher, which cannot start inside a Windows MXC container.
"""
import runpy
import site
import sys

site.addsitedir(sys.argv[1])
hook = sys.argv[2]
sys.argv = [hook]
runpy.run_path(hook, run_name='__main__')
