# ディレクトリ案内

アンロック用コードと、端末のバックアップを残しています。

## 公開するファイル

| 場所 | 内容 |
| --- | --- |
| `README.md` | アンロック手順、実行条件、注意事項 |
| `FINDINGS.md` | 実機で確認した結果と調査記録 |
| `unlock_d02k.py` | アンロック手順をまとめたスクリプト |
| `fastboot_with_reset.py` | macOS の Fastboot USB 接続の補助 |
| `test_unlock_d02k.py` | アンロック関連のオフラインテスト |
| `build_cve_root.sh`、`test_build_cve_root.py` | cve-root のソースビルドと事前検査テスト |
| `src/`、`bin/` | ツールのソースと実機用バイナリ |
| `patches/`、`licenses/` | 公開コードに対応するパッチとライセンス |
| `docs/` | この配置案内 |

## ローカルだけに置くデータ

以下は `.gitignore` の対象です。認証情報や端末固有情報を含む可能性があるため、フォルダーごと公開しないでください。

| 場所 | 内容 |
| --- | --- |
| `backup/nvme-original.bin` | 変更前の NVME バックアップ |
| `backup/unlock-code.txt` | 端末の解除コード |
| `backup/stock-boot/` | 純正 kernel／ramdisk／eRecovery と実機から取得した情報 |
| `runs/` | アンロックスクリプトが実行ごとに作る退避先。未実行時は存在しない |
| `work/cve-root.XXXXXX/` | ソースビルド時に新規作成する作業ディレクトリ。生成物、依存ソース、ビルド条件を保存 |

## 実機を使わない確認

リポジトリルートで実行します。

```bash
python3 -B -m unittest -v test_unlock_d02k.py
```
