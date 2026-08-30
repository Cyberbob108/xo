# XOXO Online

XOXO is a lightweight online two-player Tic-Tac-Toe game built with Streamlit and Supabase. Two people can open the same Streamlit Community Cloud URL on separate phones or browsers, share a six-character game code, and play from different locations.

## Features

- Create and join games with a game code
- Remote multiplayer with automatic X/O assignment
- Shared Supabase board and turn management
- Winner and draw detection
- Persistent X wins, O wins, and draw scores
- Synchronized rematches
- Mobile-friendly native Streamlit controls

## Architecture

```text
Browser X -> Streamlit -> Supabase -> Streamlit -> Browser O
```

The board, turn, round, status, players, winner, and scores are always read from Supabase. Streamlit session state contains only the local browser's game code and player symbol. The game screen polls Supabase every two seconds while a game is waiting or playing.

## Supabase Setup

In the Supabase SQL Editor, run this complete setup script:

```sql
create table public.xoxo_games (
    game_code text primary key,
    board jsonb not null default '["","","","","","","","",""]'::jsonb,
    current_player text not null default 'X',
    status text not null default 'waiting',
    winner text,
    winning_cells jsonb not null default '[]'::jsonb,
    x_score integer not null default 0,
    o_score integer not null default 0,
    draw_score integer not null default 0,
    player_x text,
    player_o text,
    round_number integer not null default 1,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.xoxo_games enable row level security;

create policy "Anonymous players can read games"
on public.xoxo_games for select to anon using (true);

create policy "Anonymous players can create games"
on public.xoxo_games for insert to anon with check (true);

create policy "Anonymous players can update games"
on public.xoxo_games for update to anon
using (true) with check (true);
```

The conditional updates in `app.py` prevent normal stale clients from overwriting a newer board or taking a turn out of order. This is intentionally an anonymous casual game: anyone who knows a code can read or attempt to modify that row, and there are no accounts or identity guarantees. Never use a Supabase service-role key in this app. For a production game, add authentication and stricter server-side authorization.

## Streamlit Secrets

For local development, configure Streamlit secrets in your user or project secret store. Do not commit `.streamlit/secrets.toml`.

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"
```

On Streamlit Community Cloud, open the app settings, choose **Secrets**, and add the same two values. Use only the Supabase anonymous/public key.

## Local Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud

1. Push `app.py`, `requirements.txt`, and `README.md` to a GitHub repository.
2. Create a new app at [share.streamlit.io](https://share.streamlit.io/).
3. Select the repository, branch, and `app.py` as the main file.
4. Add `SUPABASE_URL` and `SUPABASE_KEY` in the app's Secrets settings.
5. Deploy and share the resulting URL with both players.
