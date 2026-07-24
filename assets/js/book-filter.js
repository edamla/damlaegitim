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

    var grade = SLUG_TO_GRADE[parts[0]];
    if (grade === undefined) {
        return null;
    }

    if (parts.length === 1) {
        return { grade: grade, genre: null };
    }

    var genre = SLUG_TO_GENRE[parts[1]];
    if (genre === undefined) {
        return null;
    }

    return { grade: grade, genre: genre };
}

function buildFilterHash(grade, genre) {
    if (grade === null || grade === undefined) {
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

    if (grade !== null && options.scrollToResults !== false) {
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

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootBookFilters);
} else {
    bootBookFilters();
}

window.addEventListener('pageshow', function(event) {
    if (document.getElementById('books-section')) {
        applyFilterFromHash();
    }
});
