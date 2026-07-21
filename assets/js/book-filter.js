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

function closeAllGradeMenus() {
    document.querySelectorAll('.grade-nav-item').forEach(function(item) {
        item.classList.remove('open');
        var caret = item.querySelector('.grade-nav-caret');
        if (caret) caret.setAttribute('aria-expanded', 'false');
    });
}

function updateGradeLabels() {
    document.querySelectorAll('.grade-nav-item').forEach(function(item) {
        var label = item.querySelector('.grade-nav-label');
        item.classList.remove('has-genre');
        label.removeAttribute('data-genre-label');
        if (item.classList.contains('active') && homeFilterState.genre) {
            item.classList.add('has-genre');
            label.setAttribute('data-genre-label', ' · ' + (homeFilterState.genre === 'education' ? 'Eğitim' : 'Hikaye'));
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

function selectGrade(btn, grade) {
    var item = btn.closest('.grade-nav-item');
    if (item.classList.contains('active') && homeFilterState.grade === grade) {
        homeFilterState.grade = null;
        homeFilterState.genre = null;
        item.classList.remove('active');
    } else {
        document.querySelectorAll('.grade-nav-item').forEach(function(el) {
            el.classList.remove('active');
        });
        item.classList.add('active');
        homeFilterState.grade = grade;
        if (homeFilterState.genre) {
            homeFilterState.genre = null;
        }
    }
    closeAllGradeMenus();
    filterHomeBooks();
}

function selectGenre(btn, genre) {
    var item = btn.closest('.grade-nav-item');
    var grade = item.dataset.grade;
    document.querySelectorAll('.grade-nav-item').forEach(function(el) {
        el.classList.remove('active');
    });
    item.classList.add('active');
    homeFilterState.grade = grade;
    homeFilterState.genre = genre;
    closeAllGradeMenus();
    filterHomeBooks();
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
    if (document.querySelector('.listbooks-item')) {
        initBooksPageFilters();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootBookFilters);
} else {
    bootBookFilters();
}

window.addEventListener('pageshow', function(event) {
    if (event.persisted && document.getElementById('books-section')) {
        filterHomeBooks();
    }
});
