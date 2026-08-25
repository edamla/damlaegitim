(function() {
  'use strict';

  var root = document.querySelector('.curriculum-browse');
  if (!root) return;

  var FIELD = root.dataset.curriculumField;
  var CHIP_CLASS = root.dataset.chipClass || FIELD;
  var EMPTY_HINT = root.dataset.emptyHint || 'Bir seçim yapın';
  var siteBase = root.dataset.baseurl || '';

  function readJson(id, fallback) {
    var el = document.getElementById(id);
    if (!el) return fallback;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return fallback;
    }
  }

  var catalog = readJson('curriculum-catalog', []);
  var labelOrder = readJson('curriculum-label-order', []);
  var degerOrder = readJson('curriculum-deger-order', []);

  var gradeGrid = document.getElementById('curriculum-grade-grid');
  var chipsEl = document.getElementById('curriculum-chips');
  var resultsEl = document.getElementById('curriculum-results');
  var statusEl = document.getElementById('curriculum-status');
  var searchEl = document.getElementById('curriculum-chip-search');

  var state = {
    grade: null,
    selection: null,
    chipSearch: ''
  };

  var GRADE_STORAGE_KEY = 'curriculum-browse-grade';

  function persistGrade() {
    if (state.grade === null || state.grade === undefined) return;
    try {
      sessionStorage.setItem(GRADE_STORAGE_KEY, String(state.grade));
    } catch (e) {
      /* ignore */
    }
  }

  function readStoredGrade() {
    try {
      var stored = sessionStorage.getItem(GRADE_STORAGE_KEY);
      if (stored && /^[1-8]$/.test(stored)) return stored;
    } catch (e) {
      /* ignore */
    }
    return '3';
  }

  function slugify(label) {
    if (!window.BookFilter) return String(label || '').toLowerCase();
    return BookFilter.normLabel(label).replace(/\s+/g, '-');
  }

  function labelFromSlug(slug) {
    if (!slug) return null;
    for (var i = 0; i < labelOrder.length; i++) {
      if (slugify(labelOrder[i]) === slug) return labelOrder[i];
    }
    return null;
  }

  function booksForGrade(grade) {
    if (!window.BookFilter || grade === null || grade === undefined) return [];
    return BookFilter.filterCatalog(catalog, { genre: 'story', grade: String(grade) });
  }

  function bookMatchesLabel(book, label) {
    if (!label || !window.BookFilter) return true;
    var criteria = { genre: 'story' };
    criteria[FIELD] = [label];
    return BookFilter.filterCatalog([book], criteria).length > 0;
  }

  function collectFieldValues(books) {
    var values = {};
    books.forEach(function(book) {
      var list = book[FIELD];
      if (!Array.isArray(list)) return;
      list.forEach(function(v) {
        if (v) values[v] = true;
      });
    });
    return Object.keys(values);
  }

  function sortLabels(labels) {
    var orderMap = {};
    labelOrder.forEach(function(label, idx) {
      orderMap[BookFilter.normLabel(label)] = idx;
    });
    return labels.slice().sort(function(a, b) {
      var ia = orderMap[BookFilter.normLabel(a)];
      var ib = orderMap[BookFilter.normLabel(b)];
      if (ia == null) ia = 9999;
      if (ib == null) ib = 9999;
      if (ia !== ib) return ia - ib;
      return a.localeCompare(b, 'tr');
    });
  }

  function countForLabel(books, label) {
    var count = 0;
    books.forEach(function(book) {
      if (bookMatchesLabel(book, label)) count++;
    });
    return count;
  }

  function escapeHtml(text) {
    return String(text || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function anatemaSummary(book) {
    if (!book.anatema || !book.anatema.length) return '';
    return book.anatema.slice(0, 3).join(', ');
  }

  function renderBookCard(book) {
    var coverUrl = book.cover ? (siteBase + '/' + book.cover) : '';
    var anatema = anatemaSummary(book);
    var bookUrl = book.url ? (siteBase + book.url) : '#';
    return '<div class="col-12 col-sm-6 col-lg-3 listbooks-home-item">' +
      '<article class="book-card">' +
      '<a class="book-card__link baslik-link" href="' + escapeHtml(bookUrl) + '">' +
      '<div class="book-card__media">' +
      (coverUrl
        ? '<img class="book-card__cover cover-images" src="' + escapeHtml(coverUrl) + '" alt="" loading="lazy" width="400" height="600" decoding="async">'
        : '') +
      '</div>' +
      '<div class="book-card__info">' +
      '<h3 class="book-card__title">' + escapeHtml(book.title) + '</h3>' +
      (book.authors ? '<p class="book-card__author">' + escapeHtml(book.authors) + '</p>' : '') +
      (anatema ? '<span class="book-card__theme">' + escapeHtml(anatema) + '</span>' : '') +
      '</div></a></article></div>';
  }

  function updateUrl() {
    var params = new URLSearchParams();
    if (state.grade !== null && state.grade !== undefined) {
      params.set('sinif', String(state.grade));
    }
    if (state.selection) {
      params.set('secim', slugify(state.selection));
    }
    var query = params.toString();
    var newUrl = window.location.pathname + (query ? ('?' + query) : '');
    window.history.replaceState(null, '', newUrl);
    persistGrade();
    syncTabLinks();
  }

  function syncTabLinks() {
    if (state.grade === null || state.grade === undefined) return;
    document.querySelectorAll('.curriculum-browse__tab').forEach(function(tab) {
      if (!tab.href) return;
      var url = new URL(tab.href, window.location.origin);
      url.searchParams.set('sinif', String(state.grade));
      url.searchParams.delete('secim');
      tab.href = url.pathname + '?' + url.searchParams.toString();
    });
  }

  function parseUrl() {
    var params = new URLSearchParams(window.location.search);
    var sinif = params.get('sinif');
    var secim = params.get('secim');
    if (sinif && /^[1-8]$/.test(sinif)) {
      state.grade = sinif;
    } else {
      state.grade = readStoredGrade();
    }
    state.selection = secim ? labelFromSlug(secim) : null;
    persistGrade();
  }

  function syncGradeButtons() {
    if (!gradeGrid) return;
    gradeGrid.querySelectorAll('.curriculum-browse__grade-btn').forEach(function(btn) {
      btn.classList.toggle('is-selected', String(btn.dataset.grade) === String(state.grade));
    });
  }

  function renderChips() {
    if (!chipsEl || !window.BookFilter) return;
    var books = booksForGrade(state.grade);
    var present = collectFieldValues(books);
    var presentSet = {};
    present.forEach(function(v) { presentSet[BookFilter.normLabel(v)] = v; });

    var labels = sortLabels(labelOrder.filter(function(label) {
      return presentSet[BookFilter.normLabel(label)] !== undefined;
    }));

    var search = (state.chipSearch || '').trim().toLowerCase();
    if (search) {
      labels = labels.filter(function(label) {
        return label.toLowerCase().indexOf(search) !== -1;
      });
    }

    var html = '<button type="button" class="curriculum-browse__chip book-curriculum__chip book-curriculum__chip--' + escapeHtml(CHIP_CLASS) +
      (state.selection === null ? ' is-active' : '') + '" data-label="" aria-pressed="' + (state.selection === null ? 'true' : 'false') + '">Tümü (' + books.length + ')</button>';

    labels.forEach(function(label) {
      var count = countForLabel(books, label);
      if (count === 0) return;
      var active = state.selection === label;
      html += '<button type="button" class="curriculum-browse__chip book-curriculum__chip book-curriculum__chip--' + escapeHtml(CHIP_CLASS) +
        (active ? ' is-active' : '') + '" data-label="' + escapeHtml(label) + '" data-slug="' + escapeHtml(slugify(label)) +
        '" aria-pressed="' + (active ? 'true' : 'false') + '">' +
        escapeHtml(label) + ' (' + count + ')</button>';
    });

    chipsEl.innerHTML = html || '<p class="text-muted small mb-0">Bu sınıfta eşleşen kayıt bulunamadı.</p>';
  }

  function renderResults() {
    if (!resultsEl || !statusEl || !window.BookFilter) return;

    if (state.grade === null || state.grade === undefined) {
      statusEl.textContent = 'Kitapları görmek için sınıf seçin.';
      resultsEl.innerHTML = '';
      return;
    }

    var books = booksForGrade(state.grade);
    var filtered = books;

    if (state.selection) {
      filtered = books.filter(function(book) {
        return bookMatchesLabel(book, state.selection);
      });
    }

    if (FIELD === 'degerler') {
      filtered = BookFilter.sortStoryCatalog(filtered, degerOrder);
    } else {
      filtered = filtered.slice().sort(function(a, b) {
        return (a.title || '').localeCompare(b.title || '', 'tr');
      });
    }

    if (state.selection) {
      statusEl.textContent = filtered.length + ' kitap listeleniyor.';
    } else if (filtered.length > 0) {
      statusEl.textContent = filtered.length + ' kitap listeleniyor (tümü).';
    } else {
      statusEl.textContent = 'Bu sınıf için kitap bulunamadı.';
    }

    resultsEl.innerHTML = filtered.length
      ? filtered.map(renderBookCard).join('')
      : '<div class="col-12"><p class="text-muted">Bu kriterlere uygun kitap bulunamadı.</p></div>';
  }

  function render() {
    syncGradeButtons();
    renderChips();
    renderResults();
    updateUrl();
  }

  function onGradeClick(grade) {
    state.grade = grade;
    state.selection = null;
    persistGrade();
    render();
  }

  function onChipClick(label) {
    state.selection = label || null;
    render();
  }

  function bindEvents() {
    if (gradeGrid) {
      gradeGrid.addEventListener('click', function(e) {
        var btn = e.target.closest('.curriculum-browse__grade-btn');
        if (!btn) return;
        onGradeClick(btn.dataset.grade);
      });
    }

    if (chipsEl) {
      chipsEl.addEventListener('click', function(e) {
        var chip = e.target.closest('.curriculum-browse__chip');
        if (!chip) return;
        var label = chip.dataset.label || '';
        onChipClick(label || null);
      });
    }

    if (searchEl) {
      searchEl.addEventListener('input', function() {
        state.chipSearch = searchEl.value;
        renderChips();
      });
    }
  }

  function init() {
    if (!window.BookFilter) {
      window.setTimeout(init, 50);
      return;
    }
    parseUrl();
    bindEvents();
    syncTabLinks();
    render();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
