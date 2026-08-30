import random
import string
import json

import streamlit as st
from supabase import Client, create_client


st.set_page_config(page_title="XOXO Online", page_icon="🎮", layout="centered", initial_sidebar_state="collapsed")

WINNING_COMBINATIONS = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]

st.markdown("""
<style>
.block-container { max-width: 560px; padding: 2rem 1rem 1.5rem; }
.title { color: #102a43; font-size: 2.4rem; font-weight: 800; text-align: center; margin-bottom: 0; }
.subtitle { color: #486581; text-align: center; margin-bottom: 1.4rem; }
.game-code { background: #e8f1f5; border: 1px solid #bcccdc; border-radius: 10px; color: #102a43; font-size: 1.8rem; font-weight: 800; letter-spacing: .3rem; padding: .6rem; text-align: center; }
.status { color: #102a43; font-size: 1.25rem; font-weight: 700; padding: .65rem; text-align: center; }
.waiting { background: #f0f4f8; border-radius: 10px; margin: 1rem 0; padding: 1.2rem; text-align: center; }
.score-box { border-top: 1px solid #d9e2ec; color: #334e68; margin-top: 1.1rem; padding: .9rem; text-align: center; }
div[data-testid="stButton"] button { min-height: 58px; border-radius: 9px; font-size: 1.8rem; font-weight: 800; }
div[data-testid="stTextInput"] input { text-transform: uppercase; }
@media (max-width: 480px) { .block-container { padding-top: 1rem; } .title { font-size: 2rem; } div[data-testid="stButton"] button { min-height: 64px; } }
</style>
""", unsafe_allow_html=True)


def initialize_session():
    if "game_code" not in st.session_state:
        st.session_state.game_code = None
    if "player" not in st.session_state:
        st.session_state.player = None


@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def check_winner(board):
    for first, second, third in WINNING_COMBINATIONS:
        if board[first] and board[first] == board[second] == board[third]:
            return board[first], [first, second, third]
    return None, []


def generate_game_code():
    return "".join(random.SystemRandom().choices(string.ascii_uppercase + string.digits, k=6))


def get_game(code):
    result = get_supabase().table("xoxo_games").select("*").eq("game_code", code).limit(1).execute()
    return result.data[0] if result.data else None


def create_game():
    for _ in range(5):
        code = generate_game_code()
        data = {"game_code": code, "board": [""] * 9, "current_player": "X", "status": "waiting", "winner": None, "winning_cells": [], "x_score": 0, "o_score": 0, "draw_score": 0, "player_x": "X", "player_o": None, "round_number": 1}
        try:
            result = get_supabase().table("xoxo_games").insert(data).select("*").execute()
            if result.data:
                st.session_state.game_code = code
                st.session_state.player = "X"
                st.rerun()
        except Exception:
            continue
    st.error("We could not create a game right now. Please try again.")


def join_game(raw_code):
    code = raw_code.strip().upper()
    valid_characters = string.ascii_uppercase + string.digits
    if len(code) != 6 or any(character not in valid_characters for character in code):
        st.error("Game code must be 6 letters or numbers.")
        return
    try:
        game = get_game(code)
        if not game:
            st.error("Game not found.")
            return
        if game.get("player_o"):
            st.error("This game is already full.")
            return
        result = (get_supabase().table("xoxo_games").update({"player_o": "O", "status": "playing"})
                  .eq("game_code", code).is_("player_o", "null").eq("status", "waiting").select("*").execute())
        if not result.data:
            st.error("This game was just joined by another player.")
            return
        st.session_state.game_code = code
        st.session_state.player = "O"
        st.rerun()
    except Exception:
        st.error("Could not join the game. Please check the code and try again.")


def make_move(index):
    player = st.session_state.player
    code = st.session_state.game_code
    try:
        game = get_game(code)
        if not game:
            st.error("This game could not be found.")
            return
        board = list(game.get("board", []))
        if game.get("status") != "playing":
            st.warning("This round is already finished.")
            return
        if game.get("current_player") != player:
            st.warning("It is the other player's turn.")
            return
        if index not in range(9) or board[index]:
            st.warning("That cell is already occupied.")
            return

        old_board = board[:]
        board[index] = player
        winner, winning_cells = check_winner(board)
        update = {"board": board, "current_player": "O" if player == "X" else "X", "status": "playing", "winner": None, "winning_cells": []}
        if winner:
            update.update({"status": "finished", "winner": winner, "winning_cells": winning_cells})
            score_name = "x_score" if winner == "X" else "o_score"
            update[score_name] = game[score_name] + 1
        elif all(board):
            update.update({"status": "finished", "draw_score": game["draw_score"] + 1})

        result = (get_supabase().table("xoxo_games").update(update).eq("game_code", code)
              .eq("current_player", player).eq("board", json.dumps(old_board, separators=(",", ":"))).select("game_code").execute())
        if not result.data:
            st.warning("The game changed. The latest board is now shown.")
        st.rerun()
    except Exception:
        st.error("Your move could not be saved. Please try again.")


def play_again(game):
    try:
        result = (get_supabase().table("xoxo_games").update({"board": [""] * 9, "current_player": "X", "status": "playing", "winner": None, "winning_cells": [], "round_number": game["round_number"] + 1})
                  .eq("game_code", game["game_code"]).eq("status", "finished").eq("round_number", game["round_number"]).select("game_code").execute())
        if not result.data:
            st.info("The next round is already ready.")
        st.rerun()
    except Exception:
        st.error("Could not start the next round. Please try again.")


def leave_game():
    st.session_state.game_code = None
    st.session_state.player = None
    st.rerun()


def home_screen():
    st.markdown('<div class="title">🎮 XOXO</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Online Tic-Tac-Toe</div>', unsafe_allow_html=True)
    if st.button("Create Game", type="primary", use_container_width=True):
        try:
            create_game()
        except Exception:
            st.error("Supabase is not configured or is unavailable.")
    st.divider()
    st.subheader("Join a Game")
    code = st.text_input("Game Code", max_chars=6, placeholder="ABC123")
    if st.button("Join Game", type="primary", use_container_width=True):
        try:
            join_game(code)
        except Exception:
            st.error("Supabase is not configured or is unavailable.")


@st.fragment(run_every="2s")
def game_screen():
    code = st.session_state.game_code
    try:
        game = get_game(code)
    except Exception:
        st.error("The shared game state is temporarily unavailable.")
        return
    if not game:
        st.error("This game could not be found.")
        if st.button("Back to Home", use_container_width=True):
            leave_game()
        return

    player = st.session_state.player
    board = list(game.get("board", [""] * 9))
    winning_cells = game.get("winning_cells") or []
    st.markdown('<div class="title">🎮 XOXO</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="game-code">{game["game_code"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status">You are Player {player}</div>', unsafe_allow_html=True)
    if game["status"] == "waiting":
        st.markdown('<div class="waiting"><strong>⏳ Waiting for Player O...</strong><br>Share the game code with your friend.</div>', unsafe_allow_html=True)
    elif game["status"] == "playing":
        if game["current_player"] == player:
            st.markdown('<div class="status">🟢 Your Turn</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status">⏳ Waiting for {game["current_player"]}...</div>', unsafe_allow_html=True)
    elif game.get("winner"):
        message = "🏆 You Win!" if game["winner"] == player else "😔 You Lose!"
        st.markdown(f'<div class="status">{message}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status">🤝 It\'s a Draw!</div>', unsafe_allow_html=True)

    for row in range(3):
        columns = st.columns(3)
        for column in range(3):
            index = row * 3 + column
            value = board[index]
            label = "🏆 " + value if index in winning_cells else ("❌" if value == "X" else "⭕" if value == "O" else " ")
            disabled = game["status"] != "playing" or game["current_player"] != player or bool(value)
            with columns[column]:
                if st.button(label, key=f"cell_{game['round_number']}_{index}", disabled=disabled, use_container_width=True):
                    make_move(index)

    st.markdown(f'<div class="score-box">X Wins: <strong>{game["x_score"]}</strong> &nbsp;|&nbsp; O Wins: <strong>{game["o_score"]}</strong> &nbsp;|&nbsp; Draws: <strong>{game["draw_score"]}</strong></div>', unsafe_allow_html=True)
    if game["status"] == "finished" and st.button("🔄 Play Again", type="primary", use_container_width=True):
        play_again(game)
    if st.button("🚪 Leave Game", use_container_width=True):
        leave_game()


initialize_session()
if st.session_state.game_code and st.session_state.player:
    game_screen()
else:
    home_screen()
