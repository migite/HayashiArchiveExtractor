# 

林組より2002年に発売された「ハヤシ迷作劇場」のゲームアーカイブ`.klz`を展開するツールです。  
`pack` フォルダ内の `.klz` アーカイブを展開し、スクリプトの復号・テキスト化と音声の ogg 変換までを一括で行うツールです。  
同一ブランド他作品への対応は現時点で行っておりません。  

## 動作環境

- Windows
- Python 3.9 以上(追加パッケージは不要)
- 動画(`video\*.mov`)を変換する場合のみ [ffmpeg](https://ffmpeg.org/)(`ffmpeg.exe` が PATH にあるか、`--ffmpeg` で指定)。無い場合は動画だけ飛ばして、ほかの処理は行います。

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
| `video\*.mov` | `unpacked\movie` | 動画を軽い MPEG-1(`.mpg`、映像 400×300・30fps、音声 MP2)に変換したもの(ONScripter の `mpegplay` 用) |

- 出力先がすでにある場合は上書きします。
- `.klz` 内にスクリプトや `.kog` があれば、アーカイブ名を問わず自動で復号・変換します。
- テキストの `\k\c`(改ページ)や `\pw'NA20138.wav'`(ボイス指定)などの制御コードはそのまま残します。
- 動画の変換は約 5 秒です(29 本、計約 120 MB)。元の動画は独自形式(`MOV1`、中身は Motion JPEG と KOGG 音声)で、そのままでは再生が重いため、ONScripter(smpeg)が少ない負荷で再生できる MPEG-1 にしています。640×480 の動画は 400×300 に縮小します(`--movie-width` で変更できます)。

## コマンドラインからの実行

`tools` フォルダで実行します。オプションは `extract_all.bat` にも渡せます。

`tools` フォルダの場所に関係なく、基準フォルダ(ルート)を指定できます。ルートの既定は `tools` の1つ上のフォルダで、`pack` はルート直下から読み込み、`unpacked` はルート直下に出力します。

```
python extract_all.py [--root DIR] [--pack DIR] [--out DIR] [--only NAME ...] [--jobs N] [--no-verify]
                      [--no-movies] [--ffmpeg PATH] [--movie-width N]
```

| オプション | 説明 |
|---|---|
| `--root DIR` | ゲームのフォルダ(`pack` を含むフォルダ)。既定: `tools` の1つ上 |
| `--pack DIR` | `.klz` のあるフォルダ。`--root` からの相対パス(既定: `pack`) |
| `--out DIR` | 出力先。`--root` からの相対パス(既定: `unpacked`) |
| `--only NAME ...` | 指定したアーカイブだけ処理(例: `--only script wav`)。動画は `movie` で指定します(例: `--only movie`) |
| `--jobs N` | 展開に使うプロセス数(既定: CPU 論理コア数) |
| `--no-verify` | ogg の CRC 検証を省略(`voice` の処理が約 70 秒から約 40 秒に短縮されます) |
| `--no-movies` | `video\*.mov` を変換しません |
| `--ffmpeg PATH` | `ffmpeg` の場所(既定: PATH 上の `ffmpeg`) |
| `--movie-width N` | 動画の最大幅(ピクセル。既定: 400) |

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
| `mov_to_mpg.py` | `video\*.mov`(`MOV1` 形式)を軽い MPEG-1 の `.mpg` に変換します(ffmpeg が必要) |
| `svs_disasm.py` | `script_decoded` の `.spr` を命令単位で解析するライブラリです |
| `svs_dump.py` | `.spr` の中身(命令・引数・ラベル)を読める形で一覧表示します |
| `svs_to_ons.py` | `.spr` のシナリオを ONScripter(Ponscripter にも対応)のスクリプトに変換します |
| `ons_runtime.txt` | 変換後スクリプトの先頭に入るランタイム(ウィンドウ設定・背景・立ち絵・フェード・選択肢)です |
| `kbp_to_png.py` | `.kbp` 画像を PNG(アルファ付き)に変換します |
| `convert_to_ons.py` / `.bat` | 変換から素材の用意までを一括で行います |
| `ons_lint.py` | 変換後スクリプトのラベルの過不足を確認します |

単独でも実行できます。

```
python klz_extract.py ..\pack\dat.klz ..\unpacked\dat
python svs_decode.py ..\unpacked\script ..\unpacked\script_decoded ..\unpacked\script_text
python kog_to_ogg.py ..\unpacked\voice ..\unpacked\voice_ogg --verify
python mov_to_mpg.py ..\video ..\unpacked\movie
python svs_dump.py ..\unpacked\script_decoded\mei02b.spr
python kbp_to_png.py ..\unpacked\dat\t_li01.kbp ..\work
```


