#!/usr/bin/env python3
import argparse
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import List, Optional

from typeguard import check_argument_types

from espnet2.text.cp_build_tokenizer import build_tokenizer
from espnet2.text.cleaner import TextCleaner
from espnet2.text.phoneme_tokenizer import g2p_choices
from espnet2.utils.types import str2bool, str_or_none
from espnet.utils.cli_utils import get_commandline_args


def field2slice(field: Optional[str]) -> slice:
    """Convert field string to slice.

    Note that field string accepts 1-based integer.
    Examples:
        >>> field2slice("1-")
        slice(0, None, None)
        >>> field2slice("1-3")
        slice(0, 3, None)
        >>> field2slice("-3")
        slice(None, 3, None)
    """
    field = field.strip()
    try:
        if "-" in field:
            # e.g. "2-" or "2-5" or "-7"
            s1, s2 = field.split("-", maxsplit=1)
            if s1.strip() == "":
                s1 = None
            else:
                s1 = int(s1)
                if s1 == 0:
                    raise ValueError("1-based string")
            if s2.strip() == "":
                s2 = None
            else:
                s2 = int(s2)
        else:
            # e.g. "2"
            s1 = int(field)
            s2 = s1 + 1
            if s1 == 0:
                raise ValueError("must be 1 or more value")
    except ValueError:
        raise RuntimeError(f"Format error: e.g. '2-', '2-5', or '-5': {field}")

    if s1 is None:
        slic = slice(None, s2)
    else:
        # -1 because of 1-based integer following "cut" command
        # e.g "1-3" -> slice(0, 3)
        slic = slice(s1 - 1, s2)
    return slic


def tokenize(
    input: str,
    output: str,
    field: Optional[str],
    delimiter: Optional[str],
    token_type: str,
    space_symbol: str,
    joint_symbol: str,
    char_non_linguistic_symbols: Optional[str],
    phone_non_linguistic_symbols: Optional[str],
    bpemodel: Optional[str],
    log_level: str,
    write_vocabulary: bool,
    char_vocabulary_size: int,
    phone_vocabulary_size: int,
    remove_non_linguistic_symbols: bool,
    cutoff: int,
    add_symbol: List[str],
    cleaner: Optional[str],
    add_nonsplit_symbol: List[str],
):
    assert check_argument_types()

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s (%(module)s:%(lineno)d) %(levelname)s: %(message)s",
    )
    if input == "-":
        fin = sys.stdin
    else:
        fin = Path(input).open("r", encoding="utf-8")
    if output == "-":
        c_fout = sys.stdout
        p_fout = sys.stdout
    else:
        phone_output, char_output = output.split(",")
        c_p = Path(char_output)
        c_p.parent.mkdir(parents=True, exist_ok=True)
        c_fout = c_p.open("w", encoding="utf-8")

        p_p = Path(phone_output)
        p_p.parent.mkdir(parents=True, exist_ok=True)
        p_fout = p_p.open("w", encoding="utf-8")

    cleaner = TextCleaner(cleaner)
    tokenizer = build_tokenizer(
        token_type=token_type,
        char_non_linguistic_symbols=char_non_linguistic_symbols,
        phone_non_linguistic_symbols=phone_non_linguistic_symbols,
        remove_non_linguistic_symbols=remove_non_linguistic_symbols,
        space_symbol=space_symbol,
        joint_symbol=joint_symbol,
        nonsplit_symbol=add_nonsplit_symbol,
    )

    p_counter = Counter()
    c_counter = Counter()
    if field is not None:
        field = field2slice(field)

    for line in fin:
        line = line.rstrip()
        if field is not None:
            # e.g. field="2-"
            # uttidA hello world!! -> hello world!!
            tokens = line.split(delimiter)
            tokens = tokens[field]
            if delimiter is None:
                line = " ".join(tokens)
            else:
                line = delimiter.join(tokens)

        line = cleaner(line)
        tokens = tokenizer.text2tokens(line)
        if not write_vocabulary:
            c_fout.write(" ".join(tokens["char"]) + "\n")
            p_fout.write(" ".join(tokens["phone"]) + "\n")
        else:
            for t in tokens["char"]:
                c_counter[t] += 1
            for t in tokens["phone"]:
                p_counter[t] += 1

    if not write_vocabulary:
        return

    # ======= write_vocabulary mode from here =======
    # Sort by the number of occurrences in descending order
    # and filter lower frequency words than cutoff value
    c_words_and_counts = list(
        filter(lambda x: x[1] > cutoff, sorted(c_counter.items(), key=lambda x: -x[1]))
    )
    p_words_and_counts = list(
        filter(lambda x: x[1] > cutoff, sorted(p_counter.items(), key=lambda x: -x[1]))
    )
    # Restrict the vocabulary size
    if char_vocabulary_size > 0:
        if char_vocabulary_size < len(add_symbol):
            raise RuntimeError(
                f"char_vocabulary_size is too small: {char_vocabulary_size}"
            )
        c_words_and_counts = c_words_and_counts[
            : char_vocabulary_size - len(add_symbol)
        ]
    if phone_vocabulary_size > 0:
        if phone_vocabulary_size < len(add_symbol):
            raise RuntimeError(
                f"phone_vocabulary_size is too small: {phone_vocabulary_size}"
            )
        p_words_and_counts = p_words_and_counts[
            : phone_vocabulary_size - len(add_symbol)
        ]

    # Parse the values of --add_symbol and --add_nonsplit_symbol
    for symbol_and_id in add_symbol + add_nonsplit_symbol:
        # e.g symbol="<blank>:0"
        try:
            symbol, idx = symbol_and_id.split(":")
            idx = int(idx)
        except ValueError:
            raise RuntimeError(f"Format error: e.g. '<blank>:0': {symbol_and_id}")
        symbol = symbol.strip()

        # e.g. idx=0  -> append as the first symbol
        # e.g. idx=-1 -> append as the last symbol
        c_idx = idx
        p_idx = idx
        if idx < 0:
            c_idx = len(c_words_and_counts) + 1 + idx
            p_idx = len(p_words_and_counts) + 1 + idx
        c_words_and_counts.insert(c_idx, (symbol, None))
        p_words_and_counts.insert(p_idx, (symbol, None))

    # Write words
    for w, c in c_words_and_counts:
        c_fout.write(w + "\n")
    for w, c in p_words_and_counts:
        p_fout.write(w + "\n")

    # Logging (char)
    total_count = sum(c_counter.values())
    invocab_count = sum(c for w, c in c_words_and_counts if c is not None)
    logging.info(
        f"Char OOV rate = {(total_count - invocab_count) / total_count * 100} %"
    )

    # Logging (phone)
    total_count = sum(p_counter.values())
    invocab_count = sum(c for w, c in p_words_and_counts if c is not None)
    logging.info(
        f"Phone OOV rate = {(total_count - invocab_count) / total_count * 100} %"
    )


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tokenize texts",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--log_level",
        type=lambda x: x.upper(),
        default="INFO",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"),
        help="The verbose level of logging",
    )

    parser.add_argument(
        "--input", "-i", required=True, help="Input text. - indicates sys.stdin"
    )
    parser.add_argument(
        "--output", "-o", required=True, help="Output text. - indicates sys.stdout"
    )
    parser.add_argument(
        "--field",
        "-f",
        help="The target columns of the input text as 1-based integer. e.g 2-",
    )
    parser.add_argument(
        "--token_type",
        "-t",
        default="char",
        choices=["char", "bpe", "word", "phn", "aux_phone", "char_phone"],
        help="Token type",
    )
    parser.add_argument("--delimiter", "-d", default=None, help="The delimiter")
    parser.add_argument("--space_symbol", default="<space>", help="The space symbol")
    parser.add_argument(
        "--joint_symbol", default="@", help="The joint symbol for char and phone"
    )
    parser.add_argument("--bpemodel", default=None, help="The bpemodel file path")
    parser.add_argument(
        "--char_non_linguistic_symbols",
        type=str_or_none,
        help="non_linguistic_symbols file path",
    )
    parser.add_argument(
        "--phone_non_linguistic_symbols",
        type=str_or_none,
        help="non_linguistic_symbols file path",
    )
    parser.add_argument(
        "--remove_non_linguistic_symbols",
        type=str2bool,
        default=False,
        help="Remove non-language-symbols from tokens",
    )
    parser.add_argument(
        "--cleaner",
        type=str_or_none,
        choices=[
            None,
            "tacotron",
            "jaconv",
            "vietnamese",
            "korean_cleaner",
            "whisper_en",
            "whisper_basic",
        ],
        default=None,
        help="Apply text cleaning",
    )

    group = parser.add_argument_group("write_vocabulary mode related")
    group.add_argument(
        "--write_vocabulary",
        type=str2bool,
        default=False,
        help="Write tokens list instead of tokenized text per line",
    )
    group.add_argument(
        "--char_vocabulary_size", type=int, default=0, help="Vocabulary size"
    )
    group.add_argument(
        "--phone_vocabulary_size", type=int, default=0, help="Vocabulary size"
    )
    group.add_argument(
        "--cutoff",
        default=0,
        type=int,
        help="cut-off frequency used for write-vocabulary mode",
    )
    group.add_argument(
        "--add_symbol",
        type=str,
        default=[],
        action="append",
        help="Append symbol e.g. --add_symbol '<blank>:0' --add_symbol '<unk>:1'",
    )
    group.add_argument(
        "--add_nonsplit_symbol",
        type=str,
        default=[],
        action="append",
        help="Append symbol that is nonsplit e.g. --add_nonsplit_symbol '<sc>:2",
    )

    return parser


def main(cmd=None):
    print(get_commandline_args(), file=sys.stderr)
    parser = get_parser()
    args = parser.parse_args(cmd)
    kwargs = vars(args)
    tokenize(**kwargs)


if __name__ == "__main__":
    main()
