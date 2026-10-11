# データ展開ツール 使い方

`pack` フォルダ内の `.klz` アーカイブを展開し、スクリプトの復号・テキスト化と音声の ogg 変換までを一括で行うツールです。

## 動作環境

- Windows
- Python 3.9 以上(追加パッケージは不要)

## ワンタッチ実行

`tools\extract_all.bat` をダブルクリックするだけです。`pack` 内の全 `.klz` を処理し、結果を `unpacked` フォルダに出力します。

初回は約 1.5 分かかります(大半は `voice` の処理です)。完了後は `Press any key to continue` と表示されるので、キーを押すと閉じます。

別の場所にあるゲームフォルダを処理したい場合は、そのフォルダを `extract_all.bat` にドラッグ&ドロップしてください。そのフォルダ内の `pack` を読み込み、同じフォルダ内に `unpacked` を作ります。

```
ハヤシ迷作劇場\
├─ pack\        ← 入力(.klz)
├─ unpacked\    ← 出力(自動作成)
└─ tools\       ← このツール
```

## 出力内容

| 入力 | 出力先 | 内容 |
|---|---|---|
| `dat.klz` | `unpacked\dat` | 画像(`.bmp` / `.kbp`) |
| `wav.klz` | `unpacked\wav` | 効果音(`.wav`) |
| `music.klz` | `unpacked\music` | BGM(`.kog`) |
| | `unpacked\music_ogg` | BGM を標準 ogg に変換したもの |
| `voice.klz` | `unpacked\voice` | ボイス(`.kog`) |
| | `unpacked\voice_ogg` | ボイスを標準 ogg に変換したもの |
| `script.klz` | `unpacked\script` | スクリプト(`.spr`、圧縮のまま) |
| | `unpacked\script_decoded` | `.spr` の本体を展開したもの |
| | `unpacked\script_text` | 文字列(台詞・ファイル名など)を UTF-8 で書き出したもの |

- 出力先がすでにある場合は上書きします。
- `.klz` 内にスクリプトや `.kog` があれば、アーカイブ名を問わず自動で復号・変換します。
- テキストの `\k\c`(改ページ)や `\pw'NA20138.wav'`(ボイス指定)などの制御コードはそのまま残します。

## コマンドラインからの実行

`tools` フォルダで実行します。オプションは `extract_all.bat` にも渡せます。

`tools` フォルダの場所に関係なく、基準フォルダ(ルート)を指定できます。ルートの既定は `tools` の1つ上のフォルダで、`pack` はルート直下から読み込み、`unpacked` はルート直下に出力します。

```
python extract_all.py [--root DIR] [--pack DIR] [--out DIR] [--only NAME ...] [--jobs N] [--no-verify]
```

| オプション | 説明 |
|---|---|
| `--root DIR` | ゲームのフォルダ(`pack` を含むフォルダ)。既定: `tools` の1つ上 |
| `--pack DIR` | `.klz` のあるフォルダ。`--root` からの相対パス(既定: `pack`) |
| `--out DIR` | 出力先。`--root` からの相対パス(既定: `unpacked`) |
| `--only NAME ...` | 指定したアーカイブだけ処理(例: `--only script wav`) |
| `--jobs N` | 展開に使うプロセス数(既定: CPU 論理コア数) |
| `--no-verify` | ogg の CRC 検証を省略(`voice` の処理が約 70 秒から約 40 秒に短縮されます) |

`--pack` と `--out` には絶対パスも指定でき、その場合は `--root` に関係なくそのパスを使います。

例

```
python extract_all.py --only script
python extract_all.py --root D:\Games\Meisaku
python extract_all.py --root D:\Games\Meisaku --out D:\Work\unpacked
```

終了コードは、問題なしなら 0、サイズ不一致や変換失敗があれば 1 です。

## 個別ツール

| ファイル | 役割 |
|---|---|
| `extract_all.py` | 全体の流れを制御します(上記) |
| `klz_extract.py` | `.klz`(KLZ5 形式)を展開します |
| `svs_decode.py` | `.spr`(SVS1 形式)を展開し、文字列をテキスト化します |
| `kog_to_ogg.py` | `.kog` を ogg に変換します |

単独でも実行できます。

```
python klz_extract.py ..\pack\dat.klz ..\unpacked\dat
python svs_decode.py ..\unpacked\script ..\unpacked\script_decoded ..\unpacked\script_text
python kog_to_ogg.py ..\unpacked\voice ..\unpacked\voice_ogg --verify
```

## ファイル形式メモ

- **KLZ5**: 16 バイトのヘッダ、52 バイトのエントリ表、データ本体の順に並びます。各エントリは次のいずれかです。
  - モード 0: 無圧縮
  - モード 1: LZSS 圧縮(窓 2048 バイト)
  - モード 2: 直前バイトとの XOR(`voice` が使用)
- **SVS1**: スクリプト形式です。ヘッダの後ろの本体が、モード 1 と同じ LZSS で圧縮されています。文字列領域は NUL 区切りの Shift-JIS です。
- **KOGG**: 36 バイトのヘッダ(`KOGG` + ヘッダサイズなど)の後ろに、通常の Ogg Vorbis がそのまま続きます。

詳細は各 `.py` の冒頭コメントにも記載しています。

## トラブルシューティング

- **「Python was not found」と表示される**: Python 3.9 以上をインストールし、「Add python.exe to PATH」にチェックを入れてください。
- **`pack folder not found`**: `tools` フォルダが `pack` と同じ階層にあるか確認してください。別の場所の場合は `--root` でゲームのフォルダを指定するか、そのフォルダを `extract_all.bat` にドロップしてください。
- **文字化けする**: `script_text` は UTF-8 です。メモ帳など UTF-8 に対応したエディタで開いてください。
