"""PostToolUse(Edit|Write) Hook: 수정된 TypeScript 파일을 Prettier로 자동 포맷팅한다.

Claude Code가 stdin으로 넘겨주는 JSON에서 파일 경로를 읽고,
.ts/.tsx 파일이면 frontend/에 설치된 Prettier로 포맷한다.
포맷 실패가 작업을 막지 않도록 항상 exit code 0으로 종료한다.
"""

import json
import subprocess
import sys
from pathlib import Path

# 포맷 대상 확장자
TARGET_SUFFIXES = {".ts", ".tsx"}

# 이 스크립트 위치 기준 프로젝트 루트 (.claude/hooks/ → 루트)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def find_prettier() -> Path | None:
    """frontend/node_modules에 설치된 Prettier 실행 파일을 찾는다."""
    bin_dir = FRONTEND_DIR / "node_modules" / ".bin"
    for name in ("prettier.cmd", "prettier"):  # Windows는 .cmd 우선
        candidate = bin_dir / name
        if candidate.exists():
            return candidate
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_input = payload.get("tool_input") or {}
    tool_response = payload.get("tool_response") or {}
    file_path = tool_input.get("file_path") or tool_response.get("filePath")
    if not file_path:
        return 0

    path = Path(file_path).resolve()
    if path.suffix not in TARGET_SUFFIXES or not path.is_file():
        return 0

    # frontend/ 밖의 TS 파일은 Prettier 설정 적용 범위가 아니므로 건너뛴다.
    if FRONTEND_DIR not in path.parents:
        return 0

    prettier = find_prettier()
    if prettier is None:
        print("[format_changed] Prettier 미설치: frontend/에서 npm install 필요", file=sys.stderr)
        return 0

    result = subprocess.run(
        [str(prettier), "--write", "--log-level", "warn", str(path)],
        cwd=FRONTEND_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    if result.returncode != 0:
        print(f"[format_changed] Prettier 실패: {path}\n{result.stderr}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
