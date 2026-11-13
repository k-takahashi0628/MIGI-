# 修正履歴

この案件の修正を、新しいものを下に一件ずつ足していく。書くのは production-manager。
一件の形は `templates/history-entry.md`。最低限、次を書く。

- 版：どの版からどの版を作ったか（例：v3 → v4）
- 日付
- 指示した人：名前と立場（決裁者／進行担当／本人）
- 指示の原文：要約せず、届いたとおりに貼る
- 許した範囲：`aco scope` の `--allow` に渡した指定（例：`heading:…`）
- 差分検査：`python3 scripts/aco scope` の結果（範囲の外の差分の件数。0 件でなければ戻した内容）
- 台帳の更新：足した locked・approved・rejected・pending・rules・decisions の ID
- 気づいた点：範囲の外で気づいたが直していないこと

記録は消さない。間違えた記録は、次の行に訂正を書く。

---

（ここから下に記録を足す）
