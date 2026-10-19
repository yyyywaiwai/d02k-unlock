# d-02Kのブートローダーアンロック調査

## 結論

手元の HUAWEI d-02K（HDL-L0J、Android 8.0.0、ビルド 8.0.0.153(C341)）は、物理的な testpoint ショートや有料の解除ツールを使わずにアンロックできた。端末の初期化と通常起動を経たあと、Fastboot の `oem get-bootinfo` が `unlocked` を返した。確認後に `fastboot reboot` も正常終了した。この結果は今回接続した個体とビルドについての記録であり、別のファームウェアでの成功を意味しない。

## 実機で確認した経路

開始時点では `ro.boot.flash.locked=1` で、`fastboot oem get-bootinfo` は `locked` を返した。開発者向けオプションの「OEMロック解除を有効にする」をオンにしても、コードなしの `fastboot flashing unlock` は `check password failed!` で終了した。

一時 root の取得には P20 Lite 向けの CVE-2019-2215 実装を利用した。d-02K のカーネルに合わせてアドレスを修正し、SELinux の変更範囲を `shell` タイプに限定した。実行ログで UID 0 への変更を確認し、root シェルから NVME パーティションを退避した。CVE-2019-2215 の原因と権限昇格については [Project Zero の解説](https://projectzero.google/2019/11/bad-binder-android-in-wild-exploit.html)、元にしたコードについては [P20 Lite 向けの実装](https://github.com/willboka/CVE-2019-2215-HuaweiP20Lite)を参照した。

NVME は `/dev/block/mmcblk0p7` 上の 6,291,456 バイトで、退避したイメージには NVE 番号 315 の `USRKEY` が 7 か所にあった。各データ長は 32 バイトで、退避時の値は一致していた。16 桁の解除コードの SHA-256 を `/dev/nve0` の ioctl で `USRKEY` に書き込み、読み戻して同じ値であることを確認した。`USRKEY` に解除コードの SHA-256 を書く方式は [PotatoNV の説明](https://github.com/kitsuned/PotatoNV)と [hisi-nve の例](https://github.com/R0rt1z2/hisi-nve)を参照した。使用したコード自体はこの文書に記載せず、ローカルの `backup/unlock-code.txt` に保存した（公開リポジトリには含めない）。

続いて `fastboot oem unlock CODE` を実行した。端末側で Yes を選んで確定すると、Fastboot は `The device will reboot and do factory reset...` と `OKAY` を返した。初期化後、端末が初期設定画面まで起動したことを画面で確認した。再び Fastboot に入り、`oem get-bootinfo` の `unlocked` を確認した。一般的な `getvar unlocked` はこのブートローダーで `Command not allowed` となったため、状態判定には使っていない。

## 調査したが採用しなかった経路

標準の解除コード発行サービスは利用できず、コードなしの Fastboot 操作でも解除できなかった。[DC-Phoenix の Software Testpoint](https://www.dc-unlocker.com/dcphoenix-enable-software-tp)と [HCU Client](https://hcu-client.com/huawei-bootloader-code-read-via-testpoint/)は物理ショートを使わない候補だったが、Windows 用ツールとライセンスが必要で、今回は使っていない。Kirin Tool Linux のソースも調べたが、その経路には VCOM モードと対応するローダーが必要だった。ProjectMenu から Manufacture Mode に切り替えると Huawei の AT ポートに応答があったものの、それだけでは解除できず、最終経路には含めていない。

Mac の Fastboot は USB 接続を認識していてもコマンドが応答しないことがあった。今回の接続では VID:PID `18d1:d00d` のデバイスを libusb でリセットすると通信できた。`fastboot_with_reset.py` はこの対応をまとめたもの。8.0.0.155(C341) のファームウェアからカーネルを取り出し、オフラインで解析してアドレスを特定したが、端末へは書き込んでいない。

## データと再現条件

アンロックは端末を初期化した。実行前に `/sdcard/` の 3,050 ファイル、`/data/data` などのアプリデータ、変更前の NVME を退避した。`backup/` に保存したアプリデータや NVME には認証情報や端末固有情報が含まれる可能性があるため、第三者に共有しない。アプリデータの tar は特殊ファイル 4 件を含まず、初期化後にそのまま復元できることも確認していない。

`unlock_d02k.py` はこのビルドで確認した流れをまとめた。実行には ADB 接続と OEM ロック解除の設定が必要で、スクリプトは新たな退避を終えてから NVE を変更する。現在の端末はすでにアンロック済みで、ADB が使える状態でもロック状態の事前確認で停止する。カーネルのアドレスや NVE の構造が異なる端末への転用は検証していない。
