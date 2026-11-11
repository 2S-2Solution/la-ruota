### 6. Flash attention — PRONTA DA COLLEGARE, anche D=256 e GQA (`flash_gfx906\fa_gfx906.py`, stato in `STATO.md`)
Kernel compilati a runtime con hipRTC: nessuna ricompilazione della ruota per provarla.

**Interfaccia**
```python
import fa_gfx906 as fa
o, lse2 = fa.avanti(q, k, v, causale=False, scala=None, dropout=0.0, seme=0)
dq, dk, dv = fa.indietro(do, q, k, v, o, lse2, causale=False, scala=None, dropout=0.0, seme=0)
o = fa.attenzione(q, k, v, causale=False, scala=None, dropout=0.0, seme=None)   # autograd
```
- q `[B, H, S_q, D]`, k e v `[B, H_kv, S_k, D]`, **fp16** (bf16 no: gfx906 non ha istruzioni bf16),
  **D ∈ {64, 128, 256}**; **stride qualunque** con l'ultima dimensione contigua (righe non
  allineate a 16 byte → copia interna); **S_q ≠ S_k** ammesso.
- **GQA nativo** (20 ott): H multiplo di H_kv, la testa di query h legge la testa h // (H/H_kv),
  come `enable_gqa=True`. **Non ripetete K/V**: dk e dv tornano con la forma di k e v, sommati sulle
  teste del gruppo dentro il kernel. Qwen3.5-4B: 16 teste di query, 4 di K/V, D=256.
- `causale`: maschera **in alto a sinistra**, come `scaled_dot_product_attention` (chiave ≤ query).
- `scala`: default `D ** -0.5`.
- `dropout`: maschera da un hash deterministico di (seme, testa di query, query, chiave), uguale
  nell'avanti e nell'indietro; `seme=None` in `attenzione` ne estrae uno dal generatore di
  torch (riproducibile con `manual_seed`). NON è la stessa sequenza casuale di PyTorch.
  `fa.maschera_dropout(B, H, S_q, S_k, p, seme)` la ricalcola in torch.
- `lse2`: fp32 `[B, H, S_q]`, logsumexp in **base 2** della scala per log2(e); naturale =
  `lse2 * ln 2` (è quello che `_scaled_dot_product_flash_attention` restituisce come logsumexp).
- Uscita e dq contigui `[B, H, S_q, D]`, dk e dv `[B, H_kv, S_k, D]`.
- Non supportati: `attn_mask` arbitraria, D fuori da {64, 128, 256}.

**Correttezza** (`banco_fa.py correttezza`, 33/33): S_q ≠ S_k nei due versi, stride da layout
`[B, S, H, D]`, dropout 0,1/0,2/0,5 contro la stessa maschera, causale, a D=64/128 e gli stessi
casi a D=256, più GQA (H8/2, MQA H4/1 con dropout e stride, H16/4 come Qwen) per ogni D. Errore
assoluto su uscita e gradienti mai sopra quello del calcolo fp16 diretto. ⚠️ Se rifate il confronto
su un solo seme, il massimo è rumoroso (a volte scavalca di poco, anche a D=128): su 8 semi l'errore
quadratico della fa è 0,5-0,65 volte quello di math (`prova_errore.py`).

**Tempi** (B1 H16, avanti / avanti+indietro, contro il percorso math di oggi):
S1024 D64 1,96x / 1,72x · S4096 D64 causale 5,30x / 2,36x · S1024 D128 1,49x / 1,19x ·
S2048 D128 causale 4,35x / 1,84x · S4096 D128 causale 4,45x / 2,00x.
**D=256 causale**: S256 2,38x / 1,48x · S1024 2,15x / 1,90x · S2048 2,49x / 1,54x ·
S4096 2,58x / 1,58x; con GQA H16/4 (math con K/V ripetute) S1024 2,31x / 1,82x · S4096 2,62x / 1,59x.
⚠️ D=256 **non causale** lungo: avanti 1,13x ma avanti+indietro **0,77x** a S4096 (math a D=256 è
quasi tutto GEMM di rocBLAS). Per Qwen, che è causale, non conta.

**Memoria O(S)**: avanti+indietro causale, picco in più: S4096 D128 160 MB contro 4256; S4096 D256
224 MB contro 4320; **S8192 D256 H16/4 448 MB contro 16.832** (il percorso math non sta più sulla
scheda).

**Cosa resta a te**: collegarla a `scaled_dot_product_attention` (fp16, D 64/128/256, senza
`attn_mask`, con `enable_gqa` passando K/V senza ripeterle), e il collaudo su un addestramento vero
(LoRA Qwen3.5-4B) contro il percorso math.
