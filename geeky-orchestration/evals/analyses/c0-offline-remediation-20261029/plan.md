# Work plan

1. Establish full C0 mock and native fixture baselines inside MXC.
2. Reproduce role handoff, Windows patch and native catalog/history defects offline.
3. Integrate narrowly scoped fixes and focused regression tests.
4. Repeat relevant native MXC fixtures on the changed source and negative cases.
5. Verify evidence, update current records, preserve unresolved external limits.

Parent owns MXC runtime and integration. Worker owns isolated code worktree;
no concurrent writes to a checkout or shared runtime. Stop condition: all
locally reproduced defects fixed and relevant positive/negative checks pass,
with any upstream behavior not reproducible offline explicitly unresolved.
