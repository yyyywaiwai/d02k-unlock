# d-02K ブートローダーアンロック記録

HUAWEI d-02K（HDL-L0J、8.0.0.153(C341)）を物理 testpoint ショートなしでアンロックした際の調査とコードです。初期化後の Fastboot で `oem get-bootinfo` が `unlocked` を返し、端末は初期設定画面まで起動しました。経緯と採用しなかった経路は [FINDINGS.md](FINDINGS.md) に記録しています。

## ファイル

ローカルの調査データを含む配置と移動履歴の見方は [ディレクトリ案内](docs/DIRECTORY_LAYOUT.md) を参照してください。

| 場所 | 内容 |
| --- | --- |
| `unlock_d02k.py` | ADB で新しいバックアップを取得し、USRKEY の書き込みから Fastboot の最終確認まで進めるスクリプト |
| `fastboot_with_reset.py` | Mac で応答しなかった Fastboot USB 接続をリセットしてからコマンドを送る補助スクリプト |
| `src/nve_ctl.c`、`bin/nve_ctl-arm64` | `USRKEY` を読み書きし、書き込み後に読み戻す小さなツールと実機で使用したバイナリ |
| `bin/cve-root-arm64`、`patches/` | 一時 root に使用したバイナリと、元の P20 Lite 向けソースとの差分 |
| `build_cve_root.sh`、`test_build_cve_root.py` | ソース取得・パッチ適用・一時 root ツールのビルドと、実機を使わない事前検査テスト |
| `test_unlock_d02k.py` | NVME の `USRKEY` を読む処理のオフラインテスト |

バックアップ、端末固有の解除コード、実行時の退避データは公開対象に含めていません。`backup/`、`runs/` は `.gitignore` で除外しています。XNU・iOS 16・uniLoader 関連のローカル調査データは削除済みです。

## スクリプトを使う場合

現在の端末はアンロック済みなので、`unlock_d02k.py` を再実行する必要はありません。このスクリプトは、今回確認したビルドのロックされた端末で手順を再現するための記録です。別のビルドでの動作は確認していません。実機での一連の操作は確認済みですが、まとめ直したスクリプト全体の再実行はしていません。

実行環境は macOS、Python 3.11 以降、Android SDK の `adb` と `fastboot`、`/opt/homebrew/lib/libusb-1.0.dylib`、ADB が許可された端末です。端末側で「OEMロック解除を有効にする」をオンにしてください。アンロック時には端末が初期化され、確認画面で音量キーと電源キーの操作が必要です。スクリプトは端末情報とロック状態を照合し、実行時に `runs/` へ新しい退避を作ってから NVME を変更します。

実行前に、手元で選んだ16桁の数字を `backup/unlock-code.txt` に1行で保存してください（`backup/` は必要に応じて作成）。これは公式発行コードを照合する処理ではなく、そのコードの SHA-256 を端末へ書き込む手順です。コードファイルは公開しないでください。

```bash
git clone https://github.com/yyyywaiwai/d02k-unlock.git
cd d02k-unlock
python3 -m unittest -v test_unlock_d02k.py
python3 unlock_d02k.py SERIAL
```

`SERIAL` には対象端末の `adb devices` に表示されるシリアルを指定します。実行時は Fastboot 端末を1台だけ接続してください。事前の退避や端末情報の照合に失敗した場合は、NVME の変更より前に停止します。NVME 書き込み後に失敗した場合は、`runs/` の新しい退避と `backup/unlock-code.txt` を保管し、端末の状態を確認してください。

## ビルド元

一時 root の元コードは [willboka/CVE-2019-2215-HuaweiP20Lite](https://github.com/willboka/CVE-2019-2215-HuaweiP20Lite) の `f2c72600bf20ece6b3161526504f1ec2e8a11b72` です。`patches/d02k-cve-2019-2215.patch` を適用し、[setools-android](https://github.com/xmikos/setools-android) の `e38bff264913e5bc2c8f18f67ec9f1017ace3982` から `libsepol.a` を作り、Android NDK 28.2 で arm64 向けにビルドしました。`src/nve_ctl.c` は同じ NDK の `aarch64-linux-android21-clang -O2 -Wall -Wextra -Werror` でビルドしています。元コードと依存コードのライセンスは `licenses/` に保存しました。

実機で使ったバイナリの SHA-256 は `bin/cve-root-arm64`: `9fcdcb9043e8f36361a8a6064764c72684bb09403f98e9086cef6a8f124bb060`、`bin/nve_ctl-arm64`: `24ffeaa190bc935cbdeeb8485f32de75a117b9c3d785eb77913e240fdd47a8ea` です。

## cve-root をソースからビルドする

macOS で Git、Python 3.11 以降、Android NDK **28.2.13676358** を用意してください。初回のソース取得にはインターネット接続が必要です。NDK は Android Studio の SDK Manager などで事前にインストールしてください。

リポジトリルートで NDK の場所を指定して実行します。以下は macOS の標準的な SDK 配置の例です。

```bash
export ANDROID_NDK_HOME="$HOME/Library/Android/sdk/ndk/28.2.13676358"
bash build_cve_root.sh
```

スクリプトは上記の固定コミットを取得し、既存パッチを検査して適用した後、`libsepol.a` と cve-root を順にビルドします。対象は `arm64-v8a`、API 21、4 KiB ページです。NDK r28 では `PAGE_SIZE` が未定義となるため、d-02K に合わせて `PAGE_SIZE=4096` を指定します。

実行ごとに Git 管理外の `work/cve-root.XXXXXX/` を新しく作り、次のファイルを残します。末尾のランダムな文字列を含む実際のパスは実行時に表示されます。

- `cve-root-arm64`：ELF64／AArch64 であることを検査した生成物。
- `SHA256SUMS`：生成物の SHA-256。
- `build-info.txt`：取得コミット、NDK バージョン、主要ビルド条件。
- `source/`：パッチ適用済みのソース、依存ソース、ビルド中間生成物。

失敗時も調査用ファイルを残します。スクリプトは端末への転送・実行をせず、`bin/cve-root-arm64` と `backup/stock-boot/` も変更しません。生成物はカーネルイメージではなく Android 用実行ファイルです。配布済みバイナリとのバイト単位の一致や、生成物の実機動作は別途検証が必要です。

2026-10-22 に macOS と NDK 28.2.13676358 で、ソース取得からビルド完了、ELF64／AArch64 の検査まで確認しました。このときの生成物の SHA-256 は `d10eb968151defa8e7ccf197842247fc3b6ef9eb0b254741853615fd7bdf57d4` で、実機で使用した配布済みバイナリとは一致していません。生成物の実機実行はしていません。

端末やネットワークを使わないテストは次のコマンドで実行できます。

```bash
bash -n build_cve_root.sh
python3 -B -m unittest -v test_unlock_d02k.py test_build_cve_root.py
```
