# Aperture System: pricing notes (internal, not for clients)

Deck: `Aperture_Proposal.pdf`, source in `source/deck.html`. Pricing is on page 9 of the deck.

## Proposed monthly prices (excl. GST)
| Plan | Price | Includes |
| --- | --- | --- |
| Inbox | 22,222 | Automates all inbound and query channels into one central CRM, enquiry counts, daily report. No voice |
| Inbox + Team | 33,333 | Inbox plus the micro-operation agent setup on Telegram, up to 10 people |
| Full system | 44,444 | Team plus AI calling (1,500 min), call scoring (1,000 calls), floor view, rewards, client portal |

Overage: 10 per extra call minute, 5 per extra scored call. Setup is a one-time fee quoted at scoping (suggested 25,000 Inbox, 40,000 Full). Phone numbers and telephony registration at actual cost.

## Our run cost per client per month (estimates, rupees at about 90 per USD)
| Item | Inbox | Team adds | Full adds |
| --- | --- | --- | --- |
| Hosting and database (Vercel Pro and Supabase share) | 2,000 | | 1,500 to 2,500 (recordings, portal) |
| LLM for chats (about 1 to 2 per conversation, 1,500 to 3,000 chats) | 2,000 to 3,500 | | |
| Always-on server for the Telegram assistant | | 600 to 1,000 | |
| LLM for the assistant (10 people, follow-ups, proof checks) | | 3,000 to 5,000 | |
| Voice minutes, 1,500 at 4 to 7 per minute (telephony, speech to text, text to speech, LLM) | | | 6,000 to 10,500 |
| Call scoring, 1,000 calls at 2.5 to 3 per call | | | 2,500 to 3,000 |
| **Cumulative cost** | **4,000 to 5,500** | **8,000 to 11,500** | **18,000 to 26,500** |
| **Price** | 22,222 | 33,333 | 44,444 |
| **Gross margin** | about 75 to 82% | about 66 to 76% | about 40 to 59% |

Measured vs guessed: only "about 650 Workers AI neurons per enquiry" is measured (Maddie Demo/Plan.md). Everything else is a planning estimate. Get real quotes for telephony, speech to text and text to speech before signing a calling client.

## Things the table does not include
- Your and Atharva's time for the monthly review and fixes.
- Meta WhatsApp conversation fees if WhatsApp is added later.
- DLT and number registration for Indian outbound calling.

## Watch-outs
- Both the Instagram agent and the team assistant must run on a paid API key before a real launch. The Plan notes say the Claude Code OAuth token is in use for testing and is against Anthropic's terms in client production.
- Scoring cost scales with call volume, not seats. A 10 seat floor can make 10,000 calls a month, so a call-centre client needs a per-call quote, not the flat Full system price.
- Cloudflare free neurons (10,000 a day per account) do not cover production. Budget a paid plan or another provider.
- Client names and figures in page 8 need each client's OK before the deck goes out.

## Note (2026-11-27)
Prices set by Sanidhya: 22,222 / 33,333 / 44,444. Full system margin is now the thinnest, and it carries the usage risk, so watch call minutes and scored calls closely.
