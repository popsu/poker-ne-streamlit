import matplotlib.patches as patches
from matplotlib.pylab import f
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from graphviz import Digraph

# RANGE_INCREMENTS x means we will have (100 / x) in the range
# For example with 5 the values are [0, 0.05, 0.1, 0.15, ..., 0.95]
RANGE_INCREMENTS = 5


# probability for random number in [r, 1] of being bigger than random number in [c, 1]
def r_win_prob(r, c):
    if r > 1 or r < 0 or c > 1 or c < 0:
        raise ValueError("u and b should be in [0, 1]")
    if r >= c:
        # The math is based on looking the prob mass function
        # of the combined random variables, so basically 2d geometry.
        triangle_area = 0.5 * (1 - r) * (1 - r)
        rectangle_area = (r - c) * (1 - r)
        a_win_area = triangle_area + rectangle_area
        total_area = (1 - r) * (1 - c)

        return a_win_area / total_area
    # r < c
    return 1 - r_win_prob(c, r)


def r_bet_prob(r, c):
    return 1 - r


def r_fold_prob(r, c):
    return r


def c_call_prob(r, c):
    return 1 - c


def c_fold_prob(r, c):
    return c


def r_bet_c_fold_prob(r, c):
    r_bet = r_bet_prob(r, c)
    c_fold = c_fold_prob(r, c)

    return r_bet * c_fold


def r_bet_c_call_r_win_prob(r, c):
    r_bet = r_bet_prob(r, c)
    c_call = c_call_prob(r, c)
    r_win = r_win_prob(r, c)

    return r_bet * c_call * r_win


def u_bet_b_call_b_win_prob(u, b):
    u_bet = r_bet_prob(u, b)
    b_call = c_call_prob(u, b)
    a_win = r_win_prob(u, b)

    return u_bet * b_call * (1 - a_win)


def col_ev(r, c, pot_size, bet_size):
    total_ev = 0

    # R fold
    total_ev += r_fold_prob(r, c) * pot_size
    # R bet, C fold
    total_ev += r_bet_c_fold_prob(r, c) * 0
    # R bet, C call, R win
    total_ev += r_bet_c_call_r_win_prob(r, c) * -bet_size
    # R bet, C call, C win
    total_ev += u_bet_b_call_b_win_prob(r, c) * (pot_size + bet_size)

    return total_ev


def row_ev(r, c, pot_size, bet_size):
    total_ev = 0

    # R fold
    total_ev += r_fold_prob(r, c) * 0
    # R bet, C fold
    total_ev += r_bet_c_fold_prob(r, c) * pot_size
    # R bet, C call, R win
    total_ev += r_bet_c_call_r_win_prob(r, c) * (pot_size + bet_size)
    # R bet, C call, C win
    total_ev += u_bet_b_call_b_win_prob(r, c) * -bet_size

    return total_ev


def get_possible_ne_points(col_evs):
    length = len(col_evs)

    # col possible Nash Equilibrium points are the maximum column values in each row
    # These are the best responses for column player against each row player's strategy
    col_possible_ne_points = set()
    for row_number in range(length):
        max_value = float("-inf")
        max_indexes = []
        for col_number in range(length):
            curr_value = col_evs[row_number][col_number]

            if abs(curr_value - max_value) < 1e-6:
                max_indexes.append(col_number)
            elif curr_value > max_value:
                max_value = curr_value
                max_indexes = [col_number]

        for col_number in max_indexes:
            col_possible_ne_points.add((row_number, col_number))

    # row possible Nash Equilibrium points are the minimum row values in each column
    # These are the best responses for row player against each column player's strategy
    row_possible_ne_points = set()
    for col_number in range(length):
        min_value = float("inf")
        min_indexes = []
        for row_number in range(length):
            curr_value = col_evs[row_number][col_number]

            if abs(curr_value - min_value) < 1e-6:
                min_indexes.append(row_number)
            elif curr_value < min_value:
                min_value = curr_value
                min_indexes = [row_number]

        for row_number in min_indexes:
            row_possible_ne_points.add((row_number, col_number))


    return col_possible_ne_points, row_possible_ne_points


def get_range():
    return range(0, 100, RANGE_INCREMENTS)


def create_heatmap(pot_size=1, bet_size=1):
    col_evs = []
    for r_i in get_range():
        row_list = []
        r = r_i / 100

        for c_i in get_range():
            c = c_i / 100
            row_list.append(col_ev(r, c, pot_size, bet_size))
        col_evs.append(row_list)

    col_nes, row_nes = get_possible_ne_points(col_evs)

    axis_labels = [str(i / 100) for i in get_range()]

    cmap = sns.color_palette("rocket")

    fig, ax = plt.subplots(figsize=(20,10))

    sns.heatmap(
        data=col_evs,
        xticklabels=axis_labels,
        yticklabels=axis_labels,
        annot=True,
        fmt=".3f",
        cmap=cmap,
        ax=ax,
    )

    ax.invert_yaxis()
    ax.set_yticklabels(ax.get_yticklabels(), rotation=90)
    ax.set(xlabel="Column player minimum hand strength", ylabel="Row player minimum hand strength")
    cbar = ax.collections[0].colorbar
    cbar.set_label("Col EV")

    # Add row max-values. These are the best responses for the column player for the given row player strategy
    for col_ne in col_nes:
        row, col = col_ne
        circles = patches.Circle(
            (col + 0.5, row + 0.5), 0.5, edgecolor="black", facecolor="red"
        )
        ax.add_patch(circles)

    # Add col min values. These are the best responses for the row player for the given column player strategy
    for row_ne in row_nes:
        row, col = row_ne
        circles = patches.Circle(
            (col + 0.5, row + 0.5), 0.5, edgecolor="black", facecolor="blue"
        )
        ax.add_patch(circles)

    # Actual NE points. These are the points where the row player's strategy is the best response to the column player's strategy
    ne_points = col_nes.intersection(row_nes)

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
    plt.title(f"Col EV for Pot size {pot_size}, Bet size {bet_size}")

    return fig

def graphviz_chart():
    # Create a new directed graph
    dot = Digraph(graph_attr={'rankdir':'LR'})

    # Add nodes
    dot.node('rpc', "Row player's choice")
    dot.node('cpw1', 'Column player wins', shape='box', style='filled', fillcolor='orange')
    dot.node('rpw1', 'Row player wins', shape='box', style='filled', fillcolor='lightblue')
    dot.node('cpc', "Column player's choice")
    dot.node('sd', 'Showdown')
    dot.node('cpw2', 'Column player wins', shape='box', style='filled', fillcolor='orange')
    dot.node('rpw2', 'Row player wins', shape='box', style='filled', fillcolor='lightblue')

    # Add edges
    dot.edge('rpc', 'cpw1', label='Fold')
    dot.edge('rpc', 'cpc', label='Bet')
    dot.edge('cpc', 'rpw1', label='Fold')
    dot.edge('cpc', 'sd', label='Call')
    dot.edge('sd', 'cpw2', label='Column player has better hand')
    dot.edge('sd', 'rpw2', label='Row player has better hand')

    return dot

def run_st():
    st.markdown("""
                # Nash Equilibrium in Poker

                The goal is to try to explain the concept of Nash Equilibrium in poker. We will use a simplified version of the game of poker to illustrate the concept.

                ## Nash Equilibrium

                Nash Equilibrum is a concept in game theory. It states that in a game with 2 or more players, there is a set of strategies, one for each player, such that no player has anything to gain by changing only their own strategy. Such a set of strategies is called Nash Equilibrium. Every finite game has at least one Nash Equilibrium, and can have multiple.

                ## Simplified poker game

                This game has 2 players: Row player and Column player.

                To make the calculations simpler, we will represent player's poker hand as a number between 0 and 1. The player with the higher number wins, if there is a showdown. We will assume there is no ties.

                Initially the pot has X chips in it.

                Row player is the first to act and they can either fold or bet Z chips. If Row player folds, Column player wins the pot. If Row player bets, Column player can either fold or call and pay Z chips. If Column player folds, Row player wins the pot. If Column player calls, the players hands are compared and the player with the higher hand wins the pot and the chips that were bet.

                The following chart shows the possible outcomes and order of choices:
                """)
    gc = graphviz_chart()
    st.graphviz_chart(gc)

    st.markdown("""
                ## Expected Values (EV) for all strategy pairs

                Both players want to maximize their expected winnings. The only thing they choose is what is the minimum hand strength they are willing to play with. For example if a player has strategy of playing every hand with strength 0.5 or higher, they will fold every hand with strength lower than 0.5.

                We will calculate the EV for Column player for each possible strategy pair and plot these in a heatmap below. So Column player wants to maximize this. Because the game is zero-sum game (technically there is some extra chips in the pot), it means the Row player's EV is (X - Column player EV), where X is the initial pot size. For Row player to maximize their EV, it is equivalent for them to minimize Column player's EV.

                The X axis is the minimum hand strength of the Column player and the Y axis is the minimum hand strength of the Row player. The red circles in the heatmap show the maximum value for each row. This is the best strategy for the Column player If Row is player the strategy indicated by that row. Similarly the blue circle in the heatmap shows the minimum value for each column. This is the best strategy for the Row player if Column player is playing the strategy indicated by that column. The purple circle shows the Nash Equilibrium point, where that cell is both the maximum value in the row and minimum value in the column, so neither player has anything to gain by changing their strategy if the other player doesn't change theirs.

                You can change the Pot size and Bet size values to adjust calculations. Because the heatmap only shows strategies in 0.05 increments, it might not always show the Nash Equilibrium point with certain bet size and pot size combinations. However the nash equilibrium still always exists.
                """)

    col1, col2 = st.columns(2)

    pot_size = col1.number_input("Pot size", min_value=1, max_value=10, value=1)
    bet_size = col2.number_input("Bet size", min_value=1, max_value=10, value=1)

    fig = create_heatmap(pot_size, bet_size)
    st.pyplot(fig)

    st.markdown("""
                ## Exploiting

                If you know the strategy of the other player (and it is not Nash Equilibrium), you could win more by playing non-Nash Equilibrium strategy yourself as well. This is called exploiting and is a big part of poker. The red and blue circles in the heatmap show the best exploit strategies for each player given the other player's strategy.

                When you exploit someone, you are open to being exploited yourself. The only way to be sure to not get exploited is to play Nash Equilibrum strategy. You should only try to exploit players who are worse than you and play Nash Equilibrium strategy against better players.

                Basically playing Nash Equilibrium is safe way to play and it maximizes the winning against perfect opponents. But against worse opponents you can win more by exploiting them, but you are also open to being exploited yourself.
                """)

    st.write(
        "[Source code](https://github.com/popsu/poker-ne-streamlit)"
    )

if __name__ == "__main__":
    run_st()
