"""Erzeugt die Windows-Versionsinfo für PyInstaller (--version-file).

Damit zeigen Task-Manager, Explorer und Taskleiste "FM27 Face Generator" statt "Python".
Aufruf (im Build):  python tools/version_info.py build/version.txt
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fm27facegen import APP_NAME, __version__  # noqa: E402

nums = [int(x) for x in __version__.split(".") if x.isdigit()][:4]
nums += [0] * (4 - len(nums))
ver = tuple(nums)

TEXT = f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={ver}, prodvers={ver}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1,
                    subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040704B0', [
      StringStruct('CompanyName', 'FM27 Face Generator'),
      StringStruct('FileDescription', '{APP_NAME}'),
      StringStruct('FileVersion', '{__version__}'),
      StringStruct('InternalName', 'FM27-FaceGenerator'),
      StringStruct('OriginalFilename', 'FM27-FaceGenerator.exe'),
      StringStruct('ProductName', '{APP_NAME}'),
      StringStruct('ProductVersion', '{__version__}')])]),
    VarFileInfo([VarStruct('Translation', [0x0407, 1200])])
  ]
)
"""

if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "build/version.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(TEXT, encoding="utf-8")
    print(out)
