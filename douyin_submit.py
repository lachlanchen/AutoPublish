"""Interpret submit evidence without mistaking navigation labels for receipts."""

import re
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


def upload_progress(body_text):
    """Extract uploader evidence without confusing description counts with bytes."""
    text = body_text or ""
    amount = re.search(r"已上传[：:]\s*([\d.]+)\s*(KB|MB|GB)\s*/\s*([\d.]+)\s*(KB|MB|GB)", text, re.I)
    percent = re.search(r"(?m)^\s*(\d{1,3}(?:\.\d+)?)%\s*$", text)
    speed = re.search(r"当前速度[：:]\s*([^\n]+)", text)
    remaining = re.search(r"剩余时间[：:]\s*([^\n]+)", text)
    result = {"status": upload_outcome(text)}
    if percent and 0 <= float(percent[1]) <= 100:
        result["percent"] = float(percent[1])
    if amount:
        units = {"KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}
        result["uploaded_bytes"] = int(float(amount[1]) * units[amount[2].upper()])
        result["total_bytes"] = int(float(amount[3]) * units[amount[4].upper()])
    if speed:
        result["speed"] = speed[1].strip()
    if remaining:
        result["remaining"] = remaining[1].strip()
    return result


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
