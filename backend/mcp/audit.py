import json, time

def audit_log(tool, args, kwargs, res):
    print(json.dumps({
        "ts": time.time(),
        "tool": tool,
        "args": str(args),
        "kwargs": kwargs,
        "result_summary": str(res)[:200]
    }))