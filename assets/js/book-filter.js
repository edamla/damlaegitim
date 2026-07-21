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

function filterHomeBooksByGradeAndGenre(bookSelector, activeGrade, genreCheckboxSelector) {
    var genres = getSelectedClassPrefixes(genreCheckboxSelector, 'genre-');

    document.querySelectorAll(bookSelector).forEach(function(book) {
        var gradeFound = activeGrade === 'all' || bookMatchesGrades(book, [activeGrade]);
        var genreFound = bookMatchesClassPrefixes(book, genres);
        book.style.display = (gradeFound && genreFound) ? 'block' : 'none';
    });
}

function filterHomeBooksNav(bookSelector, sectionSelector, activeGrade, activeGenre) {
    document.querySelectorAll(bookSelector).forEach(function(book) {
        var gradeFound = activeGrade === null || bookMatchesGrades(book, [activeGrade]);
        var genreFound = activeGenre === null || book.dataset.genre === activeGenre;
        book.style.display = (gradeFound && genreFound) ? 'block' : 'none';
    });

    document.querySelectorAll(sectionSelector).forEach(function(section) {
        var hasVisible = false;
        section.querySelectorAll(bookSelector).forEach(function(book) {
            if (book.style.display !== 'none') {
                hasVisible = true;
            }
        });
        section.style.display = hasVisible ? 'block' : 'none';
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
