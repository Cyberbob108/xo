import json
import random
import string

import streamlit as st
from supabase import Client, create_client


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="XOXO Online",
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================
# WINNING COMBINATIONS
# ============================================================

WINNING_COMBINATIONS = [
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
]


# ============================================================
# MOBILE-FIRST CSS
# ============================================================

st.markdown(
    """
    <style>

    /* --------------------------------------------------------
       MAIN CONTAINER
       -------------------------------------------------------- */

    .block-container {
        width: 100%;
        max-width: 430px;
        padding: 0.8rem 0.55rem 1.2rem;
        margin: 0 auto;
    }

    header {
        visibility: hidden;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }


    /* --------------------------------------------------------
       TITLE
       -------------------------------------------------------- */

    .title {
        color: #102a43;
        font-size: 2rem;
        font-weight: 800;
        text-align: center;
        line-height: 1.1;
        margin: 0;
    }

    .subtitle {
        color: #627d98;
        font-size: 0.9rem;
        text-align: center;
        margin: 0.25rem 0 0.9rem;
    }


    /* --------------------------------------------------------
       GAME CODE
       -------------------------------------------------------- */

    .game-code {
        background: #e8f1f5;
        border: 2px solid #bcccdc;
        border-radius: 12px;
        color: #102a43;
        font-size: 1.7rem;
        font-weight: 800;
        letter-spacing: 0.45rem;
        padding: 0.55rem;
        text-align: center;
        margin: 0.5rem 0;
    }


    /* --------------------------------------------------------
       STATUS
       -------------------------------------------------------- */

    .status {
        color: #102a43;
        font-size: 1.05rem;
        font-weight: 700;
        text-align: center;
        padding: 0.35rem;
    }


    /* --------------------------------------------------------
       WAITING
       -------------------------------------------------------- */

    .waiting {
        background: #f0f4f8;
        border-radius: 14px;
        margin: 0.7rem 0;
        padding: 1rem;
        text-align: center;
        color: #334e68;
    }


    /* --------------------------------------------------------
       BOARD
       -------------------------------------------------------- */

    div[data-testid="stHorizontalBlock"] {
        gap: 0.35rem !important;
    }

    div[data-testid="stButton"] button {
        width: 100%;
        height: 88px !important;
        min-height: 88px !important;

        padding: 0 !important;
        margin: 0 !important;

        border-radius: 14px;
        border: 2px solid #d9e2ec;

        background: #ffffff;
        color: #102a43;

        font-size: 2.25rem !important;
        font-weight: 800;

        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.06);

        transition:
            transform 0.08s ease,
            background 0.08s ease;
    }

    div[data-testid="stButton"] button:active {
        transform: scale(0.96);
    }

    div[data-testid="stButton"] button:disabled {
        opacity: 1;
        color: #102a43;
        background: #ffffff;
    }


    /* --------------------------------------------------------
       PRIMARY BUTTONS
       -------------------------------------------------------- */

    div[data-testid="stButton"] button[kind="primary"] {
        min-height: 50px !important;
        height: 50px !important;
        font-size: 1rem !important;
        border-radius: 12px;
    }


    /* --------------------------------------------------------
       TEXT INPUT
       -------------------------------------------------------- */

    div[data-testid="stTextInput"] input {
        text-transform: uppercase;
        text-align: center;
        font-size: 1.3rem;
        font-weight: 700;
        letter-spacing: 0.3rem;
        height: 50px;
    }


    /* --------------------------------------------------------
       SCORE
       -------------------------------------------------------- */

    .score-box {
        border-top: 1px solid #d9e2ec;
        color: #334e68;
        margin-top: 0.8rem;
        padding: 0.7rem;
        text-align: center;
        font-size: 0.95rem;
    }


    /* --------------------------------------------------------
       TABS
       -------------------------------------------------------- */

    button[data-baseweb="tab"] {
        font-size: 0.9rem;
        font-weight: 700;
    }


    /* --------------------------------------------------------
       SMALL PHONES
       -------------------------------------------------------- */

    @media (max-width: 360px) {

        .block-container {
            padding-left: 0.35rem;
            padding-right: 0.35rem;
        }

        .title {
            font-size: 1.7rem;
        }

        .game-code {
            font-size: 1.5rem;
        }

        div[data-testid="stButton"] button {
            height: 76px !important;
            min-height: 76px !important;
            font-size: 2rem !important;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

def initialize_session():

    if "game_code" not in st.session_state:
        st.session_state.game_code = None

    if "player" not in st.session_state:
        st.session_state.player = None


initialize_session()


# ============================================================
# SUPABASE
# ============================================================

@st.cache_resource
def get_supabase() -> Client:

    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


# ============================================================
# GAME LOGIC
# ============================================================

def check_winner(board):

    for first, second, third in WINNING_COMBINATIONS:

        if (
            board[first]
            and board[first] == board[second]
            and board[first] == board[third]
        ):
            return board[first], [
                first,
                second,
                third,
            ]

    return None, []


# ============================================================
# GAME CODE
# ============================================================

def generate_game_code():

    characters = string.ascii_uppercase + string.digits

    while True:

        code = "".join(
            random.SystemRandom().choices(
                characters,
                k=4,
            )
        )

        try:

            result = (
                get_supabase()
                .table("xoxo_games")
                .select("game_code")
                .eq("game_code", code)
                .limit(1)
                .execute()
            )

            if not result.data:
                return code

        except Exception:

            return code


# ============================================================
# GET GAME
# ============================================================

def get_game(code):

    result = (
        get_supabase()
        .table("xoxo_games")
        .select("*")
        .eq("game_code", code)
        .limit(1)
        .execute()
    )

    return result.data[0] if result.data else None


# ============================================================
# DATABASE ERROR
# ============================================================

def show_database_error(error):

    message = str(error).lower()

    if "does not exist" in message:

        st.error(
            "The xoxo_games table does not exist. "
            "Run the database SQL setup."
        )

    elif (
        "row-level security" in message
        or "permission denied" in message
        or "42501" in message
    ):

        st.error(
            "Supabase blocked this request. "
            "Check your Supabase key and RLS settings."
        )

    elif "column" in message:

        st.error(
            "Your xoxo_games table does not match the app schema."
        )

    else:

        st.error(
            "Could not connect to the game server. "
            "Check your Supabase configuration."
        )


# ============================================================
# CREATE GAME
# ============================================================

def create_game():

    for _ in range(5):

        code = generate_game_code()

        data = {
            "game_code": code,
            "board": [""] * 9,
            "current_player": "X",
            "status": "waiting",
            "winner": None,
            "winning_cells": [],
            "x_score": 0,
            "o_score": 0,
            "draw_score": 0,
            "player_x": "X",
            "player_o": None,
            "round_number": 1,
        }

        try:

            result = (
                get_supabase()
                .table("xoxo_games")
                .insert(data)
                .execute()
            )

            if result.data:

                st.session_state.game_code = code
                st.session_state.player = "X"

                st.rerun()

        except Exception as error:

            if _ == 4:
                show_database_error(error)


# ============================================================
# JOIN GAME
# ============================================================

def join_game(raw_code):

    code = raw_code.strip().upper()

    valid_characters = (
        string.ascii_uppercase + string.digits
    )

    if (
        len(code) != 4
        or any(
            character not in valid_characters
            for character in code
        )
    ):

        st.error(
            "Game code must be exactly 4 letters or numbers."
        )

        return

    try:

        game = get_game(code)

        if not game:

            st.error("Game not found.")

            return

        if game.get("player_o"):

            st.error(
                "This game already has two players."
            )

            return

        result = (
            get_supabase()
            .table("xoxo_games")
            .update(
                {
                    "player_o": "O",
                    "status": "playing",
                }
            )
            .eq("game_code", code)
            .eq("status", "waiting")
            .is_("player_o", "null")
            .select("*")
            .execute()
        )

        if not result.data:

            st.error(
                "This game was just joined by another player."
            )

            return

        st.session_state.game_code = code
        st.session_state.player = "O"

        st.rerun()

    except Exception as error:

        show_database_error(error)


# ============================================================
# MAKE MOVE
# ============================================================

def make_move(index):

    player = st.session_state.player
    code = st.session_state.game_code

    try:

        game = get_game(code)

        if not game:

            st.error(
                "This game could not be found."
            )

            return

        board = list(
            game.get(
                "board",
                [""] * 9,
            )
        )

        # ----------------------------------------------------
        # CHECK GAME STATE
        # ----------------------------------------------------

        if game.get("status") != "playing":

            return

        if game.get("current_player") != player:

            st.warning(
                "It is the other player's turn."
            )

            return

        if index not in range(9):

            return

        if board[index]:

            return

        # ----------------------------------------------------
        # OLD BOARD
        # ----------------------------------------------------

        old_board = board[:]

        # ----------------------------------------------------
        # MAKE MOVE
        # ----------------------------------------------------

        board[index] = player

        winner, winning_cells = check_winner(board)

        next_player = (
            "O"
            if player == "X"
            else "X"
        )

        update = {
            "board": board,
            "current_player": next_player,
            "status": "playing",
            "winner": None,
            "winning_cells": [],
        }

        # ----------------------------------------------------
        # WIN
        # ----------------------------------------------------

        if winner:

            update.update(
                {
                    "status": "finished",
                    "winner": winner,
                    "winning_cells": winning_cells,
                }
            )

            if winner == "X":

                update["x_score"] = (
                    game["x_score"] + 1
                )

            elif winner == "O":

                update["o_score"] = (
                    game["o_score"] + 1
                )

        # ----------------------------------------------------
        # DRAW
        # ----------------------------------------------------

        elif all(board):

            update.update(
                {
                    "status": "finished",
                    "winner": None,
                    "winning_cells": [],
                    "draw_score": (
                        game["draw_score"] + 1
                    ),
                }
            )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        result = (
            get_supabase()
            .table("xoxo_games")
            .update(update)
            .eq("game_code", code)
            .eq("current_player", player)
            .eq(
                "board",
                json.dumps(
                    old_board,
                    separators=(",", ":"),
                ),
            )
            .select("game_code")
            .execute()
        )

        if not result.data:

            st.warning(
                "The board changed. Showing the latest game."
            )

        st.rerun()

    except Exception as error:

        show_database_error(error)


# ============================================================
# REMATCH
# ============================================================

def play_again(game):

    try:

        result = (
            get_supabase()
            .table("xoxo_games")
            .update(
                {
                    "board": [""] * 9,
                    "current_player": "X",
                    "status": "playing",
                    "winner": None,
                    "winning_cells": [],
                    "round_number": (
                        game["round_number"] + 1
                    ),
                }
            )
            .eq(
                "game_code",
                game["game_code"],
            )
            .eq(
                "status",
                "finished",
            )
            .eq(
                "round_number",
                game["round_number"],
            )
            .select("game_code")
            .execute()
        )

        if not result.data:

            st.info(
                "The next round is already ready."
            )

        st.rerun()

    except Exception as error:

        show_database_error(error)


# ============================================================
# LEAVE GAME
# ============================================================

def leave_game():

    st.session_state.game_code = None
    st.session_state.player = None

    st.rerun()


# ============================================================
# HOME SCREEN
# ============================================================

def home_screen():

    st.markdown(
        '<div class="title">🎮 XOXO</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">Online Tic-Tac-Toe developed with 🫰 </div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    if st.button(
        "🎮 Create Game",
        type="primary",
        use_container_width=True,
    ):

        create_game()

    st.divider()

    # --------------------------------------------------------
    # JOIN
    # --------------------------------------------------------

    st.subheader("🔗 Join a Game")

    code = st.text_input(
        "Game Code",
        max_chars=4,
        placeholder="AB12",
        label_visibility="collapsed",
    )

    if st.button(
        "Join Game",
        type="primary",
        use_container_width=True,
    ):

        join_game(code)

    st.write("")

    st.caption(
        "Create a game, share the 4-character code, "
        "and play together on two phones."
    )


# ============================================================
# GAME SCREEN
# ============================================================

@st.fragment(run_every="2s")
def game_screen():

    code = st.session_state.game_code

    try:

        game = get_game(code)

    except Exception:

        st.error(
            "The shared game state is temporarily unavailable."
        )

        return

    if not game:

        st.error(
            "This game could not be found."
        )

        if st.button(
            "Back to Home",
            use_container_width=True,
        ):

            leave_game()

        return

    player = st.session_state.player

    board = list(
        game.get(
            "board",
            [""] * 9,
        )
    )

    winning_cells = (
        game.get("winning_cells")
        or []
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.markdown(
        '<div class="title">🎮 XOXO</div>',
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

    st.markdown(
        f"""
        <div class="status">
            You are Player {player}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # WAITING
    # --------------------------------------------------------

    if game["status"] == "waiting":

        st.markdown(
            """
            <div class="waiting">
                <strong>⏳ Waiting for Player O</strong>
                <br><br>
                Share the 4-character code with your friend.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # PLAYING
    # --------------------------------------------------------

    elif game["status"] == "playing":

        if game["current_player"] == player:

            st.markdown(
                """
                <div class="status">
                    🟢 Your Turn
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                f"""
                <div class="status">
                    ⏳ Waiting for Player
                    {game["current_player"]}...
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # WINNER
    # --------------------------------------------------------

    elif game["status"] == "finished":

        if game.get("winner"):

            if game["winner"] == player:

                message = "🏆 You Win!"

            else:

                message = (
                    f"😔 Player {game['winner']} Wins"
                )

            st.markdown(
                f"""
                <div class="status">
                    {message}
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                """
                <div class="status">
                    🤝 It's a Draw!
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # BOARD
    # --------------------------------------------------------

    for row in range(3):

        columns = st.columns(3)

        for column in range(3):

            index = row * 3 + column

            value = board[index]

            # Winning cell
            if index in winning_cells:

                label = f"🏆 {value}"

            # X
            elif value == "X":

                label = "❌"

            # O
            elif value == "O":

                label = "⭕"

            # Empty
            else:

                label = " "

            disabled = (
                game["status"] != "playing"
                or game["current_player"] != player
                or bool(value)
            )

            with columns[column]:

                if st.button(
                    label,
                    key=(
                        f"cell_"
                        f"{game['game_code']}_"
                        f"{game['round_number']}_"
                        f"{index}"
                    ),
                    disabled=disabled,
                    use_container_width=True,
                ):

                    make_move(index)

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="score-box">
            ❌ X: <strong>{game["x_score"]}</strong>
            &nbsp;&nbsp;|&nbsp;&nbsp;
            ⭕ O: <strong>{game["o_score"]}</strong>
            &nbsp;&nbsp;|&nbsp;&nbsp;
            🤝 Draws: <strong>{game["draw_score"]}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # REMATCH
    # --------------------------------------------------------

    if game["status"] == "finished":

        st.write("")

        if st.button(
            "🔄 Play Again",
            type="primary",
            use_container_width=True,
        ):

            play_again(game)

    # --------------------------------------------------------
    # LEAVE
    # --------------------------------------------------------

    if st.button(
        "🚪 Leave Game",
        use_container_width=True,
    ):

        leave_game()


# ============================================================
# APPLICATION
# ============================================================

if (
    st.session_state.game_code
    and st.session_state.player
):

    game_screen()

else:

    home_screen()
