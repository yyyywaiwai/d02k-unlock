#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
: "${ANDROID_NDK_HOME:?Android NDK 28.2.13676358 の絶対パスを設定してください}"
NDK=$(cd -- "$ANDROID_NDK_HOME" && pwd)
if [[ ! -x "$NDK/ndk-build" ]] ||
    ! grep -Eq '^Pkg.Revision *= *28\.2\.13676358[[:space:]]*$' "$NDK/source.properties"; then
    echo 'Android NDK 28.2.13676358 が必要です。' >&2
    exit 1
fi
for tool in git python3; do
    command -v "$tool" >/dev/null
done

mkdir -p "$ROOT/work"
BUILD=$(mktemp -d "$ROOT/work/cve-root.XXXXXX")
trap 'echo "ビルド失敗。調査用ファイルを保持しました: $BUILD" >&2' ERR
echo "作業ディレクトリ: $BUILD"

fetch_source() {
    git clone --quiet --no-checkout "$1" "$3"
    git -C "$3" checkout --quiet --detach "$2"
    [[ $(git -C "$3" rev-parse HEAD) == "$2" ]]
}

EXPLOIT_REV=f2c72600bf20ece6b3161526504f1ec2e8a11b72
SETOOLS_REV=e38bff264913e5bc2c8f18f67ec9f1017ace3982
SRC="$BUILD/source"
fetch_source https://github.com/willboka/CVE-2019-2215-HuaweiP20Lite.git "$EXPLOIT_REV" "$SRC"
fetch_source https://github.com/xmikos/setools-android.git "$SETOOLS_REV" "$SRC/setools-android"
git -C "$SRC" apply --check "$ROOT/patches/d02k-cve-2019-2215.patch"
git -C "$SRC" apply "$ROOT/patches/d02k-cve-2019-2215.patch"

"$NDK/ndk-build" -C "$SRC/setools-android" NDK_PROJECT_PATH=. \
    APP_ABI=arm64-v8a APP_PLATFORM=android-21 APP_MODULES=sepol
cp "$SRC/setools-android/obj/local/arm64-v8a/libsepol.a" "$SRC/libsepol.a"
# d-02K は 4 KiB ページ。NDK r28 では PAGE_SIZE の明示が必要。
"$NDK/ndk-build" -C "$SRC" NDK_PROJECT_PATH=. NDK_APPLICATION_MK=Application.mk \
    APP_ABI=arm64-v8a APP_PLATFORM=android-21 APP_CFLAGS=-DPAGE_SIZE=4096
cp "$SRC/libs/arm64-v8a/cve-2019-2215" "$BUILD/cve-root-arm64"

python3 - "$BUILD/cve-root-arm64" <<'PY'
import hashlib
import struct
import sys
from pathlib import Path

binary = Path(sys.argv[1])
data = binary.read_bytes()
if len(data) < 64 or data[:7] != b"\x7fELF\x02\x01\x01" or struct.unpack_from("<H", data, 18)[0] != 183:
    raise SystemExit("生成物が ELF64 little-endian AArch64 ではありません")
checksum = f"{hashlib.sha256(data).hexdigest()}  {binary.name}\n"
(binary.parent / "SHA256SUMS").write_text(checksum)
print(checksum, end="")
PY
printf 'exploit=%s\nsetools=%s\nndk=28.2.13676358\nabi=arm64-v8a\napi=21\nPAGE_SIZE=4096\n' \
    "$EXPLOIT_REV" "$SETOOLS_REV" > "$BUILD/build-info.txt"
echo "生成物: $BUILD/cve-root-arm64"
echo 'ビルドのみ完了しました。端末操作と配布済みバイナリの上書きは行っていません。'
