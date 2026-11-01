const MIN_FILES = 2;
const MAX_FILES = 5;
const NETWORK_ERROR = 'Сервер не отвечает. Проверьте, что приложение запущено.';

let files = [];

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const pickButton = document.getElementById('pick-button');
const fileList = document.getElementById('file-list');
const counter = document.getElementById('counter');
const calcButton = document.getElementById('calc-button');
const uploadMessage = document.getElementById('upload-message');

function formatSize(bytes) {
    if (bytes < 1024) {
        return bytes + ' Б';
    }
    if (bytes < 1024 * 1024) {
        return Math.round(bytes / 1024) + ' КБ';
    }
    return (bytes / (1024 * 1024)).toFixed(1).replace('.', ',') + ' МБ';
}

function showUploadMessage(text) {
    uploadMessage.textContent = text;
    uploadMessage.hidden = !text;
}

function renderFiles() {
    fileList.textContent = '';
    files.forEach((file, index) => {
        const item = document.createElement('li');
        item.className = 'file-item';

        const icon = document.createElement('span');
        icon.className = 'file-icon';
        icon.textContent = 'XLSX';

        const name = document.createElement('span');
        name.className = 'file-name';
        name.textContent = file.name;

        const size = document.createElement('span');
        size.className = 'file-size';
        size.textContent = formatSize(file.size);

        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'file-remove';
        remove.textContent = '×';
        remove.setAttribute('aria-label', 'Убрать файл ' + file.name);
        remove.addEventListener('click', () => {
            files.splice(index, 1);
            renderFiles();
        });

        item.append(icon, name, size, remove);
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
    showUploadMessage('');
    try {
        const response = await fetch('/upload/', { method: 'POST', body });
        const data = await response.json();
        if (data.errors) {
            showUploadMessage(data.errors.join(' '));
        }
    } catch (error) {
        showUploadMessage(NETWORK_ERROR);
    }
    renderFiles();
});

renderFiles();
