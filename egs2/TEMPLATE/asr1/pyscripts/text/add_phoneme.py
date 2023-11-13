import argparse
from typing import Optional
import pyopenjtalk  # type: ignore


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--joint_symbol", type=str, default="@")
    parser.add_argument("--field", type=str, default="2-")
    parser.add_argument("--delimiter", type=str, default=" ")
    return parser.parse_args()


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


args = parse_args()
_slic = field2slice(args.field)

with open(args.input, "r", encoding="utf-8") as fin:
    with open(args.output, "w", encoding="utf-8") as fout:
        for line in fin:
            textinfo = line.rstrip()
            text = textinfo.split(args.delimiter)[_slic]
            text = args.delimiter.join(text)

            phones = pyopenjtalk.g2p(text)
            output_text = args.joint_symbol.join([textinfo, phones])
            fout.write(output_text + "\n")
