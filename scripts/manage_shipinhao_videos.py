#!/usr/bin/env python3
"""Inventory and manage Shipinhao video rows through the logged-in browser.

This script is intentionally conservative. Inventory/link discovery is read-only.
Deletion requires --apply plus a title confirmation string.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from selenium import webdriver  # noqa: E402
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException  # noqa: E402
from selenium.webdriver.chrome.service import Service  # noqa: E402

from pub_shipinhao import select_content_frame_collection  # noqa: E402


DEFAULT_MANAGEMENT_URL = "https://channels.weixin.qq.com/platform/post/list"
LALACHAN_KEYWORDS = (
    "lalachan",
    "lala chan",
    "lala xia",
    "啦啦侠",
    "阿芽酱",
    "飒飒君",
    "小云雀",
    "xiaoyunque",
    "seedance",
    "duanpian",
    "啦啦俠",
    "阿芽醬",
    "颯颯君",
    "莎莎君",
    "拉拉夏",
    "莊子機器人",
    "庄子机器人",
)
MUSIC_KEYWORDS = (
    "musia",
    "musica",
    "慕莎",
    "one sky",
    "three lights",
    "hikari ame",
    "lyrics",
    "lyric",
    "歌詞",
    "歌词",
)

INVENTORY_JS = r"""
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function visibleEnough(el) {
  const rect = el.getBoundingClientRect();
  const style = window.getComputedStyle(el);
  return rect.width > 1 && rect.height > 1 && style.display !== 'none' && style.visibility !== 'hidden';
}
function absHref(href) {
  if (!href) return '';
  try { return new URL(href, window.location.href).href; } catch (e) { return href; }
}
const selectors = [
  '.post-feed-item',
  '.ant-table-row',
  '.finder-table-wrap tr',
  '.video-list .item',
  '.post-list .item',
  '[class*="video"][class*="item"]',
  '[class*="post"][class*="item"]',
  'tr',
  '[role="row"]'
];
const rows = [];
for (const selector of selectors) {
  for (const row of queryAll(selector)) {
    if (!visibleEnough(row)) continue;
    const rowText = norm(row.innerText || row.textContent || '');
    if (!rowText || rowText.length < 4) continue;
    const links = Array.from(row.querySelectorAll('a[href]')).map((a) => absHref(a.getAttribute('href'))).filter(Boolean);
    let title = '';
    if (row.matches && row.matches('.post-feed-item')) {
      const postTitle = row.querySelector('.post-title');
      title = norm(postTitle && (postTitle.getAttribute('title') || postTitle.innerText || postTitle.textContent || ''));
      if (!title) {
        const timeLabel = row.querySelector('.time-label');
        const timeText = norm(timeLabel && (timeLabel.innerText || timeLabel.textContent || ''));
        title = timeText || rowText.slice(0, 120);
      }
    } else {
      const titleNode =
        row.querySelector('[class*="title"]') ||
        row.querySelector('[class*="name"]') ||
        row.querySelector('a[href]') ||
        row;
      title = norm(titleNode.getAttribute && (titleNode.getAttribute('title') || titleNode.getAttribute('aria-label')) || titleNode.innerText || titleNode.textContent || '');
    }
    rows.push({
      title: title || rowText.slice(0, 120),
      links,
      text: rowText.slice(0, 1200)
    });
  }
}
const seen = new Set();
return rows.filter((row) => {
  const key = row.title + '|' + row.text.slice(0, 80);
  if (seen.has(key)) return false;
  seen.add(key);
  return true;
});
"""

DELETE_JS = r"""
const query = (arguments[0] || '').toLowerCase();
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function visibleEnough(el) {
  const rect = el.getBoundingClientRect();
  const style = window.getComputedStyle(el);
  return rect.width > 1 && rect.height > 1 && style.display !== 'none' && style.visibility !== 'hidden';
}
function click(el) {
  if (!el) return false;
  el.scrollIntoView({block: 'center'});
  el.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));
  el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
  el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return true;
}
const rows = queryAll('.post-feed-item, .ant-table-row, tr, [role="row"], .item').filter(visibleEnough);
const row = rows.find((item) => norm(item.innerText || item.textContent || '').toLowerCase().includes(query));
if (!row) return {ok: false, reason: 'row-not-found'};
const buttons = Array.from(row.querySelectorAll('button, a, span, div'));
const target = buttons.find((el) => /删除|delete/i.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')));
if (!target) return {ok: false, reason: 'delete-control-not-found', rowText: norm(row.innerText || row.textContent || '').slice(0, 500)};
click(target);
return {ok: true, rowText: norm(row.innerText || row.textContent || '').slice(0, 500)};
"""

CONFIRM_JS = r"""
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function visibleEnough(el) {
  const rect = el.getBoundingClientRect();
  const style = window.getComputedStyle(el);
  return rect.width > 1 && rect.height > 1 && style.display !== 'none' && style.visibility !== 'hidden';
}
function click(el) {
  if (!el) return false;
  el.scrollIntoView({block: 'center'});
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return true;
}
const candidates = queryAll('button, a, span, div');
const target = candidates.find((el) => /确定|确认|删除|delete|confirm/i.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')));
if (!target) return false;
click(target);
return true;
"""

OPEN_EDIT_JS = r"""
const query = (arguments[0] || '').toLowerCase();
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function visibleEnough(el) {
  const rect = el.getBoundingClientRect();
  const style = window.getComputedStyle(el);
  return rect.width > 1 && rect.height > 1 && style.display !== 'none' && style.visibility !== 'hidden';
}
function click(el) {
  if (!el) return false;
  el.scrollIntoView({block: 'center', inline: 'center'});
  el.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));
  el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
  el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return true;
}
const rows = queryAll('.post-feed-item, .ant-table-row, tr, [role="row"], .item, [class*="video"][class*="item"], [class*="post"][class*="item"]').filter(visibleEnough);
const row = rows.find((item) => norm(item.innerText || item.textContent || '').toLowerCase().includes(query));
if (!row) return {ok: false, reason: 'row-not-found'};
const rowText = norm(row.innerText || row.textContent || '').slice(0, 800);
const controls = Array.from(row.querySelectorAll('.edit-cover-item, .edit-cover-text, .opr-item-wrap, .action-content, button, a, span, div'));
const exact = controls.find((el) => norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '') === '修改描述和封面' && visibleEnough(el));
const textMatch = controls.find((el) => /修改描述和封面/.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')) && visibleEnough(el));
const fallback = controls.find((el) => /编辑|編輯|修改|edit/i.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')) && visibleEnough(el));
const target = exact || textMatch || fallback;
if (target) {
  click(target);
  return {ok: true, action: 'clicked-edit', clickedText: norm(target.innerText || target.textContent || target.getAttribute('aria-label') || ''), clickedClass: String(target.className || ''), rowText};
}
const link = Array.from(row.querySelectorAll('a[href]')).find((a) => /edit|post|detail|video/.test(String(a.getAttribute('href') || '')));
if (link) {
  click(link);
  return {ok: true, action: 'clicked-link', href: link.href || link.getAttribute('href'), rowText};
}
click(row);
return {ok: true, action: 'clicked-row', rowText};
"""

FIND_EDIT_TARGET_JS = r"""
const query = (arguments[0] || '').toLowerCase();
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function visibleEnough(el) {
  const rect = el.getBoundingClientRect();
  const style = window.getComputedStyle(el);
  return rect.width > 1 && rect.height > 1 && style.display !== 'none' && style.visibility !== 'hidden';
}
const rows = queryAll('.post-feed-item, .ant-table-row, tr, [role="row"], .item, [class*="video"][class*="item"], [class*="post"][class*="item"]').filter(visibleEnough);
const row = rows.find((item) => norm(item.innerText || item.textContent || '').toLowerCase().includes(query));
if (!row) return null;
row.scrollIntoView({block: 'center', inline: 'nearest'});
const controls = Array.from(row.querySelectorAll('.edit-cover-item, .edit-cover-text, .opr-item-wrap, .action-content, button, a, span, div')).filter(visibleEnough);
const exact = controls.find((el) => norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '') === '修改描述和封面');
const textMatch = controls.find((el) => /修改描述和封面/.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')));
const fallback = controls.find((el) => /编辑|編輯|修改|edit/i.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')));
const target = exact || textMatch || fallback;
if (!target) return null;
const clickTarget = target.closest && target.closest('.edit-cover-item') || target;
clickTarget.scrollIntoView({block: 'center', inline: 'center'});
return clickTarget;
"""

FIND_EDIT_TARGET_COORD_JS = r"""
const query = (arguments[0] || '').toLowerCase();
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function visibleEnough(el) {
  const rect = el.getBoundingClientRect();
  const style = window.getComputedStyle(el);
  return rect.width > 1 && rect.height > 1 && style.display !== 'none' && style.visibility !== 'hidden';
}
const rows = queryAll('.post-feed-item, .ant-table-row, tr, [role="row"], .item, [class*="video"][class*="item"], [class*="post"][class*="item"]').filter(visibleEnough);
const row = rows.find((item) => norm(item.innerText || item.textContent || '').toLowerCase().includes(query));
if (!row) return {ok: false, reason: 'row-not-found', visibleRows: rows.length};
row.scrollIntoView({block: 'center', inline: 'nearest'});
const wrap = Array.from(row.querySelectorAll('.edit-cover-item')).find(visibleEnough);
const controls = Array.from(row.querySelectorAll('.edit-cover-item, .edit-cover-text, .opr-item-wrap, .action-content, button, a, span, div')).filter(visibleEnough);
const exact = controls.find((el) => norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '') === '修改描述和封面');
const textMatch = controls.find((el) => /修改描述和封面/.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')));
const fallback = controls.find((el) => /编辑|編輯|修改|edit/i.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')));
const raw = wrap || exact || textMatch || fallback;
if (!raw) return {ok: false, reason: 'target-not-found', rowText: norm(row.innerText || row.textContent || '').slice(0, 300)};
const target = (raw.querySelector && (raw.querySelector('.opr-item') || raw.querySelector('svg'))) || raw;
target.scrollIntoView({block: 'center', inline: 'center'});
const rect = target.getBoundingClientRect();
return {
  ok: true,
  x: Math.round(rect.left + rect.width / 2),
  y: Math.round(rect.top + rect.height / 2),
  tag: target.tagName,
  className: String(target.className || ''),
  text: norm(raw.innerText || raw.textContent || raw.getAttribute('aria-label') || ''),
  rect: {left: rect.left, top: rect.top, width: rect.width, height: rect.height}
};
"""

EDIT_DIALOG_STATE_JS = r"""
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function visibleEnough(el) {
  const rect = el.getBoundingClientRect();
  const style = window.getComputedStyle(el);
  return rect.width > 1 && rect.height > 1 && style.display !== 'none' && style.visibility !== 'hidden';
}
const editors = queryAll('.input-editor[contenteditable], [contenteditable], textarea').filter(visibleEnough);
const descriptionNode = queryAll('.edit-desc-content, .edit-select-area')
  .filter((el) => /edit-select-area|edit-desc-content/.test(String(el.className || '')))
  .find(visibleEnough);
const buttons = queryAll('button, a, span, div')
  .filter(visibleEnough)
  .map((el) => norm(el.innerText || el.textContent || el.getAttribute('aria-label') || ''))
  .filter(Boolean);
return {
  url: location.href,
  isCoverEdit: /\/coverEdit/.test(location.href) || buttons.some((text) => text.includes('修改描述和封面')),
  descriptionText: descriptionNode ? norm(descriptionNode.innerText || descriptionNode.textContent || '') : '',
  hasEditor: editors.length > 0,
  editors: editors.map((el) => ({
    tag: el.tagName,
    className: String(el.className || ''),
    placeholder: el.getAttribute('placeholder') || el.getAttribute('data-placeholder') || '',
    text: norm(el.innerText || el.textContent || el.value || '').slice(0, 120)
  })),
  buttons: buttons.slice(-30)
};
"""

ACK_COVER_EDIT_HINT_JS = r"""
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function visibleEnough(el) {
  const rect = el.getBoundingClientRect();
  const style = window.getComputedStyle(el);
  return rect.width > 1 && rect.height > 1 && style.display !== 'none' && style.visibility !== 'hidden';
}
const button = queryAll('button, a, span, div')
  .filter(visibleEnough)
  .find((el) => /^我知道了$/.test(norm(el.innerText || el.textContent || '')));
if (!button) return false;
button.click();
button.dispatchEvent(new MouseEvent('click', {bubbles: true}));
return true;
"""

SAVE_EDIT_JS = r"""
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function disabled(el) {
  const cls = String(el.className || '');
  return !!el.disabled || el.getAttribute('disabled') !== null || /\bdisabled\b/.test(cls);
}
function click(el) {
  if (!el) return false;
  el.scrollIntoView({block: 'center'});
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return true;
}
const buttons = queryAll('button, a, span, div');
const target = buttons.find((el) => /^(保存|保存修改|完成|确定|確認|提交|更新|发表|發表)$/.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')) && !disabled(el));
if (!target) return {ok: false, reason: 'save-control-not-found'};
click(target);
return {ok: true, text: norm(target.innerText || target.textContent || target.getAttribute('aria-label') || '')};
"""

ENSURE_COLLECTION_JS = r"""
const name = (arguments[0] || '').trim();
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function visibleEnough(el) {
  const rect = el.getBoundingClientRect();
  const style = window.getComputedStyle(el);
  return rect.width > 1 && rect.height > 1 && style.display !== 'none' && style.visibility !== 'hidden';
}
function click(el) {
  if (!el) return false;
  el.scrollIntoView({block: 'center'});
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return true;
}
function setValue(input, value) {
  const proto = input instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
  setter.call(input, value);
  input.dispatchEvent(new Event('input', {bubbles: true}));
  input.dispatchEvent(new Event('change', {bubbles: true}));
}
if (!name) return {ok: false, stage: 'validate', reason: 'empty-name'};

const collectionTab = queryAll('button, a, span, div').find((el) => /^合集(\s*\(\d+\))?$/.test(norm(el.innerText || el.textContent || '')));
if (collectionTab) click(collectionTab);

const existingRows = queryAll('.collection-table .ant-table-row, .collection-wrap .ant-table-row, tr.ant-table-row')
  .filter(visibleEnough)
  .map((row) => norm(row.innerText || row.textContent || ''));
const existingNames = existingRows.map((rowText) => {
  const parts = rowText.split(/\s+/).filter(Boolean);
  return parts[0] || rowText;
});
if (existingNames.includes(name) || existingRows.some((rowText) => rowText === name || rowText.startsWith(name + ' '))) {
  return {ok: true, stage: 'exists', name, existingNames};
}

const create =
  queryAll('button.weui-desktop-btn_primary, button')
    .find((el) => norm(el.innerText || el.textContent || '') === '创建合集' && visibleEnough(el)) ||
  queryAll('button, a, span, div')
    .find((el) => norm(el.innerText || el.textContent || '') === '创建合集' && visibleEnough(el) && /button|btn/i.test(String(el.className || '') + ' ' + el.tagName));
if (!create) return {ok: false, stage: 'open-create', reason: 'create-control-not-found'};
click(create);
return {ok: true, stage: 'opened-create', name, existingNames, clickedTag: create.tagName, clickedClass: String(create.className || '')};
"""

FILL_COLLECTION_DIALOG_JS = r"""
const name = (arguments[0] || '').trim();
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function visibleEnough(el) {
  const rect = el.getBoundingClientRect();
  const style = window.getComputedStyle(el);
  return rect.width > 1 && rect.height > 1 && style.display !== 'none' && style.visibility !== 'hidden';
}
function click(el) {
  if (!el) return false;
  el.scrollIntoView({block: 'center'});
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return true;
}
function setValue(input, value) {
  const proto = input instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
  setter.call(input, value);
  input.dispatchEvent(new Event('input', {bubbles: true}));
  input.dispatchEvent(new Event('change', {bubbles: true}));
}
const inputs = queryAll('input[type="text"], input').filter(visibleEnough);
const input = inputs.find((el) => /合集|标题|標題|有趣/.test(el.getAttribute('placeholder') || '')) || inputs[0];
if (!input) return {ok: false, stage: 'fill-name', reason: 'input-not-found'};
setValue(input, name);
const buttons = queryAll('button, a, span, div').filter(visibleEnough);
const submit = buttons.find((el) => /^创建$/.test(norm(el.innerText || el.textContent || '')) && !/disabled/.test(String(el.className || '')));
if (!submit) return {ok: false, stage: 'submit', reason: 'submit-control-not-found'};
click(submit);
return {ok: true, stage: 'submitted', name};
"""

ACK_COLLECTION_SUCCESS_JS = r"""
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function visibleEnough(el) {
  const rect = el.getBoundingClientRect();
  const style = window.getComputedStyle(el);
  return rect.width > 1 && rect.height > 1 && style.display !== 'none' && style.visibility !== 'hidden';
}
function click(el) {
  if (!el) return false;
  el.scrollIntoView({block: 'center'});
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return true;
}
const button = queryAll('button, a, span, div').filter(visibleEnough).find((el) => /^(我知道了|确定|確認)$/.test(norm(el.innerText || el.textContent || '')));
if (!button) return false;
click(button);
return true;
"""


def resolve_chromedriver(chromedriver: str | None = None) -> str | None:
    if chromedriver:
        return chromedriver
    for key in ("AUTOPUBLISH_CHROMEDRIVER", "CHROMEDRIVER_PATH"):
        value = os.environ.get(key)
        if value and Path(value).exists():
            return value
    for candidate in (
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/snap/bin/chromium.chromedriver",
    ):
        if Path(candidate).exists():
            return candidate
    return shutil.which("chromedriver")


def connect_driver(port: int, chromedriver: str | None = None):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    driver_path = resolve_chromedriver(chromedriver)
    service = Service(executable_path=driver_path) if driver_path else Service()
    return webdriver.Chrome(service=service, options=options)


def edit_dialog_state(driver) -> dict:
    state = driver.execute_script(EDIT_DIALOG_STATE_JS)
    return state if isinstance(state, dict) else {}


def click_viewport_point(driver, x: int, y: int) -> None:
    driver.execute_cdp_cmd(
        "Input.dispatchMouseEvent",
        {"type": "mouseMoved", "x": x, "y": y, "button": "none"},
    )
    driver.execute_cdp_cmd(
        "Input.dispatchMouseEvent",
        {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1},
    )
    driver.execute_cdp_cmd(
        "Input.dispatchMouseEvent",
        {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1},
    )


def acknowledge_cover_edit_hint(driver) -> bool:
    try:
        return bool(driver.execute_script(ACK_COVER_EDIT_HINT_JS))
    except WebDriverException:
        return False


def open_edit_row(driver, query: str, *, pause: float = 2.0, attempts: int = 4) -> dict:
    """Open the Shipinhao "modify description and cover" editor for a row."""
    last_state: dict | None = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            point = driver.execute_script(FIND_EDIT_TARGET_COORD_JS, query)
            if not isinstance(point, dict) or not point.get("ok"):
                last_state = {"ok": False, "reason": "edit-target-not-found", "attempt": attempt, "target": point}
                time.sleep(0.8)
                continue
            click_viewport_point(driver, int(point["x"]), int(point["y"]))
            deadline = time.time() + max(4.0, pause + 3.0)
            state: dict = {}
            while time.time() < deadline:
                acknowledge_cover_edit_hint(driver)
                state = edit_dialog_state(driver)
                if state.get("hasEditor") or state.get("isCoverEdit"):
                    return {"ok": True, "attempt": attempt, "target": point, "dialog_state": state}
                time.sleep(0.5)
            last_state = {"ok": False, "reason": "editor-not-open", "attempt": attempt, "dialog_state": state}
        except StaleElementReferenceException as exc:
            last_state = {"ok": False, "reason": "stale-element", "attempt": attempt, "error": str(exc)}
        except WebDriverException as exc:
            last_state = {"ok": False, "reason": "webdriver-error", "attempt": attempt, "error": str(exc)}
        time.sleep(max(0.8, pause / 2))

    # Fallback to the JavaScript dispatch path. It is less reliable in the
    # current Vue list, but keeping it helps older layouts.
    js_state = driver.execute_script(OPEN_EDIT_JS, query)
    time.sleep(max(1.5, pause))
    acknowledge_cover_edit_hint(driver)
    dialog_state = edit_dialog_state(driver)
    if dialog_state.get("hasEditor") or dialog_state.get("isCoverEdit"):
        return {"ok": True, "fallback": True, "open_state": js_state, "dialog_state": dialog_state}
    return last_state or {"ok": False, "reason": "open-failed", "open_state": js_state, "dialog_state": dialog_state}


def classify(row: dict) -> str:
    text = f"{row.get('title', '')}\n{row.get('text', '')}".lower()
    if any(keyword in text for keyword in MUSIC_KEYWORDS):
        return "music"
    if any(keyword in text for keyword in LALACHAN_KEYWORDS):
        return "lalachan"
    return "simplelife"


def inventory(driver, *, url: str | None, scrolls: int, pause: float) -> list[dict]:
    if url:
        driver.get(url)
        time.sleep(5)
    rows: list[dict] = []
    seen = set()
    for _ in range(max(1, scrolls)):
        current_rows = driver.execute_script(INVENTORY_JS) or []
        for row in current_rows:
            if not isinstance(row, dict):
                continue
            row["category_guess"] = classify(row)
            key = row.get("title") + "|" + str(row.get("links") or "")
            if key not in seen:
                seen.add(key)
                rows.append(row)
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(pause)
    return rows


def save_rows(rows: list[dict], output: str | None) -> None:
    payload = json.dumps(rows, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


def delete_row(driver, query: str, *, title_contains: str, apply: bool) -> dict:
    if not query:
        raise ValueError("--query is required for delete")
    if not title_contains:
        raise ValueError("--title-contains is required for delete")
    if not apply:
        return {"query": query, "title_contains": title_contains, "dry_run": True}
    state = driver.execute_script(DELETE_JS, query)
    text = json.dumps(state, ensure_ascii=False).lower()
    if title_contains.lower() not in text:
        raise RuntimeError("title confirmation text was not found in the matched row")
    time.sleep(1)
    confirmed = driver.execute_script(CONFIRM_JS)
    return {"query": query, "delete_clicked": state, "confirm_clicked": bool(confirmed)}


def move_row_to_collection(driver, query: str, collection: str, *, apply: bool, pause: float = 2.0) -> dict:
    if not query:
        raise ValueError("query is required")
    if not collection:
        raise ValueError("collection is required")
    if not apply:
        return {"query": query, "target_collection": collection, "dry_run": True}

    before_url = driver.current_url
    open_state = open_edit_row(driver, query, pause=pause)
    if not isinstance(open_state, dict) or not open_state.get("ok"):
        return {"query": query, "target_collection": collection, "ok": False, "stage": "open-edit", "state": open_state}
    time.sleep(max(1.0, pause))

    collection_state = None
    last_error = None
    for _ in range(20):
        try:
            collection_state = select_content_frame_collection(driver, collection, duration=3)
            break
        except Exception as exc:
            last_error = str(exc)
            time.sleep(1)
    if collection_state is None:
        return {
            "query": query,
            "target_collection": collection,
            "ok": False,
            "stage": "select-collection",
            "open_state": open_state,
            "error": last_error,
            "url": driver.current_url,
        }

    save_state = None
    for _ in range(20):
        save_state = driver.execute_script(SAVE_EDIT_JS)
        if isinstance(save_state, dict) and save_state.get("ok"):
            break
        time.sleep(1)
    time.sleep(max(2.0, pause))
    return {
        "query": query,
        "target_collection": collection,
        "ok": bool(isinstance(save_state, dict) and save_state.get("ok")),
        "open_state": open_state,
        "collection_state": collection_state,
        "save_state": save_state,
        "before_url": before_url,
        "after_url": driver.current_url,
    }


def ensure_collection(driver, name: str, *, apply: bool, pause: float = 1.5) -> dict:
    if not name:
        raise ValueError("collection name is required")
    if not apply:
        return {"name": name, "dry_run": True}
    open_state = driver.execute_script(ENSURE_COLLECTION_JS, name)
    if isinstance(open_state, dict) and open_state.get("stage") == "exists":
        return open_state
    if not isinstance(open_state, dict) or not open_state.get("ok"):
        return {"ok": False, "name": name, "stage": "open-create", "state": open_state}
    time.sleep(pause)
    fill_state = driver.execute_script(FILL_COLLECTION_DIALOG_JS, name)
    if not isinstance(fill_state, dict) or not fill_state.get("ok"):
        return {"ok": False, "name": name, "stage": "fill-dialog", "open_state": open_state, "state": fill_state}
    time.sleep(max(2.0, pause))
    ack_state = driver.execute_script(ACK_COLLECTION_SUCCESS_JS)
    time.sleep(max(2.0, pause))
    return {"ok": True, "name": name, "open_state": open_state, "fill_state": fill_state, "ack_state": bool(ack_state)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage Shipinhao video rows by attached browser session.")
    parser.add_argument("command", choices=["inventory", "link", "delete", "ensure-collection", "move", "move-lalachan", "move-music", "move-classified"])
    parser.add_argument("--port", type=int, default=5006)
    parser.add_argument("--chromedriver")
    parser.add_argument("--url", default=DEFAULT_MANAGEMENT_URL, help="Use empty string to keep current tab.")
    parser.add_argument("--scrolls", type=int, default=30)
    parser.add_argument("--pause", type=float, default=1.0)
    parser.add_argument("--output")
    parser.add_argument("--query")
    parser.add_argument("--title-contains", default="")
    parser.add_argument("--collection")
    parser.add_argument("--lalachan-collection", default="啦啦侠")
    parser.add_argument("--music-collection", default="Musia")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    driver = connect_driver(args.port, args.chromedriver)
    url = args.url if args.url else None

    if args.command == "inventory":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        save_rows(rows, args.output)
        return 0

    if args.command == "link":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        query = (args.query or "").lower()
        matches = [row for row in rows if query in json.dumps(row, ensure_ascii=False).lower()]
        save_rows(matches, args.output)
        return 0

    if args.command == "delete":
        print(json.dumps(delete_row(driver, args.query or "", title_contains=args.title_contains, apply=args.apply), ensure_ascii=False, indent=2))
        return 0

    if args.command == "ensure-collection":
        print(json.dumps(ensure_collection(driver, args.collection or args.query or "", apply=args.apply, pause=args.pause), ensure_ascii=False, indent=2))
        return 0

    if args.command == "move":
        print(json.dumps(
            move_row_to_collection(
                driver,
                args.query or "",
                args.collection or args.lalachan_collection,
                apply=args.apply,
                pause=args.pause,
            ),
            ensure_ascii=False,
            indent=2,
        ))
        return 0

    if args.command == "move-lalachan":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        targets = [row for row in rows if row.get("category_guess") == "lalachan"]
        collection = args.collection or args.lalachan_collection
        results = [
            move_row_to_collection(driver, row.get("title") or row.get("text", "")[:80], collection, apply=args.apply, pause=args.pause)
            for row in targets
        ]
        save_rows(results or [{"target_collection": collection, "dry_run": not args.apply, "candidates": []}], args.output)
        return 0

    if args.command == "move-music":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        targets = [row for row in rows if row.get("category_guess") == "music"]
        collection = args.collection or args.music_collection
        results = [
            move_row_to_collection(driver, row.get("title") or row.get("text", "")[:80], collection, apply=args.apply, pause=args.pause)
            for row in targets
        ]
        save_rows(results or [{"target_collection": collection, "dry_run": not args.apply, "candidates": []}], args.output)
        return 0

    if args.command == "move-classified":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        results = []
        for row in rows:
            category = row.get("category_guess")
            if category == "music":
                results.append(move_row_to_collection(driver, row.get("title") or row.get("text", "")[:80], args.music_collection, apply=args.apply, pause=args.pause))
            elif category == "lalachan":
                results.append(move_row_to_collection(driver, row.get("title") or row.get("text", "")[:80], args.lalachan_collection, apply=args.apply, pause=args.pause))
        save_rows(results, args.output)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
