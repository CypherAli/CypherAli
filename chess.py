import chess
import sys
import re
import os

PIECES = {
    chess.PAWN:   ('♙', '♟'),
    chess.KNIGHT: ('♘', '♞'),
    chess.BISHOP: ('♗', '♝'),
    chess.ROOK:   ('♖', '♜'),
    chess.QUEEN:  ('♕', '♛'),
    chess.KING:   ('♔', '♚'),
}

LIGHT_SQ = '`　`'
DARK_SQ  = '`▪`'

def render_board(board):
    lines = []
    lines.append('|  | **a** | **b** | **c** | **d** | **e** | **f** | **g** | **h** |')
    lines.append('|:--:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|')
    for rank in range(7, -1, -1):
        row = [f'| **{rank+1}** |']
        for file in range(8):
            sq = chess.square(file, rank)
            piece = board.piece_at(sq)
            is_light = (rank + file) % 2 != 0
            if piece is None:
                cell = f' {"🟫" if not is_light else "⬜"} |'
            else:
                emoji = PIECES[piece.piece_type][0 if piece.color == chess.WHITE else 1]
                bg = "🟫" if not is_light else "⬜"
                cell = f' {emoji} |'
        row.append(cell)
        lines.append(''.join(row))
    return '\n'.join(lines)

def render_board_clean(board):
    """Clean SVG-style board render."""
    lines = []
    files = ['a','b','c','d','e','f','g','h']
    header = '| ` ` | ' + ' | '.join(f'**{f}**' for f in files) + ' |'
    sep    = '|:---:|' + ':---:|' * 8
    lines.append(header)
    lines.append(sep)
    for rank in range(7, -1, -1):
        cells = [f'**{rank+1}**']
        for file in range(8):
            sq = chess.square(file, rank)
            piece = board.piece_at(sq)
            light = (rank + file) % 2 != 0
            if piece is None:
                cells.append('🟦' if light else '🟫')
            else:
                emoji = PIECES[piece.piece_type][0 if piece.color == chess.WHITE else 1]
                cells.append(emoji)
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)

def make_move(fen, move_str):
    board = chess.Board(fen)
    s = move_str.strip().replace(' ', '')
    # Try UCI
    try:
        m = chess.Move.from_uci(s.lower())
        if m in board.legal_moves:
            board.push(m)
            return board, None
    except Exception:
        pass
    # Try SAN
    try:
        m = board.parse_san(s)
        board.push(m)
        return board, None
    except Exception:
        pass
    return None, f'Invalid move: `{move_str}`'

def sample_moves(board, n=8):
    moves = list(board.legal_moves)[:n]
    return ' · '.join(f'`{board.san(m)}`' for m in moves)

def update_readme(board, last_move_san, player, comment_url):
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()

    turn_label = '⬜ White' if board.turn == chess.WHITE else '⬛ Black'
    board_md = render_board_clean(board)

    if board.is_checkmate():
        winner = '⬛ Black' if board.turn == chess.WHITE else '⬜ White'
        status = f'🏆 **Checkmate — {winner} wins!**  [↺ New Game](../../issues/new?title=chess+reset&body=reset)'
    elif board.is_stalemate():
        status = '🤝 **Stalemate — Draw!**  [↺ New Game](../../issues/new?title=chess+reset&body=reset)'
    elif board.is_check():
        status = f'⚠️ **{turn_label} is in CHECK!**'
    elif board.is_game_over():
        status = f'🏁 **Game over.**  [↺ New Game](../../issues/new?title=chess+reset&body=reset)'
    else:
        status = f'▸ Turn: **{turn_label}**'

    new_section = f"""<!-- CHESS-START -->
<div align="center">

### ♟ LIVE CHESS — Play Against the World

{status}

> Last move: **{last_move_san}** by [{player}]({comment_url})

{board_md}

<sub>**[➤ Make your move in Issue #1](../../issues/1)** — comment with e.g. `e2e4`, `Nf3`, `O-O`</sub>

<sub>Legal moves: {sample_moves(board)}</sub>

</div>
<!-- CHESS-END -->"""

    new_content = re.sub(
        r'<!-- CHESS-START -->.*?<!-- CHESS-END -->',
        new_section,
        content,
        flags=re.DOTALL
    )

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_content)

    with open('.chess_state', 'w', encoding='utf-8') as f:
        f.write(board.fen())

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: chess.py <move> <player> <comment_url>')
        sys.exit(1)

    move_str, player, comment_url = sys.argv[1], sys.argv[2], sys.argv[3]

    if any(kw in move_str.lower() for kw in ['reset', 'new game', 'restart']):
        board = chess.Board()
        with open('.chess_state', 'w') as f:
            f.write(board.fen())
        board_md = render_board_clean(board)
        # Rebuild section for reset
        new_section = f"""<!-- CHESS-START -->
<div align="center">

### ♟ LIVE CHESS — Play Against the World

▸ Turn: **⬜ White** — New game started!

> Game reset by [{player}]({comment_url})

{board_md}

<sub>**[➤ Make your move in Issue #1](../../issues/1)** — comment with e.g. `e2e4`, `Nf3`, `O-O`</sub>

</div>
<!-- CHESS-END -->"""
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
        import re
        new_content = re.sub(r'<!-- CHESS-START -->.*?<!-- CHESS-END -->', new_section, content, flags=re.DOTALL)
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Game reset!')
        sys.exit(0)

    fen = chess.STARTING_FEN
    if os.path.exists('.chess_state'):
        with open('.chess_state') as f:
            fen = f.read().strip()

    board, err = make_move(fen, move_str)
    if err:
        print(err)
        sys.exit(1)

    prev = chess.Board(fen)
    san = prev.san(board.peek())
    update_readme(board, san, player, comment_url)
    print(f'Move {san} applied.')
