# AutoSocial AI — Bug Report

Generated: 2025-06-26

Status: Pending fix

---

## Summary

| # | File | Severity | Bug |
|---|---|---|---|
| 1 | task_runner.py | High | Closes externally-owned BrowserManager in finally |
| 2 | task_runner.py | Low | Dead `driver = None` assignment |
| 3 | comment_task_runner.py | High | No exception handling on platform calls |
| 4 | comment_task_runner.py | Medium | Inconsistent return types for unsupported platform |
| 5 | services.py | Medium | Hash collision risk without platform comment ID |
| 6 | services.py | High | Race condition on check-then-create |
| 7 | browser_manager.py | Medium | Windows-only process cleanup |
| 8 | browser_manager.py | Medium | Windows-only Chrome profile path |
| 9 | browser_manager.py | Medium | Dead driver Chrome process leak |
| 10 | browser_manager.py | Low | Missing cleanup in close_browser |
| 11 | browser_manager.py | Medium | Conflicting detach vs quit behavior |
| 12 | task_runner.py | Low | Hard-coded sleep instead of explicit waits |
| 13 | services.py | Medium | Non-unique comment_id field |
| 14 | task_runner.py | High | Media URLs passed to platform modules without download |

---

## Bug Details

### Bug 1 — task_runner.py: Closes externally-owned BrowserManager in finally

**Severity:** High

**Description:**
The `finally` block calls `manager.close_browser()` unconditionally. When a `browser_manager` is passed in from the outside (e.g., the agent reuses it across tasks), closing it here destroys the shared driver instance, making the passed-in `browser_manager` unusable for subsequent tasks.

**Root cause:**
The function both creates its own `BrowserManager` as a fallback AND closes whatever manager it has in `finally`. The caller owns the lifecycle when it passes a manager in.

**Solution:**
Only close the browser if the function created the manager itself. Track ownership with a boolean flag:

