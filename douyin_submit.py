"""Interpret submit evidence without mistaking navigation labels for receipts."""

from urllib.parse import urlsplit


def upload_outcome(body_text):
    """Classify one visible-text snapshot, not hidden uploader templates."""
    lines = {line.strip() for line in (body_text or "").splitlines() if line.strip()}
    if any(term in line for line in lines for term in ("上传失败", "上传异常")):
        return "failed"
    if any(term in line for line in lines for term in ("正在上传", "上传中")):
        return "pending"
    if lines.intersection({"重新上传", "替换视频", "上传完成", "上传成功"}):
        return "ready"
    return "pending"


def submit_outcome(url, body_text):
    lines = {line.strip() for line in (body_text or "").splitlines() if line.strip()}
    failures = ("发布失败", "提交失败", "上传失败", "上传异常", "请填写", "不能为空", "请先", "未完成")
    if any(term in line for line in lines for term in failures):
        return "blocked"
    if urlsplit(url).path.rstrip("/") == "/creator-micro/content/manage":
        return "accepted"
    if lines.intersection({"发布成功", "视频发布成功", "作品发布成功", "提交成功", "作品已提交审核"}):
        return "accepted"
    return "pending"
