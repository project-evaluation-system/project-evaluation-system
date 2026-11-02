const MIN_FILES = 2;
const MAX_FILES = 5;
const NETWORK_ERROR = 'Сервер не отвечает. Проверьте, что приложение запущено.';

let files = [];

const screens = {
    upload: document.getElementById('screen-upload'),
    results: document.getElementById('screen-results'),
    errors: document.getElementById('screen-errors'),
};
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const pickButton = document.getElementById('pick-button');
const fileList = document.getElementById('file-list');
const counter = document.getElementById('counter');
const calcButton = document.getElementById('calc-button');
const uploadMessage = document.getElementById('upload-message');
const resultsMeta = document.getElementById('results-meta');
const resultsMessage = document.getElementById('results-message');
const resultsWarnings = document.getElementById('results-warnings');
const resultsBody = document.getElementById('results-body');
const adviceList = document.getElementById('advice-list');
const errorsBox = document.getElementById('errors-box');
const errorsWarnings = document.getElementById('errors-warnings');

function createElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) {
        element.className = className;
    }
    if (text !== undefined) {
        element.textContent = text;
    }
    return element;
}

function formatSize(bytes) {
    if (bytes < 1024) {
        return bytes + ' Б';
    }
    if (bytes < 1024 * 1024) {
        return Math.round(bytes / 1024) + ' КБ';
    }
    return (bytes / (1024 * 1024)).toFixed(1).replace('.', ',') + ' МБ';
}

function formatScore(value) {
    return value.toFixed(2).replace('.', ',');
}

function showScreen(name) {
    Object.keys(screens).forEach((key) => {
        screens[key].hidden = key !== name;
    });
    window.scrollTo(0, 0);
}

function showUploadMessage(text) {
    uploadMessage.textContent = text;
    uploadMessage.hidden = !text;
}

function showMessage(element, text) {
    element.textContent = text;
    element.hidden = !text;
}

function saveBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
}

async function errorText(response) {
    try {
        const data = await response.json();
        if (data.errors) {
            return data.errors.join(' ');
        }
    } catch (error) {
        // ответ не JSON, покажем общий текст
    }
    return 'Не удалось получить файл. Попробуйте ещё раз.';
}

function renderFiles() {
    fileList.textContent = '';
    files.forEach((file, index) => {
        const item = createElement('li', 'file-item');
        const remove = createElement('button', 'file-remove', '×');
        remove.type = 'button';
        remove.setAttribute('aria-label', 'Убрать файл ' + file.name);
        remove.addEventListener('click', () => {
            files.splice(index, 1);
            renderFiles();
        });
        item.append(
            createElement('span', 'file-icon', 'XLSX'),
            createElement('span', 'file-name', file.name),
            createElement('span', 'file-size', formatSize(file.size)),
            remove
        );
        fileList.append(item);
    });

    counter.textContent = 'Выбрано файлов: ' + files.length + ' (нужно от 2 до 5)';
    counter.classList.toggle('bad', files.length > MAX_FILES);
    calcButton.disabled = files.length < MIN_FILES || files.length > MAX_FILES;
}

function addFiles(list) {
    for (const file of list) {
        if (!files.some((f) => f.name === file.name)) {
            files.push(file);
        }
    }
    showUploadMessage('');
    renderFiles();
}

function fillWarnings(box, warnings) {
    box.textContent = '';
    box.hidden = !warnings || warnings.length === 0;
    if (box.hidden) {
        return;
    }
    const list = createElement('ul');
    warnings.forEach((text) => list.append(createElement('li', '', text)));
    box.append(list);
}

function toggleRow(mainRow, detailRow) {
    const open = detailRow.hidden;
    detailRow.hidden = !open;
    mainRow.setAttribute('aria-expanded', String(open));
    mainRow.querySelector('.arrow').textContent = open ? '▾' : '▸';
}

function renderResults(data) {
    const maxTotal = data.criteria.reduce((sum, c) => sum + c.max, 0);
    const meta = [];
    if (data.section) {
        meta.push('Секция: ' + data.section);
    }
    meta.push('экспертов: ' + data.experts.length);
    meta.push('участников: ' + data.results.length);
    resultsMeta.textContent = meta.join(', ');
    fillWarnings(resultsWarnings, data.warnings);

    resultsBody.textContent = '';
    data.results.forEach((result) => {
        const mainRow = createElement('tr', 'row-main');
        mainRow.tabIndex = 0;
        mainRow.setAttribute('aria-expanded', 'false');

        const place = createElement('td');
        place.append(result.place <= 3 ? createElement('span', 'badge', result.place) : String(result.place));

        const total = createElement('td');
        total.append(
            createElement('span', 'total', formatScore(result.total)),
            createElement('span', 'total-max', 'из ' + maxTotal)
        );

        mainRow.append(
            place,
            createElement('td', '', result.fio),
            total,
            createElement('td', '', result.experts_count),
            createElement('td', 'arrow', '▸')
        );

        const detailRow = createElement('tr', 'row-detail');
        detailRow.hidden = true;
        const detailCell = createElement('td');
        detailCell.colSpan = 5;
        const grid = createElement('div', 'criteria-grid');
        data.criteria.forEach((c) => {
            const item = createElement('div', 'criterion');
            item.append(
                createElement('span', 'criterion-name', c.short),
                createElement('span', 'criterion-value', formatScore(result.criteria[c.short]) + ' / ' + c.max)
            );
            grid.append(item);
        });
        detailCell.append(grid);
        detailRow.append(detailCell);

        mainRow.addEventListener('click', () => toggleRow(mainRow, detailRow));
        mainRow.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                toggleRow(mainRow, detailRow);
            }
        });
        resultsBody.append(mainRow, detailRow);
    });

    adviceList.textContent = '';
    if (data.advice.length === 0) {
        adviceList.append(createElement('p', 'empty-text', 'Эксперты не оставили комментариев'));
    }
    data.advice.forEach((entry) => {
        const block = createElement('div', 'advice-item');
        const list = createElement('ul');
        entry.items.forEach((advice) => {
            const li = createElement('li');
            li.append(createElement('span', 'advice-expert', advice.expert + ': '), advice.text);
            list.append(li);
        });
        block.append(createElement('strong', '', entry.fio), list);
        adviceList.append(block);
    });
}

function renderErrors(data) {
    const groups = new Map();
    const general = [];
    data.errors.forEach((text) => {
        const file = files.find((f) => text.includes('«' + f.name + '»'));
        if (!file) {
            general.push(text);
            return;
        }
        if (!groups.has(file.name)) {
            groups.set(file.name, []);
        }
        groups.get(file.name).push(text);
    });

    errorsBox.textContent = '';
    const addGroup = (title, messages) => {
        const group = createElement('div', 'error-group');
        if (title) {
            group.append(createElement('strong', '', title));
        }
        const list = createElement('ul');
        messages.forEach((text) => list.append(createElement('li', '', text)));
        group.append(list);
        errorsBox.append(group);
    };
    groups.forEach((messages, name) => addGroup(name, messages));
    if (general.length > 0) {
        addGroup('', general);
    }
    fillWarnings(errorsWarnings, data.warnings);
}

function resetFiles() {
    files = [];
    showUploadMessage('');
    showMessage(resultsMessage, '');
    renderFiles();
    showScreen('upload');
}

pickButton.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
    addFiles(fileInput.files);
    fileInput.value = '';
});

dropzone.addEventListener('dragover', (event) => {
    event.preventDefault();
    dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

dropzone.addEventListener('drop', (event) => {
    event.preventDefault();
    dropzone.classList.remove('dragover');
    addFiles(event.dataTransfer.files);
});

calcButton.addEventListener('click', async () => {
    const body = new FormData();
    files.forEach((file) => body.append('files', file));

    calcButton.disabled = true;
    calcButton.textContent = 'Считаем…';
    showUploadMessage('');

    let response;
    try {
        response = await fetch('/upload/', { method: 'POST', body });
    } catch (error) {
        showUploadMessage(NETWORK_ERROR);
    }

    if (response) {
        try {
            const data = await response.json();
            if (response.ok) {
                renderResults(data);
                showScreen('results');
            } else {
                renderErrors(data);
                showScreen('errors');
            }
        } catch (error) {
            showUploadMessage('Сервер вернул неожиданный ответ. Попробуйте ещё раз.');
        }
    }

    calcButton.textContent = 'Рассчитать рейтинг';
    renderFiles();
});

document.getElementById('report-button').addEventListener('click', async () => {
    const body = new FormData();
    files.forEach((file) => body.append('files', file));
    showMessage(resultsMessage, '');
    try {
        const response = await fetch('/generate-report/', { method: 'POST', body });
        if (response.ok) {
            saveBlob(await response.blob(), 'Итоговый_рейтинг.xlsx');
        } else {
            showMessage(resultsMessage, await errorText(response));
        }
    } catch (error) {
        showMessage(resultsMessage, NETWORK_ERROR);
    }
});

document.getElementById('template-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = document.getElementById('template-message');
    showMessage(message, '');
    try {
        const response = await fetch('/download-template', {
            method: 'POST',
            body: new FormData(event.target),
        });
        if (response.ok) {
            saveBlob(await response.blob(), 'Шаблон_оценки_жюри.xlsx');
        } else {
            showMessage(message, await errorText(response));
        }
    } catch (error) {
        showMessage(message, NETWORK_ERROR);
    }
});

document.getElementById('reset-button').addEventListener('click', resetFiles);
document.getElementById('retry-button').addEventListener('click', resetFiles);

renderFiles();
