# Interactive command line tool for performing test calculations for investment return
import math

from formula import calculate, adjust


def find_threshold(fixed_b, min_a, max_a, target):
    # print(f"min: {min_a}, max: {max_a}, target: {target}")

    if abs(max_a - min_a) <= 1:
        # print("Reached base case")

        v = calculate(min_a, fixed_b)
        # print(f"v: {v}")

        return min_a

    mid_a = (max_a + min_a) / 2
    # print(f"mid: {mid_a}")

    v = calculate(mid_a, fixed_b)
    # print(f"v: {v}")

    if v < target:
        # print("Below the target - guessing higher")
        return find_threshold(fixed_b, mid_a, max_a, target)
    else:
        # print("Above the target - guessing lower")
        return find_threshold(fixed_b, min_a, mid_a, target)


def main():
    startings = [1, 10, 20, 50]
    limit = 230
    deltas = [2, 5, 10, 20]
    threshs = [1, 1.25, 1.5, 2, 2.5]
    min_n = 0
    max_n = 1000
    print("Inizio | Fine | Totale | Rendimento")
    print("---|---|----|----")
    rets = set()
    for starting in startings:
        endings = list([d * starting for d in deltas])
        for t in threshs:
            endings.append(find_threshold(starting, min_n, max_n, t))
        endings = set([int(math.ceil(e)) for e in endings if e and e <= limit])
        endings = sorted(endings)
        for ending in endings:
            ret = calculate(ending, starting)
            rets.add(ret)
            print("{:d} | {:d} | {:.2f} | {:+.2f}".format(starting, ending, ret, ret - 1))
    pnet_worths = [0.1, 0.2, 0.5, 0.8, 1]
    top_networths = [1000, 5000, 100000, 100000000, 100000000000]
    rets = [0.1, 0.5, 1.0, 1.2, 1.5, 2, 2.5]
    print("\nPatrimonio | Top | Aggiustamento")
    print("---|---|---")
    for pnet_worth in pnet_worths:
        ret = 3
        top_networth = 1000000
        net_worth = int(pnet_worth * top_networth)
        nret = adjust(ret, net_worth, top_networth)
        print("{:,d} | {:,d} | {:+.2f}%".format(net_worth, top_networth, (nret - ret) / ret * 100))
    print("\nRend. Orig. | Patrimonio | Top | Totale | Rendimento | Delta")
    print("---|---|---|---|----|----")
    for ret in rets:
        for top_networth in top_networths:
            for pnet_worth in pnet_worths:
                net_worth = int(pnet_worth * top_networth)
                nret = adjust(ret, net_worth, top_networth)
                print(
                    "{:.2f} | {:,d} | {:,d} | {:.2f} | {:+.2f} | {:+.2f}".format(
                        ret, net_worth, top_networth, nret, nret - 1, (nret - ret) / ret * 100
                    )
                )


if __name__ == "__main__":
    main()
