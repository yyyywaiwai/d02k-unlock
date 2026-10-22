# Repository Guidelines

## プロジェクト構成
このリポジトリは HUAWEI d-02K のブートローダーアンロック手順と検証記録を管理する。

- `unlock_d02k.py`：端末照合、バックアップ、USRKEY 更新、Fastboot 状態確認。
- `fastboot_with_reset.py`：macOS の libusb を使う Fastboot 接続補助。
- `src/nve_ctl.c`、`bin/`：NVE 操作ツールのソースと実機用 arm64 バイナリ。一時 root 用バイナリの差分は `patches/`、ライセンスは `licenses/` に置く。
- `test_unlock_d02k.py`：合成 NVME データによるオフラインテスト。

実行条件の変更時は `README.md`、検証結果の記録時は `FINDINGS.md`、配置の確認時は `docs/DIRECTORY_LAYOUT.md` を参照する。過去のメモリと現在のファイルが食い違う場合は、現状を確認して判断する。削除済みの XNU・iOS 16・uniLoader 関連データを既存の開発環境として扱わず、過去の未実施診断を自動再開しない。

## 開発・ビルド・テスト
Python 3.11 以降を使用する。Python の追加パッケージは不要。次のコマンドはリポジトリルートで実行する。

```bash
python3 -B -m unittest -v test_unlock_d02k.py
```

このテストは端末に接続せず、合成データだけを使う。変更に応じて実行し、その変更による失敗を修正して再実行する。

Android NDK 28.2 のツールチェーンを PATH に設定した環境では、次のコマンドで NVE ツールをビルドする。

```bash
aarch64-linux-android21-clang -O2 -Wall -Wextra -Werror src/nve_ctl.c -o bin/nve_ctl-arm64
```

`python3 unlock_d02k.py SERIAL` は端末を初期化する実機操作。README の条件を満たし、明示的な実行依頼がある場合だけ使う。macOS、adb、fastboot、`/opt/homebrew/lib/libusb-1.0.dylib` が必要。Fastboot 端末は 1 台だけ接続する。

## コーディング規約
Python と C は既存の 4 スペースインデントに合わせる。Python の関数・変数は `snake_case`、定数は `UPPER_SNAKE_CASE`、テストは `test_*` とする。標準ライブラリと既存の補助関数を優先し、不要な依存や抽象化を増やさない。専用フォーマッター・リンター設定はない。C は上記の警告設定でビルドする。

## テスト方針
標準ライブラリの `unittest` を使う。解析処理を変えたら、正常系と関連する拒否条件のテストを追加する。実バックアップをテストデータにしない。数値のカバレッジ基準は未設定。

オフラインテスト成功、実機で確認した個別手順、整理後のスクリプト全体の再実行は区別して報告する。既存の実機記録は HDL-L0J、8.0.0.153(C341) が対象であり、別ビルドの動作を保証しない。実行前に端末の接続・ロック状態を確認し、未検証事項も明記する。

## コミット・Pull Request
既存の `feat: publish d-02K unlock scripts and research` に合わせ、`fix: ...` や `docs: ...` のような短い種別付き要約を使う。PR には目的、変更範囲、テスト結果、実機への影響、関連 issue があればそのリンクを記載する。動作条件の変更は README と調査記録にも反映する。バイナリ更新時はビルド条件と SHA-256 を示す。

## データ保護とエージェント向け指示
- `backup/`、`runs/`、解除コード、端末シリアル、認証情報をコミット・公開しない。`.gitignore` の除外を維持し、差分とステージ対象を確認する。
- `backup/stock-boot/` 内のファイルは変更・上書き・削除しない。改変が必要な場合は元ファイルを保持し、改変版を `backup/stock-boot/` の外にある別ディレクトリへ書き出す。
- 端末照合、バックアップ検証、書き込み前比較、読み戻し確認を省略しない。書き込み後に失敗した場合はバックアップを保持し、端末の状態を確認する。
- 既存の未コミット変更とローカルバックアップを保持する。削除・実機への書き込み・commit／push は、それぞれ明示的な依頼がある場合だけ行う。
- 思考は英語、ユーザーへの出力は日本語とする。完了時は変更点、検証結果、未確認事項を短く報告する。

指示ファイルの運用は [OpenAI 公式ガイド](https://learn.chatgpt.com/docs/agent-configuration/agents-md) を参照する。このファイルにはリポジトリ共通の指示を置き、詳しい経緯は上記の資料に残す。
