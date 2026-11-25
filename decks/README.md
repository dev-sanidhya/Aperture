# Aperture Decks

All pitch decks live here, one folder per deck. PDFs are the deliverable, `source/` holds the editable HTML.

| Folder | Audience | Latest PDF | Date |
| --- | --- | --- | --- |
| `aperture-ops/` | BPOs and call centers (Aperture Ops platform) | `Aperture_Ops_Pitch_Deck_v2.pdf` | Nov 2026 |
| `influencer-agencies/` | Influencer marketing and management agencies (Glad U Came system) | `Aperture_Influencer_Agencies_Deck_v1.pdf` | 2026-11-17 |
| `client-results/` | Any prospect: results with Glad U Came, ROCCS' Accounts Academy, Tanu Locks | `Aperture_Client_Results_Deck_v1.pdf` | 2026-11-25 |

## Conventions
- Folder name: lowercase audience slug. File name: `Aperture_<Audience>_Deck_v<N>.pdf`. Bump the version instead of overwriting.
- Keep editable source in `<deck>/source/` (HTML plus `img/`). Decks without source (like `aperture-ops`) hold the PDF only.
- Theme: cream #F2EEE7, ink #0B0B0A, orange #F26A21, Archivo Black headlines, JetBrains Mono labels, hard offset shadows, very little text. Start new decks from `_template.html`.
- Product visuals are drawn mockups marked "sample data". Only real client figures are shown as real.
- Render PDF: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-pdf-header-footer --virtual-time-budget=20000 --print-to-pdf=out.pdf file://$PWD/source/deck.html`
- Client names and figures need the client's OK before a deck goes out.
