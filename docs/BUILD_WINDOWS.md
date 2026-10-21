# Windows onedir

## Сборка

Нужны Windows x64, Python x64 и установленные `requirements-dev.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\build_windows.ps1
```

Скрипт сначала запускает pytest и прекращает работу при ошибке.
PyInstaller читает `Snake3D.spec`, собирает Python, расширения Panda3D,
плагины рендерера/аудио, шрифт и WAV. Выбран режим папки для удобства диагностики.
Сборщик не создаёт установщик и не требует прав администратора.

При блокировке запуска ps1 политикой выполните две команды напрямую:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm Snake3D.spec
```

## Результат

```text
dist/Snake3D/
  Snake3D.exe
  README.md
  LICENSE
  THIRD_PARTY.md
  _internal/
    assets/
    panda3d/
    ... Python и DLL
```

Нужно передавать всю папку. Одного EXE недостаточно.
Сохранения находятся в `%LOCALAPPDATA%/Snake3D/save.json`, поэтому папку
приложения можно разместить в каталоге без прав записи.
Ресурсы читаются через `sys._MEIPASS`, затем размещаются в памяти VFS:
это также обходит проблему нативных загрузчиков со строками путей Windows с кириллицей.

## Проверка сборки

Обычный запуск: `dist\Snake3D\Snake3D.exe`.
Диагностика с отдельным профилем и ограниченным числом кадров:

```powershell
dist\Snake3D\Snake3D.exe --offscreen --mute --save-path artifacts\exe-save.json --smoke-frames 30 --screenshot artifacts\exe-main.png
```

Полное прохождение и PNG основных экранов непосредственно из EXE:

```powershell
dist\Snake3D\Snake3D.exe --offscreen --self-test
```

GUI-приложение может запускаться из PowerShell асинхронно: дождитесь завершения
процесса и появления `artifacts/smoke-report.json` с `passed: true`.
Самотест использует временный профиль. Для графических проблем попробуйте
`--mute`, обновите видеодрайвер, запустите исходники из терминала для вывода ошибок.

Исходники и сборка проверены в текущем Windows x64 окружении. Проверка на
другом компьютере без Python остаётся частью ручной приёмки. EXE не подписан.
`build/`, `dist/` и `artifacts/` не отправляются в Git.
