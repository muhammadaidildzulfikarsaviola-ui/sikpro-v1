def check_nelson_rules(data, mean, ucl, lcl):
    
    violations = []

    # zona
    sigma = (ucl - mean) / 3
    zone_a = 2 * sigma
    zone_b = sigma

    # ================= RULE 1
    for i, val in enumerate(data):
        if val > ucl or val < lcl:
            violations.append(("Rule 1", i+1, "Titik di luar batas kendali"))

    # ================= RULE 2
    count = 0
    side = None
    for i, val in enumerate(data):
        current = val > mean
        if current == side:
            count += 1
        else:
            count = 1
            side = current
        if count >= 9:
            violations.append(("Rule 2", i+1, "9 titik di satu sisi mean"))

    # ================= RULE 3
    up = down = 0
    for i in range(1, len(data)):
        if data[i] > data[i-1]:
            up += 1
            down = 0
        elif data[i] < data[i-1]:
            down += 1
            up = 0

        if up >= 5:
            violations.append(("Rule 3", i+1, "Trend naik"))
        if down >= 5:
            violations.append(("Rule 3", i+1, "Trend turun"))

    # ================= RULE 4 (zigzag)
    zigzag = 0
    for i in range(2, len(data)):
        if (data[i] > data[i-1] < data[i-2]) or (data[i] < data[i-1] > data[i-2]):
            zigzag += 1
        else:
            zigzag = 0

        if zigzag >= 13:
            violations.append(("Rule 4", i+1, "Zig-zag tinggi"))

    # ================= RULE 5 (zona A)
    for i in range(len(data)-2):
        subset = data[i:i+3]
        count = sum(abs(x - mean) > zone_a for x in subset)
        if count >= 2:
            violations.append(("Rule 5", i+3, "2 dari 3 di zona A"))

    # ================= RULE 6 (zona B)
    for i in range(len(data)-4):
        subset = data[i:i+5]
        count = sum(abs(x - mean) > zone_b for x in subset)
        if count >= 4:
            violations.append(("Rule 6", i+5, "4 dari 5 di zona B"))

    # ================= RULE 7 (zona C)
    for i in range(len(data)-14):
        subset = data[i:i+15]
        if all(abs(x - mean) < zone_b for x in subset):
            violations.append(("Rule 7", i+15, "15 titik dekat mean"))

    # ================= RULE 8 (luar zona C)
    for i in range(len(data)-7):
        subset = data[i:i+8]
        if all(abs(x - mean) > zone_b for x in subset):
            violations.append(("Rule 8", i+8, "8 titik jauh dari mean"))

    return violations