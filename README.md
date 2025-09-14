# talk-to-brief
🎤 Talk-to-Brief: From 30-Min Audio → 1-Page Insights in Minutes


# 🎤 Talk-to-Brief  
From 30-Min Conference Audio → 1-Page Brief with Questions & Highlights in Minutes  

**Goal:** Walk out of any talk with:  
- A **3-line Approach Script** to talk to the speaker  
- **5 Timestamped Questions** that show you actually listened  
- **8–12 Key Highlights** with `[mm:ss]` references  
- **Claims / Assumptions / Trade-offs** to guide real conversation  

All in **≤7 min** after the talk ends.  

---

## 🚀 How It Works (80/20 Flow)
1. **Record** 30 min audio → `talk.wav` (any recorder works)  
2. **Transcribe locally** with [faster-whisper](https://github.com/SYSTRAN/faster-whisper) → `transcript.txt + timestamps`  
3. **Analyze with GPT-5** in two passes:
   - **Pass 1:** Run per-chunk prompt → 4 partial outputs  
   - **Pass 2:** Merge prompt → single `brief.md`  
4. **Skim Brief.md** → Walk up to the speaker with context + sharp questions  

---

## 📂 Repo Structure
```

talk-to-brief/
├── record.sh             # optional: 30-min recorder script
├── transcribe.py         # audio → transcript + timestamps
├── analyze\_chunk.py      # per-chunk GPT-5 call
├── merge\_brief.py        # final merge GPT-5 call
├── prompts/
│   ├── per\_chunk.md      # per-chunk prompt (Tier-1 only)
│   └── merge.md          # merge prompt
├── outputs/
│   ├── transcript.txt
│   ├── chunks/
│   ├── partials/
│   └── brief.md
└── README.md

````

---

## 🛠 Setup
```bash
git clone https://github.com/yourname/talk-to-brief.git
cd talk-to-brief
pip install -r requirements.txt
````

* Get a [GPT-5 API key](#) and set it as `OPENAI_API_KEY`.
* Install `faster-whisper` for transcription.

---

## 🏃 Usage

```bash
# 1. Record 30 min talk (or use any WAV recorder)
bash record.sh

# 2. Transcribe
python transcribe.py talk.wav

# 3. Analyze chunks in parallel
python analyze_chunk.py

# 4. Merge into final brief
python merge_brief.py

# 5. Open the brief
open outputs/brief.md
```

---

## 🎯 Output Example

```
# Approach Script
"At 12:47 you mentioned cold vector latency. I'd love to hear why PQ over OPQ was the final call — we hit similar issues in our own pipelines."

# Five High-Signal Questions
1. [12:47] Why PQ vs OPQ for latency optimization?  
2. [18:05] How did you balance cost vs recall here?  
...

# Timeline Highlights
- [05:20] Introduced hybrid index approach
- [12:47] Latency benchmarks on cold vectors
...

# Key Claims / Assumptions / Trade-offs
Claims:
- Hybrid indexing reduced cold start latency by 40%
Assumptions:
- NVMe storage cost is acceptable at this scale
Trade-offs:
- Higher indexing latency during ingestion
```

---

## 🧠 Why This Matters

You get **specific, timestamped context** + **conversation-ready questions** without sifting through 30 min of audio manually.

Perfect for:

* Conferences
* Guest lectures
* Tech meetups

---

## 📜 License

MIT
