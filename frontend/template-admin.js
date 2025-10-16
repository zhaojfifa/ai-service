(function () {
  const globalScope = typeof window !== 'undefined' ? window : globalThis;

  const ensureGlobalFileToDataUrl = () => {
    if (
      globalScope &&
      typeof globalScope.fileToDataUrl !== 'function'
    ) {
      globalScope.fileToDataUrl = (file) =>
        new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
            const value = typeof reader.result === 'string' ? reader.result : '';
            resolve(value);
          };
          reader.onerror = () => reject(reader.error || new Error('文件读取失败'));
          reader.readAsDataURL(file);
        });
    }
    return globalScope?.fileToDataUrl || null;
  };

  const readFileAsDataUrl = (file) =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const value = typeof reader.result === 'string' ? reader.result : '';
        resolve(value);
      };
      reader.onerror = () => reject(reader.error || new Error('文件读取失败'));
      reader.readAsDataURL(file);
    });

  const safeFileToDataUrl = (file) => {
    if (!file) return Promise.resolve('');

    const globalFn = ensureGlobalFileToDataUrl();

    if (typeof globalFn === 'function') {
      try {
        const result = globalFn(file);
        if (result && typeof result.then === 'function') {
          return result
            .then((value) => (typeof value === 'string' ? value : ''))
            .catch(() => readFileAsDataUrl(file));
        }
        if (typeof result === 'string') {
          return Promise.resolve(result);
        }
      } catch (error) {
        console.warn('[template-admin] global fileToDataUrl failed', error);
      }
    }

    return readFileAsDataUrl(file);
  };

  const extractBase64Payload = (dataUrl) => {
    if (typeof dataUrl !== 'string') return null;
    const trimmed = dataUrl.trim();
    const commaIndex = trimmed.indexOf(',');
    if (commaIndex === -1) return null;
    const payload = trimmed.slice(commaIndex + 1).replace(/\s+/g, '');
    return payload || null;
  };

  const grid = document.getElementById('template-poster-grid');
  if (!grid) return;

  const statusElement = document.getElementById('template-status');
  const refreshButton = document.getElementById('refresh-posters');
  const apiBaseInput = document.getElementById('api-base');
  const AppContext =
    (typeof window !== 'undefined' && window.App) || null;

  const slotLabels = {
    variant_a: '海报 A',
    variant_b: '海报 B',
  };

  const slotMap = new Map();
  grid.querySelectorAll('[data-slot]').forEach((element) => {
    const slot = element.dataset.slot;
    if (!slot) return;
    slotMap.set(slot, {
      slot,
      root: element,
      preview: element.querySelector('[data-role="preview"]'),
      placeholder: element.querySelector('[data-role="empty"]'),
      meta: element.querySelector('[data-role="meta"]'),
      selection: element.querySelector('[data-role="selection"]'),
      input: element.querySelector('input[type="file"]'),
      uploadButton: element.querySelector('[data-action="upload"]'),
      resetButton: element.querySelector('[data-action="reset"]'),
      status: element.querySelector('[data-role="slot-status"]'),
    });
  });

  if (!slotMap.size) return;

  const state = {
    base: null,
    loading: false,
  };

  const formatSize = (bytes) => {
    if (!bytes || Number.isNaN(bytes)) return '—';
    if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(1)} MB`;
    if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${bytes} B`;
  };

  const formatDimensions = (width, height) => {
    if (!width || !height) return '—';
    return `${width} × ${height}`;
  };

  const guessContentType = (file) => {
    if (!file) return null;
    if (file.type) return file.type;
    const name = file.name ? file.name.toLowerCase() : '';
    if (name.endsWith('.png')) return 'image/png';
    if (name.endsWith('.jpg') || name.endsWith('.jpeg')) return 'image/jpeg';
    if (name.endsWith('.webp')) return 'image/webp';
    return null;
  };

  const resetSlotStatusClass = (entry) => {
    if (!entry?.status) return;
    entry.status.className = 'slot-status';
  };

  const updateSlotStatus = (slot, message, level) => {
    const entry = slotMap.get(slot);
    if (!entry || !entry.status) return;
    entry.status.textContent = message || '';
    resetSlotStatusClass(entry);
    if (message && level) {
      entry.status.classList.add(`status-${level}`);
    }
  };

  const updateSelectionText = (slot, text) => {
    const entry = slotMap.get(slot);
    if (!entry || !entry.selection) return;
    entry.selection.textContent = text || '尚未选择文件';
  };

  const setSlotBusy = (slot, busy) => {
    const entry = slotMap.get(slot);
    if (!entry) return;
    if (busy) {
      entry.root.classList.add('busy');
    } else {
      entry.root.classList.remove('busy');
    }
    refreshSlotControls(slot);
  };

  const refreshSlotControls = (slot) => {
    const entry = slotMap.get(slot);
    if (!entry) return;
    const busy = entry.root.classList.contains('busy');
    const disabled = busy || state.loading;
    if (entry.input) {
      entry.input.disabled = busy || state.loading;
    }
    if (entry.uploadButton) {
      const hasFile = Boolean(entry.input?.files?.length);
      entry.uploadButton.disabled = disabled || !hasFile;
    }
    if (entry.resetButton) {
      entry.resetButton.disabled = busy || state.loading;
    }
  };

  const refreshAllControls = () => {
    slotMap.forEach((_, slot) => refreshSlotControls(slot));
    if (refreshButton) refreshButton.disabled = state.loading;
  };

  const setGlobalStatus = (message, level) => {
    if (!statusElement) return;
    if (typeof setStatus === 'function') {
      setStatus(statusElement, message, level || 'info');
    } else {
      statusElement.textContent = message || '';
    }
  };

  const updateSlotMeta = (slot, poster) => {
    const entry = slotMap.get(slot);
    if (!entry || !entry.meta) return;
    const meta = entry.meta;
    meta.innerHTML = '';
    const addItem = (label, value, options = {}) => {
      const dt = document.createElement('dt');
      dt.textContent = label;
      const dd = document.createElement('dd');
      if (options.isLink && value) {
        const link = document.createElement('a');
        link.href = value;
        link.textContent = value;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        dd.appendChild(link);
      } else {
        dd.textContent = value ?? '—';
      }
      meta.appendChild(dt);
      meta.appendChild(dd);
    };

    if (!poster) {
      addItem('当前状态', '尚未上传');
      return;
    }

    addItem('文件名', poster.filename || '—');
    addItem('格式', poster.media_type || '—');
    addItem('尺寸', formatDimensions(poster.width, poster.height));
    if (poster.url) {
      addItem('访问链接', poster.url, { isLink: true });
    }
  };

  const updateSlotPreview = (slot, poster) => {
    const entry = slotMap.get(slot);
    if (!entry) return;
    const preview = entry.preview;
    const placeholder = entry.placeholder;
    if (poster) {
      const source = poster.url || poster.data_url || '';
      if (preview) {
        if (source) {
          preview.src = source;
          preview.classList.remove('hidden');
        } else {
          preview.removeAttribute('src');
          preview.classList.add('hidden');
        }
      }
      if (placeholder) {
        placeholder.classList.toggle('hidden', Boolean(source));
      }
    } else {
      if (preview) {
        preview.removeAttribute('src');
        preview.classList.add('hidden');
      }
      if (placeholder) {
        placeholder.classList.remove('hidden');
        placeholder.textContent = '尚未上传海报';
      }
    }
  };

  const applyCollection = (collection) => {
    const posters = Array.isArray(collection?.posters) ? collection.posters : [];
    const seen = new Set();
    posters.forEach((entry) => {
      const slot = entry?.slot;
      if (!slotMap.has(slot)) return;
      seen.add(slot);
      updateSlotPreview(slot, entry.poster || null);
      updateSlotMeta(slot, entry.poster || null);
      updateSlotStatus(slot, '已加载当前模板。', 'success');
    });

    slotMap.forEach((_, slot) => {
      if (seen.has(slot)) return;
      updateSlotPreview(slot, null);
      updateSlotMeta(slot, null);
      updateSlotStatus(slot, '暂无已上传模板。', 'warning');
    });
  };

  const ensureBase = async ({ force = false, warmup = false } = {}) => {
    if (!force && state.base) return state.base;
    const candidates = AppContext?.utils?.getApiCandidates?.() || [];
    if (!candidates.length) {
      throw new Error('请先填写后端 API 地址。');
    }
    if (warmup && AppContext?.utils?.warmUp) {
      try {
        await AppContext.utils.warmUp(candidates, { force: true });
      } catch (error) {
        console.warn('[template-admin] warmUp failed', error);
      }
    }
    let base = null;
    if (AppContext?.utils?.pickHealthyBase) {
      base = await AppContext.utils.pickHealthyBase(candidates);
    }
    state.base = base || candidates[0] || null;
    if (!state.base) {
      throw new Error('未找到可用的后端 API 地址。');
    }
    return state.base;
  };

  const requestJson = async (method, path, payload) => {
    const base = await ensureBase({ warmup: method !== 'GET' });
    const url = joinBasePath ? joinBasePath(base, path) : null;
    if (!url) throw new Error('API 地址无效。');
    const body = payload ? JSON.stringify(payload) : undefined;
    const response = await fetch(url, {
      method,
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json; charset=UTF-8',
      },
      mode: 'cors',
      cache: 'no-store',
      credentials: 'omit',
      body,
    });
    const text = await response.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (error) {
        console.warn('[template-admin] response parse failed', error);
        throw new Error('服务器响应格式异常。');
      }
    }
    if (!response.ok) {
      const detail = data?.detail || data?.message || text || '请求失败';
      throw new Error(detail);
    }
    return data || {};
  };

  const fetchPosters = async ({ silent = false } = {}) => {
    state.loading = true;
    refreshAllControls();
    slotMap.forEach((_, slot) => updateSlotStatus(slot, '同步中…', 'info'));
    if (!silent) setGlobalStatus('正在读取后台模板…', 'info');
    try {
      const data = await requestJson('GET', '/api/template-posters');
      applyCollection(data);
      if (!silent) setGlobalStatus('已同步最新模板。', 'success');
    } catch (error) {
      console.error('[template-admin] fetch posters failed', error);
      const message = error?.message || '无法加载模板列表';
      setGlobalStatus(message, 'error');
      slotMap.forEach((_, slot) => updateSlotStatus(slot, '', null));
    } finally {
      state.loading = false;
      refreshAllControls();
    }
  };

  const clearSelection = (slot) => {
    const entry = slotMap.get(slot);
    if (!entry) return;
    if (entry.input) {
      entry.input.value = '';
    }
    updateSelectionText(slot, '尚未选择文件');
  };

  const uploadSlot = async (slot) => {
    const entry = slotMap.get(slot);
    if (!entry || !entry.input) return;
    const file = entry.input.files?.[0] || null;
    if (!file) {
      updateSlotStatus(slot, '请先选择图片文件。', 'warning');
      return;
    }

    const contentType = guessContentType(file);
    if (!contentType) {
      updateSlotStatus(slot, '无法识别文件格式，请上传 PNG/JPEG/WebP 图片。', 'error');
      return;
    }

    setSlotBusy(slot, true);
    updateSlotStatus(slot, '正在上传…', 'info');
    setGlobalStatus(`正在上传 ${slotLabels[slot] || slot}…`, 'info');

    try {
      const dataUrl = await safeFileToDataUrl(file);
      const base64 = extractBase64Payload(dataUrl);
      if (!base64) {
        throw new Error('图片编码失败，请重试。');
      }
      const payload = {
        slot,
        filename: file.name || `${slot}.png`,
        content_type: contentType,
        data: base64,
      };
      console.log(payload);
      await requestJson('POST', '/api/template-posters', payload);
      updateSlotStatus(slot, '上传完成。', 'success');
      clearSelection(slot);
      await fetchPosters({ silent: true });
      setGlobalStatus(`${slotLabels[slot] || slot} 上传完成。`, 'success');
    } catch (error) {
      console.error('[template-admin] upload failed', error);
      const message = error?.message || '上传失败';
      updateSlotStatus(slot, message, 'error');
      setGlobalStatus(message, 'error');
    } finally {
      setSlotBusy(slot, false);
      refreshSlotControls(slot);
    }
  };

  slotMap.forEach((entry, slot) => {
    if (entry.input) {
      entry.input.addEventListener('change', () => {
        const file = entry.input.files?.[0] || null;
        if (file) {
          updateSelectionText(slot, `${file.name} · ${formatSize(file.size)}`);
          updateSlotStatus(slot, '等待上传…', 'info');
        } else {
          updateSelectionText(slot, '尚未选择文件');
          updateSlotStatus(slot, '', null);
        }
        refreshSlotControls(slot);
      });
    }

    if (entry.uploadButton) {
      entry.uploadButton.addEventListener('click', () => uploadSlot(slot));
    }

    if (entry.resetButton) {
      entry.resetButton.addEventListener('click', () => {
        clearSelection(slot);
        updateSlotStatus(slot, '', null);
        refreshSlotControls(slot);
      });
    }

    refreshSlotControls(slot);
  });

  if (refreshButton) {
    refreshButton.addEventListener('click', () => {
      state.base = null;
      fetchPosters();
    });
  }

  if (apiBaseInput) {
    apiBaseInput.addEventListener('change', () => {
      state.base = null;
      fetchPosters({ silent: true });
    });
  }

  fetchPosters();
})();
