import streamlit as st


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="XOXO",
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------
# CSS
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        /* Main page */
        .block-container {
            max-width: 520px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Title */
        .game-title {
            text-align: center;
            font-size: 2.4rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        /* Status */
        .game-status {
            text-align: center;
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 1.2rem;
        }

        /* Board buttons */
        div.stButton > button {
            width: 100%;
            height: 105px;
            font-size: 2.8rem;
            font-weight: 700;
            border-radius: 14px;
            margin-bottom: 8px;
        }

        /* Score */
        .score-container {
            display: flex;
            justify-content: space-around;
            text-align: center;
            margin-top: 1rem;
            margin-bottom: 1.2rem;
        }

        .score-value {
            font-size: 1.8rem;
            font-weight: 700;
        }

        .score-label {
            font-size: 0.9rem;
        }

        /* Mobile adjustments */
        @media (max-width: 600px) {
            .block-container {
                padding-left: 12px;
                padding-right: 12px;
                padding-top: 1rem;
            }

            .game-title {
                font-size: 2rem;
            }

            .game-status {
                font-size: 1.2rem;
            }

            div.stButton > button {
                height: 85px;
                font-size: 2.3rem;
                border-radius: 12px;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Game initialization
# ---------------------------------------------------------
def initialize_game():
    """Initialize a new game without changing the score."""
    st.session_state.board = [""] * 9
    st.session_state.current_player = "X"
    st.session_state.game_status = "X's Turn"
    st.session_state.winner = None
    st.session_state.winning_cells = []
    st.session_state.game_over = False


def initialize_state():
    """Initialize session state the first time the app loads."""
    if "board" not in st.session_state:
        initialize_game()

    if "x_score" not in st.session_state:
        st.session_state.x_score = 0

    if "o_score" not in st.session_state:
        st.session_state.o_score = 0

    if "draw_score" not in st.session_state:
        st.session_state.draw_score = 0


# ---------------------------------------------------------
# Winner detection
# ---------------------------------------------------------
def check_winner(board):
    """
    Check whether X or O has won.

    Returns:
        tuple: (winner, winning_cells)
        winner is "X", "O", or None.
    """

    winning_combinations = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    ]

    for combination in winning_combinations:
        a, b, c = combination

        if (
            board[a]
            and board[a] == board[b]
            and board[b] == board[c]
        ):
            return board[a], list(combination)

    return None, []


# ---------------------------------------------------------
# Make a move
# ---------------------------------------------------------
def make_move(index):
    """Place the current player's symbol in the selected cell."""

    # Do not allow moves after game ends.
    if st.session_state.game_over:
        return

    # Do not allow occupied cells to be changed.
    if st.session_state.board[index] != "":
        return

    player = st.session_state.current_player

    # Place the symbol.
    st.session_state.board[index] = player

    # Check for winner.
    winner, winning_cells = check_winner(st.session_state.board)

    if winner:
        st.session_state.winner = winner
        st.session_state.winning_cells = winning_cells
        st.session_state.game_over = True
        st.session_state.game_status = f"{winner} Wins!"

        if winner == "X":
            st.session_state.x_score += 1
        else:
            st.session_state.o_score += 1

        return

    # Check for draw.
    if all(cell != "" for cell in st.session_state.board):
        st.session_state.game_over = True
        st.session_state.game_status = "It's a Draw!"
        st.session_state.draw_score += 1
        return

    # Switch player.
    st.session_state.current_player = (
        "O" if player == "X" else "X"
    )

    st.session_state.game_status = (
        f"{st.session_state.current_player}'s Turn"
    )


# ---------------------------------------------------------
# Reset game
# ---------------------------------------------------------
def reset_game():
    """Start a new game while keeping the existing score."""
    initialize_game()


# ---------------------------------------------------------
# Reset score
# ---------------------------------------------------------
def reset_score():
    """Reset all scores to zero."""
    st.session_state.x_score = 0
    st.session_state.o_score = 0
    st.session_state.draw_score = 0


# ---------------------------------------------------------
# Initialize application state
# ---------------------------------------------------------
initialize_state()


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.markdown(
    '<div class="game-title">🎮 XOXO</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="game-status">{st.session_state.game_status}</div>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Game board
# ---------------------------------------------------------
for row in range(3):
    columns = st.columns(3, gap="small")

    for col in range(3):
        index = row * 3 + col
        value = st.session_state.board[index]

        # Give winning cells a visual indicator.
        if index in st.session_state.winning_cells:
            label = f"🏆 {value}"
        else:
            label = value if value else " "

        # Disable occupied cells and all cells after game ends.
        disabled = (
            value != ""
            or st.session_state.game_over
        )

        with columns[col]:
            if st.button(
                label,
                key=f"cell_{index}",
                disabled=disabled,
                use_container_width=True,
            ):
                make_move(index)
                st.rerun()


# ---------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------
st.markdown(
    f"""
    <div class="score-container">
        <div>
            <div class="score-value">{st.session_state.x_score}</div>
            <div class="score-label">X Wins</div>
        </div>

        <div>
            <div class="score-value">{st.session_state.o_score}</div>
            <div class="score-label">O Wins</div>
        </div>

        <div>
            <div class="score-value">{st.session_state.draw_score}</div>
            <div class="score-label">Draws</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Controls
# ---------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button(
        "🔄 New Game",
        use_container_width=True,
    ):
        reset_game()
        st.rerun()

with col2:
    if st.button(
        "🗑️ Reset Score",
        use_container_width=True,
    ):
        reset_score()
        st.rerun()
