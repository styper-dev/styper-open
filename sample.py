import os
import sys
import random
random.seed(100)


def main():
    filename = sys.argv[1]
    all_lines = open(filename).read().splitlines()
    N = len(all_lines)
    choices = random.sample(range(0, N), 100)
    selected_lines = [all_lines[idx] for idx in choices]
    for line in selected_lines:
        print(line)

if __name__ == "__main__":
    main()
