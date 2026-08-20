/* Paylaşılan katalog filtresi (DOM'suz çekirdek) */
var BookFilter = (function() {
  function norm(s) {
    return String(s || '').toLowerCase().trim();
  }

  function arr(v) {
    return Array.isArray(v) ? v : [];
  }

  function matchesGrade(book, grade) {
    if (grade === null || grade === undefined || grade === '') return true;
    var g = String(grade);
    return arr(book.grades).some(function(bg) { return String(bg) === g; });
  }

  function matchesGenre(book, genre) {
    if (!genre) return true;
    return book.genre === genre;
  }

  function matchesCategories(book, categories) {
    if (!categories || categories.length === 0) return true;
    var bookCats = arr(book.categories);
    return categories.some(function(c) { return bookCats.indexOf(c) !== -1; });
  }

  function matchesTags(book, tags) {
    if (!tags || tags.length === 0) return true;
    var bookTags = arr(book.tags);
    return tags.some(function(t) { return bookTags.indexOf(t) !== -1; });
  }

  function matchesFieldList(book, field, values) {
    if (!values || values.length === 0) return true;
    var bookValues = arr(book[field]);
    return values.some(function(v) { return bookValues.indexOf(v) !== -1; });
  }

  function matchesAnatema(book, anatema) {
    return matchesFieldList(book, 'anatema', anatema);
  }

  function matchesUnite(book, unite) {
    return matchesFieldList(book, 'unite', unite);
  }

  function matchesBeceriler(book, beceriler) {
    if (!beceriler || beceriler.length === 0) return true;
    var bookBec = arr(book.beceriler);
    return beceriler.some(function(b) {
      return bookBec.some(function(bb) { return norm(bb).indexOf(norm(b)) !== -1; });
    });
  }

  function matchesKazanim(book, kazanim) {
    return matchesFieldList(book, 'kazanim', kazanim);
  }

  function matchesSearch(book, q) {
    if (!q) return true;
    var query = norm(q);
    return norm(book.title).indexOf(query) !== -1;
  }

  function filterCatalog(books, criteria) {
    criteria = criteria || {};
    return (books || []).filter(function(book) {
      return matchesGrade(book, criteria.grade) &&
        matchesGenre(book, criteria.genre) &&
        matchesCategories(book, criteria.categories) &&
        matchesTags(book, criteria.tags) &&
        matchesAnatema(book, criteria.anatema) &&
        matchesUnite(book, criteria.unite) &&
        matchesBeceriler(book, criteria.beceriler) &&
        matchesKazanim(book, criteria.kazanim) &&
        matchesSearch(book, criteria.q);
    });
  }

  function normLabel(s) {
    return norm(String(s || '')
      .replace(/İ/g, 'i')
      .replace(/I/g, 'i')
      .replace(/ı/g, 'i')
      .replace(/ğ/g, 'g')
      .replace(/ü/g, 'u')
      .replace(/ş/g, 's')
      .replace(/ö/g, 'o')
      .replace(/ç/g, 'c')
      .replace(/\s+/g, ' '));
  }

  function labelsMatch(a, b) {
    var na = normLabel(a);
    var nb = normLabel(b);
    if (!na || !nb) return false;
    if (na === nb) return true;
    return na.indexOf(nb) !== -1 || nb.indexOf(na) !== -1;
  }

  function buildGradeTymmIndex(tymmData, grade) {
    var gradeKey = String(grade);
    var gradeData = tymmData && tymmData.grades && tymmData.grades[gradeKey];
    var uniteOrder = {};
    var uniteLabels = [];
    if (!gradeData || !gradeData.unites) {
      return { uniteOrder: uniteOrder, uniteLabels: uniteLabels, hasTymm: false };
    }
    gradeData.unites.forEach(function(u, idx) {
      var label = u.label || '';
      uniteLabels.push(label);
      uniteOrder[normLabel(label)] = {
        index: idx,
        label: label,
        anatema: arr(u.degerler).concat(arr(u.egilimler)),
        beceriler: arr(u.beceriler)
      };
    });
    return { uniteOrder: uniteOrder, uniteLabels: uniteLabels, hasTymm: true };
  }

  function findUniteIndex(uniteValue, tymmIndex) {
    if (!uniteValue) return 9999;
    var key = normLabel(uniteValue);
    if (tymmIndex.uniteOrder[key]) return tymmIndex.uniteOrder[key].index;
    var keys = Object.keys(tymmIndex.uniteOrder);
    for (var i = 0; i < keys.length; i++) {
      if (labelsMatch(uniteValue, tymmIndex.uniteOrder[keys[i]].label)) {
        return tymmIndex.uniteOrder[keys[i]].index;
      }
    }
    return 9999;
  }

  function collectStoryBooks(catalog, grade) {
    return filterCatalog(catalog, { grade: grade, genre: 'story' });
  }

  function collectStoryValues(catalog, grade) {
    var books = collectStoryBooks(catalog, grade);
    var unites = {};
    var anatema = {};
    var beceriler = {};
    books.forEach(function(book) {
      arr(book.unite).forEach(function(u) { if (u) unites[u] = true; });
      arr(book.anatema).forEach(function(a) { if (a) anatema[a] = true; });
      arr(book.beceriler).forEach(function(b) { if (b) beceriler[b] = true; });
    });
    return {
      unites: Object.keys(unites),
      anatema: Object.keys(anatema),
      beceriler: Object.keys(beceriler)
    };
  }

  function sortByOrderList(values, orderList) {
    var orderMap = {};
    orderList.forEach(function(v, idx) {
      orderMap[normLabel(v)] = idx;
    });
    return values.slice().sort(function(a, b) {
      var ia = orderMap[normLabel(a)];
      var ib = orderMap[normLabel(b)];
      if (ia == null) ia = 9999;
      if (ib == null) ib = 9999;
      if (ia !== ib) return ia - ib;
      return a.localeCompare(b, 'tr');
    });
  }

  function getTymmUniteEntry(selectedUnite, tymmIndex) {
    if (!selectedUnite) return null;
    var key = normLabel(selectedUnite);
    if (tymmIndex.uniteOrder[key]) return tymmIndex.uniteOrder[key];
    var keys = Object.keys(tymmIndex.uniteOrder);
    for (var i = 0; i < keys.length; i++) {
      if (labelsMatch(selectedUnite, tymmIndex.uniteOrder[keys[i]].label)) {
        return tymmIndex.uniteOrder[keys[i]];
      }
    }
    return null;
  }

  function storyFilterOptions(catalog, grade, tymmData, selectedUnite) {
    var values = collectStoryValues(catalog, grade);
    var tymmIndex = buildGradeTymmIndex(tymmData, grade);
    var unites = values.unites.slice().sort(function(a, b) {
      var diff = findUniteIndex(a, tymmIndex) - findUniteIndex(b, tymmIndex);
      return diff !== 0 ? diff : a.localeCompare(b, 'tr');
    });

    var baseBooks = collectStoryBooks(catalog, grade);
    if (selectedUnite) {
      baseBooks = baseBooks.filter(function(book) {
        return arr(book.unite).indexOf(selectedUnite) !== -1;
      });
    }

    var anatemaSet = {};
    var becerilerSet = {};
    baseBooks.forEach(function(book) {
      arr(book.anatema).forEach(function(a) { if (a) anatemaSet[a] = true; });
      arr(book.beceriler).forEach(function(b) { if (b) becerilerSet[b] = true; });
    });

    var anatemas = Object.keys(anatemaSet);
    var becerilers = Object.keys(becerilerSet);
    var uniteEntry = getTymmUniteEntry(selectedUnite, tymmIndex);

    if (uniteEntry && uniteEntry.anatema.length) {
      anatemas = sortByOrderList(anatemas, uniteEntry.anatema);
    } else if (tymmIndex.hasTymm) {
      var allAnatema = [];
      tymmIndex.uniteLabels.forEach(function(label) {
        var entry = getTymmUniteEntry(label, tymmIndex);
        if (entry) allAnatema = allAnatema.concat(entry.anatema);
      });
      anatemas = sortByOrderList(anatemas, allAnatema);
    } else {
      anatemas.sort(function(a, b) { return a.localeCompare(b, 'tr'); });
    }

    if (uniteEntry && uniteEntry.beceriler.length) {
      becerilers = sortByOrderList(becerilers, uniteEntry.beceriler);
    } else if (tymmIndex.hasTymm) {
      var allBeceriler = [];
      tymmIndex.uniteLabels.forEach(function(label) {
        var entry = getTymmUniteEntry(label, tymmIndex);
        if (entry) allBeceriler = allBeceriler.concat(entry.beceriler);
      });
      becerilers = sortByOrderList(becerilers, allBeceriler);
    } else {
      becerilers.sort(function(a, b) { return a.localeCompare(b, 'tr'); });
    }

    return { unites: unites, anatema: anatemas, beceriler: becerilers };
  }

  function getPrimaryUniteSortKey(book, tymmIndex) {
    var unites = arr(book.unite);
    if (unites.length === 0) return 9999;
    var minIdx = 9999;
    unites.forEach(function(u) {
      var idx = findUniteIndex(u, tymmIndex);
      if (idx < minIdx) minIdx = idx;
    });
    return minIdx;
  }

  function getPrimaryUniteLabel(book) {
    var unites = arr(book.unite);
    return unites.length ? unites[0] : '';
  }

  function getPrimaryAnatemaLabel(book) {
    var anatemas = arr(book.anatema).slice(0, 3);
    return anatemas.length ? anatemas.join(', ') : '';
  }

  function sortStoryCatalog(books, grade, tymmData) {
    var tymmIndex = buildGradeTymmIndex(tymmData, grade);
    return (books || []).slice().sort(function(a, b) {
      var ua = getPrimaryUniteSortKey(a, tymmIndex);
      var ub = getPrimaryUniteSortKey(b, tymmIndex);
      if (ua !== ub) return ua - ub;
      var la = getPrimaryUniteLabel(a);
      var lb = getPrimaryUniteLabel(b);
      if (la !== lb) return la.localeCompare(lb, 'tr');
      return (a.title || '').localeCompare(b.title || '', 'tr');
    });
  }

  return {
    matchesGrade: matchesGrade,
    matchesGenre: matchesGenre,
    matchesCategories: matchesCategories,
    matchesTags: matchesTags,
    matchesAnatema: matchesAnatema,
    matchesUnite: matchesUnite,
    matchesBeceriler: matchesBeceriler,
    matchesKazanim: matchesKazanim,
    matchesSearch: matchesSearch,
    filterCatalog: filterCatalog,
    normLabel: normLabel,
    buildGradeTymmIndex: buildGradeTymmIndex,
    collectStoryValues: collectStoryValues,
    storyFilterOptions: storyFilterOptions,
    sortStoryCatalog: sortStoryCatalog,
    getPrimaryUniteLabel: getPrimaryUniteLabel,
    getPrimaryAnatemaLabel: getPrimaryAnatemaLabel
  };
})();

function getSelectedGrades(checkboxSelector) {
    var selected = [];
    document.querySelectorAll(checkboxSelector).forEach(function(checkbox) {
        if (checkbox.checked) {
            selected.push(checkbox.value);
        }
    });
    return selected;
}

function bookMatchesGrades(bookElement, selectedGrades) {
    if (selectedGrades.length === 0) {
        return false;
    }
    var bookGrades = (bookElement.dataset.grades || '').split(',').filter(Boolean);
    return selectedGrades.some(function(grade) {
        return bookGrades.indexOf(grade) !== -1;
    });
}

function getSelectedClassPrefixes(checkboxSelector, prefix) {
    var selected = [];
    document.querySelectorAll(checkboxSelector).forEach(function(checkbox) {
        if (checkbox.checked) {
            selected.push(prefix + checkbox.value);
        }
    });
    return selected;
}

function bookMatchesClassPrefixes(bookElement, classPrefixes) {
    if (classPrefixes.length === 0) {
        return false;
    }
    return classPrefixes.some(function(className) {
        return bookElement.classList.contains(className);
    });
}

function filterBooksByGradesAndGenres(bookSelector, gradeCheckboxSelector, genreCheckboxSelector) {
    var selectedGrades = getSelectedGrades(gradeCheckboxSelector);
    var genres = getSelectedClassPrefixes(genreCheckboxSelector, 'genre-');

    document.querySelectorAll(bookSelector).forEach(function(book) {
        var gradeFound = bookMatchesGrades(book, selectedGrades);
        var genreFound = bookMatchesClassPrefixes(book, genres);
        book.style.display = (gradeFound && genreFound) ? 'block' : 'none';
    });
}

function filterHomeBooksNav(bookSelector, sectionSelector, activeGrade, activeGenre) {
    document.querySelectorAll(bookSelector).forEach(function(book) {
        var gradeFound = activeGrade === null || bookMatchesGrades(book, [activeGrade]);
        var genreFound = activeGenre === null || book.dataset.genre === activeGenre;
        book.style.display = (gradeFound && genreFound) ? '' : 'none';
    });

    document.querySelectorAll(sectionSelector).forEach(function(section) {
        var hasVisible = false;
        section.querySelectorAll(bookSelector).forEach(function(book) {
            if (book.style.display !== 'none') {
                hasVisible = true;
            }
        });
        section.style.display = hasVisible ? '' : 'none';
    });
}

function filterBooksByGradesGenresAndMore(bookSelector, gradeCheckboxSelector, genreCheckboxSelector, categoryCheckboxSelector, publisherCheckboxSelector) {
    var selectedGrades = getSelectedGrades(gradeCheckboxSelector);
    var genres = getSelectedClassPrefixes(genreCheckboxSelector, 'genre-');
    var categories = getSelectedClassPrefixes(categoryCheckboxSelector, 'cat-');
    var publishers = getSelectedClassPrefixes(publisherCheckboxSelector, 'publisher-');

    document.querySelectorAll(bookSelector).forEach(function(book) {
        var gradeFound = bookMatchesGrades(book, selectedGrades);
        var genreFound = bookMatchesClassPrefixes(book, genres);
        var categoryFound = categories.length === 0 || bookMatchesClassPrefixes(book, categories);
        var publisherFound = publishers.length === 0 || bookMatchesClassPrefixes(book, publishers);
        book.style.display = (gradeFound && genreFound && categoryFound && publisherFound) ? 'block' : 'none';
    });
}

// --- Anasayfa filtreleri ---

var homeFilterState = { grade: null, genre: null };
var homeFiltersInitialized = false;
var syncingFromHash = false;

var GRADE_TO_SLUG = {
    '0': 'okul-oncesi',
    '1': '1-sinif',
    '2': '2-sinif',
    '3': '3-sinif',
    '4': '4-sinif',
    '5': '5-sinif',
    '6': '6-sinif',
    '7': '7-sinif',
    '8': '8-sinif'
};

var SLUG_TO_GRADE = {
    'okul-oncesi': '0',
    '1-sinif': '1',
    '2-sinif': '2',
    '3-sinif': '3',
    '4-sinif': '4',
    '5-sinif': '5',
    '6-sinif': '6',
    '7-sinif': '7',
    '8-sinif': '8'
};

var GENRE_TO_SLUG = {
    education: 'egitim',
    story: 'hikaye'
};

var SLUG_TO_GENRE = {
    egitim: 'education',
    hikaye: 'story'
};

function normalizeSlug(raw) {
    if (!raw) {
        return '';
    }
    var slug = decodeURIComponent(raw).toLowerCase().replace(/^\/+|\/+$/g, '');
    slug = slug
        .replace(/ğ/g, 'g')
        .replace(/ü/g, 'u')
        .replace(/ş/g, 's')
        .replace(/ı/g, 'i')
        .replace(/ö/g, 'o')
        .replace(/ç/g, 'c')
        .replace(/é/g, 'e');
    return slug;
}

function parseFilterHash() {
    var hash = window.location.hash.replace(/^#/, '');
    if (!hash) {
        return null;
    }

    var parts = hash.split('/').map(normalizeSlug).filter(Boolean);
    if (parts.length === 0 || parts.length > 2) {
        return null;
    }

    if (parts.length === 1) {
        var genreOnly = SLUG_TO_GENRE[parts[0]];
        if (genreOnly !== undefined) {
            return { grade: null, genre: genreOnly };
        }

        var gradeOnly = SLUG_TO_GRADE[parts[0]];
        if (gradeOnly !== undefined) {
            return { grade: gradeOnly, genre: null };
        }

        return null;
    }

    var grade = SLUG_TO_GRADE[parts[0]];
    if (grade === undefined) {
        return null;
    }

    var genre = SLUG_TO_GENRE[parts[1]];
    if (genre === undefined) {
        return null;
    }

    return { grade: grade, genre: genre };
}

function buildFilterHash(grade, genre) {
    if (grade === null || grade === undefined) {
        if (genre) {
            var genreOnlySlug = GENRE_TO_SLUG[genre];
            if (genreOnlySlug) {
                return '#' + genreOnlySlug;
            }
        }
        return '';
    }

    var gradeSlug = GRADE_TO_SLUG[grade];
    if (!gradeSlug) {
        return '';
    }

    if (!genre) {
        return '#' + gradeSlug;
    }

    var genreSlug = GENRE_TO_SLUG[genre];
    if (!genreSlug) {
        return '#' + gradeSlug;
    }

    return '#' + gradeSlug + '/' + genreSlug;
}

function updateFilterHash() {
    if (syncingFromHash) {
        return;
    }

    var hash = buildFilterHash(homeFilterState.grade, homeFilterState.genre);
    var url = window.location.pathname + window.location.search + hash;
    history.replaceState(null, '', url);
}

function closeAllGradeMenus() {
    document.querySelectorAll('.grade-nav-item').forEach(function(item) {
        item.classList.remove('open');
        var caret = item.querySelector('.grade-nav-caret');
        if (caret) caret.setAttribute('aria-expanded', 'false');
    });
}

function updateGradeLabels() {
    document.querySelectorAll('.grade-nav-item').forEach(function(item) {
        var labelText = item.querySelector('.grade-nav-text');
        if (!labelText) return;

        item.classList.remove('has-genre');
        labelText.removeAttribute('data-genre-label');
        if (item.classList.contains('active') && homeFilterState.genre) {
            item.classList.add('has-genre');
            labelText.setAttribute('data-genre-label', ' · ' + (homeFilterState.genre === 'education' ? 'Eğitim' : 'Hikaye'));
        }
        item.querySelectorAll('.grade-submenu button').forEach(function(btn) {
            btn.classList.remove('active');
        });
        if (item.classList.contains('active') && homeFilterState.genre) {
            var activeBtn = item.querySelector('.grade-submenu button[onclick*="' + homeFilterState.genre + '"]');
            if (activeBtn) activeBtn.classList.add('active');
        }
    });
}

function filterHomeBooks() {
    filterHomeBooksNav('.listbooks-home-item', '.book-genre-group', homeFilterState.grade, homeFilterState.genre);
    updateGradeLabels();
}

function scrollToBookResults() {
    if (!document.getElementById('books-section')) {
        return;
    }

    var target = null;
    document.querySelectorAll('.book-genre-group').forEach(function(section) {
        if (section.style.display === 'none') {
            return;
        }
        if (!target) {
            target = section.querySelector('.book-genre-heading') || section;
        }
    });

    if (!target) {
        return;
    }

    var nav = document.getElementById('MagicMenu');
    var navOffset = nav ? nav.offsetHeight : 64;
    var extraGap = 12;
    var rect = target.getBoundingClientRect();

    if (rect.top >= navOffset + extraGap && rect.top <= window.innerHeight * 0.35) {
        return;
    }

    var top = rect.top + window.pageYOffset - navOffset - extraGap;
    window.scrollTo({
        top: Math.max(0, top),
        behavior: 'smooth'
    });
}

function applyFilterState(grade, genre, options) {
    options = options || {};
    homeFilterState.grade = grade;
    homeFilterState.genre = genre;

    document.querySelectorAll('.grade-nav-item').forEach(function(el) {
        el.classList.remove('active');
    });

    if (grade !== null) {
        var activeItem = document.querySelector('.grade-nav-item[data-grade="' + grade + '"]');
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }

    closeAllGradeMenus();
    filterHomeBooks();

    if ((grade !== null || genre !== null) && options.scrollToResults !== false) {
        requestAnimationFrame(function() {
            scrollToBookResults();
        });
    }

    if (options.updateHash !== false) {
        updateFilterHash();
    }
}

function applyFilterFromHash() {
    if (!document.getElementById('books-section')) {
        return;
    }

    syncingFromHash = true;
    var parsed = parseFilterHash();

    if (parsed === null) {
        applyFilterState(null, null, { updateHash: false, scrollToResults: false });
    } else {
        applyFilterState(parsed.grade, parsed.genre, { updateHash: false, scrollToResults: true });
    }

    syncingFromHash = false;
}

function selectGrade(btn, grade) {
    var item = btn.closest('.grade-nav-item');
    if (item.classList.contains('active') && homeFilterState.grade === grade && homeFilterState.genre === null) {
        applyFilterState(null, null, { scrollToResults: false });
    } else {
        applyFilterState(grade, null);
    }
}

function selectGenre(btn, genre) {
    var item = btn.closest('.grade-nav-item');
    var grade = item.dataset.grade;
    applyFilterState(grade, genre);
}

function toggleGradeMenu(caret, event) {
    event.stopPropagation();
    var item = caret.closest('.grade-nav-item');
    var isOpen = item.classList.contains('open');
    closeAllGradeMenus();
    if (!isOpen) {
        item.classList.add('open');
        caret.setAttribute('aria-expanded', 'true');
    }
}

function initHomeBookFilters() {
    if (homeFiltersInitialized) {
        return;
    }
    homeFiltersInitialized = true;

    document.addEventListener('click', function(event) {
        if (!event.target.closest('.grade-nav-item')) {
            closeAllGradeMenus();
        }
    });

    if (window.matchMedia('(hover: hover)').matches) {
        document.querySelectorAll('.grade-nav-item').forEach(function(item) {
            item.addEventListener('mouseenter', function() {
                closeAllGradeMenus();
                item.classList.add('open');
            });
            item.addEventListener('mouseleave', function() {
                item.classList.remove('open');
            });
        });
    }

    window.addEventListener('hashchange', applyFilterFromHash);
    applyFilterFromHash();
}

// --- Ürünler sayfası filtreleri ---

function gradeselectall() {
    var checkboxes = document.querySelectorAll('input.check-grade');
    var selectAllCheckbox = document.getElementById('gradeselectall');
    checkboxes.forEach(function(checkbox) {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

function genreselectall() {
    var checkboxes = document.querySelectorAll('input.check-genre');
    var selectAllCheckbox = document.getElementById('genreselectall');
    checkboxes.forEach(function(checkbox) {
        checkbox.checked = selectAllCheckbox.checked;
    });
    filterBooks();
}

function categoryselectall() {
    var checkboxes = document.querySelectorAll('input.check-category');
    var selectAllCheckbox = document.getElementById('categoryselectall');
    checkboxes.forEach(function(checkbox) {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

function publisherselectall() {
    var checkboxes = document.querySelectorAll('input.check-publisher');
    var selectAllCheckbox = document.getElementById('publisherselectall');
    checkboxes.forEach(function(checkbox) {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

function filterBooks() {
    filterBooksByGradesAndGenres('.listbooks-item', '.check-grade', '.check-genre');
}

function initBooksPageFilters() {
    // Filtreler onclick ile bağlı; ek init gerekmez
}

// --- Başlatma ---

function bootBookFilters() {
    if (document.getElementById('books-section')) {
        initHomeBookFilters();
    }
}

function scheduleBookFilters() {
    if ('requestIdleCallback' in window) {
        requestIdleCallback(bootBookFilters);
    } else {
        setTimeout(bootBookFilters, 1);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', scheduleBookFilters);
} else {
    scheduleBookFilters();
}

window.addEventListener('pageshow', function(event) {
    if (document.getElementById('books-section')) {
        applyFilterFromHash();
    }
});
