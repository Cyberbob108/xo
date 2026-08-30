import random
import string
import uuid
import streamlit as st
from supabase import create_client, Client


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="XOXO Online",
    page_icon="❌",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================
# SUPABASE
# ============================================================

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SECRET_KEY"]
    return create_client(url, key)


supabase = get_supabase()


# ============================================================
# SESSION STATE
# ============================================================

if "player_token" not in st.session_state:
    st.session_state.player_token = str(uuid.uuid4())

if "game_id" not in st.session_state:
    st.session_state.game_id = None

if "player" not in st.session_state:
    st.session_state.player = None

if "game_code" not in st.session_state:
    st.session_state.game_code = None


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
        .main {
            max-width: 520px;
            margin: auto;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 520px;
        }

        .title {
            text-align: center;
            font-size: 2.4rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            text-align: center;
            color: #777;
            margin-bottom: 1.5rem;
        }

        .game-code {
            background: #f1f3f6;
            border-radius: 12px;
            padding: 12px;
            text-align: center;
            font-size: 1.5rem;
            font-weight: 800;
            letter-spacing: 5px;
            margin: 10px 0 20px 0;
        }

        .status {
            text-align: center;
            font-size: 1.35rem;
            font-weight: 700;
            padding: 10px;
            margin-bottom: 10px;
        }

        .score-box {
            background: #f7f7f7;
            border-radius: 12px;
            padding: 12px;
            text-align: center;
            margin-top: 15px;
        }

        .waiting {
            text-align: center;
            padding: 25px 10px;
            border-radius: 15px;
            background: #f7f7f7;
            margin: 15px 0;
        }

        button {
            min-height: 48px !important;
        }

        div[data-testid="stButton"] button {
            border-radius: 12px;
            font-weight: 700;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GAME LOGIC
# ============================================================

WINNING_COMBINATIONS = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6],
]


def check_winner(board):
    for combo in WINNING_COMBINATIONS:
        a, b, c = combo

        if (
            board[a]
            and board[a] == board[b]
            and board[a] == board[c]
        ):
            return board[a], combo

    if all(board):
        return "DRAW", []

    return None, []


def generate_game_code():
    chars = string.ascii_uppercase + string.digits

    while True:
        code = "".join(random.choices(chars, k=6))

        result = (
            supabase
            .table("xoxo_games")
            .select("id")
            .eq("game_code", code)
            .execute()
        )

        if not result.data:
            return code


def get_game(game_id):
    result = (
        supabase
        .table("xoxo_games")
        .select("*")
        .eq("id", game_id)
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


# ============================================================
# DATABASE OPERATIONS
# ============================================================

def create_game():
    code = generate_game_code()

    data = {
        "game_code": code,
        "player_x_token": st.session_state.player_token,
        "player_o_token": None,
        "board": [""] * 9,
        "current_player": "X",
        "status": "waiting",
        "winner": None,
        "winning_cells": [],
        "score_x": 0,
        "score_o": 0,
        "score_draw": 0,
        "round_number": 1,
        "version": 1,
    }

    result = (
        supabase
        .table("xoxo_games")
        .insert(data)
        .execute()
    )

    if result.data:
        game = result.data[0]

        st.session_state.game_id = game["id"]
        st.session_state.game_code = game["game_code"]
        st.session_state.player = "X"

        st.rerun()


def join_game(code):
    code = code.strip().upper()

    if len(code) != 6:
        st.error("Game code must be 6 characters.")
        return

    result = (
        supabase
        .table("xoxo_games")
        .select("*")
        .eq("game_code", code)
        .limit(1)
        .execute()
    )

    if not result.data:
        st.error("Game not found.")
        return

    game = result.data[0]

    # Creator attempting to join their own game
    if game["player_x_token"] == st.session_state.player_token:
        st.session_state.game_id = game["id"]
        st.session_state.game_code = game["game_code"]
        st.session_state.player = "X"
        st.rerun()

    # Game already has O
    if game["player_o_token"]:
        if game["player_o_token"] == st.session_state.player_token:
            st.session_state.game_id = game["id"]
            st.session_state.game_code = game["game_code"]
            st.session_state.player = "O"
            st.rerun()

        st.error("This game already has two players.")
        return

    # Atomically claim O
    update = (
        supabase
        .table("xoxo_games")
        .update(
            {
                "player_o_token": st.session_state.player_token,
                "status": "active",
                "version": game["version"] + 1,
            }
        )
        .eq("id", game["id"])
        .is_("player_o_token", "null")
        .execute()
    )

    if not update.data:
        st.error("Someone else just joined this game. Try again.")
        return

    st.session_state.game_id = game["id"]
    st.session_state.game_code = game["game_code"]
    st.session_state.player = "O"

    st.rerun()


def make_move(game, index):
    player = st.session_state.player

    if not player:
        return

    if game["status"] != "active":
        return

    if game["current_player"] != player:
        return

    board = list(game["board"])

    if board[index]:
        return

    # Make the move locally
    board[index] = player

    winner, winning_cells = check_winner(board)

    new_status = "active"
    new_winner = None
    new_current_player = "O" if player == "X" else "X"

    score_x = game["score_x"]
    score_o = game["score_o"]
    score_draw = game["score_draw"]

    if winner == "X":
        new_status = "won"
        new_winner = "X"
        score_x += 1

    elif winner == "O":
        new_status = "won"
        new_winner = "O"
        score_o += 1

    elif winner == "DRAW":
        new_status = "draw"
        new_winner = None
        score_draw += 1

    update_data = {
        "board": board,
        "current_player": new_current_player,
        "status": new_status,
        "winner": new_winner,
        "winning_cells": winning_cells,
        "score_x": score_x,
        "score_o": score_o,
        "score_draw": score_draw,
        "version": game["version"] + 1,
    }

    # Optimistic locking prevents both players from
    # successfully modifying the same board state.
    result = (
        supabase
        .table("xoxo_games")
        .update(update_data)
        .eq("id", game["id"])
        .eq("version", game["version"])
        .execute()
    )

    if not result.data:
        st.warning("Game changed. Refreshing...")
        return


def rematch(game):
    # Reset board but keep scores.
    update_data = {
        "board": [""] * 9,
        "current_player": "X",
        "status": "active",
        "winner": None,
        "winning_cells": [],
        "round_number": game["round_number"] + 1,
        "version": game["version"] + 1,
    }

    result = (
        supabase
        .table("xoxo_games")
        .update(update_data)
        .eq("id", game["id"])
        .eq("version", game["version"])
        .execute()
    )

    if not result.data:
        st.warning("The game has already been restarted.")


def leave_game():
    st.session_state.game_id = None
    st.session_state.game_code = None
    st.session_state.player = None
    st.rerun()


# ============================================================
# HOME SCREEN
# ============================================================

def home_screen():
    st.markdown(
        '<div class="title">❌⭕ XOXO</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">Online Tic-Tac-Toe</div>',
        unsafe_allow_html=True,
    )

    create_tab, join_tab = st.tabs(
        ["🎮 Create Game", "🔗 Join Game"]
    )

    with create_tab:
        st.write("")
        st.write("Create a game and share the code with your friend.")

        if st.button(
            "🎮 Create New Game",
            use_container_width=True,
            type="primary",
        ):
            create_game()

    with join_tab:
        st.write("")
        st.write("Enter the 6-character game code from your friend.")

        code = st.text_input(
            "Game Code",
            max_chars=6,
            placeholder="ABC123",
            label_visibility="collapsed",
        ).upper()

        if st.button(
            "🔗 Join Game",
            use_container_width=True,
            type="primary",
        ):
            join_game(code)

    st.divider()

    st.caption(
        "Open this app on two phones, create a game on one "
        "phone, then join using the code on the other."
    )


# ============================================================
# GAME SCREEN
# ============================================================

@st.fragment(run_every="1s")
def game_screen():
    game = get_game(st.session_state.game_id)

    if not game:
        st.error("Game no longer exists.")
        if st.button("Back to Home"):
            leave_game()
        return

    player = st.session_state.player

    st.markdown(
        '<div class="title">❌⭕ XOXO</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="game-code">
            {game["game_code"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        f"You are Player {player}"
    )

    # --------------------------------------------------------
    # WAITING FOR SECOND PLAYER
    # --------------------------------------------------------

    if not game["player_o_token"]:
        st.markdown(
            """
            <div class="waiting">
                <h3>⏳ Waiting for Player O</h3>
                <p>Share the game code above with your friend.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "🚪 Leave Game",
            use_container_width=True,
        ):
            leave_game()

        return

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if game["status"] == "active":
        if game["current_player"] == player:
            status_text = f"🟢 Your turn — {player}"
        else:
            status_text = f"⏳ Player {game['current_player']}'s turn"

    elif game["status"] == "won":
        status_text = f"🏆 Player {game['winner']} Wins!"

    else:
        status_text = "🤝 It's a Draw!"

    st.markdown(
        f'<div class="status">{status_text}</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # BOARD
    # --------------------------------------------------------

    board = game["board"]
    winning_cells = game["winning_cells"]

    for row in range(3):
        cols = st.columns(3)

        for col in range(3):
            index = row * 3 + col

            value = board[index]

            if index in winning_cells:
                label = f"🏆 {value}"
            elif value == "X":
                label = "❌"
            elif value == "O":
                label = "⭕"
            else:
                label = " "

            disabled = (
                game["status"] != "active"
                or game["current_player"] != player
                or bool(value)
            )

            with cols[col]:
                if st.button(
                    label,
                    key=f"cell_{game['id']}_{game['version']}_{index}",
                    disabled=disabled,
                    use_container_width=True,
                ):
                    make_move(game, index)

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="score-box">
            ❌ X: <b>{game["score_x"]}</b>
            &nbsp;&nbsp;|&nbsp;&nbsp;
            ⭕ O: <b>{game["score_o"]}</b>
            &nbsp;&nbsp;|&nbsp;&nbsp;
            🤝 Draws: <b>{game["score_draw"]}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # --------------------------------------------------------
    # GAME OVER
    # --------------------------------------------------------

    if game["status"] in ("won", "draw"):
        if st.button(
            "🔄 Rematch",
            use_container_width=True,
            type="primary",
        ):
            rematch(game)

    if st.button(
        "🚪 Leave Game",
        use_container_width=True,
    ):
        leave_game()


# ============================================================
# APP ROUTER
# ============================================================

if st.session_state.game_id:
    game_screen()
else:
    home_screen()
