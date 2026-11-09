# 🎟️ GiveawayProof

**Crypto giveaways the host can't rig.**

GiveawayProof is a GenLayer Intelligent Contract plus a web app for running fair community giveaways.
The host writes the rules once. GenLayer's AI validators open every participant's proof link and judge it against those rules. When entries close, winners are drawn from a SHA-256 seed of all valid entries — and anyone can re-check that draw in their own browser.

- **Live app:** https://gurusankar55.github.io/GiveawayProof/
- **Contract (GenLayer Studio):** [`0x00D0C78A636202979561e69D848d79A492ffA36b`](https://explorer-studio.genlayer.com/address/0x00D0C78A636202979561e69D848d79A492ffA36b)
- **Network:** GenLayer Studio (studionet)

---

## The problem

Giveaways on X, Discord and Telegram are everywhere in crypto, and so are the complaints:

- "The winner is the host's friend."
- "I followed every rule and was never counted."
- "Nobody can see how the winner was picked."

Today the host is judge, jury and random-number generator. Participants just have to trust them.

## The solution

GiveawayProof removes the host from the two decisions that can be abused:

| Decision | Before | With GiveawayProof |
|---|---|---|
| Is this entry valid? | Host decides privately | GenLayer AI validators read the proof page and must reach consensus |
| Who wins? | Host picks | Deterministic draw from a SHA-256 seed of all valid entries, stored on-chain |
| Can anyone check? | No | Yes — the web app recomputes the draw and shows ✓ or ✗ against the on-chain result |

The host can still create the giveaway and decide **when** to close it — but not **who** wins.

---

## How it works

1. **Host posts the rules** — title, prize, number of winners (1–50) and the rules in plain language.
2. **People enter with proof** — each wallet enters once, with a prize address and a public proof link.
3. **AI validators judge** — the contract fetches the proof page with `gl.nondet.web.render`, asks the LLM whether it satisfies the rules, and validators must agree on the exact verdict (`gl.eq_principle.strict_eq`). Each entry is stored as `VALID`, `INVALID` or `UNREADABLE`.
4. **Fair draw** — the host calls `close_and_pick`. The contract builds a seed from every valid entry and picks winners from it. The seed and winners are stored on-chain.

### Why this needs GenLayer

A normal smart contract cannot open a web page or understand a rule like *"must quote our announcement and tag two friends"*. GenLayer's Intelligent Contracts can read the web and reason about natural language, while validator consensus makes sure no single node decides the verdict.

---

## The verifiable draw

The draw uses only data that is already public on the contract:

```
seed   = sha256( id + "|" + "entrant1:wallet1|entrant2:wallet2|…" )   # valid entries, in entry order
pick k = sha256( seed + ":" + k )  mod  (remaining pool size)        # k = 0, 1, 2 …
```

Each picked entry is removed from the pool before the next pick, so nobody wins twice.

The web app repeats exactly this math with the browser's Web Crypto API and prints a **Draw Receipt**. If the host (or anyone) had changed a single winner, the receipt would show **✗ does not match**.

---

## Contract methods

### Write

| Method | Who | What it does |
|---|---|---|
| `create_giveaway(title, rules, prize, winners_count)` | anyone (becomes host) | Creates a giveaway, returns its id |
| `submit_entry(giveaway_id, wallet, proof_url)` | anyone, once per giveaway | AI-checks the proof link against the rules and stores the verdict |
| `close_and_pick(giveaway_id)` | host only | Closes entries and draws the winners |

### Read

| Method | Returns |
|---|---|
| `get_giveaway_count()` | Number of giveaways |
| `get_giveaway(giveaway_id)` | Giveaway JSON (rules, status, counts, winners, seed) |
| `get_entries(giveaway_id)` | All entries with their AI verdict and reason |
| `get_all_giveaways()` | Summary of the latest 50 giveaways |

### Safety rules in the contract

- One entry per wallet per giveaway
- Entries are refused after the giveaway is closed
- Only the host can close, and only once
- Proof links must start with `http://` or `https://`
- Winners count is limited to 1–50

---

## Tested on GenLayer Studio

| Step | Result |
|---|---|
| `create_giveaway("GenLayer Community Giveaway", …, "10 USDT", 1)` | Finalized — giveaway `#1` |
| `submit_entry("1", "0x1111…1111", "https://docs.genlayer.com")` | Finalized — AI verdict **VALID** |
| `close_and_pick("1")` | Finalized — status `closed`, 1 winner, seed `1b4942e2…eb1d1` |
| Browser recompute of the draw | Seed and winner match the on-chain result ✓ |

---

## Web app

A single `index.html` — no build step.

- Wallet choice list (MetaMask, Rabby and other EIP-6963 wallets); switches to studionet automatically
- Giveaway list shown as raffle tickets, with Open / Drawn filters
- Giveaway page with rules, entry form, live progress while validators judge, and every entry's verdict
- Host-only **Close entries and draw** button
- **Draw Receipt** that re-checks the winners in the browser
- Shareable links to each giveaway (`#g-1`)
- Works on phones

Built with [genlayer-js](https://github.com/genlayerlabs/genlayer-js) loaded from a CDN.

### Run it locally

Open `index.html` through any static server, for example:

```bash
python -m http.server 8000
```

then visit `http://localhost:8000`.

---

## Files

| File | Description |
|---|---|
| `giveaway_proof.py` | The GenLayer Intelligent Contract |
| `index.html` | The web app |
| `README.md` | This document |

## Deploy your own copy

1. Open [GenLayer Studio](https://studio.genlayer.com) and create a new contract with the contents of `giveaway_proof.py`.
2. Deploy it (the constructor takes no arguments).
3. Replace the `CONTRACT` address near the top of the script in `index.html` with your new address.

---

## Limitations and next steps

- Proof pages must be **public**. Pages behind a login wall (some X/Twitter views) may come back as `UNREADABLE`.
- The draw is deterministic and auditable, but a very motivated entrant could try to time their entry to influence the seed. A future version can mix in a seed committed by the host before entries open.
- Prizes are paid by the host off-chain today. A next step is an escrow mode where the prize is locked in the contract and released to winners automatically.

---

## Author

Built by **[gurusankar55](https://github.com/gurusankar55)** for the GenLayer Builders Portal.
