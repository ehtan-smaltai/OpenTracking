# Why This Exists

## The $100 Billion Question

Companies worldwide are pouring unprecedented investment into AI. ChatGPT, Claude, Copilot, Gemini — every knowledge worker is getting access to AI assistants. The spending is real:

- Enterprise AI seat licenses: $20-50/user/month
- API usage for custom tools: thousands per month
- Training and onboarding time: hours per employee

But when leadership asks **"What's the ROI?"**, most teams have nothing to show. No data. No metrics. Just vibes.

> "It feels faster."
> "People seem to like it."
> "I think it helps with emails."

That's not good enough when budgets are tight.

## The Individual Problem

Even at a personal level, the same gap exists:

- You pay $20/month for ChatGPT Plus. Is it worth it?
- You use Claude for coding. How much time does it actually save vs. Stack Overflow?
- You want to mention AI productivity gains in your performance review. What numbers do you give?
- You're trying to optimize your workflow. Which types of tasks benefit most from AI?

**You can't improve what you don't measure.**

## What's Missing

There's no standard way to measure AI productivity gains. Time-tracking tools like Toggl or RescueTime track *how long you work*, but they can't tell you *how much time AI saved you*. AI platforms show you token usage and conversation counts, but that says nothing about value.

The missing piece: a framework that looks at what you did with AI and estimates how long it would have taken without it.

## What This Framework Does

1. **Takes your AI conversation history** (exported from ChatGPT, Claude, etc.)
2. **Classifies each conversation** — was it work? research? casual chat?
3. **Estimates time saved** — based on benchmarks for each task type
4. **Gives you real numbers** — "This week: 4.2 hours saved across 23 conversations"

### Key design choices

- **Free by default** — the rule engine handles ~70% of cases without any API calls
- **Private by default** — your conversations never leave your machine (unless you opt into LLM fallback)
- **Conservative estimates** — we'd rather undercount than overcount. Credibility matters.
- **Customizable** — your workflow is unique. Adjust benchmarks for how fast *you* work.

## Who Is This For?

### Individuals
- Track your personal AI productivity over time
- Know which tasks benefit most from AI
- Have real numbers for performance reviews
- Decide if that AI subscription is worth the money

### Team leads
- Measure AI adoption and impact across your team
- Justify AI tool spending with data
- Identify where AI helps most and where it doesn't
- Make informed decisions about which tools to keep

### Companies
- Quantify ROI on AI investments
- Track productivity improvements over quarters
- Benchmark AI productivity across departments
- Build a data-driven case for expanding (or cutting) AI spending

## The Bottom Line

AI is the biggest shift in knowledge work since the internet. But unlike the internet, we have the chance to measure its impact from day one. This framework is a starting point — an open-source tool that turns **"AI probably helps"** into **"AI saved 4.2 hours this week, mostly on code and emails."**

That's a number you can put in a report. That's a number that justifies the investment. That's a number that helps you understand your own productivity.

---

*This is an open-source project. Contributions welcome — especially real-world time benchmarks from different professions and workflows. See [CONTRIBUTING.md](CONTRIBUTING.md).*
