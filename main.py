import matplotlib.patches as patches
import matplotlib.pyplot as plt
import seaborn as sns

POT_SIZE = 3
BET_SIZE = 2
# RANGE_INCREMENTS x means we will have (100 / x) in the range
# For example with 5 the values are [0, 0.05, 0.1, 0.15, ..., 0.95]
RANGE_INCREMENTS = 5


# prob for random number in [u, 1] being bigger than in [b, 1]
def u_win_prob(u, b):
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


def btn_ev(u, b):
    total_ev = 0

    # U fold
    total_ev += u_fold_prob(u, b) * POT_SIZE
    # U bet, B fold
    total_ev += u_bet_b_fold_prob(u, b) * 0
    # U bet, B call, U win
    total_ev += u_bet_b_call_u_win_prob(u, b) * -BET_SIZE
    # U bet, B call, B win
    total_ev += u_bet_b_call_b_win_prob(u, b) * (POT_SIZE + BET_SIZE)

    return total_ev


def utg_ev(u, b):
    total_ev = 0

    # U fold
    total_ev += u_fold_prob(u, b) * 0
    # U bet, B fold
    total_ev += u_bet_b_fold_prob(u, b) * POT_SIZE
    # U bet, B call, U win
    total_ev += u_bet_b_call_u_win_prob(u, b) * (POT_SIZE + BET_SIZE)
    # U bet, B call, B win
    total_ev += u_bet_b_call_b_win_prob(u, b) * -BET_SIZE

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


def create_heatmap():
    btn_evs = []
    for u_i in get_range():
        row_list = []
        u = u_i / 100

        for b_i in get_range():
            b = b_i / 100
            row_list.append(btn_ev(u, b))
        btn_evs.append(row_list)

    btn_nes, utg_nes = get_possible_ne_points(btn_evs)

    axis_labels = [str(i / 100) for i in get_range()]

    cmap = sns.color_palette("rocket")

    ax = sns.heatmap(
        data=btn_evs,
        vmin=0,
        vmax=POT_SIZE,
        xticklabels=axis_labels,
        yticklabels=axis_labels,
        annot=True,
        fmt=".3f",
        cmap=cmap,
    )

    ax.invert_yaxis()
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
    plt.title(f"BTN EV for Pot size {POT_SIZE}, Bet size {BET_SIZE}")

    plt.show()


if __name__ == "__main__":
    create_heatmap()
