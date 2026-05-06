"""별도 EXE로 빌드되는 업데이터.
역할: 메인 EXE 종료 후 새 EXE로 교체하고 재실행.
Usage: WorkHelper_updater.exe <old_path> <new_path> <restart_path>
"""
import sys
import os
import time
import shutil
import subprocess


def main():
    if len(sys.argv) < 4:
        print("Usage: updater <old_path> <new_path> <restart_path>")
        sys.exit(1)

    old_path, new_path, restart_path = sys.argv[1], sys.argv[2], sys.argv[3]
    time.sleep(1.5)  # 메인 프로세스 종료 대기
    try:
        shutil.move(new_path, old_path)
    except Exception as e:
        print(f"파일 교체 실패: {e}")
        sys.exit(1)
    subprocess.Popen([restart_path])


if __name__ == "__main__":
    main()
