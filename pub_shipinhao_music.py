import json
import os
import time
import traceback

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from login_shipinhao import ShiPinHaoLogin
from pub_shipinhao import (
    _execute_in_content_frame,
    click_content_frame_css,
    dismiss_alert,
    dismiss_overlays,
    find_any_in_content_frame,
    remove_non_bmp,
    save_debug_snapshot,
    send_file_to_content_frame,
)
from utils import bring_to_front, close_extra_tabs


SHIPINHAO_MUSIC_WINDOW_PATTERNS = ["视频号", "视频号助手", "发表音乐", "音乐"]
SHIPINHAO_MUSIC_UPLOAD_INPUT_SELECTORS = [
    'input[type="file"][accept*="audio"]',
    'input[type="file"][accept*="mp3"]',
    'input[type="file"][accept*="wav"]',
    'input[type="file"][accept*=".mp3"]',
    'input[type="file"][accept*=".wav"]',
    'input[type="file"]:not([accept*="video"]):not([accept*="image"])',
]
SHIPINHAO_MUSIC_IMAGE_INPUT_SELECTORS = [
    'input[type="file"][accept*="image"]',
    'input[type="file"][accept*="png"]',
    'input[type="file"][accept*="jpg"]',
    'input[type="file"][accept*="jpeg"]',
]
SHIPINHAO_MUSIC_PROOF_INPUT_SELECTORS = [
    'input[type="file"][accept*=".zip"]',
    'input[type="file"][accept*=".rar"]',
    'input[type="file"][accept*="zip"]',
    'input[type="file"][accept*="rar"]',
]
SHIPINHAO_MUSIC_MANAGEMENT_URL = "https://channels.weixin.qq.com/platform/post/music"


MUSIC_PAGE_STATE_SCRIPT = r"""
const text = (document.body && document.body.innerText || '').replace(/\s+/g, ' ').trim();
const fileInputs = Array.from(document.querySelectorAll('input[type="file"]')).map((el) => ({
  accept: el.getAttribute('accept') || '',
  multiple: !!el.multiple,
}));
const hasAudioInput = fileInputs.some((item) => /audio|mp3|wav/i.test(item.accept));
const formMarkers = ['添加音乐', '歌曲名称', '歌词内容', '音乐人说', '歌曲语言', '歌曲曲风'];
const entryMarkers = ['发表音乐', '上传一首歌曲'];
const unavailableMarkers = ['暂时无法使用该功能', '无法使用该功能'];
return {
  ready: hasAudioInput || formMarkers.some((marker) => text.includes(marker)),
  hasAudioInput,
  hasEntry: entryMarkers.some((marker) => text.includes(marker)),
  unavailable: unavailableMarkers.some((marker) => text.includes(marker)),
  text: text.slice(0, 1200),
  fileInputs,
  url: location.href,
};
"""


SET_FIELD_BY_HINT_SCRIPT = r"""
const labels = Array.isArray(arguments[0]) ? arguments[0] : [arguments[0]];
const hints = Array.isArray(arguments[1]) ? arguments[1] : [arguments[1]];
const value = arguments[2] || '';

function norm(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}

function isVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (!style || style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') {
    return false;
  }
  const rect = el.getBoundingClientRect();
  return !!(rect.width || rect.height || el.getClientRects().length);
}

function setValue(el, value) {
  el.scrollIntoView({block: 'center'});
  el.focus();
  if ((el.getAttribute('contenteditable') || '').toLowerCase() === 'true') {
    el.innerHTML = '';
    el.textContent = value;
    el.dispatchEvent(new InputEvent('input', {
      bubbles: true,
      cancelable: true,
      data: value,
      inputType: 'insertText',
    }));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    el.blur();
    return norm(el.innerText || el.textContent);
  }
  const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
  const descriptor = Object.getOwnPropertyDescriptor(proto, 'value');
  if (descriptor && descriptor.set) {
    descriptor.set.call(el, value);
  } else {
    el.value = value;
  }
  el.dispatchEvent(new Event('input', {bubbles: true}));
  el.dispatchEvent(new Event('change', {bubbles: true}));
  el.blur();
  return el.value || '';
}

const fields = Array.from(document.querySelectorAll(
  'input:not([type="file"]):not([type="hidden"]), textarea, [contenteditable="true"]'
));

function fieldText(el) {
  return norm([
    el.getAttribute('placeholder'),
    el.getAttribute('aria-label'),
    el.getAttribute('name'),
    el.getAttribute('title'),
    el.getAttribute('data-placeholder'),
    el.className,
  ].join(' '));
}

for (const hint of hints.filter(Boolean)) {
  const match = fields.find((el) => fieldText(el).includes(hint) && isVisible(el))
    || fields.find((el) => fieldText(el).includes(hint));
  if (match) {
    return {ok: true, value: setValue(match, value), method: 'hint', hint, tag: match.tagName};
  }
}

const textNodes = Array.from(document.querySelectorAll('*')).filter((el) => {
  const text = norm(el.innerText || el.textContent);
  return text && labels.some((label) => label && text.includes(label));
});

for (const labelEl of textNodes) {
  let scope = labelEl.closest('.form-item, .weui-desktop-dialog__bd, .weui-desktop-form__input-area, .cell-center, .post-with-link, .music-form-item');
  let cursor = labelEl;
  while (!scope && cursor && cursor.parentElement) {
    cursor = cursor.parentElement;
    const localFields = cursor.querySelectorAll
      ? cursor.querySelectorAll('input:not([type="file"]):not([type="hidden"]), textarea, [contenteditable="true"]')
      : [];
    if (localFields.length) {
      scope = cursor;
      break;
    }
  }
  const candidates = scope && scope.querySelectorAll
    ? Array.from(scope.querySelectorAll('input:not([type="file"]):not([type="hidden"]), textarea, [contenteditable="true"]'))
    : [];
  const field = candidates.find(isVisible) || candidates[0];
  if (field) {
    return {ok: true, value: setValue(field, value), method: 'label', label: norm(labelEl.innerText || labelEl.textContent), tag: field.tagName};
  }
}

return {ok: false, labels, hints, available: fields.map(fieldText).filter(Boolean).slice(0, 40)};
"""


CLICK_TEXT_SCRIPT = r"""
const texts = Array.isArray(arguments[0]) ? arguments[0] : [arguments[0]];
const exact = !!arguments[1];

function norm(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}

function isVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (!style || style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') {
    return false;
  }
  const rect = el.getBoundingClientRect();
  return !!(rect.width || rect.height || el.getClientRects().length);
}

function matchText(el) {
  const text = norm(el.innerText || el.textContent);
  if (!text) return false;
  return texts.some((target) => exact ? text === target : text.includes(target));
}

const candidates = Array.from(document.querySelectorAll('button, label, a, span, div, input[type="checkbox"]'));
const matches = candidates.filter((el) => isVisible(el) && matchText(el));
matches.sort((a, b) => {
  const aText = norm(a.innerText || a.textContent);
  const bText = norm(b.innerText || b.textContent);
  const aExact = texts.some((target) => aText === target) ? 0 : 1;
  const bExact = texts.some((target) => bText === target) ? 0 : 1;
  return aExact - bExact || aText.length - bText.length;
});
const match = matches[0];
if (!match) return false;
const target = match.closest('button, label, a, .weui-desktop-btn_wrp, .ant-checkbox-wrapper') || match;
target.scrollIntoView({block: 'center'});
target.dispatchEvent(new MouseEvent('mouseover', {bubbles: true, cancelable: true, view: window}));
target.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, view: window}));
if (typeof target.click === 'function') target.click();
target.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, view: window}));
target.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
return true;
"""


BUTTON_STATE_SCRIPT = r"""
const targetText = arguments[0] || '完成';
function norm(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}
function disabled(el) {
  if (!el) return true;
  const className = (el.className || '').toString();
  return !!el.disabled || el.getAttribute('disabled') !== null || el.getAttribute('aria-disabled') === 'true' || /disabled/i.test(className);
}
const button = Array.from(document.querySelectorAll('button')).find((el) => norm(el.innerText || el.textContent) === targetText);
return {exists: !!button, disabled: disabled(button), className: button ? (button.className || '').toString() : null};
"""


MUSIC_MANAGEMENT_STATE_SCRIPT = r"""
const desiredTab = arguments[0] || '';
const shouldClick = !!arguments[1];
const maxDepth = 8;

function norm(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}

function isVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (!style || style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') {
    return false;
  }
  const rect = el.getBoundingClientRect();
  return !!(rect.width || rect.height || el.getClientRects().length);
}

function queryAllDeep(root, selector, depth, acc) {
  if (!root || depth > maxDepth || !root.querySelectorAll) return acc;
  for (const el of root.querySelectorAll(selector)) {
    acc.push(el);
  }
  for (const el of root.querySelectorAll('*')) {
    if (el.shadowRoot) {
      queryAllDeep(el.shadowRoot, selector, depth + 1, acc);
    }
  }
  return acc;
}

function all(selector) {
  return queryAllDeep(document, selector, 0, []);
}

function click(el) {
  el.scrollIntoView({block: 'center'});
  el.dispatchEvent(new MouseEvent('mouseover', {bubbles: true, cancelable: true, view: window}));
  el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, view: window}));
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, view: window}));
  el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
}

const tabNodes = all('li.weui-desktop-tab__nav, .weui-desktop-tab__nav, [role="tab"], button, a')
  .filter((el) => isVisible(el))
  .map((el) => ({
    el,
    text: norm(el.innerText || el.textContent),
    className: String(el.className || ''),
  }))
  .filter((item) => item.text === '专辑' || item.text === '音乐' || item.text.includes('专辑') || item.text.includes('音乐'));

let clicked = false;
if (shouldClick && desiredTab) {
  const target = tabNodes.find((item) => item.text === desiredTab) || tabNodes.find((item) => item.text.includes(desiredTab));
  if (target) {
    click(target.el);
    clicked = true;
  }
}

const headers = all('th')
  .filter(isVisible)
  .map((el) => norm(el.innerText || el.textContent))
  .filter(Boolean);

const rows = all('tbody tr, .ant-table-tbody tr')
  .filter(isVisible)
  .map((row) => {
    const cells = Array.from(row.querySelectorAll('td')).map((cell) => norm(cell.innerText || cell.textContent)).filter(Boolean);
    return {
      text: norm(row.innerText || row.textContent),
      cells,
      className: String(row.className || ''),
    };
  })
  .filter((row) => row.text && !row.text.includes('暂无数据'));

const tableTexts = all('.ant-table, .finder-table-wrap, .album-list-wrap, .music-list-wrap, table')
  .filter(isVisible)
  .map((el) => norm(el.innerText || el.textContent))
  .filter(Boolean)
  .slice(0, 8);

const activeTabs = tabNodes
  .filter((item) => /current|active|selected/i.test(item.className))
  .map((item) => item.text);

const bodyText = norm([
  document.body && (document.body.innerText || document.body.textContent || ''),
  ...all('wujie-app, .post-view, .router-view, .finder-table-wrap').map((el) => el.innerText || el.textContent || ''),
].join(' '));

return {
  clicked,
  desiredTab,
  activeTabs,
  tabs: tabNodes.map((item) => ({text: item.text, className: item.className})),
  headers,
  rows,
  rowCount: rows.length,
  tableTexts,
  empty: bodyText.includes('暂无数据'),
  bodyText: bodyText.slice(0, 2000),
  url: location.href,
};
"""


MUSIC_GLOBAL_STATE_SCRIPT = r"""
const maxDepth = 8;

function norm(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}

function isVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (!style || style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') {
    return false;
  }
  const rect = el.getBoundingClientRect();
  return !!(rect.width || rect.height || el.getClientRects().length);
}

function queryAllDeep(root, selector, depth, acc) {
  if (!root || depth > maxDepth || !root.querySelectorAll) return acc;
  for (const el of root.querySelectorAll(selector)) {
    acc.push(el);
  }
  for (const el of root.querySelectorAll('*')) {
    if (el.shadowRoot) {
      queryAllDeep(el.shadowRoot, selector, depth + 1, acc);
    }
  }
  return acc;
}

const candidates = queryAllDeep(document, '.weui-desktop-dialog__wrp, .weui-toptips, .common-toptip', 0, []);
const visibleMessages = candidates
  .filter(isVisible)
  .map((el) => norm(el.innerText || el.textContent))
  .filter(Boolean);
return {
  url: location.href,
  title: document.title || '',
  visibleMessages,
  bodyText: norm(document.body && (document.body.innerText || document.body.textContent) || '').slice(0, 1600),
};
"""


MUSIC_FORM_STATE_SCRIPT = r"""
function norm(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}
function isVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (!style || style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') return false;
  const rect = el.getBoundingClientRect();
  return !!(rect.width || rect.height || el.getClientRects().length);
}
function disabled(el) {
  if (!el) return true;
  const className = String(el.className || '');
  return !!el.disabled || el.getAttribute('disabled') !== null || el.getAttribute('aria-disabled') === 'true' || /disabled/i.test(className);
}
function scopeFor(label) {
  const labels = Array.from(document.querySelectorAll('.label-font, .normal-input-wrap, .weui-desktop-form__control-group, *'))
    .filter((el) => isVisible(el) && norm(el.innerText || el.textContent).includes(label));
  labels.sort((a, b) => norm(a.innerText || a.textContent).length - norm(b.innerText || b.textContent).length);
  const labelEl = labels[0];
  return labelEl ? (labelEl.closest('.normal-input-wrap, .weui-desktop-form__control-group') || labelEl.parentElement) : null;
}
function fieldValue(label) {
  const scope = scopeFor(label);
  if (!scope) return {found: false, value: ''};
  const field = scope.querySelector('input:not([type="file"]):not([type="hidden"]), textarea, [contenteditable="true"]');
  const dropdown = scope.querySelector('.weui-desktop-form__dropdowncascade__dt');
  let value = '';
  if (field) {
    value = field.value || field.innerText || field.textContent || '';
  } else if (dropdown) {
    value = dropdown.innerText || dropdown.textContent || '';
  }
  return {
    found: true,
    value: norm(value),
    text: norm(scope.innerText || scope.textContent).slice(0, 300),
  };
}
const button = Array.from(document.querySelectorAll('button'))
  .find((el) => isVisible(el) && norm(el.innerText || el.textContent) === '发表音乐');
const fields = {};
for (const label of ['歌曲名称', '歌曲版本', '歌词内容', '歌曲曲风', '语言', '演唱者', '词作者', '曲作者', '音乐制作人', '专辑名称', '专辑简介']) {
  fields[label] = fieldValue(label);
}
return {
  fields,
  publishButton: {
    exists: !!button,
    disabled: disabled(button),
    className: button ? String(button.className || '') : '',
  },
  bodyText: norm(document.body && (document.body.innerText || document.body.textContent) || '').slice(0, 1800),
};
"""


MUSIC_PROOF_UPLOAD_STATE_SCRIPT = r"""
function norm(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}
function isVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (!style || style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') return false;
  const rect = el.getBoundingClientRect();
  return !!(rect.width || rect.height || el.getClientRects().length);
}
const proofScopes = Array.from(document.querySelectorAll('.normal-input-wrap, .weui-desktop-form__control-group, .all-pic-wrap, .content'))
  .filter((el) => isVisible(el) && /证明文件|原创证明|\.zip|\.rar|删除|%/.test(norm(el.innerText || el.textContent)));
const text = norm(proofScopes.map((el) => el.innerText || el.textContent || '').join(' '));
const hasArchive = /\.zip|\.rar/i.test(text);
const hasProgress = /\d+(?:\.\d+)?%/.test(text);
const publishButton = Array.from(document.querySelectorAll('button'))
  .find((el) => isVisible(el) && norm(el.innerText || el.textContent) === '发表音乐');
const publishReady = !!publishButton
  && !publishButton.disabled
  && publishButton.getAttribute('disabled') === null
  && publishButton.getAttribute('aria-disabled') !== 'true'
  && !/disabled/i.test(String(publishButton.className || ''));
return {
  ok: !hasArchive || !hasProgress || publishReady,
  hasArchive,
  hasProgress,
  publishReady,
  text: text.slice(0, 800),
};
"""


SHOW_NEW_ALBUM_FIELDS_SCRIPT = r"""
const albumName = arguments[0] || '';
const albumIntro = arguments[1] || albumName;

function norm(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}
function isVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (!style || style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') return false;
  const rect = el.getBoundingClientRect();
  return !!(rect.width || rect.height || el.getClientRects().length);
}
function findRootVm() {
  const seen = new Set();
  function walk(root) {
    if (!root || seen.has(root)) return null;
    seen.add(root);
    const elements = root.querySelectorAll ? Array.from(root.querySelectorAll('*')) : [];
    for (const el of elements) {
      for (const key of Object.keys(el).filter((name) => name.startsWith('__vue'))) {
        const vm = el[key];
        if (vm && vm.postMusicStore && vm.$refs && vm.$refs.albumInfo) {
          return vm;
        }
      }
      if (el.shadowRoot) {
        const nested = walk(el.shadowRoot);
        if (nested) return nested;
      }
    }
    return null;
  }
  return walk(document);
}

const root = findRootVm();
const albumComponent = root && root.$refs && root.$refs.albumInfo;
const beforeText = albumComponent && albumComponent.$el ? norm(albumComponent.$el.innerText || albumComponent.$el.textContent) : '';
if (!albumComponent) {
  return {ok: false, reason: 'album-component-not-found', beforeText};
}

if (!beforeText.includes('专辑名称')) {
  if (typeof albumComponent.handleAlbumListEmpty === 'function') {
    try {
      albumComponent.handleAlbumListEmpty();
    } catch (error) {
      // Keep going; direct state update below is the fallback for newer builds.
    }
  }
  const store = albumComponent.postMusicStore || (root && root.postMusicStore);
  if (store) {
    store.shouldCreateNewAlbum = true;
    store.albumInfo = {
      albumName: '',
      coverUrl: '',
      introduction: '',
      issueTime: Math.floor(Date.now() / 1000),
    };
    if (root.$set) {
      root.$set(store, 'shouldCreateNewAlbum', true);
      root.$set(store, 'albumInfo', store.albumInfo);
    }
  }
  albumComponent.currentAlbumName = '新建专辑';
  albumComponent.currentSelectVal = '-1';
  albumComponent.showListBody = false;
  if (typeof albumComponent.$forceUpdate === 'function') albumComponent.$forceUpdate();
  if (root && typeof root.$forceUpdate === 'function') root.$forceUpdate();
}

return new Promise((resolve) => setTimeout(() => {
  const text = albumComponent.$el ? norm(albumComponent.$el.innerText || albumComponent.$el.textContent) : '';
  resolve({
    ok: text.includes('专辑名称'),
    beforeText,
    afterText: text.slice(0, 800),
    currentAlbumName: albumComponent.currentAlbumName,
    currentSelectVal: albumComponent.currentSelectVal,
  });
}, 500));
"""


CHECK_MUSIC_AGREEMENT_SCRIPT = r"""
function norm(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}
function isVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (!style || style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') return false;
  const rect = el.getBoundingClientRect();
  return !!(rect.width || rect.height || el.getClientRects().length);
}
const wrappers = Array.from(document.querySelectorAll('label, .ant-checkbox-wrapper, .original-proto-wrapper, div, span'))
  .filter((el) => isVisible(el) && norm(el.innerText || el.textContent).includes('我已阅读'));
for (const wrapper of wrappers) {
  const input = wrapper.querySelector('input[type="checkbox"]')
    || wrapper.closest('label, .ant-checkbox-wrapper, .original-proto-wrapper')?.querySelector('input[type="checkbox"]');
  if (input) {
    input.scrollIntoView({block: 'center'});
    if (!input.checked) {
      input.click();
      input.dispatchEvent(new Event('input', {bubbles: true}));
      input.dispatchEvent(new Event('change', {bubbles: true}));
    }
    return {ok: true, checked: input.checked, method: 'input'};
  }
  const label = wrapper.closest('label, .ant-checkbox-wrapper') || wrapper;
  label.scrollIntoView({block: 'center'});
  label.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, view: window}));
  if (typeof label.click === 'function') label.click();
  label.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, view: window}));
  label.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
  return {ok: true, checked: !!(label.querySelector('input[type="checkbox"]') || {}).checked, method: 'label'};
}
return {ok: false};
"""


SELECT_BY_LABEL_SCRIPT = r"""
const label = arguments[0] || '';
const optionText = arguments[1] || '';

function norm(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}
function isVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (!style || style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') return false;
  const rect = el.getBoundingClientRect();
  return !!(rect.width || rect.height || el.getClientRects().length);
}
function click(el) {
  el.scrollIntoView({block: 'center'});
  el.dispatchEvent(new MouseEvent('mouseover', {bubbles: true, cancelable: true, view: window}));
  el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, view: window}));
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, view: window}));
  el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
}

const genreLeafMap = {
  '流行': '城市流行',
  '国语流行': '城市流行',
  '中文流行': '城市流行',
  '华语流行': '城市流行',
  '英文流行': '欧美流行',
  '英语流行': '欧美流行',
  '日文流行': 'J-pop',
  '日语流行': 'J-pop',
  '日本流行': 'J-pop',
};
const languageMap = {
  '中文': '普通话',
  '汉语': '普通话',
  '国语': '普通话',
  '普通话': '普通话',
  '英文': '英语',
  '英语': '英语',
  '日文': '日语',
  '日语': '日语',
  '日本語': '日语',
};

function visibleText(el) {
  return norm(el.innerText || el.textContent);
}

function leafTarget(label, optionText) {
  if (label.includes('歌曲曲风')) return genreLeafMap[optionText] || optionText;
  if (label.includes('语言')) return languageMap[optionText] || optionText;
  return optionText;
}

function optionCandidates(scope, text) {
  const selector = '.weui-desktop-dropdown__list-ele, .weui-desktop-dropdown__list-ele__text, li, span, button, div';
  return Array.from(scope.querySelectorAll(selector))
    .filter((el) => visibleText(el) === text && (isVisible(el) || el.closest('.weui-desktop-dropdowncascade-menu__wrp')));
}

function clickOption(scope, text, preferLeaf) {
  const candidates = optionCandidates(scope, text);
  if (!candidates.length) return null;
  let match = null;
  if (preferLeaf) {
    match = candidates.find((el) => el.tagName === 'LI' && !String(el.className || '').includes('module-has-options'));
  }
  match = match
    || candidates.find((el) => el.tagName === 'LI')
    || candidates.find((el) => !String(el.className || '').includes('tooltip'))
    || candidates[0];
  click(match.closest('li, button') || match);
  return {
    text: visibleText(match),
    className: String(match.className || ''),
    tag: match.tagName,
  };
}

const labelCandidates = Array.from(document.querySelectorAll('.label-font, .weui-desktop-form__control-group, .normal-input-wrap, *'))
  .filter((el) => isVisible(el) && visibleText(el).includes(label))
  .map((el) => ({
    el,
    text: visibleText(el),
    className: String(el.className || ''),
  }));
labelCandidates.sort((a, b) => {
  const aExact = a.text === label ? 0 : 1;
  const bExact = b.text === label ? 0 : 1;
  const aLabelClass = /label-font|control-group|normal-input-wrap/.test(a.className) ? 0 : 1;
  const bLabelClass = /label-font|control-group|normal-input-wrap/.test(b.className) ? 0 : 1;
  return aExact - bExact || aLabelClass - bLabelClass || a.text.length - b.text.length;
});
const labelEl = (labelCandidates[0] || {}).el;
if (!labelEl) return {ok: false, reason: 'label-not-found'};
const scope = labelEl.closest('.normal-input-wrap, .weui-desktop-form__control-group, .form-item, .cell-center, .weui-desktop-form__input-area') || labelEl.parentElement || labelEl;
const currentValue = norm((scope.querySelector('input:not([type="hidden"]):not([type="file"])') || {}).value || '');
const dropdownValue = norm((scope.querySelector('.weui-desktop-form__dropdowncascade__dt') || {}).innerText || '');
const targetText = leafTarget(label, optionText);
if (currentValue === targetText || dropdownValue === targetText || dropdownValue.includes(targetText)) {
  return {ok: true, selected: targetText, alreadySelected: true};
}

const clickable = scope.querySelector('.weui-desktop-form__dropdowncascade__dt')
  || scope.querySelector('input[placeholder*="请选择"]')
  || Array.from(scope.querySelectorAll('button, input, .weui-desktop-form__dropdown, .weui-desktop-dropdown, .display, .display-text, .arrow-icon, .content, div, span'))
    .find((el) => isVisible(el) && el !== labelEl)
  || scope;
click(clickable);

if (label.includes('歌曲曲风') && targetText !== optionText) {
  const parent = clickOption(scope, optionText, false);
  const leaf = clickOption(scope, targetText, true);
  const updated = norm((scope.querySelector('.weui-desktop-form__dropdowncascade__dt') || {}).innerText || '');
  if (leaf && updated.includes(targetText)) {
    return {ok: true, selected: updated, parent, leaf};
  }
  return {ok: false, reason: 'genre-leaf-not-selected', parent, leaf, wanted: targetText, updated, scopeText: visibleText(scope).slice(0, 500)};
}

const scoped = clickOption(scope, targetText, true);
if (scoped) {
  const updatedInput = norm((scope.querySelector('input:not([type="hidden"]):not([type="file"])') || {}).value || '');
  const updatedDropdown = norm((scope.querySelector('.weui-desktop-form__dropdowncascade__dt') || {}).innerText || '');
  const updated = updatedInput || updatedDropdown || visibleText(scope);
  if (updated.includes(targetText) || scoped.text === targetText) {
    return {ok: true, selected: updated, option: scoped};
  }
}

const globalOptions = Array.from(document.querySelectorAll('li, span, div, button'))
  .filter((el) => isVisible(el) && visibleText(el) === targetText);
const option = globalOptions.find((el) => el.tagName === 'LI') || globalOptions[0];
if (!option) return {ok: false, reason: 'option-not-found', wanted: targetText, scopeText: visibleText(scope).slice(0, 500)};
click(option.closest('li, button') || option);
return {ok: true, selected: visibleText(option), option: {tag: option.tagName, className: String(option.className || '')}};
"""


def _candidate_music_urls():
    env_urls = os.environ.get("SHIPINHAO_MUSIC_CREATE_URLS") or os.environ.get("SHIPINHAO_MUSIC_CREATE_URL")
    if env_urls:
        for url in env_urls.split(","):
            url = url.strip()
            if url:
                yield url
    defaults = [
        "https://channels.weixin.qq.com/platform/post/createMusic",
        "https://channels.weixin.qq.com/micro/content/post/createMusic",
        "https://channels.weixin.qq.com/platform/music/create",
        "https://channels.weixin.qq.com/platform/post/music",
        "https://channels.weixin.qq.com/platform/audio/create",
        "https://channels.weixin.qq.com/platform/audio",
        "https://channels.weixin.qq.com/platform/music",
        "https://channels.weixin.qq.com/platform/post/create?type=music",
    ]
    for url in defaults:
        yield url


def _metadata_text(metadata, *keys, default=""):
    for key in keys:
        value = metadata.get(key)
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            value = "\n".join(str(item) for item in value if item)
        text = str(value).strip()
        if text:
            return remove_non_bmp(text)
    return default


def _normalize_language(value):
    text = str(value or "").strip()
    mapping = {
        "zh": "普通话",
        "zh-cn": "普通话",
        "zh-hans": "普通话",
        "zh-hant": "普通话",
        "cn": "普通话",
        "chinese": "普通话",
        "中文": "普通话",
        "普通话": "普通话",
        "en": "英语",
        "english": "英语",
        "英文": "英语",
        "英语": "英语",
        "ja": "日语",
        "jp": "日语",
        "japanese": "日语",
        "日文": "日语",
        "日语": "日语",
        "日本語": "日语",
        "mul": "普通话",
        "mixed": "普通话",
        "多语言": "普通话",
        "混合": "普通话",
    }
    return mapping.get(text.lower(), text or "普通话")


def _music_page_state(driver):
    state = _execute_in_content_frame(driver, MUSIC_PAGE_STATE_SCRIPT)
    return state if isinstance(state, dict) else {}


def _wait_for_music_page_ready(driver, duration=45):
    last_state = None
    deadline = time.time() + duration
    while time.time() < deadline:
        last_state = _music_page_state(driver)
        if last_state.get("unavailable"):
            raise RuntimeError("Shipinhao music upload is unavailable for this account or route.")
        if last_state.get("ready") or last_state.get("hasEntry"):
            print(f"Shipinhao music page ready: {last_state}")
            return last_state
        time.sleep(1)
    raise TimeoutException(f"Timed out waiting for Shipinhao music form. Last state: {last_state}")


def _enter_music_form(driver, duration=20):
    """Open the actual music upload form from the music-management page."""
    deadline = time.time() + duration
    last_state = None
    clicked_entry = False
    while time.time() < deadline:
        last_state = _music_page_state(driver)
        if last_state.get("unavailable"):
            raise RuntimeError("Shipinhao music upload is unavailable for this account or route.")
        if last_state.get("ready"):
            print(f"Shipinhao music upload form ready: {last_state}")
            return last_state
        if last_state.get("hasEntry") and not clicked_entry:
            print("Opening Shipinhao music upload form from music management page...")
            _click_music_text(driver, ["发表音乐", "上传一首歌曲", "添加音乐"], exact=False, duration=12)
            clicked_entry = True
            time.sleep(4)
            continue
        time.sleep(1)
    raise TimeoutException(f"Timed out entering Shipinhao music upload form. Last state: {last_state}")


def _find_music_page(driver):
    last_error = None
    try:
        driver.set_page_load_timeout(int(os.environ.get("SHIPINHAO_MUSIC_PAGE_LOAD_TIMEOUT", "20")))
    except Exception:
        pass
    for url in _candidate_music_urls():
        try:
            print(f"Trying Shipinhao music URL: {url}")
            try:
                driver.get(url)
            except TimeoutException as exc:
                last_error = exc
                print(f"Shipinhao music URL load timed out, stopping page load: {url}: {exc}")
                try:
                    driver.execute_script("window.stop();")
                except Exception:
                    pass
            dismiss_alert(driver)
            time.sleep(3)
            state = _wait_for_music_page_ready(driver, duration=12)
            if state.get("hasEntry") and not state.get("hasAudioInput"):
                state = _enter_music_form(driver, duration=20)
            return url, state
        except Exception as exc:
            last_error = exc
            print(f"Music URL candidate did not expose form: {url}: {exc}")
    save_debug_snapshot(driver, "music_route_not_found")
    raise RuntimeError(f"Could not find a usable Shipinhao music publish route: {last_error}")


def _set_music_field(driver, labels, hints, value, required=False, duration=20):
    value = remove_non_bmp(value or "")
    if not value:
        if required:
            raise ValueError(f"Missing value for music field {labels}")
        return None

    def _set(current_driver):
        result = _execute_in_content_frame(current_driver, SET_FIELD_BY_HINT_SCRIPT, labels, hints, value)
        if isinstance(result, dict) and result.get("ok"):
            return result
        return False

    try:
        result = WebDriverWait(driver, duration).until(_set)
        print(f"Shipinhao music field set: {labels} -> {result}")
        return result
    except Exception:
        if required:
            raise
        print(f"Optional Shipinhao music field not found: labels={labels} hints={hints}")
        return None


def _click_music_text(driver, texts, exact=False, duration=10):
    return WebDriverWait(driver, duration).until(
        lambda current_driver: _execute_in_content_frame(current_driver, CLICK_TEXT_SCRIPT, texts, exact)
    )


def _select_music_option(driver, label, option, duration=8, required=False):
    if not option:
        return None
    try:
        def _select(current_driver):
            result = _execute_in_content_frame(current_driver, SELECT_BY_LABEL_SCRIPT, label, option)
            if isinstance(result, dict) and result.get("ok"):
                return result
            return False

        result = WebDriverWait(driver, duration).until(_select)
        print(f"Shipinhao music option selected: {label}={option} -> {result}")
        return result
    except Exception as exc:
        if required:
            raise
        print(f"Optional Shipinhao music option not selected ({label}={option}): {exc}")
        return None


def _shipinhao_music_genre(value):
    raw = str(value or "").strip()
    if not raw:
        return "流行"
    normalized = raw.lower().replace("-", " ").replace("_", " ")
    aliases = {
        "bedroom pop": "流行",
        "indie pop": "流行",
        "pop": "流行",
        "lofi": "流行",
        "lo fi": "流行",
        "lofi pop": "流行",
        "lo fi pop": "流行",
        "children": "儿童",
        "children's": "儿童",
        "kids": "儿童",
        "folk": "民谣",
        "rock": "摇滚",
        "electronic": "电子",
        "jazz": "爵士",
        "classical": "古典",
    }
    return aliases.get(normalized, raw)


def _check_music_agreement(driver, duration=8):
    deadline = time.time() + duration
    last_state = None
    while time.time() < deadline:
        state = _execute_in_content_frame(driver, CHECK_MUSIC_AGREEMENT_SCRIPT)
        if isinstance(state, dict):
            last_state = state
            if state.get("ok") and state.get("checked"):
                print(f"Shipinhao music agreement checked: {state}")
                return state
        time.sleep(1)
    print(f"Optional Shipinhao music agreement checkbox not set: {last_state}")
    return last_state


def _wait_for_button_ready(driver, text="完成", duration=60):
    deadline = time.time() + duration
    last_state = None
    while time.time() < deadline:
        state = _execute_in_content_frame(driver, BUTTON_STATE_SCRIPT, text)
        if isinstance(state, dict):
            last_state = state
            if state.get("exists") and not state.get("disabled"):
                return state
        time.sleep(1)
    raise TimeoutException(f"Timed out waiting for Shipinhao music button {text!r}. Last state: {last_state}")


def _click_button_if_ready(driver, text="完成", duration=8):
    try:
        state = _wait_for_button_ready(driver, text=text, duration=duration)
    except TimeoutException:
        return False
    print(f"Shipinhao music optional button ready: {state}")
    click_content_frame_css(driver, "button", duration=10, text=text, exact=True)
    return True


def _music_global_state(driver):
    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    try:
        state = driver.execute_script(MUSIC_GLOBAL_STATE_SCRIPT)
        return state if isinstance(state, dict) else {}
    except Exception:
        return {}


def _music_form_state(driver):
    try:
        state = _execute_in_content_frame(driver, MUSIC_FORM_STATE_SCRIPT)
        return state if isinstance(state, dict) else {}
    except Exception:
        return {}


def _wait_for_music_proof_upload(driver, duration=45):
    deadline = time.time() + duration
    last_state = None
    while time.time() < deadline:
        state = _execute_in_content_frame(driver, MUSIC_PROOF_UPLOAD_STATE_SCRIPT)
        if isinstance(state, dict):
            last_state = state
            if state.get("ok"):
                print(f"Shipinhao music proof upload ready: {state}")
                return state
        time.sleep(1)
    raise TimeoutException(f"Timed out waiting for Shipinhao music proof upload. Last state: {last_state}")


def _ensure_new_album_fields(driver, album_name, album_intro, duration=8):
    """Switch the album area from existing-album selector to new-album fields.

    Shipinhao changed the form after the account has at least one album: the
    album section initially shows only "选择专辑". The desktop page still supports
    new album creation from this song form, but the visible control is a Vue
    component rather than a plain input. Use the component state only to reveal
    the standard inputs; the actual values are still filled through normal DOM
    input events below.
    """
    deadline = time.time() + duration
    last_state = None
    while time.time() < deadline:
        state = _execute_in_content_frame(driver, SHOW_NEW_ALBUM_FIELDS_SCRIPT, album_name, album_intro)
        if isinstance(state, dict):
            last_state = state
            if state.get("ok"):
                print(f"Shipinhao music new-album fields ready: {json.dumps(state, ensure_ascii=False)}")
                return state
        time.sleep(0.5)
    print(f"Shipinhao music new-album fields were not revealed: {last_state}")
    return last_state


def _raise_on_visible_music_error(driver):
    state = _music_global_state(driver)
    messages = [str(message) for message in state.get("visibleMessages") or [] if message]
    if messages:
        print(f"Shipinhao music visible messages: {json.dumps(messages, ensure_ascii=False)}")
    error_markers = [
        "表单信息不完整",
        "暂时无法使用该功能",
        "无法使用该功能",
        "不满足",
        "未满足",
        "上传失败",
        "发表失败",
        "发布失败",
        "错误",
    ]
    for message in messages:
        if any(marker in message for marker in error_markers):
            raise RuntimeError(f"Shipinhao music submit failed: {message}")
    return state


def read_shipinhao_music_management(driver, tabs=("专辑", "音乐"), settle_seconds=2):
    """Return visible Shipinhao music-management state for album and song tabs.

    Shipinhao currently exposes album (专辑) as a management tab and as required
    fields inside the music publish form. There is no verified album-only
    creation route, so this reader is intentionally non-destructive.
    """
    try:
        driver.set_page_load_timeout(int(os.environ.get("SHIPINHAO_MUSIC_PAGE_LOAD_TIMEOUT", "20")))
    except Exception:
        pass
    try:
        driver.get(SHIPINHAO_MUSIC_MANAGEMENT_URL)
    except TimeoutException:
        try:
            driver.execute_script("window.stop();")
        except Exception:
            pass
    dismiss_alert(driver)
    time.sleep(max(1, settle_seconds))

    snapshots = {}
    for tab in tabs:
        state = _execute_in_content_frame(driver, MUSIC_MANAGEMENT_STATE_SCRIPT, tab, True)
        time.sleep(max(1, settle_seconds))
        state = _execute_in_content_frame(driver, MUSIC_MANAGEMENT_STATE_SCRIPT, tab, False)
        snapshots[tab] = state if isinstance(state, dict) else {"error": "state-unavailable", "raw": state}
    return {
        "management_url": SHIPINHAO_MUSIC_MANAGEMENT_URL,
        "captured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tabs": snapshots,
    }


def save_shipinhao_music_management_snapshot(driver, label="music_management"):
    snapshot = read_shipinhao_music_management(driver)
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    safe_label = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)[:80]
    path = os.path.join(logs_dir, f"shipinhao-{safe_label}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, ensure_ascii=False, indent=2)
    print(f"Saved Shipinhao music management snapshot to {path}")
    return snapshot


class ShiPinHaoMusicPublisher:
    def __init__(self, driver, audio_path, cover_path, metadata, test=False):
        self.driver = driver
        self.audio_path = audio_path
        self.cover_path = cover_path
        self.metadata = metadata or {}
        self.test = test
        self.retry_count = 0

        shi_pin_hao_login = ShiPinHaoLogin(driver)
        shi_pin_hao_login.check_and_act()

    def _upload_audio(self):
        if not self.audio_path or not os.path.exists(self.audio_path):
            raise FileNotFoundError(f"Shipinhao music file missing: {self.audio_path}")
        find_any_in_content_frame(
            self.driver,
            SHIPINHAO_MUSIC_UPLOAD_INPUT_SELECTORS,
            duration=30,
            visible=False,
        )
        send_file_to_content_frame(
            self.driver,
            SHIPINHAO_MUSIC_UPLOAD_INPUT_SELECTORS,
            self.audio_path,
            duration=30,
        )
        print(f"Shipinhao music audio selected: {self.audio_path}")

    def _upload_images(self):
        image_paths = []
        for path in self.metadata.get("background_image_paths") or []:
            if path and os.path.exists(path):
                image_paths.append(path)
        filenames = self.metadata.get("background_image_filenames") or []
        package_root = os.path.dirname(self.audio_path)
        for name in filenames:
            path = os.path.join(package_root, name)
            if os.path.exists(path):
                image_paths.append(path)
        if self.cover_path and os.path.exists(self.cover_path):
            image_paths.insert(0, self.cover_path)

        unique_paths = []
        for path in image_paths:
            if path not in unique_paths:
                unique_paths.append(path)
        if not unique_paths:
            print("No Shipinhao music background image provided.")
            return

        try:
            send_file_to_content_frame(
                self.driver,
                SHIPINHAO_MUSIC_IMAGE_INPUT_SELECTORS,
                unique_paths[0],
                duration=20,
            )
            print(f"Shipinhao music background image selected: {unique_paths[0]}")
        except Exception as exc:
            print(f"Optional Shipinhao music background upload failed: {exc}")

    def _upload_original_proof(self):
        package_root = os.path.dirname(self.audio_path)
        proof_candidates = []
        proof_filename = _metadata_text(
            self.metadata,
            "original_proof_filename",
            "proof_zip_filename",
            default="",
        )
        if proof_filename:
            proof_candidates.append(proof_filename)
        for filename in self.metadata.get("proof_filenames") or []:
            if str(filename).lower().endswith((".zip", ".rar")):
                proof_candidates.append(filename)

        proof_path = None
        for candidate in proof_candidates:
            candidate_path = candidate if os.path.isabs(str(candidate)) else os.path.join(package_root, str(candidate))
            if os.path.exists(candidate_path):
                proof_path = candidate_path
                break
        if not proof_path:
            print("No Shipinhao music original-proof archive provided.")
            return False

        try:
            find_any_in_content_frame(
                self.driver,
                SHIPINHAO_MUSIC_PROOF_INPUT_SELECTORS,
                duration=5,
                visible=False,
            )
            send_file_to_content_frame(
                self.driver,
                SHIPINHAO_MUSIC_PROOF_INPUT_SELECTORS,
                proof_path,
                duration=10,
            )
            print(f"Shipinhao music original proof selected: {proof_path}")
            return True
        except Exception as exc:
            print(f"Optional Shipinhao music original proof upload skipped: {exc}")
            return False

    def _fill_music_fields(self):
        metadata = self.metadata
        title = _metadata_text(metadata, "song_title", "music_title", "title", default=os.path.splitext(os.path.basename(self.audio_path))[0])
        lyrics = _metadata_text(metadata, "lyrics", "song_lyrics", "lyric_text", default="")
        story = _metadata_text(
            metadata,
            "music_story",
            "story",
            "middle_description",
            "brief_description",
            default="",
        )
        author = _metadata_text(metadata, "author", "artist", "composer", default="Musia 慕莎")
        singer = _metadata_text(metadata, "singer", "vocalist", "performer", "artist", "author", default=author)
        lyricist = _metadata_text(metadata, "lyricist", "lyrics_author", "author", "artist", default=author)
        composer = _metadata_text(metadata, "composer", "music_author", "author", "artist", default=author)
        producer = _metadata_text(metadata, "producer", "music_producer", "author", "artist", default=author)
        band = _metadata_text(metadata, "band", "group", default="")
        genre = _metadata_text(metadata, "genre", "style", default="")
        language = _normalize_language(_metadata_text(metadata, "language", "song_language", default="中文"))
        published_elsewhere = bool(
            metadata.get("published_elsewhere")
            or metadata.get("source_url")
            or metadata.get("canonical_url")
            or metadata.get("website_url")
        )
        album_name = _metadata_text(metadata, "album_name", "album", "song_title", "music_title", "title", default=title)
        album_intro = _metadata_text(
            metadata,
            "album_intro",
            "album_description",
            "brief_description",
            "music_story",
            "story",
            "middle_description",
            "long_description",
            default=story or title,
        )

        _set_music_field(
            self.driver,
            ["歌曲名称", "音乐名称", "歌名"],
            ["歌曲名称", "音乐名称", "歌名", "song", "title"],
            title,
            required=True,
            duration=30,
        )
        _select_music_option(self.driver, "歌曲版本", "完整版", duration=8, required=True)

        try:
            _click_music_text(self.driver, ["歌词内容", "添加歌词", "填写歌词"], exact=False, duration=5)
            time.sleep(1)
        except Exception:
            pass
        _set_music_field(
            self.driver,
            ["歌词内容", "歌词"],
            ["歌词", "歌词内容", "请输入歌词", "lyrics"],
            lyrics,
            required=bool(lyrics),
            duration=20,
        )
        try:
            _click_music_text(self.driver, ["确定", "保存"], exact=True, duration=4)
        except Exception:
            pass

        _set_music_field(
            self.driver,
            ["作者信息", "作者", "音乐人"],
            ["作者", "音乐人", "artist", "author"],
            author,
            required=False,
            duration=10,
        )
        _set_music_field(
            self.driver,
            ["音乐人说", "歌曲简介", "歌曲故事"],
            ["音乐人说", "歌曲简介", "歌曲故事", "story", "description"],
            story[:300],
            required=False,
            duration=10,
        )

        _select_music_option(self.driver, "歌曲曲风", _shipinhao_music_genre(genre), duration=8, required=True)
        _select_music_option(self.driver, "语言", language, duration=8)
        _set_music_field(
            self.driver,
            ["演唱者"],
            ["演唱者", "歌手", "singer", "performer"],
            singer,
            required=False,
            duration=10,
        )
        _set_music_field(
            self.driver,
            ["词作者"],
            ["词作者", "作词", "lyricist"],
            lyricist,
            required=False,
            duration=10,
        )
        _set_music_field(
            self.driver,
            ["曲作者"],
            ["曲作者", "作曲", "composer"],
            composer,
            required=False,
            duration=10,
        )
        _set_music_field(
            self.driver,
            ["音乐制作人"],
            ["音乐制作人", "制作人", "producer"],
            producer,
            required=False,
            duration=10,
        )
        if band:
            _set_music_field(
                self.driver,
                ["乐队"],
                ["乐队", "band"],
                band,
                required=False,
                duration=8,
            )
        _select_music_option(self.driver, "是否已在其他平台发表", "是" if published_elsewhere else "否", duration=8)

        if bool(metadata.get("declare_original", False)):
            try:
                _click_music_text(self.driver, ["声明原创"], exact=False, duration=5)
                time.sleep(1)
            except Exception as exc:
                print(f"Optional music original declaration click failed: {exc}")

        _check_music_agreement(self.driver, duration=8)

        _ensure_new_album_fields(self.driver, album_name, album_intro[:1000], duration=8)
        _set_music_field(
            self.driver,
            ["专辑名称"],
            ["专辑名称", "请填写专辑名称"],
            album_name,
            required=True,
            duration=15,
        )
        _set_music_field(
            self.driver,
            ["专辑简介"],
            ["专辑简介", "填写专辑简介"],
            album_intro[:1000],
            required=True,
            duration=15,
        )

    def publish(self):
        if self.retry_count >= 3:
            raise RuntimeError("Maximum retry attempts reached. Shipinhao music process failed.")

        try:
            driver = self.driver
            print("Starting the music publishing process on ShiPinHao...")
            bring_to_front(SHIPINHAO_MUSIC_WINDOW_PATTERNS)
            close_extra_tabs(driver)
            _find_music_page(driver)
            dismiss_alert(driver)
            dismiss_overlays(driver)

            self._upload_audio()
            time.sleep(8)
            self._fill_music_fields()
            self._upload_images()
            time.sleep(3)
            if _click_button_if_ready(driver, text="确认", duration=8):
                time.sleep(3)
            if self._upload_original_proof():
                _wait_for_music_proof_upload(driver, duration=45)

            if self.test:
                user_input = input("Do you want to publish this music now? Type 'yes' to confirm: ").strip().lower()
            else:
                user_input = "yes"

            if user_input == "yes":
                form_state = _music_form_state(driver)
                if form_state:
                    print(f"Shipinhao music form state before submit: {json.dumps(form_state, ensure_ascii=False)}")
                state = _wait_for_button_ready(driver, text="发表音乐", duration=90)
                print(f"Shipinhao music publish button ready: {state}")
                click_content_frame_css(driver, "button", duration=20, text="发表音乐", exact=True)
                time.sleep(3)
                _raise_on_visible_music_error(driver)
                time.sleep(7)
                print("Shipinhao music submitted.")
                try:
                    management = save_shipinhao_music_management_snapshot(driver, "music_after_submit")
                    summary = {
                        name: {
                            "rowCount": (state or {}).get("rowCount"),
                            "activeTabs": (state or {}).get("activeTabs"),
                            "empty": (state or {}).get("empty"),
                        }
                        for name, state in (management.get("tabs") or {}).items()
                    }
                    print(f"Shipinhao music management summary after submit: {json.dumps(summary, ensure_ascii=False)}")
                except Exception as exc:
                    print(f"Optional Shipinhao music management verification failed: {exc}")
            else:
                print("Shipinhao music publishing cancelled by user.")

            self.retry_count = 0
            return True
        except Exception as exc:
            print(f"Shipinhao music publish error: {exc}")
            traceback.print_exc()
            save_debug_snapshot(self.driver, f"music_publish_attempt_{self.retry_count + 1}")
            self.retry_count += 1
            if self.retry_count >= 3:
                raise RuntimeError("Maximum retry attempts reached. Shipinhao music process failed.") from exc
            print(f"Retrying Shipinhao music publish... Attempt {self.retry_count}")
            return self.publish()
