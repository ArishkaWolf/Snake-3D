# Распространение Snake 3D v1.0

## Архив игрока

`dist/Snake-3D-v1.0-Windows.zip` содержит одну папку:

```text
Snake-3D-v1.0-Windows/
  Snake3D.exe
  README.txt                 инструкция игрока: распаковать и запустить
  _internal/                 Python, Panda3D, DLL, шрифты и WAV
  LICENSE
  THIRD_PARTY.md
  NotoSans-OFL.txt
  Panda3D-LICENSE.txt
  README_SOURCE.md
  docs/
  BUILD_INFO.json            версия и коммит исходников
  MANIFEST.sha256            контрольные суммы всех файлов сборки
```

Игроку не нужны Python, pip, Panda3D, Blender или сеть. Требуется Windows 10/11 x64
и рабочий графический драйвер OpenGL. ZIP нужно извлечь целиком; запуск одного EXE,
перенесённого без `_internal`, не поддерживается. Сохранения — в профиле Windows.

Упаковка — PyInstaller onedir, совместимый с используемым Panda3D 1.10.16.
Проект не переносился на другой движок; браузерная версия не создаётся.

## Воспроизводимая подготовка

Установите зависимости разработчика из `requirements-dev.txt`, затем:

```powershell
.\build_release.ps1
```

Скрипт запускает тесты, собирает EXE, создаёт обложки и скриншоты, упаковывает ZIP
и проверяет запуск извлечённой игры. Сборка в архив содержит состояние текущих
исходников: для публичного релиза сначала сделайте коммит, затем создайте архив.
`BUILD_INFO.json` отмечает незакоммиченные изменения, а публикация такого ZIP запрещена
скриптом `tools/github_release.py`.

Отдельные шаги:

```powershell
.\.venv\Scripts\python.exe tools\create_press_kit.py
.\.venv\Scripts\python.exe tools\package_release.py
.\.venv\Scripts\python.exe tools\verify_release.py dist\Snake-3D-v1.0-Windows.zip
```

Контрольная сумма всего архива находится в `Snake-3D-v1.0-Windows.zip.sha256`.
Результат запуска — `Snake-3D-v1.0-Windows.verification.json`.
Проверить SHA256 можно командой `Get-FileHash .\Snake-3D-v1.0-Windows.zip -Algorithm SHA256`.

## Что проверяет извлечённый EXE

- CRC ZIP и соответствие каждого файла MANIFEST.sha256.
- Запуск из отдельного каталога с пробелами и кириллицей, без исходников и Python в PATH.
- Создание сохранения по обычному пути LOCALAPPDATA, загрузку образа и настроек после перезапуска.
- Настоящее графическое окно, шрифт с кириллицей и пять загруженных звуков ненулевой длительности.
- Полный встроенный самотест трёх миров, меню, камеры, карты, наград и удаления сцен.
- Наличие встроенного интерпретатора и расположение ресурсов внутри извлечённого приложения.

Это изоляция зависимостей в текущей Windows, а не чистая Windows VM.
Windows Sandbox/отдельная VM в текущем окружении не доступны. На чистом другом
компьютере запуск пока не подтверждён. Проверка без Python в PATH не подменяет этот факт.

## GitHub Releases

Репозиторий: https://github.com/ArishkaWolf/Snake-3D
Релиз v1.0: https://github.com/ArishkaWolf/Snake-3D/releases/tag/v1.0

ZIP не хранится в Git-истории. Для публикации используется официальный REST API.
Авторизация берётся из GH_TOKEN / GITHUB_TOKEN либо настроенного Git Credential Manager;
секреты не выводятся и не записываются в файлы. Разрешение токена — Contents: write.

```powershell
.\.venv\Scripts\python.exe tools\github_release.py --check
.\.venv\Scripts\python.exe tools\github_release.py --publish --commit ПОЛНЫЙ_ХЕШ_КОММИТА
```

Публикация требует успешного отчёта для того же ZIP и того же чистого коммита.
Сначала создаётся черновик, затем загружаются игровой ZIP, SHA256 и набор itch.io.
Размеры и SHA256 удалённых файлов проверяются через API перед открытием релиза.
При конфликте с существующим файлом инструмент прекращает работу и не удаляет его.

## itch.io

Набор: `publishing/itchio/` и `dist/Snake-3D-v1.0-itchio-kit.zip`.
Название, описание, параметры страницы, инструкция, обложки 1260×1000/630×500
и пять PNG 1280×800 готовы. Порядок публикации — `publishing/itchio/PUBLISH_GUIDE.md`.
Войти в личный аккаунт и опубликовать страницу может владелец. Публикация на itch.io
этим проектом автоматически не выполняется.
