# データ展開ツール 使い方

`pack` フォルダ内の `.klz` アーカイブを展開し、スクリプトの復号・テキスト化と音声の ogg 変換までを一括で行うツールです。

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

## ONScripter への変換

`extract_all.bat` で展開したあとに `tools\convert_to_ons.bat`(または `python convert_to_ons.py`)を実行すると、`onscripter` フォルダにゲーム一式ができます。本家 ONScripter(ogapee 版)向けが既定で、`--engine ponscripter` を付けると Ponscripter 向けの `ponscripter` フォルダを作ります。

```
python convert_to_ons.py [--engine onscripter|ponscripter] [--root DIR] [--out DIR] [--encoding cp932|utf-8] [--no-assets] [--copy]
```

| オプション | 説明 |
|---|---|
| `--engine` | 対象のエンジン(既定: `onscripter`) |
| `--root DIR` | `unpacked` を含むフォルダ(既定: `tools` の1つ上) |
| `--out DIR` | 出力先(既定: `<root>\onscripter` または `<root>\ponscripter`) |
| `--encoding` | スクリプトの文字コード。既定は ONScripter が `cp932`(Shift-JIS)、Ponscripter が `utf-8` |
| `--no-assets` | `0.txt` だけを作ります |
| `--copy` | 素材をハードリンクではなくコピーします(別ドライブに出力するとき) |

出力内容

| ファイル | 内容 |
|---|---|
| `0.txt` | 変換したゲーム本体のスクリプト |
| `*.bmp` | スクリプトが使う背景・イベント画像(`unpacked\dat` からのリンク。黒/白の全画面 `b.bmp` `w.bmp` を含む) |
| `t_*.png` / `window.png` | 立ち絵とメッセージウィンドウ(`.kbp` から変換) |
| `sel\sel_NN.png` | 選択肢のボタン画像(`select_mes.kbp` を切り出したもの。左が通常、右が選択中) |
| `music\` `voice\` `wav\` | スクリプトが使う音声(ogg / wav) |
| `movie\*.mpg` | スクリプトが使う動画(`unpacked\movie` からのリンク。`tools\extract_all.bat` が `video\*.mov` から作ります) |

### 実行のしかた

1. `onscripter` フォルダの直下に ONScripter 本体(`onscripter.exe` と SDL 関連の DLL)と、日本語対応のフォント `default.ttf` を置きます(どちらも同梱していません)。ONScripter は Windows 用のビルド済みファイルを配布していないので、<https://github.com/ogapee/onscripter_win> のソースからビルドするか、配布されているビルドを使ってください。
2. `onscripter.exe` を実行します。同じフォルダの `0.txt` が自動で読み込まれます。ウィンドウモードにするには `--window` を付けます。
3. ONScripter は文字コードが Shift-JIS の `0.txt` を前提にしています。UTF-8 で出力した `0.txt` は読めません。

ONScripter 向けに合わせてある点

- 立ち絵・メッセージウィンドウ・選択肢ボタンの PNG は、アルファを使うように `:a;`(選択肢は `:a/2,0,3;`)を付けて読み込みます。ONScripter は既定だと左上の色を透明色として扱い、PNG のアルファを無視するためです。
- ONScripter には矩形スプライト(`lsp ">800,600,#000000"`)が無いので、フェードアウト/フラッシュには `b.bmp` / `w.bmp` を `:c;`(透過なし)で使います。
- 選択肢の `btnwait` は、時間切れのとき `-2`(`btntime` 使用時)や `0` を返すため、これらを「時間切れ」として扱います(右クリックの `-1` は無視して待ち直します)。
- `globalon` は定義部、`getparam` はユーザー定義コマンド(`defsub`)の中だけで使える、というエンジンの制限に従って配置しています。

### 変換の方針

- 変換対象は `mei*.spr`(本編)、`eye.spr`、`ed1`〜`ed5.spr`(エピローグ)です。メニュー・CG/シーン鑑賞・セーブ画面などはエンジンの機能に任せるため変換しません。
- 各 `.spr` は共通ライブラリ(メッセージ表示・立ち絵・BGM など)を内蔵しています。変換ツールはその表から背景ファイル名・BGM・立ち絵のファイルと選択肢の配置を読み取り、ライブラリ呼び出しを `ons_runtime.txt` のコマンド(`s_bg` `s_chr` `s_fadein` `s_select` など)に置き換えます。
- メッセージは「名前 → ボイス → 本文」の順の ONScripter 形式になります(`\k\c` は `\`、`\k` は `@`、`\pw'..'` はボイス、`\ps'..'` は効果音)。名前は `s_nm` コマンドで名前欄の文字スプライトとして表示します。
- 選択肢は時間制限付きです。時間切れは「選択肢の数 + 1」番の結果になります(元のスクリプトと同じ扱い)。
- 章の切り替えは `name.spr` と `save.spr` の分岐表を `ons_runtime.txt` の `*s_chapter` に写してあります。
- 元のゲームでシーン鑑賞中だけ有効なフラグ(`V101[80]`)は 0 として扱い、到達しないコードは出力しません。
- 変数の対応は `ons_runtime.txt` の冒頭に書いてあります(物語のフラグは `%n`、CG解放フラグは `%400〜` など)。
- 動画は `mpegplay`(MPEG-1、クリックか Esc でスキップ)で再生します。`ons_runtime.txt` の `s_movie` が BGM・立ち絵・ウィンドウを片付けてから再生し、終わったら黒画面に戻します。再生する場所は元のスクリプトに合わせています。
  - アイキャッチ(`eye*.mov`): `eye.spr` の呼び出しそのままです。元のスクリプトでは、最初のアイキャッチ(`eye?a`)のあとに CM を 1 本流し、そのあとのアイキャッチ(`eye?b`)から本編に戻ります。以降の章は `eye?b` だけです(元のスクリプトの `V101[65]` が 1 のままのため)。
  - オープニング(`mei_demo.mov`): 「はじめから」を選んだあとに再生します。
  - CM: ゲーム開始時に 2 本を無作為に選び(`op.spr` と同じ)、1 本目をオープニングの後、2 本目を最初のアイキャッチの間に流します。同じ CM は選びません。`paru_cm1/2`・`TG1/2`・`youko`/`o_love` は元のゲームと同じく無作為に選びます。元の CM のうち 4 本(2・3・4・13 番)は動画ではなく静止画のスライドなので変換せず、選びません。CM の番号を表示する「提供」画面(`c_no.spr`)も変換していません。
  - エンディング(`ed_demo.mov`): 最終章のあと、エピローグの前に再生します。
  - `unpacked\movie` が無い、または一部の動画が無いときは、その動画を飛ばします(`0.txt` にも `s_movie` の行を出力しません)。
- 雪の演出、選択肢の制限時間ゲージ、スキップ以外の細かい画面効果は未対応です。未知のコマンドは `;` で始まるコメントとして残します。

### 確認していること・していないこと

- `ons_lint.py` で、ラベルの重複・未定義がないことを確認しています。
- Shift-JIS に変換できない文字が無いことを、全スクリプトの変換で確認しています(変換できない文字があれば、変換ツールがエラーで止まります)。
- 使っているコマンドがすべて ONScripter のソース(<https://github.com/ogapee/onscripter>)に存在すること、定義部/実行部の制限に反していないことを、ソースを読んで確認しています。
- 実際に ONScripter を起動しての動作確認は、このツールを作った環境にビルド済みの本体が無く、できていません。表示位置・フェードの見た目・音声の再生などは、実機で確認してください。動画は、変換した `.mpg` を ffmpeg で最後まで復号できること(映像は MPEG-1 の 30fps、音声は MP2 の 44.1kHz ステレオ)までは確認していますが、ONScripter の `mpegplay` で再生できるかは未確認です。`mpegplay` は smpeg を組み込んだビルドでのみ動きます。再生できないビルドの場合は、`unpacked\movie` を削除して変換し直すと、動画なしで遊べます。
- Ponscripter v4.0.0 では、起動時にスクリプトの処理中にエンジンが落ちる現象を確認しました(`msvcrt` のメモリコピーの異常で、このツールの作った環境でのみ再現するのか、スクリプトに原因があるのかは切り分けられていません)。Ponscripter 向けの出力はその点で動作未確認です。

## ファイル形式メモ

- **KLZ5**: 16 バイトのヘッダ、52 バイトのエントリ表、データ本体の順に並びます。各エントリは次のいずれかです。
  - モード 0: 無圧縮
  - モード 1: LZSS 圧縮(窓 2048 バイト)
  - モード 2: 直前バイトとの XOR(`voice` が使用)
- **SVS1**: スクリプト形式です。ヘッダの後ろの本体が、モード 1 と同じ LZSS で圧縮されています。文字列領域は NUL 区切りの Shift-JIS です。
- **SVS1 のコード部**: ヘッダ直後(+0x20)に 1024 個のラベル表があり、その後ろがバイトコードです(命令は 16 ビット単位)。先頭から `+0x04` までは全スクリプト共通のライブラリで、その後ろが各スクリプト固有のコードです。式は RPN で、`0x0200` が数値式、`0x0201` が文字列式、`0x019f` で終わります。`0x0314` が式の結果を引数として積み、`0x1000`〜`0x17ff` がコマンド、`0x0310` がラベル呼び出し、`0x0300`〜`0x0305` が分岐です。詳細は `svs_disasm.py` の冒頭コメントを見てください。
- **KBP1**: `KBP1`、0、幅、高さ、ヘッダサイズ(0x14)の順に各 32 ビットで並び、その後ろに BGRA の生データが続きます。アルファは 6 ビット(0〜63)です。
- **KOGG**: 36 バイトのヘッダ(`KOGG` + ヘッダサイズなど)の後ろに、通常の Ogg Vorbis がそのまま続きます。
- **MOV1**(`video\*.mov`): QuickTime ではない独自形式です。48 バイトのヘッダ(`MOV1`、フレーム数、15fps、幅、高さ、24bit、ファイルサイズ、トラック数 2、データ領域の位置)の後ろに、24 バイトのインデックス(フレーム数 + 1 個: 番号・サイズ・展開後サイズ・種別・位置・0)が続きます。最初のフレーム数個が JPEG のフレーム、最後の 1 個が音声(KOGG)です。位置はデータ領域の先頭からの相対値です。

詳細は各 `.py` の冒頭コメントにも記載しています。

## トラブルシューティング

- **「Python was not found」と表示される**: Python 3.9 以上をインストールし、「Add python.exe to PATH」にチェックを入れてください。
- **`pack folder not found`**: `tools` フォルダが `pack` と同じ階層にあるか確認してください。別の場所の場合は `--root` でゲームのフォルダを指定するか、そのフォルダを `extract_all.bat` にドロップしてください。
- **文字化けする**: `script_text` は UTF-8 です。メモ帳など UTF-8 に対応したエディタで開いてください。
