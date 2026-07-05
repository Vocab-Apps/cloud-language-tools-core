# Forvo Chinese dialect voices: actual API control (correction to the prior issue file)

## TL;DR

The companion file `20260705_FORVO_CHINESE_ISSUE.md` states that "Forvo's API itself has no
sub-language/dialect parameter — for it, `zh` is a single bucket that mixes Mandarin, Min Nan,
Wu, Hakka, etc."

**This is incorrect.** Forvo's `word-pronunciations` endpoint accepts a `language` parameter
that can be set to *many* distinct Chinese-variety codes, not just `zh`. The bug is on our side:
`cloudlanguagetools/forvo.py` (`get_voices_for_language_entry`) hardcodes
`voice_key['language_code'] = language['code']` from the language-list response and never
overrides it per `audio_language`, so every Chinese-variety voice ends up with `language_code='zh'`.

Most of the affected dialect voices are **fixable** by mapping them to the correct Forvo language
code. A minority (`zh_CN_henan`, `zh_CN_shaanxi`, `zh_CN_gansu`) have no dedicated Forvo code and
should be collapsed.

## What the Forvo API actually lets us control

The `word-pronunciations` endpoint
(https://api.forvo.com/documentation/word-pronunciations/) accepts these optional filters:

| Parameter | What it filters | Granularity |
|---|---|---|
| `language` | Forvo's own language taxonomy code | **Dialect-level** (see table below) |
| `country` | ISO 3166-1 Alpha-3 of the *contributor's* country | Country only (CHN/TWN/HKG) — **no sub-national** |
| `username` | A specific contributor | Per-user |
| `sex` | `m` / `f` | Gender |
| `rate` | Minimum rating threshold | Integer |
| `order` | `date-desc/asc`, `rate-desc/asc` | Sort |
| `limit` | Max items returned | Integer |
| `group-in-languages` | Group results by language | bool |

The lever that matters is `language`. `country` cannot help with the Chinese-dialect problem
(it only knows CHN/TWN/HKG, so it cannot distinguish Liaoning from Sichuan).

## Forvo's Chinese-variety language codes

Source: cached Forvo `language-list` response at `temp_data_files/forvo_language_list`
(retrieved via the `language-list` action documented at
https://api.forvo.com/documentation/language-list/). Forvo exposes distinct codes for far
more than just `zh` / `yue`:

| Forvo code | Forvo name | Our `AudioLanguage` that should map to it | Status |
|---|---|---|---|
| `zh` | Mandarin Chinese | `zh_CN` | Already correct |
| `yue` | Cantonese | `yue_CN`, `zh_HK` | Already correct |
| `nan` | Min Nan | `nan_CN` | **Fixable** |
| `wuu` | Wu Chinese | `wuu_CN` | **Fixable** |
| `jliu` | Jiaoliao Mandarin (Shandong–Liaoning branch) | `zh_CN_liaoning` | **Fixable** |
| `jlua` | Jilu Mandarin | `zh_CN_shandong` | **Fixable** |
| `juai` | Lower Yangtze Mandarin (= Jianghuai) | `zh_CN_anhui` | **Fixable** |
| `xghu` | Southwestern Mandarin | `zh_CN_sichuan` | **Fixable** |
| `xghu` | Southwestern Mandarin | `zh_CN_guangxi` | Fixable (accept the grouping) or collapse |
| `xghu` | Southwestern Mandarin | `zh_CN_hunan` | Fixable (accept the grouping) or collapse |
| `tisa` | Toisanese Cantonese | — | Available if we want it |
| `cdo` | Min Dong | — | Available if we want it |
| `jusi` | Shanghainese | — | Available if we want it |
| `taiu` | Taihu Wu | — | Available if we want it |
| `gan` | Gan Chinese | — | Available if we want it |
| `hak` | Hakka | — | Available if we want it |
| `cjy` | Jin Chinese | — | Available if we want it |
| `ltc` | Middle Chinese | — | Available if we want it |
| `plig` | Changzhou | — | Available if we want it |
| `fzho` | Fuzhou | — | Available if we want it |
| `hsn` | Xiang Chinese | `zh_CN_hunan` (alternative — Xiang is its own branch, not Mandarin) | Optional |

For completeness, the Forvo codes that do **not** exist as separate entries and therefore
cannot be targeted via the `language` parameter:

| Our `AudioLanguage` | Reason no Forvo code exists |
|---|---|
| `zh_CN_henan` | Zhongyuan Mandarin — Forvo only has `zh` for this branch |
| `zh_CN_shaanxi` | Zhongyuan Mandarin — same |
| `zh_CN_gansu` | Lanyin Mandarin — same |

## Root cause (corrected)

The bug is in `cloudlanguagetools/forvo.py`, `get_voices_for_language_entry` (lines ~290–318):

```python
language_code = language['code']               # <-- always 'zh' for Mandarin Chinese
...
for audio_language in audio_language_list:
    country_code = self.get_country_code(audio_language)
    voices.append(ForvoVoice(language_code, country_code, audio_language, gender))
                            ^^^^^^^^^^^^^^
                            # passed verbatim to voice_key['language_code']
```

The `language_code` is taken once from the language-list entry and reused for every
`audio_language` in that bucket. For Mandarin Chinese the bucket contains `zh_CN`, `nan_CN`,
`wuu_CN`, `zh_CN_liaoning`, `zh_CN_henan`, … and they all inherit `language_code='zh'`.

`get_tts_audio` (lines 73–92) then builds the URL purely from `voice_key`:

```
.../word/<text>/language/zh/sex/m/order/rate-desc/limit/1/country/CHN
```

So every dialect voice hits the same `language/zh/country/CHN` bucket, and Forvo returns
whichever recording is top-rated there (typically Standard Mandarin, but Min Nan / Wu / Hakka
recordings tagged under `zh` by contributors show up in the same bucket too — exactly the
"Northeastern Mandarin returns Minnan audio" symptom in the issue file).

The dialect signal in `audio_languages` is never transmitted to Forvo because the
`language_code` field that *is* transmitted is wrong for every non-Mandarin variety.

## What level of control we have, by dialect

| Dialect voice | Can we target it on the Forvo API? | How |
|---|---|---|
| `nan_CN` (Minnan) | **Yes** | `language/nan` |
| `wuu_CN` (Wu) | **Yes** | `language/wuu` |
| `zh_CN_liaoning` (Northeastern Mandarin) | **Yes** | `language/jliu` (Jiaoliao Mandarin) |
| `zh_CN_shandong` (Jilu Mandarin) | **Yes** | `language/jlua` |
| `zh_CN_anhui` (Jianghuai Mandarin) | **Yes** | `language/juai` (Lower Yangtze Mandarin) |
| `zh_CN_sichuan` (Southwestern Mandarin) | **Yes** | `language/xghu` |
| `zh_CN_guangxi` (Guangxi accent Mandarin) | **Yes, with caveats** | `language/xghu` (lumps Guangxi in with all Southwestern Mandarin) |
| `zh_CN_hunan` (Hunan accent Mandarin) | **Yes, with caveats** | `language/xghu` (Mandarin-accented) or `language/hsn` (true Xiang Chinese) — pick one |
| `zh_CN_henan` (Zhongyuan Mandarin) | **No** | Forvo only has `zh` for this branch |
| `zh_CN_shaanxi` (Zhongyuan Mandarin) | **No** | Forvo only has `zh` for this branch |
| `zh_CN_gansu` (Lanyin Mandarin) | **No** | Forvo only has `zh` for this branch |

## Recommended fix (correcting the prior recommendation)

The issue file recommends "Option 1 — collapse all dialect voices" because it assumes the API
has no dialect parameter. Since that assumption is wrong, the correct fix is a hybrid:

### 1. Add an `audio_language → forvo_language_code` override map

In `cloudlanguagetools/forvo.py`, add something like:

```python
AUDIO_LANGUAGE_TO_FORVO_CODE = {
    AudioLanguage.nan_CN:            'nan',
    AudioLanguage.wuu_CN:            'wuu',
    AudioLanguage.zh_CN_liaoning:    'jliu',
    AudioLanguage.zh_CN_shandong:    'jlua',
    AudioLanguage.zh_CN_anhui:       'juai',
    AudioLanguage.zh_CN_sichuan:     'xghu',
    # Optional / needs a product decision:
    # AudioLanguage.zh_CN_guangxi:     'xghu',
    # AudioLanguage.zh_CN_hunan:       'xghu',   # or 'hsn' for true Xiang
}
```

### 2. Apply it in `get_voices_for_language_entry`

When constructing each `ForvoVoice`, look up the override for the current `audio_language`
and use it as the `language_code` instead of the bucket-level `language['code']`:

```python
for audio_language in audio_language_list:
    country_code = self.get_country_code(audio_language)
    language_code = AUDIO_LANGUAGE_TO_FORVO_CODE.get(
        audio_language, language['code']
    )
    voices.append(ForvoVoice(language_code, country_code, audio_language, gender))
```

No change to `get_tts_audio` is required — it already reads `voice_key['language_code']`
and passes it as the `language/<code>` URL segment, so once the voice key carries the right
code the request will target the right Forvo bucket.

### 3. Collapse the un-targetable voices

Remove the voices for `AudioLanguage` values with no dedicated Forvo code:

- `zh_CN_henan`
- `zh_CN_shaanxi`
- `zh_CN_gansu`

(And optionally `zh_CN_guangxi` / `zh_CN_hunan` if you decide not to lump them under
`xghu` Southwestern Mandarin.)

These voices never worked and cannot work via the `language` parameter; they should not be
advertised. If `username`-based targeting (the issue file's "Option 3") is ever curated for
these specific branches, they could be reintroduced with a `preferred_user` pin.

## Why the issue file's "Option 2" is unnecessary

"Option 2 — post-filter Forvo results by dialect metadata" proposes calling Forvo without
`limit/1`, inspecting `items[*].country` / `city`, and selecting the first matching item.

This is unnecessary because the `language` parameter already gives server-side dialect
filtering for every variety Forvo recognises — we don't need to over-fetch and filter
client-side. It's also unworkable for the cases the issue file worried about: Forvo's `items`
only carry `country` (e.g. `CHN`) and a free-text `city`, neither of which reliably identifies
dialect, so post-filtering would be noisier than just using the right `language` code in the
first place.

## Files to change

- `cloudlanguagetools/forvo.py` — add the override map; modify
  `get_voices_for_language_entry` (lines ~290–318) to consult it.
- `hypertts_addon/services/voicelist.py` — the Forvo block (~lines 16312–21763): regenerate
  so the `zh-CHN` dialect voices now carry distinct `voice_key['language_code']` values, and
  drop the collapsed (`zh_CN_henan` / `zh_CN_shaanxi` / `zh_CN_gansu`) entries. If the
  voicelist is generated from `get_tts_voice_list_v3()`, this happens automatically once the
  core change is in.
- `tests/test_tts_services/test_forvo.py` and `tests/test_audio.py` — add a regression test
  asserting that two distinct `audio_languages` for the same service produce different
  Forvo URLs (e.g. `nan_CN` → `language/nan`, `zh_CN` → `language/zh`).

## Open product decision

For `zh_CN_guangxi` and `zh_CN_hunan`:

- Route both to `language/xghu` (Southwestern Mandarin) — matches "Mandarin with a regional
  accent" framing but lumps Guangxi and Hunan Mandarin together with Sichuanese.
- Route `zh_CN_hunan` to `language/hsn` (Xiang Chinese) — linguistically a different branch
  from "Hunan-accented Mandarin", but is the native language of much of Hunan.
- Collapse both if neither mapping is acceptable.

This is a linguistic/product call, not a technical one.

## References

- Forvo `word-pronunciations` API: https://api.forvo.com/documentation/word-pronunciations/
- Forvo `language-list` API: https://api.forvo.com/documentation/language-list/
- Cached Forvo language list: `temp_data_files/forvo_language_list`
- Current service code: `cloudlanguagetools/forvo.py:73-92` (`get_tts_audio`) and
  `cloudlanguagetools/forvo.py:290-318` (`get_voices_for_language_entry`)
- Prior (incorrect) analysis: `20260705_FORVO_CHINESE_ISSUE.md`
