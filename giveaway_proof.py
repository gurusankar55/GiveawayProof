# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

import json
import hashlib


class GiveawayProof(gl.Contract):
    giveaway_count: u256
    giveaways: TreeMap[str, str]
    entries: TreeMap[str, str]
    entered: TreeMap[str, str]

    def __init__(self):
        self.giveaway_count = 0

    # ---------------- helpers ----------------

    def _load(self, giveaway_id: str) -> dict:
        gid = giveaway_id.strip()
        if gid not in self.giveaways:
            raise Exception("Giveaway not found")
        return json.loads(self.giveaways[gid])

    # ---------------- write methods ----------------

    @gl.public.write
    def create_giveaway(self, title: str, rules: str, prize: str, winners_count: int) -> str:
        if len(title.strip()) == 0:
            raise Exception("Title is required")
        if len(rules.strip()) == 0:
            raise Exception("Rules are required")
        if winners_count < 1 or winners_count > 50:
            raise Exception("Winners count must be between 1 and 50")

        new_id = int(self.giveaway_count) + 1
        self.giveaway_count = new_id
        gid = str(new_id)

        data = {
            "id": gid,
            "host": gl.message.sender_address.as_hex,
            "title": title.strip(),
            "rules": rules.strip(),
            "prize": prize.strip(),
            "winners_count": winners_count,
            "status": "open",
            "entry_count": 0,
            "valid_count": 0,
            "winners": [],
            "seed": "",
        }
        self.giveaways[gid] = json.dumps(data)
        return gid

    @gl.public.write
    def submit_entry(self, giveaway_id: str, wallet: str, proof_url: str) -> str:
        data = self._load(giveaway_id)
        gid = data["id"]

        if data["status"] != "open":
            raise Exception("Giveaway is closed")

        w = wallet.strip()
        url = proof_url.strip()
        if len(w) == 0:
            raise Exception("Wallet is required")
        if not (url.startswith("http://") or url.startswith("https://")):
            raise Exception("Proof link must start with http:// or https://")

        sender = gl.message.sender_address.as_hex
        key = gid + "|" + sender.lower()
        if key in self.entered:
            raise Exception("You already entered this giveaway")

        rules = data["rules"]

        def check_entry() -> str:
            try:
                page = gl.nondet.web.render(url, mode="text")
            except Exception:
                return "UNREADABLE"
            text = str(page)[:5000]
            if len(text.strip()) < 20:
                return "UNREADABLE"
            prompt = (
                "You are a fair judge for a crypto giveaway.\n"
                "GIVEAWAY RULES:\n" + rules + "\n\n"
                "PARTICIPANT WALLET: " + w + "\n\n"
                "CONTENT OF THE PARTICIPANT'S PROOF PAGE:\n" + text + "\n\n"
                "Does this proof page show that the participant followed the giveaway rules? "
                "Answer with exactly one word: VALID or INVALID."
            )
            answer = str(gl.nondet.exec_prompt(prompt)).strip().upper()
            if "INVALID" in answer:
                return "INVALID"
            if "VALID" in answer:
                return "VALID"
            return "INVALID"

        verdict = gl.eq_principle.strict_eq(check_entry)

        if verdict == "VALID":
            reason = "Proof matches the giveaway rules"
        elif verdict == "UNREADABLE":
            reason = "Proof page could not be read"
        else:
            reason = "Proof does not match the giveaway rules"

        index = int(data["entry_count"]) + 1
        entry = {
            "index": index,
            "giveaway_id": gid,
            "entrant": sender,
            "wallet": w,
            "proof_url": url,
            "verdict": verdict,
            "reason": reason,
        }
        self.entries[gid + ":" + str(index)] = json.dumps(entry)
        self.entered[key] = "1"

        data["entry_count"] = index
        if verdict == "VALID":
            data["valid_count"] = int(data["valid_count"]) + 1
        self.giveaways[gid] = json.dumps(data)
        return verdict

    @gl.public.write
    def close_and_pick(self, giveaway_id: str) -> str:
        data = self._load(giveaway_id)
        gid = data["id"]

        if data["status"] != "open":
            raise Exception("Giveaway is already closed")
        if gl.message.sender_address.as_hex.lower() != data["host"].lower():
            raise Exception("Only the host can close this giveaway")

        valid = []
        for i in range(1, int(data["entry_count"]) + 1):
            e = json.loads(self.entries[gid + ":" + str(i)])
            if e["verdict"] == "VALID":
                valid.append(e)

        seed_src = gid + "|" + "|".join(e["entrant"] + ":" + e["wallet"] for e in valid)
        seed = hashlib.sha256(seed_src.encode("utf-8")).hexdigest()

        pool = list(valid)
        winners = []
        n = min(int(data["winners_count"]), len(pool))
        for k in range(n):
            h = hashlib.sha256((seed + ":" + str(k)).encode("utf-8")).hexdigest()
            idx = int(h, 16) % len(pool)
            p = pool.pop(idx)
            winners.append({
                "entrant": p["entrant"],
                "wallet": p["wallet"],
                "proof_url": p["proof_url"],
            })

        data["status"] = "closed"
        data["winners"] = winners
        data["seed"] = seed
        self.giveaways[gid] = json.dumps(data)
        return json.dumps(winners)

    # ---------------- view methods ----------------

    @gl.public.view
    def get_giveaway_count(self) -> int:
        return int(self.giveaway_count)

    @gl.public.view
    def get_giveaway(self, giveaway_id: str) -> str:
        return json.dumps(self._load(giveaway_id))

    @gl.public.view
    def get_entries(self, giveaway_id: str) -> str:
        data = self._load(giveaway_id)
        gid = data["id"]
        result = []
        for i in range(1, int(data["entry_count"]) + 1):
            result.append(json.loads(self.entries[gid + ":" + str(i)]))
        return json.dumps(result)

    @gl.public.view
    def get_all_giveaways(self) -> str:
        total = int(self.giveaway_count)
        result = []
        start = max(1, total - 49)
        for i in range(total, start - 1, -1):
            d = json.loads(self.giveaways[str(i)])
            result.append({
                "id": d["id"],
                "title": d["title"],
                "prize": d["prize"],
                "status": d["status"],
                "entry_count": d["entry_count"],
                "valid_count": d["valid_count"],
                "winners_count": d["winners_count"],
            })
        return json.dumps(result)
