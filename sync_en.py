#!/usr/bin/env python3
"""
sync_en.py - 中英文镜像同步工具

用法：
  python sync_en.py --init        # 初始化 video-gen-en 目录
  python sync_en.py --check       # 检查差异
  python sync_en.py --sync        # 提取待翻译内容，生成翻译清单
  python sync_en.py --terms       # 显示术语表
  python sync_en.py --status      # 显示同步状态

翻译流程：
1. 运行 sync_en.py --sync，生成 translation_tasks.json
2. 将 translation_tasks.json 内容发给 Claude Code
3. Claude Code 执行翻译，生成 translated_files/
4. sync_en.py 将翻译结果同步到 video-gen-en/
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

# 目录配置
SOURCE_DIR = Path.home() / ".claude" / "skills" / "video-gen"
TARGET_DIR = Path.home() / ".claude" / "skills" / "video-gen-en"
META_DIR = SOURCE_DIR / ".sync"

# 需要翻译的文件列表
TRANSLATE_FILES = [
    "SKILL.md",
    "README.md",
    "reference/storyboard-spec.md",
    "reference/backend-guide.md",
    "reference/prompt-guide.md",
    "reference/api-reference.md",
    "video_gen_tools.py",
    "video_gen_editor.py",
]

# 直接复制的文件
COPY_FILES = [
    "config.json.example",
    "requirements.txt",
]


def load_terms() -> Dict:
    """加载术语映射表"""
    terms_path = META_DIR / "terms.json"
    if terms_path.exists():
        return json.loads(terms_path.read_text(encoding="utf-8"))
    return {"terms": {}, "skip_patterns": [], "preserve_in_code": []}


def compute_checksum(file_path: Path) -> str:
    """计算文件校验和"""
    content = file_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def load_checksums() -> Dict[str, str]:
    """加载已保存的校验和"""
    checksums_path = META_DIR / "checksums.json"
    if checksums_path.exists():
        return json.loads(checksums_path.read_text(encoding="utf-8"))
    return {}


def save_checksums(checksums: Dict[str, str]):
    """保存校验和"""
    checksums_path = META_DIR / "checksums.json"
    checksums_path.write_text(json.dumps(checksums, indent=2), encoding="utf-8")


def detect_chinese(text: str) -> bool:
    """检测文本中是否包含中文"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def find_chinese_segments(text: str) -> List[Tuple[int, int, str]]:
    """找出文本中所有中文片段的位置和内容"""
    segments = []
    for match in re.finditer(r'[\u4e00-\u9fff]+[^\u4e00-\u9fff]*[\u4e00-\u9fff]*', text):
        segments.append((match.start(), match.end(), match.group()))
    return segments


def extract_chinese_from_python(content: str) -> Dict[str, List[str]]:
    """提取 Python 文件中的中文内容（注释、docstring、日志）"""
    chinese_items = {
        "comments": [],
        "docstrings": [],
        "log_messages": [],
        "fstrings": [],
    }

    # 单行注释
    for match in re.finditer(r'#.*[\u4e00-\u9fff]+', content):
        chinese_items["comments"].append(match.group())

    # Docstring (三引号)
    for match in re.finditer(r'"""[\u4e00-\u9fff]+.*?"""', content, re.DOTALL):
        chinese_items["docstrings"].append(match.group())
    for match in re.finditer(r"'''[\u4e00-\u9fff]+.*?'''", content, re.DOTALL):
        chinese_items["docstrings"].append(match.group())

    # logger 日志消息
    for match in re.finditer(r'logger\.[a-z]+\([^)]*[\u4e00-\u9fff]+[^)]*\)', content):
        chinese_items["log_messages"].append(match.group())

    # f-string 中的中文
    for match in re.finditer(r'f"[^"]*[\u4e00-\u9fff]+[^"]*"', content):
        chinese_items["fstrings"].append(match.group())
    for match in re.finditer(r"f'[^']*[\u4e00-\u9fff]+[^']*'", content):
        chinese_items["fstrings"].append(match.group())

    return chinese_items


def check_diff() -> Dict[str, List[str]]:
    """检查源目录与目标目录的差异"""
    current_checksums = {}
    for file in TRANSLATE_FILES + COPY_FILES:
        source_path = SOURCE_DIR / file
        if source_path.exists():
            current_checksums[file] = compute_checksum(source_path)

    saved_checksums = load_checksums()

    diff = {
        "new_files": [],
        "modified": [],
        "unchanged": [],
        "missing": [],
    }

    for file, checksum in current_checksums.items():
        if file not in saved_checksums:
            diff["new_files"].append(file)
        elif saved_checksums[file] != checksum:
            diff["modified"].append(file)
        else:
            diff["unchanged"].append(file)

    for file in TRANSLATE_FILES + COPY_FILES:
        source_path = SOURCE_DIR / file
        if not source_path.exists():
            diff["missing"].append(file)

    return diff


def init_target_dir():
    """初始化目标目录"""
    print(f"Initializing {TARGET_DIR}...")

    if not TARGET_DIR.exists():
        TARGET_DIR.mkdir(parents=True)
        print(f"Created directory: {TARGET_DIR}")

    # 初始化 Git 仓库
    git_dir = TARGET_DIR / ".git"
    if not git_dir.exists():
        os.system(f"cd {TARGET_DIR} && git init")
        print("Initialized Git repository")

    # 创建子目录
    (TARGET_DIR / "reference").mkdir(exist_ok=True)

    print("✅ Target directory initialized")


def generate_translation_tasks() -> Dict:
    """生成翻译任务清单"""
    diff = check_diff()
    tasks = {
        "generated_at": datetime.now().isoformat(),
        "files_to_translate": [],
        "files_to_copy": [],
        "terms": load_terms()["terms"],
    }

    # 需要翻译的文件
    for file in diff["new_files"] + diff["modified"]:
        if file in TRANSLATE_FILES:
            source_path = SOURCE_DIR / file
            content = source_path.read_text(encoding="utf-8")

            task = {
                "file": file,
                "type": "markdown" if file.endswith(".md") else "python",
                "source_path": str(source_path),
                "target_path": str(TARGET_DIR / file),
                "content_preview": content[:500] + "..." if len(content) > 500 else content,
                "chinese_detected": detect_chinese(content),
            }

            if file.endswith(".py"):
                task["chinese_items"] = extract_chinese_from_python(content)

            tasks["files_to_translate"].append(task)

    # 直接复制的文件
    for file in COPY_FILES:
        if file in diff["new_files"] + diff["modified"] or not (TARGET_DIR / file).exists():
            tasks["files_to_copy"].append({
                "file": file,
                "source_path": str(SOURCE_DIR / file),
                "target_path": str(TARGET_DIR / file),
            })

    return tasks


def save_translation_tasks(tasks: Dict):
    """保存翻译任务清单"""
    tasks_path = META_DIR / "translation_tasks.json"
    tasks_path.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Translation tasks saved to: {tasks_path}")
    return tasks_path


def sync_copy_files(tasks: Dict):
    """同步直接复制的文件"""
    for item in tasks.get("files_to_copy", []):
        source = Path(item["source_path"])
        target = Path(item["target_path"])
        if source.exists():
            shutil.copy(source, target)
            print(f"Copied: {item['file']}")


def apply_translations(translated_dir: Path):
    """应用翻译结果"""
    if not translated_dir.exists():
        print(f"Error: {translated_dir} not found")
        return False

    for file in TRANSLATE_FILES:
        translated_path = translated_dir / file
        target_path = TARGET_DIR / file

        if translated_path.exists():
            # 确保 target 目录存在
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(translated_path, target_path)
            print(f"Applied translation: {file}")

    return True


def update_checksums():
    """更新校验和"""
    checksums = {}
    for file in TRANSLATE_FILES + COPY_FILES:
        source_path = SOURCE_DIR / file
        if source_path.exists():
            checksums[file] = compute_checksum(source_path)
    save_checksums(checksums)
    print("Checksums updated")


def show_status():
    """显示同步状态"""
    diff = check_diff()

    print("\n=== Sync Status ===")
    print(f"Source: {SOURCE_DIR}")
    print(f"Target: {TARGET_DIR}")

    print(f"\nNew files ({len(diff['new_files'])}):")
    for f in diff["new_files"]:
        print(f"  + {f}")

    print(f"\nModified ({len(diff['modified'])}):")
    for f in diff["modified"]:
        print(f"  ~ {f}")

    print(f"\nUnchanged ({len(diff['unchanged'])}):")
    for f in diff["unchanged"]:
        print(f"  = {f}")

    if diff["missing"]:
        print(f"\nMissing ({len(diff['missing'])}):")
        for f in diff["missing"]:
            print(f"  ! {f}")

    needs_sync = diff["new_files"] + diff["modified"]
    if needs_sync:
        print(f"\n⚠️ {len(needs_sync)} files need sync")
        print("Run: python sync_en.py --sync")
    else:
        print("\n✅ All files synced")


def show_terms():
    """显示术语表"""
    terms = load_terms()
    print("\n=== Term Mapping ===")
    for zh, en in sorted(terms["terms"].items()):
        print(f"  {zh} → {en}")


def main():
    parser = argparse.ArgumentParser(description="Sync video-gen to video-gen-en")
    parser.add_argument("--init", action="store_true", help="Initialize target directory")
    parser.add_argument("--check", action="store_true", help="Check diff between source and target")
    parser.add_argument("--sync", action="store_true", help="Generate translation tasks")
    parser.add_argument("--apply", action="store_true", help="Apply translations from translated_files/")
    parser.add_argument("--terms", action="store_true", help="Show term mapping")
    parser.add_argument("--status", action="store_true", help="Show sync status")

    args = parser.parse_args()

    if args.init:
        init_target_dir()
    elif args.check or args.status:
        show_status()
    elif args.sync:
        tasks = generate_translation_tasks()
        tasks_path = save_translation_tasks(tasks)
        sync_copy_files(tasks)
        print(f"\n📋 Translation tasks generated: {tasks_path}")
        print("\nNext steps:")
        print("1. Share translation_tasks.json with Claude Code")
        print("2. Claude Code will translate and output to translated_files/")
        print("3. Run: python sync_en.py --apply")
    elif args.apply:
        translated_dir = META_DIR / "translated_files"
        if apply_translations(translated_dir):
            update_checksums()
            print("\n✅ Translations applied")
    elif args.terms:
        show_terms()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()