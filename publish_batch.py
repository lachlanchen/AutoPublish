"""Finish independent targets, preserving partial success for scoped retries."""


def publish_batch(publishers, publish, *, before_each=None, on_result=None):
    results = {}
    for publisher, name in publishers:
        if on_result:
            on_result(name, {"status": "running"})
        try:
            if before_each:
                before_each(name)
            if publish(publisher, name) is False:
                raise RuntimeError("Publisher returned unsuccessful status")
        except Exception as exc:
            results[name] = {"status": "failed", "error": str(exc)}
        else:
            results[name] = {"status": "done", "error": None}
        if on_result:
            on_result(name, results[name])
    failures = [f"{name}: {r['error']}" for name, r in results.items() if r["status"] == "failed"]
    if failures:
        raise RuntimeError("Some platforms failed; retry only failed targets: " + "; ".join(failures))
    return results
