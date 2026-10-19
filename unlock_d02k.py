#!/usr/bin/env python3
"""Replay the verified HDL-L0J 8.0.0.153(C341) unlock path on its backed-up device."""

import hashlib
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FINGERPRINT = "dtab/HDL-L0J/d-02K:8.0.0/HUAWEIHDL-L0J/19012602:user/release-keys"


def run(argv, *, input_text=None, timeout=100):
    result = subprocess.run(argv, input=input_text, text=True, capture_output=True, timeout=timeout)
    output = result.stdout + result.stderr
    if result.returncode:
        raise RuntimeError(output[-2000:] or f"command exited {result.returncode}")
    return output


def original_usrkey(raw):
    if len(raw) != 6_291_456:
        raise ValueError("NVME backup size differs from the tested device")
    offsets = [m.start() for m in re.finditer(b"USRKEY\0\0", raw)]
    if len(offsets) != 7:
        raise ValueError("expected seven USRKEY records")
    values = set()
    for offset in offsets:
        if int.from_bytes(raw[offset - 4:offset], "little") != 315:
            raise ValueError("USRKEY record number differs")
        if int.from_bytes(raw[offset + 12:offset + 16], "little") != 32:
            raise ValueError("USRKEY record size differs")
        values.add(raw[offset + 20:offset + 52])
    if len(values) != 1:
        raise ValueError("USRKEY copies disagree")
    return values.pop()


def wait_fastboot(serial, seconds=90):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        devices = run(["fastboot", "devices"], timeout=10)
        if devices.strip().split() == [serial, "fastboot"]:
            return
        time.sleep(1)
    raise RuntimeError("target did not enter Fastboot")


def main():
    if len(sys.argv) != 2 or not re.fullmatch(r"[A-Za-z0-9]+", sys.argv[1]):
        raise SystemExit("usage: python3 unlock_d02k.py SERIAL")
    serial = sys.argv[1]
    code = (ROOT / "backup/unlock-code.txt").read_text().strip()
    if not re.fullmatch(r"[0-9]{16}", code):
        raise ValueError("unlock-code.txt must contain 16 digits")
    desired = hashlib.sha256(code.encode("ascii")).digest()

    adb = ["adb", "-s", serial]
    if run(adb + ["get-state"]).strip() != "device":
        raise RuntimeError("ADB authorization is required")
    if run(adb + ["shell", "getprop", "ro.build.fingerprint"]).strip() != FINGERPRINT:
        raise RuntimeError("firmware fingerprint differs from the tested build")
    if run(adb + ["shell", "getprop", "ro.boot.flash.locked"]).strip() != "1":
        raise RuntimeError("bootloader is not in the expected locked state")

    print("OEMロック解除を有効にしてから続行してください。", flush=True)
    if input("初期化とデータ消去を伴います。続行する場合は UNLOCK と入力: ") != "UNLOCK":
        raise RuntimeError("cancelled before any NVE write")

    run(adb + ["push", str(ROOT / "bin/cve-root-arm64"), "/data/local/tmp/cve-root"])
    run(adb + ["push", str(ROOT / "bin/nve_ctl-arm64"), "/data/local/tmp/nve-ctl"])
    run(adb + ["shell", "chmod", "700", "/data/local/tmp/cve-root", "/data/local/tmp/nve-ctl"])

    def root(command, seconds=60):
        return run(adb + ["shell", "-T", f"timeout -k 5 {seconds} /data/local/tmp/cve-root"],
                   input_text=command + "\nexit\n", timeout=seconds + 30)

    backup = ROOT / "runs" / datetime.now().strftime("%Y%m%d-%H%M%S")
    backup.mkdir(parents=True, mode=0o700)
    print("共有ストレージを退避しています。", flush=True)
    run(adb + ["pull", "/sdcard/", str(backup)], timeout=1800)
    (backup / "sdcard").rename(backup / "shared-storage")
    if not any(p.is_file() for p in (backup / "shared-storage").rglob("*")):
        raise RuntimeError("shared-storage backup is empty")

    print("アプリデータとNVMEを退避しています。", flush=True)
    tar_output = root("umask 077; tar -C /data -cf /data/local/tmp/d02k-private-backup.tar "
                      "data user_de/0 system misc 2>/data/local/tmp/d02k-tar-errors.txt; "
                      "echo TAR_STATUS:$?; "
                      "dd if=/dev/block/mmcblk0p7 of=/data/local/tmp/d02k-nvme-original.bin bs=131072; "
                      "sha256sum /data/local/tmp/d02k-private-backup.tar /data/local/tmp/d02k-nvme-original.bin; "
                      "chown shell:shell /data/local/tmp/d02k-private-backup.tar "
                      "/data/local/tmp/d02k-tar-errors.txt /data/local/tmp/d02k-nvme-original.bin", seconds=600)
    status = re.search(r"TAR_STATUS:(\d+)", tar_output)
    if not status:
        raise RuntimeError("private data archive status is missing")
    for remote, local in (("d02k-private-backup.tar", "private-app-data.tar"),
                          ("d02k-tar-errors.txt", "private-app-data-warnings.txt"),
                          ("d02k-nvme-original.bin", "nvme-original.bin")):
        run(adb + ["pull", "/data/local/tmp/" + remote, str(backup / local)], timeout=1800)
        (backup / local).chmod(0o600)
    warnings = (backup / "private-app-data-warnings.txt").read_text().splitlines()
    if status.group(1) != "0" and not (status.group(1) == "1" and warnings and
                                          all("unknown file type '140000'" in line for line in warnings)):
        raise RuntimeError("private data archive failed; inspect warnings")
    for remote, local in (("d02k-private-backup.tar", "private-app-data.tar"),
                          ("d02k-nvme-original.bin", "nvme-original.bin")):
        match = re.search(r"([0-9a-f]{64})\s+/data/local/tmp/" + remote, tar_output)
        with (backup / local).open("rb") as file:
            digest = hashlib.file_digest(file, "sha256").hexdigest()
        if not match or digest != match.group(1):
            raise RuntimeError(local + " checksum mismatch")
    if (backup / "private-app-data.tar").stat().st_size < 1024:
        raise RuntimeError("private data archive is empty")
    original = original_usrkey((backup / "nvme-original.bin").read_bytes())
    if original == desired:
        raise ValueError("new and original USRKEY are equal")
    run(adb + ["shell", "rm", "/data/local/tmp/d02k-private-backup.tar",
               "/data/local/tmp/d02k-tar-errors.txt", "/data/local/tmp/d02k-nvme-original.bin"])

    current = root("/data/local/tmp/nve-ctl read").splitlines()[-1]
    if current != original.hex():
        raise RuntimeError("live USRKEY does not match the backed-up partition")
    output = root(f"/data/local/tmp/nve-ctl write {original.hex()} {desired.hex()}")
    if "USRKEY write and read-back verified" not in output:
        raise RuntimeError("USRKEY write was not verified")
    print("USRKEYを書き込み、読み戻しを確認しました。", flush=True)

    run(adb + ["reboot", "bootloader"])
    wait_fastboot(serial)
    fastboot = ["python3", str(ROOT / "fastboot_with_reset.py"), "-s", serial]
    if not re.search(r"\(bootloader\)\s+locked\b", run(fastboot + ["oem", "get-bootinfo"])):
        raise RuntimeError("Fastboot did not report locked; unlock command was not sent")
    print("端末に確認画面が出たら、音量キーで Yes を選び、電源キーで確定してください。", flush=True)
    print(run(fastboot + ["oem", "unlock", code], timeout=200), flush=True)
    print("初期設定画面まで起動したら、端末を再びFastbootに切り替えてください。", flush=True)
    wait_fastboot(serial, seconds=600)
    if not re.search(r"\(bootloader\)\s+unlocked\b", run(fastboot + ["oem", "get-bootinfo"])):
        raise RuntimeError("final Fastboot unlock verification failed")
    print("fastboot oem get-bootinfo: unlocked", flush=True)
    print(run(fastboot + ["reboot"]), flush=True)


if __name__ == "__main__":
    main()
