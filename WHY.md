# Why This Exists

## The Problem

You use AI assistants every day — ChatGPT, Claude, Copilot, Gemini. You write code with them, draft emails, research topics, brainstorm ideas. It *feels* like you're getting more done.

But how much more? You have no idea.

- How many hours did AI save you this week?
- Which tasks benefit most from AI — coding? writing? research?
- Is your $20/month subscription actually worth it?
- Are you getting better at using AI over time, or just chatting more?

**You can't improve what you don't measure.**

## What's Missing

Time-tracking tools like Toggl or RescueTime track *how long you work*, but they can't tell you *how much time AI saved you*. AI platforms show you token usage and conversation counts, but that says nothing about value.

The missing piece: something that looks at what you did with AI and estimates how long it would have taken without it.

## What This Framework Does

1. **Takes your AI conversation history** (exported from ChatGPT, Claude, etc.)
2. **Classifies each conversation** — was it productive work? research? learning? just chatting?
3. **Estimates time saved** — based on benchmarks for each task type
4. **Tracks it over time** — so you can see your productivity trends week over week

```
This week:
  23 conversations with AI
  18 were productive (78%)
  ~4.2 hours saved
  Breakdown: 2.1h code, 1.3h emails/docs, 0.8h research
```

## Design Principles

- **Free by default** — the rule engine handles ~70% of conversations without any API calls
- **Private by default** — your conversations never leave your machine (unless you opt into LLM fallback)
- **Conservative estimates** — we'd rather undercount than overcount. Honest numbers matter.
- **Customizable** — your workflow is unique. Adjust benchmarks for how fast *you* work.

## Who Is This For?

- **Developers** who use Copilot/Claude/ChatGPT for coding and want to know how much time it saves
- **Knowledge workers** who use AI for writing, research, and daily tasks
- **Curious people** who want data about their own AI usage patterns
- **Anyone** who pays for an AI subscription and wants to know if it's worth it

## The Goal

Turn **"AI probably helps me"** into **"AI saved me 4.2 hours this week — 2.1h on code, 1.3h on emails, 0.8h on research."**

That's a real number. Something you can look at, learn from, and use to get even better.

---

*This is an open-source project. Contributions welcome — especially real-world time benchmarks from different workflows. See [CONTRIBUTING.md](CONTRIBUTING.md).*
