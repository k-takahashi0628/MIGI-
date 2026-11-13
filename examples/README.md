# サンプル案件（架空）

実在の会社・人は使っていない。ここにあるのは、案件フォルダの形と、制作の流れを試すための素材だけ。

## sample-aosagi（株式会社アオサギ製麺（架空）・社員インタビュー）

- `project.json`・`ledger.json`：案件の基本情報と台帳（表記ルール 1 件・要確認 1 件）
- `sources/interview-record.md`：取材の記録（架空・27 発言）
- `sources/request.md`：採用担当からの依頼メモ（架空）
- `reference-run/`：2026-11-11 に STEP 1〜10 を通しで回したときの中間成果物と納品物。結果は「公開不可」で、清書は作っていない（公開の了承がない情報 3 件と時期の食い違い 1 件が残り、文章では直せないため。代表と本人への確認依頼を `delivery/reply.md` に作って止めた）。記事は 1,372 字で依頼の字数に届かず、作った文で埋めずに追加取材の質問 6 問を出した。発言の照合は A 28／D 0／E 0

## 試し方

```bash
cp -R examples/sample-aosagi projects/sample-aosagi
```

Claude Code で次のように頼む。

```text
/article-desk sample-aosagi 依頼メモと取材の記録から、社員インタビュー記事を作りたい
```

`projects/` の中身は Git に入らない（`.gitignore`）。サンプルを直したいときは `examples/` 側を直す。
