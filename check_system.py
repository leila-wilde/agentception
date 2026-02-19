#!/usr/bin/env python3
"""System validation script for Agentception.

Checks that Docker, Ollama, and workspace are properly configured.
Run this before starting your first session: python check_system.py
"""

import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: str) -> tuple[bool, str]:
    """Run a shell command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def check_docker() -> bool:
    """Verify Docker is installed and running."""
    print("[*] Checking Docker...")
    success, output = run_cmd("docker ps")
    if not success:
        print("  ❌ Docker is not running or not installed")
        print("     Fix: Install Docker or run: docker daemon")
        return False
    print("  ✅ Docker is running")
    return True


def check_docker_image() -> bool:
    """Verify agentception:dev image is built."""
    print("[*] Checking Docker image 'agentception:dev'...")
    success, output = run_cmd("docker image inspect agentception:dev")
    if not success:
        print("  ❌ Image 'agentception:dev' not found")
        print("     Fix: Build the image with: docker build -t agentception:dev .")
        return False
    print("  ✅ Docker image 'agentception:dev' is built")
    return True


def check_ollama() -> bool:
    """Verify Ollama is reachable."""
    print("[*] Checking Ollama connectivity...")
    success, output = run_cmd("curl -s http://localhost:11434/api/tags > /dev/null 2>&1")
    if not success:
        print("  ❌ Ollama is not reachable at http://localhost:11434")
        print("     Fix: Start Ollama in another terminal: ollama serve")
        return False
    print("  ✅ Ollama is reachable")
    return True


def check_ollama_model() -> bool:
    """Verify a model is available in Ollama."""
    print("[*] Checking for available models...")
    success, output = run_cmd("ollama list")
    if not success or "llama" not in output.lower():
        print("  ⚠️  No common models found")
        print("     Fix: Pull a model: ollama pull llama3.2")
        return False
    print("  ✅ Models available")
    return True


def check_python() -> bool:
    """Verify Python 3.11+ is available."""
    print("[*] Checking Python version...")
    success, output = run_cmd("python --version")
    if not success:
        print("  ❌ Python is not available")
        return False
    # Parse version
    try:
        version_str = output.strip()
        version_parts = version_str.split()[-1].split(".")
        major, minor = int(version_parts[0]), int(version_parts[1])
        if major < 3 or (major == 3 and minor < 11):
            print(f"  ⚠️  Python {major}.{minor} is installed, but 3.11+ is recommended")
            return True  # Soft fail — it might still work
        print(f"  ✅ Python {major}.{minor} is installed")
        return True
    except (ValueError, IndexError):
        print(f"  ⚠️  Could not parse Python version: {output}")
        return True  # Soft fail


def check_agentception_cli() -> bool:
    """Verify agentception CLI is installed."""
    print("[*] Checking agentception CLI...")
    success, output = run_cmd("agentception version")
    if not success:
        print("  ❌ 'agentception' command not found")
        print("     Fix: Install with: pip install -e .")
        return False
    print(f"  ✅ agentception CLI is installed ({output.strip()})")
    return True


def check_workspace() -> bool:
    """Verify workspace directory is writable."""
    print("[*] Checking workspace writability...")
    workspace = Path("/tmp/agentception-test")
    try:
        workspace.mkdir(parents=True, exist_ok=True)
        test_file = workspace / ".test"
        test_file.write_text("test")
        test_file.unlink()
        workspace.rmdir()
        print(f"  ✅ Workspace is writable (tested at {workspace})")
        return True
    except Exception as e:
        print(f"  ❌ Workspace not writable: {str(e)}")
        print("     Fix: Ensure /tmp/ is writable or use --workspace /path/to/workspace")
        return False


def main() -> int:
    """Run all checks and report status."""
    print("\n" + "=" * 60)
    print("Agentception System Validation")
    print("=" * 60 + "\n")

    checks = [
        ("Python", check_python),
        ("Docker", check_docker),
        ("Docker Image", check_docker_image),
        ("Ollama", check_ollama),
        ("Ollama Models", check_ollama_model),
        ("Agentception CLI", check_agentception_cli),
        ("Workspace", check_workspace),
    ]

    results = []
    for name, check_fn in checks:
        try:
            passed = check_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"  ❌ Exception during check: {str(e)}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")

    print(f"\n{passed_count}/{total_count} checks passed\n")

    if passed_count == total_count:
        print("🎉 All checks passed! You're ready to run: agentception chat")
        return 0
    elif passed_count >= total_count - 1:
        print(
            "⚠️  Most checks passed. Some optional components may be missing.\n"
            "You can still try: agentception chat"
        )
        return 0
    else:
        print("❌ Please fix the failing checks above before running agentception chat")
        return 1


if __name__ == "__main__":
    sys.exit(main())
