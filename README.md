# 🎟️ GiveawayProof

**Crypto giveaways the host can't rig — and can't skip paying.**

GiveawayProof is a GenLayer Intelligent Contract plus a web app for running fair community giveaways.
The host locks the GEN prize inside the contract when the giveaway is created. GenLayer's AI validators judge every entry's proof link against the rules. Entries close at a time fixed on-chain, the winners are drawn from a public **drand** randomness round that is only published *after* closing, and the contract pays the winners itself.

- **Live app:** https://gurusankar55.github.io/GiveawayProof/
- **Contract (GenLayer Studio):** [`0x58dd856cf9E0cd2357218321768a27b99F618712`](https://explorer-studio.genlayer.com/address/0x58dd856cf9E0cd2357218321768a27b99F618712)
- **Network:** GenLayer Studio (studionet)

---

## The problem

Giveaways on X, Discord and Telegram are everywhere in crypto, and so are the complaints:

- "The winner is the host's friend."
- "The host closed it right when his friend was winning."
- "I won and never got paid."

Today the host is judge, timekeeper, random-number generator and bank. Participants just have to trust them.

## The solution — v2

| Risk | How GiveawayProof v2 removes it |
|---|---|
| Host never pays the prize | `create_giveaway` is **payable**: the GEN prize is sent with the transaction and held by the contract. `draw` sends it to the winners automatically. |
| Host closes early/late to suit a friend | The closing time is set **once, at creation** (`close_at`). There is no close function. Nobody can move it. |
| Host predicts the winner before closing | The draw uses drand round `draw_round`, which is fixed at creation and published **after** `close_at`. Before closing, nobody — host included — can know its value, so nobody can know the winner. |
| Host times the draw | **Anyone** can call `draw` after closing. Because the round is fixed, the result is identical whoever calls it and whenever. |
| Draw never runs | If the draw hasn't run 24 h after closing, anyone can call `split_to_entrants`: the prize is split equally between **all valid entrants**. The host gets nothing back. |
| Host grabs the prize back | `cancel_giveaway` works **only while there are zero entries**. Once someone enters, the prize can only go to entrants. |
| Host enters with own wallet / reused proofs | The host can't enter. One entry per sender, per prize wallet and per proof link. |
| Entry is judged by one person | GenLayer validators open the proof page and must reach the same verdict (`strict_eq`). |

The only case where the prize returns to the host is when **no entry passes the AI check** (nobody to pay) or the host cancels before anyone entered.

---

## How it works

1. **Host locks the prize** — `create_giveaway(title, rules, winners_count, entry_minutes)` with the GEN prize as the transaction value. The contract stores `close_at`, `draw_round` and `draw_deadline`.
2. **People enter with proof** — `submit_entry(giveaway_id, wallet, proof_url)` until `close_at`. Validators fetch the page with `gl.nondet.web.render`, ask the LLM whether it follows the rules (page content is treated as data, not instructions) and must agree on `VALID`, `INVALID` or `UNREADABLE`.
3. **Anyone runs the draw** — after closing, `draw(giveaway_id)` makes validators read drand round `draw_round` (`api.drand.sh`, fallback `drand.cloudflare.com`) and agree on its randomness.
4. **Contract pays** — winners are picked and the prize is split equally (leftover wei to winner 1) and transferred to each winner's prize wallet in the same transaction.

### Why this needs GenLayer

A normal smart contract cannot open a web page, understand a rule like *"must quote our announcement and tag two friends"*, or read a public randomness beacon. GenLayer's Intelligent Contracts can do all three, with validator consensus making sure no single node decides.

---

## The verifiable draw

```
draw_round = first drand quicknet round published after close_at
randomness = drand quicknet round <draw_round>            # public, 3-second beacon
seed       = sha256( randomness + "|" + id + "|" + "entrant1:wallet1|entrant2:wallet2|…" )   # valid entries in entry order
pick k     = sha256( seed + ":" + k )  mod  (remaining pool size)                           # k = 0, 1, 2 …
```

Each picked entry is removed from the pool before the next pick, so nobody wins twice.

The web app fetches the same drand round directly from drand, repeats the math with the browser's Web Crypto API and prints a **Draw Receipt** that shows ✓ only if the randomness, the seed and every winner match the on-chain result.

drand quicknet: chain `52db9ba70e0cc0f6eaf7803dd07447a1f5477735fd3f661792ba94600c84e971`, genesis `1692803367`, period 3 s.

---

## Contract methods

### Write

| Method | Who | What it does |
|---|---|---|
| `create_giveaway(title, rules, winners_count, entry_minutes)` **payable** | anyone (becomes host) | Locks the sent GEN as the prize, fixes `close_at` (5 min – 30 days) and `draw_round` |
| `submit_entry(giveaway_id, wallet, proof_url)` | anyone except the host, before `close_at` | AI-checks the proof link against the rules and stores the verdict |
| `draw(giveaway_id)` | anyone, after `close_at` | Reads the drand round, picks winners, pays them |
| `split_to_entrants(giveaway_id)` | anyone, 24 h after `close_at` if not drawn | Splits the prize equally between all valid entrants |
| `cancel_giveaway(giveaway_id)` | host, only with 0 entries | Refunds the prize to the host |

### Read

| Method | Returns |
|---|---|
| `get_config()` | drand settings and limits |
| `get_giveaway_count()` | Number of giveaways |
| `get_giveaway(giveaway_id)` | Giveaway JSON (rules, prize, times, drand round, randomness, seed, winners, payouts) |
| `get_entries(giveaway_id)` | All entries with their AI verdict and reason |
| `get_all_giveaways()` | Summary of the latest 50 giveaways |

Amounts are stored as wei strings (`prize_wei`, `amount_wei`) so JavaScript never loses precision.

### Limits

- 1–50 winners, up to 200 entries per giveaway
- Entry window 5 minutes to 30 days
- Prize must be at least 1 wei per winner
- Proof links must start with `http://` or `https://`; prize wallets must be `0x` addresses

---

## Web app

A single `index.html` — no build step.

- Wallet choice list (MetaMask, Rabby and other EIP-6963 wallets); switches to studionet automatically
- Create form: GEN prize to lock, fixed entry window, winners count
- Giveaway list as raffle tickets with locked prize, countdown and status (Open / Ready to draw / Prize paid / Split / Cancelled)
- Giveaway page with rules, entry form, live countdown, **Draw and pay** button for anyone after closing, safety split after 24 h, host cancel while empty
- Payments table showing every transfer the contract made
- **Draw Receipt** that re-checks drand, the seed and the winners in the browser
- Shareable links to each giveaway (`#g-1`), works on phones

Built with [genlayer-js](https://github.com/genlayerlabs/genlayer-js) loaded from a CDN.

### Run it locally

```bash
python -m http.server 8000
```

then visit `http://localhost:8000`.

## Deploy your own copy

1. Open [GenLayer Studio](https://studio.genlayer.com) and create a new contract with `giveaway_proof.py`.
2. Deploy it (the constructor takes no arguments).
3. Put the new address in the `CONTRACT` constant near the top of the script in `index.html`.

---

## Trust model and limitations

- Randomness comes from drand (League of Entropy). Validators fetch the round and must agree on it; anyone can compare it with drand directly from the receipt.
- Proof pages must be **public**. Pages behind a login wall may come back as `UNREADABLE`.
- Prizes are in GEN (the native token). Token prizes (ERC-20) are a possible next step.

## Author

Built by **[gurusankar55](https://github.com/gurusankar55)** for the GenLayer Builders Portal.
