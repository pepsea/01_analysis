"""
ペプチド分子量計算モジュール

アミノ酸配列からペプチドの分子量を計算する。
モノアイソトピック質量および平均質量の両方に対応。
"""

# モノアイソトピック残基質量 (Da)
MONOISOTOPIC_MASS = {
    "G": 57.02146,
    "A": 71.03711,
    "V": 99.06841,
    "L": 113.08406,
    "I": 113.08406,
    "P": 97.05276,
    "F": 147.06841,
    "W": 186.07931,
    "M": 131.04049,
    "S": 87.03203,
    "T": 101.04768,
    "C": 103.00919,
    "Y": 163.06333,
    "H": 137.05891,
    "D": 115.02694,
    "E": 129.04259,
    "N": 114.04293,
    "Q": 128.05858,
    "K": 128.09496,
    "R": 156.10111,
}

# 平均残基質量 (Da)
AVERAGE_MASS = {
    "G": 57.0519,
    "A": 71.0788,
    "V": 99.1326,
    "L": 113.1594,
    "I": 113.1594,
    "P": 97.1167,
    "F": 147.1766,
    "W": 186.2132,
    "M": 131.1926,
    "S": 87.0782,
    "T": 101.1051,
    "C": 103.1388,
    "Y": 163.1760,
    "H": 137.1411,
    "D": 115.0886,
    "E": 129.1155,
    "N": 114.1038,
    "Q": 128.1307,
    "K": 128.1741,
    "R": 156.1875,
}

# 水分子の質量 (ペプチド結合形成時にN末端のHとC末端のOHを加算)
WATER_MONOISOTOPIC = 18.01056
WATER_AVERAGE = 18.0153

# 一般的な修飾の質量変化
MODIFICATIONS = {
    "phosphorylation": 79.96633,       # リン酸化 (S, T, Y)
    "acetylation": 42.01057,           # アセチル化 (N末端, K)
    "methylation": 14.01565,           # メチル化 (K, R)
    "dimethylation": 28.03130,         # ジメチル化
    "trimethylation": 42.04695,        # トリメチル化
    "oxidation": 15.99491,             # 酸化 (M)
    "deamidation": 0.98402,            # 脱アミド化 (N, Q)
    "carbamidomethylation": 57.02146,  # カルバミドメチル化 (C)
    "ubiquitination": 114.04293,       # ユビキチン化 (K) - GlyGly tag
}


def calculate_mw(sequence, mass_type="monoisotopic", modifications=None):
    """
    ペプチド配列から分子量を計算する。

    Parameters
    ----------
    sequence : str
        アミノ酸の一文字表記配列 (例: "ACDEFGHIK")
    mass_type : str
        "monoisotopic" (モノアイソトピック質量) または "average" (平均質量)
    modifications : list of dict, optional
        修飾のリスト。各要素は {"position": int, "type": str} の辞書。
        position は0始まりのインデックス。
        type は MODIFICATIONS 辞書のキー、またはカスタム質量 (float)。

    Returns
    -------
    float
        計算された分子量 (Da)

    Raises
    ------
    ValueError
        不明なアミノ酸や質量タイプが指定された場合
    """
    sequence = sequence.upper().replace(" ", "").replace("\n", "")

    if mass_type == "monoisotopic":
        mass_table = MONOISOTOPIC_MASS
        water = WATER_MONOISOTOPIC
    elif mass_type == "average":
        mass_table = AVERAGE_MASS
        water = WATER_AVERAGE
    else:
        raise ValueError(f"不明な質量タイプ: {mass_type} ('monoisotopic' または 'average' を指定)")

    # 不明なアミノ酸のチェック
    unknown = set(sequence) - set(mass_table.keys())
    if unknown:
        raise ValueError(f"不明なアミノ酸: {', '.join(sorted(unknown))}")

    # 残基質量の合計 + 水分子(N末端H + C末端OH)
    mw = sum(mass_table[aa] for aa in sequence) + water

    # 修飾の適用
    if modifications:
        for mod in modifications:
            mod_type = mod["type"]
            if isinstance(mod_type, (int, float)):
                mw += float(mod_type)
            elif mod_type in MODIFICATIONS:
                mw += MODIFICATIONS[mod_type]
            else:
                raise ValueError(f"不明な修飾タイプ: {mod_type}")

    return mw


def calculate_mz(sequence, charge, mass_type="monoisotopic", modifications=None):
    """
    ペプチドのm/z値を計算する（質量分析用）。

    Parameters
    ----------
    sequence : str
        アミノ酸の一文字表記配列
    charge : int
        荷電状態 (z)。正イオンモードでは正の整数。
    mass_type : str
        "monoisotopic" または "average"
    modifications : list of dict, optional
        修飾のリスト

    Returns
    -------
    float
        m/z 値
    """
    if charge == 0:
        raise ValueError("荷電状態は0以外を指定してください")

    proton_mass = 1.00728
    mw = calculate_mw(sequence, mass_type, modifications)
    return (mw + charge * proton_mass) / abs(charge)


def amino_acid_composition(sequence):
    """
    アミノ酸組成を返す。

    Parameters
    ----------
    sequence : str
        アミノ酸の一文字表記配列

    Returns
    -------
    dict
        各アミノ酸の出現回数
    """
    sequence = sequence.upper().replace(" ", "").replace("\n", "")
    composition = {}
    for aa in sequence:
        composition[aa] = composition.get(aa, 0) + 1
    return dict(sorted(composition.items()))


def sequence_summary(sequence, mass_type="monoisotopic"):
    """
    ペプチド配列の概要情報を返す。

    Parameters
    ----------
    sequence : str
        アミノ酸の一文字表記配列
    mass_type : str
        "monoisotopic" または "average"

    Returns
    -------
    dict
        配列の概要情報
    """
    sequence = sequence.upper().replace(" ", "").replace("\n", "")
    mw = calculate_mw(sequence, mass_type)
    composition = amino_acid_composition(sequence)

    return {
        "sequence": sequence,
        "length": len(sequence),
        "molecular_weight": round(mw, 5),
        "mass_type": mass_type,
        "composition": composition,
        "mz_1": round(calculate_mz(sequence, 1, mass_type), 5),
        "mz_2": round(calculate_mz(sequence, 2, mass_type), 5),
        "mz_3": round(calculate_mz(sequence, 3, mass_type), 5),
    }


if __name__ == "__main__":
    # 使用例
    test_sequences = [
        "ACDEFGHIKLMNPQRSTVWY",  # 全20種アミノ酸
        "SIINFEKL",               # OVA257-264 (マウスMHC-I エピトープ)
        "GILGFVFTL",              # Influenza M1 (HLA-A2エピトープ)
    ]

    for seq in test_sequences:
        info = sequence_summary(seq)
        print(f"配列: {info['sequence']}")
        print(f"  長さ: {info['length']} aa")
        print(f"  分子量 (monoisotopic): {info['molecular_weight']:.5f} Da")
        print(f"  [M+H]+:  {info['mz_1']:.5f}")
        print(f"  [M+2H]2+: {info['mz_2']:.5f}")
        print(f"  [M+3H]3+: {info['mz_3']:.5f}")
        print(f"  組成: {info['composition']}")
        print()
