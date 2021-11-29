import math

from fastnumbers import fast_float

OP_BONUS = 1.5
OC_BONUS = 50  # return investment.amount / OC_BONUS


def calculate(new, old, net_worth=0, top_networth=0):
    new = fast_float(new)
    old = fast_float(old)
    net_worth = fast_float(net_worth)

    # Treat anything below 0 upvotes as 0 upvotes
    if old < 0:
        old = 0
    if new < 0:
        new = 0
    if net_worth < 0:
        net_worth = 1

    # Compute gain
    delta = new - old

    # Treat negative gain as no gain
    if delta < 0:
        delta = 0

    # Compute the maximum of the sigmoid
    sig_max = sigmoid_max(old)

    # Compute the midpoint of the sigmoid
    sig_mp = sigmoid_midpoint(old)

    # Compute the steepness of the sigmoid
    sig_stp = sigmoid_steepness(old)

    # Calculate return
    factor = sigmoid(delta, sig_max, sig_mp, sig_stp)

    factor = adjust(factor, net_worth, top_networth)

    factor = max(0, factor)
    return factor


def sigmoid(x, maxvalue, midpoint, steepness):
    arg = -(steepness * (x - midpoint))
    y = fast_float(maxvalue) / (1 + math.exp(arg))
    return y


MAX_A = 2.6
MAX_B = 0
MAX_C = 30


def sigmoid_max(old):
    return MAX_A + MAX_B / ((old / MAX_C) + 1)


MID_A = 70
MID_B = 5000
MID_M = 25000


def sigmoid_midpoint(old):
    return linear_interpolate(old, 0, MID_M, MID_A, MID_B)


STEEP_A = 0.05
STEEP_C = 400


def sigmoid_steepness(old):
    return STEEP_A / ((old / STEEP_C) + 1)


def linear_interpolate(x, x_0, x_1, y_0, y_1):
    m = (y_1 - y_0) / fast_float(x_1 - x_0)
    c = y_0
    y = (m * x) + c
    return y


def adjust(factor, net_worth=0, top_networth=0) -> float:
    # aggiusta il factor per movimentare la classifica
    if net_worth and top_networth:
        # Normalize between -1 and 1
        # factor = factor - 1

        # Adjust based on net worth, only for earnings
        if factor > 1:
            factor = factor * net_worth_coefficient(net_worth, top_networth)

        # Return investment amount multiplier (change + 1)
        # factor = factor + 1
    return factor


def net_worth_coefficient(net_worth, top_networth=0) -> float:
    # questa funzione restituisce un moltimplicatore che amplifica (o riduce)
    # il ritorno di un investimento in base alla rapporto tra net_worth e top_networth
    # più l'investitore è povero, più il ritorno sarà amplificato (valore >1)
    # più il patrimonio dell'investitore è sopra lo 0.7 del top_networth,
    #     più il ritorno sarà diminuito
    factor = 0.155
    if top_networth:
        # normalizzo il rapporto tra patrimonio e massimo in 100esimi
        net_worth = max(1, net_worth * 100 / top_networth)
        # il fattore è pre-calcolato rispetto ad un massimo di 100
        factor = 0.4217397848287947  # math.log(6, 100 * 0.7)
    return (net_worth ** -factor) * 6
