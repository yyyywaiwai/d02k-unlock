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

## 2026-10-22 の不要データ削除

ユーザー指定により、XNU・iOS 16・uniLoader 関連の調査データを削除しました。

- `work/` 全体：外部ソース、XNU ビルドツリー、iOS 16 素材、payload、QEMU 結果、ログ、補助コード、調査パッチ。
- `backup/stock-boot/card-map/`：iOS root 用の SD／eMMC ストレージ配置データ。
- 直前の整理で作成した移動記録・復元手順も `work/` とともに削除。

独立した uniLoader ディレクトリは、削除前の確認時点で存在しませんでした。関連調査が残っていた `work/` を削除対象に含めています。
アンロック用スクリプト、公開用バイナリ・パッチ、解除コード、NVME と純正起動イメージのバックアップは保持しています。
削除した調査データの新しい退避コピーは作成していません。`.gitignore` の `/work/` と `/upstream-uniloader/` は、再作成時の誤公開を防ぐため残しています。

## 実機を使わない確認

リポジトリルートで実行します。

```bash
python3 -B -m unittest -v test_unlock_d02k.py
```
