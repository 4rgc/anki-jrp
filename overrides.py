from collections.abc import Generator
from dataclasses import dataclass

from util import ConfigError, check_json_value


@dataclass
class IgnoreOverride:
    variants: list[str]
    reading: str | None = None

    def match(self, variant: str, reading: str | None) -> bool:
        return variant in self.variants and (not self.reading or reading == self.reading)

    @classmethod
    def from_json(cls, obj: dict) -> "IgnoreOverride":
        variants = check_json_value(obj, "variants", list, str, True)
        reading = check_json_value(obj, "reading", str)
        return cls(variants, reading)


@dataclass
class WordOverride:
    old_variants: list[str]
    old_reading: str | None
    new_variants: list[str] | None
    new_reading: str | None
    pre_lookup: bool = False
    post_lookup: bool = True

    def apply(self, variant: str, reading: str | None) -> Generator[tuple[str, str | None]] | None:
        if variant in self.old_variants and (not self.old_reading or not reading or reading == self.old_reading):
            new_variants = self.new_variants or (variant,)
            return ((nv, self.new_reading or reading) for nv in new_variants)
        else:
            return None

    @classmethod
    def from_json(cls, obj: dict) -> "WordOverride":
        old_variants = check_json_value(obj, "old_variants", list, str, True)
        old_reading = check_json_value(obj, "old_reading", str)
        new_variants = check_json_value(obj, "new_variants", list, str)
        new_reading = check_json_value(obj, "new_reading", str)
        pre_lookup = check_json_value(obj, "pre_lookup", bool)
        post_lookup = check_json_value(obj, "post_lookup", bool)
        if not new_variants and not new_reading:
            raise ConfigError("new variant list and new reading can't both be missing")
        return cls(old_variants, old_reading, new_variants, new_reading, pre_lookup, post_lookup)


@dataclass
class AccentOverride:
    variants: list[str]
    reading: str
    accents: list[int]

    @classmethod
    def from_json(cls, obj: dict) -> "AccentOverride":
        variants = check_json_value(obj, "variants", list, str, True)
        reading = check_json_value(obj, "reading", str, required=True)
        accents = check_json_value(obj, "accents", list, int, True)
        return cls(variants, reading, accents)
