# Interactive command line tool for performing test calculations for investment return
import math

from formula import adjust, calculate


def find_threshold(fixed_b, min_a, max_a, target):
    # print(f"min: {min_a}, max: {max_a}, target: {target}")

    if abs(max_a - min_a) <= 1:
        # print("Reached base case")

        v = calculate(min_a, fixed_b)
        if v > target:
            # v = calculate(max_a, fixed_b)
            # print(f"v: {v} - {max_a}")
            return min_a

        # print(f"v: {v} - {min_a}")
        return max_a

    mid_a = int((max_a + min_a) / 2)
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
    startings = [1, 5, 10, 20, 50]
    limit = 900
    deltas = [2, 5, 10, 20]
    threshs = [1, 1.25, 1.5, 2, 2.4]
    print("Inizio | Fine | Totale | Rendimento")
    print("---|---|----|----")
    rets = set()
    for starting in startings:
        endings = list([d * starting for d in deltas])
        for t in threshs:
            endings.append(find_threshold(starting, 0, limit, t))
        endings = set([int(math.ceil(e)) for e in endings if e and e <= limit])
        endings = sorted(endings)
        for ending in endings:
            ret = calculate(ending, starting)
            rets.add(ret)
            print(f"{starting:d} | {ending:d} | {ret:.2f} | {ret - 1:+.2f}")
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
        print(f"{net_worth:,d} | {top_networth:,d} | {(nret - ret) / ret * 100:+.2f}%")
    print("\nRend. Orig. | Patrimonio | Top | Totale | Rendimento | Delta")
    print("---|---|---|---|----|----")
    for ret in rets:
        for top_networth in top_networths:
            for pnet_worth in pnet_worths:
                net_worth = int(pnet_worth * top_networth)
                nret = adjust(ret, net_worth, top_networth)
                print(
                    f"{ret:.2f} | {net_worth:,d} | {top_networth:,d} | {nret:.2f} | {nret - 1:+.2f} | {(nret - ret) / ret * 100:+.2f}"
                )


if __name__ == "__main__":
    main()
