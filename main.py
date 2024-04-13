import matplotlib.patches as patches
from matplotlib.pylab import f
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from graphviz import Digraph

# RANGE_INCREMENTS x means we will have (100 / x) in the range
# For example with 5 the values are [0, 0.05, 0.1, 0.15, ..., 0.95]
RANGE_INCREMENTS = 5


# prob for random number in [u, 1] being bigger than in [b, 1]
def u_win_prob(u, b):
    if u > 1 or u < 0 or b > 1 or b < 0:
        raise ValueError("u and b should be in [0, 1]")
    if u >= b:
        # The math is based on looking the prob mass function
        # of the combined random variables, so basically 2d geometry.
        triangle_area = 0.5 * (1 - u) * (1 - u)
        rectangle_area = (u - b) * (1 - u)
        a_win_area = triangle_area + rectangle_area
        total_area = (1 - u) * (1 - b)

        return a_win_area / total_area
    # b > u
    return 1 - u_win_prob(b, u)


def u_bet_prob(u, b):
    return 1 - u


def u_fold_prob(u, b):
    return u


def b_call_prob(u, b):
    return 1 - b


def b_fold_prob(u, b):
    return b


def u_bet_b_fold_prob(u, b):
    u_bet = u_bet_prob(u, b)
    b_fold = b_fold_prob(u, b)

    return u_bet * b_fold


def u_bet_b_call_u_win_prob(u, b):
    u_bet = u_bet_prob(u, b)
    b_call = b_call_prob(u, b)
    a_win = u_win_prob(u, b)

    return u_bet * b_call * a_win


def u_bet_b_call_b_win_prob(u, b):
    u_bet = u_bet_prob(u, b)
    b_call = b_call_prob(u, b)
    a_win = u_win_prob(u, b)

    return u_bet * b_call * (1 - a_win)


def btn_ev(u, b, pot_size, bet_size):
    total_ev = 0

    # U fold
    total_ev += u_fold_prob(u, b) * pot_size
    # U bet, B fold
    total_ev += u_bet_b_fold_prob(u, b) * 0
    # U bet, B call, U win
    total_ev += u_bet_b_call_u_win_prob(u, b) * -bet_size
    # U bet, B call, B win
    total_ev += u_bet_b_call_b_win_prob(u, b) * (pot_size + bet_size)

    return total_ev


def utg_ev(u, b, pot_size, bet_size):
    total_ev = 0

    # U fold
    total_ev += u_fold_prob(u, b) * 0
    # U bet, B fold
    total_ev += u_bet_b_fold_prob(u, b) * pot_size
    # U bet, B call, U win
    total_ev += u_bet_b_call_u_win_prob(u, b) * (pot_size + bet_size)
    # U bet, B call, B win
    total_ev += u_bet_b_call_b_win_prob(u, b) * -bet_size

    return total_ev


def get_possible_ne_points(btn_evs):
    length = len(btn_evs)

    # BTN possible Nash Equilibrium points are the maximum column values in each row
    btn_possible_ne_points = set()
    for row_number in range(length):
        max_value = float("-inf")
        max_indexes = []
        for col_number in range(length):
            curr_value = btn_evs[row_number][col_number]

            if abs(curr_value - max_value) < 1e-6:
                max_indexes.append(col_number)
            elif curr_value > max_value:
                max_value = curr_value
                max_indexes = [col_number]

        for col_number in max_indexes:
            btn_possible_ne_points.add((row_number, col_number))

    # UTG possible Nash Equilibrium points are the minimum row values in each column
    utg_possible_ne_points = set()
    for col_number in range(length):
        min_value = float("inf")
        min_indexes = []
        for row_number in range(length):
            curr_value = btn_evs[row_number][col_number]

            if abs(curr_value - min_value) < 1e-6:
                min_indexes.append(row_number)
            elif curr_value < min_value:
                min_value = curr_value
                min_indexes = [row_number]

        for row_number in min_indexes:
            utg_possible_ne_points.add((row_number, col_number))


    return btn_possible_ne_points, utg_possible_ne_points


def get_range():
    return range(0, 100, RANGE_INCREMENTS)


def create_heatmap(pot_size=1, bet_size=1):
    btn_evs = []
    for u_i in get_range():
        row_list = []
        u = u_i / 100

        for b_i in get_range():
            b = b_i / 100
            row_list.append(btn_ev(u, b, pot_size, bet_size))
        btn_evs.append(row_list)

    btn_nes, utg_nes = get_possible_ne_points(btn_evs)

    axis_labels = [str(i / 100) for i in get_range()]

    cmap = sns.color_palette("rocket")

    fig, ax = plt.subplots(figsize=(20,10))

    sns.heatmap(
        data=btn_evs,
        # vmin=0,
        # vmax=pot_size,
        xticklabels=axis_labels,
        yticklabels=axis_labels,
        annot=True,
        fmt=".3f",
        cmap=cmap,
        ax=ax,
    )

    ax.invert_yaxis()
    ax.set_yticklabels(ax.get_yticklabels(), rotation=90)
    ax.set(xlabel="BTN minimum hand strength", ylabel="UTG minimum hand strength")
    cbar = ax.collections[0].colorbar
    cbar.set_label("BTN EV")

    # Add row max-values
    for btn_ne in btn_nes:
        row, col = btn_ne
        circles = patches.Circle(
            (col + 0.5, row + 0.5), 0.5, edgecolor="black", facecolor="red"
        )
        ax.add_patch(circles)

    # Add col min values
    for utg_ne in utg_nes:
        row, col = utg_ne
        circles = patches.Circle(
            (col + 0.5, row + 0.5), 0.5, edgecolor="black", facecolor="blue"
        )
        ax.add_patch(circles)

    # Draw a circle around the Nash Equilibrium point. The point is hardcoded,
    # but could be calculated from the data, since this is the point where the
    # value is the maximum in the row and minimum in the column.

    # Actual NE points
    ne_points = btn_nes.intersection(utg_nes)

    for ne_point in ne_points:
        row, col = ne_point
        circle = patches.Circle(
            (col + 0.5, row + 0.5), 0.5, edgecolor="black", facecolor="darkviolet"
        )
        ax.add_patch(circle)

    # Create a legend
    red_patch = patches.Patch(color="red", label="Row max value")
    blue_patch = patches.Patch(color="blue", label="Col min value")
    violet_patch = patches.Patch(color="darkviolet", label="Nash Equilibrium")
    plt.legend(
        handles=[red_patch, blue_patch, violet_patch],
        bbox_to_anchor=(1.15, 1),
        loc="upper left",
    )
    plt.title(f"BTN EV for Pot size {pot_size}, Bet size {bet_size}")

    return fig

def graphviz_chart():
    # Create a new directed graph
    dot = Digraph(graph_attr={'rankdir':'LR'})

    # Add nodes
    dot.node('ua1', 'UTG choice')
    dot.node('bw1', 'BTN wins', shape='box', style='filled', fillcolor='orange')
    dot.node('uw1', 'UTG wins', shape='box', style='filled', fillcolor='lightblue')
    dot.node('ba1', 'BTN choice')
    dot.node('sd', 'Showdown')
    dot.node('bw2', 'BTN wins', shape='box', style='filled', fillcolor='orange')
    dot.node('uw2', 'UTG wins', shape='box', style='filled', fillcolor='lightblue')

    # Add edges
    dot.edge('ua1', 'bw1', label='Fold')
    dot.edge('ua1', 'ba1', label='Bet')
    dot.edge('ba1', 'uw1', label='Fold')
    dot.edge('ba1', 'sd', label='Call')
    dot.edge('sd', 'bw2', label='BTN has better hand')
    dot.edge('sd', 'uw2', label='UTG has better hand')

    return dot

def run_st():
    st.markdown("""
                # Poker

                This is very simplified poker game. The goal is to try to explain the concept of Nash Equilibrium in poker.

                This game has 2 players: UTG (short for under-the-gun) and BTN (short for button). These terms are poker jargon and refer to the positions of the players at the table.

                Players hands are represented as a number between 0 and 1. If there is a showdon, the player with the higher number wins the hand. For simplicity we assume the numbers cannot be equal.

                Initially the pot has X chips in it.

                UTG is the first to act and they can either fold or bet Z chips. If UTG folds, BTN wins the pot. If UTG bets, BTN can either fold or call and pay Z chips. If BTN folds, UTG wins the pot. If BTN calls, the players hands are compared and the player with the higher hand wins the pot and the chips that were bet.

                The following chart shows the possible outcomes:
                """)
    gc = graphviz_chart()
    st.graphviz_chart(gc)

    col1, col2 = st.columns(2)

    pot_size = col1.number_input("Pot size", min_value=1, max_value=10, value=1)
    bet_size = col2.number_input("Bet size", min_value=1, max_value=10, value=1)

    fig = create_heatmap(pot_size, bet_size)
    st.pyplot(fig)


if __name__ == "__main__":
    run_st()
