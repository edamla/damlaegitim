(function() {
  var STORAGE_KEY = 'damlaokul:kbs-wizard';
  var TOTAL_STEPS = 4;
  var STEP_LABELS = ['Branş', 'Sınıf', 'İletişim', 'Gönder'];

  var config = { submitUrl: '', recaptchaSiteKey: '', okullarUrl: '' };
  var recaptchaWidgetId = null;
  var recaptchaRetryCount = 0;
  var adresIlIlce = { iller: [] };
  var okullarData = null;
  var okullarFetchPromise = null;
  var citySelectInitialized = false;

  var state = {
    step: 1,
    branches: [],
    grades: [],
    contact: {},
    version: 1
  };

  function loadConfig() {
    var el = document.getElementById('kbs-wizard-config');
    if (!el) return;
    try {
      var parsed = JSON.parse(el.textContent);
      config.submitUrl = parsed.submitUrl || '';
      config.recaptchaSiteKey = parsed.recaptchaSiteKey || '';
      config.okullarUrl = parsed.okullarUrl || '';
    } catch (e) { /* ignore */ }
  }

  function loadState() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      var saved = JSON.parse(raw);
      if (saved.version !== 1) return;
      Object.assign(state, saved);
      if (!Array.isArray(state.branches)) state.branches = [];
      if (!Array.isArray(state.grades)) state.grades = [];
      if (!state.contact) state.contact = {};
      if (state.step < 1 || state.step > TOTAL_STEPS) state.step = 1;
    } catch (e) { /* ignore */ }
  }

  function saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function uuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

  function escapeHtml(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function updateProgressChrome(n) {
    var label = STEP_LABELS[n - 1] || '';
    document.querySelectorAll('.kbs-wizard .ogretmen-wizard__step-dot').forEach(function(d) {
      var i = parseInt(d.dataset.progress, 10);
      d.classList.toggle('is-active', i === n);
      d.classList.toggle('is-done', i < n);
    });
    var progressEl = document.getElementById('kbs-progress');
    if (progressEl) {
      progressEl.setAttribute('aria-valuemax', String(TOTAL_STEPS));
      progressEl.setAttribute('aria-valuenow', String(n));
      progressEl.setAttribute('aria-valuetext', 'Adım ' + n + ' / ' + TOTAL_STEPS + ': ' + label);
    }
    var progressLabel = document.getElementById('kbs-progress-label');
    if (progressLabel) {
      progressLabel.textContent = 'Adım ' + n + ' / ' + TOTAL_STEPS + ' · ' + label;
    }
  }

  function showStep(n, opts) {
    opts = opts || {};
    n = Math.max(1, Math.min(TOTAL_STEPS, parseInt(n, 10) || 1));
    state.step = n;
    saveState();
    document.querySelectorAll('.kbs-wizard .ogretmen-wizard__panel').forEach(function(p) {
      p.classList.toggle('is-active', parseInt(p.dataset.step, 10) === n);
    });
    updateProgressChrome(n);
    document.getElementById('kbs-btn-prev').disabled = n <= 1;
    document.getElementById('kbs-btn-next').textContent = n >= TOTAL_STEPS ? 'Gönder' : 'İleri';
    if (n === 3) initCityDistrictSelects();
    if (n === 4) {
      renderSummary();
      scheduleRecaptchaRender();
    }
    if (opts.scroll !== false) {
      var wizardEl = document.getElementById('kbs-wizard');
      if (wizardEl) wizardEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function syncMultiSelectFromState(gridId, selectedValues) {
    var grid = document.getElementById(gridId);
    if (!grid) return;
    grid.querySelectorAll('[data-value]').forEach(function(btn) {
      var val = btn.dataset.value;
      btn.classList.toggle('is-selected', selectedValues.indexOf(val) >= 0);
    });
  }

  function toggleMultiValue(arr, value) {
    var idx = arr.indexOf(value);
    if (idx >= 0) arr.splice(idx, 1);
    else arr.push(value);
  }

  function findIl(kodOrName) {
    if (!kodOrName || !adresIlIlce.iller.length) return null;
    var key = String(kodOrName);
    for (var i = 0; i < adresIlIlce.iller.length; i++) {
      var il = adresIlIlce.iller[i];
      if (String(il.kod) === key || il.ad === key) return il;
    }
    return null;
  }

  function findIlce(il, kodOrName) {
    if (!il || !kodOrName) return null;
    var key = String(kodOrName);
    for (var j = 0; j < il.ilceler.length; j++) {
      var ilce = il.ilceler[j];
      if (String(ilce.kod) === key || ilce.ad === key) return ilce;
    }
    return null;
  }

  function selectedOptionMeta(selectEl) {
    if (!selectEl || selectEl.selectedIndex < 0) return { kod: '', ad: '' };
    var opt = selectEl.options[selectEl.selectedIndex];
    return {
      kod: (opt && opt.value) || '',
      ad: (opt && (opt.dataset.ad || opt.textContent)) || ''
    };
  }

  function loadOkullarData() {
    if (okullarData) return Promise.resolve(okullarData);
    if (okullarFetchPromise) return okullarFetchPromise;
    if (!config.okullarUrl) {
      okullarData = { iller: {} };
      return Promise.resolve(okullarData);
    }
    okullarFetchPromise = fetch(config.okullarUrl)
      .then(function(res) {
        if (!res.ok) throw new Error('okullar.json yüklenemedi');
        return res.json();
      })
      .then(function(data) {
        okullarData = data || {};
        return okullarData;
      })
      .catch(function(err) {
        console.log('Okul listesi yüklenemedi:', err);
        okullarData = { iller: {} };
        return okullarData;
      });
    return okullarFetchPromise;
  }

  function populateSchoolList(ilKod, ilceKod, selectedSchool) {
    var schoolInput = document.getElementById('kbs-school');
    var datalist = document.getElementById('kbs-school-list');
    var hint = document.getElementById('kbs-school-hint');
    if (!schoolInput || !datalist) return;

    datalist.innerHTML = '';
    if (!ilKod || !ilceKod) {
      schoolInput.placeholder = 'Önce il ve ilçe seçin';
      if (hint) hint.textContent = 'İl ve ilçe seçildiğinde MEB kurum listesi yüklenir. Listede yoksa okul adını elle yazabilirsiniz.';
      return;
    }

    schoolInput.placeholder = 'Okul arayın veya yazın…';
    if (hint) hint.textContent = 'Kurum listesi yükleniyor…';

    loadOkullarData().then(function(data) {
      datalist.innerHTML = '';
      var ilNode = data.iller && data.iller[String(ilKod)];
      var ilceNode = ilNode && ilNode.ilceler && ilNode.ilceler[String(ilceKod)];
      var kurumlar = (ilceNode && ilceNode.kurumlar) || [];
      kurumlar.slice().sort(function(a, b) {
        return (a.ad || '').localeCompare(b.ad || '', 'tr');
      }).forEach(function(kurum) {
        if (!kurum.ad) return;
        var opt = document.createElement('option');
        opt.value = kurum.ad;
        datalist.appendChild(opt);
      });
      if (hint) {
        if (kurumlar.length) {
          hint.textContent = kurumlar.length + ' kurum listelendi. Listede yoksa okul adını elle yazabilirsiniz.';
        } else {
          hint.textContent = 'Bu ilçe için kayıtlı kurum bulunamadı; okul adını elle yazın.';
        }
      }
      if (selectedSchool) schoolInput.value = selectedSchool;
    });
  }

  function populateDistrictSelect(ilKod, selectedIlce) {
    var districtSel = document.getElementById('kbs-district');
    if (!districtSel) return;
    districtSel.innerHTML = '';
    var il = findIl(ilKod);
    if (!ilKod || !il) {
      districtSel.disabled = true;
      var emptyOpt = document.createElement('option');
      emptyOpt.value = '';
      emptyOpt.textContent = 'Önce il seçin';
      districtSel.appendChild(emptyOpt);
      populateSchoolList('', '', '');
      return;
    }
    districtSel.disabled = false;
    var placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'İlçe seçin';
    districtSel.appendChild(placeholder);
    il.ilceler.slice().sort(function(a, b) {
      return a.ad.localeCompare(b.ad, 'tr');
    }).forEach(function(ilce) {
      var opt = document.createElement('option');
      opt.value = String(ilce.kod);
      opt.dataset.ad = ilce.ad;
      opt.textContent = ilce.ad;
      districtSel.appendChild(opt);
    });
    var ilce = findIlce(il, selectedIlce);
    if (ilce) {
      districtSel.value = String(ilce.kod);
      populateSchoolList(String(il.kod), String(ilce.kod), state.contact && state.contact.school);
    } else {
      populateSchoolList(String(il.kod), '', '');
    }
  }

  function ensureCityOption(citySel, kodOrName) {
    if (!kodOrName || !citySel) return;
    var il = findIl(kodOrName);
    if (il) {
      for (var i = 0; i < citySel.options.length; i++) {
        if (citySel.options[i].value === String(il.kod)) return;
      }
      var opt = document.createElement('option');
      opt.value = String(il.kod);
      opt.dataset.ad = il.ad;
      opt.textContent = il.ad;
      citySel.appendChild(opt);
      return;
    }
    for (var j = 0; j < citySel.options.length; j++) {
      if (citySel.options[j].value === kodOrName) return;
    }
    var legacy = document.createElement('option');
    legacy.value = kodOrName;
    legacy.dataset.ad = kodOrName;
    legacy.textContent = kodOrName;
    citySel.appendChild(legacy);
  }

  function readContactForm() {
    var citySel = document.getElementById('kbs-city');
    var districtSel = document.getElementById('kbs-district');
    var cityMeta = selectedOptionMeta(citySel);
    var districtMeta = selectedOptionMeta(districtSel);
    return {
      firstName: document.getElementById('kbs-first-name').value.trim(),
      lastName: document.getElementById('kbs-last-name').value.trim(),
      city: cityMeta.ad.trim(),
      cityKod: cityMeta.kod.trim(),
      district: districtMeta.ad.trim(),
      districtKod: districtMeta.kod.trim(),
      phone: document.getElementById('kbs-phone').value.trim(),
      email: document.getElementById('kbs-email').value.trim(),
      school: document.getElementById('kbs-school').value.trim(),
      whatsapp: document.getElementById('kbs-whatsapp').value.trim(),
      instagram: document.getElementById('kbs-instagram').value.trim(),
      x: document.getElementById('kbs-x').value.trim()
    };
  }

  function fillContactForm() {
    var c = state.contact || {};
    if (c.firstName) document.getElementById('kbs-first-name').value = c.firstName;
    if (c.lastName) document.getElementById('kbs-last-name').value = c.lastName;
    if (c.phone) document.getElementById('kbs-phone').value = c.phone;
    if (c.email) document.getElementById('kbs-email').value = c.email;
    if (c.whatsapp) document.getElementById('kbs-whatsapp').value = c.whatsapp;
    if (c.instagram) document.getElementById('kbs-instagram').value = c.instagram;
    if (c.x) document.getElementById('kbs-x').value = c.x;
    initCityDistrictSelects();
  }

  function initCityDistrictSelects() {
    var citySel = document.getElementById('kbs-city');
    var districtSel = document.getElementById('kbs-district');
    if (!citySel || !districtSel) return;

    if (!citySelectInitialized) {
      adresIlIlce.iller.slice().sort(function(a, b) {
        return a.ad.localeCompare(b.ad, 'tr');
      }).forEach(function(il) {
        var opt = document.createElement('option');
        opt.value = String(il.kod);
        opt.dataset.ad = il.ad;
        opt.textContent = il.ad;
        citySel.appendChild(opt);
      });
      citySel.addEventListener('change', function() {
        populateDistrictSelect(citySel.value, '');
        var schoolInput = document.getElementById('kbs-school');
        if (schoolInput) schoolInput.value = '';
        state.contact = readContactForm();
        state.contact.district = '';
        state.contact.districtKod = '';
        state.contact.school = '';
        saveState();
      });
      districtSel.addEventListener('change', function() {
        var ilKod = citySel.value;
        var ilceKod = districtSel.value;
        var schoolInput = document.getElementById('kbs-school');
        if (schoolInput) schoolInput.value = '';
        populateSchoolList(ilKod, ilceKod, '');
        state.contact = readContactForm();
        state.contact.school = '';
        saveState();
      });
      var schoolInput = document.getElementById('kbs-school');
      if (schoolInput) {
        schoolInput.addEventListener('change', function() {
          state.contact = readContactForm();
          saveState();
        });
        schoolInput.addEventListener('input', function() {
          state.contact = readContactForm();
          saveState();
        });
      }
      citySelectInitialized = true;
    }

    var saved = state.contact || {};
    var savedCity = saved.cityKod || saved.city || citySel.value;
    if (savedCity) {
      ensureCityOption(citySel, savedCity);
      var il = findIl(savedCity);
      citySel.value = il ? String(il.kod) : savedCity;
      populateDistrictSelect(citySel.value, saved.districtKod || saved.district);
      if (saved.school) {
        populateSchoolList(citySel.value, districtSel.value, saved.school);
      }
    } else {
      populateDistrictSelect('', '');
      populateSchoolList('', '', '');
    }
  }

  function renderSummary() {
    var greetingEl = document.getElementById('kbs-summary-greeting');
    var metaEl = document.getElementById('kbs-summary-meta');
    if (!metaEl) return;
    var c = readContactForm();
    if (greetingEl) {
      greetingEl.innerHTML =
        '<p class="ogretmen-wizard__summary-greeting">Değerli öğretmenimiz ' +
        '<strong>' + escapeHtml(c.firstName + ' ' + c.lastName) + '</strong>, ' +
        'aşağıda özetlenen bilgilerle «Kitapla Büyüyen Sınıflar» başvurunuz gönderilecektir.</p>';
    }
    var social = [];
    if (c.whatsapp) social.push('WhatsApp: ' + c.whatsapp);
    if (c.instagram) social.push('Instagram: ' + c.instagram);
    if (c.x) social.push('X: ' + c.x);
    metaEl.innerHTML =
      '<div class="ogretmen-wizard__summary-meta-row"><span>Branş</span><strong>' + escapeHtml(state.branches.join(', ')) + '</strong></div>' +
      '<div class="ogretmen-wizard__summary-meta-row"><span>Sınıf</span><strong>' + escapeHtml(state.grades.join(', ')) + '</strong></div>' +
      '<div class="ogretmen-wizard__summary-meta-row"><span>Okul</span><strong>' + escapeHtml(c.school) + '</strong></div>' +
      '<div class="ogretmen-wizard__summary-meta-row"><span>Konum</span><strong>' + escapeHtml(c.city + ' / ' + c.district) + '</strong></div>' +
      '<div class="ogretmen-wizard__summary-meta-row"><span>Telefon</span><strong>' + escapeHtml(c.phone) + '</strong></div>' +
      '<div class="ogretmen-wizard__summary-meta-row"><span>E-posta</span><strong>' + escapeHtml(c.email) + '</strong></div>' +
      (social.length ? '<div class="ogretmen-wizard__summary-meta-row"><span>Sosyal</span><strong>' + escapeHtml(social.join(' · ')) + '</strong></div>' : '');
  }

  function setStatus(msg, type) {
    var el = document.getElementById('kbs-status');
    if (!el) return;
    el.textContent = msg;
    el.className = 'ogretmen-wizard__status is-' + type;
  }

  function setRecaptchaHint(msg, visible) {
    var hint = document.getElementById('kbs-recaptcha-hint');
    if (!hint) return;
    hint.hidden = !visible;
    if (visible && msg) hint.textContent = msg;
  }

  function scheduleRecaptchaRender() {
    setRecaptchaHint('Yükleniyor…', true);
    window.setTimeout(ensureRecaptcha, 50);
  }

  function ensureRecaptcha() {
    if (!config.recaptchaSiteKey) return;
    var el = document.getElementById('kbs-recaptcha');
    if (!el) return;
    var panel = document.getElementById('kbs-step-4');
    if (panel && !panel.classList.contains('is-active')) return;
    if (typeof grecaptcha === 'undefined' || typeof grecaptcha.render !== 'function') {
      if (recaptchaRetryCount < 40) {
        recaptchaRetryCount++;
        setTimeout(ensureRecaptcha, 300);
      } else {
        setRecaptchaHint('Doğrulama yüklenemedi. Sayfayı yenileyip tekrar deneyin.', true);
      }
      return;
    }
    recaptchaRetryCount = 0;
    if (recaptchaWidgetId === null) {
      try {
        recaptchaWidgetId = grecaptcha.render(el, { sitekey: config.recaptchaSiteKey });
        setRecaptchaHint('', false);
      } catch (err) {
        recaptchaWidgetId = null;
        setRecaptchaHint('Doğrulama başlatılamadı. Sayfayı yenileyin.', true);
        console.log('reCAPTCHA render:', err);
      }
      return;
    }
    grecaptcha.reset(recaptchaWidgetId);
    setRecaptchaHint('', false);
  }

  function getRecaptchaToken() {
    if (!config.recaptchaSiteKey) return '';
    if (typeof grecaptcha === 'undefined' || recaptchaWidgetId === null) return '';
    return grecaptcha.getResponse(recaptchaWidgetId);
  }

  function resetRecaptcha() {
    if (typeof grecaptcha === 'undefined' || recaptchaWidgetId === null) return;
    grecaptcha.reset(recaptchaWidgetId);
  }

  function setSubmitting(active) {
    var loading = document.getElementById('kbs-loading');
    var nextBtn = document.getElementById('kbs-btn-next');
    var prevBtn = document.getElementById('kbs-btn-prev');
    var wizardEl = document.getElementById('kbs-wizard');
    if (loading) loading.hidden = !active;
    if (wizardEl) wizardEl.classList.toggle('is-submitting', active);
    if (nextBtn) {
      nextBtn.disabled = active;
      nextBtn.textContent = active ? 'Gönderiliyor…' : (state.step >= TOTAL_STEPS ? 'Gönder' : 'İleri');
    }
    if (prevBtn) prevBtn.disabled = active || state.step <= 1;
  }

  function collectBrowserMeta() {
    var nav = navigator;
    var parts = [];
    if (nav.userAgent) parts.push('UA: ' + nav.userAgent);
    if (nav.platform) parts.push('Platform: ' + nav.platform);
    if (nav.language) parts.push('Language: ' + nav.language);
    if (nav.languages && nav.languages.length) {
      parts.push('Languages: ' + Array.prototype.slice.call(nav.languages).join(','));
    }
    if (typeof screen !== 'undefined' && screen.width && screen.height) {
      parts.push('Screen: ' + screen.width + 'x' + screen.height);
    }
    if (window.devicePixelRatio) parts.push('DPR: ' + window.devicePixelRatio);
    try {
      var tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if (tz) parts.push('Timezone: ' + tz);
    } catch (tzErr) { /* ignore */ }
    if (nav.hardwareConcurrency) parts.push('CPU cores: ' + nav.hardwareConcurrency);
    if (typeof nav.maxTouchPoints === 'number') parts.push('Touch points: ' + nav.maxTouchPoints);
    if (nav.vendor) parts.push('Vendor: ' + nav.vendor);
    parts.push('Cookies: ' + (nav.cookieEnabled ? 'yes' : 'no'));
    return parts.join(' | ');
  }

  function buildUserAgentField(publicIp) {
    var meta = collectBrowserMeta();
    if (!meta) meta = 'UA: (tarayici bilgisi alinamadi)';
    var parts = [];
    if (publicIp) parts.push('IP: ' + publicIp);
    parts.push(meta);
    return parts.join(' | ');
  }

  function fetchPublicIp(timeoutMs) {
    return new Promise(function(resolve) {
      var settled = false;
      function finish(ip) {
        if (settled) return;
        settled = true;
        resolve(ip || '');
      }
      var timer = setTimeout(function() { finish(''); }, timeoutMs || 2500);
      var urls = [
        'https://api.ipify.org?format=json',
        'https://api64.ipify.org?format=json'
      ];
      function tryUrl(idx) {
        if (idx >= urls.length) {
          clearTimeout(timer);
          finish('');
          return;
        }
        fetch(urls[idx], { method: 'GET', cache: 'no-store' })
          .then(function(res) {
            if (!res.ok) throw new Error('ip');
            return res.json();
          })
          .then(function(data) {
            clearTimeout(timer);
            finish(data && data.ip ? String(data.ip) : '');
          })
          .catch(function() {
            tryUrl(idx + 1);
          });
      }
      tryUrl(0);
    });
  }

  function buildPayload(userAgentStr) {
    var c = readContactForm();
    return {
      basvuru_id: uuid(),
      ad: c.firstName,
      soyad: c.lastName,
      okul_adi: c.school,
      il: c.city,
      ilce: c.district,
      branslar: state.branches.join(' | '),
      siniflar: state.grades.join(' | '),
      telefon: c.phone,
      eposta: c.email,
      whatsapp: c.whatsapp,
      instagram: c.instagram,
      x_hesabi: c.x,
      kvkk_onay: true,
      kaynak_url: window.location.href,
      user_agent: userAgentStr || buildUserAgentField('')
    };
  }

  function showSuccessView() {
    var summaryView = document.getElementById('kbs-summary-view');
    var successView = document.getElementById('kbs-success-view');
    var prevBtn = document.getElementById('kbs-btn-prev');
    var nextBtn = document.getElementById('kbs-btn-next');
    var actions = document.querySelector('.kbs-wizard .ogretmen-wizard__actions');
    if (summaryView) summaryView.hidden = true;
    if (successView) successView.hidden = false;
    if (prevBtn) prevBtn.hidden = true;
    if (nextBtn) nextBtn.hidden = true;
    if (actions) actions.hidden = true;
    var statusEl = document.getElementById('kbs-status');
    if (statusEl) {
      statusEl.textContent = '';
      statusEl.className = 'ogretmen-wizard__status';
    }
    var wizardEl = document.getElementById('kbs-wizard');
    if (wizardEl) wizardEl.classList.add('is-submitted');
  }

  function submitToSheets() {
    if (!config.submitUrl) {
      setStatus('Gönderim henüz yapılandırılmadı. Yöneticiniz Apps Script URL\'sini eklediğinde tekrar deneyin.', 'error');
      return;
    }
    var kvkk = document.getElementById('kbs-kvkk');
    if (kvkk && !kvkk.checked) {
      setStatus('Lütfen aydınlatma metni onay kutusunu işaretleyin.', 'error');
      return;
    }
    if (config.recaptchaSiteKey && !getRecaptchaToken()) {
      setStatus('Lütfen «Ben robot değilim» doğrulamasını tamamlayın.', 'error');
      return;
    }
    setSubmitting(true);
    var browserMeta = collectBrowserMeta() || 'UA: (tarayici bilgisi alinamadi)';
    fetchPublicIp(2500).then(function(publicIp) {
      var ua = buildUserAgentField(publicIp);
      if (!ua || ua.indexOf('UA:') < 0) {
        ua = (publicIp ? 'IP: ' + publicIp + ' | ' : '') + browserMeta;
      }
      var payload = buildPayload(ua);
      if (config.recaptchaSiteKey) payload.recaptcha_token = getRecaptchaToken();
      if (!payload.user_agent) payload.user_agent = ua;
      return fetch(config.submitUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify(payload)
      });
    }).then(function(res) {
      if (!res) return { ok: false };
      return res.text().then(function(text) {
        try {
          return JSON.parse(text);
        } catch (parseErr) {
          console.log('Apps Script yanıtı JSON değil:', text.slice(0, 500));
          return { ok: false, error: 'invalid_response' };
        }
      });
    }).then(function(data) {
      if (!data || data.ok !== true) {
        console.log('Gönderim hatası:', data);
        resetRecaptcha();
        setStatus('Gönderim sırasında bir hata oluştu. Lütfen tekrar deneyin.', 'error');
        return;
      }
      showSuccessView();
      localStorage.removeItem(STORAGE_KEY);
    }).catch(function(err) {
      console.log('Gönderim hatası:', err);
      resetRecaptcha();
      setStatus('Gönderim sırasında bir hata oluştu. Lütfen tekrar deneyin.', 'error');
    }).finally(function() {
      setSubmitting(false);
    });
  }

  function validateStep(n) {
    if (n === 1 && state.branches.length === 0) {
      alert('Lütfen en az bir branş seçin.');
      return false;
    }
    if (n === 2 && state.grades.length === 0) {
      alert('Lütfen en az bir sınıf seviyesi seçin.');
      return false;
    }
    if (n === 3) {
      var form = document.getElementById('kbs-contact-form');
      if (!form || !form.reportValidity()) return false;
      state.contact = readContactForm();
      saveState();
    }
    return true;
  }

  function bindMultiSelectGrid(gridId, stateKey) {
    var grid = document.getElementById(gridId);
    if (!grid) return;
    grid.addEventListener('click', function(e) {
      var btn = e.target.closest('[data-value]');
      if (!btn) return;
      toggleMultiValue(state[stateKey], btn.dataset.value);
      btn.classList.toggle('is-selected', state[stateKey].indexOf(btn.dataset.value) >= 0);
      saveState();
    });
  }

  function init() {
    var wizardRoot = document.getElementById('kbs-wizard');
    if (!wizardRoot) return;

    loadConfig();
    var adresEl = document.getElementById('kbs-adres-il-ilce');
    if (adresEl) {
      try { adresIlIlce = JSON.parse(adresEl.textContent); } catch (e) { adresIlIlce = { iller: [] }; }
    }
    loadState();

    var contactForm = document.getElementById('kbs-contact-form');
    if (contactForm) {
      contactForm.addEventListener('submit', function(e) { e.preventDefault(); });
    }

    document.addEventListener('kbs-recaptcha-ready', function() {
      if (state.step === 4) scheduleRecaptchaRender();
    });
    if (window.kbsRecaptchaApiReady && state.step === 4) {
      scheduleRecaptchaRender();
    }

    syncMultiSelectFromState('kbs-branch-grid', state.branches);
    syncMultiSelectFromState('kbs-grade-grid', state.grades);
    bindMultiSelectGrid('kbs-branch-grid', 'branches');
    bindMultiSelectGrid('kbs-grade-grid', 'grades');
    fillContactForm();

    document.getElementById('kbs-btn-prev').addEventListener('click', function() {
      if (state.step > 1) showStep(state.step - 1);
    });

    document.getElementById('kbs-btn-next').addEventListener('click', function() {
      if (state.step < TOTAL_STEPS) {
        if (!validateStep(state.step)) return;
        showStep(state.step + 1);
      } else {
        if (!validateStep(3)) {
          showStep(3);
          return;
        }
        state.contact = readContactForm();
        saveState();
        renderSummary();
        submitToSheets();
      }
    });

    showStep(state.step, { scroll: false });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
