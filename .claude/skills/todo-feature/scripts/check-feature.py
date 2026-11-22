"""ToDo 기능 검증: 프로젝트 루트에서 실행. 설치된 검사기만 실행."""
from pathlib import Path
import shutil
import subprocess
import sys

root = Path.cwd()
checks = []
if (root / 'frontend' / 'package.json').exists():
    npm = shutil.which('npm')
    if npm:
        # Windows에서는 npm이 npm.cmd라서 'npm' 이름만으로는 실행되지 않는다. which로 찾은 경로를 쓴다.
        checks.append(([npm, 'run', 'build'], root / 'frontend'))
    else:
        print('SKIP: npm 미설치')
if (root / 'backend').is_dir():
    checks.append(([sys.executable, '-m', 'compileall', '-q', 'backend'], root))
    ruff = shutil.which('ruff')
    if ruff:
        checks.append(([ruff, 'check', 'backend'], root))
    else:
        print('SKIP: Ruff 미설치')
if not checks:
    print('SKIP: 검사 대상 프로젝트 없음')
    sys.exit(0)
failed = False
for command, cwd in checks:
    print('RUN:', ' '.join(command), flush=True)
    if subprocess.run(command, cwd=cwd, check=False).returncode:
        failed = True
print('FAIL' if failed else 'PASS')
sys.exit(1 if failed else 0)
